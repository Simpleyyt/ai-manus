#!/bin/bash

echo "Starting MCP Client Service..."

# 设置环境变量
export PYTHONPATH=/app

# 启动应用
cd /app
python -m app.main 