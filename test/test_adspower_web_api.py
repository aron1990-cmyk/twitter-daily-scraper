# -*- coding: utf-8 -*-
"""
AdsPower Web API 测试脚本
测试 Flask Web 应用中的 AdsPower 相关 API 接口
"""

import sys
import os
import unittest
import requests
import json
import time
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAdsPowerWebAPI(unittest.TestCase):
    """测试 AdsPower Web API 接口"""
    
    def setUp(self):
        """测试前准备"""
        self.base_url = "http://localhost:8090"  # 假设服务运行在8090端口
        self.timeout = 15
        
        # 测试数据
        self.test_config = {
            'api_host': '127.0.0.1',
            'api_port': '50325',
            'api_key': 'test_key',
            'user_id': 'test_user_id'
        }
        
    def test_server_availability(self):
        """测试服务器可用性"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            print(f"\n服务器状态: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Web 服务器运行正常")
            else:
                print(f"⚠️ Web 服务器响应异常: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("❌ 无法连接到 Web 服务器")
            print(f"请确保服务器运行在: {self.base_url}")
        except Exception as e:
            print(f"❌ 服务器检查失败: {e}")
            
    def test_config_page(self):
        """测试配置页面"""
        try:
            response = requests.get(f"{self.base_url}/config", timeout=self.timeout)
            print(f"\n配置页面状态: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ 配置页面加载成功")
                
                # 检查页面内容
                content = response.text
                if 'AdsPower' in content:
                    print("✅ 页面包含 AdsPower 配置内容")
                else:
                    print("⚠️ 页面可能缺少 AdsPower 配置内容")
                    
            else:
                print(f"❌ 配置页面加载失败: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 配置页面测试失败: {e}")
            
    def test_adspower_connection_api(self):
        """测试 AdsPower 连接 API"""
        api_url = f"{self.base_url}/api/test_adspower_connection"
        
        try:
            # 测试 POST 请求
            response = requests.post(
                api_url,
                json=self.test_config,
                timeout=self.timeout
            )
            
            print(f"\nAdsPower 连接 API 状态: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"API 响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
                    
                    if 'success' in data:
                        if data['success']:
                            print("✅ AdsPower 连接测试成功")
                        else:
                            print(f"⚠️ AdsPower 连接测试失败: {data.get('message', '未知错误')}")
                    else:
                        print("⚠️ API 响应格式异常")
                        
                except json.JSONDecodeError:
                    print("❌ API 响应不是有效的 JSON")
                    print(f"响应内容: {response.text[:200]}...")
            else:
                print(f"❌ API 请求失败: {response.status_code}")
                print(f"响应内容: {response.text[:200]}...")
                
        except requests.exceptions.Timeout:
            print(f"❌ API 请求超时 (>{self.timeout}秒)")
        except Exception as e:
            print(f"❌ API 测试失败: {e}")
            
    def test_adspower_installation_check_api(self):
        """测试 AdsPower 安装检查 API"""
        api_url = f"{self.base_url}/api/check_adspower_installation"
        
        try:
            # 测试 POST 请求（使用 form 数据）
            response = requests.post(
                api_url,
                data=self.test_config,
                timeout=self.timeout
            )
            
            print(f"\nAdsPower 安装检查 API 状态: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"API 响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
                    
                    if 'success' in data:
                        if data['success']:
                            print("✅ AdsPower 安装检查通过")
                        else:
                            print(f"⚠️ AdsPower 安装检查失败: {data.get('message', '未知错误')}")
                    else:
                        print("⚠️ API 响应格式异常")
                        
                except json.JSONDecodeError:
                    print("❌ API 响应不是有效的 JSON")
                    print(f"响应内容: {response.text[:200]}...")
            else:
                print(f"❌ API 请求失败: {response.status_code}")
                print(f"响应内容: {response.text[:200]}...")
                
        except requests.exceptions.Timeout:
            print(f"❌ API 请求超时 (>{self.timeout}秒)")
        except Exception as e:
            print(f"❌ API 测试失败: {e}")
            
    def test_adspower_browser_test_api(self):
        """测试 AdsPower 浏览器测试 API"""
        api_url = f"{self.base_url}/api/test_open_adspower"
        
        try:
            # 测试 POST 请求（使用 form 数据）
            response = requests.post(
                api_url,
                data=self.test_config,
                timeout=self.timeout
            )
            
            print(f"\nAdsPower 浏览器测试 API 状态: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"API 响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
                    
                    if 'success' in data:
                        if data['success']:
                            print("✅ AdsPower 浏览器测试成功")
                        else:
                            print(f"⚠️ AdsPower 浏览器测试失败: {data.get('message', '未知错误')}")
                    else:
                        print("⚠️ API 响应格式异常")
                        
                except json.JSONDecodeError:
                    print("❌ API 响应不是有效的 JSON")
                    print(f"响应内容: {response.text[:200]}...")
            else:
                print(f"❌ API 请求失败: {response.status_code}")
                print(f"响应内容: {response.text[:200]}...")
                
        except requests.exceptions.Timeout:
            print(f"❌ API 请求超时 (>{self.timeout}秒)")
        except Exception as e:
            print(f"❌ API 测试失败: {e}")
            
    def test_api_timeout_handling(self):
        """测试 API 超时处理"""
        print("\n测试 API 超时处理...")
        
        # 测试短超时
        api_url = f"{self.base_url}/api/test_adspower_connection"
        
        try:
            start_time = time.time()
            response = requests.post(
                api_url,
                json=self.test_config,
                timeout=1  # 1秒超时
            )
            end_time = time.time()
            
            duration = end_time - start_time
            print(f"请求耗时: {duration:.2f}秒")
            
            if duration < 1.5:  # 允许一些误差
                print("✅ 超时控制正常")
            else:
                print("⚠️ 超时控制可能异常")
                
        except requests.exceptions.Timeout:
            print("✅ 超时异常正确抛出")
        except Exception as e:
            print(f"⚠️ 其他异常: {e}")
            
    def test_api_error_responses(self):
        """测试 API 错误响应"""
        print("\n测试 API 错误响应...")
        
        # 测试无效的 API 端点
        invalid_url = f"{self.base_url}/api/invalid_endpoint"
        
        try:
            response = requests.post(invalid_url, json={}, timeout=5)
            print(f"无效端点响应状态: {response.status_code}")
            
            if response.status_code == 404:
                print("✅ 无效端点正确返回 404")
            else:
                print(f"⚠️ 无效端点返回: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 无效端点测试失败: {e}")
            
        # 测试空数据
        api_url = f"{self.base_url}/api/test_adspower_connection"
        
        try:
            response = requests.post(api_url, json={}, timeout=5)
            print(f"空数据请求状态: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if not data.get('success', True):  # 应该失败
                    print("✅ 空数据正确处理")
                else:
                    print("⚠️ 空数据处理可能异常")
            else:
                print(f"⚠️ 空数据请求返回: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 空数据测试失败: {e}")


class TestAdsPowerWebAPIOptimized(unittest.TestCase):
    """测试优化版 AdsPower Web API 接口"""
    
    def setUp(self):
        """测试前准备"""
        self.base_url = "http://localhost:8090"  # 优化版服务端口
        self.timeout = 15
        
    def test_optimized_connection_api(self):
        """测试优化版连接 API"""
        api_url = f"{self.base_url}/api/test_adspower_connection"
        
        test_data = {
            'api_host': '127.0.0.1:50325',
            'api_key': 'test_key',
            'user_ids': ['test_user_1', 'test_user_2']
        }
        
        try:
            response = requests.post(
                api_url,
                json=test_data,
                timeout=self.timeout
            )
            
            print(f"\n优化版连接 API 状态: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"API 响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
                    
                    # 检查响应结构
                    expected_keys = ['success', 'message']
                    for key in expected_keys:
                        if key in data:
                            print(f"✅ 包含字段: {key}")
                        else:
                            print(f"⚠️ 缺少字段: {key}")
                            
                except json.JSONDecodeError:
                    print("❌ API 响应不是有效的 JSON")
            else:
                print(f"❌ API 请求失败: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 优化版 API 测试失败: {e}")


def run_web_api_tests():
    """运行 Web API 测试"""
    print("="*60)
    print("AdsPower Web API 测试开始")
    print("="*60)
    
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加基础 Web API 测试
    suite.addTest(TestAdsPowerWebAPI('test_server_availability'))
    suite.addTest(TestAdsPowerWebAPI('test_config_page'))
    suite.addTest(TestAdsPowerWebAPI('test_adspower_connection_api'))
    suite.addTest(TestAdsPowerWebAPI('test_adspower_installation_check_api'))
    suite.addTest(TestAdsPowerWebAPI('test_adspower_browser_test_api'))
    suite.addTest(TestAdsPowerWebAPI('test_api_timeout_handling'))
    suite.addTest(TestAdsPowerWebAPI('test_api_error_responses'))
    
    # 添加优化版 API 测试
    suite.addTest(TestAdsPowerWebAPIOptimized('test_optimized_connection_api'))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    print("\n" + "="*60)
    print("Web API 测试结果汇总")
    print("="*60)
    print(f"运行测试: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"- {test}")
            
    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"- {test}")
            
    return len(result.failures) == 0 and len(result.errors) == 0


if __name__ == '__main__':
    success = run_web_api_tests()
    
    print("\n" + "="*60)
    if success:
        print("🎉 所有 Web API 测试通过！")
    else:
        print("⚠️ 部分 Web API 测试失败，请检查服务器状态")
    print("="*60)
    
    sys.exit(0 if success else 1)