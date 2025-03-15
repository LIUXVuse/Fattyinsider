"""
數據加載服務 - 負責加載和處理數據
"""
import os
import glob
from typing import List, Dict, Any, Optional
import re

from app.services.document_processor import DocumentProcessor
from app.services.vector_store import VectorStore
from app.models.schemas import DocumentChunk
from app.utils.logger import get_logger

logger = get_logger(__name__)

class DataLoader:
    """數據加載器類"""
    
    def __init__(
        self,
        document_processor: DocumentProcessor,
        vector_store: VectorStore
    ):
        """
        初始化數據加載器
        
        Args:
            document_processor: 文檔處理器實例
            vector_store: 向量存儲實例
        """
        self.document_processor = document_processor
        self.vector_store = vector_store
        logger.info("初始化數據加載器")
    
    def load_file(self, file_path: str) -> List[str]:
        """
        加載單個文件
        
        Args:
            file_path: 文件路徑
            
        Returns:
            添加的文檔 ID 列表
        """
        logger.info(f"加載文件: {file_path}")
        
        # 提取元數據
        filename = os.path.basename(file_path)
        metadata = self._extract_metadata(filename)
        
        # 處理文件
        chunks = self.document_processor.process_file(file_path, metadata)
        
        # 添加到向量存儲
        ids = self.vector_store.add_documents(chunks)
        
        logger.info(f"文件 {filename} 已加載，生成了 {len(chunks)} 個分塊")
        return ids
    
    def load_directory(self, directory_path: str, pattern: str = "*.txt") -> Dict[str, List[str]]:
        """
        加載目錄中的所有文件
        
        Args:
            directory_path: 目錄路徑
            pattern: 文件匹配模式
            
        Returns:
            文件路徑到文檔 ID 列表的映射
        """
        logger.info(f"加載目錄: {directory_path}, 模式: {pattern}")
        
        # 獲取所有匹配的文件
        file_paths = glob.glob(os.path.join(directory_path, pattern))
        
        # 加載每個文件
        results = {}
        for file_path in file_paths:
            try:
                ids = self.load_file(file_path)
                results[file_path] = ids
            except Exception as e:
                logger.error(f"加載文件 {file_path} 時出錯: {str(e)}")
        
        logger.info(f"已加載 {len(results)} 個文件")
        return results
    
    def _extract_metadata(self, filename: str) -> Dict[str, Any]:
        """
        從文件名提取元數據
        
        Args:
            filename: 文件名
            
        Returns:
            元數據字典
        """
        metadata = {
            "filename": filename,
            "type": "podcast_transcript"
        }
        
        # 提取集數信息
        episode_match = re.search(r'S(\d+)EP(\d+)', filename)
        if episode_match:
            season = int(episode_match.group(1))
            episode = int(episode_match.group(2))
            metadata["season"] = season
            metadata["episode"] = episode
            metadata["episode_id"] = f"S{season}EP{episode}"
        
        # 提取類型信息
        if "talk" in filename:
            metadata["content_type"] = "talk"
        elif "ver.1" in filename:
            metadata["content_type"] = "version1"
        elif "summaries" in filename:
            metadata["content_type"] = "summary"
        
        return metadata 