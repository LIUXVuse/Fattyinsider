"""
數據加載腳本 - 加載播客逐字稿數據到向量存儲
"""
import os
import argparse
import time
from dotenv import load_dotenv

from app.services.document_processor import DocumentProcessor
from app.services.vector_store import VectorStore
from app.services.data_loader import DataLoader
from app.utils.logger import get_logger

# 加載環境變數
load_dotenv()

logger = get_logger(__name__)

def main():
    """主函數"""
    # 解析命令行參數
    parser = argparse.ArgumentParser(description="加載播客逐字稿數據到向量存儲")
    parser.add_argument("--directory", type=str, default="S3EP201_204", help="數據目錄路徑")
    parser.add_argument("--pattern", type=str, default="*.txt", help="文件匹配模式")
    parser.add_argument("--clear", action="store_true", help="是否清空現有數據")
    args = parser.parse_args()
    
    # 初始化服務
    logger.info("初始化文檔處理器和向量存儲服務...")
    document_processor = DocumentProcessor()
    vector_store = VectorStore()
    data_loader = DataLoader(
        document_processor=document_processor,
        vector_store=vector_store
    )
    
    # 檢查目錄是否存在
    if not os.path.exists(args.directory) or not os.path.isdir(args.directory):
        logger.error(f"目錄不存在: {args.directory}")
        return
    
    # 清空現有數據
    if args.clear:
        logger.info("嘗試清空現有數據...")
        try:
            vector_store.clear()
            logger.info("成功清空現有數據")
        except Exception as e:
            logger.error(f"清空數據時出錯: {str(e)}")
            logger.info("繼續加載數據到現有索引...")
    
    # 加載數據
    logger.info(f"開始加載數據: 目錄={args.directory}, 模式={args.pattern}")
    start_time = time.time()
    
    try:
        results = data_loader.load_directory(args.directory, args.pattern)
        
        # 輸出結果
        total_files = len(results)
        total_chunks = sum(len(ids) for ids in results.values())
        elapsed_time = time.time() - start_time
        
        logger.info(f"數據加載完成: 處理了 {total_files} 個文件，生成了 {total_chunks} 個分塊")
        logger.info(f"總耗時: {elapsed_time:.2f} 秒")
        
        # 輸出每個文件的詳細信息
        for file_path, ids in results.items():
            logger.info(f"文件 {os.path.basename(file_path)}: 生成了 {len(ids)} 個分塊")
    except Exception as e:
        logger.error(f"加載數據時出錯: {str(e)}")
        return

if __name__ == "__main__":
    main() 