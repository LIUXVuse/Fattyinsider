"""
文檔處理服務 - 負責處理和分塊文檔
"""
import os
from typing import List, Dict, Any, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.models.schemas import DocumentChunk
from app.utils.logger import get_logger

logger = get_logger(__name__)

class DocumentProcessor:
    """文檔處理器類"""
    
    def __init__(
        self,
        chunk_size: int = 500,  # 從1000減小到500
        chunk_overlap: int = 100  # 從200減小到100
    ):
        """
        初始化文檔處理器
        
        Args:
            chunk_size: 文本分塊大小
            chunk_overlap: 文本分塊重疊大小
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
            separators=["\n\n", "\n", "。", "，", "；", "：", "！", "？", " ", ""]  # 添加更多中文分隔符
        )
        logger.info(f"初始化文檔處理器: chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")
    
    def process_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[DocumentChunk]:
        """
        處理文本並分塊
        
        Args:
            text: 要處理的文本
            metadata: 文檔元數據
            
        Returns:
            文檔分塊列表
        """
        if metadata is None:
            metadata = {}
            
        # 分割文本
        chunks = self.text_splitter.split_text(text)
        logger.debug(f"文本已分割為 {len(chunks)} 個塊")
        
        # 創建文檔分塊
        doc_chunks = []
        for i, chunk_text in enumerate(chunks):
            # 為每個分塊創建元數據副本，並添加分塊索引
            chunk_metadata = metadata.copy()
            chunk_metadata["chunk_index"] = i
            
            # 創建文檔分塊
            doc_chunk = DocumentChunk(
                text=chunk_text,
                metadata=chunk_metadata
            )
            doc_chunks.append(doc_chunk)
        
        return doc_chunks
    
    def process_file(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> List[DocumentChunk]:
        """
        處理文件並分塊
        
        Args:
            file_path: 文件路徑
            metadata: 文檔元數據
            
        Returns:
            文檔分塊列表
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
            
        if metadata is None:
            metadata = {}
            
        # 添加文件元數據
        file_metadata = {
            "source": file_path,
            "filename": os.path.basename(file_path)
        }
        metadata.update(file_metadata)
        
        # 讀取文件
        logger.info(f"正在處理文件: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
            
        # 處理文本
        return self.process_text(text, metadata) 