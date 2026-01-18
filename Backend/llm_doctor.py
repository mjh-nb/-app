# llm_doctor.py

def get_diagnosis_and_reply(current_text, history, features):
    """
    队友的任务：接收用户文本、历史记录、身体特征，调用文心一言/GPT，返回回复。
    """
    print(f"【LLM模块】收到特征：{features}")
    print(f"【LLM模块】收到用户话语：{current_text}")

    # TODO: 以后在这里写调用 LLM API 的代码

    # 模拟医生的回复
    fake_reply = "根据您的舌象（苔白腻），您可能是脾虚湿盛。建议少吃生冷食物。"

    return fake_reply