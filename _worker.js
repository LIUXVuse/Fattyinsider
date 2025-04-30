// _worker.js
export default {
    async fetch(request, env, ctx) {
      const url = new URL(request.url);
      const pathname = url.pathname;
      const method = request.method;
  
      console.log(`[JS WORKER DEBUG] Method=${method}, Path=${pathname}`);
  
      // API 路由: 處理對 /api/chat 的 POST 請求
      if (pathname === "/api/chat" && method === "POST") {
        console.log("[JS WORKER DEBUG] Handling /api/chat POST...");
        const responseData = { message: "POST /api/chat handled by JS worker!" };
        const headers = new Headers({
          "Content-Type": "application/json",
        });
        try {
          return new Response(JSON.stringify(responseData), { status: 200, headers });
        } catch (e) {
          console.error("Error creating POST response:", e);
          return new Response("Error creating POST response", { status: 500 });
        }
      }
  
      // 靜態檔案路由: 對於所有其他請求，嘗試從 ASSETS 提供服務
      console.log(`[JS WORKER DEBUG] Path '${pathname}' not API route, attempting static asset...`);
      try {
        return await env.ASSETS.fetch(request);
      } catch (e) {
        console.error(`[JS WORKER DEBUG] Error fetching static asset for path '${pathname}':`, e);
        return new Response("資源未找到 (Not Found)", { status: 404 });
      }
    },
  };