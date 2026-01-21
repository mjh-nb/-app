# main.py - 完整的中医AI后端逻辑 (基于复杂症状提取 & 证候匹配)

from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Dict, Optional, List, Union
import pandas as pd
from openai import OpenAI
import json
import uvicorn

# --- 1. 初始化配置 ---
app = FastAPI()

# 替换你的 API Key
client = OpenAI(
    api_key="sk-aad791214f9441a9b5af19b6c63f1ed3", 
    base_url="https://api.deepseek.com"
)

# --- 全局数据容器 ---
SYMPTOM_SCHEMA = {}   # 给 LLM 看的定义
ID_TO_CODE_MAP = {}   # ID(TF01) -> Code(Headache)
DISEASE_DB = {}       # 证候匹配规则库

# --- 2. 核心数据加载模块 ---

def load_all_data(symptom_file="rules.xlsx", disease_file="diseases.xlsx", tongue_file="tongue.xlsx"):
    print("🚀 正在初始化系统数据...")
    
    global SYMPTOM_SCHEMA, ID_TO_CODE_MAP, DISEASE_DB
    
    # === 第一步：加载症状定义 (rules.xlsx) ===
    try:
        df_sym = pd.read_excel(symptom_file).fillna("")
        for _, row in df_sym.iterrows():
            # 假设表头是 '症状编码' 和 '症状英文'
            # 如果你的表头名字不一样，请在这里修改 string 里的名字
            s_id = str(row.get('症状编码', '')).strip() 
            s_code = str(row.get('症状英文', '')).strip()
            
            # 如果英文为空，就用中文当 Code
            if not s_code: 
                s_code = str(row.get('症状中文', '')).strip()

            # 建立 ID -> Code 映射
            if s_id:
                ID_TO_CODE_MAP[s_id] = s_code
            
            # 解析3个维度及其选项
            dims = []
            options = []
            for i in range(1, 4):
                dim_name = str(row.get(f'采集维度{i}', '')).strip()
                opt_str = str(row.get(f'选项{i}', '')).strip()
                
                if dim_name:
                    dims.append(dim_name)
                    options.append(opt_str.split(';') if opt_str else [])
            
            SYMPTOM_SCHEMA[s_code] = {
                "dims": dims,      
                "options": options 
            }
        print(f"✅ 加载了 {len(SYMPTOM_SCHEMA)} 个症状定义")
            
    except Exception as e:
        print(f"❌ 加载症状表失败: {e}")

    # === 【新增】第二步：加载舌象定义 (tongue.xlsx) ===
    try:
        # 假设你的舌象文件叫 tongue.xlsx
        df_tongue = pd.read_excel(tongue_file).fillna("")
        print(f"👅 正在加载舌象库...")
        
        for _, row in df_tongue.iterrows():
            t_id = str(row.get('症状编码', '')).strip()
            # 优先读英文代码，如果没有就读中文名称
            t_code = str(row.get('英文代码', '')).strip()
            if not t_code:
                t_code = str(row.get('症状名称', '')).strip()
                
            # 存入全局映射表：以后看到 TS01 就知道它是 PaleRed
            if t_id:
                ID_TO_CODE_MAP[t_id] = t_code
                
        print(f"✅ 加载了 {len(df_tongue)} 条舌象定义")
        
    except Exception as e:
        # 如果没有舌象表，不影响主程序运行，只是报个错
        print(f"⚠️ 舌象表加载跳过: {e}")

    # === 第三步：加载证候定义 (diseases.xlsx) ===
    try:
        df_dis = pd.read_excel(disease_file).fillna("")
        for _, row in df_dis.iterrows():
            d_name = row['证候名称']
            
            # 解析核心症状 (字符串 "TF01;XF03" -> 列表)
            # 并把 ID 翻译成 英文Code
            core_raw = str(row.get('核心症状编码', '')).split(';')
            side_raw = str(row.get('非核心症状编码', '')).split(';')
            
            core_codes = [ID_TO_CODE_MAP.get(pid.strip(), pid.strip()) for pid in core_raw if pid.strip()]
            side_codes = [ID_TO_CODE_MAP.get(pid.strip(), pid.strip()) for pid in side_raw if pid.strip()]
            
            DISEASE_DB[d_name] = {
                "core": core_codes, 
                "side": side_codes
            }
            
        print(f"✅ 成功加载 {len(DISEASE_DB)} 种证候规则")
        
    except Exception as e:
        print(f"❌ 加载证候表失败: {e}")

# 启动时执行加载
load_all_data()


# --- 3. 定义数据模型 ---

class SymptomState(BaseModel):
    # Key: 症状英文名 (Headache)
    # Value: 详情字典 {"部位": "前额", "性质": "胀痛"}
    data: Dict[str, Dict[str, str]] = Field(default_factory=dict)

class TongueState(BaseModel):
    # Key: 舌象英文名 (yellow_coating)
    # Value: 1 (存在)
    data: Dict[str, int] = Field(default_factory=dict)

