"""
向量存儲服務 - 負責管理向量數據庫
"""
from typing import List, Dict, Any, Optional, Union
import os
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
import time
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec

from app.core.config import settings
from app.models.schemas import DocumentChunk, SearchResult
from app.utils.logger import get_logger

logger = get_logger(__name__)

class VectorStore:
    """向量存儲類"""
    
    def __init__(self, embedding_model: str = None):
        """初始化向量存儲
        
        Args:
            embedding_model: 嵌入模型名稱
        """
        self.embedding_model = embedding_model or settings.EMBEDDING_MODEL
        self.embeddings = None
        self.vector_store = None
        
        try:
            print(f"正在初始化嵌入模型: {self.embedding_model}")
            self.embeddings = HuggingFaceEmbeddings(
                model_name=self.embedding_model,
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            self.vector_store = self._init_vector_store()
        except Exception as e:
            print(f"初始化向量存儲時出錯: {str(e)}")
            raise
    
    def _init_vector_store(self):
        """初始化向量存儲"""
        if settings.USE_PINECONE:
            # 初始化 Pinecone
            pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            
            # 檢查索引是否存在
            if settings.PINECONE_INDEX_NAME not in pc.list_indexes().names():
                # 創建索引
                pc.create_index(
                    name=settings.PINECONE_INDEX_NAME,
                    dimension=384,  # sentence-transformers/all-MiniLM-L6-v2 的維度
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='aws',
                        region='us-west-2'
                    )
                )
            
            # 獲取索引
            index = pc.Index(settings.PINECONE_INDEX_NAME)
            
            # 創建 LangChain 向量存儲
            return PineconeVectorStore(
                pinecone_api_key=settings.PINECONE_API_KEY,
                index_name=settings.PINECONE_INDEX_NAME,
                embedding=self.embeddings,
                text_key="text"
            )
        else:
            # 使用本地 FAISS 向量存儲
            try:
                return FAISS.load_local("faiss_index", self.embeddings)
            except:
                return FAISS.from_texts(["初始化向量库"], self.embeddings)
    
    def save(self):
        """保存向量存儲"""
        if not settings.USE_PINECONE and self.vector_store:
            self.vector_store.save_local("faiss_index")
    
    def clear(self):
        """清空向量存儲"""
        if settings.USE_PINECONE:
            # 清空 Pinecone 索引
            pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            index = pc.Index(settings.PINECONE_INDEX_NAME)
            index.delete(delete_all=True)
        else:
            # 重新初始化本地向量存儲
            self.vector_store = FAISS.from_texts(["初始化向量库"], self.embeddings)
            self.save()
    
    def add_documents(self, documents: List[DocumentChunk]) -> List[str]:
        """添加文檔到向量存儲
        
        Args:
            documents: 文檔列表
            
        Returns:
            文檔ID列表
        """
        try:
            logger.info(f"添加 {len(documents)} 個文檔到向量存儲")
            
            # 準備文檔
            texts = [doc.text for doc in documents]
            metadatas = [doc.metadata for doc in documents]
            
            # 添加到向量存儲
            ids = self.vector_store.add_texts(
                texts=texts,
                metadatas=metadatas
            )
            
            # 如果是本地FAISS，保存索引
            if not settings.USE_PINECONE:
                self.save()
            
            logger.info(f"成功添加 {len(ids)} 個文檔")
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
        
        if settings.USE_PINECONE:
            try:
                index = pinecone.Index(settings.PINECONE_INDEX_NAME)
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
            if settings.USE_PINECONE:
                # 清空Pinecone索引
                index = pinecone.Index(settings.PINECONE_INDEX_NAME)
                index.delete(delete_all=True, namespace=settings.PINECONE_NAMESPACE)
                logger.info(f"成功清空 Pinecone 索引: {settings.PINECONE_INDEX_NAME}")
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