# llm_doctor.py
import json
import re
from openai import OpenAI
import data_loader

client = OpenAI(
    api_key="sk-aad791214f9441a9b5af19b6c63f1ed3",
    base_url="https://api.deepseek.com"
)


class DoctorResult:
    def __init__(self, reply, new_info=None):
        self.reply = reply
        self.new_info = new_info


# ==========================================
# PART 1: 基础工具 (队友的算分逻辑)
# ==========================================

def clean_excel_cell(cell_text):
    text = str(cell_text)
    text = text.replace("**", "")
    text = re.sub(r'\(.*?\)', '', text)  # 去掉英文括号
    text = re.sub(r'（.*?）', '', text)  # 去掉中文括号
    keywords = re.split(r'[;；,，、]', text)
    return [k.strip() for k in keywords if k.strip()]


def calculate_score_deterministic(table_key, user_symptoms):
    df = data_loader.get_table(table_key)
    if df.empty: return {}, []

    results = []
    for index, row in df.iterrows():
        score = 0
        matched_core = []
        matched_side = []
        missing_core = []

        pattern_name = row.get('辨证类型', '未知')
        core_list = clean_excel_cell(row.get('核心临床表现', ''))
        side_list = clean_excel_cell(row.get('可能/伴见表现', ''))

        # 1. 核心症状 (+10)
        for c_sym in core_list:
            is_found = False
            for u_sym in user_symptoms:
                if u_sym in c_sym or c_sym in u_sym:  # 简单的包含匹配
                    is_found = True
                    break
            if is_found:
                if c_sym not in matched_core:
                    score += 10
                    matched_core.append(c_sym)
            else:
                missing_core.append(c_sym)

        # 2. 伴见症状 (+3)
        for u_sym in user_symptoms:
            if any(u_sym in c or c in u_sym for c in core_list): continue
            for s_sym in side_list:
                if u_sym in s_sym or s_sym in u_sym:
                    if u_sym not in matched_side:
                        score += 3
                        matched_side.append(u_sym)
                    break

        if score > 0:
            results.append({
                "pattern": pattern_name,
                "score": score,
                "evidence_str": f"核心命中 {matched_core}，伴见命中 {matched_side}",
                "missing_core": missing_core
            })

    results.sort(key=lambda x: x['score'], reverse=True)
    score_dict = {r['pattern']: r['score'] for r in results}
    return score_dict, results


# ==========================================
# PART 2: 核心诊断逻辑
# ==========================================

def normalize_user_symptoms(user_text):
    """LLM 将口语转化为标准术语"""
    if not user_text: return []
    prompt = f"""
    你是一个中医术语标准化助手。
    【用户输入】: "{user_text}"
    【任务】: 将口语转化为标准中医术语列表 (尽量简短，如'舌红', '苔黄')。
    【输出】: 仅输出 JSON列表，如 ["恶寒", "发热"]，不要Markdown。
    """
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        content = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)
    except:
        return []


def run_diagnosis_pipeline(current_symptoms_list):
    """运行决策树: 八纲 -> 特定 -> 脏腑"""
    trace = []

    # 1. 八纲
    scores_8_dict, _ = calculate_score_deterministic('八纲', current_symptoms_list)
    s_biao = scores_8_dict.get('表证', 0)
    s_li = scores_8_dict.get('里证', 0)

    target_table_key = ""
    if s_biao >= s_li and s_biao > 0:
        trace.append("表证")
        s_han = scores_8_dict.get('寒证', 0)
        s_re = scores_8_dict.get('热证', 0)
        target_table_key = "六经" if s_han >= s_re else "卫气营血"
    else:
        trace.append("里证")
        s_xu = scores_8_dict.get('虚证', 0)
        s_shi = scores_8_dict.get('实证', 0)
        target_table_key = "气血津液" if s_xu >= s_shi else "病因"

    # 2. 特定辨证
    best_specific = None
    if target_table_key:
        _, spec_results = calculate_score_deterministic(target_table_key, current_symptoms_list)
        if spec_results: best_specific = spec_results[0]

    # 3. 脏腑辨证 (作为保底或补充)
    best_zangfu = None
    _, zangfu_results = calculate_score_deterministic('脏腑', current_symptoms_list)
    if zangfu_results: best_zangfu = zangfu_results[0]

    # 优先返回特定辨证，没有则返回脏腑
    return {"specific": best_specific, "organ": best_zangfu}


# ==========================================
# PART 3: 主交互入口 (融合增强版)
# ==========================================

