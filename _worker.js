// _worker.js - Modified for AutoRAG (ai-search), Serper Web Search, and Hybrid Deepseek Mode with Error Handling

// Helper function to format response for frontend
function formatResponse(content, role = "assistant", finish_reason = "stop") {
  // Basic sanitization or validation could be added here if needed
  const finalContent = typeof content === 'string' ? content : '(无效的回應内容)';
  return {
    choices: [
      {
        message: { role, content: finalContent },
        finish_reason,
      },
    ],
  };
}

// --- AutoRAG Interaction (Using ai-search for both modes now in hybrid path) ---
async function callAutoRag(endpoint, token, query) {
    console.log(`[Worker AutoRAG] Calling AutoRAG (ai-search mode) with query: "${query}"`);
    const url = new URL(endpoint);
    // Ensure we target the ai-search endpoint
    if (!url.pathname.endsWith('/ai-search')) {
         url.pathname = url.pathname.replace(/\/(search)?$/, '') + '/ai-search';
         console.log(`[Worker AutoRAG DEBUG] Adjusted URL to ai-search: ${url.toString()}`);
    } else {
         console.log(`[Worker AutoRAG DEBUG] Using existing ai-search URL: ${url.toString()}`);
    }

    const payload = {
        query: query,
        stream: false,
    };
    console.log(`[Worker AutoRAG DEBUG] Sending payload to AutoRAG (${url.toString()}):`, JSON.stringify(payload));

    const response = await fetch(url.toString(), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
    });

    console.log(`[Worker AutoRAG] Received response status from AutoRAG: ${response.status}`);
    // Log headers only if needed for debugging
    // console.log("[Worker AutoRAG DEBUG] Received response headers:", JSON.stringify(Object.fromEntries(response.headers.entries())));

    if (!response.ok) {
        let errorBody = "(Failed to read AutoRAG error body)";
        try { errorBody = await response.text(); } catch (e) { /* ignore */ }
        console.error(`[Worker AutoRAG] AutoRAG API Error: ${response.status}. Body: ${errorBody}`);
        throw new Error(`AutoRAG request failed with status ${response.status}: ${errorBody}`);
    }

    const contentType = response.headers.get("content-type") || "";
    if (!contentType.includes("application/json")) {
        const textBody = await response.text();
        console.error(`[Worker AutoRAG] Received non-JSON Content-Type from AutoRAG: ${contentType}. Body:`, textBody.substring(0, 500));
        throw new Error(`AutoRAG returned non-JSON response: ${textBody}`);
    }

    console.log(`[Worker AutoRAG DEBUG] Attempting to parse AutoRAG response as JSON...`);
    const result = await response.json();
    console.log(`[Worker AutoRAG DEBUG] Parsed AutoRAG JSON result:`, JSON.stringify(result).substring(0, 500) + '...');

    // --- Extract answer from AutoRAG response ---
    let answerContent = null; // Use null to indicate not found initially
    if (result && result.result && result.result.response) { // Primary expected format
        answerContent = result.result.response;
    } else if (result && result.answer) { // Alternative format 1
        answerContent = result.answer;
    } else if (result.choices && result.choices[0]?.message?.content) { // Alternative format 2 (OpenAI-like)
        answerContent = result.choices[0].message.content;
    }

    if (answerContent === null) {
         console.warn("[Worker AutoRAG DEBUG] Could not find expected answer in AutoRAG /ai-search JSON response. Structure:", JSON.stringify(result).substring(0, 300));
         // Decide how to handle: throw error or return null? Let's return null for now.
         // throw new Error("AutoRAG response structure unexpected, could not extract answer.");
    } else {
        console.log(`[Worker AutoRAG DEBUG] Extracted AutoRAG answer content (length: ${answerContent?.length ?? 0})`);
    }
    return answerContent; // Return only the answer string or null
}

