from dotenv import load_dotenv
import os
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.vectorstores import Pinecone
import pinecone

def migrate_to_pinecone():
    try:
        print("開始遷移數據到Pinecone...")
        
        # 加載環境變量
        load_dotenv()
        
        # 初始化embedding模型
        embeddings = OpenAIEmbeddings(
            openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
            openai_api_base="https://api.deepseek.com/v1"
        )
        
        print("正在加載本地FAISS索引...")
        # 加載本地FAISS索引，允許反序列化
        local_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
        
        print("正在初始化Pinecone...")
        # 初始化Pinecone
        pinecone.init(
            api_key=os.getenv("PINECONE_API_KEY"),
            environment=os.getenv("PINECONE_ENVIRONMENT")
        )
        
        print("正在準備數據...")
        # 獲取所有文檔
        docs = local_db.similarity_search("")
        texts = [doc.page_content for doc in docs]
        metadatas = [doc.metadata for doc in docs]
        
        print(f"找到 {len(texts)} 個文檔")
        
        print("正在遷移到Pinecone...")
        # 創建Pinecone索引
        index_name = os.getenv("PINECONE_INDEX_NAME")
        Pinecone.from_texts(
            texts=texts,
            embedding=embeddings,
            index_name=index_name,
            metadatas=metadatas
        )
        
        print("遷移完成！")
        
    except Exception as e:
        print(f"遷移過程中發生錯誤: {str(e)}")

if __name__ == "__main__":
    migrate_to_pinecone() 