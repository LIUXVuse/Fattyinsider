import os
import sys
import json
import logging
import urllib.request
import urllib.error
import socket
from http.server import BaseHTTPRequestHandler
from dotenv import load_dotenv

# 載入 .env 文件中的環境變數
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout) # 直接輸出到標準輸出
    ]
)
logger = logging.getLogger(__name__)

# HTML 模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>肥宅老司機 AI</title>
    <style>
        body {{ font-family: sans-serif; display: flex; flex-direction: column; height: 100vh; margin: 0; background-color: #f4f4f4; }}
        #chat-container {{ flex-grow: 1; overflow-y: auto; padding: 20px; background-color: #fff; border-radius: 8px; margin: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .message {{ margin-bottom: 15px; padding: 10px 15px; border-radius: 18px; max-width: 80%; }}
        .user-message {{ background-color: #007bff; color: white; align-self: flex-end; margin-left: auto; border-bottom-right-radius: 5px; }}
        .ai-message {{ background-color: #e9e9eb; color: #333; align-self: flex-start; border-bottom-left-radius: 5px; }}
        #input-area {{ display: flex; padding: 15px; border-top: 1px solid #ccc; background-color: #fff; }}
        #message-input {{ flex-grow: 1; padding: 10px; border: 1px solid #ccc; border-radius: 20px; margin-right: 10px; }}
        #send-button {{ padding: 10px 20px; background-color: #007bff; color: white; border: none; border-radius: 20px; cursor: pointer; }}
        #send-button:disabled {{ background-color: #a0cfff; cursor: not-allowed; }}
        #status {{ text-align: center; padding: 5px; font-size: 0.9em; color: #666; }}
        .typing-indicator span {{ display: inline-block; width: 8px; height: 8px; margin: 0 2px; background-color: #aaa; border-radius: 50%; animation: typing 1s infinite; }}
        .typing-indicator span:nth-child(2) {{ animation-delay: 0.2s; }}
        .typing-indicator span:nth-child(3) {{ animation-delay: 0.4s; }}
        @keyframes typing {{ 0% {{ transform: translateY(0); }} 50% {{ transform: translateY(-4px); }} 100% {{ transform: translateY(0); }} }}
    </style>
</head>
<body>
    <div id="chat-container">
        <!-- 聊天消息将在这里显示 -->
    </div>
    <div id="status">輸入訊息開始聊天...</div>
    <div id="input-area">
        <input type="text" id="message-input" placeholder="輸入訊息...">
        <button id="send-button">發送</button>
    </div>

    <script>
        const chatContainer = document.getElementById('chat-container');
        const messageInput = document.getElementById('message-input');
        const sendButton = document.getElementById('send-button');
        const statusElement = document.getElementById('status');
        
        // 保存对话历史
        const messageHistory = [];
        
        // 初始化时添加系统消息
        messageHistory.push({
            role: 'system',
            content: '你是肥宅老司機AI聊天機器人，一個友好、幽默的助手。請務必使用繁體中文（Traditional Chinese）回覆。'
        });
        
        // 发送消息函数
        async function sendMessage() {
            const messageText = messageInput.value.trim();
            if (!messageText) return;

            // 显示用户消息
            appendMessage('user', messageText);
            messageInput.value = '';
            sendButton.disabled = true;
            statusElement.innerHTML = '<span class="typing-indicator"><span></span><span></span><span></span></span> AI 正在思考中...';

            // 将用户消息添加到历史记录
            messageHistory.push({ role: 'user', content: messageText });

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ messages: messageHistory })
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
                }

                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let aiResponse = '';
                let firstChunk = true;
                let aiMessageElement = null;

                while (true) {
                    const {{value, done}} = await reader.read();
                    if (done) break;
                    
                    const chunk = decoder.decode(value, {{stream: true}});
                    // 處理可能的 SSE 格式 (簡單處理)
                    const lines = chunk.split('\n');
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const data = line.substring(6);
                            if (data.trim() === '[DONE]') {
                                // 如果收到 [DONE] 標記，表示流結束
                                break;
                            } 
                            try {
                                const parsedData = JSON.parse(data);
                                // 根據 DeepSeek 或 OpenAI 的 SSE 格式提取內容
                                let content = '';
                                if (parsedData.choices && parsedData.choices[0].delta) {
                                    content = parsedData.choices[0].delta.content || '';
                                }
                                
                                if (content) {
                                    aiResponse += content;
                                    if (firstChunk) {
                                        aiMessageElement = appendMessage('ai', content, true); // 初始時創建元素
                                        firstChunk = false;
                                    } else {
                                        aiMessageElement.textContent += content; // 逐字添加到現有元素
                                    }
                                    chatContainer.scrollTop = chatContainer.scrollHeight;
                                }
                            } catch (e) {
                                // 如果 JSON 解析失敗，可能是純文本或其他格式，嘗試直接附加
                                // 注意：這裡的處理比較簡陋，可能需要根據實際返回的SSE格式調整
                                if (!line.startsWith('event:') && !line.startsWith('id:') && line.trim() !== ''){
                                    console.warn("Received non-JSON data chunk (or parse failed):", line);
                                    // 嘗試附加非 JSON 文本 (如果需要)
                                    // aiResponse += line; 
                                    // if (firstChunk) ... else ... (類似上面)
                                } 
                            } 
                        }
                    }
                }
                
                 // 確保即使流結束時沒有顯式[DONE]，最終的aiResponse也被添加到歷史記錄
                if (!firstChunk) { // 確保至少收到過內容
                    messageHistory.push({ role: 'assistant', content: aiResponse });
                } else {
                    // 如果 firstChunk 仍然是 true，表示沒有收到任何有效內容
                    appendMessage('ai', '抱歉，沒有收到有效的 AI 回覆。');
                }

            } catch (error) {
                console.error('Error sending message:', error);
                appendMessage('ai', `發生錯誤：${error.message}`);
                messageHistory.push({ role: 'assistant', content: `發生錯誤：${error.message}` });
            } finally {
                sendButton.disabled = false;
                statusElement.textContent = '準備好接收下一條訊息';
            }
        }

        // 添加消息到聊天窗口
        function appendMessage(sender, text, isStreaming = false) {
            const messageElement = document.createElement('div');
            messageElement.classList.add('message');
            if (sender === 'user') {
                messageElement.classList.add('user-message');
            } else {
                messageElement.classList.add('ai-message');
            }
            messageElement.textContent = text;
            chatContainer.appendChild(messageElement);
            if (!isStreaming) { // 非流式輸出才滾動到底部，流式輸出在接收時滾動
               chatContainer.scrollTop = chatContainer.scrollHeight;
            }
            return messageElement; // 返回創建的元素，以便流式更新
        }

        // 绑定事件
        sendButton.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        
        // 清空对话历史 (如果需要)
        /*
        function clearChat() {
            // 清空前端歷史
            messageHistory.length = 0; 
            
            // 重新加入初始的系統訊息 (如果後端需要它)
            messageHistory.push({
                role: 'system',
                content: '你是肥宅老司機AI聊天機器人，一個友好、幽默的助手。請務必使用繁體中文（Traditional Chinese）回覆。'
            });
            // 清空聊天界面
            chatContainer.innerHTML = ''; 
            statusElement.textContent = '對話已清空，輸入訊息開始聊天...';
        }
        // 可以添加一個清空按鈕並綁定 clearChat() 事件
        */

    </script>
</body>
</html>
"""

def generate_chat_response(messages):
    api_key = os.getenv("DEEPSEEK_API_KEY")
    logger.info(f"使用 API Key: {'已設置' if api_key else '未設置！！！！！！'}")
    if not api_key:
        logger.error("未设置DEEPSEEK_API_KEY环境变量。請確認 .env 文件存在且包含 DEEPSEEK_API_KEY。")
        # 返回錯誤訊息，讓前端知道問題
        return json.dumps({"error": "未设置DEEPSEEK_API_KEY环境变量。"}).encode('utf-8'), 401

    # 优化消息历史，只保留最近的几条消息 (包含系统消息)
    MAX_HISTORY = 10
    if len(messages) > MAX_HISTORY:
        system_messages = [msg for msg in messages if msg.get('role') == 'system']
        recent_messages = messages[- (MAX_HISTORY - len(system_messages)):] # 保留最近 N-1 條對話
        messages = system_messages + recent_messages
        logger.info(f"消息历史过长，已优化为{len(messages)}条消息")

    # 准备请求数据 - 使用DeepSeek V3模型
    request_data = {
        "model": "deepseek-chat",
        "messages": messages,
        "temperature": 0.7, # 稍微提高一點溫度增加趣味性
        "max_tokens": 4096, # 根據需要調整
        "stream": True # 開啟流式輸出
    }

    # 创建请求
    req = urllib.request.Request(
        "https://api.deepseek.com/v1/chat/completions",
        data=json.dumps(request_data).encode('utf-8'),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        method="POST"
    )

    try:
        logger.info(f"發送請求到 DeepSeek API: {json.dumps(request_data, ensure_ascii=False)}")
        response = urllib.request.urlopen(req, timeout=60) # 增加超時時間
        logger.info(f"收到 DeepSeek API 回應狀態: {response.status}")
        # 直接將流式響應返回給客戶端
        return response, response.status # 返回原始 response 物件和狀態碼

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        logger.error(f"HTTP错误: {e.code} {e.reason}")
        logger.error(f"错误详情: {error_body}")
        # 返回包含錯誤信息的 JSON 和 HTTP 錯誤碼
        return json.dumps({"error": f"API 请求失败: {e.code}", "detail": error_body}).encode('utf-8'), e.code
    except urllib.error.URLError as e:
        logger.error(f"URL错误: {e.reason}")
        # 返回包含錯誤信息的 JSON 和 500 狀態碼
        return json.dumps({"error": "网络连接或 URL 错误", "detail": str(e.reason)}).encode('utf-8'), 500
    except socket.timeout:
        logger.error("请求 DeepSeek API 超时")
        # 返回包含錯誤信息的 JSON 和 504 狀態碼
        return json.dumps({"error": "请求 AI 服务超时"}).encode('utf-8'), 504
    except Exception as e:
        logger.exception("处理聊天请求时发生未知错误")
        # 返回包含錯誤信息的 JSON 和 500 狀態碼
        return json.dumps({"error": "內部伺服器錯誤"}).encode('utf-8'), 500

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode('utf-8'))
        else:
            self.send_error(404, 'File Not Found: %s' % self.path)

    def do_POST(self):
        if self.path == '/api/chat':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                request_body = json.loads(post_data.decode('utf-8'))
                messages = request_body.get('messages', [])

                if not messages:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "请求体中缺少 'messages' 字段或为空"}).encode('utf-8'))
                    return

                # 调用 DeepSeek API
                api_response, status_code = generate_chat_response(messages)

                # 檢查 generate_chat_response 返回的是否是錯誤信息
                if status_code >= 400:
                    self.send_response(status_code)
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.end_headers()
                    # api_response 已經是 bytes 了
                    self.wfile.write(api_response)
                else:
                    # 是成功的流式響應 (urllib.response 物件)
                    self.send_response(status_code) # 通常是 200
                    # 設置 SSE 的 Header
                    self.send_header('Content-Type', 'text/event-stream; charset=utf-8')
                    self.send_header('Cache-Control', 'no-cache')
                    self.send_header('Connection', 'keep-alive')
                    self.end_headers()
                    
                    # 分塊讀取並寫入響應流
                    try:
                        while True:
                            chunk = api_response.read(1024) # 讀取一塊數據
                            if not chunk:
                                break # 流結束
                            self.wfile.write(chunk)
                            self.wfile.flush() # 確保立即發送
                    except Exception as e:
                        logger.error(f"寫入 SSE 流時出錯: {e}")
                    finally:
                        api_response.close() # 確保關閉 response 物件

            except json.JSONDecodeError:
                self.send_response(400)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "无效的 JSON 请求体"}).encode('utf-8'))
            except Exception as e:
                logger.exception("处理 POST 请求时发生未知错误")
                self.send_response(500)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "內部伺服器錯誤"}).encode('utf-8'))
        else:
            self.send_error(404, 'File Not Found: %s' % self.path)


if __name__ == "__main__":
    from http.server import HTTPServer
    # 允許從環境變數讀取端口，預設為 8000
    port = int(os.getenv('PORT', 8000)) 
    # 使用 '' 代替 '0.0.0.0' 以兼容不同系统和容器環境
    server_address = ('', port) 
    print(f"正在 {port} 端口上啟動 HTTP 伺服器...")
    logger.info(f"伺服器監聽於 http://localhost:{port}")
    httpd = HTTPServer(server_address, handler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n伺服器已停止.")
        logger.info("伺服器已通過 KeyboardInterrupt 停止")
        httpd.server_close() 