// --- Serper Web Search Interaction ---
async function callSerperSearch(apiKey, query) {
    const SERPER_API_URL = "https://google.serper.dev/search";
    console.log(`[Worker Serper] Calling Serper API with query: "${query}"`);

    const payload = JSON.stringify({
        q: query,
        gl: 'tw', // Specify region: Taiwan
        hl: 'zh-tw', // Specify language: Traditional Chinese (Taiwan)
        num: 5 // Request top 5 results (adjust as needed)
    });

    try {
        const response = await fetch(SERPER_API_URL, {
            method: 'POST',
            headers: {
                'X-API-KEY': apiKey,
                'Content-Type': 'application/json'
            },
            body: payload
        });

        console.log(`[Worker Serper] Received response status from Serper: ${response.status}`);

        if (!response.ok) {
            let errorBody = "(Failed to read Serper error body)";
            try { errorBody = await response.text(); } catch (e) { /* ignore */ }
            console.error(`[Worker Serper] Serper API Error: ${response.status}. Body: ${errorBody}`);
            // Don't throw, just return null so Deepseek can proceed without search results
            return null;
        }

        const results = await response.json();
        console.log(`[Worker Serper DEBUG] Parsed Serper JSON result (showing first few):`, JSON.stringify(results.organic?.slice(0,2) ?? results).substring(0, 500) + '...');

        // Format results for the prompt (e.g., title + snippet)
        if (results.organic && results.organic.length > 0) {
            return results.organic.slice(0, 5) // Take top 5 organic results
                .map((item, index) => `[搜尋結果 ${index + 1}] ${item.title}\n${item.snippet || '(無摘要)'}\n來源: ${item.link || '(無連結)'}`)
                .join("\n\n");
        } else {
            console.log("[Worker Serper] No organic results found in Serper response.");
            return null; // No useful results
        }
    } catch (e) {
        console.error("[Worker Serper] FATAL Error calling Serper API:", e);
        return null; // Return null on any fetch error
    }
}


