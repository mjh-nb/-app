# image_processor.py

def analyze_image_features(image_base64_str):
    """
    你的任务：接收图片的 base64 字符串，调用视觉大模型，返回特征字典。
    目前先返回假数据，用来测试架构通不通。
    """
    print("【图像模块】正在处理图片...")

    # TODO: 以后在这里写真正的 API 调用代码

    # 模拟提取出的特征
    fake_features = {
        "tongue_color": "淡白",
        "tongue_shape": "胖大",
        "coating": "白腻苔",
        "face_color": "萎黄",
        "description": "舌淡胖大，苔白腻，面色萎黄。"  # 汇总描述
    }

    return fake_features