"""
數據 API 路由 - 處理數據加載和管理相關的 API 請求
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File, Form, Query
import os
import tempfile
import shutil

from app.services.document_processor import DocumentProcessor
from app.services.vector_store import VectorStore
from app.services.data_loader import DataLoader
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/data", tags=["data"])

# 依賴注入
def get_document_processor() -> DocumentProcessor:
    """獲取文檔處理器實例"""
    return DocumentProcessor()

def get_vector_store() -> VectorStore:
    """獲取向量存儲實例"""
    return VectorStore()

def get_data_loader(
    document_processor: DocumentProcessor = Depends(get_document_processor),
    vector_store: VectorStore = Depends(get_vector_store)
) -> DataLoader:
    """獲取數據加載器實例"""
    return DataLoader(
        document_processor=document_processor,
        vector_store=vector_store
    )

@router.post("/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    data_loader: DataLoader = Depends(get_data_loader)
):
    """
    上傳文件並加載到向量存儲
    
    Args:
        background_tasks: 背景任務
        file: 上傳的文件
        data_loader: 數據加載器實例
        
    Returns:
        上傳結果
    """
    logger.info(f"收到文件上傳: {file.filename}")
    
    try:
        # 創建臨時文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp_file:
            # 將上傳的文件內容寫入臨時文件
            shutil.copyfileobj(file.file, temp_file)
            temp_file_path = temp_file.name
        
        # 在背景任務中加載文件
        def load_file_task():
            try:
                ids = data_loader.load_file(temp_file_path)
                logger.info(f"文件 {file.filename} 已加載，生成了 {len(ids)} 個文檔 ID")
            except Exception as e:
                logger.error(f"加載文件 {file.filename} 時出錯: {str(e)}")
            finally:
                # 刪除臨時文件
                os.unlink(temp_file_path)
        
        # 添加背景任務
        background_tasks.add_task(load_file_task)
        
        return {"message": f"文件 {file.filename} 已上傳並正在處理"}
    
    except Exception as e:
        logger.error(f"處理文件上傳時出錯: {str(e)}")
        raise HTTPException(status_code=500, detail=f"處理請求時出錯: {str(e)}")
    finally:
        # 關閉文件
        file.file.close()

@router.post("/load-directory")
async def load_directory(
    background_tasks: BackgroundTasks,
    directory: str = Form(...),
    pattern: str = Form("*.txt"),
    data_loader: DataLoader = Depends(get_data_loader)
):
    """
    加載目錄中的文件
    
    Args:
        background_tasks: 背景任務
        directory: 目錄路徑
        pattern: 文件匹配模式
        data_loader: 數據加載器實例
        
    Returns:
        加載結果
    """
    logger.info(f"收到目錄加載請求: {directory}, 模式: {pattern}")
    
    try:
        # 檢查目錄是否存在
        if not os.path.exists(directory) or not os.path.isdir(directory):
            raise HTTPException(status_code=400, detail=f"目錄不存在: {directory}")
        
        # 在背景任務中加載目錄
        def load_directory_task():
            try:
                results = data_loader.load_directory(directory, pattern)
                logger.info(f"目錄 {directory} 已加載，處理了 {len(results)} 個文件")
            except Exception as e:
                logger.error(f"加載目錄 {directory} 時出錯: {str(e)}")
        
        # 添加背景任務
        background_tasks.add_task(load_directory_task)
        
        return {"message": f"目錄 {directory} 正在處理中"}
    
    except Exception as e:
        logger.error(f"處理目錄加載請求時出錯: {str(e)}")
        raise HTTPException(status_code=500, detail=f"處理請求時出錯: {str(e)}")

@router.delete("/clear")
async def clear_data(
    confirm: bool = Query(False, description="確認清空所有數據"),
    vector_store: VectorStore = Depends(get_vector_store)
):
    """
    清空向量存儲中的所有數據
    
    Args:
        confirm: 確認清空所有數據
        vector_store: 向量存儲實例
        
    Returns:
        清空結果
    """
    logger.warning(f"收到清空數據請求, 確認: {confirm}")
    
    try:
        # 檢查確認標誌
        if not confirm:
            raise HTTPException(status_code=400, detail="必須確認清空所有數據")
        
        # 清空向量存儲
        vector_store.clear()
        
        return {"message": "所有數據已清空"}
    
    except Exception as e:
        logger.error(f"處理清空數據請求時出錯: {str(e)}")
        raise HTTPException(status_code=500, detail=f"處理請求時出錯: {str(e)}") 