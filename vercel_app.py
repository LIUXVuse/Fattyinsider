"""
Vercel部署入口点 - 用于Vercel无服务器部署
"""
import os
import sys
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("vercel_app")

# 设置环境变量
if os.environ.get("VERCEL") == "1":
    os.environ["APP_ENV"] = "production"
    os.environ["USE_PINECONE"] = "true"
    logger.info("运行在Vercel生产环境中")
else:
    logger.info(f"运行在环境: {os.environ.get('APP_ENV', 'development')}")

# 检查必要的环境变量
required_env_vars = ["DEEPSEEK_API_KEY", "PINECONE_API_KEY", "PINECONE_INDEX_NAME"]
missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
if missing_vars:
    error_msg = f"缺少必要的环境变量: {', '.join(missing_vars)}"
    logger.error(error_msg)
    raise ValueError(error_msg)

# 创建一个简单的FastAPI应用
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Fattyinsider AI API",
    description="肥宅老司機播客內容檢索 API",
    version="0.1.0"
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 健康检查路由
@app.get("/health")
async def health_check():
    """健康检查路由"""
    try:
        return {
            "status": "healthy",
            "environment": os.environ.get("APP_ENV", "development"),
            "vercel": os.environ.get("VERCEL", "false")
        }
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}, 500

# 根路由
@app.get("/")
async def root():
    """网站首页"""
    return {
        "message": "欢迎使用 Fattyinsider AI API",
        "version": "0.1.0",
        "docs_url": "/docs",
        "environment": os.environ.get("APP_ENV", "development")
    }

# 这是Vercel需要的入口点
# Vercel会自动识别这个文件并使用它来启动应用程序 