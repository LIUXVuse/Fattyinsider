#!/bin/bash

echo "开始执行Vercel构建脚本..."

# 检查Python版本
echo "检查Python版本..."
which python || echo "未找到Python"
python --version || echo "无法获取Python版本"

# 检查pip版本
echo "检查pip版本..."
which pip || echo "未找到pip"
pip --version || echo "无法获取pip版本"

# 安装核心依赖
echo "安装核心依赖..."
pip install --upgrade pip
pip install fastapi==0.110.0 uvicorn==0.27.1 python-dotenv==1.0.1

# 安装其他依赖，使用--no-deps避免依赖冲突
echo "安装其他依赖..."
pip install --no-deps -r requirements.txt || echo "部分依赖安装失败，继续执行"

# 单独安装关键依赖
echo "安装关键依赖..."
pip install langchain>=0.0.310 langchain-openai>=0.0.2 openai>=1.6.1,<2.0.0
pip install pinecone-client==2.2.2 loguru==0.7.0 tqdm==4.66.1
pip install python-multipart==0.0.9 jinja2==3.1.2 httpx==0.24.1 pyyaml==5.4.1
pip install aiohttp==3.8.5 sse-starlette==1.6.5

# 显示已安装的包
echo "显示已安装的包..."
pip list || echo "无法显示已安装的包"

# 确保目录结构正确
echo "创建必要的目录..."
mkdir -p data/vector_store

echo "Vercel构建完成！" 