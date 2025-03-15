# 肥宅老司機AI聊天機器人

*最後更新: 2025/03/16*

## 專案概述

這是一個基於 FastAPI 打造的智能聊天機器人系統，專為肥宅老司機(Fattyinsider)設計。系統使用 RAG 技術，結合播客內容知識庫，提供問答服務和內容檢索功能。

### 核心特點

- 🤖 智能對話界面
- 🎯 內容檢索
- 🔍 向量搜索
- 🌐 本地部署與雲端部署
- 🔒 隱私數據保護
- 💬 流式響應體驗

## 當前系統狀態

### 已實現功能

- ✅ 基本的文本處理和向量存儲功能
- ✅ 使用FAISS作為本地向量數據庫
- ✅ 支持Pinecone作為雲端向量數據庫
- ✅ 集成SiliconFlow的DeepSeek R1模型
- ✅ 流式響應功能
- ✅ 基本的搜索功能
- ✅ 優化的文本分塊和索引建立
- ✅ Vercel雲端部署支持

### 存在問題

- ⚠️ 本地部署方式，無法充分利用雲端服務的優勢
- ⚠️ 前端界面仍需進一步優化

## 優化建議

### 1. 文本處理優化

已完成優化，使用更適合中文的分割方式：

```python
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,  # 減小切片大小
    chunk_overlap=100,  # 適當調整重疊
    separators=["\n\n", "\n", "。", "，", "！", "？", " ", ""],  # 優先按自然段落切割
    keep_separator=False
)
```

### 2. LLM服務集成

已完成集成SiliconFlow提供的DeepSeek R1模型：

```python
# 使用SiliconFlow的DeepSeek R1模型
llm = ChatOpenAI(
    model="deepseek-ai/DeepSeek-R1",
    temperature=0.7,
    streaming=True,  # 啟用流式響應
    openai_api_key=settings.DEEPSEEK_API_KEY,
    openai_api_base="https://api.siliconflow.cn/v1"
)
```

### 3. 雲端部署方案

已完成Vercel部署準備工作，並支持Pinecone作為向量數據庫：

- 創建了`vercel.json`配置文件
- 創建了`vercel_app.py`入口點
- 更新了`vector_store.py`以支持Pinecone
- 創建了`migrate_to_pinecone.py`用於數據遷移

## 系統架構

### 當前技術棧

#### 前端層
- HTML/CSS/JavaScript
- TailwindCSS
- 流式響應UI

#### AI對話層
- FastAPI
- DeepSeek R1模型
- RAG Pipeline
- 流式響應API

#### 計算層
- Python 3.10+
- FastAPI
- Uvicorn

#### 存儲層
- FAISS (本地向量存儲)
- Pinecone (雲端向量存儲)
- 文件系統 (文本存儲)

## 部署指南

### 本地部署

1. 克隆專案
```bash
git clone https://github.com/yourusername/fattyinsider-ai.git
cd fattyinsider-ai
```

2. 創建虛擬環境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```

3. 安裝依賴
```bash
pip install -r requirements.txt
```

4. 環境配置
```env
# API密鑰
DEEPSEEK_API_KEY=your-api-key
PINECONE_API_KEY=your-pinecone-api-key  # 如果使用Pinecone

# 向量數據庫配置
PINECONE_INDEX_NAME=fattyinsider-index  # 如果使用Pinecone

# 應用配置
APP_ENV=development  # development, production
LOG_LEVEL=info  # debug, info, warning, error
```

5. 加載數據
```bash
# 使用本地FAISS
python load_data.py

# 或遷移到Pinecone
python migrate_to_pinecone.py
```

6. 運行應用
```bash
python run.py
```

7. 訪問應用
```
http://localhost:8000
```

### Vercel部署

1. Fork或克隆專案到GitHub

2. 在Vercel上創建新項目
   - 連接GitHub倉庫
   - 設置環境變量：
     - `DEEPSEEK_API_KEY`
     - `PINECONE_API_KEY`
     - `PINECONE_INDEX_NAME`
     - `APP_ENV=production`
     - `USE_PINECONE=true`

3. 部署項目
   - Vercel會自動識別`vercel.json`和`vercel_app.py`

4. 數據遷移
   - 在本地運行`python migrate_to_pinecone.py`將數據遷移到Pinecone

## API使用指南

### 聊天API

#### 普通聊天請求
```
POST /chat/completions
Content-Type: application/json

{
  "messages": [
    {"role": "user", "content": "肥宅老司機是什麼？"}
  ],
  "stream": false
}
```

#### 流式聊天請求
```
POST /chat/completions
Content-Type: application/json

{
  "messages": [
    {"role": "user", "content": "肥宅老司機是什麼？"}
  ],
  "stream": true
}
```

或使用專用流式端點：
```
POST /chat/stream
Content-Type: application/json

{
  "messages": [
    {"role": "user", "content": "肥宅老司機是什麼？"}
  ]
}
```

### 搜索API

```
GET /search/simple?q=肥宅老司機
```

## 下一步計劃

1. **短期改進**：
   - 進一步優化前端界面
   - 添加用戶反饋機制
   - 改進錯誤處理

2. **中期目標**：
   - 實現多輪對話記憶功能
   - 添加更多播客內容
   - 實現更好的搜索體驗

3. **長期規劃**：
   - 實現個性化推薦
   - 支持多模態內容(音頻、圖片)
   - 添加數據分析和用戶行為洞察

## 授權協議

MIT License
