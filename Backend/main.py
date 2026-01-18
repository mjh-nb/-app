# main.py
import uvicorn
from fastapi import FastAPI, HTTPException
from schemas import ClientRequest, ServerResponse
# 引入另外两个模块
import image_processor
import llm_doctor

app = FastAPI()


@app.post("/api/tcm_process", response_model=ServerResponse)
async def main_entry(request: ClientRequest):
    """
    这是唯一的入口。
    前端不管干什么，都向这个地址发 POST 请求。
    """
    try:
        response_data = {}

        # --- 分流逻辑 ---

        # 场景 1：前端发来的是图片，要求提取特征
        if request.request_type == "image":
            if not request.payload.image_base64:
                raise ValueError("请求类型为 image，但没有上传图片数据")

            # 调用你的模块
            features = image_processor.analyze_image_features(request.payload.image_base64)

            response_data = {
                "type": "image_result",
                "features": features,
                "reply_text": "已收到您的舌象/面相照片，特征识别完成。"
            }

        # 场景 2：前端发来的是对话，要求问诊
        elif request.request_type == "chat":
            user_text = request.payload.user_text
            history = request.payload.history
            # 注意：前端把之前识别的特征带回来了
            features = request.payload.existing_features

            # 调用队友的模块
            doctor_reply = llm_doctor.get_diagnosis_and_reply(user_text, history, features)

            response_data = {
                "type": "chat_result",
                "reply_text": doctor_reply
            }

        else:
            raise ValueError(f"不支持的请求类型: {request.request_type}")

        # 返回成功结果
        return ServerResponse(status="success", data=response_data)

    except Exception as e:
        print(f"Error: {e}")
        # 返回错误结果
        return ServerResponse(status="error", message=str(e), data={})


if __name__ == "__main__":
    # 启动服务器，端口 8000
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)