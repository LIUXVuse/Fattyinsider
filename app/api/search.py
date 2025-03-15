"""
搜索 API 路由 - 處理搜索相關的 API 請求
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from app.models.schemas import SearchQuery, SearchResult
from app.services.vector_store import VectorStore
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/search", tags=["search"])

# 依賴注入
def get_vector_store() -> VectorStore:
    """獲取向量存儲實例"""
    return VectorStore()

@router.post("/query", response_model=List[SearchResult])
async def search_query(
    query: SearchQuery,
    vector_store: VectorStore = Depends(get_vector_store)
) -> List[SearchResult]:
    """
    執行搜索查詢
    
    Args:
        query: 搜索查詢
        vector_store: 向量存儲實例
        
    Returns:
        搜索結果列表
    """
    logger.info(f"收到搜索查詢: {query.query}")
    
    try:
        # 執行搜索
        results = vector_store.search(
            query=query.query,
            top_k=query.top_k,
            filter=query.filter
        )
        
        return results
    
    except Exception as e:
        logger.error(f"處理搜索查詢時出錯: {str(e)}")
        raise HTTPException(status_code=500, detail=f"處理請求時出錯: {str(e)}")

@router.get("/simple", response_model=List[SearchResult])
async def simple_search(
    q: str = Query(..., description="搜索查詢文本"),
    top_k: int = Query(5, description="返回的最大結果數量"),
    vector_store: VectorStore = Depends(get_vector_store)
) -> List[SearchResult]:
    """
    執行簡單搜索
    
    Args:
        q: 搜索查詢文本
        top_k: 返回的最大結果數量
        vector_store: 向量存儲實例
        
    Returns:
        搜索結果列表
    """
    logger.info(f"收到簡單搜索: {q}")
    
    try:
        # 執行搜索
        results = vector_store.search(
            query=q,
            top_k=top_k
        )
        
        return results
    
    except Exception as e:
        logger.error(f"處理簡單搜索時出錯: {str(e)}")
        raise HTTPException(status_code=500, detail=f"處理請求時出錯: {str(e)}")

@router.get("/episodes/{episode_id}", response_model=List[SearchResult])
async def search_by_episode(
    episode_id: str,
    q: Optional[str] = Query(None, description="搜索查詢文本"),
    top_k: int = Query(10, description="返回的最大結果數量"),
    vector_store: VectorStore = Depends(get_vector_store)
) -> List[SearchResult]:
    """
    按集數搜索
    
    Args:
        episode_id: 集數 ID (例如: S3EP201)
        q: 搜索查詢文本
        top_k: 返回的最大結果數量
        vector_store: 向量存儲實例
        
    Returns:
        搜索結果列表
    """
    logger.info(f"收到按集數搜索: {episode_id}, 查詢: {q}")
    
    try:
        # 創建過濾條件
        filter = {"episode_id": episode_id}
        
        # 如果有查詢文本，則執行相似度搜索
        if q:
            results = vector_store.search(
                query=q,
                top_k=top_k,
                filter=filter
            )
        else:
            # TODO: 實現按元數據過濾的搜索
            raise HTTPException(status_code=501, detail="尚未實現按元數據過濾的搜索")
        
        return results
    
    except Exception as e:
        logger.error(f"處理按集數搜索時出錯: {str(e)}")
        raise HTTPException(status_code=500, detail=f"處理請求時出錯: {str(e)}") 