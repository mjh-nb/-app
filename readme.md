
# 🌿 中医智能辅助诊疗系统——岐黄ai

> 基于多模态大模型与专家规则引擎的“全场景随身中医智能体”后端服务。

## 📖 项目简介

本项目是**全国软件创新大赛**参赛作品的核心后端服务。旨在探索 AI 技术如何赋能传统中医，解决移动场景下中医诊疗“难以量化、缺乏即时反馈”的痛点。

系统采用 **"Neuro-Symbolic" (神经符号)** 混合架构：
1.  **感知层**：利用视觉大模型 (VLM) 实现舌象、面象的标准化特征提取。
2.  **推理层**：结合 **LLM (DeepSeek)** 的语义理解能力与 **基于 Excel 知识库的确定性规则引擎**，实现严谨的证候推理。
3.  **服务层**：基于 FastAPI 提供高性能的端云协同接口。

## ✨ 核心功能

*   **📸 多模态望诊**
    *   **智能舌诊**：识别舌质（淡红、紫暗等）、舌苔（黄腻、薄白等）。
    *   **智能面诊**：识别面色特征（萎黄、潮红等）。
*   **💬 深度问诊交互**
    *   基于上下文的自然语言对话。
    *   **八纲辨证**引导：自动根据当前信息缺失情况，进行表里/寒热/虚实的定向追问。
*   **🧠 专家决策引擎**
    *   内置 **八纲、六经、卫气营血、脏腑** 等多套辨证体系。
    *   基于加权评分算法的证候匹配，给出可解释的诊断依据。
*   **💊 方剂智能推荐**
    *   根据确诊证型，自动检索《方剂学》数据库，推荐主方及附方。
    *   提供详细的方剂组成与调理建议。

## 🛠 技术栈

*   **Web 框架**: FastAPI, Uvicorn
*   **数据验证**: Pydantic
*   **数据处理**: Pandas, NumPy
*   **大模型基座**:
    *   **NLP**: DeepSeek-Chat (通过 OpenAI SDK 调用)
    *   **Vision**: Qwen-VL-Max (通义千问视觉模型)
*   **知识库**: 基于 `.xlsx` 的结构化中医规则库 (Rules Base)

## 📂 项目结构

```text
TCM_Backend/
├── main.py              # 程序主入口 (FastAPI App)
├── schemas.py           # Pydantic 数据模型定义 (API 接口协议)
├── image_processor.py   # 图像处理模块 (调用 Qwen-VL 进行特征提取)
├── llm_doctor.py        # 核心诊疗逻辑 (融合 NLP 提取 + 规则算分 + LLM 回复)
├── data_loader.py       # 数据加载器 (初始化 Excel 知识库)
├── requirements.txt     # Python 依赖包
├── 中医诊断学/           # [核心数据] 辨证规则数据库
│   ├── 八纲证候判断表.xlsx
│   ├── 脏腑辨证表.xlsx
│   └── ...
└── 方剂学/               # [核心数据] 方剂数据库
    ├── 方剂学查询表.xlsx
    └── ...
```

## 🚀 快速开始

### 1. 环境准备
确保 Python 版本 >= 3.8。

```bash
# 克隆项目
git clone [你的仓库地址]
cd TCM_Backend

# 安装依赖
pip install pandas fastapi uvicorn openai dashscope openpyxl
```

### 2. 配置 API Key
请在 `image_processor.py` 和 `llm_doctor.py` 中填入相应的 API Key，或配置环境变量：
*   `DASHSCOPE_API_KEY`: 用于图像识别 (阿里云 DashScope)
*   `DEEPSEEK_API_KEY`: 用于文本对话 (DeepSeek)

### 3. 数据准备
确保项目根目录下存在 `中医诊断学` 和 `方剂学` 两个数据文件夹，且包含完整的 Excel 规则表。

### 4. 启动服务

```bash
# 启动本地开发服务器 (默认端口 8000)
python main.py
```

服务启动后，将会加载 Excel 规则库：
```text
🚀 [DataLoader] 正在初始化诊断数据库...
✅ [DataLoader] 加载成功: 中医诊断学/八纲证候判断表.xlsx (xx 行)
...
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## 🔌 API 接口说明

**主接口**: `POST /api/tcm_process`

**请求示例 (JSON)**:
```json
{
  "request_type": "multi",
  "payload": {
    "user_text": "我最近总是失眠，感觉心慌",
    "images": {
      "tongue": "BASE64_STRING..." 
    },
    "saved_context": {
      "profile": {"sex": "女", "age": 25},
      "symptoms": ["失眠"]
    }
  }
}
```

## 👨‍💻 团队分工

*   **秦姝月**: 核心算法实现（规则引擎算分、Excel 数据清洗、方剂匹配逻辑）。
*   **马锦浩**: 后端架构设计、图象识别。
*   **李吉然**: 所有前端内容。
*   **郭欣琪**：提供有关中医的专业知识。

## ⚠️ 免责声明

本项目仅供软件创新大赛演示使用，系统给出的诊断结果和方剂建议仅基于算法推演，**不构成真实的医疗建议**。身体不适请前往正规医院就诊。