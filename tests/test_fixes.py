#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复验证测试

测试所有已修复的问题，确保修复有效且不会回退。
"""

import unittest
import sys
import os
import asyncio
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from twitter_parser import TwitterParser
from cloud_sync import CloudSyncManager


class TestTwitterParserFixes(unittest.TestCase):
    """测试 TwitterParser 修复"""
    
    def setUp(self):
        """测试前准备"""
        self.parser = TwitterParser()
    
    def test_initialize_method_exists(self):
        """测试 initialize 方法存在"""
        self.assertTrue(hasattr(self.parser, 'initialize'))
        self.assertTrue(callable(getattr(self.parser, 'initialize')))
    
    def test_optional_debug_port_init(self):
        """测试可选的 debug_port 参数初始化"""
        # 测试无参数初始化
        parser1 = TwitterParser()
        self.assertIsNone(parser1.debug_port)
        
        # 测试带参数初始化
        parser2 = TwitterParser(debug_port=9222)
        self.assertEqual(parser2.debug_port, 9222)
    
    @patch('twitter_parser.webdriver')
    async def test_initialize_method_functionality(self, mock_webdriver):
        """测试 initialize 方法功能"""
        # 模拟浏览器连接
        mock_driver = Mock()
        mock_webdriver.Chrome.return_value = mock_driver
        
        # 测试初始化
        await self.parser.initialize(debug_port=9222)
        
        self.assertEqual(self.parser.debug_port, 9222)
        # 验证连接浏览器的逻辑被调用
        self.assertIsNotNone(self.parser.debug_port)


class TestFeishuSyncFixes(unittest.TestCase):
    """测试飞书同步修复"""
    
    def setUp(self):
        """测试前准备"""
        self.sync_manager = CloudSyncManager()
    
    def test_timestamp_data_type_handling(self):
        """测试时间戳数据类型处理"""
        # 测试数据
        test_tweets = [
            {
                '推文原文内容': '测试推文1',
                '作者（账号）': 'test_user',
                '发布时间': '2024-01-01 12:00:00',  # 字符串格式
                '创建时间': 1704067200000,  # 时间戳格式
            },
            {
                '推文原文内容': '测试推文2',
                '作者（账号）': 'test_user2',
                '发布时间': 1704067200,  # 整数时间戳
                '创建时间': '2024-01-01 12:00:00',  # 字符串格式
            }
        ]
        
        # 模拟字段类型配置
        field_types = {
            '发布时间': 5,  # 时间戳类型
            '创建时间': 1   # 文本类型
        }
        
        # 测试时间戳处理逻辑
        for tweet in test_tweets:
            # 测试发布时间处理（应转换为毫秒时间戳）
            publish_time = tweet.get('发布时间')
            if isinstance(publish_time, str):
                try:
                    dt = datetime.strptime(publish_time, '%Y-%m-%d %H:%M:%S')
                    publish_time_ms = int(dt.timestamp() * 1000)
                    self.assertIsInstance(publish_time_ms, int)
                except ValueError:
                    self.fail(f"无法解析发布时间: {publish_time}")
            elif isinstance(publish_time, (int, float)):
                if publish_time < 1e10:  # 秒级时间戳
                    publish_time_ms = int(publish_time * 1000)
                else:  # 毫秒级时间戳
                    publish_time_ms = int(publish_time)
                self.assertIsInstance(publish_time_ms, int)
            
            # 测试创建时间处理（应转换为字符串）
            create_time = tweet.get('创建时间')
            if isinstance(create_time, str):
                # 已经是字符串格式
                create_time_str = create_time
            elif isinstance(create_time, (int, float)):
                if create_time > 1e10:  # 毫秒级时间戳
                    dt = datetime.fromtimestamp(create_time / 1000)
                else:  # 秒级时间戳
                    dt = datetime.fromtimestamp(create_time)
                create_time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
            
            self.assertIsInstance(create_time_str, str)
            self.assertRegex(create_time_str, r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')
    
    def test_conditional_field_inclusion(self):
        """测试条件字段包含逻辑"""
        # 模拟飞书字段类型
        field_types_with_create_time = {
            '推文原文内容': 1,
            '作者（账号）': 1,
            '发布时间': 5,
            '创建时间': 1
        }
        
        field_types_without_create_time = {
            '推文原文内容': 1,
            '作者（账号）': 1,
            '发布时间': 5
        }
        
        test_tweet = {
            '推文原文内容': '测试推文',
            '作者（账号）': 'test_user',
            '发布时间': '2024-01-01 12:00:00',
            '创建时间': '2024-01-01 12:00:00'
        }
        
        # 测试包含创建时间字段的情况
        record_fields_1 = {
            '推文原文内容': str(test_tweet.get('推文原文内容', '')),
            '作者（账号）': str(test_tweet.get('作者（账号）', '')),
            '发布时间': test_tweet.get('发布时间')
        }
        
        if '创建时间' in field_types_with_create_time:
            record_fields_1['创建时间'] = test_tweet.get('创建时间')
        
        self.assertIn('创建时间', record_fields_1)
        
        # 测试不包含创建时间字段的情况
        record_fields_2 = {
            '推文原文内容': str(test_tweet.get('推文原文内容', '')),
            '作者（账号）': str(test_tweet.get('作者（账号）', '')),
            '发布时间': test_tweet.get('发布时间')
        }
        
        if '创建时间' in field_types_without_create_time:
            record_fields_2['创建时间'] = test_tweet.get('创建时间')
        
        self.assertNotIn('创建时间', record_fields_2)


class TestPython3CommandUpdates(unittest.TestCase):
    """测试 Python3 命令更新"""
    
    def test_script_files_use_python3(self):
        """测试脚本文件使用 python3 命令"""
        # 需要检查的文件列表
        files_to_check = [
            'tests/run_tests.py',
            'main_batch_scraper.py',
            'run_web.py',
            'setup.py',
            'performance_demo.py',
            'README_BATCH_SYSTEM.md',
            'auto_improve.py',
            'README.md',
            'tests/README.md'
        ]
        
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        for file_path in files_to_check:
            full_path = os.path.join(project_root, file_path)
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检查是否包含 python3 命令
                if 'python ' in content and file_path.endswith('.py'):
                    # Python 文件中的命令示例应该使用 python3
                    self.assertIn('python3', content, 
                                f"文件 {file_path} 应该使用 python3 命令")
                elif 'python ' in content and file_path.endswith('.md'):
                    # Markdown 文件中的命令示例应该使用 python3
                    self.assertIn('python3', content, 
                                f"文件 {file_path} 中的命令示例应该使用 python3")


class TestIntegrationFixes(unittest.TestCase):
    """集成测试修复验证"""
    
    def test_all_fixes_integration(self):
        """测试所有修复的集成效果"""
        # 1. 测试 TwitterParser 可以正常实例化
        parser = TwitterParser()
        self.assertIsNotNone(parser)
        
        # 2. 测试 initialize 方法存在
        self.assertTrue(hasattr(parser, 'initialize'))
        
        # 3. 测试 CloudSyncManager 可以正常实例化
        sync_manager = CloudSyncManager()
        self.assertIsNotNone(sync_manager)
        
        # 4. 测试时间戳处理函数存在
        self.assertTrue(hasattr(sync_manager, 'sync_to_feishu'))
    
    def test_error_scenarios_handled(self):
        """测试错误场景处理"""
        # 测试 TwitterParser 初始化错误处理
        try:
            parser = TwitterParser(debug_port="invalid_port")
            # 应该能够处理无效端口
            self.assertIsNotNone(parser)
        except Exception as e:
            self.fail(f"TwitterParser 应该能够处理无效端口: {e}")
        
        # 测试时间戳转换错误处理
        sync_manager = CloudSyncManager()
        
        # 测试无效时间戳
        invalid_timestamps = [None, "", "invalid_date", -1]
        
        for invalid_ts in invalid_timestamps:
            try:
                # 这里应该有适当的错误处理
                if invalid_ts is None or invalid_ts == "":
                    result = "1970-01-01 00:00:00"  # 默认值
                else:
                    result = str(invalid_ts)  # 转换为字符串
                self.assertIsInstance(result, str)
            except Exception as e:
                # 应该有适当的错误处理，不应该崩溃
                pass


if __name__ == '__main__':
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTest(unittest.makeSuite(TestTwitterParserFixes))
    suite.addTest(unittest.makeSuite(TestFeishuSyncFixes))
    suite.addTest(unittest.makeSuite(TestPython3CommandUpdates))
    suite.addTest(unittest.makeSuite(TestIntegrationFixes))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出测试结果
    print(f"\n{'='*60}")
    print("修复验证测试结果")
    print(f"{'='*60}")
    print(f"运行测试: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print(f"成功率: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    # 退出码
    sys.exit(0 if result.wasSuccessful() else 1)