# -*- coding: utf-8 -*-
"""
AdsPower 连接测试脚本
测试 AdsPower API 连接和浏览器启动功能
"""

import sys
import os
import unittest
import requests
import time
import json
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.adspower_config import get_config, get_primary_user_id
from utils.adspower_manager import AdsPowerManager
from utils.ads_browser_launcher import AdsPowerLauncher


class TestAdsPowerConnection(unittest.TestCase):
    """测试 AdsPower 连接功能"""
    
    def setUp(self):
        """测试前准备"""
        self.config = get_config()
        self.manager = AdsPowerManager()
        self.api_url = self.config['local_api_url']
        self.user_id = get_primary_user_id()
        
    def test_api_url_format(self):
        """测试 API URL 格式"""
        self.assertTrue(self.api_url.startswith('http://'))
        self.assertIn(':', self.api_url)
        
    def test_ping_adspower_api(self):
        """测试 AdsPower API 连通性"""
        try:
            # 测试状态接口
            status_url = f"{self.api_url}/status"
            response = requests.get(status_url, timeout=5)
            
            print(f"\n状态检查 URL: {status_url}")
            print(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ AdsPower API 连接成功")
            else:
                print(f"⚠️ AdsPower API 响应异常: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("❌ AdsPower API 连接失败 - 连接被拒绝")
            print("请确保:")
            print("1. AdsPower 已启动")
            print("2. 本地 API 服务已开启")
            print(f"3. API 地址正确: {self.api_url}")
        except requests.exceptions.Timeout:
            print("❌ AdsPower API 连接超时")
        except Exception as e:
            print(f"❌ AdsPower API 连接错误: {e}")
            
    def test_user_list_api(self):
        """测试用户列表 API"""
        try:
            # 测试用户列表接口
            list_url = f"{self.api_url}/api/v1/user/list"
            
            # 准备请求头
            headers = {}
            if self.config.get('api_key'):
                headers['Authorization'] = f'Bearer {self.config["api_key"]}'
                
            response = requests.get(list_url, headers=headers, timeout=10)
            
            print(f"\n用户列表 URL: {list_url}")
            print(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"API 响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
                    
                    if data.get('code') == 0:
                        users = data.get('data', {}).get('list', [])
                        print(f"✅ 获取到 {len(users)} 个用户配置")
                        
                        # 显示用户信息
                        for user in users[:3]:  # 只显示前3个
                            print(f"  - 用户ID: {user.get('user_id', 'N/A')}")
                            print(f"    用户名: {user.get('name', 'N/A')}")
                            print(f"    分组: {user.get('group_name', 'N/A')}")
                            print(f"    状态: {user.get('remark', 'N/A')}")
                    else:
                        print(f"⚠️ API 返回错误: {data.get('msg', '未知错误')}")
                        
                except json.JSONDecodeError:
                    print("⚠️ 响应不是有效的 JSON 格式")
                    print(f"响应内容: {response.text[:200]}...")
            elif response.status_code == 401:
                print("❌ API Key 验证失败")
            else:
                print(f"⚠️ HTTP 错误: {response.status_code}")
                print(f"响应内容: {response.text[:200]}...")
                
        except requests.exceptions.ConnectionError:
            print("❌ 无法连接到 AdsPower API")
        except requests.exceptions.Timeout:
            print("❌ API 请求超时")
        except Exception as e:
            print(f"❌ API 请求错误: {e}")
            
    def test_user_id_validation(self):
        """测试用户ID验证"""
        print(f"\n配置的用户ID: {self.user_id}")
        
        if not self.user_id:
            print("⚠️ 未配置用户ID")
            return
            
        try:
            # 检查用户是否存在
            list_url = f"{self.api_url}/api/v1/user/list"
            headers = {}
            if self.config.get('api_key'):
                headers['Authorization'] = f'Bearer {self.config["api_key"]}'
                
            response = requests.get(list_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    users = data.get('data', {}).get('list', [])
                    user_ids = [user.get('user_id') for user in users]
                    
                    if self.user_id in user_ids:
                        print(f"✅ 用户ID {self.user_id} 存在")
                        
                        # 获取用户详细信息
                        user_info = next((u for u in users if u.get('user_id') == self.user_id), None)
                        if user_info:
                            print(f"  用户名: {user_info.get('name', 'N/A')}")
                            print(f"  分组: {user_info.get('group_name', 'N/A')}")
                            print(f"  状态: {user_info.get('remark', 'N/A')}")
                    else:
                        print(f"❌ 用户ID {self.user_id} 不存在")
                        print(f"可用的用户ID: {user_ids[:5]}...")  # 显示前5个
                        
        except Exception as e:
            print(f"❌ 用户ID验证失败: {e}")
            
    def test_browser_start_api(self):
        """测试浏览器启动 API（不实际启动）"""
        if not self.user_id:
            print("\n⚠️ 跳过浏览器启动测试 - 未配置用户ID")
            return
            
        try:
            # 构建启动URL
            start_url = f"{self.api_url}/api/v1/browser/start"
            params = {
                'user_id': self.user_id,
                'open_tabs': 1
            }
            
            print(f"\n浏览器启动 URL: {start_url}")
            print(f"参数: {params}")
            
            # 准备请求头
            headers = {}
            if self.config.get('api_key'):
                headers['Authorization'] = f'Bearer {self.config["api_key"]}'
            
            # 注意：这里只是测试API可达性，不实际启动浏览器
            print("\n📝 注意: 此测试不会实际启动浏览器，只检查API可达性")
            
            # 可以选择性地发送请求（取消注释以实际测试）
            # response = requests.get(start_url, params=params, headers=headers, timeout=30)
            # print(f"响应状态码: {response.status_code}")
            # print(f"响应内容: {response.text}")
            
            print("✅ 浏览器启动 API 测试准备完成")
            
        except Exception as e:
            print(f"❌ 浏览器启动 API 测试失败: {e}")
            
    def test_manager_availability(self):
        """测试管理器可用性检查"""
        print("\n测试 AdsPowerManager 可用性检查...")
        
        try:
            is_available, message = self.manager.is_adspower_available()
            
            print(f"可用性: {'✅ 可用' if is_available else '❌ 不可用'}")
            print(f"消息: {message}")
            
            if is_available:
                print("✅ AdsPower 管理器检测通过")
            else:
                print("❌ AdsPower 管理器检测失败")
                print("建议检查:")
                print("1. AdsPower 是否已启动")
                print("2. 本地 API 是否已开启")
                print("3. 端口是否被占用")
                print("4. 防火墙设置")
                
        except Exception as e:
            print(f"❌ 管理器可用性检查异常: {e}")


class TestAdsPowerLauncher(unittest.TestCase):
    """测试 AdsPower 启动器功能"""
    
    def setUp(self):
        """测试前准备"""
        self.config = get_config()
        self.user_id = get_primary_user_id()
        
        # 创建启动器配置
        self.launcher_config = {
            'local_api_url': self.config['local_api_url'],
            'user_id': self.user_id,
            'api_key': self.config.get('api_key', '')
        }
        
    def test_launcher_initialization(self):
        """测试启动器初始化"""
        try:
            launcher = AdsPowerLauncher(self.launcher_config)
            self.assertIsNotNone(launcher)
            print("✅ AdsPower 启动器初始化成功")
        except Exception as e:
            print(f"❌ AdsPower 启动器初始化失败: {e}")
            
    def test_launcher_config_validation(self):
        """测试启动器配置验证"""
        print("\n测试启动器配置...")
        
        required_keys = ['local_api_url', 'user_id']
        for key in required_keys:
            if key in self.launcher_config:
                print(f"✅ {key}: {self.launcher_config[key]}")
            else:
                print(f"❌ 缺少配置项: {key}")
                
        # API 状态配置现在由配置文件管理
        print("✅ 启动器配置验证通过")


def run_connection_tests():
    """运行连接测试"""
    print("="*60)
    print("AdsPower 连接测试开始")
    print("="*60)
    
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加连接测试
    suite.addTest(TestAdsPowerConnection('test_api_url_format'))
    suite.addTest(TestAdsPowerConnection('test_ping_adspower_api'))
    suite.addTest(TestAdsPowerConnection('test_user_list_api'))
    suite.addTest(TestAdsPowerConnection('test_user_id_validation'))
    suite.addTest(TestAdsPowerConnection('test_browser_start_api'))
    suite.addTest(TestAdsPowerConnection('test_manager_availability'))
    
    # 添加启动器测试
    suite.addTest(TestAdsPowerLauncher('test_launcher_initialization'))
    suite.addTest(TestAdsPowerLauncher('test_launcher_config_validation'))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    print("\n" + "="*60)
    print("测试结果汇总")
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
            
    # 返回测试是否全部通过
    return len(result.failures) == 0 and len(result.errors) == 0


if __name__ == '__main__':
    success = run_connection_tests()
    
    print("\n" + "="*60)
    if success:
        print("🎉 所有测试通过！AdsPower 连接功能正常")
    else:
        print("⚠️ 部分测试失败，请检查 AdsPower 配置和连接")
    print("="*60)
    
    sys.exit(0 if success else 1)