"""
聊天服務 - 負責處理聊天請求和生成回應
"""
from typing import List, Dict, Any, Optional, Generator, Union
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
import os

from app.core.config import settings
from app.models.schemas import Message, ChatRequest, ChatResponse, SearchResult
from app.services.vector_store import VectorStore
from app.utils.logger import get_logger

logger = get_logger(__name__)

class ChatService:
    """聊天服務類"""
    
    def __init__(
        self,
        vector_store: VectorStore,
        model_name: str = "deepseek-ai/DeepSeek-R1",  # 默認使用DeepSeek R1模型
        temperature: float = 0.7
    ):
        """
        初始化聊天服務
        
        Args:
            vector_store: 向量存儲實例
            model_name: 聊天模型名稱
            temperature: 溫度參數
        """
        self.vector_store = vector_store
        self.model_name = model_name
        self.temperature = temperature
        
        # 初始化LLM模型
        try:
            if model_name != "simple-response":
                self.llm = ChatOpenAI(
                    model=model_name,
                    temperature=temperature,
                    openai_api_key=settings.DEEPSEEK_API_KEY,
                    openai_api_base="https://api.siliconflow.cn/v1",
                    streaming=True
                )
                logger.info(f"成功初始化LLM模型: {model_name}")
            else:
                self.llm = None
                logger.info("使用簡單回應模式，不初始化LLM模型")
        except Exception as e:
            logger.error(f"初始化LLM模型時出錯: {str(e)}")
            logger.info("回退到簡單回應模式")
            self.model_name = "simple-response"
            self.llm = None
        
        logger.info(f"初始化聊天服務: model_name={model_name}, temperature={temperature}")
    
    def _format_chat_history(self, messages: List[Message]) -> List[Union[HumanMessage, AIMessage, SystemMessage]]:
        """
        格式化聊天歷史
        
        Args:
            messages: 聊天消息列表
            
        Returns:
            格式化後的聊天歷史
        """
        formatted_messages = []
        
        for message in messages:
            if message.role == "user":
                formatted_messages.append(HumanMessage(content=message.content))
            elif message.role == "assistant":
                formatted_messages.append(AIMessage(content=message.content))
            elif message.role == "system":
                formatted_messages.append(SystemMessage(content=message.content))
        
        return formatted_messages
    
    def _search_relevant_context(self, query: str, top_k: int = 5) -> str:
        """
        搜索相關上下文
        
        Args:
            query: 搜索查詢
            top_k: 返回的最大結果數量
            
        Returns:
            相關上下文文本
        """
        # 搜索向量存儲
        search_results = self.vector_store.search(query=query, top_k=top_k)
        
        # 格式化搜索結果
        context_texts = []
        for i, result in enumerate(search_results):
            source = result.metadata.get("source", "未知來源")
            episode = os.path.basename(source).replace(".txt", "")
            context_text = f"[{i+1}] {result.text}\n來源: {episode}\n"
            context_texts.append(context_text)
        
        # 合併上下文
        context = "\n".join(context_texts)
        return context
    
    def generate_response(self, request: ChatRequest) -> ChatResponse:
        """
        生成聊天回應
        
        Args:
            request: 聊天請求
            
        Returns:
            聊天回應
        """
        logger.info(f"處理聊天請求: {len(request.messages)} 條消息")
        
        # 獲取用戶最後一條消息
        user_message = request.messages[-1].content
        
        # 搜索相關上下文
        context = self._search_relevant_context(user_message)
        
        # 根據模型類型生成回應
        if self.model_name == "simple-response" or self.llm is None:
            # 使用簡單回應模式
            response_content = self._generate_simple_response(user_message, context)
        else:
            # 使用LLM生成回應
            response_content = self._generate_llm_response(request.messages, context)
        
        # 創建回應
        chat_response = ChatResponse(
            message=Message(role="assistant", content=response_content),
            sources=[]  # TODO: 添加來源引用
        )
        
        return chat_response
    
    def _generate_llm_response(self, messages: List[Message], context: str) -> str:
        """
        使用LLM生成回應
        
        Args:
            messages: 聊天消息列表
            context: 相關上下文
            
        Returns:
            LLM生成的回應
        """
        try:
            # 構建系統提示
            system_prompt = f"""你是肥宅老司機播客的AI助手，負責回答用戶關於播客內容的問題。
            請根據以下相關上下文，簡潔扼要地回答用戶問題。
            如果上下文中沒有相關信息，請誠實告知用戶你不知道，不要編造信息。
            
            相關上下文:
            {context}
            """
            
            # 準備消息列表
            formatted_messages = [{"role": "system", "content": system_prompt}]
            
            # 添加用戶消息
            for message in messages:
                if message.role != "system":  # 跳過系統消息，因為我們已經添加了自定義的系統提示
                    formatted_messages.append({"role": message.role, "content": message.content})
            
            # 調用LLM生成回應
            response = self.llm.invoke(formatted_messages, stream=False)
            return response.content
        except Exception as e:
            logger.error(f"使用LLM生成回應時出錯: {str(e)}")
            # 回退到簡單回應模式
            return self._generate_simple_response(messages[-1].content, context)
    
    def _generate_simple_response(self, query: str, context: str) -> str:
        """
        生成簡單回應
        
        Args:
            query: 用戶查詢
            context: 相關上下文
            
        Returns:
            簡單回應
        """
        if not context:
            return "抱歉，我沒有找到與您問題相關的信息。請嘗試其他問題，或者使用搜索功能直接查找播客內容。"
        
        # 根據查詢關鍵詞生成簡單回應
        if "肥宅老司機" in query:
            return "肥宅老司機是一個由 Manny 和 Ethan 主持的中文科技播客，討論各種科技話題、遊戲、電影和流行文化。以下是我從播客內容中找到的相關信息：\n\n" + context
        elif "播客" in query or "podcast" in query.lower():
            return "肥宅老司機是一個受歡迎的中文科技播客，以下是我從播客內容中找到的相關信息：\n\n" + context
        elif "主持人" in query or "誰主持" in query:
            return "肥宅老司機播客由 Manny 和 Ethan 主持。以下是我從播客內容中找到的相關信息：\n\n" + context
        else:
            return f"以下是關於「{query}」的相關信息：\n\n" + context
    
    def generate_stream(self, request: ChatRequest) -> Generator[str, None, None]:
        """
        生成流式聊天回應
        
        Args:
            request: 聊天請求
            
        Returns:
            流式回應生成器
        """
        logger.info(f"處理流式聊天請求: {len(request.messages)} 條消息")
        
        # 獲取用戶最後一條消息
        user_message = request.messages[-1].content
        
        # 搜索相關上下文
        context = self._search_relevant_context(user_message)
        
        # 根據模型類型生成流式回應
        if self.model_name == "simple-response" or self.llm is None:
            # 使用簡單回應模式模擬流式回應
            response_content = self._generate_simple_response(user_message, context)
            words = response_content.split()
            for i in range(0, len(words), 3):
                chunk = " ".join(words[i:i+3])
                yield chunk + " "
        else:
            try:
                # 構建系統提示
                system_prompt = f"""你是肥宅老司機播客的AI助手，負責回答用戶關於播客內容的問題。
                請根據以下相關上下文，簡潔扼要地回答用戶問題。
                如果上下文中沒有相關信息，請誠實告知用戶你不知道，不要編造信息。
                
                相關上下文:
                {context}
                """
                
                # 準備消息列表
                formatted_messages = [{"role": "system", "content": system_prompt}]
                
                # 添加用戶消息
                for message in request.messages:
                    if message.role != "system":
                        formatted_messages.append({"role": message.role, "content": message.content})
                
                # 使用LLM生成流式回應
                stream = self.llm.invoke(formatted_messages, stream=True)
                for chunk in stream:
                    if chunk.content:
                        yield chunk.content
            except Exception as e:
                logger.error(f"使用LLM生成流式回應時出錯: {str(e)}")
                # 回退到簡單回應模式
                response_content = self._generate_simple_response(user_message, context)
                words = response_content.split()
                for i in range(0, len(words), 3):
                    chunk = " ".join(words[i:i+3])
                    yield chunk + " " 