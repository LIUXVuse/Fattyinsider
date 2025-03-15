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

# 安装依赖
echo "安装Python依赖..."
python -m pip install -r requirements.txt || pip install -r requirements.txt || echo "pip安装失败"

# 显示已安装的包
echo "显示已安装的包..."
python -m pip list || pip list || echo "无法显示已安装的包"

# 确保目录结构正确
echo "创建必要的目录..."
mkdir -p data/vector_store

echo "Vercel构建完成！" 