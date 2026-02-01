# schemas.py
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


# 多模态图像输入结构，接收Base64编码
class Images(BaseModel):
    # 面部和舌象数据，均为可选字段
    face: Optional[str] = None
    tongue: Optional[str] = None


# 请求载体，封装单次交互的所有必要信息
class Payload(BaseModel):
    # 多模态图像数据
    images: Optional[Images] = None

    # 用户当前的主诉文本
    user_text: Optional[str] = None

    # 客户端维护的持久化上下文（包含症状集合、用户Profile等）
    # 使用Dict[str, Any]以保持结构扩展性
    saved_context: Dict[str, Any] = {}

    # 多轮对话历史，用于LLM理解上下文
    history: List[Dict[str, str]] = []


# 客户端请求顶层结构
class ClientRequest(BaseModel):
    user_id: str = "default_user"
    request_type: str = "multi"  # 默认为多模态混合交互模式
    payload: Payload


# 业务层响应数据DTO
class ServerResponseData(BaseModel):
    # LLM生成的回复文本
    reply_text: str

    # 标记是否有新的上下文信息（如新识别的症状）需要客户端更新
    has_new_context: bool

    # 需要客户端保存的上下文更新数据
    new_context_to_save: Dict[str, Any] = {}


# 标准API响应包装类
class ServerResponse(BaseModel):
    status: str = "success"
    message: str = ""
    data: ServerResponseData