# schemas.py
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


# --- 新增：专门用来接图片的结构 ---
class Images(BaseModel):
    # 对应 json 里的 "face" 和 "tongue"
    # 前端可能不传，或者传 null，所以设为 Optional
    face: Optional[str] = None
    tongue: Optional[str] = None


# --- 修改：Payload 结构 ---
class Payload(BaseModel):
    # 1. 图片变成了嵌套结构
    images: Optional[Images] = None

    # 2. 用户主诉
    user_text: Optional[str] = None

    # 3. 关键信息库
    # 前端截图里只有 profile，但我们之前的 symptoms (症状) 和 tongue (舌象数据) 也要存在这里
    # 所以定义为 Dict[str, Any] 是最安全的，啥都能存
    saved_context: Dict[str, Any] = {}

    # 4. 历史记录
    history: List[Dict[str, str]] = []


# --- 修改：外层请求 ---
class ClientRequest(BaseModel):
    user_id: str = "default_user"
    request_type: str = "multi"  # 默认改为 multi
    payload: Payload


# --- 响应结构 (保持不变，或者根据需要微调) ---
class ServerResponseData(BaseModel):
    reply_text: str
    has_new_context: bool
    new_context_to_save: Dict[str, Any] = {}


class ServerResponse(BaseModel):
    status: str = "success"
    message: str = ""
    data: ServerResponseData