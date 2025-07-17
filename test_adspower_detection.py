#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AdsPower安装检测功能完整测试
测试范围：
1. 后端API功能测试
2. 前端界面测试
3. 边界情况测试
4. 错误处理测试
"""

import requests
import json
import time
import threading
from unittest.mock import patch, MagicMock
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_app import app
from config import ADS_POWER_CONFIG

class AdsPowerDetectionTester:
    def __init__(self, base_url="http://localhost:8084"):
        self.base_url = base_url
        self.test_results = []
        self.failed_tests = []
        
    def log_test(self, test_name, success, message="", details=None):
        """记录测试结果"""
        result = {
            'test_name': test_name,
            'success': success,
            'message': message,
            'details': details,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
        if not success:
            self.failed_tests.append(result)
            if details:
                print(f"   详细信息: {details}")
    
    def test_api_check_adspower_installation_success(self):
        """测试AdsPower安装检测API - 成功情况"""
        test_name = "API检测AdsPower安装 - 成功情况"
        
        try:
            # 模拟AdsPower正常运行的情况
            with patch('requests.get') as mock_get:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    'code': 0,
                    'data': {
                        'list': [
                            {'user_id': 'test1', 'name': 'Test User 1'},
                            {'user_id': 'test2', 'name': 'Test User 2'}
                        ]
                    }
                }
                mock_get.return_value = mock_response
                
                # 发送测试请求
                response = requests.post(
                    f"{self.base_url}/api/check_adspower_installation",
                    json={'api_url': 'http://local.adspower.net:50325'},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success') and 'user_count' in data:
                        self.log_test(test_name, True, "API正确返回AdsPower安装状态")
                    else:
                        self.log_test(test_name, False, "API返回数据格式错误", data)
                else:
                    self.log_test(test_name, False, f"HTTP状态码错误: {response.status_code}")
                    
        except Exception as e:
            self.log_test(test_name, False, f"测试异常: {str(e)}")
    
    def test_api_check_adspower_installation_not_running(self):
        """测试AdsPower安装检测API - 未运行情况"""
        test_name = "API检测AdsPower安装 - 未运行情况"
        
        try:
            # 模拟AdsPower未运行的情况
            response = requests.post(
                f"{self.base_url}/api/check_adspower_installation",
                json={'api_url': 'http://localhost:99999'},  # 使用不存在的端口
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if not data.get('success') and ('AdsPower未启动或未安装' in data.get('message', '') or 
                                               'Connection refused' in data.get('message', '') or
                                               '连接失败' in data.get('message', '')):
                    self.log_test(test_name, True, "正确检测到AdsPower未运行")
                else:
                    self.log_test(test_name, False, "未正确处理连接失败情况", data)
            else:
                self.log_test(test_name, False, f"HTTP状态码错误: {response.status_code}")
                    
        except Exception as e:
            self.log_test(test_name, False, f"测试异常: {str(e)}")
    
    def test_api_check_adspower_installation_timeout(self):
        """测试AdsPower安装检测API - 超时情况"""
        test_name = "API检测AdsPower安装 - 超时情况"
        
        try:
            # 模拟超时情况 - 使用一个会超时的地址
            response = requests.post(
                f"{self.base_url}/api/check_adspower_installation",
                json={'api_url': 'http://10.255.255.1:50325'},  # 使用会超时的地址
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if not data.get('success') and ('AdsPower连接超时' in data.get('message', '') or
                                               '超时' in data.get('message', '') or
                                               'timeout' in data.get('message', '').lower()):
                    self.log_test(test_name, True, "正确处理超时情况")
                else:
                    self.log_test(test_name, False, "未正确处理超时情况", data)
            else:
                self.log_test(test_name, False, f"HTTP状态码错误: {response.status_code}")
                    
        except Exception as e:
            self.log_test(test_name, False, f"测试异常: {str(e)}")
    
    def test_api_check_adspower_installation_api_error(self):
        """测试AdsPower安装检测API - API错误情况"""
        test_name = "API检测AdsPower安装 - API错误情况"
        
        try:
            # 模拟AdsPower API返回错误
            with patch('requests.get') as mock_get:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    'code': -1,
                    'msg': 'API调用失败'
                }
                mock_get.return_value = mock_response
                
                response = requests.post(
                    f"{self.base_url}/api/check_adspower_installation",
                    json={'api_url': 'http://local.adspower.net:50325'},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if not data.get('success') and 'AdsPower API返回错误' in data.get('message', ''):
                        self.log_test(test_name, True, "正确处理API错误")
                    else:
                        self.log_test(test_name, False, "未正确处理API错误", data)
                else:
                    self.log_test(test_name, False, f"HTTP状态码错误: {response.status_code}")
                    
        except Exception as e:
            self.log_test(test_name, False, f"测试异常: {str(e)}")
    
    def test_config_page_accessibility(self):
        """测试配置页面可访问性"""
        test_name = "配置页面可访问性"
        
        try:
            response = requests.get(f"{self.base_url}/config", timeout=10)
            
            if response.status_code == 200:
                content = response.text
                # 检查关键元素是否存在
                required_elements = [
                    'id="status-loading"',
                    'id="status-text"',
                    'id="install-guide"',
                    'checkAdsPowerInstallation()',
                    'https://www.adspower.net/share/hftJaRHMQl1r7jw'
                ]
                
                missing_elements = []
                for element in required_elements:
                    if element not in content:
                        missing_elements.append(element)
                
                if not missing_elements:
                    self.log_test(test_name, True, "配置页面包含所有必需元素")
                else:
                    self.log_test(test_name, False, "配置页面缺少必需元素", missing_elements)
            else:
                self.log_test(test_name, False, f"无法访问配置页面: {response.status_code}")
                
        except Exception as e:
            self.log_test(test_name, False, f"测试异常: {str(e)}")
    
    def test_javascript_function_presence(self):
        """测试JavaScript函数是否存在"""
        test_name = "JavaScript函数存在性"
        
        try:
            response = requests.get(f"{self.base_url}/config", timeout=10)
            
            if response.status_code == 200:
                content = response.text
                
                # 检查JavaScript函数
                js_functions = [
                    'function checkAdsPowerInstallation()',
                    'function testAdsPowerConnection()'
                ]
                
                missing_functions = []
                for func in js_functions:
                    if func not in content:
                        missing_functions.append(func)
                
                if not missing_functions:
                    self.log_test(test_name, True, "所有JavaScript函数都存在")
                else:
                    self.log_test(test_name, False, "缺少JavaScript函数", missing_functions)
            else:
                self.log_test(test_name, False, f"无法访问配置页面: {response.status_code}")
                
        except Exception as e:
            self.log_test(test_name, False, f"测试异常: {str(e)}")
    
    def test_real_adspower_connection(self):
        """测试真实的AdsPower连接"""
        test_name = "真实AdsPower连接测试"
        
        try:
            # 尝试连接真实的AdsPower
            api_url = ADS_POWER_CONFIG.get('local_api_url', 'http://local.adspower.net:50325')
            
            response = requests.post(
                f"{self.base_url}/api/check_adspower_installation",
                json={'api_url': api_url},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_test(test_name, True, f"AdsPower正在运行，检测到{data.get('user_count', 0)}个用户")
                else:
                    self.log_test(test_name, True, f"AdsPower未运行: {data.get('message')}")
            else:
                self.log_test(test_name, False, f"API请求失败: {response.status_code}")
                
        except Exception as e:
            self.log_test(test_name, False, f"测试异常: {str(e)}")
    
    def test_edge_cases(self):
        """测试边界情况"""
        test_name = "边界情况测试"
        
        edge_cases = [
            # 空API URL
            {'api_url': ''},
            # 无效API URL
            {'api_url': 'invalid-url'},
            # 不存在的端口
            {'api_url': 'http://localhost:99999'},
            # 缺少api_url参数
            {}
        ]
        
        passed_cases = 0
        total_cases = len(edge_cases)
        
        for i, case in enumerate(edge_cases):
            try:
                response = requests.post(
                    f"{self.base_url}/api/check_adspower_installation",
                    json=case,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # 边界情况应该返回失败
                    if not data.get('success'):
                        passed_cases += 1
                        print(f"   边界情况 {i+1}: ✅ 正确处理")
                    else:
                        print(f"   边界情况 {i+1}: ❌ 未正确处理")
                else:
                    print(f"   边界情况 {i+1}: ❌ HTTP错误 {response.status_code}")
                    
            except Exception as e:
                print(f"   边界情况 {i+1}: ❌ 异常 {str(e)}")
        
        if passed_cases == total_cases:
            self.log_test(test_name, True, f"所有{total_cases}个边界情况都正确处理")
        else:
            self.log_test(test_name, False, f"只有{passed_cases}/{total_cases}个边界情况正确处理")
    
    def test_concurrent_requests(self):
        """测试并发请求"""
        test_name = "并发请求测试"
        
        def make_request():
            try:
                response = requests.post(
                    f"{self.base_url}/api/check_adspower_installation",
                    json={'api_url': 'http://local.adspower.net:50325'},
                    timeout=10
                )
                return response.status_code == 200
            except:
                return False
        
        # 创建10个并发请求
        threads = []
        results = []
        
        for _ in range(10):
            thread = threading.Thread(target=lambda: results.append(make_request()))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        success_count = sum(results)
        if success_count == 10:
            self.log_test(test_name, True, "所有并发请求都成功")
        else:
            self.log_test(test_name, False, f"只有{success_count}/10个并发请求成功")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🧪 开始AdsPower安装检测功能完整测试")
        print("=" * 60)
        
        # 检查Web服务器是否运行
        try:
            response = requests.get(self.base_url, timeout=5)
            if response.status_code != 200:
                print(f"❌ Web服务器未运行或无法访问: {self.base_url}")
                return
        except:
            print(f"❌ 无法连接到Web服务器: {self.base_url}")
            return
        
        print(f"✅ Web服务器运行正常: {self.base_url}")
        print()
        
        # 运行所有测试
        test_methods = [
            self.test_api_check_adspower_installation_success,
            self.test_api_check_adspower_installation_not_running,
            self.test_api_check_adspower_installation_timeout,
            self.test_api_check_adspower_installation_api_error,
            self.test_config_page_accessibility,
            self.test_javascript_function_presence,
            self.test_real_adspower_connection,
            self.test_edge_cases,
            self.test_concurrent_requests
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                self.log_test(test_method.__name__, False, f"测试执行异常: {str(e)}")
            print()  # 空行分隔
        
        # 输出测试总结
        self.print_summary()
    
    def print_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 60)
        print("📊 测试总结")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = len(self.failed_tests)
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {failed_tests} ❌")
        print(f"成功率: {(passed_tests/total_tests*100):.1f}%")
        
        if self.failed_tests:
            print("\n❌ 失败的测试:")
            for test in self.failed_tests:
                print(f"  - {test['test_name']}: {test['message']}")
                if test['details']:
                    print(f"    详细信息: {test['details']}")
        
        print("\n" + "=" * 60)
        
        if failed_tests == 0:
            print("🎉 所有测试都通过了！功能正常工作。")
        else:
            print(f"⚠️  有{failed_tests}个测试失败，需要修复。")
            
        # 保存测试报告
        self.save_test_report()
    
    def save_test_report(self):
        """保存测试报告"""
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_tests': len(self.test_results),
            'passed_tests': len([r for r in self.test_results if r['success']]),
            'failed_tests': len(self.failed_tests),
            'test_results': self.test_results
        }
        
        try:
            with open('adspower_detection_test_report.json', 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"\n📄 测试报告已保存到: adspower_detection_test_report.json")
        except Exception as e:
            print(f"\n❌ 保存测试报告失败: {str(e)}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AdsPower安装检测功能测试')
    parser.add_argument('--url', default='http://localhost:8084', 
                       help='Web服务器地址 (默认: http://localhost:8084)')
    
    args = parser.parse_args()
    
    tester = AdsPowerDetectionTester(args.url)
    tester.run_all_tests()

if __name__ == '__main__':
    main()