#!/usr/bin/env python3
"""
简单的文件 API 测试脚本
使用前请确保后端服务已启动
"""

import requests
import json
import io
import os
from typing import Optional

# 配置
API_BASE_URL = "http://localhost:8000/api/v1"
TEST_FILE_CONTENT = "这是一个测试文件的内容\nHello World!\n测试中文内容"
TEST_FILE_NAME = "test_file.txt"


class FileAPITester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.uploaded_file_id: Optional[str] = None
    
    def test_upload_file(self):
        """测试文件上传"""
        print("🔄 测试文件上传...")
        
        # 创建测试文件
        files = {
            'file': (TEST_FILE_NAME, io.StringIO(TEST_FILE_CONTENT), 'text/plain')
        }
        
        try:
            response = requests.post(f"{self.base_url}/files", files=files)
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    data = result['data']
                    self.uploaded_file_id = data['file_id']
                    print(f"   ✅ 上传成功!")
                    print(f"   文件ID: {data['file_id']}")
                    print(f"   文件名: {data['filename']}")
                    print(f"   文件大小: {data['size']} bytes")
                    print(f"   上传时间: {data['upload_date']}")
                    return True
                else:
                    print(f"   ❌ 上传失败: {result}")
            else:
                print(f"   ❌ 上传失败: {response.text}")
        except Exception as e:
            print(f"   ❌ 上传异常: {str(e)}")
        
        return False
    
    def test_get_file_info(self):
        """测试获取文件信息"""
        if not self.uploaded_file_id:
            print("   ⚠️  跳过文件信息测试：没有已上传的文件")
            return False
        
        print("🔄 测试获取文件信息...")
        
        try:
            response = requests.get(f"{self.base_url}/files/{self.uploaded_file_id}/info")
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    data = result['data']
                    print(f"   ✅ 获取文件信息成功!")
                    print(f"   文件ID: {data['file_id']}")
                    print(f"   文件名: {data['filename']}")
                    print(f"   文件类型: {data['content_type']}")
                    print(f"   文件大小: {data['size']} bytes")
                    print(f"   上传时间: {data['upload_date']}")
                    return True
                else:
                    print(f"   ❌ 获取失败: {result}")
            else:
                print(f"   ❌ 获取失败: {response.text}")
        except Exception as e:
            print(f"   ❌ 获取异常: {str(e)}")
        
        return False
    
    def test_list_files(self):
        """测试文件列表"""
        print("🔄 测试文件列表...")
        
        try:
            response = requests.get(f"{self.base_url}/files?limit=10&skip=0")
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    data = result['data']
                    print(f"   ✅ 获取文件列表成功!")
                    print(f"   总文件数: {data['total']}")
                    print(f"   当前页文件数: {len(data['files'])}")
                    
                    for i, file_info in enumerate(data['files'][:3]):  # 只显示前3个
                        print(f"   文件 {i+1}: {file_info['filename']} ({file_info['size']} bytes)")
                    
                    return True
                else:
                    print(f"   ❌ 获取失败: {result}")
            else:
                print(f"   ❌ 获取失败: {response.text}")
        except Exception as e:
            print(f"   ❌ 获取异常: {str(e)}")
        
        return False
    
    def test_download_file(self):
        """测试文件下载"""
        if not self.uploaded_file_id:
            print("   ⚠️  跳过文件下载测试：没有已上传的文件")
            return False
        
        print("🔄 测试文件下载...")
        
        try:
            response = requests.get(f"{self.base_url}/files/{self.uploaded_file_id}")
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                content = response.text
                print(f"   ✅ 下载成功!")
                print(f"   文件内容长度: {len(content)} 字符")
                print(f"   内容预览: {content[:50]}{'...' if len(content) > 50 else ''}")
                
                # 验证内容是否正确
                if TEST_FILE_CONTENT in content:
                    print("   ✅ 文件内容验证成功!")
                    return True
                else:
                    print("   ❌ 文件内容验证失败!")
            else:
                print(f"   ❌ 下载失败: {response.text}")
        except Exception as e:
            print(f"   ❌ 下载异常: {str(e)}")
        
        return False
    
    def test_file_exists(self):
        """测试文件存在检查"""
        if not self.uploaded_file_id:
            print("   ⚠️  跳过文件存在检查：没有已上传的文件")
            return False
        
        print("🔄 测试文件存在检查...")
        
        try:
            response = requests.get(f"{self.base_url}/files/{self.uploaded_file_id}/exists")
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    exists = result['data']
                    print(f"   ✅ 检查成功! 文件存在: {exists}")
                    return exists
                else:
                    print(f"   ❌ 检查失败: {result}")
            else:
                print(f"   ❌ 检查失败: {response.text}")
        except Exception as e:
            print(f"   ❌ 检查异常: {str(e)}")
        
        return False
    
    def test_delete_file(self):
        """测试文件删除"""
        if not self.uploaded_file_id:
            print("   ⚠️  跳过文件删除测试：没有已上传的文件")
            return False
        
        print("🔄 测试文件删除...")
        
        try:
            response = requests.delete(f"{self.base_url}/files/{self.uploaded_file_id}")
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    print(f"   ✅ 删除成功!")
                    return True
                else:
                    print(f"   ❌ 删除失败: {result}")
            else:
                print(f"   ❌ 删除失败: {response.text}")
        except Exception as e:
            print(f"   ❌ 删除异常: {str(e)}")
        
        return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始文件 API 测试\n")
        
        tests = [
            ("文件上传", self.test_upload_file),
            ("获取文件信息", self.test_get_file_info),
            ("文件列表", self.test_list_files),
            ("文件下载", self.test_download_file),
            ("文件存在检查", self.test_file_exists),
            ("文件删除", self.test_delete_file),
        ]
        
        results = []
        for test_name, test_func in tests:
            print(f"\n{'='*50}")
            result = test_func()
            results.append((test_name, result))
            print()
        
        # 显示测试总结
        print(f"\n{'='*50}")
        print("📊 测试总结:")
        passed = 0
        for test_name, result in results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"   {test_name}: {status}")
            if result:
                passed += 1
        
        print(f"\n总计: {passed}/{len(results)} 个测试通过")
        return passed == len(results)


def main():
    """主函数"""
    print("文件 API 测试工具")
    print(f"API 地址: {API_BASE_URL}")
    
    # 检查服务是否可用
    try:
        response = requests.get(f"{API_BASE_URL}/../")  # 尝试访问根路径
        print("✅ 服务连接正常")
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务，请确保后端服务已启动")
        print("   启动命令: python -m app.main")
        return
    except Exception as e:
        print(f"⚠️  服务连接检查异常: {str(e)}")
    
    # 运行测试
    tester = FileAPITester(API_BASE_URL)
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 所有测试通过!")
    else:
        print("\n⚠️  部分测试失败，请检查服务状态")


if __name__ == "__main__":
    main() 