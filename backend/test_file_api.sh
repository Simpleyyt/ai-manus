#!/bin/bash

# 文件 API 测试脚本
# 使用前请确保后端服务已启动

API_BASE="http://localhost:8000/api/v1"
TEST_FILE="test_upload.txt"

echo "🚀 开始文件 API 测试"
echo "API 地址: $API_BASE"
echo

# 创建测试文件
echo "创建测试文件..."
cat > $TEST_FILE << EOF
这是一个测试文件
Hello World!
测试中文内容
EOF
echo "✅ 测试文件创建完成: $TEST_FILE"
echo

# 1. 测试文件上传
echo "===================================================="
echo "🔄 测试文件上传..."
UPLOAD_RESPONSE=$(curl -s -X POST "$API_BASE/files" -F "file=@$TEST_FILE")
echo "上传响应: $UPLOAD_RESPONSE"

# 提取文件ID
FILE_ID=$(echo $UPLOAD_RESPONSE | grep -o '"file_id":"[^"]*"' | cut -d'"' -f4)
echo "文件ID: $FILE_ID"
echo

if [ -z "$FILE_ID" ]; then
    echo "❌ 文件上传失败，无法获取文件ID"
    exit 1
fi

# 2. 测试获取文件信息
echo "===================================================="
echo "🔄 测试获取文件信息..."
curl -s -X GET "$API_BASE/files/$FILE_ID/info"
echo

# 3. 测试文件列表
echo "===================================================="
echo "🔄 测试文件列表..."
curl -s -X GET "$API_BASE/files?limit=5"
echo

# 4. 测试文件下载
echo "===================================================="
echo "🔄 测试文件下载..."
curl -s -X GET "$API_BASE/files/$FILE_ID" -o "downloaded_$TEST_FILE"
echo "文件已下载为: downloaded_$TEST_FILE"
echo "下载内容:"
cat "downloaded_$TEST_FILE"
echo
echo

# 5. 测试文件存在检查
echo "===================================================="
echo "🔄 测试文件存在检查..."
curl -s -X GET "$API_BASE/files/$FILE_ID/exists"
echo

# 6. 测试文件删除
echo "===================================================="
echo "🔄 测试文件删除..."
curl -s -X DELETE "$API_BASE/files/$FILE_ID"
echo

# 7. 验证文件已删除
echo "===================================================="
echo "🔄 验证文件已删除..."
curl -s -X GET "$API_BASE/files/$FILE_ID/exists"
echo

# 清理测试文件
echo "===================================================="
echo "🧹 清理测试文件..."
rm -f "$TEST_FILE" "downloaded_$TEST_FILE"
echo "✅ 测试完成!" 