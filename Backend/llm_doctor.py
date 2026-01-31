# llm_doctor.py
import json
import re
import pandas as pd
import os
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
# PART 1: 基础工具 (超详细 Debug 版)
# ==========================================

# ==========================================
# PART 1: 基础工具 (升级版数据清洗)
# ==========================================

def remove_markdown_symbol(text):
    if not text: return ""
    # 去除 **加粗**
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    # 去除 *斜体*
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    # 去除标题和链接
    text = text.replace("##", "").replace("#", "")
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    return text

def clean_excel_cell(cell_text):
    text = str(cell_text)
    
    # 1. 去除 Markdown 加粗
    text = text.replace("**", "")
    
    # 2. 【核心修复】去除中英文方括号及内容 [12] [34,35]
    #    这能解决你遇到的 ['[34', '35]。'] 问题
    text = re.sub(r'\[.*?\]', '', text) 
    
    # 3. 去除中英文圆括号及内容 (解释) （说明）
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'（.*?）', '', text)
    
    # 4. 【核心修复】去除句号和其他标点干扰
    text = text.replace("。", "").replace(".", "")
    
    # 5. 按各种分隔符切分 (分号、逗号、顿号、空格)
    keywords = re.split(r'[;；,，、\s]+', text)
    
    # 6. 再次清洗并过滤空值
    return [k.strip() for k in keywords if k.strip()]

def calculate_score_deterministic(table_key, user_symptoms_synonyms):
    """
    带详细日志的算分函数
    """
    df = data_loader.get_table(table_key)
    
    # === [Debug] 打印读取状态 ===
    print(f"\n   🔎 [Debug-Deep] 正在扫描表格: <{table_key}>")
    if df.empty:
        print(f"   ❌ [Error] 表格为空或未加载! 请检查 data_loader.py")
        return {}, []
    else:
        print(f"   📄 [Info] 表格包含 {len(df)} 行数据。")
        # 打印第一行数据，检查列名是否正确
        first_row = df.iloc[0].to_dict()
        print(f"   📄 [Info] 表头示例: {list(first_row.keys())}")
    # =============================

    results = []
    
    # 遍历每一行（每一个证型）
    for index, row in df.iterrows():
        score = 0
        matched_core = []
        unknown_core = [] 
        
        # 获取列内容（带容错处理）
        pattern_name = row.get('辨证类型', '未知证型')
        raw_core = str(row.get('核心临床表现（含判断关键）', ''))
        raw_side = str(row.get('可能/伴见表现', ''))
        
        core_list = clean_excel_cell(raw_core)
        side_list = clean_excel_cell(raw_side)

        # --- 1. 核心症状逻辑 ---
        for c_sym in core_list:
            is_found = False
            matched_word = ""
            
            for u_word in user_symptoms_synonyms:
                if not isinstance(u_word, str): continue
                # 双向匹配
                if u_word in c_sym or c_sym in u_word:
                    is_found = True
                    matched_word = u_word
                    break
            
            if is_found:
                if c_sym not in matched_core:
                    score += 10
                    matched_core.append(c_sym)
                    # === [Debug] 打印命中详情 ===
                    print(f"      ✅ [Hit] 用户词'{matched_word}' 命中 <{pattern_name}> 的核心词 '{c_sym}' (+10分)")
            else:
                unknown_core.append(c_sym)

        # --- 2. 伴见症状逻辑 ---
        for u_word in user_symptoms_synonyms:
            if not isinstance(u_word, str): continue
            if any(u_word in c or c in u_word for c in core_list): continue
            
            for s_sym in side_list:
                if u_word in s_sym or s_sym in u_word:
                    score += 5
                    # === [Debug] 打印命中详情 ===
                    print(f"      ☑️ [Side] 用户词'{u_word}' 命中 <{pattern_name}> 的伴见词 '{s_sym}' (+5分)")
                    break

        if score > 0: 
            results.append({
                "pattern": pattern_name,
                "score": score,
                "evidence_str": f"已确认核心症状：{matched_core}",
                "unknown_core": unknown_core, 
                "is_fully_explored": len(unknown_core) == 0 
            })

    results.sort(key=lambda x: x['score'], reverse=True)
    score_dict = {r['pattern']: r['score'] for r in results}
    return score_dict, results

