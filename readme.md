# 肥宅老司機 AI 聊天機器人

## 項目概述

肥宅老司機 AI 聊天機器人是一個基於 DeepSeek V3 大型語言模型的聊天應用，部署在 Vercel 平台上。該應用允許用戶通過簡單的網頁界面與 AI 進行對話交流。

## 技術架構

- **前端**：HTML, CSS, JavaScript
- **後端**：Python (FastAPI)
- **AI 模型**：DeepSeek V3
- **部署平台**：Vercel Serverless Functions
- **向量數據庫**：Pinecone (已配置但尚未完全實現)

## 當前功能

- 基本的聊天界面
- 與 DeepSeek V3 模型的 API 集成
- 消息歷史管理（保留最近的對話）
- 錯誤處理和超時管理

## 已知問題

### Vercel 函數超時限制

**主要問題**：即使將超時設置為接近 Vercel 免費計劃的最大限制（60秒），API 調用仍然經常超時。

**具體表現**：
- 用戶發送較長或複雜的問題時，DeepSeek API 無法在限定時間內返回響應
- 系統日誌顯示 "API請求超時" 錯誤
- 用戶體驗受到嚴重影響

**已嘗試的解決方案**：
1. 將 Vercel 函數的 `maxDuration` 設置為 59.9 秒（接近免費用戶上限）
2. 將 socket 超時設置為 55 秒
3. 將前端 JavaScript 超時設置為 58 秒
4. 優化消息歷史，只保留最近的幾條消息
5. 減少 API 請求的 `max_tokens` 參數值
6. 調整模型參數（temperature, top_p 等）以加快響應

**結論**：
即使進行了上述優化，Vercel 免費計劃的 60 秒限制對於 LLM API 調用來說仍然不夠充分，特別是對於較複雜的查詢。

## 項目狀態

**當前狀態**：項目暫停開發

**原因**：
1. Vercel 免費計劃的函數執行時間限制（60秒）不足以支持穩定的 LLM API 調用
2. 需要評估其他部署選項或付費計劃

## 未來計劃

1. **探索替代部署選項**：
   - 考慮使用其他無服務器平台（如 AWS Lambda 等）
   - 評估使用傳統虛擬主機或 VPS 部署

2. **功能改進**（待恢復開發後）：
   - 實現流式響應（Streaming Response）
   - 完成向量數據庫集成，實現 RAG（檢索增強生成）功能
   - 改進用戶界面和體驗
   - 添加更多自定義選項

## 部署說明

### 環境變量

需要設置以下環境變量：
- `DEEPSEEK_API_KEY`：DeepSeek API 密鑰
- `USE_PINECONE`：是否使用 Pinecone 向量數據庫（"true" 或 "false"）
- `PINECONE_API_KEY`：Pinecone API 密鑰（如果啟用 Pinecone）
- `PINECONE_ENVIRONMENT`：Pinecone 環境
- `PINECONE_INDEX`：Pinecone 索引名稱

### Vercel 配置

`vercel.json` 文件包含以下關鍵配置：
```json
{
  "functions": {
    "vercel_app.py": {
      "maxDuration": 59.9
    }
  }
}
```

## 開發者說明

如果您想繼續開發此項目，請考慮以下幾點：

1. **解決超時問題**：
   - 升級到 Vercel Pro 計劃（最大超時 300 秒）
   - 實現流式響應機制
   - 考慮使用其他部署平台

2. **代碼結構**：
   - `vercel_app.py` 是主要入口點
   - HTML 模板和 JavaScript 代碼嵌入在 Python 文件中
   - API 調用使用標準庫實現，避免依賴外部庫

## 聯繫方式

如有問題或建議，請通過 GitHub Issues 聯繫。

---

*最後更新：2024年10月*
