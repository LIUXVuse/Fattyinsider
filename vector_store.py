from langchain.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS, Pinecone
from settings import settings
import pinecone

# 使用硅基流动的 embedding 模型
embeddings = OpenAIEmbeddings(
    model="BAAI/bge-large-zh-v1.5",  # 使用硅基流动的中文 embedding 模型
    openai_api_key=settings.DEEPSEEK_API_KEY,
    openai_api_base="https://api.siliconflow.cn/v1"
)

def init_vector_store():
    """初始化向量存储"""
    if settings.USE_PINECONE:
        # 初始化 Pinecone
        pinecone.init(
            api_key=settings.PINECONE_API_KEY,
            environment=settings.PINECONE_ENVIRONMENT
        )
        
        # 获取或创建 Pinecone 索引
        return Pinecone.from_existing_index(
            index_name=settings.PINECONE_INDEX_NAME,
            embedding=embeddings
        )
    else:
        # 使用本地 FAISS 向量存储
        try:
            return FAISS.load_local("faiss_index", embeddings)
        except:
            return FAISS.from_texts(["初始化向量库"], embeddings)

# 初始化向量存储
vector_store = init_vector_store() 