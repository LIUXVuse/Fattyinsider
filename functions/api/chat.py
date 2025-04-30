import os
import sys
import json
import logging
import urllib.request
import urllib.error
import socket
# 注意：不再需要 BaseHTTPRequestHandler 和 load_dotenv (Key 從 context 獲取)

# 配置日志 (類似之前，但在函數內初始化可能更好，或依賴 Cloudflare 環境)
# logging.basicConfig(...) 
# logger = logging.getLogger(__name__)
# 暫時簡化，直接使用 print 或依賴 Cloudflare 的日誌

def generate_chat_response(messages, api_key):
    # api_key = os.getenv("DEEPSEEK_API_KEY") # 不再從 .env 讀取
    print(f"使用 API Key: {'已提供' if api_key else '未提供！！！！！！'}")
    if not api_key:
        print("未提供 DEEPSEEK_API_KEY")
        # 返回錯誤訊息，讓前端知道問題
        # 在 Functions 中，通常返回 Response 物件
        error_response = {"error": "未配置 DEEPSEEK_API_KEY"}
        return Response(json.dumps(error_response), status=401, headers={"Content-Type": "application/json"})

    # 优化消息历史...
    MAX_HISTORY = 10
    if len(messages) > MAX_HISTORY:
        system_messages = [msg for msg in messages if msg.get('role') == 'system']
        recent_messages = messages[- (MAX_HISTORY - len(system_messages)):]
        messages = system_messages + recent_messages
        print(f"消息历史已优化为{len(messages)}条消息")

    request_data = {
        "model": "deepseek-chat",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 4096,
        "stream": True
    }

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
        print(f"發送請求到 DeepSeek API: {json.dumps(request_data, ensure_ascii=False)}")
        api_response = urllib.request.urlopen(req, timeout=60)
        print(f"收到 DeepSeek API 回應狀態: {api_response.status}")
        
        # Cloudflare Functions 需要返回一個 Response 物件
        # 我們需要一個方法將 urllib 的流轉換成 Workers 能理解的流
        # 最簡單的方法是讀取所有內容再返回，但這會失去流式效果
        # 保持流式需要更複雜的處理，可能涉及 ReadableStream
        
        # === 簡化版：一次性讀取並返回 (失去流式效果) ===
        # response_body = api_response.read()
        # api_response.close()
        # headers = {
        #     'Content-Type': 'application/json; charset=utf-8',
        # }
        # return Response(response_body, status=api_response.status, headers=headers)
        # =============================================

        # === 嘗試保持流式 (需要 Cloudflare 環境支援) ===
        # 注意：這部分程式碼在標準 Python 環境下無法直接運行
        # 它需要 Cloudflare Workers Runtime 提供的 Response 和 ReadableStream
        
        # 創建一個可以推送數據的流控制器
        readable_stream, writable_stream = TransformStream().values()
        writer = writable_stream.getWriter()

        # 異步讀取 API 響應並寫入流
        async def stream_data():
            try:
                while True:
                    chunk = api_response.read(1024) # 讀取一塊數據
                    if not chunk:
                        break # 流結束
                    await writer.write(chunk) # 寫入 Workers 流
            except Exception as e:
                print(f"讀取或寫入流時出錯: {e}")
                await writer.abort(e)
            finally:
                api_response.close()
                await writer.close()

        # 在背景執行流數據的傳輸 (需要協程環境，如 asyncio 或 Workers Runtime)
        # asyncio.create_task(stream_data()) # 假設在 asyncio 環境
        # 在 Workers 環境中，這個異步過程可能需要不同的啟動方式
        # Cloudflare Workers 通常會自動處理異步函數
        
        # 返回包含 ReadableStream 的 Response
        headers = {
            'Content-Type': 'text/event-stream; charset=utf-8',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        }
        # 返回 Response，其 body 是我們創建的 readable_stream
        # 需要從 Workers 環境導入 Response
        # return Response(readable_stream, status=api_response.status, headers=headers)
        
        # --- 為了讓代碼至少在語法上正確，暫時註釋掉 Worker 特定部分 --- 
        # --- 並回退到非流式版本，以便至少能部署測試 --- 
        print("警告：暫時回退到非流式響應以確保部署。")
        response_body = api_response.read()
        api_response.close()
        headers = {
             'Content-Type': 'application/json; charset=utf-8', # 改成 JSON 因為不是流了
        }
        # 需要 Response 類，這裡假設它存在於環境中
        # from cloudflare import Response # 假設導入
        # return Response(response_body, status=api_response.status, headers=headers)
        # 為了讓語法通過，暫時返回字典模擬
        return {"status": api_response.status, "body": response_body, "headers": headers}
        # ---------------------------------------------------------------------

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"HTTP错误: {e.code} {e.reason}")
        print(f"错误详情: {error_body}")
        response_data = {"error": f"API 请求失败: {e.code}", "detail": error_body}
        # return Response(json.dumps(response_data), status=e.code, headers={"Content-Type": "application/json"})
        return {"status": e.code, "body": json.dumps(response_data).encode('utf-8'), "headers": {"Content-Type": "application/json"}}
    # ... 其他錯誤處理 ...
    except Exception as e:
        print(f"未知错误: {e}")
        response_data = {"error": "內部伺服器錯誤"}
        # return Response(json.dumps(response_data), status=500, headers={"Content-Type": "application/json"})
        return {"status": 500, "body": json.dumps(response_data).encode('utf-8'), "headers": {"Content-Type": "application/json"}}


