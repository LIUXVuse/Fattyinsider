"""
數據遷移腳本 - 將本地FAISS索引遷移到Pinecone
"""
import os
import argparse
from dotenv import load_dotenv
import pinecone
from langchain_community.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Pinecone

from app.core.config import settings
from app.utils.logger import get_logger

# 加載環境變量
load_dotenv()

logger = get_logger(__name__)

def migrate_to_pinecone():
    print("開始遷移數據到Pinecone...")
    
    # 初始化embedding模型
    embeddings = OpenAIEmbeddings(
        model="BAAI/bge-large-zh-v1.5",
        openai_api_key=settings.DEEPSEEK_API_KEY,
        openai_api_base="https://api.siliconflow.cn/v1"
    )
    
    try:
        # 加載本地FAISS索引
        print("正在加載本地FAISS索引...")
        local_store = FAISS.load_local("faiss_index", embeddings)
        
        # 初始化Pinecone
        print("正在初始化Pinecone...")
        pinecone.init(
            api_key=settings.PINECONE_API_KEY,
            environment=settings.PINECONE_ENVIRONMENT
        )
        
        # 獲取所有文檔
        print("正在準備數據...")
        docs = local_store.similarity_search("", k=10000)  # 獲取所有文檔
        texts = [doc.page_content for doc in docs]
        
        # 創建Pinecone索引
        print(f"正在將數據遷移到Pinecone索引: {settings.PINECONE_INDEX_NAME}")
        Pinecone.from_texts(
            texts=texts,
            embedding=embeddings,
            index_name=settings.PINECONE_INDEX_NAME
        )
        
        print("數據遷移完成！")
        return True
        
    except Exception as e:
        print(f"遷移過程中發生錯誤: {str(e)}")
        return False

if __name__ == "__main__":
    migrate_to_pinecone() 