# 肥宅老司機 AI 聊天機器人

## 項目概述

肥宅老司機 AI 聊天機器人是一個聊天應用，旨在為「肥宅老司機」Podcast 的聽眾提供一個互動界面。此應用利用 **Cloudflare AutoRAG** 整合節目內容摘要，並可選用 **Serper.dev** 進行網路搜尋，或直接使用 **Deepseek API** 進行通用 AI 回應。應用程式透過 **Cloudflare Pages** 部署。

*最後更新時間: 2025/05/01*

## 當前狀態 (Cloudflare Pages + AutoRAG + Serper + Deepseek)

- **前端**: `index.html` (位於專案根目錄)，包含 HTML, CSS, 和 JavaScript。特色：
    - 暗黑主題的左右分欄介面 (左側資訊/Logo，右側聊天)。
    - 載入時有年齡確認彈窗。
    - 提供模式切換選項 (單選按鈕) 可選擇「純情 RAG (預設)」、「混和動力」或「通用模式 (Deepseek)」。
    - 支援 Shift+Enter 換行。
- **後端 (請求處理)**: `_worker.js` (使用 Cloudflare Pages Advanced Mode) 處理 `/api/chat` 請求，根據前端選擇的模式 (`autorag`, `hybrid`, `deepseek`) 執行不同邏輯：
    - 提供靜態前端文件 (`index.html` 等)。
    - **AutoRAG 模式 (預設)**:
        1. 呼叫 **Cloudflare AutoRAG** 的 `/ai-search` 端點，傳遞使用者查詢。
        2. 將 AutoRAG (內建 LLM) 生成的回應直接回傳給前端。
    - **混合模式 (Hybrid Mode)**:
        1. **(嘗試)** 呼叫 **Cloudflare AutoRAG** 的 `/ai-search` 端點獲取基於節目摘要的回答。會捕捉執行錯誤 (例如 Token 限制)。
        2. **(如果 `SERPER_API_KEY` 存在)** 呼叫 **Serper.dev API** 進行網路搜尋。
        3. 將使用者原始問題、AutoRAG 的回答 (或錯誤訊息)、網路搜尋結果 (如果有的話) 傳遞給 **Deepseek API** (`deepseek-chat` 模型) 進行最終的整合與潤飾。
        4. 將 Deepseek 的回應回傳給前端。
    - **通用模式 (Deepseek Mode)**:
        1. **(如果 `DEEPSEEK_API_KEY` 存在)** 直接呼叫 **Deepseek API** (`deepseek-chat` 模型)，使用通用型系統提示 (包含翻譯時提供原文對照的指示)。
        2. 將 Deepseek 的回應回傳給前端。
- **後端 (資料處理 & AI 模型)**:
    - **Cloudflare AutoRAG**: 持續從 R2 儲存桶 (`fattyinsider`) 同步、處理 `.md` 檔案，管理 Vectorize 索引，並透過 `/ai-search` 提供 RAG 生成服務。
    - **Serper.dev**: 提供即時網路搜尋結果。
    - **Deepseek**: 提供整合 RAG/搜尋結果或獨立的通用語言生成能力。
- **主要資料來源**: 存放在 Cloudflare R2 儲存桶 (`fattyinsider`) 中的 Markdown 格式節目摘要 (用於 RAG 和混合模式)。
- **運行環境**: Cloudflare Pages (使用 `_worker.js` 進階模式), Cloudflare AutoRAG, (外部) Serper.dev API, (外部) Deepseek API。
- **部署**: 自動從 GitHub (`master` 分支) 部署至 Cloudflare Pages。
- **核心功能**: 提供三種模式的聊天：
    1. **純情 RAG**: 快速、基於節目摘要的回應 (AutoRAG)。
    2. **混和動力**: 結合節目摘要、網路搜尋的全面回應 (AutoRAG + Serper + Deepseek)，包含 RAG 錯誤處理。
    3. **通用模式**: 直接使用 Deepseek 進行翻譯、寫作等通用任務。

## 重要設定與流程

### AutoRAG 整合流程 (用於 RAG 與混合模式)

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
    - `DEEPSEEK_API_KEY`: (混合模式**及通用模式**需要) 你的 Deepseek API 金鑰 (設為 Secret)。
    - `SERPER_API_KEY`: (混合模式需要) 你的 Serper.dev API 金鑰 (設為 Secret)。

### Worker (`_worker.js`) 邏輯

- **環境遷移**: 從 Vercel/Python 遷移至 Cloudflare。
- **部署錯誤**: 經歷了 `functions` 目錄衝突、`.venv` 符號連結、405 Method Not Allowed、422 Unprocessable Content 等錯誤。
- **路由/靜態文件問題**: Cloudflare Pages 的「建置輸出目錄」設定與 `_worker.js` 進階模式路由的交互問題。
- **AutoRAG API 理解與錯誤處理**: 釐清 `/search` 與 `/ai-search` 端點的差異，處理 `/search` 回應格式不符預期的問題，處理 `/ai-search` 可能的 Token 限制錯誤 (500 Internal Server Error)。
- **混合模式邏輯**: 設計並實現 AutoRAG -> Serper -> Deepseek 的流程，包含錯誤處理和提示工程。
- **UI/UX 改進**: 從基本聊天介面改為暗黑主題的左右分欄佈局，並加入年齡確認。
- **最終解決方案**: 
    - 使用 `_worker.js` 進階模式，`index.html` 放在根目錄，建置目錄設為 `.`。
    - 實現 `autorag` 和 `hybrid` 兩種模式，後者包含 Serper 和 Deepseek 整合及 AutoRAG 錯誤處理。
    - 透過 CSS 和 JavaScript 改善前端介面。

## 如何在本地運行 (使用 Wrangler)

1.  確保已安裝 Node.js 和 npm/yarn/pnpm。
2.  安裝 Wrangler CLI: `npm install -g wrangler`
3.  克隆倉庫並進入專案目錄。
4.  創建 `.dev.vars` 文件 (此文件不應提交到 Git)，並在其中設定 AutoRAG 的環境變數：
    ```
    AUTORAG_ENDPOINT="YOUR_AUTORAG_API_ENDPOINT_URL"
    AUTORAG_API_TOKEN="YOUR_SERVICE_API_TOKEN_VALUE"
    DEEPSEEK_API_KEY="YOUR_DEEPSEEK_API_KEY"
    SERPER_API_KEY="YOUR_SERPER_API_KEY"
    ```
    (將引號內的內容替換為實際值)。
5.  運行本地開發伺服器: `wrangler pages dev .`
6.  在瀏覽器中訪問 `http://localhost:8788` (或 Wrangler 顯示的其他端口)。

## 密鑰管理

- **生產環境**: `AUTORAG_ENDPOINT`, `AUTORAG_API_TOKEN`, `DEEPSEEK_API_KEY`, 和 `SERPER_API_KEY` **必須**在 Cloudflare Pages 專案的「設定」->「環境變數」中配置。API Token 和 Key 應標記為 **Secret**。
- **本地開發**: 使用 `.dev.vars` 文件管理本地測試所需的密鑰。

## 未來展望

- **會員/訂閱制**: 由於混合模式會消耗 AutoRAG、Serper.dev 和 Deepseek 的 API 額度，未來可能考慮引入會員或訂閱機制，以分攤 API 成本，確保服務的持續運營。
- **功能優化**: 持續觀察各 API 的穩定性和回應品質，調整提示工程或錯誤處理邏輯。
- **RAG 資料更新**: 定期更新 R2 中的節目摘要，確保 AutoRAG 能提供最新的節目資訊。 