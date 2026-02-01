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
    # 服务启动时预加载Excel数据到内存
    data_loader.load_all_data()


@app.post("/api/tcm_process", response_model=ServerResponse)
async def main_entry(request: ClientRequest):
    try:
        # 解包请求数据和上下文
        payload = request.payload
        saved_context = payload.saved_context

        # 用于收集本轮对话中视觉模型提取的特征
        current_image_features = {}

        # --- 舌诊图像处理 ---
        # 检查是否包含舌象图片数据
        if payload.images and payload.images.tongue:
            # 调用视觉模型提取舌质、舌苔特征
            tongue_features = image_processor.analyze_image_features(payload.images.tongue)
            # 合并特征到当前集合
            current_image_features.update(tongue_features)

        # --- 面诊图像处理 ---
        # 检查是否包含面部图片数据
        if payload.images and payload.images.face:
            # 调用视觉模型提取面色特征
            face_features = image_processor.analyze_face_features(payload.images.face)
            # 合并特征到当前集合，后续会自动进入症状列表参与算分
            current_image_features.update(face_features)

        # --- 核心诊断流程 ---
        # 调用医生模块，传入用户文本、历史记录、上下文及视觉特征
        # 该模块内部包含NLP提取、规则引擎算分及LLM回复生成
        doctor_result = llm_doctor.get_diagnosis_and_reply(
            user_text=payload.user_text,
            history=payload.history,
            saved_context=saved_context,
            current_image_features=current_image_features
        )

        # --- 构造响应数据 ---
        # 检查是否有新的上下文信息需要客户端更新（如提取到了新症状）
        has_new = False
        new_data = {}
        if doctor_result.new_info:
            has_new = True
            new_data = doctor_result.new_info

        # 封装符合Schema定义的返回对象
        response_data = ServerResponseData(
            reply_text=doctor_result.reply,
            has_new_context=has_new,
            new_context_to_save=new_data
        )

        return ServerResponse(status="success", data=response_data)

    except Exception as e:
        print(f"Error: {e}")
        # 输出完整堆栈信息以辅助调试
        import traceback
        traceback.print_exc()

        # 发生异常时返回友好提示，避免前端崩溃
        empty_data = ServerResponseData(reply_text="服务器内部错误", has_new_context=False)
        return ServerResponse(status="error", message=str(e), data=empty_data)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)