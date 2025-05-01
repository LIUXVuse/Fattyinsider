# 肥宅老司機 AI 聊天機器人

## 項目概述

肥宅老司機 AI 聊天機器人是一個聊天應用，旨在為「肥宅老司機」Podcast 的聽眾提供一個互動界面。此應用利用 **Cloudflare AutoRAG** 整合節目內容摘要，以實現 RAG (Retrieval-Augmented Generation) 功能，並透過 **Cloudflare Pages** 部署。

*最後更新時間: 2025/05/01*

## 當前狀態 (Cloudflare Pages + AutoRAG)

- **前端**: `index.html` (位於專案根目錄)，包含 HTML, CSS, 和 JavaScript 用於聊天界面。
- **後端 (資料處理)**: **Cloudflare AutoRAG** 負責：
    - 從指定的 R2 儲存桶 (`fattyinsider`) 自動讀取、轉換、分塊和向量化 Markdown 文件。
    - 管理底層的 Vectorize 索引。
    - 提供 API 端點以接收查詢並返回結合了 RAG 結果的最終答案。
- **後端 (請求處理)**: `_worker.js` (使用 Cloudflare Pages Advanced Mode) 負責：
    - 提供靜態前端文件 (`index.html` 等)。
    - 接收前端 `/api/chat` 請求。
    - 將使用者查詢轉發給 **AutoRAG API 端點**。
    - 將 AutoRAG 回傳的答案格式化後回傳給前端。
- **資料來源**: 存放在 Cloudflare R2 儲存桶 (`fattyinsider`) 中的 Markdown 格式節目摘要。
- **運行環境**: Cloudflare Pages (使用 `_worker.js` 進階模式) + Cloudflare AutoRAG。
- **部署**: 自動從 GitHub (`master` 分支) 部署。
- **核心功能**: 預期實現基於節目摘要的 RAG 聊天功能。

## AutoRAG 整合流程

1.  **資料準備 (使用 `rename_txt_to_md.py`)**: 
    - 將新的節目摘要檔案 (假設是 `.txt` 格式) 放入指定的資料夾 (例如 `S3EP201_204/`)。
    - 執行 Python 腳本 `rename_txt_to_md.py` 將該資料夾內的所有 `.txt` 轉換為 `.md` 格式。在專案根目錄執行指令：
      ```bash
      python rename_txt_to_md.py <你的資料夾路徑>
      # 範例: python rename_txt_to_md.py S3EP201_204
      ```
2.  **上傳至 R2**: 將準備好的 `.md` 檔案上傳至 Cloudflare R2 儲存桶 (`fattyinsider`)。可以透過 Cloudflare 儀表板或 Wrangler CLI 上傳。
3.  **建立/同步 AutoRAG 實例**: 
    - (首次設定) 在 Cloudflare 儀表板建立 AutoRAG 實例，連接 `fattyinsider` R2 儲存桶，選擇模型，建立 AI Gateway 和 Service API Token。
    - (後續更新) 上傳新檔案到 R2 後，AutoRAG 會自動在數小時內同步並重新索引。若需立即生效，可以手動點擊 AutoRAG 頁面的「同步索引 (Sync Index)」按鈕。
4.  **設定環境變數**: 在 Cloudflare Pages 專案設定中，添加以下環境變數：
    - `AUTORAG_ENDPOINT`: AutoRAG 實例的 API 端點 URL。
    - `AUTORAG_API_TOKEN`: 建立的 Service API Token 的值 (設為 Secret)。
5.  **Worker (`_worker.js`) 邏輯**: `_worker.js` 接收前端請求，將使用者問題發送到 `AUTORAG_ENDPOINT` (使用 `AUTORAG_API_TOKEN` 認證)，並處理 AutoRAG 的回應。

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
4.  創建 `.dev.vars` 文件 (此文件不應提交到 Git)，並在其中設定 AutoRAG 的環境變數：
    ```
    AUTORAG_ENDPOINT="YOUR_AUTORAG_API_ENDPOINT_URL"
    AUTORAG_API_TOKEN="YOUR_SERVICE_API_TOKEN_VALUE"
    ```
    (將引號內的內容替換為實際值)。
5.  運行本地開發伺服器: `wrangler pages dev .`
6.  在瀏覽器中訪問 `http://localhost:8788` (或 Wrangler 顯示的其他端口)。

## 密鑰管理

- **生產環境**: `AUTORAG_ENDPOINT` 和 `AUTORAG_API_TOKEN` **必須**在 Cloudflare Pages 專案的「設定」->「環境變數」中配置。`AUTORAG_API_TOKEN` 應標記為 **Secret**。
- **本地開發**: 使用 `.dev.vars` 文件管理本地測試所需的密鑰。 