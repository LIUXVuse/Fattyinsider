"""
向量存儲服務 - 負責管理向量數據庫
"""
from typing import List, Dict, Any, Optional, Union
import os
from pathlib import Path
from langchain_community.vectorstores import FAISS, Pinecone
from langchain_community.embeddings import HuggingFaceEmbeddings
import time
import pinecone

from app.core.config import settings
from app.models.schemas import DocumentChunk, SearchResult
from app.utils.logger import get_logger

logger = get_logger(__name__)

class VectorStore:
    """向量存儲類"""
    
    def __init__(
        self,
        index_name: str = settings.PINECONE_INDEX_NAME,
        embedding_model: str = settings.EMBEDDING_MODEL,
        use_pinecone: bool = settings.USE_PINECONE
    ):
        """
        初始化向量存儲
        
        Args:
            index_name: 索引名稱
            embedding_model: 嵌入模型名稱
            use_pinecone: 是否使用Pinecone
        """
        try:
            self.index_name = index_name
            self.embedding_model = embedding_model
            self.use_pinecone = use_pinecone
            
            # 初始化嵌入模型
            logger.info(f"正在初始化嵌入模型: {embedding_model}")
            self.embeddings = HuggingFaceEmbeddings(
                model_name=embedding_model,
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            
            if use_pinecone:
                # 初始化Pinecone
                logger.info(f"正在初始化Pinecone: index_name={index_name}")
                pinecone.init(
                    api_key=settings.PINECONE_API_KEY,
                    environment=settings.PINECONE_ENVIRONMENT
                )
                
                # 檢查索引是否存在
                if index_name not in pinecone.list_indexes():
                    logger.warning(f"Pinecone索引 {index_name} 不存在，請在Pinecone控制台創建")
                    logger.warning(f"維度應設置為384，指標類型為cosine")
                    # 創建一個空的向量存儲
                    self.vector_store = FAISS.from_texts(
                        texts=["初始化文本"],  # 需要至少一個文本來初始化
                        embedding=self.embeddings
                    )
                else:
                    # 初始化向量存儲
                    self.vector_store = Pinecone.from_existing_index(
                        index_name=index_name,
                        embedding=self.embeddings,
                        text_key="text",
                        namespace=settings.PINECONE_NAMESPACE
                    )
                    logger.info(f"初始化Pinecone向量存儲完成: index_name={index_name}")
            else:
                # 使用本地FAISS
                self.index_path = Path(settings.VECTOR_STORE_PATH) / index_name
                os.makedirs(self.index_path.parent, exist_ok=True)
                
                # 檢查是否存在現有索引
                if self.index_path.exists() and any(self.index_path.iterdir()):
                    logger.info(f"正在加載現有 FAISS 索引: {self.index_path}")
                    self.vector_store = FAISS.load_local(
                        folder_path=str(self.index_path),
                        embeddings=self.embeddings,
                        allow_dangerous_deserialization=True
                    )
                    logger.info(f"成功加載 FAISS 索引: {self.index_path}")
                else:
                    logger.info(f"創建新的 FAISS 索引: {self.index_path}")
                    # 創建一個空的向量存儲
                    self.vector_store = FAISS.from_texts(
                        texts=["初始化文本"],  # 需要至少一個文本來初始化
                        embedding=self.embeddings
                    )
                    # 保存索引
                    self.vector_store.save_local(str(self.index_path))
                    logger.info(f"成功創建並保存 FAISS 索引: {self.index_path}")
                
                logger.info(f"初始化向量存儲完成: index_path={self.index_path}, embedding_model={embedding_model}")
        
        except Exception as e:
            logger.error(f"初始化向量存儲時出錯: {str(e)}")
            raise
    
    def add_documents(self, documents: List[DocumentChunk]) -> List[str]:
        """
        添加文檔到向量存儲
        
        Args:
            documents: 文檔分塊列表
            
        Returns:
            添加的文檔 ID 列表
        """
        logger.info(f"添加 {len(documents)} 個文檔到向量存儲")
        
        try:
            # 將 DocumentChunk 轉換為 langchain 文檔
            texts = [doc.text for doc in documents]
            metadatas = [doc.metadata for doc in documents]
            
            # 添加到向量存儲
            ids = self.vector_store.add_texts(
                texts=texts,
                metadatas=metadatas
            )
            
            # 如果是本地FAISS，保存索引
            if not self.use_pinecone:
                self.vector_store.save_local(str(self.index_path))
                logger.info(f"成功保存 FAISS 索引: {self.index_path}")
            
            return ids
        except Exception as e:
            logger.error(f"添加文檔到向量存儲時出錯: {str(e)}")
            raise
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        搜索向量存儲
        
        Args:
            query: 搜索查詢
            top_k: 返回的最大結果數量
            filter: 搜索過濾條件
            
        Returns:
            搜索結果列表
        """
        logger.info(f"搜索向量存儲: query='{query}', top_k={top_k}")
        
        try:
            # 執行相似度搜索
            results = self.vector_store.similarity_search_with_score(
                query=query,
                k=top_k,
                filter=filter
            )
            
            # 轉換結果
            search_results = []
            for doc, score in results:
                result = SearchResult(
                    text=doc.page_content,
                    metadata=doc.metadata,
                    score=score
                )
                search_results.append(result)
            
            return search_results
        except Exception as e:
            logger.error(f"搜索向量存儲時出錯: {str(e)}")
            # 返回空結果而不是拋出異常
            return []
    
    def delete(self, ids: List[str]) -> None:
        """
        從向量存儲中刪除文檔
        
        Args:
            ids: 要刪除的文檔 ID 列表
        """
        logger.info(f"從向量存儲中刪除 {len(ids)} 個文檔")
        
        if self.use_pinecone:
            try:
                index = pinecone.Index(self.index_name)
                index.delete(ids=ids, namespace=settings.PINECONE_NAMESPACE)
                logger.info(f"成功從Pinecone中刪除 {len(ids)} 個文檔")
            except Exception as e:
                logger.error(f"從Pinecone刪除文檔時出錯: {str(e)}")
        else:
            logger.warning("FAISS 不支持按 ID 刪除，此操作將被忽略")
    
    def clear(self) -> None:
        """清空向量存儲"""
        logger.warning("清空向量存儲中的所有數據")
        
        try:
            if self.use_pinecone:
                # 清空Pinecone索引
                index = pinecone.Index(self.index_name)
                index.delete(delete_all=True, namespace=settings.PINECONE_NAMESPACE)
                logger.info(f"成功清空 Pinecone 索引: {self.index_name}")
            else:
                # 創建一個新的空向量存儲
                self.vector_store = FAISS.from_texts(
                    texts=["初始化文本"],  # 需要至少一個文本來初始化
                    embedding=self.embeddings
                )
                # 保存索引
                self.vector_store.save_local(str(self.index_path))
                logger.info(f"成功清空並保存 FAISS 索引: {self.index_path}")
        except Exception as e:
            logger.error(f"清空向量存儲時出錯: {str(e)}")
            logger.info("繼續使用現有索引...") 