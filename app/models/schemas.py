"""
數據模型定義 - 定義應用程序中使用的數據模型
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class Message(BaseModel):
    """聊天消息模型"""
    role: str = Field(..., description="消息角色 (user, assistant, system)")
    content: str = Field(..., description="消息內容")


class ChatRequest(BaseModel):
    """聊天請求模型"""
    messages: List[Message] = Field(..., description="聊天歷史消息列表")
    stream: bool = Field(False, description="是否使用流式響應")
    model: Optional[str] = Field(None, description="使用的模型名稱")
    temperature: float = Field(0.7, description="溫度參數，控制隨機性")
    max_tokens: Optional[int] = Field(None, description="最大生成令牌數")


class ChatResponse(BaseModel):
    """聊天響應模型"""
    message: Message = Field(..., description="助手回覆消息")
    sources: List[Dict[str, Any]] = Field([], description="引用的信息源")


class DocumentChunk(BaseModel):
    """文檔分塊模型"""
    text: str = Field(..., description="分塊文本內容")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="分塊元數據")


class SearchQuery(BaseModel):
    """搜索查詢模型"""
    query: str = Field(..., description="搜索查詢文本")
    top_k: int = Field(5, description="返回的最大結果數量")
    filter: Optional[Dict[str, Any]] = Field(None, description="搜索過濾條件")


class SearchResult(BaseModel):
    """搜索結果模型"""
    text: str = Field(..., description="結果文本")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="結果元數據")
    score: float = Field(..., description="相似度分數") 