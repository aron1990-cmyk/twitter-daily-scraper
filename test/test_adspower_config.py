# -*- coding: utf-8 -*-
"""
AdsPower 配置测试脚本
测试 AdsPower 配置相关功能
"""

import sys
import os
import unittest
import json
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.adspower_config import (
    ADSPOWER_CONFIG,
    get_api_url,
    get_config,
    get_primary_user_id,
    get_all_user_ids
)
from utils.adspower_manager import AdsPowerConfig, AdsPowerManager


class TestAdsPowerConfig(unittest.TestCase):
    """测试 AdsPower 配置功能"""
    
    def test_default_config_values(self):
        """测试默认配置值"""
        self.assertEqual(ADSPOWER_CONFIG['api_host'], '127.0.0.1')
        self.assertEqual(ADSPOWER_CONFIG['api_port'], 50325)
        self.assertIsInstance(ADSPOWER_CONFIG['user_ids'], list)
        self.assertFalse(ADSPOWER_CONFIG['headless'])
        self.assertEqual(ADSPOWER_CONFIG['max_concurrent_tasks'], 2)
        self.assertEqual(ADSPOWER_CONFIG['task_timeout'], 900)
        
    def test_get_api_url(self):
        """测试 API URL 生成"""
        expected_url = f"http://{ADSPOWER_CONFIG['api_host']}:{ADSPOWER_CONFIG['api_port']}"
        self.assertEqual(get_api_url(), expected_url)
        
    def test_get_config(self):
        """测试配置获取"""
        config = get_config()
        self.assertIn('local_api_url', config)
        self.assertEqual(config['api_host'], ADSPOWER_CONFIG['api_host'])
        self.assertEqual(config['api_port'], ADSPOWER_CONFIG['api_port'])
        
    def test_get_primary_user_id(self):
        """测试主用户ID获取"""
        if ADSPOWER_CONFIG['user_ids']:
            self.assertEqual(get_primary_user_id(), ADSPOWER_CONFIG['user_ids'][0])
        else:
            self.assertEqual(get_primary_user_id(), '')
            
    def test_get_all_user_ids(self):
        """测试所有用户ID获取"""
        user_ids = get_all_user_ids()
        self.assertIsInstance(user_ids, list)
        self.assertEqual(user_ids, ADSPOWER_CONFIG['user_ids'])
        
    def test_config_validation(self):
        """测试配置验证"""
        # 检查必要的配置项
        required_keys = ['api_host', 'api_port', 'user_ids', 'headless']
        for key in required_keys:
            self.assertIn(key, ADSPOWER_CONFIG)
            
        # 检查数据类型
        self.assertIsInstance(ADSPOWER_CONFIG['api_host'], str)
        self.assertIsInstance(ADSPOWER_CONFIG['api_port'], int)
        self.assertIsInstance(ADSPOWER_CONFIG['user_ids'], list)
        self.assertIsInstance(ADSPOWER_CONFIG['headless'], bool)


class TestAdsPowerConfigClass(unittest.TestCase):
    """测试 AdsPowerConfig 数据类"""
    
    def test_default_values(self):
        """测试默认值"""
        config = AdsPowerConfig()
        self.assertEqual(config.host, "localhost")
        self.assertEqual(config.port, 50325)
        self.assertFalse(config.headless)
        self.assertEqual(config.user_ids, [])
        self.assertEqual(config.api_key, "")
        
    def test_api_url_property(self):
        """测试 API URL 属性"""
        config = AdsPowerConfig(host="127.0.0.1", port=50325)
        expected_url = "http://127.0.0.1:50325"
        self.assertEqual(config.api_url, expected_url)
        
    def test_to_dict(self):
        """测试转换为字典"""
        config = AdsPowerConfig(
            host="localhost",
            port=50325,
            headless=True,
            user_ids=["test_id"],
            api_key="test_key"
        )
        config_dict = config.to_dict()
        
        self.assertEqual(config_dict['host'], "localhost")
        self.assertEqual(config_dict['port'], 50325)
        self.assertTrue(config_dict['headless'])
        self.assertEqual(config_dict['user_ids'], ["test_id"])
        self.assertEqual(config_dict['api_key'], "test_key")
        
    def test_from_dict(self):
        """测试从字典创建配置"""
        data = {
            'host': '192.168.1.100',
            'port': 8080,
            'headless': True,
            'user_ids': ['user1', 'user2'],
            'api_key': 'secret_key'
        }
        
        config = AdsPowerConfig.from_dict(data)
        self.assertEqual(config.host, '192.168.1.100')
        self.assertEqual(config.port, 8080)
        self.assertTrue(config.headless)
        self.assertEqual(config.user_ids, ['user1', 'user2'])
        self.assertEqual(config.api_key, 'secret_key')


class TestAdsPowerManager(unittest.TestCase):
    """测试 AdsPowerManager 类"""
    
    def setUp(self):
        """测试前准备"""
        self.manager = AdsPowerManager()
        
    def test_manager_initialization(self):
        """测试管理器初始化"""
        self.assertIsNotNone(self.manager)
        self.assertIsNotNone(self.manager.logger)
        
    @patch('utils.adspower_manager.requests.get')
    def test_check_availability_success(self, mock_get):
        """测试可用性检查 - 成功情况"""
        # 模拟成功响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'code': 0, 'msg': 'success'}
        mock_get.return_value = mock_response
        
        is_available, message = self.manager.is_adspower_available()
        self.assertTrue(is_available)
        self.assertIn('运行正常', message)
        
    @patch('utils.adspower_manager.requests.get')
    def test_check_availability_connection_error(self, mock_get):
        """测试可用性检查 - 连接错误"""
        # 模拟连接错误
        mock_get.side_effect = ConnectionError("Connection refused")
        
        is_available, message = self.manager.is_adspower_available()
        self.assertFalse(is_available)
        self.assertIn('检查失败', message)
        
    @patch('utils.adspower_manager.requests.get')
    def test_check_availability_timeout(self, mock_get):
        """测试可用性检查 - 超时"""
        # 模拟超时
        from requests.exceptions import Timeout
        mock_get.side_effect = Timeout("Request timeout")
        
        is_available, message = self.manager.is_adspower_available()
        self.assertFalse(is_available)
        self.assertIn('连接超时', message)
        
    @patch('utils.adspower_manager.requests.get')
    def test_check_availability_api_error(self, mock_get):
        """测试可用性检查 - API错误"""
        # 模拟API错误响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'code': -1, 'msg': 'API Error'}
        mock_get.return_value = mock_response
        
        is_available, message = self.manager.is_adspower_available()
        self.assertFalse(is_available)
        self.assertIn('AdsPower状态异常', message)
        
    @patch('utils.adspower_manager.requests.get')
    def test_check_availability_http_error(self, mock_get):
        """测试可用性检查 - HTTP错误"""
        # 模拟HTTP错误
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        is_available, message = self.manager.is_adspower_available()
        self.assertFalse(is_available)
        self.assertIn('HTTP错误', message)


if __name__ == '__main__':
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加配置测试
    suite.addTest(unittest.makeSuite(TestAdsPowerConfig))
    suite.addTest(unittest.makeSuite(TestAdsPowerConfigClass))
    suite.addTest(unittest.makeSuite(TestAdsPowerManager))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出测试结果
    print(f"\n测试完成:")
    print(f"运行测试: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
            
    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")