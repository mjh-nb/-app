# image_processor.py
import base64
import os
import json
import tempfile
from http import HTTPStatus
import dashscope

dashscope.api_key = "sk-588a2db89b454327ad4cc1a43ffedc7c"


def analyze_image_features(image_base64_str):
    """
    接收 Base64 图片，调用视觉大模型，返回符合限定词的特征。
    """
    print("【1. 图像模块】开始处理图片...")

    # --- 1. Base64 解码并保存为临时文件 ---
    # 大模型 API 通常需要一个文件路径或者 URL
    # 我们创建一个临时文件来存这张图

    # 去掉可能存在的 header (例如 "data:image/jpeg;base64,")
    if "," in image_base64_str:
        image_base64_str = image_base64_str.split(",")[1]

    img_data = base64.b64decode(image_base64_str)

    # 创建一个临时文件 (会自动删除，但为了稳妥我们手动控制一下)
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    temp_file.write(img_data)
    temp_file.close()
    image_path = temp_file.name  # 拿到这个文件的绝对路径

    try:
        # --- 2. 构造 Prompt (你的核心竞争力) ---
        # 把你截图里的那个表格变成文字规则

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

        # --- 3. 调用通义千问-VL API ---
        messages = [
            {
                "role": "user",
                "content": [
                    {"image": f"file://{image_path}"},  # 传入本地文件路径
                    {"text": prompt}
                ]
            }
        ]

        # 使用 qwen-vl-max (效果最好) 或 qwen-vl-plus
        response = dashscope.MultiModalConversation.call(
            model='qwen-vl-max',
            messages=messages
        )

        # --- 4. 解析结果 ---
        if response.status_code == HTTPStatus.OK:
            result_text = response.output.choices[0].message.content[0]['text']
            print(f"【1. 图像模块】大模型原始返回: {result_text}")

            # 清洗数据：有时候大模型会返回 ```json ... ```，需要去掉 Markdown 标记
            clean_json = result_text.replace("```json", "").replace("```", "").strip()

            # 转成 Python 字典
            features = json.loads(clean_json)
            return features

        else:
            print(f"API调用失败: {response.code} - {response.message}")
            raise Exception("视觉模型调用失败")

    except Exception as e:
        print(f"Error in image processing: {e}")
        # 发生错误时的兜底（防止程序崩掉）
        return {
            "visual_summary": "图片识别异常，请重试",
            "tongue_substance": "未知",
            "tongue_coating": "未知"
        }

    finally:
        # --- 5. 清理战场 ---
        # 删掉那个临时图片文件，不占硬盘
        if os.path.exists(image_path):
            os.remove(image_path)

