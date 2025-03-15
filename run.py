"""
啟動腳本 - 啟動 FastAPI 應用程序
"""
import uvicorn
import argparse
import os
from dotenv import load_dotenv

# 加載環境變數
load_dotenv()

def main():
    """主函數"""
    # 解析命令行參數
    parser = argparse.ArgumentParser(description="啟動 Fattyinsider AI API 服務")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="主機地址")
    parser.add_argument("--port", type=int, default=8000, help="端口號")
    parser.add_argument("--reload", action="store_true", help="是否啟用熱重載")
    parser.add_argument("--workers", type=int, default=1, help="工作進程數")
    parser.add_argument("--env", type=str, default=None, help="環境 (development, production)")
    args = parser.parse_args()
    
    # 設置環境變數
    if args.env:
        os.environ["APP_ENV"] = args.env
    
    # 啟動服務器
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers
    )

if __name__ == "__main__":
    main() 