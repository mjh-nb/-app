# main.py
import uvicorn
from fastapi import FastAPI
from schemas import ClientRequest, ServerResponse, ServerResponseData
import image_processor
import llm_doctor
import data_loader

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    data_loader.load_all_data()


@app.post("/api/tcm_process", response_model=ServerResponse)
async def main_entry(request: ClientRequest):
    try:
        # 1. 拆解数据
        payload = request.payload
        saved_context = payload.saved_context

        # 临时变量
        current_image_features = {}

        # ==========================================
        # 步骤 A: 检查有没有发舌头照片
        # ==========================================
        if payload.images and payload.images.tongue:
            # 调用你的图像处理模块
            tongue_features = image_processor.analyze_image_features(payload.images.tongue)
            # 把结果存入特征字典，Key 可以定为 "tongue_image_result"
            current_image_features.update(tongue_features)

        # ==========================================
        # 步骤 B: 检查有没有发面部照片 (预留)
        # ==========================================
        if payload.images and payload.images.face:
            # 暂时还没有面部处理函数，先打印一下
            print("收到面部照片，暂未处理")
            # current_image_features.update(face_features)

        # ==========================================
        # 步骤 C: 全权交给医生
        # ==========================================
        # 医生不仅要看 user_text，现在还能看到 saved_context 里的 profile (性别年龄)

        doctor_result = llm_doctor.get_diagnosis_and_reply(
            user_text=payload.user_text,
            history=payload.history,
            saved_context=saved_context,
            current_image_features=current_image_features
        )

        # ==========================================
        # 步骤 D: 返回
        # ==========================================
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
        # 打印详细错误栈，方便调试
        import traceback
        traceback.print_exc()

        empty_data = ServerResponseData(reply_text="服务器内部错误", has_new_context=False)
        return ServerResponse(status="error", message=str(e), data=empty_data)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)