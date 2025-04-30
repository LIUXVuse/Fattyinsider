import json
from js import Response, Headers, TransformStream, URL, fetch # 從 JavaScript 環境導入 Workers API

# 注意：不再需要 os, sys, socket, logging (日誌用 print，API Key 從 env)

# _worker.py 的主入口點
async def fetch(request, env, context):
    """處理所有進入的請求 - 極簡調試版。"""
    url = URL(request.url)
    url_pathname = url.pathname
    method = request.method
    print(f"[WORKER DEBUG] Method={method}, Path={url_pathname}")

    # API 路由: 處理對 /api/chat 的 POST 請求
    if url_pathname == "/api/chat" and method == "POST":
        print("[WORKER DEBUG] Handling /api/chat POST...")
        # 不做任何處理，直接返回成功訊息
        response_data = {"message": "POST /api/chat handled by minimal worker!"}
        # 創建 Headers
        headers = Headers()
        headers.append("Content-Type", "application/json")
        try:
            return Response(json.dumps(response_data), status=200, headers=headers)
        except Exception as e:
             print(f"Error creating POST response: {e}")
             return Response("Error creating POST response", status=500)

    # 靜態檔案路由: 對於所有其他請求，嘗試從 ASSETS 提供服務
    print(f"[WORKER DEBUG] Path '{url_pathname}' not API route, attempting static asset...")
    try:
        # env.ASSETS 是 Cloudflare Pages 注入的
        return await env.ASSETS.fetch(request)
    except Exception as e:
        print(f"[WORKER DEBUG] Error fetching static asset for path '{url_pathname}': {e}")
        return Response("資源未找到 (Not Found)", status=404)

# 注意: _worker.py 不需要 if __name__ == "__main__"
# Cloudflare 會直接調用 fetch 函數 