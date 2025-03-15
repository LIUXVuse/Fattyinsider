#!/bin/bash

# 安裝Python依賴
pip install -r requirements.txt

# 顯示已安裝的包
pip list

# 確保目錄結構正確
mkdir -p data/vector_store

echo "構建完成！" 