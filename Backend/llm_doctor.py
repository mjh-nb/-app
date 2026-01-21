# llm_doctor.py
import json
from openai import OpenAI
import data_loader  # 引入刚才写的数据模块

# 初始化 DeepSeek 客户端 (请替换你的 Key)
client = OpenAI(
    api_key="sk-aad791214f9441a9b5af19b6c63f1ed3",
    base_url="https://api.deepseek.com"
)


class DoctorResult:
    def __init__(self, reply, new_info=None):
        self.reply = reply
        self.new_info = new_info  # 这里的 new_info 是整个 context 的更新


# --- 核心函数 1: 症状提取 (来自队友代码) ---
def extract_complex_info(user_text):
    if not user_text: return {}

    # 动态构造 Prompt
    schema_prompt = {}
    for code, info in data_loader.SYMPTOM_SCHEMA.items():
        schema_prompt[code] = {}
        for i, dim in enumerate(info['dims']):
            opts = info['options'][i]
            schema_prompt[code][dim] = f"可选: {','.join(opts)}" if opts else "自由文本"

    prompt = f"""
    你是一个医疗记录员。请分析用户输入。
    【症状定义表】: 
    {json.dumps(schema_prompt, ensure_ascii=False, indent=2)}
    【用户输入】: "{user_text}"
    【任务】:
    1. 识别用户提到了哪些症状？
    2. 对于每个症状，根据定义表提取具体的维度信息。
    3. 严禁编造，只提取原文提到的信息。
    【输出格式 (JSON)】:
    {{ "Headache": {{ "部位": "前额" }} }}
    没有提取到则返回 {{}}。不要Markdown格式。
    """
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            stream=False
        )
        raw = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        if not raw: return {}
        return json.loads(raw)
    except Exception as e:
        print(f"[LLM] 提取出错: {e}")
        return {}


# --- 核心函数 2: 证候匹配 (来自队友代码) ---
def calculate_disease_match(symptom_keys, tongue_keys):
    all_keys = set(symptom_keys) | set(tongue_keys)
    scores = {}
    for disease_name, rules in data_loader.DISEASE_DB.items():
        current_score = 0
        max_possible = 0
        for code in rules['core']:
            max_possible += 10
            if code in all_keys: current_score += 10
        for code in rules['side']:
            max_possible += 3
            if code in all_keys: current_score += 3

        if max_possible > 0:
            match_rate = int((current_score / max_possible) * 100)
            if match_rate > 15:
                scores[disease_name] = match_rate
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


# --- 主逻辑: 诊断与回复 ---
def get_diagnosis_and_reply(user_text, history, saved_context, current_image_features=None):
    # 1. 解析前端传来的 Context
    # 确保结构存在，防止报错
    current_symptoms = saved_context.get("symptoms", {})
    current_tongue = saved_context.get("tongue", {})

    has_update = False

    # 2. 处理图像特征 (如果有)
    # image_processor 返回的是 {"tongue_substance": "舌红"} 这种字典
    # 我们需要把它存入 current_tongue，这里假设 value=1 代表存在
    if current_image_features:
        # 这里需要做一个简单的映射，或者直接存
        # 假设 current_image_features 里的 value 就是 code (例如 "PaleRed")
        # 为简化，直接把 feature 的 value 当作 key 存入 tongue 字典
        for k, v in current_image_features.items():
            if k in ["tongue_substance", "tongue_coating"]:
                # 注意：这里可能需要根据你的 Excel 映射一下中文到英文Code
                # 暂时假设 v 就是 Code，或者后续匹配算法能处理中文
                current_tongue[v] = 1
        has_update = True

    # 3. 处理文本提取 (如果有)
    if user_text:
        new_extracted = extract_complex_info(user_text)
        if new_extracted:
            # 合并症状
            for code, details in new_extracted.items():
                if code not in current_symptoms:
                    current_symptoms[code] = details
                else:
                    current_symptoms[code].update(details)
            has_update = True

    # 4. 执行证候匹配算法
    symptom_keys = list(current_symptoms.keys())
    tongue_keys = list(current_tongue.keys())
    matches = calculate_disease_match(symptom_keys, tongue_keys)

    # 5. 生成回复 Prompt
    if not matches:
        top_diagnosis = "未匹配到明显证候"
        system_prompt = "你是一个中医助手。用户目前症状信息不足。请引导用户多描述一些身体感受。"
    else:
        top_diagnosis, top_score = matches[0]
        if top_score < 40:
            system_prompt = f"你是一个中医助手。目前最怀疑是【{top_diagnosis}】(匹配度{top_score}%)，但不敢确诊。请根据该证候的典型症状进行追问。"
        else:
            system_prompt = f"你是一个老中医。系统诊断用户为【{top_diagnosis}】。请给出该证型的解释和调理建议。"

    # 6. 调用 DeepSeek 生成最终回复
    try:
        reply_resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"用户症状：{current_symptoms}。用户刚才说：{user_text}"}
            ]
        )
        ai_msg = reply_resp.choices[0].message.content
    except Exception as e:
        ai_msg = f"系统繁忙: {str(e)}"

    # 7. 返回结果
    # 构造新的 Context 结构返回给前端保存
    new_context_full = {
        "symptoms": current_symptoms,
        "tongue": current_tongue,
        "diagnosis": top_diagnosis  # 也可以把诊断结果存下来
    }

    return DoctorResult(reply=ai_msg, new_info=new_context_full if has_update else None)