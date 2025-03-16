"""
LLM服务模块 - 处理与DeepSeek模型的通信
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator

import openai
from openai import AsyncOpenAI

# 配置日志
logger = logging.getLogger("llm_service")

# 配置OpenAI客户端
client = AsyncOpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY", ""),
    base_url="https://api.siliconflow.cn/v1"
)

async def generate_chat_response(
    messages: List[Dict[str, str]], 
    stream: bool = False,
    temperature: float = 0.7,
    max_tokens: int = 1000
) -> Dict[str, Any]:
    """
    生成聊天回复
    
    Args:
        messages: 聊天消息列表
        stream: 是否使用流式响应
        temperature: 温度参数
        max_tokens: 最大生成令牌数
        
    Returns:
        聊天回复
    """
    try:
        # 记录请求
        logger.info(f"发送请求到DeepSeek模型，消息数: {len(messages)}")
        
        # 调用API
        response = await client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )
        
        # 返回响应
        if not stream:
            logger.info(f"收到DeepSeek模型响应，长度: {len(response.choices[0].message.content)}")
            return {
                "content": response.choices[0].message.content,
                "role": "assistant"
            }
        else:
            return response
            
    except Exception as e:
        logger.error(f"调用DeepSeek模型时出错: {str(e)}")
        return {
            "content": f"抱歉，我遇到了一些问题: {str(e)}",
            "role": "assistant"
        }

async def generate_stream_response(
    messages: List[Dict[str, str]],
    temperature: float = 0.7,
    max_tokens: int = 1000
) -> AsyncGenerator[str, None]:
    """
    生成流式聊天回复
    
    Args:
        messages: 聊天消息列表
        temperature: 温度参数
        max_tokens: 最大生成令牌数
        
    Yields:
        流式响应片段
    """
    try:
        # 记录请求
        logger.info(f"发送流式请求到DeepSeek模型，消息数: {len(messages)}")
        
        # 调用API
        stream = await client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        
        # 流式返回响应
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
                
    except Exception as e:
        logger.error(f"流式调用DeepSeek模型时出错: {str(e)}")
        yield f"抱歉，我遇到了一些问题: {str(e)}" 