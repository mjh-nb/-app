# llm_doctor.py
import json
import re
import pandas as pd
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
# PART 1: 基础工具 (新增：计算缺失症状)
# ==========================================

def clean_excel_cell(cell_text):
    """清洗 Excel 单元格内容"""
    text = str(cell_text)
    text = text.replace("**", "")
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'（.*?）', '', text)
    keywords = re.split(r'[;；,，、]', text)
    return [k.strip() for k in keywords if k.strip()]

def calculate_score_deterministic(table_key, user_symptoms):
    """
    算分逻辑升级：
    除了计算得分，还计算 'missing_core' (缺失的核心症状)
    """
    df = data_loader.get_table(table_key)
    if df.empty: return {}, []
    
    results = []

    for index, row in df.iterrows():
        score = 0
        matched_core = []
        matched_side = []
        missing_core = [] # [新增] 用于存储缺失的核心症状
        
        pattern_name = row.get('辨证类型', '未知')
        core_list = clean_excel_cell(row.get('核心临床表现', ''))
        side_list = clean_excel_cell(row.get('可能/伴见表现', ''))

        # 1. 核心症状匹配 (+10)
        for c_sym in core_list:
            is_found = False
            for u_sym in user_symptoms:
                # 双向匹配
                if u_sym in c_sym or c_sym in u_sym:
                    is_found = True
                    break
            
            if is_found:
                # 避免同一个用户症状给多个核心词加分 (虽然一般不会)
                if c_sym not in matched_core: 
                    score += 10
                    matched_core.append(c_sym)
            else:
                # [新增] 没找到，记录为缺失
                missing_core.append(c_sym)

        # 2. 伴见症状匹配 (+3)
        for u_sym in user_symptoms:
            # 如果是核心词，跳过
            if any(u_sym in c or c in u_sym for c in core_list):
                continue
            
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
                "evidence_str": f"核心命中 {matched_core}(+10x{len(matched_core)})，伴见命中 {matched_side}(+3x{len(matched_side)})",
                "missing_core": missing_core  # [新增] 返回缺失列表
            })
    
    results.sort(key=lambda x: x['score'], reverse=True)
    score_dict = {r['pattern']: r['score'] for r in results}
    return score_dict, results

# ==========================================
# PART 2: 核心诊断逻辑 (不变)
# ==========================================

