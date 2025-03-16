# 肥宅老司機專用AI聊天機器人

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

## Vercel部署指南

本项目支持使用Vercel进行部署。由于Vercel目前不支持公开的Docker部署，我们使用标准的Python运行时进行部署。

### 部署步骤

1. **Fork或克隆项目到GitHub**
   ```bash
   git clone https://github.com/yourusername/fattyinsider-ai.git
   cd fattyinsider-ai
   ```

2. **推送代码到GitHub**
   ```bash
   git add .
   git commit -m "Prepare for Vercel deployment"
   git push origin master
   ```

3. **在Vercel上创建新项目**
   - 登录Vercel账户
   - 点击"New Project"
   - 选择你的GitHub仓库
   - 配置项目设置

4. **配置环境变量**
   在Vercel项目设置中，添加以下环境变量：
   - `DEEPSEEK_API_KEY`: SiliconFlow API密钥
   - `PINECONE_API_KEY`: Pinecone API密钥（如果使用Pinecone）
   - `PINECONE_INDEX_NAME`: Pinecone索引名称（如果使用Pinecone）
   - `APP_ENV`: 设置为`production`
   - `USE_PINECONE`: 设置为`true`（如果使用Pinecone）

5. **部署项目**
   - 点击"Deploy"按钮
   - Vercel会自动识别`vercel.json`和`vercel_app.py`
   - 构建过程会执行`vercel-build.sh`脚本

6. **数据迁移**
   - 在本地运行`python migrate_to_pinecone.py`将数据迁移到Pinecone

### 使用Vercel CLI部署

如果你想使用命令行部署，可以按照以下步骤操作：

1. **安装Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **登录Vercel**
   ```bash
   vercel login
   ```

3. **部署项目**
   ```bash
   vercel --prod
   ```

### 故障排除

如果遇到部署问题，请检查：

1. **依赖冲突**：
   - 检查`requirements.txt`中的依赖版本是否兼容
   - 查看Vercel构建日志中的错误信息

2. **环境变量**：
   - 确保所有必要的环境变量都已正确设置
   - 检查API密钥是否有效

3. **构建脚本**：
   - 检查`vercel-build.sh`脚本是否有执行权限
   - 确保脚本中的命令在Vercel环境中可以正常运行

4. **资源限制**：
   - Vercel有一定的资源限制，确保你的应用不会超出这些限制
   - 如果应用较大，可以考虑增加`maxLambdaSize`设置

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
