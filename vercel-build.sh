#!/bin/bash

echo "开始执行Vercel构建脚本..."

# 检查Python版本
echo "检查Python版本..."
which python3.9 || which python3 || which python || echo "未找到Python"
python3.9 --version || python3 --version || python --version || echo "无法获取Python版本"

# 检查pip版本
echo "检查pip版本..."
which pip3.9 || which pip3 || which pip || echo "未找到pip"
pip3.9 --version || pip3 --version || pip --version || echo "无法获取pip版本"

# 尝试使用不同的pip命令安装依赖
echo "安装Python依赖..."
pip3.9 install -r requirements.txt || pip3 install -r requirements.txt || pip install -r requirements.txt || python3.9 -m pip install -r requirements.txt || python3 -m pip install -r requirements.txt || python -m pip install -r requirements.txt || echo "所有pip安装方法都失败了"

# 显示已安装的包
echo "显示已安装的包..."
pip3.9 list || pip3 list || pip list || python3.9 -m pip list || python3 -m pip list || python -m pip list || echo "无法显示已安装的包"

# 确保目录结构正确
echo "创建必要的目录..."
mkdir -p data/vector_store

echo "Vercel构建完成！" 