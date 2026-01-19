# llm_doctor.py

class DoctorResult:
    def __init__(self, reply, new_info=None):
        self.reply = reply  # 给病人说的话
        self.new_info = new_info  # 提取出的关键信息 (字典)


def get_diagnosis_and_reply(user_text, history, saved_context, current_image_features=None):
    """
    saved_context: 前端传来的之前记得笔记
    current_image_features: 刚刚从图片里看出来的新特征
    """

    # --- 1. 准备本次产生的“新笔记” ---
    new_context_update = {}

    # 如果这次有图片特征，这肯定是新笔记，得存！
    if current_image_features:
        # 把图像特征合并进去
        new_context_update.update(current_image_features)

    # --- 2. (可选) 进阶：用 LLM 从文字里提取新笔记 ---
    # 比如用户说“我这几天拉肚子”，你可以写代码让 LLM 提取出 {"symptom": "腹泻"}
    # 这里暂时略过，先只存图像特征，逻辑简单点

    # --- 3. 构造 Prompt ---
    # 我们把“旧笔记”和“新笔记”都给 LLM 看

    # 合并当前所有已知信息 (用于生成回复)
    full_knowledge = saved_context.copy()
    full_knowledge.update(new_context_update)  # 加上刚看出来的

    system_prompt = f"你是一位中医。已知患者关键信息：{full_knowledge}。请诊断。"

    # --- 4. 模拟 LLM 回复 ---
    if current_image_features:
        reply = f"已识别您的舌象特征：{current_image_features.get('visual_summary')}。这提示您可能..."
    else:
        reply = f"收到。结合您之前的舌象（{saved_context.get('visual_summary', '未知')}），建议您..."

    # --- 5. 打包返回 ---
    # 把“话”和“新笔记”一起返回
    return DoctorResult(reply=reply, new_info=new_context_update)