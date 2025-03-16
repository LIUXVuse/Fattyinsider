"""
Vercel部署入口点 - 简化版本，不使用外部依赖
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
        .message {
            margin-bottom: 10px;
            padding: 10px;
            border-radius: 5px;
        }
        .user {
            background-color: #dcf8c6;
            text-align: right;
        }
        .bot {
            background-color: #e5e5ea;
        }
        .input-area {
            display: flex;
            margin-top: 20px;
        }
        input {
            flex: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        button {
            padding: 10px 20px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            margin-left: 10px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <h1>肥宅老司機 AI 聊天機器人</h1>
    
    <div class="chat-container">
        <div id="chat">
            <div class="message bot">你好！我是肥宅老司機 AI 聊天機器人。有什麼我能幫你的嗎？</div>
        </div>
        
        <div class="input-area">
            <input type="text" id="user-input" placeholder="輸入你的問題...">
            <button onclick="sendMessage()">發送</button>
        </div>
    </div>

    <script>
        function sendMessage() {
            const input = document.getElementById('user-input');
            const message = input.value.trim();
            
            if (message === '') return;
            
            // 添加用户消息
            const chat = document.getElementById('chat');
            const userDiv = document.createElement('div');
            userDiv.className = 'message user';
            userDiv.textContent = message;
            chat.appendChild(userDiv);
            
            // 清空输入框
            input.value = '';
            
            // 添加机器人回复
            setTimeout(() => {
                const botDiv = document.createElement('div');
                botDiv.className = 'message bot';
                botDiv.textContent = "我收到了你的消息：" + message + "。目前我处于测试阶段，暂时无法连接到DeepSeek模型。";
                chat.appendChild(botDiv);
            }, 500);
        }
        
        // 按Enter发送消息
        document.getElementById('user-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    </script>
</body>
</html>
"""

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(HTML_TEMPLATE.encode('utf-8'))
        return

# 这是Vercel需要的入口点
# Vercel会自动识别这个文件并使用它来启动应用程序 