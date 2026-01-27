# debug_main.py
import uvicorn
import json
import copy
from fastapi import FastAPI
from schemas import ClientRequest, ServerResponse, ServerResponseData
import image_processor
import llm_doctor
import data_loader

app = FastAPI()


# --- 辅助工具：用于漂亮打印日志，并自动隐藏过长的图片数据 ---
def debug_log(stage_name, data_obj):
    """
    stage_name: 当前步骤名称
    data_obj: 要打印的对象 (Pydantic对象, 字典, 或普通类实例)
    """
    try:
        # 1. 将各种对象转换为字典，方便处理
        if hasattr(data_obj, "model_dump"):  # Pydantic v2
            data_dict = data_obj.model_dump()
        elif hasattr(data_obj, "dict"):  # Pydantic v1
            data_dict = data_obj.dict()
        elif hasattr(data_obj, "__dict__"):  # 普通 Python 类
            data_dict = data_obj.__dict__
        elif isinstance(data_obj, dict):
            data_dict = data_obj
        else:
            data_dict = {"raw_value": str(data_obj)}

        # 2. 深拷贝一份，防止修改原始数据
        # 我们只修改打印用的这份数据
        log_copy = copy.deepcopy(data_dict)

        # 3. 如果里面有 image_base64 且特别长，把它截断，防止刷屏
        # 递归检查 payload 里的 image_base64
        if "payload" in log_copy and isinstance(log_copy["payload"], dict):
            if log_copy["payload"].get("image_base64"):
                log_copy["payload"]["image_base64"] = "【Base64数据过长，已隐藏...】"
        # 直接检查第一层
        if log_copy.get("image_base64"):
            log_copy["image_base64"] = "【Base64数据过长，已隐藏...】"

        # 4. 打印漂亮的分割线和 JSON
        print(f"\n{'=' * 20} 【DEBUG: {stage_name}】 {'=' * 20}")
        print(json.dumps(log_copy, ensure_ascii=False, indent=2))
        print(f"{'=' * 60}\n")

    except Exception as e:
        print(f"DEBUG日志打印失败 (不影响主流程): {e}")


@app.on_event("startup")
async def startup_event():
    # 启动时加载数据
    data_loader.load_all_data()


@app.post("/api/tcm_process", response_model=ServerResponse)
async def main_entry(request: ClientRequest):
    try:
        # =======================================================
        # 节点 1：接收到 POST 请求时
        # =======================================================
        debug_log("1. 收到前端请求 (ClientRequest)", request)

        client_saved_context = request.payload.saved_context
        current_image_features = None
        user_input_text = request.payload.user_text

        # 图像处理逻辑
        if request.request_type == "image" and request.payload.image_base64:
            print(">>> 正在调用图像处理模块...")
            current_image_features = image_processor.analyze_image_features(request.payload.image_base64)
            print(f">>> 图像处理完成: {current_image_features}")

        # =======================================================
        # 节点 2：即将传递给 LLM 时
        # =======================================================
        # 这里我们将要传给函数的参数打包打印一下
        llm_input_preview = {
            "user_text": user_input_text,
            "saved_context (旧笔记)": client_saved_context,
            "current_image_features (新特征)": current_image_features,
            "history_length": len(request.payload.history)
        }
        debug_log("2. 准备调用 LLM (Doctor Input)", llm_input_preview)

        # 调用 LLM 核心逻辑
        doctor_result = llm_doctor.get_diagnosis_and_reply(
            user_text=user_input_text,
            history=request.payload.history,
            saved_context=client_saved_context,
            current_image_features=current_image_features
        )

        # =======================================================
        # 节点 3：LLM 处理完毕，拿到结果后
        # =======================================================
        debug_log("3. LLM 返回结果 (DoctorResult)", doctor_result)

        # 组装返回数据
        has_new = False
        new_data = {}
        # 判断是否有新的 context 需要前端保存
        if doctor_result.new_info and len(doctor_result.new_info) > 0:
            has_new = True
            new_data = doctor_result.new_info

        # 构造 Response Data
        response_data = ServerResponseData(
            reply_text=doctor_result.reply,
            has_new_context=has_new,
            new_context_to_save=new_data
        )

        # 构造最终 Response 对象
        final_response = ServerResponse(status="success", data=response_data)

        # =======================================================
        # 节点 4：即将以 JSON 形式返回给前端时
        # =======================================================
        debug_log("4. 最终响应数据 (ServerResponse)", final_response)

        return final_response

    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"!!!! 发生严重错误 !!!!: {error_msg}")
        traceback.print_exc()  # 打印详细报错堆栈

        # 构造错误返回
        empty_data = ServerResponseData(reply_text="服务器内部错误", has_new_context=False)
        return ServerResponse(status="error", message=error_msg, data=empty_data)


if __name__ == "__main__":
    # 启动服务
    uvicorn.run("debug_main:app", host="0.0.0.0", port=8000, reload=True)