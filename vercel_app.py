"""
Vercel部署入口點 - 用於Vercel無服務器部署
"""
import os
from dotenv import load_dotenv

# 加載環境變量
load_dotenv()

# 設置環境變量
if os.environ.get("VERCEL_ENV") == "production":
    os.environ["APP_ENV"] = "production"
    os.environ["USE_PINECONE"] = "true"

# 導入FastAPI應用
from app.main import app

# 這是Vercel需要的入口點
# Vercel會自動識別這個文件並使用它來啟動應用程序 