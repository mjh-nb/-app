# schemas.py
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


# --- 1. 前端发给后端的 (Request) ---
# 前端每次都要把“传家宝”（关键信息）带过来

class Payload(BaseModel):
    # 本次请求的内容
    image_base64: Optional[str] = None  # 这次有没有发图？
    user_text: Optional[str] = None  # 这次有没有说话？

    # 【核心变化】：前端存的“关键信息库”
    # 这是一个字典，比如 {"tongue": "白腻", "main_symptom": "头疼"}
    # 每次请求都要全量带过来
    saved_context: Dict[str, Any] = {}

    # 历史对话记录 (用于 LLM 理解上下文流)
    history: List[Dict[str, str]] = []


class ClientRequest(BaseModel):
    user_id: str = "default_user"
    request_type: str  # "image" 或 "chat"
    payload: Payload


# --- 2. 后端发给前端的 (Response) ---
# 后端要告诉前端：“这次有没有新知识要你记下来？”

class ServerResponseData(BaseModel):
    # 1. 给用户看的话
    reply_text: str

    # 2. 是否产生了新信息 (True/False)
    has_new_context: bool

    # 3. 需要前端更新/合并的关键信息 (如果有的话)
    # 比如后端识别了舌头，这里返回 {"tongue": "红"}
    # 前端拿到后，要把这个 merge 到自己的 saved_context 里
    new_context_to_save: Dict[str, Any] = {}


class ServerResponse(BaseModel):
    status: str = "success"
    message: str = ""
    data: ServerResponseData  # 嵌套上面的结构