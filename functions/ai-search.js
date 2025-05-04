// functions/ai-search.js

// --- 關鍵字列表 (用於 query 內容判斷) ---
// 全部轉為小寫以方便比對
const PODCAST_KEYWORDS = ['s3ep', '哪一集', '老雞', '依依', '節目', '回聽'];
// 將 "關生" 和 "探店" 加入 travel 關鍵字，提高優先級
const TRAVEL_KEYWORDS = ['關生', '探店', '按摩', '快餐', 'gogobar', '包夜', '胡志明', '芭提雅'];

// Helper function to check if query contains any keyword from a list
function containsKeyword(query, keywords) {
  const lowerQuery = query.toLowerCase();
  return keywords.some(keyword => lowerQuery.includes(keyword));
}

// Cloudflare Pages Function handler for POST requests
export async function onRequestPost(context) {
  const { request, env } = context;

  let requestBody;
  try {
    requestBody = await request.json();
  } catch (e) {
    console.error("[AI Search Func] Invalid JSON body:", e);
    return new Response(JSON.stringify({ error: "无效的 JSON 请求体" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  const { query, type } = requestBody;

  if (!query || typeof query !== 'string' || query.trim() === '') {
    console.error("[AI Search Func] Missing or invalid 'query' in request.");
    return new Response(JSON.stringify({ error: "请求体中缺少有效的 'query' 字段" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  console.log(`[AI Search Func] Received query: "${query}", type: "${type}"`);

  // --- 決定使用哪個 AutoRAG 實例 (優化判斷順序) ---
  let targetEndpoint = '';
  let targetToken = '';
  let selectedRag = ''; // For logging

  const lowerQuery = query.toLowerCase(); // 先轉換一次，避免重複轉換

  // 1. 優先檢查探店關鍵字 (包含 "關生" 和 "探店")
  if (containsKeyword(lowerQuery, TRAVEL_KEYWORDS)) {
      console.log("[AI Search Func] Query contains travel keywords (關生/探店 prioritized). Selecting Travel RAG.");
      targetEndpoint = env.AUTORAG_TRAVEL_ENDPOINT;
      targetToken = env.AUTORAG_TRAVEL_TOKEN;
      selectedRag = 'Travel (Query Keyword)';
  }
  // 2. 如果沒有探店關鍵字，再檢查節目關鍵字
  else if (containsKeyword(lowerQuery, PODCAST_KEYWORDS)) {
      console.log("[AI Search Func] Query contains podcast keywords. Selecting Podcast RAG.");
      targetEndpoint = env.AUTORAG_ENDPOINT;
      targetToken = env.AUTORAG_API_TOKEN;
      selectedRag = 'Podcast (Query Keyword)';
  }
  // 3. 如果都沒有，預設使用 Podcast RAG
  else {
      console.log("[AI Search Func] No specific keywords matched. Defaulting to Podcast RAG.");
      targetEndpoint = env.AUTORAG_ENDPOINT;
      targetToken = env.AUTORAG_API_TOKEN;
      selectedRag = 'Podcast (Default)';
  }

  // --- 檢查環境變數是否存在 ---
  if (!targetEndpoint || !targetToken) {
    console.error(`[AI Search Func] Missing environment variables for selected RAG: ${selectedRag}. Endpoint found: ${!!targetEndpoint}, Token found: ${!!targetToken}`);
    let missingVars = [];
    if (!targetEndpoint) missingVars.push(selectedRag.includes('Travel') ? 'AUTORAG_TRAVEL_ENDPOINT' : 'AUTORAG_ENDPOINT');
    if (!targetToken) missingVars.push(selectedRag.includes('Travel') ? 'AUTORAG_TRAVEL_TOKEN' : 'AUTORAG_API_TOKEN');

    return new Response(JSON.stringify({
        error: `後端 ${selectedRag} AutoRAG 設定未完成`,
        details: `缺少環境變數: ${missingVars.join(', ')}`
    }), {
      status: 500, // Internal Server Error
      headers: { "Content-Type": "application/json" },
    });
  }

  console.log(`[AI Search Func] Using ${selectedRag} RAG. Endpoint: ${targetEndpoint.substring(0, 60)}... Token: [REDACTED]`);

  // --- 呼叫選定的 AutoRAG API ---
  const autoRagPayload = {
    query: query,
    stream: false, // 目前先用非流式，若需流式要再調整
  };

  try {
    const response = await fetch(targetEndpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${targetToken}`,
      },
      body: JSON.stringify(autoRagPayload),
    });

    console.log(`[AI Search Func] AutoRAG API response status: ${response.status}`);

    // 直接將 AutoRAG 的回應 (包含狀態碼、標頭、內容) 回傳給前端
    // 這樣前端就能收到原始的成功或失敗資訊
    const headers = new Headers(response.headers);
    headers.set('Access-Control-Allow-Origin', '*'); // 如果需要 CORS

    // return response; // This forwards the response directly, good for simple pass-through

    // Or read the body to potentially log/modify before sending
     const responseBody = await response.text(); // Read as text first
     try {
         const jsonData = JSON.parse(responseBody); // Try parsing as JSON
         console.log(`[AI Search Func DEBUG] Parsed AutoRAG response body (first 300 chars):`, responseBody.substring(0, 300));
         return new Response(JSON.stringify(jsonData), {
             status: response.status,
             headers: headers // Pass original headers + CORS
         });
     } catch(parseError) {
         console.warn("[AI Search Func DEBUG] AutoRAG response was not valid JSON. Body:", responseBody.substring(0, 500));
         // Return the raw text response if not JSON
          return new Response(responseBody, {
             status: response.status,
             headers: headers // Pass original headers + CORS
         });
     }


  } catch (e) {
    console.error("[AI Search Func] Error calling AutoRAG API:", e);
    return new Response(JSON.stringify({
        error: "呼叫 AutoRAG 時發生內部錯誤",
        details: e.message || "Unknown fetch error"
    }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
}

// Handle other methods if needed, e.g., OPTIONS for CORS preflight
export async function onRequestOptions(context) {
  return new Response(null, {
    status: 204,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
      'Access-Control-Max-Age': '86400', // Cache preflight for 1 day
    },
  });
} 