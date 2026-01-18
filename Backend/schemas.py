# schemas.py
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# --- 1. 定义前端发来的数据格式 (Request) ---

class Payload(BaseModel):
    # 如果是图片请求，这里会有 Base64 字符串
    image_base64: Optional[str] = None
    # 如果是对话请求，这里会有用户说的话
    user_text: Optional[str] = None
    # 历史对话记录 (前端传过来的)
    history: Optional[List[Dict[str, str]]] = []
    # 之前提取的特征 (前端暂存后传回来的)
    existing_features: Optional[Dict[str, Any]] = {}

class ClientRequest(BaseModel):
    user_id: str = "default_user"
    # 请求类型：只能是 "image" 或 "chat"
    request_type: str
    payload: Payload

# --- 2. 定义后端返回的数据格式 (Response) ---

class ServerResponse(BaseModel):
    status: str = "success"
    message: str = ""
    # 这里面放具体的回复内容
    data: Dict[str, Any]