# ==========================================
# PART 2: 核心诊断逻辑 (LLM 泛化同义词)
# ==========================================

# ==========================================
# PART 2: 核心诊断逻辑 (修复版：匹配主逻辑的双列表要求)
# ==========================================

def normalize_user_symptoms(user_text, history):
    # 1. 获取上一句 AI 的话，解决“对对对”的问题
    last_ai_msg = "无"
    if history and len(history) > 0:
        for msg in reversed(history):
            if msg.get('role') == 'assistant':
                last_ai_msg = msg.get('content', '')
                break

    if not user_text: return {"pos": [], "neg": []}
    
    prompt = f"""
    你是一个中医术语转换器。
    【上下文】：医生问="{last_ai_msg}"，患者答="{user_text}"
    
    【任务】：
    1. 分析患者【确认有】的症状，放入 "pos" 列表。
       ⚠️ 必须包含同义词！(为了匹配表格)
       例如：确认有"怕冷"，pos=["怕冷", "恶寒", "畏寒", "肢冷"]。
       
    2. 分析患者【确认无/排除】的症状，放入 "neg" 列表。
    
    【输出】：JSON 对象 {{ "pos": [], "neg": [] }}
    """
    try:
        response = client.chat.completions.create(
            model="deepseek-chat", messages=[{"role": "user", "content": prompt}], temperature=0.1
        )
        content = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)
        # 打印一下看看提取到了什么
        print(f"🧠 [Debug-LLM] 提取结果: {result}")
        return result
    except Exception as e:
        print(f"🧠 [Debug-LLM] 提取失败: {e}")
        return {"pos": [], "neg": []}

def run_diagnosis_pipeline(symptoms_list):
    print(f"\n🚀 [Debug-Pipeline] 开始全表扫描，当前症状池({len(symptoms_list)}个): {symptoms_list}")
    
    # 1. 跑八纲
    scores_8_dict, _ = calculate_score_deterministic('八纲', symptoms_list)
    
    s_biao = scores_8_dict.get('表证', 0)
    s_li = scores_8_dict.get('里证', 0)
    s_han = scores_8_dict.get('寒证', 0)
    s_re = scores_8_dict.get('热证', 0)
    s_xu = scores_8_dict.get('虚证', 0)
    s_shi = scores_8_dict.get('实证', 0)

    print(f"   ⚖️ [Debug-八纲] 表:{s_biao} vs 里:{s_li} | 寒:{s_han} vs 热:{s_re} | 虚:{s_xu} vs 实:{s_shi}")

    # 2. 选表逻辑
    target_table_key = ""
    if s_biao >= s_li and s_biao > 0:
        target_table_key = "六经" if s_han >= s_re else "卫气营血"
    else:
        # 如果里证大，或者都没分(默认里)
        target_table_key = "气血津液" if s_xu >= s_shi else "病因"

    print(f"   👉 [Debug-选表] 根据八纲结果，决定进入: <{target_table_key}辨证表>")

    # 3. 跑具体表
    specific_results = []
    if target_table_key:
        _, specific_results = calculate_score_deterministic(target_table_key, symptoms_list)

    # 4. 跑脏腑表
    _, zangfu_results = calculate_score_deterministic('脏腑', symptoms_list)

    return {
        "specific_list": specific_results,
        "organ_list": zangfu_results
    }

# ==========================================
# PART 2.5: 方剂推荐逻辑
# ==========================================

