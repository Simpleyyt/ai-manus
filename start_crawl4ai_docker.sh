#!/bin/bash

echo "🚀 Crawl4AI Docker 快速启动脚本"
echo "=================================="

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker 未运行，请先启动 Docker"
    exit 1
fi

# 检查 docker-compose 是否可用
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose 未安装，请先安装 docker-compose"
    exit 1
fi

echo "📦 构建 Docker 镜像..."
docker-compose build backend

if [ $? -ne 0 ]; then
    echo "❌ 镜像构建失败"
    exit 1
fi

echo "🚀 启动服务..."
docker-compose up -d

if [ $? -ne 0 ]; then
    echo "❌ 服务启动失败"
    exit 1
fi

echo "⏳ 等待服务启动..."
sleep 15

# 检查服务状态
echo "📊 检查服务状态..."
docker-compose ps

# 测试 Crawl4AI 功能
echo "🧪 测试 Crawl4AI 功能..."
docker-compose exec backend python test_crawl4ai.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 启动成功！"
    echo "=================================="
    echo "🌐 访问地址:"
    echo "   前端界面: http://localhost:5173"
    echo "   后端 API: http://localhost:8000"
    echo "   API 文档: http://localhost:8000/docs"
    echo ""
    echo "📖 使用说明:"
    echo "   1. 打开前端界面"
    echo "   2. 选择浏览器模式（快速/完整）"
    echo "   3. 输入要访问的网址"
    echo "   4. 开始浏览网页内容"
    echo ""
    echo "🔧 常用命令:"
    echo "   查看日志: docker-compose logs -f backend"
    echo "   停止服务: docker-compose down"
    echo "   重启服务: docker-compose restart"
else
    echo "⚠️ Crawl4AI 测试失败，但服务已启动"
    echo "请检查日志: docker-compose logs backend"
fi 