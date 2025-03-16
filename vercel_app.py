"""
Vercel部署入口点 - 用于Vercel无服务器部署
"""
import os
import sys
from dotenv import load_dotenv
from loguru import logger

# 配置日志 - 只使用stderr，避免文件系统操作
logger.remove()
logger.add(sys.stderr, level="INFO")

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

try:
    # 导入FastAPI应用
    from app.main import app
    logger.info("成功导入FastAPI应用")
except Exception as e:
    error_msg = f"导入FastAPI应用失败: {str(e)}"
    logger.error(error_msg)
    raise ImportError(error_msg)

# 添加错误处理中间件
@app.middleware("http")
async def error_handling_middleware(request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        error_msg = f"请求处理错误: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg, "status": "error"}, 500

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

# 这是Vercel需要的入口点
# Vercel会自动识别这个文件并使用它来启动应用程序 