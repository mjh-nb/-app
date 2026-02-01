# image_processor.py
import base64
import os
import json
import tempfile
from http import HTTPStatus
import dashscope

# 请在环境变量中配置 DASH_SCOPE_API_KEY，此处为演示Key
dashscope.api_key = "DASHSCOPE_API_KEY"

def analyze_image_features(image_base64_str):
    """
    处理舌象图片：Base64解码 -> 临时文件存储 -> 调用VL大模型 -> 提取标准化特征
    """
    print("【1. 图像模块】开始处理舌象图片...")

    # 对Base64字符串进行预处理，移除可能存在的Data URI scheme前缀
    if "," in image_base64_str:
        image_base64_str = image_base64_str.split(",")[1]

    img_data = base64.b64decode(image_base64_str)

    # 创建临时文件保存图片，供API读取
    # 使用后需手动清理，防止磁盘空间占用
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    temp_file.write(img_data)
    temp_file.close()
    image_path = temp_file.name

    try:
        # 定义舌诊的标准化词汇表，确保模型输出可被后续算分逻辑识别
        candidates_substance = "舌淡红, 舌淡边有齿痕, 舌淡, 舌红, 舌淡胖, 舌质紫暗或有瘀斑"
        candidates_coating = "苔薄白, 苔白, 少苔或无苔, 苔白滑, 苔黄腻, 苔薄白或薄黄, 苔白腻或厚腻"

        prompt = f"""
        你是一位经验丰富的中医AI助手。请仔细观察这张舌象照片。
        请严格根据画面内容，从下方的【标准候选项】中，分别选出最符合的一个【舌质】描述和一个【舌苔】描述。

        注意：
        1. 必须完全使用我提供的词汇，不要自己造词。
        2. 如果看不清或不确定，选择最接近的一项。

        【标准候选项 - 舌质】：{candidates_substance}
        【标准候选项 - 舌苔】：{candidates_coating}

        请仅返回一个纯 JSON 字符串，格式如下：
        {{
            "visual_summary": "这里用一句话总结，例如：舌淡胖，苔白腻",
            "tongue_substance": "选出的舌质词汇",
            "tongue_coating": "选出的舌苔词汇"
        }}
        """

        # 构造多模态请求消息
        messages = [
            {
                "role": "user",
                "content": [
                    {"image": f"file://{image_path}"},  # 指定本地文件协议
                    {"text": prompt}
                ]
            }
        ]

        # 调用通义千问-VL模型进行推理
        response = dashscope.MultiModalConversation.call(
            model='qwen-vl-max',
            messages=messages
        )

        # 解析API响应结果
        if response.status_code == HTTPStatus.OK:
            result_text = response.output.choices[0].message.content[0]['text']
            print(f"【1. 图像模块】大模型原始返回: {result_text}")

            # 清洗可能包含的Markdown格式标记
            clean_json = result_text.replace("```json", "").replace("```", "").strip()

            # 反序列化为字典对象
            features = json.loads(clean_json)
            return features

        else:
            print(f"API调用失败: {response.code} - {response.message}")
            raise Exception("视觉模型调用失败")

    except Exception as e:
        print(f"Error in image processing: {e}")
        # 异常兜底，返回未知状态以保证流程不中断
        return {
            "visual_summary": "图片识别异常，请重试",
            "tongue_substance": "未知",
            "tongue_coating": "未知"
        }

    finally:
        # 清理临时文件
        if os.path.exists(image_path):
            os.remove(image_path)


def analyze_face_features(image_base64_str):
    """
    处理面诊图片：流程同上，主要区别在于提示词和候选项
    """
    print("【1. 图像模块】开始处理面部照片...")

    # Base64解码
    if "," in image_base64_str:
        image_base64_str = image_base64_str.split(",")[1]
    img_data = base64.b64decode(image_base64_str)

    # 保存临时文件
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    temp_file.write(img_data)
    temp_file.close()
    image_path = temp_file.name

    try:
        # 定义面诊标准化词汇表
        candidates_face = "面色淡白, 面色红, 面色萎黄, 面色晦暗, 面色青紫, 面色潮红, 颧红"

        prompt = f"""
        你是一位中医面诊专家。请观察这张人像照片的面部气色。
        请严格根据画面内容，从下方的【标准候选项】中，选出最符合的一个描述。

        注意：
        1. 必须完全使用我提供的词汇，不要自己造词。
        2. 重点关注皮肤颜色和光泽。

        【标准候选项】：{candidates_face}

        请仅返回一个纯 JSON 字符串，格式如下：
        {{
            "visual_summary": "面色...（一句话总结）",
            "face_color": "选出的标准词汇"
        }}
        """

        # 构造请求
        messages = [
            {
                "role": "user",
                "content": [
                    {"image": f"file://{image_path}"},
                    {"text": prompt}
                ]
            }
        ]

        # 调用模型
        response = dashscope.MultiModalConversation.call(
            model='qwen-vl-max',
            messages=messages
        )

        if response.status_code == HTTPStatus.OK:
            result_text = response.output.choices[0].message.content[0]['text']
            clean_json = result_text.replace("```json", "").replace("```", "").strip()
            features = json.loads(clean_json)
            print(f"【面诊结果】: {features}")
            return features
        else:
            raise Exception("API调用失败")

    except Exception as e:
        print(f"面诊出错: {e}")
        return {}  # 返回空字典表示无有效特征

    finally:
        # 清理资源
        if os.path.exists(image_path):
            os.remove(image_path)