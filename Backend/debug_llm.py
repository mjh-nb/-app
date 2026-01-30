import streamlit as st
import llm_doctor
import data_loader
import io
import contextlib # 引入捕获输出的库

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
    st.session_state.context = {} 
if "last_logs" not in st.session_state:
    st.session_state.last_logs = "暂无运行日志" # 用于存储捕获的 print 信息

# === 4. 侧边栏：显示后台数据 (增强版) ===
with st.sidebar:
    st.header("🧠 大脑记忆 (Context)")
    
    # 显示症状
    current_symptoms = st.session_state.context.get("symptoms", [])
    st.write("📋 **当前已知症状:**")
    st.json(current_symptoms)
    
    # 显示诊断结论
    st.write("🩺 **当前诊断结论:**")
    st.info(st.session_state.context.get("last_diag_name", "暂无"))
    
    # --- 新增：显示后台详细日志 ---
    st.header("🛠️ 后台运行日志 (Debug)")
    with st.expander("点击查看详细推演过程", expanded=True):
        # 使用 code 块显示日志，保持格式且有滚动条
        st.code(st.session_state.last_logs, language="text")

    st.divider()
    if st.button("🗑️ 清空重来", type="primary"):
        st.session_state.history = []
        st.session_state.context = {}
        st.session_state.last_logs = "已清空"
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

    # 2. 调用后端逻辑 (带日志捕获)
    with st.spinner("老中医正在推演..."):
        
        # --- 核心修改：捕获 print 输出 ---
        # 创建一个内存缓冲区，假装它是屏幕
        capture_buffer = io.StringIO()
        
        # 在这个 with 块里执行的所有 print 都会被抓到 buffer 里
        with contextlib.redirect_stdout(capture_buffer):
            result = llm_doctor.get_diagnosis_and_reply(
                user_text=prompt,
                history=st.session_state.history,
                saved_context=st.session_state.context
            )
        
        # 把抓到的文字存入 Session State
        logs = capture_buffer.getvalue()
        if logs.strip():
            st.session_state.last_logs = logs
        else:
            st.session_state.last_logs = "本次交互无后台输出 (可能是 LLM 直接回复)"
        # -------------------------------

    # 3. 更新记忆
    if result.new_info:
        st.session_state.context = result.new_info

    # 4. 显示 AI 回复
    with st.chat_message("assistant"):
        st.markdown(result.reply)
    st.session_state.history.append({"role": "assistant", "content": result.reply})

    # 5. 强制刷新页面以更新侧边栏日志
    st.rerun()