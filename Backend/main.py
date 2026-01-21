# main.py
import uvicorn
from fastapi import FastAPI
from schemas import ClientRequest, ServerResponse, ServerResponseData
import image_processor
import llm_doctor
import data_loader  # 引入数据加载器

app = FastAPI()


# 【重要】：在 App 启动时加载数据
@app.on_event("startup")
async def startup_event():
    data_loader.load_all_data()


@app.post("/api/tcm_process", response_model=ServerResponse)
async def main_entry(request: ClientRequest):
    # ... 后面的逻辑基本不用变，直接用之前的即可 ...
    # ... 因为 llm_doctor 的接口签名我们保持了一致 ...
    try:
        client_saved_context = request.payload.saved_context
        current_image_features = None
        user_input_text = request.payload.user_text

        if request.request_type == "image" and request.payload.image_base64:
            current_image_features = image_processor.analyze_image_features(request.payload.image_base64)

        doctor_result = llm_doctor.get_diagnosis_and_reply(
            user_text=user_input_text,
            history=request.payload.history,
            saved_context=client_saved_context,
            current_image_features=current_image_features
        )

        # ... 组装返回，同之前的 main.py ...
        has_new = False
        new_data = {}
        if doctor_result.new_info:
            has_new = True
            new_data = doctor_result.new_info

        response_data = ServerResponseData(
            reply_text=doctor_result.reply,
            has_new_context=has_new,
            new_context_to_save=new_data
        )
        return ServerResponse(status="success", data=response_data)

    except Exception as e:
        print(f"Error: {e}")
        empty_data = ServerResponseData(reply_text="服务器出错了", has_new_context=False)
        return ServerResponse(status="error", message=str(e), data=empty_data)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)