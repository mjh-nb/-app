# main.py
import uvicorn
from fastapi import FastAPI
from schemas import ClientRequest, ServerResponse, ServerResponseData
import image_processor
import llm_doctor

app = FastAPI()


@app.post("/api/tcm_process", response_model=ServerResponse)
async def main_entry(request: ClientRequest):
    try:
        # 1. 拿出前端带来的“传家宝” (已保存的关键信息)
        client_saved_context = request.payload.saved_context

        # 临时变量
        current_image_features = None
        user_input_text = request.payload.user_text

        # ==========================================
        # 步骤 A: 如果有图，先看图 (提取新特征)
        # ==========================================
        if request.request_type == "image":
            if request.payload.image_base64:
                # 这一步产生了一些“新知识”
                current_image_features = image_processor.analyze_image_features(request.payload.image_base64)

        # ==========================================
        # 步骤 B: 医生会诊 (核心)
        # ==========================================
        # 把 [旧笔记] + [新图片特征] 一起给医生

        doctor_result = llm_doctor.get_diagnosis_and_reply(
            user_text=user_input_text,
            history=request.payload.history,
            saved_context=client_saved_context,  # 传入旧笔记
            current_image_features=current_image_features  # 传入新特征
        )

        # ==========================================
        # 步骤 C: 组装返回数据
        # ==========================================

        # 判断医生有没有提取出新东西
        has_new = False
        new_data = {}

        if doctor_result.new_info and len(doctor_result.new_info) > 0:
            has_new = True
            new_data = doctor_result.new_info

        # 构造符合 schemas 定义的结构
        response_data = ServerResponseData(
            reply_text=doctor_result.reply,
            has_new_context=has_new,
            new_context_to_save=new_data
        )

        return ServerResponse(status="success", data=response_data)

    except Exception as e:
        print(f"Error: {e}")
        # 构造一个空的错误数据
        empty_data = ServerResponseData(reply_text="服务器出错了", has_new_context=False)
        return ServerResponse(status="error", message=str(e), data=empty_data)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)