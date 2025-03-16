"""
Vercel部署入口点 - 使用标准库实现LLM调用，优化超时处理
"""
import os
import sys
import json
import logging
import urllib.request
import urllib.error
import socket
from http.server import BaseHTTPRequestHandler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("vercel_app")

# 调用DeepSeek API生成回复
def generate_chat_response(messages):
    """使用标准库调用DeepSeek API，优化超时处理"""
    try:
        # 获取API密钥
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        if not api_key:
            logger.error("未设置DEEPSEEK_API_KEY环境变量")
            return "抱歉，系统未配置API密钥，无法连接到DeepSeek模型。"
        
        # 优化消息历史，只保留最近的几条消息
        if len(messages) > 3:
            # 保留第一条系统消息（如果有）和最近的2条对话
            system_messages = [msg for msg in messages if msg.get('role') == 'system']
            recent_messages = messages[-2:]
            messages = system_messages + recent_messages
            logger.info(f"消息历史过长，已优化为{len(messages)}条消息")
        
        # 准备请求数据 - 使用DeepSeek V3模型
        request_data = {
            "model": "deepseek-ai/DeepSeek-V3",  # 确保模型名称正确
            "messages": messages,
            "temperature": 0.3,  # 进一步降低温度以加快响应
            "max_tokens": 200,   # 减少token数量以加快响应
            "top_p": 0.5,        # 添加top_p参数控制输出多样性
            "top_k": 30,         # 添加top_k参数限制候选词数量
            "frequency_penalty": 0.5, # 添加频率惩罚减少重复
            "stream": False      # 不使用流式输出，因为标准库不易处理
        }
        
        # 创建请求
        req = urllib.request.Request(
            "https://api.siliconflow.cn/v1/chat/completions",
            data=json.dumps(request_data).encode('utf-8'),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            method="POST"
        )
        
        # 设置更长的超时时间
        socket.setdefaulttimeout(55)  # 设置55秒超时，接近Vercel免费用户的最大限制60秒
        
        # 发送请求
        with urllib.request.urlopen(req) as response:
            response_data = json.loads(response.read().decode('utf-8'))
            
            # 提取回复内容
            if "choices" in response_data and len(response_data["choices"]) > 0:
                content = response_data["choices"][0]["message"]["content"]
                # 记录token使用情况
                if "usage" in response_data:
                    usage = response_data["usage"]
                    logger.info(f"Token使用情况: 提示词={usage.get('prompt_tokens', 0)}, 回复={usage.get('completion_tokens', 0)}, 总计={usage.get('total_tokens', 0)}")
                return content
            else:
                logger.error(f"DeepSeek API响应格式错误: {response_data}")
                return "抱歉，无法解析DeepSeek API的响应。"
    
    except urllib.error.HTTPError as e:
        logger.error(f"HTTP错误: {e.code} {e.reason}")
        # 添加更详细的错误信息
        try:
            error_body = e.read().decode('utf-8')
            logger.error(f"错误详情: {error_body}")
            error_json = json.loads(error_body)
            error_message = error_json.get("message", "未知错误")
            return f"抱歉，调用DeepSeek API时出错: {error_message}"
        except:
            return f"抱歉，调用DeepSeek API时出错: HTTP {e.code}"
    
    except socket.timeout:
        logger.error("API请求超时（55秒）")
        return "抱歉，API请求超时。请尝试发送更简短的消息，或者稍后再试。"
    
    except Exception as e:
        logger.error(f"生成回复时出错: {str(e)}")
        return f"抱歉，我遇到了一些问题: {str(e)}"

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
            word-wrap: break-word;
        }
        .user {
            background-color: #dcf8c6;
            text-align: right;
            margin-left: 20%;
        }
        .bot {
            background-color: #e5e5ea;
            margin-right: 20%;
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
        button:disabled {
            background-color: #cccccc;
            cursor: not-allowed;
        }
        .status {
            text-align: center;
            color: #666;
            font-style: italic;
            margin-top: 10px;
        }
        .warning {
            background-color: #fff3cd;
            color: #856404;
            padding: 10px;
            border-radius: 5px;
            margin-top: 10px;
            font-size: 0.9em;
        }
        .model-info {
            text-align: center;
            color: #666;
            font-size: 0.8em;
            margin-top: 5px;
        }
        .clear-button {
            display: block;
            margin: 10px auto;
            padding: 5px 10px;
            background-color: #f8f9fa;
            color: #666;
            border: 1px solid #ddd;
            border-radius: 5px;
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
            <button id="send-button">發送</button>
        </div>
        
        <div class="status" id="status"></div>
        <button class="clear-button" id="clear-button">清空對話</button>
        <div class="warning">注意：由於Vercel函數執行時間限制，請保持問題簡短，避免複雜長問題導致超時。每次對話僅保留最近2條消息。回應時間最長為55秒。</div>
        <div class="model-info">使用 DeepSeek V3 模型提供服務</div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const chat = document.getElementById('chat');
            const userInput = document.getElementById('user-input');
            const sendButton = document.getElementById('send-button');
            const clearButton = document.getElementById('clear-button');
            const statusElement = document.getElementById('status');
            
            // 保存对话历史
            const messageHistory = [];
            
            // 初始化时添加系统消息
            messageHistory.push({
                role: 'system',
                content: '你是肥宅老司機AI聊天機器人，一個友好、幽默的助手。請提供簡短、準確的回答。'
            });
            
            // 发送消息函数
            async function sendMessage() {
                const message = userInput.value.trim();
                if (message === '') return;
                
                // 禁用输入和按钮
                userInput.disabled = true;
                sendButton.disabled = true;
                
                // 添加用户消息
                const userDiv = document.createElement('div');
                userDiv.className = 'message user';
                userDiv.textContent = message;
                chat.appendChild(userDiv);
                
                // 清空输入框
                userInput.value = '';
                
                // 添加到历史记录
                messageHistory.push({ role: 'user', content: message });
                
                // 显示状态
                statusElement.textContent = '機器人正在思考...';
                
                try {
                    // 设置超时
                    const controller = new AbortController();
                    const timeoutId = setTimeout(() => controller.abort(), 58000);
                    
                    // 发送请求到API
                    const response = await fetch('/api/chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            messages: messageHistory
                        }),
                        signal: controller.signal
                    });
                    
                    clearTimeout(timeoutId);
                    
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    
                    const data = await response.json();
                    
                    // 添加机器人回复
                    const botDiv = document.createElement('div');
                    botDiv.className = 'message bot';
                    botDiv.textContent = data.content;
                    chat.appendChild(botDiv);
                    
                    // 添加到历史记录
                    messageHistory.push({ role: 'assistant', content: data.content });
                    
                    // 如果历史记录太长，删除最早的非系统消息
                    if (messageHistory.length > 5) { // 保留1个系统消息和4个对话消息
                        const systemMessages = messageHistory.filter(msg => msg.role === 'system');
                        const nonSystemMessages = messageHistory.filter(msg => msg.role !== 'system');
                        
                        while (nonSystemMessages.length > 4) {
                            nonSystemMessages.shift();
                        }
                        
                        messageHistory.length = 0;
                        messageHistory.push(...systemMessages, ...nonSystemMessages);
                    }
                    
                    // 清除状态
                    statusElement.textContent = '';
                } catch (error) {
                    console.error('Error:', error);
                    
                    let errorMessage = '抱歉，我遇到了一些問題，請稍後再試。';
                    
                    if (error.name === 'AbortError') {
                        errorMessage = '抱歉，請求超時。請嘗試發送更簡短的消息。';
                        statusElement.textContent = '請求超時';
                    } else {
                        statusElement.textContent = '發生錯誤';
                    }
                    
                    // 添加错误消息
                    const botDiv = document.createElement('div');
                    botDiv.className = 'message bot';
                    botDiv.textContent = errorMessage;
                    chat.appendChild(botDiv);
                } finally {
                    // 重新启用输入和按钮
                    userInput.disabled = false;
                    sendButton.disabled = false;
                    userInput.focus();
                }
                
                // 滚动到底部
                chat.scrollTop = chat.scrollHeight;
            }
            
            // 清空对话历史
            function clearChat() {
                // 保留系统消息
                const systemMessages = messageHistory.filter(msg => msg.role === 'system');
                messageHistory.length = 0;
                messageHistory.push(...systemMessages);
                
                // 清空聊天界面，只保留欢迎消息
                chat.innerHTML = '<div class="message bot">你好！我是肥宅老司機 AI 聊天機器人。有什麼我能幫你的嗎？</div>';
                
                // 清除状态
                statusElement.textContent = '';
            }
            
            // 发送按钮点击事件
            sendButton.addEventListener('click', sendMessage);
            
            // 清空按钮点击事件
            clearButton.addEventListener('click', clearChat);
            
            // 输入框回车事件
            userInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
            
            // 自动聚焦输入框
            userInput.focus();
        });
    </script>
</body>
</html>
"""

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """处理GET请求"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(HTML_TEMPLATE.encode('utf-8'))
        return
    
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
                response_content = generate_chat_response(messages)
                
                # 返回响应
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                response = {
                    "content": response_content,
                    "role": "assistant"
                }
                
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