# Cloudflare Pages Functions 的通用入口點
async def onRequest(context):
    # 從 context 中獲取請求對象
    request = context.request
    print(f"onRequest 函數被呼叫！請求方法: {request.method}")

    # 檢查請求方法是否為 POST
    if request.method == "POST":
        print("處理 POST 請求...")
        try:
            # 嘗試讀取請求體
            try:
                request_body = await request.json()
                print(f"收到請求體: {request_body}")
            except Exception as e:
                print(f"讀取請求體時出錯 (但不中斷調試): {e}")
                # 即使讀取失敗，在調試階段也繼續返回成功

            # 直接返回一個固定的成功響應 (用於調試)
            debug_response = {"message": "POST request received successfully via onRequest (debug)"}
            
            # Cloudflare Pages 會自動將字典轉換為 JSON Response (狀態碼 200)
            return debug_response

        except Exception as e:
            print(f"處理 POST 請求時發生未知錯誤: {e}")
            error_response = {"error": "內部伺服器錯誤 (調試模式)"}
            # 返回字典，CF 會處理成 status 500 JSON Response
            # 需要顯式返回 Response 物件才能自訂狀態碼和標頭
            # from cloudflare import Response # 假設導入
            # return Response(json.dumps(error_response), status=500, headers={"Content-Type": "application/json"})
            return error_response
    
    # 如果不是 POST 請求，則返回 405 Method Not Allowed
    else:
        print(f"拒絕非 POST ({request.method}) 請求")
        # 為了返回正確的 405，我們需要 Response 對象
        # 暫時返回一個表示錯誤的字典，狀態碼可能不會是 405
        # return {"error": f"{request.method} method not allowed for /api/chat"}
        # 嘗試標準 Response (如果環境支援)
        try:
            # 假設 Response 類可以直接使用
            return Response(f"{request.method} method not allowed for /api/chat", status=405)
        except NameError:
             # 如果 Response 不可用，返回字典
             return {"error": f"{request.method} method not allowed for /api/chat", "status_intended": 405}

# 移除舊的 onRequestPost 和 generate_chat_response
# async def onRequestPost(context): ...
# def generate_chat_response(messages, api_key): ...

# 注意：不再需要 if __name__ == "__main__": 和 HTTPServer 部分 