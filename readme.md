# 肥宅老司機 AI 聊天機器人

## 項目概述

肥宅老司機 AI 聊天機器人是一個基於 DeepSeek 大型語言模型的聊天應用，部署在 Cloudflare Pages 上。此應用旨在為「肥宅老司機」Podcast 的聽眾提供一個互動界面，並計劃整合節目內容摘要以實現 RAG (Retrieval-Augmented Generation) 功能。

## 當前狀態 (Cloudflare Pages)

- **前端**: `index.html` (位於專案根目錄)，包含 HTML, CSS, 和 JavaScript 用於聊天界面。
- **後端**: `_worker.js` (使用 Cloudflare Pages Advanced Mode)，處理 API 路由 (`/api/chat`) 和靜態文件服務。
- **AI 模型**: DeepSeek (`deepseek-chat` 模型)，通過後端 Worker 調用其 API。
- **運行環境**: Cloudflare Pages (使用 `_worker.js` 進階模式)。
- **部署**: 自動從 GitHub (`master` 分支) 部署。
- **核心功能**: 基本聊天功能已可正常運作。

## RAG 整合計劃

- **目標**: 利用 `S3EP201_204/podcast_summaries_merged.txt` 中的節目摘要，讓 AI 能夠回答關於特定節目內容的問題。
- **向量數據庫**: **Cloudflare Vectorize** (推薦方案)。利用其與 Workers 的原生整合和 Serverless 特性。
- **Embedding 模型**: **Cloudflare Workers AI** (例如 `baai/bge-base-en-v1.5` 或其他適合中文的模型)。在 Worker 中直接調用生成向量。
- **流程**: 
    1. 預處理 `podcast_summaries_merged.txt`。
    2. 使用 Workers AI Embedding 模型將摘要文本轉換為向量。
    3. 將文本及其向量儲存到 Cloudflare Vectorize。
    4. 在 `_worker.js` 中：
        a. 接收用戶問題。
        b. 將問題轉換為向量。
        c. 在 Vectorize 中進行相似性搜索，找出最相關的節目摘要。
        d. 將相關摘要內容與原始問題一起組合進 Prompt。
        e. 將組合後的 Prompt 發送給 DeepSeek API。
        f. 將 DeepSeek 的回答返回給前端。

## 開發歷程中的主要挑戰與解決方案

- **環境遷移**: 從 Vercel/Python 遷移至 Cloudflare。
- **部署錯誤**: 經歷了 `functions` 目錄衝突、`.venv` 符號連結、405 Method Not Allowed、422 Unprocessable Content 等錯誤。
- **路由/靜態文件問題**: Cloudflare Pages 的「建置輸出目錄」設定與 `_worker.js` 進階模式路由的交互問題導致前端文件版本不一致或路由失敗。
- **最終解決方案**: 
    - 使用 `_worker.js` 進階模式。
    - 將 `index.html` 移至專案根目錄。
    - 將 Cloudflare Pages 的「建置輸出目錄」設定為 `.` (或 `/`)。
    - 確保 `_worker.js` 正確處理 API 路由和靜態文件 fallback。

## 如何在本地運行 (使用 Wrangler)

1.  確保已安裝 Node.js 和 npm/yarn/pnpm。
2.  安裝 Wrangler CLI: `npm install -g wrangler`
3.  克隆倉庫並進入專案目錄。
4.  (可選) 創建 `.dev.vars` 文件並在其中設定 `DEEPSEEK_API_KEY = "YOUR_API_KEY"` 以供本地開發使用 (注意不要提交此文件到 Git)。或者，運行時通過環境變數傳遞。
5.  運行本地開發伺服器: `wrangler pages dev . --kv=YOUR_KV_BINDING_IF_ANY --vectorize=YOUR_VECTORIZE_BINDING_IF_ANY --ai=YOUR_AI_BINDING_IF_ANY --var DEEPSEEK_API_KEY:YOUR_API_KEY` (根據需要添加綁定和變數)。如果沒有綁定，可以直接運行 `wrangler pages dev . --var DEEPSEEK_API_KEY:YOUR_API_KEY`。
6.  在瀏覽器中訪問 `http://localhost:8788` (或 Wrangler 顯示的其他端口)。

## 密鑰管理

- **生產環境**: `DEEPSEEK_API_KEY` 應在 Cloudflare Pages 專案的「設定」->「環境變數」中配置。 