class ChatRequest(BaseModel):
    user_text: str = ""                         
    history_symptoms: SymptomState              
    history_tongue: TongueState                 
    new_tongue_image_base64: Optional[str] = None 


# --- 4. 功能模块 ---

# 模块 A: 模拟舌象识别
def recognize_tongue(base64_str):
    print("🤖 (B模块) 正在识别舌象...")
    # TODO: 这里接 B 队友的代码
    return ["Thin white coating"] 

# 模块 B: 用 LLM 提取复杂信息
def extract_complex_info(user_text):
    if not user_text: return {}

    # 构造精简 Schema
    schema_prompt = {}
    for code, info in SYMPTOM_SCHEMA.items():
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
    3. 如果用户没提到的维度，留空。
    4. 严禁编造，只提取原文提到的信息。
    
    【输出格式 (JSON)】:
    {{
        "Headache": {{ "部位": "前额", "性质": "胀痛" }},
        "Cough": {{ "痰液": "无痰" }}
    }}
    没有提取到则返回 {{}}。不要Markdown格式。
    """

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            stream=False
        )
        raw = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        # 有时候 LLM 会返回空字符串
        if not raw: return {}
        return json.loads(raw)
    except Exception as e:
        print(f"LLM 提取出错: {e}")
        return {}

# 模块 C: 证候匹配引擎
def calculate_disease_match(user_symptoms_keys: list, user_tongue_keys: list):
    """
    输入：['Headache', 'Cold'], ['yellow_coating']
    输出：[('肝郁气滞证', 85), ('脾气虚证', 20)...]
    """
    all_keys = set(user_symptoms_keys) | set(user_tongue_keys)
    scores = {}
    
    for disease_name, rules in DISEASE_DB.items():
        current_score = 0
        max_possible = 0
        
        # 核心症状 (权重 10)
        for code in rules['core']:
            max_possible += 10
            if code in all_keys:
                current_score += 10
        
        # 非核心症状 (权重 3)
        for code in rules['side']:
            max_possible += 3
            if code in all_keys:
                current_score += 3
        
        if max_possible > 0:
            match_rate = int((current_score / max_possible) * 100)
            if match_rate > 15: # 门槛：匹配度大于15%才显示
                scores[disease_name] = match_rate
                
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


# --- 5. 主接口 ---
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    print(f"\n📩 收到新消息: {request.user_text}")
    
    current_symptoms = request.history_symptoms.data
    current_tongue = request.history_tongue.data
    
    # 1. 视觉识别 (如有)
    if request.new_tongue_image_base64:
        identified_tags = recognize_tongue(request.new_tongue_image_base64)
        for tag in identified_tags:
            current_tongue[tag] = 1 
            print(f"📸 识别舌象: {tag}")
            
    # 2. 文本提取 (如有)
    if request.user_text:
        new_extracted = extract_complex_info(request.user_text)
        print(f"📝 提取信息: {new_extracted}")
        
        # 更新历史症状 (合并字典)
        for code, details in new_extracted.items():
            # 如果之前没有这个症状，或者有更新
            if code not in current_symptoms:
                current_symptoms[code] = details
            else:
                # 简单的合并逻辑：新提取的覆盖旧的
                current_symptoms[code].update(details)

    # 3. 证候匹配
    # 我们只关心 Key (症状名)，用来去匹配证候
    symptom_keys = list(current_symptoms.keys())
    tongue_keys = list(current_tongue.keys())
    
    matches = calculate_disease_match(symptom_keys, tongue_keys)
    
    # 4. 决定 AI 回复逻辑
    if not matches:
        top_diagnosis = "未匹配到明显证候"
        system_prompt = "你是一个中医助手。用户目前症状信息不足。请引导用户多描述一些身体感受。"
    else:
        top_diagnosis, top_score = matches[0]
        print(f"📊 最高匹配: {top_diagnosis} ({top_score}%)")
        
        if top_score < 40:
            # 匹配度低 -> 追问
            system_prompt = f"你是一个中医助手。目前最怀疑是【{top_diagnosis}】，但匹配度不高。请根据该证候的典型症状进行追问。"
        else:
            # 匹配度高 -> 下诊断
            system_prompt = f"你是一个老中医。系统诊断用户为【{top_diagnosis}】。请给出该证型的解释和调理建议。不要直接说'确诊'，要说'疑似'。"

    # 5. 生成最终回复
    try:
        reply_resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"用户当前症状：{current_symptoms}。用户刚才说：{request.user_text}"}
            ]
        )
        ai_msg = reply_resp.choices[0].message.content
    except Exception as e:
        ai_msg = "系统繁忙，请稍后再试。"

    # 6. 返回
    return {
        "reply_text": ai_msg,
        "updated_symptoms": current_symptoms, 
        "updated_tongue": current_tongue,
        "diagnosis_list": matches # 前端可以把这个列表展示出来
    }

if __name__ == "__main__":
    uvicorn.run(app, host="192.168.1.7", port=8000)