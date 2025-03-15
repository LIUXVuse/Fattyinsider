#!/bin/bash

# 显示Python和pip版本
python --version
pip --version

# 安装Python依赖
pip install -r requirements.txt

# 显示已安装的包
pip list

# 确保目录结构正确
mkdir -p data/vector_store

echo "Vercel构建完成！" 