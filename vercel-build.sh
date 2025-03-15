#!/bin/bash

echo "开始执行Vercel构建脚本..."

# 检查Python版本
echo "检查Python版本..."
which python || which python3 || echo "未找到Python"
python --version || python3 --version || echo "无法获取Python版本"

# 检查pip版本
echo "检查pip版本..."
which pip || which pip3 || echo "未找到pip"
pip --version || pip3 --version || echo "无法获取pip版本"

# 尝试使用不同的pip命令安装依赖
echo "安装Python依赖..."
pip install -r requirements.txt || pip3 install -r requirements.txt || python -m pip install -r requirements.txt || python3 -m pip install -r requirements.txt || echo "所有pip安装方法都失败了"

# 显示已安装的包
echo "显示已安装的包..."
pip list || pip3 list || python -m pip list || python3 -m pip list || echo "无法显示已安装的包"

# 确保目录结构正确
echo "创建必要的目录..."
mkdir -p data/vector_store

echo "Vercel构建完成！" 