def recommend_prescription_pipeline(user_symptoms):
    print(f"\n💊 [Debug-选方] 开始执行方剂推荐...")
    KNOWN_CHAPTER_FILES = [
        "方剂学/第一章解表剂.xlsx", "方剂学/第二章泻下剂.xlsx", "方剂学/第三章和解剂.xlsx",
        "方剂学/第四章清热剂.xlsx", "方剂学/第五章祛暑剂.xlsx", "方剂学/第六章温里剂.xlsx",
        "方剂学/第七章表里双解剂.xlsx", "方剂学/第八章补益剂.xlsx", "方剂学/第九章固涩剂.xlsx",
        "方剂学/第十章安神剂.xlsx", "方剂学/第十一章开窍剂.xlsx", "方剂学/第十二章理气剂.xlsx",
        "方剂学/第十三章理血剂.xlsx", "方剂学/第十四章治风剂.xlsx", "方剂学/第十五章治燥剂.xlsx",
        "方剂学/第十六章祛湿剂.xlsx", "方剂学/第十七章祛痰剂.xlsx", "方剂学/第十八章消食剂.xlsx",
        "方剂学/第十九章驱虫剂.xlsx", "方剂学/第二十章涌吐剂.xlsx", "方剂学/第二十一章治疡剂.xlsx"
    ]

    try:
        df_index = pd.read_excel('方剂学/方剂学查询表.xlsx').fillna("")
    except Exception as e:
        print(f"❌ [Debug-选方] 索引表读取失败: {e}")
        return None

    best_chapter_target = ""
    max_chapter_score = -1

    for idx, row in df_index.iterrows():
        chapter_keywords = clean_excel_cell(row.get('核心症状/证候表现', ''))
        chapter_name = str(row.get('对应查找章节', '')).strip()
        current_score = 0
        for u_sym in user_symptoms:
            if not isinstance(u_sym, str): continue
            for k_sym in chapter_keywords:
                if u_sym in k_sym or k_sym in u_sym: current_score += 1
        if current_score > max_chapter_score and current_score > 0:
            max_chapter_score = current_score
            best_chapter_target = chapter_name

    if not best_chapter_target:
        print(f"❌ [Debug-选方] 未匹配到任何章节。")
        return None 

    print(f"✅ [Debug-选方] 锁定章节: 【{best_chapter_target}】")

    target_filename = ""
    clean_target = best_chapter_target.replace(" ", "")
    for fname in KNOWN_CHAPTER_FILES:
        if clean_target in fname:
            target_filename = fname
            break
            
    if not target_filename or not os.path.exists(target_filename): return None

    try:
        df_chapter = pd.read_excel(target_filename).fillna("")
        df_chapter.columns = df_chapter.columns.str.strip()
    except: return None

    candidates = []
    for idx, row in df_chapter.iterrows():
        rx_name = str(row.get('方剂名称', ''))
        core_symptoms = clean_excel_cell(row.get('核心临床表现', ''))
        score = 0
        matched = []
        for u_sym in user_symptoms:
            if not isinstance(u_sym, str): continue
            for c_sym in core_symptoms:
                if u_sym in c_sym or c_sym in u_sym:
                    score += 10
                    matched.append(u_sym)
                    break 
        if score > 0:
            candidates.append({"row_data": row, "score": score, "matched": matched})

    if not candidates: return None

    candidates.sort(key=lambda x: x['score'], reverse=True)
    winner = candidates[0]
    row_winner = winner['row_data']
    print(f"🏆 [Debug-选方] 胜出: {row_winner.get('方剂名称')}")
    
    rx_name = str(row_winner.get('方剂名称', ''))
    rx_type = str(row_winner.get('正附分类', '正方')).strip()
    rx_ingredients = str(row_winner.get('具体成分', '暂无'))
    
    final_output = {
        "name": rx_name, "ingredients": rx_ingredients,
        "reason": f"症状命中：{winner['matched']}",
        "is_attached": False, "main_rx": None
    }

    if "附方" in rx_type:
        main_name = str(row_winner.get('对应主方', '')).strip()
        final_output["is_attached"] = True
        final_output["main_rx_name"] = main_name
        main_row_df = df_chapter[df_chapter['方剂名称'] == main_name]
        if not main_row_df.empty:
            final_output["main_rx"] = {"name": main_name, "ingredients": str(main_row_df.iloc[0].get('具体成分', ''))}
        else:
            final_output["main_rx"] = {"name": main_name, "ingredients": "未知"}

    return final_output

