# llm_doctor.py
import json
from openai import OpenAI
import data_loader  # 确保你的目录下有这个模块

# 初始化 DeepSeek 客户端
# 【注意】请妥善保管 Key，不要上传到公开代码仓库
client = OpenAI(
    api_key="sk-aad791214f9441a9b5af19b6c63f1ed3",  # 替换为你的真实 Key
    base_url="https://api.deepseek.com"
)

class DoctorResult:
    def __init__(self, reply, new_info=None):
        self.reply = reply
        self.new_info = new_info  # 用于返回更新后的 context 给前端保存

# --- 核心函数 1: 症状提取 ---
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
            stream=False,
            temperature=0.1 # 提取信息需要精确，温度设低点
        )
        raw = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        if not raw: return {}
        return json.loads(raw)
    except Exception as e:
        print(f"[LLM] 提取出错: {e}")
        return {}

# --- 核心函数 2: 证候匹配 ---
def calculate_disease_match(symptom_keys, tongue_keys):
    all_keys = set(symptom_keys) | set(tongue_keys)
    scores = {}
    
    # 遍历 data_loader 里的疾病库
    for disease_name, rules in data_loader.DISEASE_DB.items():
        current_score = 0
        max_possible = 0
        
        # 核心症状加分 (权重高)
        for code in rules['core']:
            max_possible += 10
            if code in all_keys: current_score += 10
            
        # 次要症状加分 (权重低)
        for code in rules['side']:
            max_possible += 3
            if code in all_keys: current_score += 3

        if max_possible > 0:
            match_rate = int((current_score / max_possible) * 100)
            # 只有匹配度超过一定阈值才记录
            if match_rate > 15:
                scores[disease_name] = match_rate
                
    # 返回按分数排序的列表，例如 [('肝肾阴虚', 60), ('脾虚', 20)]
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


# --- 主逻辑: 诊断与回复 (已修复历史记忆与追问逻辑) ---
def get_diagnosis_and_reply(user_text, history, saved_context, current_image_features=None):
    # 1. 解析前端传来的 Context (恢复记忆)
    current_symptoms = saved_context.get("symptoms", {})
    current_tongue = saved_context.get("tongue", {})
    has_update = False

    # 2. 处理图像特征 (如果有图片上传)
    if current_image_features:
        for k, v in current_image_features.items():
            if k in ["tongue_substance", "tongue_coating"]:
                # 假设 v 是对应的特征 Code，存入舌象字典
                current_tongue[v] = 1
        has_update = True

    # 3. 处理文本提取 (从用户新输入中提取症状)
    if user_text:
        new_extracted = extract_complex_info(user_text)
        if new_extracted:
            # 合并新旧症状
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
    
    # 获取最高匹配项
    top_diagnosis, top_score = matches[0] if matches else ("暂无明显指向", 0)

    # 5. 生成 System Prompt (针对性优化)
    base_persona = """
    你是一位经验丰富、说话亲切的老中医。
    你的诊断风格是：**大胆假设，小心求证，但绝不啰嗦**。
    **重要提示**：请仔细阅读【对话历史】，不要重复询问已经问过的问题！
    如果不确定用户是否回答过，请先假设已经回答过。
    """

    if not matches:
        # 情况 A: 信息太少
        system_prompt = f"""
        {base_persona}
        目前用户症状太少，无法判断。
        【任务】：
        1. 结合【对话历史】，只提出 1 个 **还没问过** 的身体感受问题（比如“平时怕冷还是怕热”）。
        2. **严禁**列出清单（1.2.3...）。像聊天一样自然。
        """
    elif top_score < 50:
        # 情况 B: 有怀疑方向，但分不够
        system_prompt = f"""
        {base_persona}
        你初步怀疑是【{top_diagnosis}】（匹配度{top_score}%）。
        
        【回复策略】：
        1. 开门见山：直接告诉用户“从目前看，我怀疑你是{top_diagnosis}”。
        2. 单一追问：**只问 1 个**最关键的、且**历史记录里没问过**的问题来确认。
        3. 严禁一次问两个以上问题。
        """
    else:
        # 情况 C: 基本确诊
        system_prompt = f"""
        {base_persona}
        系统判定用户极大概率为【{top_diagnosis}】。
        【任务】：
        1. 告知诊断结果。
        2. 给出具体的调理建议（饮食、作息）。
        """

    # 6. 构建发给 DeepSeek 的完整消息链 (修复核心：注入历史)
    messages_payload = [{"role": "system", "content": system_prompt}]

    # 【修复点】：把历史记录加进去
    if history and isinstance(history, list):
        # 简单过滤，防止有非法格式
        valid_history = [
            h for h in history 
            if isinstance(h, dict) and 'role' in h and 'content' in h
        ]
        messages_payload.extend(valid_history)

    # 构造当前用户输入，带上已知症状作为强提示
    symptoms_desc = ", ".join([f"{k}:{v}" for k, v in current_symptoms.items()])
    final_user_content = f"""
    【系统记忆 - 当前已知症状】：{symptoms_desc}
    【用户本次回复】："{user_text}"
    """
    messages_payload.append({"role": "user", "content": final_user_content})

    # 7. 调用 DeepSeek
    try:
        reply_resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages_payload, # 这里现在包含了完整的上下文
            temperature=0.7 
        )
        ai_msg = reply_resp.choices[0].message.content
    except Exception as e:
        ai_msg = f"系统繁忙: {str(e)}"

    # 8. 返回结果
    # 构造新的 Context 结构返回给前端保存
    new_context_full = {
        "symptoms": current_symptoms,
        "tongue": current_tongue,
        "diagnosis": top_diagnosis
    }

    return DoctorResult(reply=ai_msg, new_info=new_context_full if has_update else None)