#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
推文采集功能综合测试用例
测试各种采集场景和边界情况
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import List, Dict, Any
import pytest

# 导入测试所需的模块
from ads_browser_launcher import AdsPowerLauncher
from twitter_parser import TwitterParser
from human_behavior_simulator import HumanBehaviorSimulator
from config import BROWSER_CONFIG

class ComprehensiveScrapingTest:
    """推文采集综合测试类"""
    
    def __init__(self):
        self.logger = self.setup_logging()
        self.test_results = []
        self.browser_launcher = None
        self.parser = None
        
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('test_comprehensive_scraping.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    async def setup_browser(self):
        """初始化浏览器"""
        try:
            self.browser_launcher = AdsPowerLauncher()
            browser_info = self.browser_launcher.start_browser()
            
            if not browser_info:
                raise Exception("浏览器启动失败")
            
            debug_port = browser_info.get('ws', {}).get('puppeteer')
            if not debug_port:
                raise Exception("无法获取浏览器调试端口")
            
            self.parser = TwitterParser(debug_port)
            await self.parser.initialize()
            
            self.logger.info("✅ 浏览器初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 浏览器初始化失败: {e}")
            return False
    
    async def cleanup_browser(self):
        """清理浏览器资源"""
        try:
            if self.parser:
                await self.parser.close()
            if self.browser_launcher:
                self.browser_launcher.close_browser()
            self.logger.info("✅ 浏览器资源清理完成")
        except Exception as e:
            self.logger.error(f"❌ 浏览器清理失败: {e}")
    
    def record_test_result(self, test_name: str, success: bool, 
                          expected_count: int, actual_count: int, 
                          duration: float, error_msg: str = None):
        """记录测试结果"""
        result = {
            'test_name': test_name,
            'success': success,
            'expected_count': expected_count,
            'actual_count': actual_count,
            'duration': duration,
            'timestamp': datetime.now().isoformat(),
            'error_msg': error_msg
        }
        self.test_results.append(result)
        
        status = "✅ 通过" if success else "❌ 失败"
        self.logger.info(f"{status} {test_name}: 期望{expected_count}条，实际{actual_count}条，耗时{duration:.2f}秒")
        if error_msg:
            self.logger.error(f"错误信息: {error_msg}")
    
    async def test_user_profile_scraping(self):
        """测试用户个人资料页面采集"""
        test_cases = [
            {'username': 'elonmusk', 'max_tweets': 5, 'description': '知名用户少量推文'},
            {'username': 'elonmusk', 'max_tweets': 20, 'description': '知名用户中等数量推文'},
            {'username': 'elonmusk', 'max_tweets': 50, 'description': '知名用户大量推文'},
        ]
        
        for case in test_cases:
            start_time = time.time()
            try:
                self.logger.info(f"🧪 开始测试: {case['description']}")
                
                tweets = await self.parser.scrape_user_tweets(
                    username=case['username'],
                    max_tweets=case['max_tweets']
                )
                
                duration = time.time() - start_time
                actual_count = len(tweets)
                
                # 判断测试是否成功（允许一定的误差范围）
                success = actual_count >= min(case['max_tweets'] * 0.6, 5)  # 至少60%或5条
                
                self.record_test_result(
                    test_name=f"用户采集-{case['description']}",
                    success=success,
                    expected_count=case['max_tweets'],
                    actual_count=actual_count,
                    duration=duration
                )
                
                # 验证推文数据质量
                if tweets:
                    self.validate_tweet_data_quality(tweets, f"用户采集-{case['description']}")
                
            except Exception as e:
                duration = time.time() - start_time
                self.record_test_result(
                    test_name=f"用户采集-{case['description']}",
                    success=False,
                    expected_count=case['max_tweets'],
                    actual_count=0,
                    duration=duration,
                    error_msg=str(e)
                )
    
    async def test_keyword_search_scraping(self):
        """测试关键词搜索采集"""
        test_cases = [
            {'keyword': 'AI', 'max_tweets': 10, 'description': '热门关键词'},
            {'keyword': 'Python', 'max_tweets': 15, 'description': '技术关键词'},
            {'keyword': '人工智能', 'max_tweets': 8, 'description': '中文关键词'},
            {'keyword': 'veryrareuncommonkeyword123', 'max_tweets': 5, 'description': '罕见关键词'},
        ]
        
        for case in test_cases:
            start_time = time.time()
            try:
                self.logger.info(f"🧪 开始测试: {case['description']}")
                
                tweets = await self.parser.scrape_keyword_tweets(
                    keyword=case['keyword'],
                    max_tweets=case['max_tweets']
                )
                
                duration = time.time() - start_time
                actual_count = len(tweets)
                
                # 对于罕见关键词，允许结果为0
                if case['keyword'] == 'veryrareuncommonkeyword123':
                    success = True  # 罕见关键词测试主要验证不会崩溃
                else:
                    success = actual_count >= min(case['max_tweets'] * 0.4, 3)  # 至少40%或3条
                
                self.record_test_result(
                    test_name=f"关键词采集-{case['description']}",
                    success=success,
                    expected_count=case['max_tweets'],
                    actual_count=actual_count,
                    duration=duration
                )
                
                # 验证推文数据质量
                if tweets:
                    self.validate_tweet_data_quality(tweets, f"关键词采集-{case['description']}")
                
            except Exception as e:
                duration = time.time() - start_time
                self.record_test_result(
                    test_name=f"关键词采集-{case['description']}",
                    success=False,
                    expected_count=case['max_tweets'],
                    actual_count=0,
                    duration=duration,
                    error_msg=str(e)
                )
    
    async def test_user_keyword_combined_scraping(self):
        """测试用户+关键词组合采集"""
        test_cases = [
            {'username': 'elonmusk', 'keyword': 'Tesla', 'max_tweets': 8, 'description': '用户特定关键词'},
            {'username': 'elonmusk', 'keyword': 'AI', 'max_tweets': 5, 'description': '用户AI相关推文'},
        ]
        
        for case in test_cases:
            start_time = time.time()
            try:
                self.logger.info(f"🧪 开始测试: {case['description']}")
                
                tweets = await self.parser.scrape_user_keyword_tweets(
                    username=case['username'],
                    keyword=case['keyword'],
                    max_tweets=case['max_tweets']
                )
                
                duration = time.time() - start_time
                actual_count = len(tweets)
                
                # 组合搜索可能结果较少，降低期望
                success = actual_count >= min(case['max_tweets'] * 0.3, 2)  # 至少30%或2条
                
                self.record_test_result(
                    test_name=f"组合采集-{case['description']}",
                    success=success,
                    expected_count=case['max_tweets'],
                    actual_count=actual_count,
                    duration=duration
                )
                
                # 验证推文数据质量
                if tweets:
                    self.validate_tweet_data_quality(tweets, f"组合采集-{case['description']}")
                
            except Exception as e:
                duration = time.time() - start_time
                self.record_test_result(
                    test_name=f"组合采集-{case['description']}",
                    success=False,
                    expected_count=case['max_tweets'],
                    actual_count=0,
                    duration=duration,
                    error_msg=str(e)
                )
    
    async def test_edge_cases(self):
        """测试边界情况"""
        edge_cases = [
            {'test_type': 'zero_tweets', 'max_tweets': 0, 'description': '零推文请求'},
            {'test_type': 'large_number', 'max_tweets': 100, 'description': '大数量推文请求'},
            {'test_type': 'invalid_user', 'username': 'thisuserdoesnotexist12345', 'max_tweets': 5, 'description': '不存在的用户'},
        ]
        
        for case in edge_cases:
            start_time = time.time()
            try:
                self.logger.info(f"🧪 开始测试边界情况: {case['description']}")
                
                if case['test_type'] == 'zero_tweets':
                    tweets = await self.parser.scrape_user_tweets(
                        username='elonmusk',
                        max_tweets=case['max_tweets']
                    )
                elif case['test_type'] == 'large_number':
                    tweets = await self.parser.scrape_user_tweets(
                        username='elonmusk',
                        max_tweets=case['max_tweets']
                    )
                elif case['test_type'] == 'invalid_user':
                    tweets = await self.parser.scrape_user_tweets(
                        username=case['username'],
                        max_tweets=case['max_tweets']
                    )
                
                duration = time.time() - start_time
                actual_count = len(tweets)
                
                # 边界情况的成功标准
                if case['test_type'] == 'zero_tweets':
                    success = actual_count == 0
                elif case['test_type'] == 'large_number':
                    success = actual_count >= 20  # 大数量请求至少应该获得20条
                elif case['test_type'] == 'invalid_user':
                    success = actual_count == 0  # 不存在的用户应该返回0条
                
                self.record_test_result(
                    test_name=f"边界测试-{case['description']}",
                    success=success,
                    expected_count=case['max_tweets'],
                    actual_count=actual_count,
                    duration=duration
                )
                
            except Exception as e:
                duration = time.time() - start_time
                # 对于某些边界情况，异常是预期的
                if case['test_type'] == 'invalid_user':
                    success = True  # 不存在用户抛异常是正常的
                else:
                    success = False
                
                self.record_test_result(
                    test_name=f"边界测试-{case['description']}",
                    success=success,
                    expected_count=case['max_tweets'],
                    actual_count=0,
                    duration=duration,
                    error_msg=str(e)
                )
    
    def validate_tweet_data_quality(self, tweets: List[Dict], test_name: str):
        """验证推文数据质量"""
        quality_issues = []
        
        for i, tweet in enumerate(tweets):
            # 检查必要字段
            required_fields = ['username', 'content', 'likes', 'comments', 'retweets']
            for field in required_fields:
                if field not in tweet or tweet[field] is None:
                    quality_issues.append(f"推文{i+1}缺少字段: {field}")
            
            # 检查数据类型
            if 'likes' in tweet and not isinstance(tweet['likes'], int):
                quality_issues.append(f"推文{i+1}点赞数类型错误")
            
            if 'content' in tweet and not isinstance(tweet['content'], str):
                quality_issues.append(f"推文{i+1}内容类型错误")
            
            # 检查内容是否为空
            if 'content' in tweet and not tweet['content'].strip():
                quality_issues.append(f"推文{i+1}内容为空")
        
        if quality_issues:
            self.logger.warning(f"⚠️ {test_name} 数据质量问题: {'; '.join(quality_issues[:5])}")
        else:
            self.logger.info(f"✅ {test_name} 数据质量良好")
    
    async def test_performance_metrics(self):
        """测试性能指标"""
        self.logger.info("🧪 开始性能测试")
        
        # 测试单条推文平均处理时间
        start_time = time.time()
        tweets = await self.parser.scrape_user_tweets(
            username='elonmusk',
            max_tweets=10
        )
        duration = time.time() - start_time
        
        if tweets:
            avg_time_per_tweet = duration / len(tweets)
            self.logger.info(f"📊 平均每条推文处理时间: {avg_time_per_tweet:.2f}秒")
            
            # 性能标准：每条推文处理时间不超过5秒
            performance_ok = avg_time_per_tweet <= 5.0
            
            self.record_test_result(
                test_name="性能测试-处理速度",
                success=performance_ok,
                expected_count=10,
                actual_count=len(tweets),
                duration=duration
            )
    
    def generate_test_report(self):
        """生成测试报告"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        report = {
            'test_summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'success_rate': f"{(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%",
                'test_time': datetime.now().isoformat()
            },
            'detailed_results': self.test_results
        }
        
        # 保存报告到文件
        with open('comprehensive_scraping_test_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 打印摘要
        self.logger.info("\n" + "="*50)
        self.logger.info("📋 测试报告摘要")
        self.logger.info("="*50)
        self.logger.info(f"总测试数: {total_tests}")
        self.logger.info(f"通过测试: {passed_tests}")
        self.logger.info(f"失败测试: {failed_tests}")
        self.logger.info(f"成功率: {(passed_tests/total_tests*100):.1f}%")
        self.logger.info("="*50)
        
        return report
    
    async def run_all_tests(self):
        """运行所有测试"""
        self.logger.info("🚀 开始推文采集功能综合测试")
        
        # 初始化浏览器
        if not await self.setup_browser():
            self.logger.error("❌ 浏览器初始化失败，测试终止")
            return
        
        try:
            # 运行各类测试
            await self.test_user_profile_scraping()
            await asyncio.sleep(2)  # 测试间隔
            
            await self.test_keyword_search_scraping()
            await asyncio.sleep(2)
            
            await self.test_user_keyword_combined_scraping()
            await asyncio.sleep(2)
            
            await self.test_edge_cases()
            await asyncio.sleep(2)
            
            await self.test_performance_metrics()
            
        except Exception as e:
            self.logger.error(f"❌ 测试执行过程中发生错误: {e}")
        
        finally:
            # 清理资源
            await self.cleanup_browser()
            
            # 生成报告
            report = self.generate_test_report()
            
            self.logger.info("✅ 测试完成，报告已保存到 comprehensive_scraping_test_report.json")
            
            return report

# 主函数
async def main():
    """主测试函数"""
    test_runner = ComprehensiveScrapingTest()
    await test_runner.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())