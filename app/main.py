"""
主應用程序 - FastAPI 應用程序入口點
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import time
import os
import pathlib

from app.api import chat, search, data
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# 創建 FastAPI 應用程序
app = FastAPI(
    title="Fattyinsider AI API",
    description="肥宅老司機播客內容檢索 API",
    version="0.1.0"
)

# 添加 CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生產環境中應該限制來源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加路由器
app.include_router(chat.router)
app.include_router(search.router)
app.include_router(data.router)

# 掛載靜態文件
static_dir = pathlib.Path(__file__).parent / "static"
if not static_dir.exists():
    static_dir.mkdir(parents=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 添加請求日誌中間件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """記錄請求日誌的中間件"""
    start_time = time.time()
    
    # 處理請求
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # 記錄請求日誌
        logger.info(
            f"請求: {request.method} {request.url.path} "
            f"狀態碼: {response.status_code} "
            f"處理時間: {process_time:.4f}s"
        )
        
        return response
    except Exception as e:
        # 記錄錯誤日誌
        process_time = time.time() - start_time
        logger.error(
            f"請求: {request.method} {request.url.path} "
            f"錯誤: {str(e)} "
            f"處理時間: {process_time:.4f}s"
        )
        
        # 返回錯誤響應
        return JSONResponse(
            status_code=500,
            content={"detail": f"內部服務器錯誤: {str(e)}"}
        )

# 根路由
@app.get("/", response_class=HTMLResponse)
async def root():
    """網站首頁"""
    index_path = static_dir / "index.html"
    if index_path.exists():
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        return """
        <html>
            <head>
                <title>Fattyinsider AI API</title>
            </head>
            <body>
                <h1>歡迎使用 Fattyinsider AI API</h1>
                <p>API 文檔: <a href="/docs">/docs</a></p>
            </body>
        </html>
        """

# API 根路由
@app.get("/api")
async def api_root():
    """API 根路由"""
    return {
        "message": "歡迎使用 Fattyinsider AI API",
        "version": "0.1.0",
        "docs_url": "/docs",
        "environment": settings.APP_ENV
    }

# 健康檢查路由
@app.get("/health")
async def health_check():
    """健康檢查路由"""
    return {
        "status": "healthy",
        "timestamp": time.time()
    }

# 啟動事件
@app.on_event("startup")
async def startup_event():
    """應用程序啟動事件"""
    logger.info(f"應用程序啟動，環境: {settings.APP_ENV}")
    
    # 檢查必要的環境變數
    if settings.is_production:
        try:
            settings.validate()
        except ValueError as e:
            logger.error(f"環境變數驗證失敗: {str(e)}")

# 關閉事件
@app.on_event("shutdown")
async def shutdown_event():
    """應用程序關閉事件"""
    logger.info("應用程序關閉") 