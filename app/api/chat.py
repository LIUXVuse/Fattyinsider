"""
聊天 API 路由 - 處理聊天相關的 API 請求
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse, JSONResponse

from app.models.schemas import ChatRequest, ChatResponse, Message
from app.services.chat_service import ChatService
from app.services.vector_store import VectorStore
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# 依賴注入
def get_vector_store() -> VectorStore:
    """獲取向量存儲實例"""
    return VectorStore()

def get_chat_service(vector_store: VectorStore = Depends(get_vector_store)) -> ChatService:
    """獲取聊天服務實例"""
    return ChatService(vector_store=vector_store)

@router.post("/completions", response_model=ChatResponse)
async def chat_completions(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
) -> ChatResponse:
    """
    生成聊天回應
    
    Args:
        request: 聊天請求
        chat_service: 聊天服務實例
        
    Returns:
        聊天回應或流式響應
    """
    logger.info(f"收到聊天請求: {len(request.messages)} 條消息")
    
    try:
        # 檢查消息列表是否為空
        if not request.messages:
            raise HTTPException(status_code=400, detail="消息列表不能為空")
        
        # 檢查最後一條消息是否為用戶消息
        if request.messages[-1].role != "user":
            raise HTTPException(status_code=400, detail="最後一條消息必須是用戶消息")
        
        # 如果請求流式響應，則返回流式響應
        if request.stream:
            return StreamingResponse(
                chat_service.generate_stream_async(request),
                media_type="text/event-stream"
            )
        
        # 否則返回普通響應
        response = chat_service.generate_response(request)
        return response
    
    except Exception as e:
        logger.error(f"處理聊天請求時出錯: {str(e)}")
        raise HTTPException(status_code=500, detail=f"處理請求時出錯: {str(e)}")

@router.post("/stream", response_class=StreamingResponse)
async def chat_stream(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    生成流式聊天回應
    
    Args:
        request: 聊天請求
        chat_service: 聊天服務實例
        
    Returns:
        流式響應
    """
    logger.info(f"收到流式聊天請求: {len(request.messages)} 條消息")
    
    try:
        # 檢查消息列表是否為空
        if not request.messages:
            raise HTTPException(status_code=400, detail="消息列表不能為空")
        
        # 檢查最後一條消息是否為用戶消息
        if request.messages[-1].role != "user":
            raise HTTPException(status_code=400, detail="最後一條消息必須是用戶消息")
        
        # 強制設置為流式響應
        request.stream = True
        
        # 返回流式響應
        return StreamingResponse(
            chat_service.generate_stream_async(request),
            media_type="text/event-stream"
        )
    
    except Exception as e:
        logger.error(f"處理流式聊天請求時出錯: {str(e)}")
        raise HTTPException(status_code=500, detail=f"處理請求時出錯: {str(e)}")

@router.post("/messages", response_model=Message)
async def create_message(
    message: Message,
    background_tasks: BackgroundTasks,
    chat_service: ChatService = Depends(get_chat_service)
) -> Message:
    """
    創建新消息
    
    Args:
        message: 消息
        background_tasks: 背景任務
        chat_service: 聊天服務實例
        
    Returns:
        創建的消息
    """
    logger.info(f"收到新消息: {message.role}")
    
    try:
        # 檢查消息角色
        if message.role not in ["user", "assistant", "system"]:
            raise HTTPException(status_code=400, detail="無效的消息角色")
        
        # TODO: 保存消息到數據庫
        
        return message
    
    except Exception as e:
        logger.error(f"處理消息時出錯: {str(e)}")
        raise HTTPException(status_code=500, detail=f"處理請求時出錯: {str(e)}") 