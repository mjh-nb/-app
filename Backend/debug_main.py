# debug_main.py
import uvicorn
import json
from fastapi import FastAPI
from schemas import ClientRequest, ServerResponse, ServerResponseData
import image_processor
import llm_doctor
import data_loader

app = FastAPI()


# --- 调试辅助函数：让打印更好看 ---
def print_debug_step(step_name, data):
    print(f"\n{'=' * 20} 🛑 DEBUG: {step_name} {'=' * 20}")
    try:
        # 尝试把 Pydantic 对象转为字典
        if hasattr(data, 'dict'):
            content = data.dict()
        elif hasattr(data, 'model_dump'):  # Pydantic v2
            content = data.model_dump()
        elif hasattr(data, '__dict__'):  # 普通类
            content = data.__dict__
        else:
            content = data

        # 打印漂亮的 JSON
        print(json.dumps(content, indent=4, ensure_ascii=False, default=str))
    except Exception as e:
        # 如果转 JSON 失败，直接打印字符串
        print(f"[无法序列化为JSON]: {data}")
    print(f"{'=' * 50}\n")


@app.on_event("startup")
async def startup_event():
    data_loader.load_all_data()


@app.post("/api/tcm_process", response_model=ServerResponse)
async def main_entry(request: ClientRequest):
    try:
        # ==========================================
        # 节点 1: 接收到 POST 请求
        # ==========================================
        print_debug_step("1. 收到前端原始请求 (Request Received)", request)

        # 1. 拆解数据
        payload = request.payload
        saved_context = payload.saved_context

        # 临时变量
        current_image_features = {}

        # ==========================================
        # 步骤 A: 检查有没有发舌头照片
        # ==========================================
        if payload.images and payload.images.tongue:
            print(f"📸 检测到舌象图片数据，正在调用图像模型...")
            # 调用你的图像处理模块
            tongue_features = image_processor.analyze_image_features(payload.images.tongue)
            # 把结果存入特征字典
            current_image_features.update(tongue_features)
            print(f"✅ 舌象识别完成: {tongue_features}")

        # ==========================================
        # 步骤 B: 检查有没有发面部照片 (预留)
        # ==========================================
        if payload.images and payload.images.face:
            print("📸 收到面部照片，暂未处理 (代码预留位)")

        # ==========================================
        # 节点 2: 即将传递给 LLM
        # ==========================================
        # 构造一个字典来展示我们要传给 LLM 的所有东西
        llm_input_debug = {
            "user_text": payload.user_text,
            "history_count": len(payload.history) if payload.history else 0,
            "history_preview": payload.history[-2:] if payload.history else [],  # 只看最近2条
            "saved_context": saved_context,
            "current_image_features": current_image_features
        }
        print_debug_step("2. 准备传给 LLM Doctor 的参数 (Input for LLM)", llm_input_debug)

        # ==========================================
        # 步骤 C: 全权交给医生
        # ==========================================
        doctor_result = llm_doctor.get_diagnosis_and_reply(
            user_text=payload.user_text,
            history=payload.history,
            saved_context=saved_context,
            current_image_features=current_image_features
        )

        # ==========================================
        # 节点 3: LLM 处理完成
        # ==========================================
        print_debug_step("3. LLM Doctor 返回结果 (Output from LLM)", doctor_result)

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

        final_response = ServerResponse(status="success", data=response_data)

        # ==========================================
        # 节点 4: 即将返回给前端
        # ==========================================
        print_debug_step("4. 最终返回给前端的 JSON (Final Response)", final_response)

        return final_response

    except Exception as e:
        print(f"\n❌ 发生严重错误: {e}")
        import traceback
        traceback.print_exc()

        empty_data = ServerResponseData(reply_text="服务器内部错误", has_new_context=False)
        return ServerResponse(status="error", message=str(e), data=empty_data)


if __name__ == "__main__":
    # 启动命令
    print("🚀 Debug 模式服务器启动中...")
    uvicorn.run("debug_main:app", host="0.0.0.0", port=8000, reload=True)