// --- Deepseek Interaction ---
async function callDeepseek(apiKey, messages, autoRagAnswer = null, searchResults = null, autoRagError = null) {
    const DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions";
    console.log("[Worker Deepseek] Calling Deepseek API...");

    // --- Construct Prompt for Deepseek ---
    let finalSystemPrompt;
    let addedInfo = false; // Flag to track if any useful info was added

    // Check if we have any context (RAG answer, Search results, or even a RAG error counts as context)
    const hasContext = autoRagAnswer || searchResults || autoRagError;
    const isDeepseekOnlyMode = !hasContext; // Helper variable

    if (hasContext) {
        // Use the detailed prompt for RAG/Hybrid modes
        finalSystemPrompt = "你是肥宅老司機 AI (FattyInsiderAI)，一個服務於台灣成年向 Podcast 節目「肥宅老司機」的助理。你的回答風格應該輕鬆有趣。請總是使用繁體中文回答。";
        finalSystemPrompt += "\n\n請整合以下資訊來回答使用者的問題：";

        if (autoRagAnswer) {
            finalSystemPrompt += `\n\n1. **節目摘要重點 (請優先參考此內容回答節目相關問題，並盡可能保留如 '(出自 S3EPXX)' 的來源標註)**:\n---\n${autoRagAnswer}\n---`;
            addedInfo = true;
        } else if (autoRagError) {
            finalSystemPrompt += `\n\n1. **注意：無法從節目摘要資料庫獲取相關資訊。** 請主要根據以下網路搜尋結果和你的通用知識回答。`;
             console.log(`[Worker Deepseek DEBUG] AutoRAG failed with error: ${autoRagError}`); // Log the original error
        } else {
            finalSystemPrompt += `\n\n1. **節目摘要資料庫中未找到相關資訊。** 請主要根據以下網路搜尋結果和你的通用知識回答。`;
        }

        if (searchResults) {
            finalSystemPrompt += `\n\n2. **網路搜尋結果 (用於補充時事、通用知識或節目未提及的細節)**:\n---\n${searchResults}\n---`;
            addedInfo = true;
        } else {
            if (!autoRagAnswer && hasContext) { // Add note only if RAG context was expected but missing/failed
                finalSystemPrompt += `\n\n2. **網路搜尋也未執行或未找到結果。**`;
            }
        }

        // Final instruction based on what info was available
        if (addedInfo) {
             finalSystemPrompt += "\n\n請用自然、口語化的方式綜合以上資訊，提供一個完整且有趣的回答。";
             if (autoRagAnswer && searchResults) { // Only add conflict instruction if both are present
                 finalSystemPrompt += "如果節目摘要和網路搜尋結果有衝突，請優先採信節目摘要的內容，或婉轉指出可能的差異。";
             } else if (autoRagAnswer) {
                 finalSystemPrompt += "請盡可能保留如 '(出自 S3EPXX)' 的來源標註。";
             }
        } else {
             // Neither RAG nor Search provided info, but AutoRAG might have failed
             finalSystemPrompt += "\n\n請根據你的通用知識回答。";
        }
    } else {
         // No context provided (Deepseek-only mode)
         finalSystemPrompt = "你是一個使用繁體中文回答問題的通用 AI 助理。請直接、準確地回答使用者的問題。如果使用者要求翻譯，請在回答中同時提供原文和譯文以方便對照。";
         console.log("[Worker Deepseek DEBUG] Using generic system prompt for Deepseek-only mode.");
    }

    // Prepare messages for Deepseek: Add the constructed system prompt and user/assistant history
    let messagesForDeepseek = [{ role: "system", content: finalSystemPrompt }];
    messagesForDeepseek = messagesForDeepseek.concat(messages); // Add conversation history

    // Optional: Clean up history slightly? Maybe remove previous AI answers if prompt gets too long?
    // For now, keep full history.

    console.log("[Worker Deepseek DEBUG] Final system prompt for Deepseek:", finalSystemPrompt);
    console.log("[Worker Deepseek DEBUG] Message history being sent (excluding new system prompt):", JSON.stringify(messages, null, 2));

    const payload = {
        model: "deepseek-chat",
        messages: messagesForDeepseek,
        stream: false
    };

    const response = await fetch(DEEPSEEK_API_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${apiKey}`
        },
        body: JSON.stringify(payload)
    });

    console.log(`[Worker Deepseek] Received response status from Deepseek: ${response.status}`);

    if (!response.ok) {
        let errorBody = "(Failed to read Deepseek error body)";
        try { errorBody = await response.text(); } catch (e) { /* ignore */ }
        console.error(`[Worker Deepseek] Deepseek API Error: ${response.status}. Body: ${errorBody}`);
        throw new Error(`Deepseek request failed with status ${response.status}: ${errorBody}`);
    }

    const result = await response.json();
    console.log("[Worker Deepseek DEBUG] Parsed Deepseek JSON result:", JSON.stringify(result).substring(0, 500) + '...');
    // Extract the actual response content
     if (result.choices && result.choices[0] && result.choices[0].message && result.choices[0].message.content) {
         return result.choices[0].message.content;
     } else {
         console.warn("[Worker Deepseek DEBUG] Could not find expected content in Deepseek JSON response.");
         throw new Error("Deepseek response structure unexpected, could not extract answer.");
     }
}

/**
 * Handles direct RAG search requests to /functions/ai-search.
 */
async function handleAiSearchRequest(request, env) {
    console.log("[Worker AI Search] Entering handleAiSearchRequest...");
    let requestBody;
    try {
        requestBody = await request.json();
    } catch (e) {
        console.error("[Worker AI Search] Invalid JSON body:", e);
        return new Response(JSON.stringify({ error: "无效的 JSON 请求体" }), { status: 400, headers: { "Content-Type": "application/json" } });
    }

    // 檢查是否有來自前端的 useTravelRag 標記
    const { query, useTravelRag } = requestBody;

    if (!query || typeof query !== 'string' /*|| query.trim() === ''*/) {
         // Allow empty query if prefix was used, handle potential downstream errors
        if (query !== "" || !useTravelRag) { // Only error if query is not empty string OR prefix wasn't used
            console.error("[Worker AI Search] Missing or invalid 'query' in request.");
            return new Response(JSON.stringify({ error: "请求体中缺少有效的 'query' 字段" }), { status: 400, headers: { "Content-Type": "application/json" } });
        }
         console.warn("[Worker AI Search] Received empty query, likely due to prefix removal. Proceeding...");
    }

    console.log(`[Worker AI Search] Received query: "${query}", useTravelRag flag: ${useTravelRag}`);

    // --- Decide RAG instance based on flag or query content ---
    let targetEndpoint = '';
    let targetToken = '';
    let selectedRag = '';
    const lowerQuery = query.toLowerCase();

    // 1. 檢查是否有強制使用 Travel RAG 的標記
    if (useTravelRag === true) {
        console.log("[Worker AI Search] Selecting Travel RAG based on useTravelRag flag from frontend.");
        targetEndpoint = env.AUTORAG_TRAVEL_ENDPOINT;
        targetToken = env.AUTORAG_TRAVEL_TOKEN;
        selectedRag = 'Travel (Flag Triggered)';
    }
    // 2. 如果沒有標記，執行關鍵字判斷邏輯
    else if (containsKeyword(lowerQuery, TRAVEL_KEYWORDS)) {
        console.log("[Worker AI Search] Query contains travel keywords. Selecting Travel RAG.");
        targetEndpoint = env.AUTORAG_TRAVEL_ENDPOINT;
        targetToken = env.AUTORAG_TRAVEL_TOKEN;
        selectedRag = 'Travel (Query Keyword)';
    } else if (containsKeyword(lowerQuery, PODCAST_KEYWORDS)) {
        console.log("[Worker AI Search] Query contains podcast keywords. Selecting Podcast RAG.");
        targetEndpoint = env.AUTORAG_ENDPOINT;
        targetToken = env.AUTORAG_API_TOKEN;
        selectedRag = 'Podcast (Query Keyword)';
    } else {
        console.log("[Worker AI Search] No flag and no specific keywords matched. Defaulting to Podcast RAG.");
        targetEndpoint = env.AUTORAG_ENDPOINT;
        targetToken = env.AUTORAG_API_TOKEN;
        selectedRag = 'Podcast (Default)';
    }

    // Check environment variables
    if (!targetEndpoint || !targetToken) {
        // ... (Error handling for missing env vars - same as before) ...
         console.error(`[Worker AI Search] Missing environment variables for selected RAG: ${selectedRag}. Endpoint found: ${!!targetEndpoint}, Token found: ${!!targetToken}`);
         let missingVars = [];
         if (!targetEndpoint) missingVars.push(selectedRag.includes('Travel') ? 'AUTORAG_TRAVEL_ENDPOINT' : 'AUTORAG_ENDPOINT');
         if (!targetToken) missingVars.push(selectedRag.includes('Travel') ? 'AUTORAG_TRAVEL_TOKEN' : 'AUTORAG_API_TOKEN');
         return new Response(JSON.stringify({ error: `後端 ${selectedRag} AutoRAG 設定未完成`, details: `缺少環境變數: ${missingVars.join(', ')}` }), { status: 500, headers: { "Content-Type": "application/json" } });
    }

    console.log(`[Worker AI Search] Using ${selectedRag} RAG. Endpoint: ${targetEndpoint.substring(0, 60)}... Token: [REDACTED]`);

    // --- Call the selected AutoRAG API --- 
    try {
        // Use the existing callAutoRag function, which returns the answer string or null
        const autoRagAnswer = await callAutoRag(targetEndpoint, targetToken, query);

        if (autoRagAnswer === null) {
             console.error("[Worker AI Search] AutoRAG failed to provide an answer.");
             // Return a structured error, similar to how /api/chat might handle it
             return new Response(JSON.stringify({ error: "無法從 AutoRAG 獲取回答", detail: "Response structure might be incorrect or API failed." }), { status: 500, headers: { 'Content-Type': 'application/json' }});
        }

        // Format the successful response similar to /api/chat's final step
        const formattedResponse = formatResponse(autoRagAnswer);
        console.log("[Worker AI Search DEBUG] Sending formatted AutoRAG response to client.");
        const headers = new Headers({ 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
        return new Response(JSON.stringify(formattedResponse), {
            status: 200,
            headers: headers
        });

    } catch (e) {
         console.error("[Worker AI Search] Error calling AutoRAG:", e);
         return new Response(JSON.stringify({ error: "呼叫 AutoRAG 時發生內部錯誤", details: e.message || "Unknown fetch error" }), { status: 500, headers: { "Content-Type": "application/json" } });
    }
}

/**
 * Handles chat requests, routing based on mode.
 */
async function handleChatRequest(request, env) {
    console.log("[Worker Request] Entering handleChatRequest...");
    let requestBody;
    try {
        requestBody = await request.json();
        console.log("[Worker Request DEBUG] Parsed request body.");
    } catch (e) {
        console.error("[Worker Request] Invalid JSON in request body:", e);
        return new Response(JSON.stringify({ error: "无效的 JSON 请求体" }), { status: 400, headers: { "Content-Type": "application/json" } });
    }

    const messages = requestBody.messages;
    const mode = requestBody.mode || 'autorag'; // Default to 'autorag'
    console.log(`[Worker Request] Received mode: ${mode}`);

    if (!messages || !Array.isArray(messages) || messages.length === 0) {
        console.error("[Worker Request] Invalid or missing 'messages' in request body.");
        return new Response(JSON.stringify({ error: "请求体中缺少有效的 'messages' 字段" }), { status: 400, headers: { "Content-Type": "application/json" } });
    }

    const lastUserMessage = messages.findLast(msg => msg.role === 'user');
    if (!lastUserMessage || !lastUserMessage.content) {
        console.error("[Worker Request] No user message found in history.");
        return new Response(JSON.stringify({ error: "聊天歷史中找不到使用者訊息" }), { status: 400, headers: { "Content-Type": "application/json" } });
    }
    const userQuery = lastUserMessage.content;
    console.log(`[Worker Request DEBUG] Extracted user query: "${userQuery}"`);

    // --- Get Environment Variables ---
    const { AUTORAG_ENDPOINT, AUTORAG_API_TOKEN, DEEPSEEK_API_KEY, SERPER_API_KEY } = env;

    console.log(`[Worker ENV DEBUG] AUTORAG_ENDPOINT: ${AUTORAG_ENDPOINT ? 'Loaded' : 'MISSING!'}`);
    console.log(`[Worker ENV DEBUG] AUTORAG_API_TOKEN: ${AUTORAG_API_TOKEN ? 'Loaded' : 'MISSING!'}`);
    console.log(`[Worker ENV DEBUG] DEEPSEEK_API_KEY: ${DEEPSEEK_API_KEY ? 'Loaded' : 'MISSING!'}`);
    console.log(`[Worker ENV DEBUG] SERPER_API_KEY: ${SERPER_API_KEY ? 'Loaded' : 'MISSING!'}`); // Check Serper key

    if (!AUTORAG_ENDPOINT || !AUTORAG_API_TOKEN) {
        console.error("[Worker ENV] AutoRAG environment variables missing.");
        return new Response(JSON.stringify({ error: "後端 AutoRAG 設定未完成" }), { status: 500, headers: { "Content-Type": "application/json" } });
    }

    // Filter message history (remove system prompts before sending to APIs)
    const conversationHistory = messages.filter(msg => msg.role !== 'system');

    try {
        if (mode === 'deepseek') {
            console.log("[Worker Logic] Entering Deepseek-Only Mode...");
            if (!DEEPSEEK_API_KEY) {
                console.error("[Worker ENV] DEEPSEEK_API_KEY is missing for Deepseek-only mode.");
                return new Response(JSON.stringify({ error: "後端 Deepseek API 金鑰未設定" }), { status: 500, headers: { "Content-Type": "application/json" } });
            }

            // Call Deepseek directly without RAG or Search context
            const deepseekAnswer = await callDeepseek(DEEPSEEK_API_KEY, [...conversationHistory], null, null, null);
            const formattedResponse = formatResponse(deepseekAnswer);
            console.log("[Worker Logic DEBUG] Sending formatted Deepseek response to client (Deepseek-Only Mode).");
            return new Response(JSON.stringify(formattedResponse), { status: 200, headers: { 'Content-Type': 'application/json' } });

        } else if (mode === 'hybrid') {
            console.log("[Worker Logic] Entering Hybrid Mode (AutoRAG -> Serper -> Deepseek)...");
            if (!DEEPSEEK_API_KEY) {
                console.error("[Worker ENV] DEEPSEEK_API_KEY is missing for Hybrid mode.");
                return new Response(JSON.stringify({ error: "後端 Deepseek API 金鑰未設定" }), { status: 500, headers: { "Content-Type": "application/json" } });
            }
             let serperKeyAvailable = true; // Assume available initially
             if (!SERPER_API_KEY) {
                console.error("[Worker ENV] SERPER_API_KEY is missing for Hybrid mode web search.");
                console.warn("[Worker Logic] SERPER_API_KEY missing, proceeding without web search.");
                serperKeyAvailable = false;
             }

            let autoRagAnswer = null;
            let autoRagError = null; // Variable to store potential AutoRAG error message

            // 1. Call AutoRAG (ai-search) and catch errors
            console.log("[Worker Logic] Step 1: Calling AutoRAG ai-search...");
            try {
                 autoRagAnswer = await callAutoRag(AUTORAG_ENDPOINT, AUTORAG_API_TOKEN, userQuery);
                 if (autoRagAnswer === null) {
                     console.warn("[Worker Logic] AutoRAG did not return a valid answer (returned null). Continuing...");
                 }
            } catch (e) {
                console.error("[Worker Logic] AutoRAG call failed:", e.message);
                autoRagError = e.message; // Store the error message
                autoRagAnswer = null; // Ensure answer is null on error
            }


            // 2. Call Serper (if key exists)
             let searchResults = null;
             if (serperKeyAvailable) { // Use the flag check
                console.log("[Worker Logic] Step 2: Calling Serper Web Search...");
                searchResults = await callSerperSearch(SERPER_API_KEY, userQuery);
                 if (searchResults === null) {
                     console.warn("[Worker Logic] Web search failed or returned no results.");
                 }
             } else {
                 console.log("[Worker Logic] Step 2: Skipping web search (SERPER_API_KEY not found).");
             }


            // 3. Call Deepseek with RAG answer, Search results, and potential RAG error
            console.log("[Worker Logic] Step 3: Calling Deepseek for synthesis...");
            const deepseekFinalAnswer = await callDeepseek(DEEPSEEK_API_KEY, [...conversationHistory], autoRagAnswer, searchResults, autoRagError); // Pass autoRagError

            // 4. Format and return Deepseek response
            console.log(`[Worker Logic DEBUG] Extracted Deepseek final answer (Hybrid Mode, length: ${deepseekFinalAnswer.length})`);
            const formattedResponse = formatResponse(deepseekFinalAnswer);
            console.log("[Worker Logic DEBUG] Sending formatted Deepseek response to client (Hybrid Mode).");
            return new Response(JSON.stringify(formattedResponse), { status: 200, headers: { 'Content-Type': 'application/json' } });

        } else { // Default 'autorag' mode
            console.log("[Worker Logic] Entering AutoRAG Mode (default)...");
            // Call AutoRAG (ai-search)
            const autoRagAnswer = await callAutoRag(AUTORAG_ENDPOINT, AUTORAG_API_TOKEN, userQuery);

            if (autoRagAnswer === null) {
                // Handle case where AutoRAG fails or returns unexpected structure
                console.error("[Worker Logic] AutoRAG failed to provide an answer in AutoRAG mode.");
                 return new Response(JSON.stringify({ error: "無法從 AutoRAG 獲取回答", detail: "Response structure might be incorrect or API failed." }), { status: 500, headers: { 'Content-Type': 'application/json' }});
            }

            // Format and return AutoRAG response
            const formattedResponse = formatResponse(autoRagAnswer);
            console.log("[Worker Logic DEBUG] Sending formatted AutoRAG response to client (AutoRAG Mode).");
            return new Response(JSON.stringify(formattedResponse), { status: 200, headers: { 'Content-Type': 'application/json' } });
        }

    } catch (e) {
        console.error("[Worker Logic] FATAL Error during processing:", e);
        if (e.stack) console.error("[Worker Logic DEBUG] Error Stack:", e.stack);
        const errorMsg = "處理請求時發生內部錯誤 (Worker)";
        const errorDetail = e.message || "Unknown error";
        return new Response(JSON.stringify({ error: errorMsg, detail: errorDetail }), { status: 500, headers: { 'Content-Type': 'application/json' } });
    }
}

// _worker.js entry point
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const pathname = url.pathname;
    const method = request.method;

    console.log(`[Worker Entry] Request: ${method} ${pathname}`);

    // --- New Route for direct AI Search --- 
    if (pathname === "/functions/ai-search" && method === "POST") {
        return handleAiSearchRequest(request, env);
    }

    // --- Existing API route for chat --- 
    if (pathname === "/api/chat" && method === "POST") {
        return handleChatRequest(request, env);
    }

    // --- CORS Preflight for both routes --- 
    if (method === "OPTIONS" && (pathname === "/api/chat" || pathname === "/functions/ai-search")) {
        return new Response(null, {
            status: 204,
            headers: {
              'Access-Control-Allow-Origin': '*',
              'Access-Control-Allow-Methods': 'POST, OPTIONS',
              'Access-Control-Allow-Headers': 'Content-Type',
              'Access-Control-Max-Age': '86400',
            },
          });
    }

    // Static assets route
    if (method === "GET") {
        try {
            if (!env.ASSETS) {
                console.error("[Worker Static] env.ASSETS is not defined.");
                return new Response("靜態資源服務未配置", { status: 500 });
            }
            return await env.ASSETS.fetch(request);
        } catch (e) {
            if (pathname === '/' || pathname === '/index.html') {
                console.error(`[Worker Static] Critical asset not found: ${pathname}`, e.message);
                return new Response("找不到主要頁面 (index.html)", { status: 404 });
            } else {
                return new Response("資源未找到 (Not Found)", { status: 404 });
            }
        }
    }

    // Other methods
    console.warn(`[Worker Entry] Method ${method} not allowed for path '${pathname}'.`);
    return new Response("方法不允許 (Method Not Allowed)", { status: 405 });
  },
};