"""
向量数据库服务模块 - 处理与Pinecone的通信
"""
import os
import logging
from typing import List, Dict, Any, Optional

import pinecone

# 配置日志
logger = logging.getLogger("vector_service")

# Pinecone配置
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY", "")
PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "fattyinsider-index")
PINECONE_ENVIRONMENT = os.environ.get("PINECONE_ENVIRONMENT", "gcp-starter")
PINECONE_NAMESPACE = os.environ.get("PINECONE_NAMESPACE", "default")

# 初始化Pinecone
def init_pinecone():
    """初始化Pinecone客户端"""
    try:
        pinecone.init(
            api_key=PINECONE_API_KEY,
            environment=PINECONE_ENVIRONMENT
        )
        logger.info(f"Pinecone初始化成功，环境: {PINECONE_ENVIRONMENT}")
        
        # 检查索引是否存在
        if PINECONE_INDEX_NAME not in pinecone.list_indexes():
            logger.warning(f"Pinecone索引 {PINECONE_INDEX_NAME} 不存在")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Pinecone初始化失败: {str(e)}")
        return False

# 搜索相关内容
async def search_similar_content(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    搜索与查询相似的内容
    
    Args:
        query: 查询文本
        top_k: 返回结果数量
        
    Returns:
        相似内容列表
    """
    try:
        # 初始化Pinecone
        if not init_pinecone():
            return []
            
        # 获取索引
        index = pinecone.Index(PINECONE_INDEX_NAME)
        
        # 查询向量数据库
        # 注意：这里需要先将查询文本转换为向量
        # 由于我们目前没有嵌入模型，这里只是一个示例
        # 实际使用时需要添加嵌入模型
        vector = [0.1] * 384  # 示例向量，实际应使用嵌入模型生成
        
        results = index.query(
            vector=vector,
            top_k=top_k,
            namespace=PINECONE_NAMESPACE,
            include_metadata=True
        )
        
        # 处理结果
        similar_contents = []
        for match in results.matches:
            if match.score > 0.7:  # 相似度阈值
                similar_contents.append({
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata
                })
                
        logger.info(f"查询Pinecone成功，找到 {len(similar_contents)} 条相似内容")
        return similar_contents
        
    except Exception as e:
        logger.error(f"查询Pinecone时出错: {str(e)}")
        return [] 