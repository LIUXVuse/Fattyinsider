// _worker.js

/**
 * 呼叫 DeepSeek API 並處理響應，支持流式輸出。
 * @param {Array<object>} messages - 對話歷史
 * @param {string} apiKey - DeepSeek API Key
 * @returns {Promise<Response>} - 返回給客戶端的 Response 物件
 */
async function generateChatResponse(messages, apiKey) {
  console.log(`[DeepSeek Call] Using API Key: ${apiKey ? 'Provided' : 'MISSING!'}`);
  if (!apiKey) {
    console.error("[DeepSeek Call] DEEPSEEK_API_KEY environment variable not set.");
    const errorResponse = { error: "服務端未配置 API Key" };
    return new Response(JSON.stringify(errorResponse), {
      status: 500, // 使用 500 Internal Server Error 更合適
      headers: { "Content-Type": "application/json" },
    });
  }

  // 消息歷史優化 (與 Python 版本邏輯相同)
  const MAX_HISTORY = 10;
  if (messages.length > MAX_HISTORY) {
    const systemMessages = messages.filter(msg => msg.role === 'system');
    const numRecent = Math.max(0, MAX_HISTORY - systemMessages.length);
    const recentMessages = numRecent > 0 ? messages.slice(-numRecent) : [];
    messages = [...systemMessages, ...recentMessages];
    console.log(`[DeepSeek Call] Message history optimized to ${messages.length} messages.`);
  }

  const requestData = {
    model: "deepseek-chat", // 確認模型名稱正確
    messages: messages,
    temperature: 0.7,
    max_tokens: 4096,
    stream: true,
  };

  const deepseekUrl = "https://api.deepseek.com/v1/chat/completions";
  const fetchHeaders = new Headers({
    "Content-Type": "application/json",
    "Authorization": `Bearer ${apiKey}`,
  });

  try {
    console.log(`[DeepSeek Call] Sending request to DeepSeek API: ${JSON.stringify(requestData)}`);
    const apiResponse = await fetch(deepseekUrl, {
      method: "POST",
      headers: fetchHeaders,
      body: JSON.stringify(requestData),
    });
    console.log(`[DeepSeek Call] Received DeepSeek API status: ${apiResponse.status}`);

    if (!apiResponse.ok) {
      const errorBody = await apiResponse.text();
      console.error(`[DeepSeek Call] DeepSeek API HTTP Error: ${apiResponse.status}`);
      console.error(`[DeepSeek Call] Error Body: ${errorBody}`);
      const responseData = { error: `DeepSeek API 請求失敗: ${apiResponse.status}`, detail: errorBody };
      return new Response(JSON.stringify(responseData), {
        status: apiResponse.status,
        headers: { "Content-Type": "application/json" },
      });
    }

    // --- 處理流式響應 ---
    // 檢查 Content-Type 是否為 event-stream
    const contentType = apiResponse.headers.get("content-type") || "";
    if (!contentType.includes("event-stream")) {
        console.error("[DeepSeek Call] Unexpected Content-Type from DeepSeek API:", contentType);
        // 如果不是流式，嘗試讀取完整 JSON (雖然設定了 stream:true，以防萬一)
        try {
             const fallbackJson = await apiResponse.json();
             // 需要模擬成流式的第一個事件發送給前端？或者直接報錯？
             // 這裡先報錯處理
             const errorResponse = { error: "後端收到非預期的非流式回應" };
             return new Response(JSON.stringify(errorResponse), {
                 status: 500,
                 headers: { "Content-Type": "application/json" },
             });
        } catch (e) {
             const fallbackText = await apiResponse.text();
              console.error("[DeepSeek Call] Failed to parse non-stream response as JSON:", fallbackText);
              const errorResponse = { error: "後端收到無法解析的回應", detail: fallbackText };
             return new Response(JSON.stringify(errorResponse), {
                 status: 500,
                 headers: { "Content-Type": "application/json" },
             });
        }
    }

    // 設定返回給客戶端的 SSE Headers
    const responseHeaders = new Headers({
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache",
      "Connection": "keep-alive",
    });

    console.log("[DeepSeek Call] Streaming DeepSeek API response to client...");
    // 直接將 DeepSeek API 的流式響應 body 返回給客戶端
    // Cloudflare Workers 會自動處理 ReadableStream
    return new Response(apiResponse.body, {
      status: apiResponse.status,
      headers: responseHeaders,
    });

  } catch (e) {
    console.error("[DeepSeek Call] Unknown error calling DeepSeek API or processing response:", e);
    const responseData = { error: "服務端內部錯誤 (Worker)" };
    return new Response(JSON.stringify(responseData), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
}

// _worker.js 的主入口點
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const pathname = url.pathname;
    const method = request.method;

    console.log(`[Worker Fetch] Method=${method}, Path=${pathname}`);

    // API 路由: 處理對 /api/chat 的 POST 請求
    if (pathname === "/api/chat" && method === "POST") {
      console.log("[Worker Fetch] Handling /api/chat POST...");
      try {
        const requestBody = await request.json();
        const messages = requestBody.messages;

        if (!messages || !Array.isArray(messages) || messages.length === 0) {
          console.error("[Worker Fetch] Invalid or missing 'messages' in request body.");
          const errorResponse = { error: "请求体中缺少有效的 'messages' 字段" };
          return new Response(JSON.stringify(errorResponse), {
            status: 400,
            headers: { "Content-Type": "application/json" },
          });
        }

        // 從環境變數獲取 API Key (重要！)
        const apiKey = env.DEEPSEEK_API_KEY;

        // 調用核心邏輯函數
        return await generateChatResponse(messages, apiKey);

      } catch (e) {
        if (e instanceof SyntaxError) { // JSON 解析錯誤
             console.error("[Worker Fetch] Invalid JSON in request body:", e);
             const errorResponse = { error: "无效的 JSON 请求体" };
             return new Response(JSON.stringify(errorResponse), {
                status: 400,
                headers: { "Content-Type": "application/json" },
             });
        } else {
            console.error("[Worker Fetch] Unknown error handling /api/chat POST:", e);
            const errorResponse = { error: "處理請求時發生內部錯誤 (Worker)" };
            return new Response(JSON.stringify(errorResponse), {
                status: 500,
                headers: { "Content-Type": "application/json" },
            });
        }
      }
    }

    // 靜態檔案路由: 對於所有其他請求，嘗試從 ASSETS 提供服務
    console.log(`[Worker Fetch] Path '${pathname}' not API route, attempting static asset...`);
    try {
      return await env.ASSETS.fetch(request);
    } catch (e) {
      console.error(`[Worker Fetch] Error fetching static asset for path '${pathname}':`, e);
      // 對於找不到的靜態資源，返回 404 HTML 頁面可能更好，但文字也可以
      return new Response("資源未找到 (Not Found)", { status: 404 });
    }
  },
};