# 肥宅老司機 AI 聊天機器人

## 項目概述.

肥宅老司機 AI 聊天機器人是一個基於 DeepSeek 大型語言模型的聊天應用。該應用最初設計用於 Vercel 平台，因遇到執行時間限制和依賴安裝問題，現計劃遷移至 Cloudflare 平台。

## 技術架構 (目標 for Cloudflare)

- **前端**：HTML, CSS, JavaScript (嵌入在 Python 文件中)
- **後端**：Python (需要適配 Cloudflare Workers 運行環境)
- **AI 模型**：DeepSeek (`deepseek-chat` 模型)
- **運行環境**：Cloudflare Workers / Pages
- **向量數據庫**：計劃使用 ChromaDB (本地運行) 或 Cloudflare Vectorize
- **Embedding 模型**：計劃使用 `sentence-transformers` (本地運行，需確認 Workers 相容性)
- **依賴管理**：`requirements.txt` (需要根據 Workers 環境調整)
- **密鑰管理**：Cloudflare 環境變數 (包含 `DEEPSEEK_API_KEY`)

## 當前功能 (Devbox 基準)

- 基本的聊天界面
- 與 DeepSeek API (`deepseek-chat` 模型) 成功集成
- 消息歷史管理（保留最近的 10 條對話）
- AI 已配置為使用繁體中文回覆

## 開發進度與挑戰

1.  **環境遷移 (Vercel -> ClawCloud Devbox)**：已完成，但遇到持續的依賴安裝問題 (`pip` 解析衝突, `PyYAML` 編譯錯誤, `torch` 資源耗盡) 和部署問題 (`nodePort range is full`)。
2.  **API 連接**：成功連接 DeepSeek API，解決了 API Key、端點和模型名稱問題。
3.  **向量數據庫選型**：
    - 放棄 ClawCloud Milvus (潛在費用)。
    - 初步選定 ChromaDB + `sentence-transformers` (本地運行)。
    - DeepSeek 官方暫不提供 Embedding API。
4.  **決定再次遷移 (ClawCloud Devbox -> Cloudflare)**：由於 Devbox 環境不穩定，決定遷移到 Cloudflare。

## 下一步計劃 (Cloudflare 遷移)

1.  **清理專案**：移除 Vercel 和 Devbox Dockerfile，整理 `requirements.txt`。(進行中)
2.  **恢復核心代碼**：確保 `vercel_app.py` 的核心邏輯可用。(進行中)
3.  **更新 GitHub 倉庫**：將清理後的專案推送到 GitHub。(進行中)
4.  **適配 Cloudflare Workers**：
    - 修改 `vercel_app.py` 以符合 Workers 的事件處理模型 (可能使用 `itty-router-python`)。
    - 重新評估 `requirements.txt`，確保依賴與 Python Workers (Wasm) 環境兼容。
    - 研究在 Workers 中運行 `sentence-transformers` 的可行性，或尋找替代方案 (如 Cloudflare Vectorize + Workers AI Embedding)。
5.  **設定 Cloudflare Pages/Workers 部署**：連接 GitHub 倉庫，設定自動部署。
6.  **配置環境變數**：在 Cloudflare 中設定 `DEEPSEEK_API_KEY`。
7.  **實現 RAG**：在 Cloudflare 環境下整合向量數據庫和 Embedding。

## 如何在本地運行 (Devbox - 僅供參考，可能已失效)

1.  確保已安裝 Python 3.11。
2.  創建並激活虛擬環境：
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```
3.  安裝依賴：
    ```bash
    pip install -r requirements.txt 
    ```
4.  創建 `.env` 文件並設置 `DEEPSEEK_API_KEY`。
5.  運行應用：
    ```bash
    python vercel_app.py
    ```
6.  在瀏覽器中訪問 `http://localhost:8000` (或 Devbox 提供的端口轉發地址)。 