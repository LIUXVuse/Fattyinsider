"""
Vercel部署入口点 - 用于Vercel无服务器部署
"""
import os
from dotenv import load_dotenv

# 尝试加载环境变量，如果.env文件存在
try:
    load_dotenv()
except:
    pass

# 设置环境变量
if os.environ.get("VERCEL") == "1":
    os.environ["APP_ENV"] = "production"
    os.environ["USE_PINECONE"] = "true"
    print("Running in Vercel production environment")
else:
    print(f"Running in environment: {os.environ.get('APP_ENV', 'development')}")

# 导入FastAPI应用
from app.main import app

# 这是Vercel需要的入口点
# Vercel会自动识别这个文件并使用它来启动应用程序 