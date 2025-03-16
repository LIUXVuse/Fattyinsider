"""
Vercel部署专用配置模块 - 不使用dotenv
"""
from typing import Optional
import os

class Settings:
    """应用程序设置"""
    
    # API 密钥
    DEEPSEEK_API_KEY: str = os.environ.get("DEEPSEEK_API_KEY", "")
    PINECONE_API_KEY: str = os.environ.get("PINECONE_API_KEY", "")
    OPENAI_API_KEY: Optional[str] = os.environ.get("OPENAI_API_KEY", "")
    
    # 向量数据库配置
    PINECONE_INDEX_NAME: str = os.environ.get("PINECONE_INDEX_NAME", "fattyinsider-index")
    PINECONE_ENVIRONMENT: str = os.environ.get("PINECONE_ENVIRONMENT", "gcp-starter")
    PINECONE_NAMESPACE: str = os.environ.get("PINECONE_NAMESPACE", "default")
    USE_PINECONE: bool = os.environ.get("USE_PINECONE", "false").lower() == "true"
    VECTOR_STORE_PATH: str = "data/vector_store"
    
    # 嵌入模型
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    CHAT_MODEL: str = "deepseek-ai/DeepSeek-R1"
    
    # 文本处理配置
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 100
    
    # 应用配置
    APP_ENV: str = os.environ.get("APP_ENV", "development")
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "info")
    
    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.APP_ENV.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.APP_ENV.lower() == "development"
    
    def validate(self) -> None:
        """验证配置"""
        required_env_vars = [
            "DEEPSEEK_API_KEY"
        ]
        
        if self.USE_PINECONE:
            required_env_vars.append("PINECONE_API_KEY")
        
        missing_vars = []
        for var in required_env_vars:
            value = getattr(self, var)
            if not value or value.startswith("your-") or "your-api-key" in value.lower():
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"缺少必要的环境变量: {', '.join(missing_vars)}")

# 创建设置实例
settings = Settings() 