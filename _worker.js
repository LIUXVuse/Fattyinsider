// _worker.js - Modified for Cloudflare AutoRAG with enhanced logging

/**
 * 處理來自前端的聊天請求，將其轉發給 AutoRAG 並返回結果。
 * @param {Request} request - 收到的請求
 * @param {object} env - Worker 環境變數 (包含 AutoRAG 相關設置)
 * @returns {Promise<Response>}
 */
async function handleChatRequest(request, env) {
  console.log("[Worker AutoRAG DEBUG] Entering handleChatRequest..."); // 新增日誌
  try {
    const requestBody = await request.json();
    console.log("[Worker AutoRAG DEBUG] Parsed request body."); // 新增日誌
    const messages = requestBody.messages;

    if (!messages || !Array.isArray(messages) || messages.length === 0) {
      console.error("[Worker AutoRAG] Invalid or missing 'messages' in request body.");
      return new Response(JSON.stringify({ error: "请求体中缺少有效的 'messages' 字段" }), {
        status: 400,
        headers: { "Content-Type": "application/json" },
      });
    }

    // 提取最後一條 user message 作為查詢
    const lastUserMessage = messages.findLast(msg => msg.role === 'user');
    if (!lastUserMessage || !lastUserMessage.content) {
        console.error("[Worker AutoRAG] No user message found in history.");
        return new Response(JSON.stringify({ error: "聊天歷史中找不到使用者訊息" }), {
            status: 400,
            headers: { "Content-Type": "application/json" },
        });
    }
    const userQuery = lastUserMessage.content;
    console.log(`[Worker AutoRAG DEBUG] Extracted user query: "${userQuery}"`); // 新增日誌

    // --- AutoRAG API 呼叫 --- 
    const AUTORAG_ENDPOINT = env.AUTORAG_ENDPOINT;
    const AUTORAG_API_TOKEN = env.AUTORAG_API_TOKEN;

    // 打印環境變數 (檢查是否存在，但不打印 Token 值)
    console.log(`[Worker AutoRAG DEBUG] AUTORAG_ENDPOINT: ${AUTORAG_ENDPOINT ? 'Loaded' : 'MISSING!'}`);
    console.log(`[Worker AutoRAG DEBUG] AUTORAG_API_TOKEN: ${AUTORAG_API_TOKEN ? 'Loaded' : 'MISSING!'}`);

    if (!AUTORAG_ENDPOINT || !AUTORAG_API_TOKEN) {
        console.error("[Worker AutoRAG] AUTORAG_ENDPOINT or AUTORAG_API_TOKEN is not configured in environment variables.");
        return new Response(JSON.stringify({ error: "後端 AutoRAG 設定未完成" }), {
            status: 500,
            headers: { "Content-Type": "application/json" },
        });
    }

    const autoRagPayload = {
        query: userQuery,
        // 根據 AutoRAG API 文件，可能需要包含 stream 參數
        stream: false // 明確指定非流式，如果需要流式則改為 true
    };
    console.log("[Worker AutoRAG DEBUG] Sending payload to AutoRAG:", JSON.stringify(autoRagPayload)); // 新增日誌

    const response = await fetch(AUTORAG_ENDPOINT, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${AUTORAG_API_TOKEN}`
        },
        body: JSON.stringify(autoRagPayload)
    });

    console.log(`[Worker AutoRAG] Received response status from AutoRAG: ${response.status}`);
    console.log("[Worker AutoRAG DEBUG] Received response headers:", JSON.stringify(Object.fromEntries(response.headers.entries()))); // 新增日誌

    if (!response.ok) {
        let errorBody = "(Failed to read error body)";
        try {
           errorBody = await response.text();
        } catch (e) { console.error("[Worker AutoRAG DEBUG] Error reading error body:", e); }
        console.error(`[Worker AutoRAG] AutoRAG API Error: ${response.status}. Body: ${errorBody}`);
        return new Response(JSON.stringify({ error: `AutoRAG 請求失敗: ${response.status}`, detail: errorBody }), {
            status: response.status,
            headers: { 'Content-Type': 'application/json' }
        });
    }

    // --- 處理 AutoRAG 回應 --- 
    // 檢查 Content-Type 是否為流式
    const contentType = response.headers.get("content-type") || "";
    console.log(`[Worker AutoRAG DEBUG] AutoRAG response Content-Type: ${contentType}`);

    if (contentType.includes("text/event-stream")) {
        // --- 處理流式響應 (如果需要) --- 
        console.log("[Worker AutoRAG] Streaming AutoRAG response to client...");
        // 注意：前端目前設定為處理 JSON 或特定流格式，直接轉發 SSE 可能不相容
        // 可能需要解析 SSE 並轉換格式，或者修改前端
        // 暫時先返回錯誤，表示未實現流式處理
        console.error("[Worker AutoRAG] Streaming response from AutoRAG received, but frontend/worker not configured to handle it directly yet.");
        return new Response(JSON.stringify({ error: "後端收到流式回應，但尚未完全支援" }), {
            status: 501, // 501 Not Implemented
            headers: { 'Content-Type': 'application/json' }
        });
        /* // 直接轉發流的程式碼 (可能需要調整)
        const responseHeaders = new Headers(response.headers);
        responseHeaders.set("Content-Type", "text/event-stream; charset=utf-8"); 
        return new Response(response.body, {
            status: response.status,
            headers: responseHeaders,
        });
        */
    } else if (contentType.includes("application/json")) {
         // --- 處理 JSON 響應 --- 
        console.log("[Worker AutoRAG DEBUG] Attempting to parse AutoRAG response as JSON...");
        const autoRagResult = await response.json();
        console.log("[Worker AutoRAG DEBUG] Parsed AutoRAG JSON result:", JSON.stringify(autoRagResult).substring(0, 500) + '...'); 

        // --- 將 AutoRAG 回應轉換成前端需要的格式 --- 
        // 假設答案在 autoRagResult.answer 或 autoRagResult.result.response (常見格式)
        let answerContent = "(AutoRAG 未提供答案或無法解析)";
        if (autoRagResult && autoRagResult.answer) {
            answerContent = autoRagResult.answer;
        } else if (autoRagResult && autoRagResult.result && autoRagResult.result.response) {
             answerContent = autoRagResult.result.response;
        } else {
            console.warn("[Worker AutoRAG DEBUG] Could not find 'answer' or 'result.response' in AutoRAG JSON.");
        }
        console.log(`[Worker AutoRAG DEBUG] Extracted answer content (length: ${answerContent.length})`);

        const formattedResponse = {
            choices: [
                {
                    message: {
                        role: "assistant",
                        content: answerContent
                    },
                    finish_reason: "stop" 
                }
            ]
        };
        console.log("[Worker AutoRAG DEBUG] Sending formatted JSON response to client.");
        return new Response(JSON.stringify(formattedResponse), {
            status: 200,
            headers: { 'Content-Type': 'application/json' }
        });
    } else {
        // --- 處理未知 Content-Type --- 
        console.warn(`[Worker AutoRAG] Received unknown Content-Type from AutoRAG: ${contentType}. Attempting to read as text.`);
        const fallbackText = await response.text();
        console.log("[Worker AutoRAG DEBUG] AutoRAG fallback text response:", fallbackText.substring(0, 500) + '...');
         // 嘗試將純文字包裝後發送
         const formattedResponse = {
            choices: [
                {
                    message: {
                        role: "assistant",
                        content: fallbackText || "(AutoRAG 回應為空或非預期格式)"
                    },
                    finish_reason: "stop" 
                }
            ]
        };
        return new Response(JSON.stringify(formattedResponse), {
            status: 200, // 雖然格式未知，但請求成功了
            headers: { 'Content-Type': 'application/json' }
        });
    }

  } catch (e) {
    console.error("[Worker AutoRAG] FATAL Error handling /api/chat POST:", e);
    if (e.stack) {
      console.error("[Worker AutoRAG DEBUG] Error Stack:", e.stack);
    }
    const status = (e instanceof SyntaxError) ? 400 : 500;
    const errorMsg = (e instanceof SyntaxError) ? "无效的 JSON 请求体" : "處理請求時發生內部錯誤 (Worker)";
    // 在 detail 中包含更詳細的錯誤訊息
    const errorDetail = e.message + (e.cause ? ` - Cause: ${JSON.stringify(e.cause)}` : '');
    return new Response(JSON.stringify({ error: errorMsg, detail: errorDetail }), {
        status: status,
        headers: { 'Content-Type': 'application/json' },
    });
  }
}

// _worker.js 的主入口點
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const pathname = url.pathname;
    const method = request.method;

    console.log(`[Worker Start] Request: ${method} ${pathname}`); // 簡化啟動日誌

    // API 路由: 處理對 /api/chat 的 POST 請求
    if (pathname === "/api/chat" && method === "POST") {
        return handleChatRequest(request, env);
    }

    // 靜態檔案路由: 對於所有其他 GET 請求，嘗試從 ASSETS 提供服務
    if (method === "GET") {
        // console.log(`[Worker Fetch] Path '${pathname}' not API route, attempting static asset...`); // 減少靜態資源日誌
        try {
          if (!env.ASSETS) {
              console.error("[Worker Fetch] env.ASSETS is not defined. Ensure this worker is run within a Pages environment.");
              return new Response("靜態資源服務未配置", { status: 500 });
          }
          // 從 ASSETS 提供靜態文件
          return await env.ASSETS.fetch(request);
        } catch (e) {
          // 只記錄查找靜態資源的錯誤，避免過多日誌
          // console.error(`[Worker Fetch] Error fetching static asset for path '${pathname}':`, e.message);
          // 檢查是否請求根目錄，找不到通常是部署問題
          if (pathname === '/' || pathname === '/index.html') {
            console.error(`[Worker Fetch] Critical asset not found: ${pathname}`);
            return new Response("找不到主要頁面 (index.html)", { status: 404 });
          } else {
            // 對於其他資源返回標準 404
            return new Response("資源未找到 (Not Found)", { status: 404 });
          }
        }
    } else {
        // 拒絕非 GET/POST 的請求
        console.warn(`[Worker No Match] Method ${method} not allowed for path '${pathname}'.`);
        return new Response("方法不允許 (Method Not Allowed)", { status: 405 });
    }
  },
};