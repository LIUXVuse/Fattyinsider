"""
數據遷移腳本 - 將本地FAISS索引遷移到Pinecone
"""
import os
import argparse
from dotenv import load_dotenv
import pinecone
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

from app.core.config import settings
from app.utils.logger import get_logger

# 加載環境變量
load_dotenv()

logger = get_logger(__name__)

def migrate_faiss_to_pinecone(
    index_name: str = settings.PINECONE_INDEX_NAME,
    embedding_model: str = settings.EMBEDDING_MODEL,
    batch_size: int = 100
):
    """
    將本地FAISS索引遷移到Pinecone
    
    Args:
        index_name: Pinecone索引名稱
        embedding_model: 嵌入模型名稱
        batch_size: 批處理大小
    """
    # 初始化嵌入模型
    logger.info(f"初始化嵌入模型: {embedding_model}")
    embeddings = HuggingFaceEmbeddings(
        model_name=embedding_model,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    # 加載本地FAISS索引
    local_index_path = os.path.join(settings.VECTOR_STORE_PATH, index_name)
    logger.info(f"加載本地FAISS索引: {local_index_path}")
    local_db = FAISS.load_local(
        folder_path=local_index_path,
        embeddings=embeddings,
        allow_dangerous_deserialization=True
    )
    
    # 初始化Pinecone
    logger.info(f"初始化Pinecone: {index_name}")
    pinecone.init(
        api_key=settings.PINECONE_API_KEY,
        environment=settings.PINECONE_ENVIRONMENT
    )
    
    # 檢查索引是否存在
    if index_name not in pinecone.list_indexes():
        logger.warning(f"Pinecone索引 {index_name} 不存在，請在Pinecone控制台創建")
        logger.warning(f"維度應設置為384，指標類型為cosine")
        return
    
    # 獲取所有文檔
    logger.info("獲取本地索引中的所有文檔")
    docs = local_db.similarity_search("", k=10000)  # 獲取所有文檔
    logger.info(f"找到 {len(docs)} 個文檔")
    
    # 將文檔添加到Pinecone
    logger.info(f"將 {len(docs)} 個文檔添加到Pinecone")
    from langchain_community.vectorstores import Pinecone as PineconeVS
    
    # 批量處理
    for i in range(0, len(docs), batch_size):
        batch = docs[i:i+batch_size]
        logger.info(f"處理批次 {i//batch_size + 1}/{(len(docs)-1)//batch_size + 1}: {len(batch)} 個文檔")
        
        if i == 0:
            # 第一批，創建索引
            pinecone_db = PineconeVS.from_documents(
                documents=batch,
                embedding=embeddings,
                index_name=index_name,
                namespace=settings.PINECONE_NAMESPACE
            )
        else:
            # 後續批次，添加到現有索引
            pinecone_db = PineconeVS.from_existing_index(
                index_name=index_name,
                embedding=embeddings,
                namespace=settings.PINECONE_NAMESPACE
            )
            pinecone_db.add_documents(documents=batch)
    
    logger.info("遷移完成")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="將本地FAISS索引遷移到Pinecone")
    parser.add_argument("--index-name", type=str, default=settings.PINECONE_INDEX_NAME, help="Pinecone索引名稱")
    parser.add_argument("--embedding-model", type=str, default=settings.EMBEDDING_MODEL, help="嵌入模型名稱")
    parser.add_argument("--batch-size", type=int, default=100, help="批處理大小")
    
    args = parser.parse_args()
    
    migrate_faiss_to_pinecone(
        index_name=args.index_name,
        embedding_model=args.embedding_model,
        batch_size=args.batch_size
    ) 