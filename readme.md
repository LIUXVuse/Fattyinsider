# 肥宅老司機 AI 聊天機器人

## 項目概述

肥宅老司機 AI 聊天機器人是一個基於 DeepSeek 大型語言模型的聊天應用。該應用最初設計用於 Vercel 平台，現已遷移至 ClawCloud Devbox 環境進行開發和運行，以解決 Vercel 的執行時間限制問題。應用允許用戶通過簡單的網頁界面與 AI 進行對話交流。

## 技術架構

- **前端**：HTML, CSS, JavaScript (嵌入在 Python 文件中)
- **後端**：Python (使用標準庫 `http.server`)
- **AI 模型**：DeepSeek (`deepseek-chat` 模型)
- **開發與運行環境**：ClawCloud Devbox
- **向量數據庫**：計劃使用 ClawCloud Milvus (尚未實現)
- **依賴管理**：Python 虛擬環境 (`.venv`) + `requirements.txt`
- **密鑰管理**：`.env` 文件 (包含 `DEEPSEEK_API_KEY`)

## 當前功能

- 基本的聊天界面
- 與 DeepSeek API (`deepseek-chat` 模型) 成功集成
- 消息歷史管理（保留最近的 10 條對話）
- 可在 ClawCloud Devbox 環境中通過 `python vercel_app.py` 成功啟動和運行
- 可透過 Devbox 的端口轉發從瀏覽器訪問
- AI 已配置為使用繁體中文回覆

## 開發進度 (ClawCloud Devbox)

1.  **環境遷移**：成功將項目從 GitHub 克隆到 ClawCloud Devbox。
2.  **環境設定**：
    - 創建並啟動了 Python 虛擬環境 (`.venv`)。
    - 解決了初始的 `python3-venv` 缺失問題。
    - 解決了 `requirements.txt` 中因 `pydantic` 和 `pyyaml` 版本衝突導致的多次依賴安裝失敗問題。
    - 成功安裝所有必要的 Python 套件。
3.  **程式碼調整**：
    - 發現 `vercel_app.py` 使用 `http.server` 而非 FastAPI。
    - 修改 `vercel_app.py` 以支持本地直接運行 (`if __name__ == "__main__":`)。
    - 添加 `python-dotenv` 依賴以加載 `.env` 文件。
4.  **API 連接**：
    - 設置了 `.env` 文件儲存 `DEEPSEEK_API_KEY`。
    - 解決了 API 金鑰無效的問題 (使用了正確的金鑰)。
    - 解決了 API 端點錯誤的問題 (從 SiliconFlow 改為 DeepSeek 官方端點)。
    - 解決了模型名稱錯誤的問題 (從 `deepseek-ai/DeepSeek-V3` 改為 `deepseek-chat`)。
    - 成功連接到 DeepSeek API 並獲得回應。
5.  **功能優化**：
    - 移除了 Vercel 特有的超時限制 (如 `socket.setdefaulttimeout`)。
    - 增加了 API 請求的 `max_tokens`。
    - 調整了系統提示，要求 AI 使用繁體中文回覆。
6.  **後續準備**：
    - 安裝了 `pymilvus` 套件，為整合 Milvus 做準備。
    - 等待使用者在 ClawCloud 平台上創建 Milvus 實例。

## 項目狀態

**當前狀態**：正在 ClawCloud Devbox 環境積極開發中

**原因**：
1.  成功將項目遷移至 ClawCloud Devbox，解決了 Vercel 的執行時間限制。
2.  已完成基本聊天功能的調試和運行。
3.  正在準備整合 Milvus 向量數據庫以實現 RAG 功能。

## 未來計劃

1.  **整合向量數據庫 (實現 RAG 功能)**：
    - **目標**：讓 AI 能夠參考外部知識文件進行回答，提高回覆的準確性和相關性。
    - **初步方案評估**：
        - **Milvus (ClawCloud 提供)**：最初考慮的方案。但在評估後發現，其使用量可能超過 ClawCloud 提供的免費額度，導致額外費用。因此暫緩使用 Milvus。
        - **替代方案探索**：
            - **ChromaDB**: 開源、免費的向量數據庫，專為 AI 設計，易於與 Python 整合，可直接在 Devbox 或應用服務中運行。**目前建議優先評估此方案。**
            - **Qdrant**: 功能強大的開源選項，提供自行部署或雲端版本 (可能有免費方案)。
            - **FAISS**: Facebook 開發的高效搜索函式庫，需要自行管理索引儲存，更偏向底層函式庫而非完整資料庫。
    - **下一步**：將研究並嘗試整合 ChromaDB。主要步驟包含：
        - 安裝 `chromadb` Python 套件。
        - 選擇或配置一個 Embedding 模型將文字轉換為向量 (可能利用 DeepSeek API 或其他模型)。
        - 實現將知識文件 (例如文檔、FAQ) 嵌入並儲存到 ChromaDB 的功能。
        - 實現根據使用者提問進行向量搜索，從 ChromaDB 檢索最相關的知識片段。
        - 將檢索到的知識片段整合到給 DeepSeek API 的提示中，以生成更豐富的回覆。

2.  **公開部署應用程式**：
    - 使用 ClawCloud Application Service 將目前在 Devbox 運行的應用程式部署到公開網路，讓任何人都能訪問。(需要創建 `Dockerfile` 並在 ClawCloud 上配置服務)。

## 開發與運行說明

### 環境變量

需要在項目根目錄 (`Fattyinsider/`) 下創建一個 `.env` 文件，並包含以下內容：
```
DEEPSEEK_API_KEY=你的DeepSeek_API金鑰
```
(未來可能會加入 Milvus 連線相關的環境變數)

### 運行步驟

1.  確保已安裝 Python 3.11 或相容版本。
2.  在 `Fattyinsider` 目錄下創建虛擬環境：`python3 -m venv .venv`
3.  啟動虛擬環境：`source .venv/bin/activate`
4.  安裝依賴：`pip install -r requirements.txt`
5.  創建並配置好 `.env` 文件。
6.  運行應用：`python vercel_app.py`
7.  應用程式將在 `http://0.0.0.0:8000` 上運行。可以通過 ClawCloud Devbox 的端口轉發功能在瀏覽器中訪問。

## 聯繫方式

如有問題或建議，請通過 GitHub Issues 聯繫。

---

*最後更新：2025年04月29日*
