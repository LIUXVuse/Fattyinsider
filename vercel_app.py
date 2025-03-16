"""
Vercel部署入口点 - 集成LLM和向量数据库
"""
import os
import sys
import json
import logging
import asyncio
import httpx
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

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

# 定义LLM服务函数
async def generate_chat_response(messages, stream=False, temperature=0.7, max_tokens=1000):
    """
    生成聊天回复，调用DeepSeek API
    """
    try:
        # 记录请求
        logger.info(f"处理聊天请求，消息数: {len(messages)}")
        
        # 获取API密钥
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        if not api_key:
            logger.error("未设置DEEPSEEK_API_KEY环境变量")
            return {
                "content": "抱歉，系统未配置API密钥，无法连接到DeepSeek模型。",
                "role": "assistant"
            }
        
        # 准备请求数据
        request_data = {
            "model": "deepseek-ai/DeepSeek-R1",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        # 调用DeepSeek API
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.siliconflow.cn/v1/chat/completions",
                json=request_data,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
            )
            
            # 检查响应状态
            if response.status_code != 200:
                logger.error(f"DeepSeek API请求失败: {response.status_code} {response.text}")
                return {
                    "content": f"抱歉，调用DeepSeek API时出错: HTTP {response.status_code}",
                    "role": "assistant"
                }
            
            # 解析响应
            response_data = response.json()
            logger.info(f"收到DeepSeek API响应: {response_data}")
            
            # 提取回复内容
            if "choices" in response_data and len(response_data["choices"]) > 0:
                content = response_data["choices"][0]["message"]["content"]
                return {
                    "content": content,
                    "role": "assistant"
                }
            else:
                logger.error(f"DeepSeek API响应格式错误: {response_data}")
                return {
                    "content": "抱歉，无法解析DeepSeek API的响应。",
                    "role": "assistant"
                }
            
    except Exception as e:
        logger.error(f"生成回复时出错: {str(e)}")
        return {
            "content": f"抱歉，我遇到了一些问题: {str(e)}",
            "role": "assistant"
        }

# HTML页面模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>肥宅老司機 AI 聊天機器人</title>
    <style>
        body {
            font-family: 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        h1 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
        }
        .chat-container {
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 20px;
            margin-bottom: 20px;
        }
        .chat-messages {
            height: 400px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 10px;
            margin-bottom: 15px;
            background-color: #f9f9f9;
        }
        .message {
            margin-bottom: 10px;
            padding: 8px 12px;
            border-radius: 18px;
            max-width: 80%;
            word-wrap: break-word;
        }
        .user-message {
            background-color: #dcf8c6;
            margin-left: auto;
            border-bottom-right-radius: 5px;
        }
        .bot-message {
            background-color: #e5e5ea;
            margin-right: auto;
            border-bottom-left-radius: 5px;
        }
        .input-area {
            display: flex;
        }
        #message-input {
            flex: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
        }
        #send-button {
            padding: 10px 20px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            margin-left: 10px;
            cursor: pointer;
            font-size: 16px;
        }
        #send-button:hover {
            background-color: #45a049;
        }
        .status {
            text-align: center;
            color: #666;
            font-style: italic;
            margin-top: 10px;
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            color: #666;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <h1>肥宅老司機 AI 聊天機器人</h1>
    
    <div class="chat-container">
        <div class="chat-messages" id="chat-messages">
            <div class="message bot-message">你好！我是肥宅老司機 AI 聊天機器人。有什麼我能幫你的嗎？</div>
        </div>
        
        <div class="input-area">
            <input type="text" id="message-input" placeholder="輸入你的問題..." autocomplete="off">
            <button id="send-button">發送</button>
        </div>
        
        <div class="status" id="status"></div>
    </div>
    
    <div class="footer">
        <p>© 2025 肥宅老司機 AI 聊天機器人 | 版本 0.1.0</p>
        <p>已連接到DeepSeek R1模型</p>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const chatMessages = document.getElementById('chat-messages');
            const messageInput = document.getElementById('message-input');
            const sendButton = document.getElementById('send-button');
            const statusElement = document.getElementById('status');
            
            // 保存对话历史
            const messageHistory = [];
            
            // 发送消息函数
            async function sendMessage() {
                const message = messageInput.value.trim();
                if (message === '') return;
                
                // 添加用户消息到聊天窗口
                addMessage(message, 'user');
                messageInput.value = '';
                
                // 添加到历史记录
                messageHistory.push({ role: 'user', content: message });
                
                // 显示状态
                statusElement.textContent = '機器人正在思考...';
                
                try {
                    // 发送请求到API
                    const response = await fetch('/api/chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            messages: messageHistory
                        })
                    });
                    
                    if (!response.ok) {
                        throw new Error('API请求失败');
                    }
                    
                    const data = await response.json();
                    addMessage(data.content, 'bot');
                    
                    // 添加到历史记录
                    messageHistory.push({ role: 'assistant', content: data.content });
                    
                    // 如果历史记录太长，删除最早的消息
                    if (messageHistory.length > 10) {
                        messageHistory.splice(0, 2);
                    }
                } catch (error) {
                    console.error('发送消息失败:', error);
                    addMessage('抱歉，我遇到了一些问题，无法回应你的问题。', 'bot');
                } finally {
                    statusElement.textContent = '';
                }
            }
            
            // 添加消息到聊天窗口
            function addMessage(text, sender) {
                const messageElement = document.createElement('div');
                messageElement.classList.add('message');
                messageElement.classList.add(sender + '-message');
                messageElement.textContent = text;
                
                chatMessages.appendChild(messageElement);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
            
            // 事件监听器
            sendButton.addEventListener('click', sendMessage);
            messageInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
        });
    </script>
</body>
</html>
"""

# 创建一个简单的HTTP处理器
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """处理GET请求"""
        try:
            # 健康检查路由
            if self.path == "/health":
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                response = {
                    "status": "healthy",
                    "environment": os.environ.get("APP_ENV", "development"),
                    "vercel": os.environ.get("VERCEL", "false")
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # API根路由
            if self.path == "/api":
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                response = {
                    "message": "欢迎使用 Fattyinsider AI API",
                    "version": "0.1.0",
                    "docs_url": "/docs",
                    "environment": os.environ.get("APP_ENV", "development")
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # 根路由 - 返回HTML页面
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode('utf-8'))
            
        except Exception as e:
            logger.error(f"请求处理错误: {str(e)}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            error_response = {
                "error": str(e),
                "status": "error"
            }
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def do_POST(self):
        """处理POST请求"""
        try:
            # 聊天API端点
            if self.path == "/api/chat":
                # 读取请求体
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length).decode('utf-8')
                request_data = json.loads(post_data)
                
                # 获取消息
                messages = request_data.get('messages', [])
                
                # 调用LLM服务
                response = asyncio.run(generate_chat_response(messages))
                
                # 返回响应
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # 未找到API端点
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            error_response = {
                "error": "API端点不存在",
                "status": "error"
            }
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
            
        except Exception as e:
            logger.error(f"API请求处理错误: {str(e)}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            error_response = {
                "error": str(e),
                "status": "error"
            }
            self.wfile.write(json.dumps(error_response).encode('utf-8'))

# 这是Vercel需要的入口点
# Vercel会自动识别这个文件并使用它来启动应用程序 