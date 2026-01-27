import streamlit as st
import llm_doctor
import data_loader

# === 1. 初始化页面配置 ===
st.set_page_config(page_title="老中医 AI 诊室", layout="wide")
st.title("🤖 中医智能辨证系统 (Debug 面板)")

# === 2. 加载数据 (只执行一次) ===
@st.cache_resource
def init_system():
    data_loader.load_all_data()
    return "System Loaded"

init_system()

# === 3. 初始化 Session State (记忆) ===
if "history" not in st.session_state:
    st.session_state.history = []
if "context" not in st.session_state:
    st.session_state.context = {} # 存储症状、诊断状态

# === 4. 侧边栏：显示后台数据 (核心 Debug 功能) ===
with st.sidebar:
    st.header("🧠 大脑记忆 (Context)")
    st.info("这里显示后台提取到的症状和状态")
    
    # 实时显示症状列表
    current_symptoms = st.session_state.context.get("symptoms", [])
    st.write("📋 **当前已知症状:**")
    st.json(current_symptoms)
    
    # 显示当前诊断状态
    st.write("🩺 **当前诊断结论:**")
    st.write(st.session_state.context.get("last_diag_name", "暂无"))
    
    # 按钮：清空记忆
    if st.button("🗑️ 清空重来"):
        st.session_state.history = []
        st.session_state.context = {}
        st.rerun()

# === 5. 聊天主界面 ===
# 渲染历史消息
for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 处理用户输入
if prompt := st.chat_input("请描述你的症状（例如：头痛，怕冷...）"):
    # 1. 显示用户消息
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.history.append({"role": "user", "content": prompt})

    # 2. 调用后端逻辑 (你的 llm_doctor.py)
    with st.spinner("老中医正在思考..."):
        result = llm_doctor.get_diagnosis_and_reply(
            user_text=prompt,
            history=st.session_state.history,
            saved_context=st.session_state.context
        )

    # 3. 更新记忆
    if result.new_info:
        st.session_state.context = result.new_info

    # 4. 显示 AI 回复
    with st.chat_message("assistant"):
        st.markdown(result.reply)
    st.session_state.history.append({"role": "assistant", "content": result.reply})

    # 5. 强制刷新页面以更新侧边栏数据
    st.rerun()