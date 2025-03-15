#!/bin/bash

# 安裝Python依賴
python -m pip install -r requirements.txt

# 顯示已安裝的包
python -m pip list

# 確保目錄結構正確
mkdir -p data/vector_store

echo "構建完成！" 