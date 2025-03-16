FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装核心依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir fastapi==0.110.0 uvicorn==0.27.1 python-dotenv==1.0.1

# 安装其他依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p data/vector_store

# 设置环境变量
ENV APP_ENV=production
ENV LOG_LEVEL=info
ENV USE_PINECONE=true
ENV PORT=8000

# 暴露端口 - Vercel会自动映射这个端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD uvicorn vercel_app:app --host 0.0.0.0 --port ${PORT:-8000} 