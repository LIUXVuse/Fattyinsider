#!/bin/bash

# 显示Python版本
python --version

# 安装Python依赖
pip install -r requirements.txt

# 显示已安装的包
pip list

# 确保目录结构正确
mkdir -p data/vector_store

echo "构建完成！" 