def normalize_user_symptoms(user_text):
    """LLM 语义提取"""
    if not user_text: return []
    prompt = f"""
    你是一个中医术语标准化助手。
    【用户输入】: "{user_text}"
    【任务】: 将口语转化为标准中医术语列表。
    【输出】: JSON列表，如 ["恶寒", "发热"]
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
    """运行决策树"""
    trace = []
    
    # 1. 八纲
    scores_8_dict, _ = calculate_score_deterministic('八纲', current_symptoms_list)
    s_biao = scores_8_dict.get('表证', 0)
    s_li = scores_8_dict.get('里证', 0)
    
    target_table_key = ""
    if s_biao >= s_li and s_biao > 0:
        trace.append("八纲：表证")
        s_han = scores_8_dict.get('寒证', 0)
        s_re = scores_8_dict.get('热证', 0)
        target_table_key = "六经" if s_han >= s_re else "卫气营血"
    else:
        trace.append("八纲：里证")
        s_xu = scores_8_dict.get('虚证', 0)
        s_shi = scores_8_dict.get('实证', 0)
        target_table_key = "气血津液" if s_xu >= s_shi else "病因"

    # 2. 特定辨证
    best_specific = None
    if target_table_key:
        _, spec_results = calculate_score_deterministic(target_table_key, current_symptoms_list)
        if spec_results:
            best_specific = spec_results[0]

    # 3. 脏腑辨证
    best_zangfu = None
    _, zangfu_results = calculate_score_deterministic('脏腑', current_symptoms_list)
    if zangfu_results:
        best_zangfu = zangfu_results[0]

    return {"specific": best_specific, "organ": best_zangfu}

# ==========================================
# PART 3: 主交互入口 (逻辑修改：定向追问)
# ==========================================

def get_diagnosis_and_reply(user_text, history, saved_context, current_image_features=None):
    # 1. 上下文恢复
    current_symptoms_list = saved_context.get("symptoms", [])
    if not isinstance(current_symptoms_list, list): current_symptoms_list = []
    has_update = False

    # 2. 症状更新
    if user_text:
        new_symptoms = normalize_user_symptoms(user_text)
        if new_symptoms:
            updated_set = set(current_symptoms_list) | set(new_symptoms)
            current_symptoms_list = list(updated_set)
            has_update = True

    # 3. 诊断
    diag_result = run_diagnosis_pipeline(current_symptoms_list)
    top_match = diag_result['specific'] or diag_result['organ']
    
    # 4. Prompt 构建
    base_persona = """
    你是一位经验丰富的中医。风格：亲切、专业、严谨。
    请仔细阅读【对话历史】，**绝对不要**重复询问用户已经回答过的问题。
    """
    
    diagnosis_status = "UNKNOWN"

    if not top_match:
        # ============================================================
        # A. 无方向 -> 改为【八纲定性】问诊
        # ============================================================
        system_prompt = f"""
        {base_persona}
        目前用户提供的症状 ({current_symptoms_list}) 过于稀缺，无法指向具体的脏腑或病邪。
        此时需要先进行【八纲辨证】（表里、寒热、虚实）的定性。
        
        【任务】：
        请基于“八纲辨证”的逻辑，选择 **一个** 目前最不清楚的维度进行自然询问。
        
        参考问诊方向（仅供参考，请转化为口语）：
        1. **辨表里**：如果有头痛/恶寒/发热，优先问这些（判断病位深浅）。
        2. **辨寒热**：问平时怕冷还是怕热？口渴吗？喜欢喝热水还是冷水？小便颜色清还是黄？
        3. **辨虚实**：问发病多久了？是感觉身体沉重乏力（虚），还是疼痛剧烈、按压更痛（实）？
        
        **要求**：
        1. 像老医生聊天一样自然，**不要**暴露“我要辨别八纲”这种术语。
        2. **一次只问 1 个** 维度的相关问题，不要堆砌问题。
        """
    else:
        score = top_match['score']
        name = top_match['pattern']
        missing_symptoms = top_match.get('missing_core', []) # 获取缺失的核心症状
        
        # 转换成字符串供Prompt使用
        missing_str = "、".join(missing_symptoms) if missing_symptoms else "无"

        if score < 40: # 阈值 (比如40分才算比较稳)
            # B. 疑似 -> 定向追问 [核心修改点]
            diagnosis_status = "SUSPECTED"
            system_prompt = f"""
            {base_persona}
            【系统诊断现状】：
            1. 最怀疑证型：【{name}】（匹配度 {score}分，尚未达到确诊标准）。
            2. 已有证据：{top_match['evidence_str']}。
            3. **缺失的核心证据**：【{missing_str}】。
            
            【任务】：
            1. 告知用户你怀疑是“{name}”方向。
            2. **验证假设**：从上述【缺失的核心证据】中，挑选 1-2 个最关键的症状进行询问。
            例如：如果缺失“口苦”，就问“平时嘴里会有苦味吗？”
            3. 严禁询问与该证型无关的问题，严禁重复历史记录里问过的问题。
            """
        else:
            # C. 确诊 -> 建议
            diagnosis_status = "CONFIRMED"
            system_prompt = f"""
            {base_persona}
            【系统诊断结论】：
            确诊为【{name}】（得分 {score}，置信度高）。
            依据：{top_match['evidence_str']}。
            
            【任务】：
            1. 清晰告知诊断结果。
            2. 解释为什么是这个病（引用上述依据）。
            3. 给出针对【{name}】的饮食、作息建议。
            """

    # 5. 组装消息
    messages_payload = [{"role": "system", "content": system_prompt}]
    
    if history and isinstance(history, list):
        for h in history:
            if isinstance(h, dict) and h.get('role') in ['user', 'assistant']:
                messages_payload.append({"role": h['role'], "content": str(h['content'])})

    final_user_input = f"【已知症状】：{current_symptoms_list}\n【用户输入】：{user_text}"
    messages_payload.append({"role": "user", "content": final_user_input})

    # 6. 调用
    try:
        reply_resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages_payload,
            temperature=0.6 # 稍微降低温度，让它严格执行提问指令
        )
        ai_reply = reply_resp.choices[0].message.content
    except Exception as e:
        ai_reply = f"系统繁忙: {e}"

    # 7. 返回
    new_context = {
        "symptoms": current_symptoms_list,
        "last_diag_name": top_match['pattern'] if top_match else None,
        "status": diagnosis_status
    }

    return DoctorResult(reply=ai_reply, new_info=new_context if has_update else None)