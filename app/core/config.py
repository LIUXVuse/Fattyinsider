"""
配置模塊 - 管理應用程序配置
"""
from typing import Optional, Dict, Any, List
from pydantic import Field, validator
from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    """應用程序設置"""
    
    # API 密鑰
    DEEPSEEK_API_KEY: str = Field(..., env="DEEPSEEK_API_KEY")
    PINECONE_API_KEY: str = Field(..., env="PINECONE_API_KEY")
    OPENAI_API_KEY: Optional[str] = Field(None, env="OPENAI_API_KEY")  # 可選的 OpenAI API 密鑰
    
    # 向量數據庫配置
    PINECONE_INDEX_NAME: str = Field("fattyinsider-index", env="PINECONE_INDEX_NAME")
    PINECONE_ENVIRONMENT: str = Field("gcp-starter", env="PINECONE_ENVIRONMENT")
    PINECONE_NAMESPACE: str = Field("default", env="PINECONE_NAMESPACE")
    USE_PINECONE: bool = Field(False, env="USE_PINECONE")
    VECTOR_STORE_PATH: str = "data/vector_store"  # 本地向量存儲路徑
    
    # 嵌入模型
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"  # 使用 HuggingFace 的模型
    CHAT_MODEL: str = "deepseek-ai/DeepSeek-R1"  # DeepSeek 聊天模型
    
    # 文本處理配置
    CHUNK_SIZE: int = 500  # 文本分塊大小
    CHUNK_OVERLAP: int = 100  # 文本分塊重疊大小
    
    # 應用配置
    APP_ENV: str = Field("development", env="APP_ENV")
    LOG_LEVEL: str = Field("info", env="LOG_LEVEL")
    
    # 計算屬性
    @property
    def is_production(self) -> bool:
        """是否為生產環境"""
        return self.APP_ENV.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """是否為開發環境"""
        return self.APP_ENV.lower() == "development"
    
    # 驗證方法
    def validate(self) -> None:
        """驗證配置"""
        required_env_vars = [
            "DEEPSEEK_API_KEY"
        ]
        
        # 如果使用Pinecone，則需要Pinecone API密鑰
        if self.USE_PINECONE:
            required_env_vars.append("PINECONE_API_KEY")
        
        missing_vars = []
        for var in required_env_vars:
            value = getattr(self, var)
            if not value or value.startswith("your-") or "your-api-key" in value.lower():
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"缺少必要的環境變數: {', '.join(missing_vars)}")

# 創建設置實例
settings = Settings() 