# ==========================================
# PART 3: 主交互入口 (压平逻辑 + 分支打印)
# ==========================================

def get_diagnosis_and_reply(user_text, history, saved_context, current_image_features=None):
    # --- 1. 恢复记忆 ---
    current_symptoms = saved_context.get("symptoms", [])
    if not isinstance(current_symptoms, list): current_symptoms = []

    has_update = False

    # --- 2. 图像融合 ---
    if current_image_features:
        img_symptoms = [v for k,v in current_image_features.items() if isinstance(v, str) and len(v)<10]
        if img_symptoms:
            for s in img_symptoms:
                if s not in current_symptoms: current_symptoms.append(s)
            has_update = True

    # --- 3. 文本更新 ---
    if user_text:
        extracted = normalize_user_symptoms(user_text,history)
        to_add_raw = extracted.get("pos", [])
        to_remove_raw = extracted.get("neg", [])

        # 压平逻辑
        def flatten_and_clean(raw_list):
            flat = []
            for item in raw_list:
                if isinstance(item, list):
                    for sub in item:
                        if isinstance(sub, str): flat.append(sub)
                elif isinstance(item, str):
                    flat.append(item)
            return flat

        new_pos = flatten_and_clean(to_add_raw)
        new_neg = flatten_and_clean(to_remove_raw)

        if new_pos or new_neg:
            for n in new_neg:
                current_symptoms = [s for s in current_symptoms if n not in s and s not in n]
            for p in new_pos:
                if p not in current_symptoms: current_symptoms.append(p)
            has_update = True
    
    # --- 4. 运行诊断 ---
    diag_result = run_diagnosis_pipeline(current_symptoms)
    candidates = diag_result['specific_list'] + diag_result['organ_list']
    candidates.sort(key=lambda x: x['score'], reverse=True)
    
    top_candidate = candidates[0] if candidates else None

    # --- 5. 决策逻辑 (穷尽 1 -> 开方) ---
    final_decision = None 
    target_to_ask = None
    CONFIRM_THRESHOLD = 25 

    # === [Debug] 打印当前决策状态 ===
    print(f"\n🎯 [Debug-决策中心]")
    if top_candidate:
        print(f"   当前第一名: 【{top_candidate['pattern']}】")
        print(f"   当前分数: {top_candidate['score']} (目标: {CONFIRM_THRESHOLD})")
        print(f"   是否问完: {top_candidate['is_fully_explored']}")
        print(f"   剩余核心症状: {top_candidate['unknown_core']}")
    else:
        print(f"   ⚠️ 当前无匹配候选项 (所有表评分均为0)")
    # ==============================

    if not top_candidate:
        print(f"👉 进入分支: [C. 无方向]")
        pass 
    else:
        if top_candidate['score'] >= CONFIRM_THRESHOLD:
            print(f"👉 进入分支: [A. 确诊 (分数达标)]")
            final_decision = top_candidate
        
        elif not top_candidate['is_fully_explored']:
            print(f"👉 进入分支: [B. 追问 (继续问第一名)]")
            target_to_ask = top_candidate
            
        else:
            print(f"👉 进入分支: [A. 确诊 (强制确诊)]")
            final_decision = top_candidate

    # --- 6. 构建 Prompt ---
    user_profile = saved_context.get("profile", {})
    p_sex = user_profile.get("sex", "")
    p_age = str(user_profile.get("age", ""))
    profile_desc = f"患者信息：{p_sex} {p_age}岁。" if p_sex or p_age else ""

    base_persona = f"""
    你是一位经验丰富的中医。{profile_desc}
    风格：亲切、专业、严谨。
    请仔细阅读【对话历史】，不要重复询问用户已经回答过的问题。

    ⚠️【格式严格要求】：
    1. **绝对禁止**使用Markdown格式。
    2. **不要**使用 **加粗**、# 标题 等符号。
    3. 仅输出纯文本，就像微信聊天一样。
    """

    if final_decision:
        diagnosis_status = "CONFIRMED"
        rx_result = recommend_prescription_pipeline(current_symptoms)
        
        rx_text = "暂无匹配方剂"
        if rx_result:
            if rx_result['is_attached']:
                main_info = rx_result['main_rx']
                rx_text = f"推荐方剂：【{rx_result['name']}】（{rx_result['main_rx_name']}的附方）。\n组成：{rx_result['ingredients']}\n主方组成：{main_info['ingredients']}"
            else:
                rx_text = f"推荐方剂：【{rx_result['name']}】。\n组成：{rx_result['ingredients']}"

        forced_msg = ""
        if final_decision['score'] < CONFIRM_THRESHOLD:
            forced_msg = "(注：虽然典型症状不全，但已排除其他可能性，倾向于此)"

        system_prompt = f"""
        {base_persona}
        【结论】：确诊为【{final_decision['pattern']}】{forced_msg}。
        【依据】：{final_decision['evidence_str']}。
        【选方】：{rx_text}
        
        任务：
        1. 告知结果。
        2. 解释原因。
        3. 介绍方剂。
        4. 给建议。
        5. 提醒遵医嘱,提醒该诊断仅供参考。
        """

    elif target_to_ask:
        diagnosis_status = "ASKING"
        name = target_to_ask['pattern']
        unknowns = target_to_ask['unknown_core']
        ask_focus = unknowns[:2] 
        ask_str = "、".join(ask_focus)

        system_prompt = f"""
        {base_persona}
        【当前状态】：数据收集阶段 (INVESTIGATING)。
        【推断】：怀疑是【{name}】（{target_to_ask['score']}分）。
        【缺失】：{ask_str}。

        任务：
        1. 告知怀疑方向。
        2. 询问缺失症状。
        ⚠️ 严禁诊断：现在还不是确诊的时候，禁止说“你得了XX病”。
        ⚠️ 严禁建议：现在不要给治疗建议。
        """

    else:
        diagnosis_status = "UNKNOWN"
        system_prompt = f"""
        {base_persona}
        目前症状 ({current_symptoms}) 无法定位。
        请基于八纲（寒热/表里/虚实），选择一到两个维度询问。
        """

    # --- 7. 调用 LLM ---
    messages_payload = [{"role": "system", "content": system_prompt}]
    if history:
        for h in history:
            messages_payload.append({"role": h.get('role', 'user'), "content": str(h.get('content', ''))})
    
    final_input = f"【已知症状】：{current_symptoms}\n【用户输入】：{user_text}"
    messages_payload.append({"role": "user", "content": final_input})

    try:
        reply_resp = client.chat.completions.create(
            model="deepseek-chat", messages=messages_payload, temperature=0.6
        )
        ai_reply = reply_resp.choices[0].message.content

        ai_reply = remove_markdown_symbol(ai_reply)
    except Exception as e:
        ai_reply = f"系统繁忙: {e}"

    # --- 8. 保存记忆 ---
    new_context = {
        "symptoms": current_symptoms, 
        "last_diag_name": final_decision['pattern'] if final_decision else (target_to_ask['pattern'] if target_to_ask else None),
        "status": diagnosis_status
    }
    
    return DoctorResult(reply=ai_reply, new_info=new_context if has_update else None)