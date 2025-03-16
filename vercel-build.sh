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

# 安装所有依赖
echo "安装项目依赖..."
pip install -r requirements.txt

# 显示已安装的包
echo "显示已安装的包..."
pip list || echo "无法显示已安装的包"

# 创建必要的目录
echo "创建必要的目录..."
mkdir -p data/vector_store

# 检查环境变量
echo "检查环境变量..."
if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo "警告: DEEPSEEK_API_KEY 未设置"
fi
if [ -z "$PINECONE_API_KEY" ]; then
    echo "警告: PINECONE_API_KEY 未设置"
fi
if [ -z "$PINECONE_INDEX_NAME" ]; then
    echo "警告: PINECONE_INDEX_NAME 未设置"
fi

echo "Vercel构建完成！" 