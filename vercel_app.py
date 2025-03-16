"""
Vercel部署入口点 - 极简版，不使用任何外部依赖
"""
import os
import sys
import json
import logging
from http.server import BaseHTTPRequestHandler

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
        <p>目前處於簡易模式，完整功能即將推出</p>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const chatMessages = document.getElementById('chat-messages');
            const messageInput = document.getElementById('message-input');
            const sendButton = document.getElementById('send-button');
            const statusElement = document.getElementById('status');
            
            // 發送訊息函數
            function sendMessage() {
                const message = messageInput.value.trim();
                if (message === '') return;
                
                // 添加用戶訊息到聊天窗口
                addMessage(message, 'user');
                messageInput.value = '';
                
                // 顯示狀態
                statusElement.textContent = '機器人正在思考...';
                
                // 模擬回應（目前是簡易模式）
                setTimeout(() => {
                    const response = "目前我處於簡易模式，無法提供完整的回應功能。完整版即將推出，敬請期待！";
                    addMessage(response, 'bot');
                    statusElement.textContent = '';
                }, 1000);
            }
            
            // 添加訊息到聊天窗口
            function addMessage(text, sender) {
                const messageElement = document.createElement('div');
                messageElement.classList.add('message');
                messageElement.classList.add(sender + '-message');
                messageElement.textContent = text;
                
                chatMessages.appendChild(messageElement);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
            
            // 事件監聽器
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

# 这是Vercel需要的入口点
# Vercel会自动识别这个文件并使用它来启动应用程序 