def get_diagnosis_and_reply(user_text, history, saved_context, current_image_features=None):
    # --- 1. 数据准备 & 融合图像特征 ---

    # 从 Context 恢复之前的症状列表 (如果是第一次，就是一个空列表)
    # 注意：队友逻辑里 saved_context['symptoms'] 是个 List，不是 Dict 了
    current_symptoms_list = saved_context.get("symptoms", [])
    if not isinstance(current_symptoms_list, list): current_symptoms_list = []

    has_update = False

    # 【融合点 A】: 处理图像特征
    # 把 image_processor 返回的字典 (比如 {"tongue_color": "舌红"}) 压扁成列表
    if current_image_features:
        img_symptoms = []
        for k, v in current_image_features.items():
            # 过滤掉无关字段，只留特征值
            if isinstance(v, str) and len(v) < 10:  # 简单的保护
                img_symptoms.append(v)

        if img_symptoms:
            # 合并到总症状列表
            updated_set = set(current_symptoms_list) | set(img_symptoms)
            current_symptoms_list = list(updated_set)
            has_update = True

    # 【融合点 B】: 处理文本特征
    if user_text:
        new_symptoms = normalize_user_symptoms(user_text)
        if new_symptoms:
            updated_set = set(current_symptoms_list) | set(new_symptoms)
            current_symptoms_list = list(updated_set)
            has_update = True

    # 【融合点 C】: 获取用户信息 (Profile)
    user_profile = saved_context.get("profile", {})
    p_sex = user_profile.get("sex", "")
    p_age = str(user_profile.get("age", ""))
    profile_desc = f"患者信息：{p_sex} {p_age}岁。" if p_sex or p_age else ""

    # --- 2. 运行诊断引擎 ---
    diag_result = run_diagnosis_pipeline(current_symptoms_list)

    # 优先选 Specific (六经/卫气营血等)，其次选 Organ (脏腑)
    top_match = diag_result['specific'] or diag_result['organ']

    # --- 3. 构造 Prompt ---

    base_persona = f"""
    你是一位经验丰富的中医。{profile_desc}
    风格：亲切、专业、严谨。
    请仔细阅读【对话历史】，**绝对不要**重复询问用户已经回答过的问题。
    """

    diagnosis_status = "UNKNOWN"
    system_prompt = ""

    if not top_match:
        # A. 无方向 -> 八纲问诊
        system_prompt = f"""
        {base_persona}
        目前症状 ({current_symptoms_list}) 无法指向具体证候。
        请基于【八纲辨证】（表里、寒热、虚实），选择**一个**最不清楚的维度，用自然口语进行询问。
        例如：发病多久了？怕冷还是怕热？头痛吗？
        一次只问一个问题。
        """
    else:
        score = top_match['score']
        name = top_match['pattern']
        missing_symptoms = top_match.get('missing_core', [])
        missing_str = "、".join(missing_symptoms) if missing_symptoms else "无"

        if score < 40:
            # B. 疑似 -> 追问缺失核心
            diagnosis_status = "SUSPECTED"
            system_prompt = f"""
            {base_persona}
            【系统推断】：怀疑是【{name}】（匹配度 {score}分）。
            【缺失证据】：{missing_str}。

            任务：
            1. 告知怀疑方向。
            2. 验证假设：从【缺失证据】中挑 1-2 个点进行询问。
            例如：如果缺失“口苦”，问“嘴里苦吗？”
            """
        else:
            # C. 确诊 -> 建议
            diagnosis_status = "CONFIRMED"
            system_prompt = f"""
            {base_persona}
            【系统推断】：确诊为【{name}】（置信度高）。
            【依据】：{top_match['evidence_str']}。

            任务：
            1. 告知诊断结果及依据。
            2. 给出针对性的饮食、作息调理建议。
            """

    # --- 4. 调用 LLM 生成回复 ---
    messages_payload = [{"role": "system", "content": system_prompt}]

    if history and isinstance(history, list):
        for h in history:
            messages_payload.append({"role": h.get('role', 'user'), "content": str(h.get('content', ''))})

    final_user_input = f"【已知症状列表】：{current_symptoms_list}\n【用户最新输入】：{user_text}"
    messages_payload.append({"role": "user", "content": final_user_input})

    try:
        reply_resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages_payload,
            temperature=0.6
        )
        ai_reply = reply_resp.choices[0].message.content
    except Exception as e:
        ai_reply = f"系统繁忙，请重试。"

    # --- 5. 返回结果 ---
    # 构造新的 Context 给前端保存
    # 注意：symptoms 现在是一个 List，直接覆盖保存即可
    new_context = {
        "symptoms": current_symptoms_list,
        "last_diag_name": top_match['pattern'] if top_match else None,
        "status": diagnosis_status
    }

    # 这里的 profile 也要传回去吗？其实不需要，前端自己有。
    # 我们只传回我们会修改的部分。

    return DoctorResult(reply=ai_reply, new_info=new_context if has_update else None)