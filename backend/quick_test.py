#!/usr/bin/env python3
"""
快速文件 API 测试
"""

import requests
import json
from io import BytesIO

# 配置
API_BASE = "http://localhost:8000/api/v1"

def test_file_api():
    """快速测试文件 API"""
    print("🚀 快速文件 API 测试")
    
    # 1. 上传文件
    print("\n1️⃣ 上传测试文件...")
    test_content = "Hello World!\n这是一个测试文件\n测试中文内容"
    files = {'file': ('test.txt', BytesIO(test_content.encode('utf-8')), 'text/plain')}
    
    try:
        response = requests.post(f"{API_BASE}/files", files=files)
        if response.status_code == 200:
            result = response.json()
            file_id = result['data']['file_id']
            print(f"✅ 上传成功! 文件ID: {file_id}")
        else:
            print(f"❌ 上传失败: {response.text}")
            return
    except Exception as e:
        print(f"❌ 上传异常: {e}")
        return
    
    # 2. 获取文件信息
    print("\n2️⃣ 获取文件信息...")
    try:
        response = requests.get(f"{API_BASE}/files/{file_id}/info")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 文件信息: {json.dumps(result['data'], indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 获取失败: {response.text}")
    except Exception as e:
        print(f"❌ 获取异常: {e}")
    
    # 3. 下载文件
    print("\n3️⃣ 下载文件...")
    try:
        response = requests.get(f"{API_BASE}/files/{file_id}")
        if response.status_code == 200:
            content = response.text
            print(f"✅ 下载成功! 内容: {repr(content[:50])}")
        else:
            print(f"❌ 下载失败: {response.text}")
    except Exception as e:
        print(f"❌ 下载异常: {e}")
    
    # 4. 列出文件
    print("\n4️⃣ 列出文件...")
    try:
        response = requests.get(f"{API_BASE}/files?limit=3")
        if response.status_code == 200:
            result = response.json()
            files_count = len(result['data']['files'])
            total = result['data']['total']
            print(f"✅ 文件列表: 共 {total} 个文件，显示 {files_count} 个")
        else:
            print(f"❌ 列表失败: {response.text}")
    except Exception as e:
        print(f"❌ 列表异常: {e}")
    
    # 5. 删除文件
    print("\n5️⃣ 删除文件...")
    try:
        response = requests.delete(f"{API_BASE}/files/{file_id}")
        if response.status_code == 200:
            print("✅ 删除成功!")
        else:
            print(f"❌ 删除失败: {response.text}")
    except Exception as e:
        print(f"❌ 删除异常: {e}")
    
    print("\n🎉 测试完成!")

if __name__ == "__main__":
    test_file_api() 