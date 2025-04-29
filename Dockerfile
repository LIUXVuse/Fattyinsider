# 使用官方 Python 映像檔作為基礎
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 複製依賴需求文件
COPY requirements.txt requirements.txt

# 安裝依賴
# --no-cache-dir 不保留下載快取，減少映像檔大小
# --default-timeout 增加超時時間，防止網路不穩導致安裝失敗
RUN pip install --no-cache-dir --default-timeout=100 -r requirements.txt

# 複製應用程式程式碼到工作目錄
COPY . .

# 設定環境變數 (指定 DeepSeek API Key，實際值應在 ClawCloud 服務中設定)
# ENV DEEPSEEK_API_KEY="your_api_key_here"

# 開放應用程式運行的端口
EXPOSE 8000

# 執行應用程式的指令
CMD ["python", "vercel_app.py"] 