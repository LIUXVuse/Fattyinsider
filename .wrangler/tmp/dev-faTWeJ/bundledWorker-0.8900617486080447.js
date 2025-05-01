var __defProp = Object.defineProperty;
var __name = (target, value) => __defProp(target, "name", { value, configurable: true });

// .wrangler/tmp/pages-USfAWB/bundledWorker-0.8900617486080447.mjs
var __defProp2 = Object.defineProperty;
var __name2 = /* @__PURE__ */ __name((target, value) => __defProp2(target, "name", { value, configurable: true }), "__name");
function formatResponse(content, role = "assistant", finish_reason = "stop") {
  const finalContent = typeof content === "string" ? content : "(\u65E0\u6548\u7684\u56DE\u61C9\u5185\u5BB9)";
  return {
    choices: [
      {
        message: { role, content: finalContent },
        finish_reason
      }
    ]
  };
}
__name(formatResponse, "formatResponse");
__name2(formatResponse, "formatResponse");
async function callAutoRag(endpoint, token, query) {
  console.log(`[Worker AutoRAG] Calling AutoRAG (ai-search mode) with query: "${query}"`);
  const url = new URL(endpoint);
  if (!url.pathname.endsWith("/ai-search")) {
    url.pathname = url.pathname.replace(/\/(search)?$/, "") + "/ai-search";
    console.log(`[Worker AutoRAG DEBUG] Adjusted URL to ai-search: ${url.toString()}`);
  } else {
    console.log(`[Worker AutoRAG DEBUG] Using existing ai-search URL: ${url.toString()}`);
  }
  const payload = {
    query,
    stream: false
  };
  console.log(`[Worker AutoRAG DEBUG] Sending payload to AutoRAG (${url.toString()}):`, JSON.stringify(payload));
  const response = await fetch(url.toString(), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  });
  console.log(`[Worker AutoRAG] Received response status from AutoRAG: ${response.status}`);
  if (!response.ok) {
    let errorBody = "(Failed to read AutoRAG error body)";
    try {
      errorBody = await response.text();
    } catch (e) {
    }
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
  console.log(`[Worker AutoRAG DEBUG] Parsed AutoRAG JSON result:`, JSON.stringify(result).substring(0, 500) + "...");
  let answerContent = null;
  if (result && result.result && result.result.response) {
    answerContent = result.result.response;
  } else if (result && result.answer) {
    answerContent = result.answer;
  } else if (result.choices && result.choices[0]?.message?.content) {
    answerContent = result.choices[0].message.content;
  }
  if (answerContent === null) {
    console.warn("[Worker AutoRAG DEBUG] Could not find expected answer in AutoRAG /ai-search JSON response. Structure:", JSON.stringify(result).substring(0, 300));
  } else {
    console.log(`[Worker AutoRAG DEBUG] Extracted AutoRAG answer content (length: ${answerContent?.length ?? 0})`);
  }
  return answerContent;
}
__name(callAutoRag, "callAutoRag");
__name2(callAutoRag, "callAutoRag");
async function callSerperSearch(apiKey, query) {
  const SERPER_API_URL = "https://google.serper.dev/search";
  console.log(`[Worker Serper] Calling Serper API with query: "${query}"`);
  const payload = JSON.stringify({
    q: query,
    num: 5
    // Request top 5 results (adjust as needed)
  });
  try {
    const response = await fetch(SERPER_API_URL, {
      method: "POST",
      headers: {
        "X-API-KEY": apiKey,
        "Content-Type": "application/json"
      },
      body: payload
    });
    console.log(`[Worker Serper] Received response status from Serper: ${response.status}`);
    if (!response.ok) {
      let errorBody = "(Failed to read Serper error body)";
      try {
        errorBody = await response.text();
      } catch (e) {
      }
      console.error(`[Worker Serper] Serper API Error: ${response.status}. Body: ${errorBody}`);
      return null;
    }
    const results = await response.json();
    console.log(`[Worker Serper DEBUG] Parsed Serper JSON result (showing first few):`, JSON.stringify(results.organic?.slice(0, 2) ?? results).substring(0, 500) + "...");
    if (results.organic && results.organic.length > 0) {
      return results.organic.slice(0, 5).map((item, index) => `[\u641C\u5C0B\u7D50\u679C ${index + 1}] ${item.title}
${item.snippet || "(\u7121\u6458\u8981)"}
\u4F86\u6E90: ${item.link || "(\u7121\u9023\u7D50)"}`).join("\n\n");
    } else {
      console.log("[Worker Serper] No organic results found in Serper response.");
      return null;
    }
  } catch (e) {
    console.error("[Worker Serper] FATAL Error calling Serper API:", e);
    return null;
  }
}
__name(callSerperSearch, "callSerperSearch");
__name2(callSerperSearch, "callSerperSearch");
async function callDeepseek(apiKey, messages, autoRagAnswer = null, searchResults = null, autoRagError = null) {
  const DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions";
  console.log("[Worker Deepseek] Calling Deepseek API...");
  const baseSystemPrompt = "\u4F60\u662F\u80A5\u5B85\u8001\u53F8\u6A5F AI (FattyInsiderAI)\uFF0C\u4E00\u500B\u670D\u52D9\u65BC\u53F0\u7063\u6210\u5E74\u5411 Podcast \u7BC0\u76EE\u300C\u80A5\u5B85\u8001\u53F8\u6A5F\u300D\u7684\u52A9\u7406\u3002\u4F60\u7684\u56DE\u7B54\u98A8\u683C\u61C9\u8A72\u8F15\u9B06\u6709\u8DA3\u3002\u8ACB\u7E3D\u662F\u4F7F\u7528\u7E41\u9AD4\u4E2D\u6587\u56DE\u7B54\u3002";
  let finalSystemPrompt = baseSystemPrompt;
  let addedInfo = false;
  finalSystemPrompt += "\n\n\u8ACB\u6574\u5408\u4EE5\u4E0B\u8CC7\u8A0A\u4F86\u56DE\u7B54\u4F7F\u7528\u8005\u7684\u554F\u984C\uFF1A";
  if (autoRagAnswer) {
    finalSystemPrompt += `

1. **\u7BC0\u76EE\u6458\u8981\u91CD\u9EDE (\u8ACB\u512A\u5148\u53C3\u8003\u6B64\u5167\u5BB9\u56DE\u7B54\u7BC0\u76EE\u76F8\u95DC\u554F\u984C\uFF0C\u4E26\u76E1\u53EF\u80FD\u4FDD\u7559\u5982 '(\u51FA\u81EA S3EPXX)' \u7684\u4F86\u6E90\u6A19\u8A3B)**:
---
${autoRagAnswer}
---`;
    addedInfo = true;
  } else if (autoRagError) {
    finalSystemPrompt += `

1. **\u6CE8\u610F\uFF1A\u7121\u6CD5\u5F9E\u7BC0\u76EE\u6458\u8981\u8CC7\u6599\u5EAB\u7372\u53D6\u76F8\u95DC\u8CC7\u8A0A\u3002** \u8ACB\u4E3B\u8981\u6839\u64DA\u4EE5\u4E0B\u7DB2\u8DEF\u641C\u5C0B\u7D50\u679C\u548C\u4F60\u7684\u901A\u7528\u77E5\u8B58\u56DE\u7B54\u3002`;
    console.log(`[Worker Deepseek DEBUG] AutoRAG failed with error: ${autoRagError}`);
  } else {
    finalSystemPrompt += `

1. **\u7BC0\u76EE\u6458\u8981\u8CC7\u6599\u5EAB\u4E2D\u672A\u627E\u5230\u76F8\u95DC\u8CC7\u8A0A\u3002** \u8ACB\u4E3B\u8981\u6839\u64DA\u4EE5\u4E0B\u7DB2\u8DEF\u641C\u5C0B\u7D50\u679C\u548C\u4F60\u7684\u901A\u7528\u77E5\u8B58\u56DE\u7B54\u3002`;
  }
  if (searchResults) {
    finalSystemPrompt += `

2. **\u7DB2\u8DEF\u641C\u5C0B\u7D50\u679C (\u7528\u65BC\u88DC\u5145\u6642\u4E8B\u3001\u901A\u7528\u77E5\u8B58\u6216\u7BC0\u76EE\u672A\u63D0\u53CA\u7684\u7D30\u7BC0)**:
---
${searchResults}
---`;
    addedInfo = true;
  } else {
    if (!autoRagAnswer) {
      finalSystemPrompt += `

2. **\u7DB2\u8DEF\u641C\u5C0B\u4E5F\u672A\u57F7\u884C\u6216\u672A\u627E\u5230\u7D50\u679C\u3002**`;
    }
  }
  if (addedInfo) {
    finalSystemPrompt += "\n\n\u8ACB\u7528\u81EA\u7136\u3001\u53E3\u8A9E\u5316\u7684\u65B9\u5F0F\u7D9C\u5408\u4EE5\u4E0A\u8CC7\u8A0A\uFF0C\u63D0\u4F9B\u4E00\u500B\u5B8C\u6574\u4E14\u6709\u8DA3\u7684\u56DE\u7B54\u3002";
    if (autoRagAnswer && searchResults) {
      finalSystemPrompt += "\u5982\u679C\u7BC0\u76EE\u6458\u8981\u548C\u7DB2\u8DEF\u641C\u5C0B\u7D50\u679C\u6709\u885D\u7A81\uFF0C\u8ACB\u512A\u5148\u63A1\u4FE1\u7BC0\u76EE\u6458\u8981\u7684\u5167\u5BB9\uFF0C\u6216\u5A49\u8F49\u6307\u51FA\u53EF\u80FD\u7684\u5DEE\u7570\u3002";
    } else if (autoRagAnswer) {
      finalSystemPrompt += "\u8ACB\u76E1\u53EF\u80FD\u4FDD\u7559\u5982 '(\u51FA\u81EA S3EPXX)' \u7684\u4F86\u6E90\u6A19\u8A3B\u3002";
    }
  } else {
    finalSystemPrompt += "\n\n\u8ACB\u6839\u64DA\u4F60\u7684\u901A\u7528\u77E5\u8B58\u56DE\u7B54\u3002";
    if (autoRagError) {
    }
  }
  let messagesForDeepseek = [{ role: "system", content: finalSystemPrompt }];
  messagesForDeepseek = messagesForDeepseek.concat(messages);
  console.log("[Worker Deepseek DEBUG] Final system prompt for Deepseek:", finalSystemPrompt);
  console.log("[Worker Deepseek DEBUG] Message history being sent (excluding new system prompt):", JSON.stringify(messages, null, 2));
  const payload = {
    model: "deepseek-chat",
    messages: messagesForDeepseek,
    stream: false
  };
  const response = await fetch(DEEPSEEK_API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${apiKey}`
    },
    body: JSON.stringify(payload)
  });
  console.log(`[Worker Deepseek] Received response status from Deepseek: ${response.status}`);
  if (!response.ok) {
    let errorBody = "(Failed to read Deepseek error body)";
    try {
      errorBody = await response.text();
    } catch (e) {
    }
    console.error(`[Worker Deepseek] Deepseek API Error: ${response.status}. Body: ${errorBody}`);
    throw new Error(`Deepseek request failed with status ${response.status}: ${errorBody}`);
  }
  const result = await response.json();
  console.log("[Worker Deepseek DEBUG] Parsed Deepseek JSON result:", JSON.stringify(result).substring(0, 500) + "...");
  if (result.choices && result.choices[0] && result.choices[0].message && result.choices[0].message.content) {
    return result.choices[0].message.content;
  } else {
    console.warn("[Worker Deepseek DEBUG] Could not find expected content in Deepseek JSON response.");
    throw new Error("Deepseek response structure unexpected, could not extract answer.");
  }
}
__name(callDeepseek, "callDeepseek");
__name2(callDeepseek, "callDeepseek");
async function handleChatRequest(request, env) {
  console.log("[Worker Request] Entering handleChatRequest...");
  let requestBody;
  try {
    requestBody = await request.json();
    console.log("[Worker Request DEBUG] Parsed request body.");
  } catch (e) {
    console.error("[Worker Request] Invalid JSON in request body:", e);
    return new Response(JSON.stringify({ error: "\u65E0\u6548\u7684 JSON \u8BF7\u6C42\u4F53" }), { status: 400, headers: { "Content-Type": "application/json" } });
  }
  const messages = requestBody.messages;
  const mode = requestBody.mode || "autorag";
  console.log(`[Worker Request] Received mode: ${mode}`);
  if (!messages || !Array.isArray(messages) || messages.length === 0) {
    console.error("[Worker Request] Invalid or missing 'messages' in request body.");
    return new Response(JSON.stringify({ error: "\u8BF7\u6C42\u4F53\u4E2D\u7F3A\u5C11\u6709\u6548\u7684 'messages' \u5B57\u6BB5" }), { status: 400, headers: { "Content-Type": "application/json" } });
  }
  const lastUserMessage = messages.findLast((msg) => msg.role === "user");
  if (!lastUserMessage || !lastUserMessage.content) {
    console.error("[Worker Request] No user message found in history.");
    return new Response(JSON.stringify({ error: "\u804A\u5929\u6B77\u53F2\u4E2D\u627E\u4E0D\u5230\u4F7F\u7528\u8005\u8A0A\u606F" }), { status: 400, headers: { "Content-Type": "application/json" } });
  }
  const userQuery = lastUserMessage.content;
  console.log(`[Worker Request DEBUG] Extracted user query: "${userQuery}"`);
  const { AUTORAG_ENDPOINT, AUTORAG_API_TOKEN, DEEPSEEK_API_KEY, SERPER_API_KEY } = env;
  console.log(`[Worker ENV DEBUG] AUTORAG_ENDPOINT: ${AUTORAG_ENDPOINT ? "Loaded" : "MISSING!"}`);
  console.log(`[Worker ENV DEBUG] AUTORAG_API_TOKEN: ${AUTORAG_API_TOKEN ? "Loaded" : "MISSING!"}`);
  console.log(`[Worker ENV DEBUG] DEEPSEEK_API_KEY: ${DEEPSEEK_API_KEY ? "Loaded" : "MISSING!"}`);
  console.log(`[Worker ENV DEBUG] SERPER_API_KEY: ${SERPER_API_KEY ? "Loaded" : "MISSING!"}`);
  if (!AUTORAG_ENDPOINT || !AUTORAG_API_TOKEN) {
    console.error("[Worker ENV] AutoRAG environment variables missing.");
    return new Response(JSON.stringify({ error: "\u5F8C\u7AEF AutoRAG \u8A2D\u5B9A\u672A\u5B8C\u6210" }), { status: 500, headers: { "Content-Type": "application/json" } });
  }
  const conversationHistory = messages.filter((msg) => msg.role !== "system");
  try {
    if (mode === "hybrid") {
      console.log("[Worker Logic] Entering Hybrid Mode (AutoRAG -> Serper -> Deepseek)...");
      if (!DEEPSEEK_API_KEY) {
        console.error("[Worker ENV] DEEPSEEK_API_KEY is missing for Hybrid mode.");
        return new Response(JSON.stringify({ error: "\u5F8C\u7AEF Deepseek API \u91D1\u9470\u672A\u8A2D\u5B9A" }), { status: 500, headers: { "Content-Type": "application/json" } });
      }
      let serperKeyAvailable = true;
      if (!SERPER_API_KEY) {
        console.error("[Worker ENV] SERPER_API_KEY is missing for Hybrid mode web search.");
        console.warn("[Worker Logic] SERPER_API_KEY missing, proceeding without web search.");
        serperKeyAvailable = false;
      }
      let autoRagAnswer = null;
      let autoRagError = null;
      console.log("[Worker Logic] Step 1: Calling AutoRAG ai-search...");
      try {
        autoRagAnswer = await callAutoRag(AUTORAG_ENDPOINT, AUTORAG_API_TOKEN, userQuery);
        if (autoRagAnswer === null) {
          console.warn("[Worker Logic] AutoRAG did not return a valid answer (returned null). Continuing...");
        }
      } catch (e) {
        console.error("[Worker Logic] AutoRAG call failed:", e.message);
        autoRagError = e.message;
        autoRagAnswer = null;
      }
      let searchResults = null;
      if (serperKeyAvailable) {
        console.log("[Worker Logic] Step 2: Calling Serper Web Search...");
        searchResults = await callSerperSearch(SERPER_API_KEY, userQuery);
        if (searchResults === null) {
          console.warn("[Worker Logic] Web search failed or returned no results.");
        }
      } else {
        console.log("[Worker Logic] Step 2: Skipping web search (SERPER_API_KEY not found).");
      }
      console.log("[Worker Logic] Step 3: Calling Deepseek for synthesis...");
      const deepseekFinalAnswer = await callDeepseek(DEEPSEEK_API_KEY, [...conversationHistory], autoRagAnswer, searchResults, autoRagError);
      console.log(`[Worker Logic DEBUG] Extracted Deepseek final answer (Hybrid Mode, length: ${deepseekFinalAnswer.length})`);
      const formattedResponse = formatResponse(deepseekFinalAnswer);
      console.log("[Worker Logic DEBUG] Sending formatted Deepseek response to client (Hybrid Mode).");
      return new Response(JSON.stringify(formattedResponse), { status: 200, headers: { "Content-Type": "application/json" } });
    } else {
      console.log("[Worker Logic] Entering AutoRAG Mode (default)...");
      const autoRagAnswer = await callAutoRag(AUTORAG_ENDPOINT, AUTORAG_API_TOKEN, userQuery);
      if (autoRagAnswer === null) {
        console.error("[Worker Logic] AutoRAG failed to provide an answer in AutoRAG mode.");
        return new Response(JSON.stringify({ error: "\u7121\u6CD5\u5F9E AutoRAG \u7372\u53D6\u56DE\u7B54", detail: "Response structure might be incorrect or API failed." }), { status: 500, headers: { "Content-Type": "application/json" } });
      }
      const formattedResponse = formatResponse(autoRagAnswer);
      console.log("[Worker Logic DEBUG] Sending formatted AutoRAG response to client (AutoRAG Mode).");
      return new Response(JSON.stringify(formattedResponse), { status: 200, headers: { "Content-Type": "application/json" } });
    }
  } catch (e) {
    console.error("[Worker Logic] FATAL Error during processing:", e);
    if (e.stack) console.error("[Worker Logic DEBUG] Error Stack:", e.stack);
    const errorMsg = "\u8655\u7406\u8ACB\u6C42\u6642\u767C\u751F\u5167\u90E8\u932F\u8AA4 (Worker)";
    const errorDetail = e.message || "Unknown error";
    return new Response(JSON.stringify({ error: errorMsg, detail: errorDetail }), { status: 500, headers: { "Content-Type": "application/json" } });
  }
}
__name(handleChatRequest, "handleChatRequest");
__name2(handleChatRequest, "handleChatRequest");
var worker_default = {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const pathname = url.pathname;
    const method = request.method;
    console.log(`[Worker Entry] Request: ${method} ${pathname}`);
    if (pathname === "/api/chat" && method === "POST") {
      return handleChatRequest(request, env);
    }
    if (method === "GET") {
      try {
        if (!env.ASSETS) {
          console.error("[Worker Static] env.ASSETS is not defined.");
          return new Response("\u975C\u614B\u8CC7\u6E90\u670D\u52D9\u672A\u914D\u7F6E", { status: 500 });
        }
        return await env.ASSETS.fetch(request);
      } catch (e) {
        if (pathname === "/" || pathname === "/index.html") {
          console.error(`[Worker Static] Critical asset not found: ${pathname}`, e.message);
          return new Response("\u627E\u4E0D\u5230\u4E3B\u8981\u9801\u9762 (index.html)", { status: 404 });
        } else {
          return new Response("\u8CC7\u6E90\u672A\u627E\u5230 (Not Found)", { status: 404 });
        }
      }
    }
    console.warn(`[Worker Entry] Method ${method} not allowed for path '${pathname}'.`);
    return new Response("\u65B9\u6CD5\u4E0D\u5141\u8A31 (Method Not Allowed)", { status: 405 });
  }
};
var drainBody = /* @__PURE__ */ __name2(async (request, env, _ctx, middlewareCtx) => {
  try {
    return await middlewareCtx.next(request, env);
  } finally {
    try {
      if (request.body !== null && !request.bodyUsed) {
        const reader = request.body.getReader();
        while (!(await reader.read()).done) {
        }
      }
    } catch (e) {
      console.error("Failed to drain the unused request body.", e);
    }
  }
}, "drainBody");
var middleware_ensure_req_body_drained_default = drainBody;
function reduceError(e) {
  return {
    name: e?.name,
    message: e?.message ?? String(e),
    stack: e?.stack,
    cause: e?.cause === void 0 ? void 0 : reduceError(e.cause)
  };
}
__name(reduceError, "reduceError");
__name2(reduceError, "reduceError");
var jsonError = /* @__PURE__ */ __name2(async (request, env, _ctx, middlewareCtx) => {
  try {
    return await middlewareCtx.next(request, env);
  } catch (e) {
    const error = reduceError(e);
    return Response.json(error, {
      status: 500,
      headers: { "MF-Experimental-Error-Stack": "true" }
    });
  }
}, "jsonError");
var middleware_miniflare3_json_error_default = jsonError;
var __INTERNAL_WRANGLER_MIDDLEWARE__ = [
  middleware_ensure_req_body_drained_default,
  middleware_miniflare3_json_error_default
];
var middleware_insertion_facade_default = worker_default;
var __facade_middleware__ = [];
function __facade_register__(...args) {
  __facade_middleware__.push(...args.flat());
}
__name(__facade_register__, "__facade_register__");
__name2(__facade_register__, "__facade_register__");
function __facade_invokeChain__(request, env, ctx, dispatch, middlewareChain) {
  const [head, ...tail] = middlewareChain;
  const middlewareCtx = {
    dispatch,
    next(newRequest, newEnv) {
      return __facade_invokeChain__(newRequest, newEnv, ctx, dispatch, tail);
    }
  };
  return head(request, env, ctx, middlewareCtx);
}
__name(__facade_invokeChain__, "__facade_invokeChain__");
__name2(__facade_invokeChain__, "__facade_invokeChain__");
function __facade_invoke__(request, env, ctx, dispatch, finalMiddleware) {
  return __facade_invokeChain__(request, env, ctx, dispatch, [
    ...__facade_middleware__,
    finalMiddleware
  ]);
}
__name(__facade_invoke__, "__facade_invoke__");
__name2(__facade_invoke__, "__facade_invoke__");
var __Facade_ScheduledController__ = class ___Facade_ScheduledController__ {
  static {
    __name(this, "___Facade_ScheduledController__");
  }
  constructor(scheduledTime, cron, noRetry) {
    this.scheduledTime = scheduledTime;
    this.cron = cron;
    this.#noRetry = noRetry;
  }
  static {
    __name2(this, "__Facade_ScheduledController__");
  }
  #noRetry;
  noRetry() {
    if (!(this instanceof ___Facade_ScheduledController__)) {
      throw new TypeError("Illegal invocation");
    }
    this.#noRetry();
  }
};
function wrapExportedHandler(worker) {
  if (__INTERNAL_WRANGLER_MIDDLEWARE__ === void 0 || __INTERNAL_WRANGLER_MIDDLEWARE__.length === 0) {
    return worker;
  }
  for (const middleware of __INTERNAL_WRANGLER_MIDDLEWARE__) {
    __facade_register__(middleware);
  }
  const fetchDispatcher = /* @__PURE__ */ __name2(function(request, env, ctx) {
    if (worker.fetch === void 0) {
      throw new Error("Handler does not export a fetch() function.");
    }
    return worker.fetch(request, env, ctx);
  }, "fetchDispatcher");
  return {
    ...worker,
    fetch(request, env, ctx) {
      const dispatcher = /* @__PURE__ */ __name2(function(type, init) {
        if (type === "scheduled" && worker.scheduled !== void 0) {
          const controller = new __Facade_ScheduledController__(
            Date.now(),
            init.cron ?? "",
            () => {
            }
          );
          return worker.scheduled(controller, env, ctx);
        }
      }, "dispatcher");
      return __facade_invoke__(request, env, ctx, dispatcher, fetchDispatcher);
    }
  };
}
__name(wrapExportedHandler, "wrapExportedHandler");
__name2(wrapExportedHandler, "wrapExportedHandler");
function wrapWorkerEntrypoint(klass) {
  if (__INTERNAL_WRANGLER_MIDDLEWARE__ === void 0 || __INTERNAL_WRANGLER_MIDDLEWARE__.length === 0) {
    return klass;
  }
  for (const middleware of __INTERNAL_WRANGLER_MIDDLEWARE__) {
    __facade_register__(middleware);
  }
  return class extends klass {
    #fetchDispatcher = /* @__PURE__ */ __name2((request, env, ctx) => {
      this.env = env;
      this.ctx = ctx;
      if (super.fetch === void 0) {
        throw new Error("Entrypoint class does not define a fetch() function.");
      }
      return super.fetch(request);
    }, "#fetchDispatcher");
    #dispatcher = /* @__PURE__ */ __name2((type, init) => {
      if (type === "scheduled" && super.scheduled !== void 0) {
        const controller = new __Facade_ScheduledController__(
          Date.now(),
          init.cron ?? "",
          () => {
          }
        );
        return super.scheduled(controller);
      }
    }, "#dispatcher");
    fetch(request) {
      return __facade_invoke__(
        request,
        this.env,
        this.ctx,
        this.#dispatcher,
        this.#fetchDispatcher
      );
    }
  };
}
__name(wrapWorkerEntrypoint, "wrapWorkerEntrypoint");
__name2(wrapWorkerEntrypoint, "wrapWorkerEntrypoint");
var WRAPPED_ENTRY;
if (typeof middleware_insertion_facade_default === "object") {
  WRAPPED_ENTRY = wrapExportedHandler(middleware_insertion_facade_default);
} else if (typeof middleware_insertion_facade_default === "function") {
  WRAPPED_ENTRY = wrapWorkerEntrypoint(middleware_insertion_facade_default);
}
var middleware_loader_entry_default = WRAPPED_ENTRY;

// C:/Users/PONY/AppData/Roaming/npm/node_modules/wrangler/templates/middleware/middleware-ensure-req-body-drained.ts
var drainBody2 = /* @__PURE__ */ __name(async (request, env, _ctx, middlewareCtx) => {
  try {
    return await middlewareCtx.next(request, env);
  } finally {
    try {
      if (request.body !== null && !request.bodyUsed) {
        const reader = request.body.getReader();
        while (!(await reader.read()).done) {
        }
      }
    } catch (e) {
      console.error("Failed to drain the unused request body.", e);
    }
  }
}, "drainBody");
var middleware_ensure_req_body_drained_default2 = drainBody2;

// C:/Users/PONY/AppData/Roaming/npm/node_modules/wrangler/templates/middleware/middleware-miniflare3-json-error.ts
function reduceError2(e) {
  return {
    name: e?.name,
    message: e?.message ?? String(e),
    stack: e?.stack,
    cause: e?.cause === void 0 ? void 0 : reduceError2(e.cause)
  };
}
__name(reduceError2, "reduceError");
var jsonError2 = /* @__PURE__ */ __name(async (request, env, _ctx, middlewareCtx) => {
  try {
    return await middlewareCtx.next(request, env);
  } catch (e) {
    const error = reduceError2(e);
    return Response.json(error, {
      status: 500,
      headers: { "MF-Experimental-Error-Stack": "true" }
    });
  }
}, "jsonError");
var middleware_miniflare3_json_error_default2 = jsonError2;

// .wrangler/tmp/bundle-itZTqT/middleware-insertion-facade.js
var __INTERNAL_WRANGLER_MIDDLEWARE__2 = [
  middleware_ensure_req_body_drained_default2,
  middleware_miniflare3_json_error_default2
];
var middleware_insertion_facade_default2 = middleware_loader_entry_default;

// C:/Users/PONY/AppData/Roaming/npm/node_modules/wrangler/templates/middleware/common.ts
var __facade_middleware__2 = [];
function __facade_register__2(...args) {
  __facade_middleware__2.push(...args.flat());
}
__name(__facade_register__2, "__facade_register__");
function __facade_invokeChain__2(request, env, ctx, dispatch, middlewareChain) {
  const [head, ...tail] = middlewareChain;
  const middlewareCtx = {
    dispatch,
    next(newRequest, newEnv) {
      return __facade_invokeChain__2(newRequest, newEnv, ctx, dispatch, tail);
    }
  };
  return head(request, env, ctx, middlewareCtx);
}
__name(__facade_invokeChain__2, "__facade_invokeChain__");
function __facade_invoke__2(request, env, ctx, dispatch, finalMiddleware) {
  return __facade_invokeChain__2(request, env, ctx, dispatch, [
    ...__facade_middleware__2,
    finalMiddleware
  ]);
}
__name(__facade_invoke__2, "__facade_invoke__");

// .wrangler/tmp/bundle-itZTqT/middleware-loader.entry.ts
var __Facade_ScheduledController__2 = class ___Facade_ScheduledController__2 {
  constructor(scheduledTime, cron, noRetry) {
    this.scheduledTime = scheduledTime;
    this.cron = cron;
    this.#noRetry = noRetry;
  }
  static {
    __name(this, "__Facade_ScheduledController__");
  }
  #noRetry;
  noRetry() {
    if (!(this instanceof ___Facade_ScheduledController__2)) {
      throw new TypeError("Illegal invocation");
    }
    this.#noRetry();
  }
};
function wrapExportedHandler2(worker) {
  if (__INTERNAL_WRANGLER_MIDDLEWARE__2 === void 0 || __INTERNAL_WRANGLER_MIDDLEWARE__2.length === 0) {
    return worker;
  }
  for (const middleware of __INTERNAL_WRANGLER_MIDDLEWARE__2) {
    __facade_register__2(middleware);
  }
  const fetchDispatcher = /* @__PURE__ */ __name(function(request, env, ctx) {
    if (worker.fetch === void 0) {
      throw new Error("Handler does not export a fetch() function.");
    }
    return worker.fetch(request, env, ctx);
  }, "fetchDispatcher");
  return {
    ...worker,
    fetch(request, env, ctx) {
      const dispatcher = /* @__PURE__ */ __name(function(type, init) {
        if (type === "scheduled" && worker.scheduled !== void 0) {
          const controller = new __Facade_ScheduledController__2(
            Date.now(),
            init.cron ?? "",
            () => {
            }
          );
          return worker.scheduled(controller, env, ctx);
        }
      }, "dispatcher");
      return __facade_invoke__2(request, env, ctx, dispatcher, fetchDispatcher);
    }
  };
}
__name(wrapExportedHandler2, "wrapExportedHandler");
function wrapWorkerEntrypoint2(klass) {
  if (__INTERNAL_WRANGLER_MIDDLEWARE__2 === void 0 || __INTERNAL_WRANGLER_MIDDLEWARE__2.length === 0) {
    return klass;
  }
  for (const middleware of __INTERNAL_WRANGLER_MIDDLEWARE__2) {
    __facade_register__2(middleware);
  }
  return class extends klass {
    #fetchDispatcher = /* @__PURE__ */ __name((request, env, ctx) => {
      this.env = env;
      this.ctx = ctx;
      if (super.fetch === void 0) {
        throw new Error("Entrypoint class does not define a fetch() function.");
      }
      return super.fetch(request);
    }, "#fetchDispatcher");
    #dispatcher = /* @__PURE__ */ __name((type, init) => {
      if (type === "scheduled" && super.scheduled !== void 0) {
        const controller = new __Facade_ScheduledController__2(
          Date.now(),
          init.cron ?? "",
          () => {
          }
        );
        return super.scheduled(controller);
      }
    }, "#dispatcher");
    fetch(request) {
      return __facade_invoke__2(
        request,
        this.env,
        this.ctx,
        this.#dispatcher,
        this.#fetchDispatcher
      );
    }
  };
}
__name(wrapWorkerEntrypoint2, "wrapWorkerEntrypoint");
var WRAPPED_ENTRY2;
if (typeof middleware_insertion_facade_default2 === "object") {
  WRAPPED_ENTRY2 = wrapExportedHandler2(middleware_insertion_facade_default2);
} else if (typeof middleware_insertion_facade_default2 === "function") {
  WRAPPED_ENTRY2 = wrapWorkerEntrypoint2(middleware_insertion_facade_default2);
}
var middleware_loader_entry_default2 = WRAPPED_ENTRY2;
export {
  __INTERNAL_WRANGLER_MIDDLEWARE__2 as __INTERNAL_WRANGLER_MIDDLEWARE__,
  middleware_loader_entry_default2 as default
};
//# sourceMappingURL=bundledWorker-0.8900617486080447.js.map
