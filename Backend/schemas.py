# schemas.py
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


# 前端发来的 Payload
class Payload(BaseModel):
    image_base64: Optional[str] = None
    user_text: Optional[str] = None

    # 【核心修改】：saved_context 现在的结构变复杂了
    # 建议前端把它拆成两部分存，或者混在一起存。
    # 为了兼容队友的逻辑，我们假设 saved_context 包含两个 key:
    # "symptoms": { "Headache": {"部位": "前额"} }
    # "tongue": { "YellowCoating": 1 }
    saved_context: Dict[str, Any] = {}

    history: List[Dict[str, str]] = []


class ClientRequest(BaseModel):
    user_id: str = "default_user"
    request_type: str
    payload: Payload


# 后端返回的数据
class ServerResponseData(BaseModel):
    reply_text: str
    has_new_context: bool

    # 这里返回更新后的全量数据（或者增量数据），给前端覆盖保存
    new_context_to_save: Dict[str, Any] = {}


class ServerResponse(BaseModel):
    status: str = "success"
    message: str = ""
    data: ServerResponseData