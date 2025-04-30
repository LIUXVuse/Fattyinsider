import json
# import urllib.request # 不再需要，改用 fetch
# import urllib.error
from js import Response, Headers, TransformStream, URL, fetch # 從 JavaScript 環境導入 Workers API

# 注意：不再需要 os, sys, socket, logging (日誌用 print，API Key 從 env)

async def generate_chat_response(messages, api_key):
    """呼叫 DeepSeek API 並處理響應，支持流式輸出。"""
    print(f"使用 API Key: {'已提供' if api_key else '未提供！！！！！！'}")
    if not api_key:
        print("未提供 DEEPSEEK_API_KEY 環境變數")
        error_response = {"error": "服務端未配置 API Key"}
        # 在 _worker.py 中，我們需要返回標準的 Response 物件
        # 注意 Headers 的用法
        headers = Headers()
        headers.append("Content-Type", "application/json")
        return Response(json.dumps(error_response), status=401, headers=headers)

    # 消息歷史優化 (與之前相同)
    MAX_HISTORY = 10
    if len(messages) > MAX_HISTORY:
        system_messages = [msg for msg in messages if msg.get('role') == 'system']
        # 確保至少保留 MAX_HISTORY 條，即使 system message 很多
        num_recent = max(0, MAX_HISTORY - len(system_messages)) 
        recent_messages = messages[-num_recent:] if num_recent > 0 else []
        messages = system_messages + recent_messages
        print(f"消息历史已优化为{len(messages)}条消息")

    request_data = {
        "model": "deepseek-chat",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 4096,
        "stream": True # 保持流式請求
    }

    deepseek_url = "https://api.deepseek.com/v1/chat/completions"
    # 修正 Headers 創建方式
    fetch_headers = Headers()
    fetch_headers.append("Content-Type", "application/json")
    fetch_headers.append("Authorization", f"Bearer {api_key}")
    
    try:
        print(f"發送請求到 DeepSeek API (使用 fetch): {json.dumps(request_data, ensure_ascii=False)}")
        # 使用 fetch API 發送請求
        # 注意： fetch 的參數需要是 JS 環境能理解的類型
        api_response = await fetch(deepseek_url, method="POST", headers=fetch_headers, body=json.dumps(request_data))
        print(f"收到 DeepSeek API 回應狀態: {api_response.status}")

        if not api_response.ok:
             # 如果 API 返回錯誤狀態碼，讀取錯誤詳情並返回
             error_body = await api_response.text()
             print(f"DeepSeek API HTTP 錯誤: {api_response.status}")
             print(f"錯誤詳情: {error_body}")
             response_data = {"error": f"DeepSeek API 請求失敗: {api_response.status}", "detail": error_body}
             err_headers = Headers()
             err_headers.append("Content-Type", "application/json")
             return Response(json.dumps(response_data), status=api_response.status, headers=err_headers)

        # --- 處理流式響應 ---
        response_headers = Headers()
        response_headers.append("Content-Type", "text/event-stream; charset=utf-8")
        response_headers.append("Cache-Control", "no-cache")
        response_headers.append("Connection", "keep-alive")
        
        print("正在返回 DeepSeek API 的流式響應...")
        # 直接將 DeepSeek API 的流式響應 body 返回給客戶端
        return Response(api_response.body, status=api_response.status, headers=response_headers)

    except Exception as e:
        # 捕捉 fetch 或其他異步操作可能引發的錯誤
        print(f"調用 DeepSeek API 或處理響應時發生未知錯誤: {e}")
        response_data = {"error": "服務端內部錯誤"}
        err_headers = Headers()
        err_headers.append("Content-Type", "application/json")
        return Response(json.dumps(response_data), status=500, headers=err_headers)


# _worker.py 的主入口點
async def fetch(request, env, context):
    """處理所有進入的請求。"""
    # 使用從 js import 的 URL
    url = URL(request.url)
    url_pathname = url.pathname
    print(f"[Worker Fetch] Received request: Method={request.method}, Path={url_pathname}")

    # API 路由: 處理對 /api/chat 的 POST 請求
    if url_pathname == "/api/chat" and request.method == "POST":
        print("[Worker Fetch] Routing to API handler...")
        try:
            request_body = await request.json()
            messages = request_body.get('messages', [])
            
            if not messages:
                 error_response = {"error": "请求体中缺少 'messages' 字段或为空"}
                 err_headers = Headers()
                 err_headers.append("Content-Type", "application/json")
                 return Response(json.dumps(error_response), status=400, headers=err_headers)

            # 從環境變數獲取 API Key
            api_key = env.DEEPSEEK_API_KEY
            
            # 調用核心邏輯函數
            return await generate_chat_response(messages, api_key)

        except json.JSONDecodeError:
            error_response = {"error": "无效的 JSON 请求体"}
            err_headers = Headers()
            err_headers.append("Content-Type", "application/json")
            return Response(json.dumps(error_response), status=400, headers=err_headers)
        except Exception as e:
            print(f"處理 /api/chat POST 請求時發生未知錯誤: {e}")
            error_response = {"error": "處理請求時發生內部錯誤"}
            err_headers = Headers()
            err_headers.append("Content-Type", "application/json")
            return Response(json.dumps(error_response), status=500, headers=err_headers)

    # 靜態檔案路由: 對於所有其他請求，嘗試從 ASSETS 提供服務
    print(f"[Worker Fetch] Path '{url_pathname}' not API route, attempting to serve static asset...")
    try:
        # env.ASSETS 是 Cloudflare Pages 注入的，用於獲取靜態資源
        return await env.ASSETS.fetch(request)
    except Exception as e:
        # 如果 ASSETS.fetch 失敗 (例如檔案不存在)
        print(f"[Worker Fetch] Error fetching static asset for path '{url_pathname}': {e}")
        # 返回簡單的文字 404
        return Response("資源未找到 (Not Found)", status=404)

# 注意: _worker.py 不需要 if __name__ == "__main__"
# Cloudflare 會直接調用 fetch 函數 