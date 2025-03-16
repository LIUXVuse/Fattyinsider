from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Keys
    DEEPSEEK_API_KEY: str
    PINECONE_API_KEY: str = ""
    
    # Pinecone 配置
    PINECONE_INDEX_NAME: str = "fattyinsider"
    PINECONE_ENVIRONMENT: str = "gcp-starter"  # Pinecone 免费版环境
    USE_PINECONE: bool = True
    
    # 应用配置
    APP_ENV: str = "development"
    LOG_LEVEL: str = "info"
    
    class Config:
        env_file = ".env"

settings = Settings() 