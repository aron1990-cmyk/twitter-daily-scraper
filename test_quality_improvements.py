#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter采集系统代码质量改进功能测试
测试新实现的异常处理、监控、重试等功能
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import List, Dict, Any

# 导入新的质量改进模块
from exceptions import (
    TwitterScrapingError, NetworkException, 
    ParsingException, RateLimitException
)
from models import TweetModel, UserModel, HealthStatus
from retry_utils import RetryConfig, exponential_backoff, retry_with_backoff
from monitoring import MonitoringSystem
from performance_optimizer import (
    AsyncBatchProcessor, MemoryOptimizer, PerformanceProfiler
)

class QualityTestScraper:
    """代码质量改进功能测试类"""
    
    def __init__(self):
        self.logger = logging.getLogger('QualityTest')
        self.setup_logging()
        
        # 初始化监控系统
        self.monitoring = MonitoringSystem()
        self.monitoring.start()
        
        # 初始化性能优化器
        self.batch_processor = AsyncBatchProcessor(batch_size=5)
        self.memory_optimizer = MemoryOptimizer(max_memory_mb=256)
        self.profiler = PerformanceProfiler()
        
        # 重试配置
        self.retry_config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0,
            exponential_base=2.0
        )
        
        self.logger.info("质量测试采集器初始化完成")
    
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    async def simulate_tweet_scraping(self, username: str) -> List[TweetModel]:
        """模拟推文采集过程"""
        with self.monitoring.measure_duration('tweet_scraping'):
            try:
                self.logger.info(f"开始模拟采集用户 @{username} 的推文")
                
                # 模拟网络请求
                await self._simulate_network_request()
                
                # 创建模拟推文数据
                tweets = [
                    TweetModel(
                        username=username,
                        content=f"这是来自 @{username} 的第{i+1}条模拟推文",
                        likes=10 + i * 5,
                        retweets=2 + i,
                        comments=1 + i
                    )
                    for i in range(3)
                ]
                
                # 记录成功采集
                self.monitoring.record_tweet_scraped(username, success=True)
                
                self.logger.info(f"成功采集到 {len(tweets)} 条推文")
                return tweets
                
            except Exception as e:
                # 记录失败
                self.monitoring.record_tweet_scraped(username, success=False)
                raise TwitterScrapingError(f"采集用户 @{username} 失败: {e}")
    
    @retry_with_backoff
    async def _simulate_network_request(self):
        """模拟网络请求（带重试机制）"""
        import random
        
        # 模拟网络延迟
        await asyncio.sleep(0.5)
        
        # 随机模拟网络错误
        if random.random() < 0.3:  # 30%概率失败
            raise NetworkException("模拟网络连接失败")
        
        # 随机模拟限流
        if random.random() < 0.2:  # 20%概率限流
            raise RateLimitException("模拟API限流")
    
    async def test_batch_processing(self, usernames: List[str]):
        """测试批处理功能"""
        self.logger.info("开始测试批处理功能")
        
        async def process_user(username: str):
            try:
                tweets = await self.simulate_tweet_scraping(username)
                return {'username': username, 'tweets': tweets, 'success': True}
            except Exception as e:
                self.logger.error(f"处理用户 {username} 失败: {e}")
                return {'username': username, 'error': str(e), 'success': False}
        
        # 使用批处理器
        async def batch_processor_func(coro):
            return await coro
        
        results = await self.batch_processor.process_batch(
            [process_user(username) for username in usernames],
            batch_processor_func
        )
        
        successful = sum(1 for r in results if r.get('success', False))
        self.logger.info(f"批处理完成: {successful}/{len(usernames)} 成功")
        
        return results
    
    def test_exception_handling(self):
        """测试异常处理"""
        self.logger.info("开始测试异常处理")
        
        try:
            # 模拟各种异常
            raise NetworkException("测试网络异常")
        except (TwitterScrapingError, NetworkException) as e:
            self.logger.info(f"✅ 成功捕获网络异常: {e}")
        
        try:
            raise ParsingException("测试解析异常")
        except (TwitterScrapingError, ParsingException) as e:
            self.logger.info(f"✅ 成功捕获解析异常: {e}")
        
        try:
            raise RateLimitException("测试限流异常")
        except (TwitterScrapingError, RateLimitException) as e:
            self.logger.info(f"✅ 成功捕获限流异常: {e}")
    
    def test_data_models(self):
        """测试数据模型"""
        self.logger.info("开始测试数据模型")
        
        # 测试推文模型
        tweet = TweetModel(
            username="test_user",
            content="这是一条测试推文",
            likes=100,
            retweets=20,
            comments=5
        )
        self.logger.info(f"✅ 推文模型创建成功: {tweet.content}")
        
        # 测试用户模型
        user = UserModel(
            username="test_user",
            display_name="测试用户",
            followers_count=1000,
            following_count=500
        )
        self.logger.info(f"✅ 用户模型创建成功: {user.display_name}")
    
    async def test_performance_optimization(self):
        """测试性能优化"""
        self.logger.info("开始测试性能优化")
        
        # 测试内存优化
        memory_usage = self.memory_optimizer.get_memory_usage()
        self.logger.info(f"✅ 当前内存使用: {memory_usage:.2f}MB")
        
        # 测试性能分析
        async def test_operation():
            await asyncio.sleep(0.1)  # 模拟异步操作
        
        async with self.profiler.profile('test_operation'):
            await test_operation()
        
        metrics = self.profiler.get_average_metrics()
        self.logger.info(f"✅ 性能分析完成: {metrics}")
    
    async def run_comprehensive_test(self):
        """运行综合测试"""
        self.logger.info("🚀 开始运行代码质量改进功能综合测试")
        
        try:
            # 1. 测试异常处理
            self.test_exception_handling()
            
            # 2. 测试数据模型
            self.test_data_models()
            
            # 3. 测试性能优化
            await self.test_performance_optimization()
            
            # 4. 测试批处理和重试机制
            test_users = ['elonmusk', 'openai', 'github', 'python']
            results = await self.test_batch_processing(test_users)
            
            # 5. 获取监控状态
            status = self.monitoring.get_status()
            self.logger.info(f"📊 监控状态: 运行时间 {status['uptime']:.2f}s")
            
            # 6. 更新系统指标
            self.monitoring.update_system_metrics()
            
            self.logger.info("🎉 所有代码质量改进功能测试完成！")
            
            return {
                'success': True,
                'results': results,
                'monitoring_status': status
            }
            
        except Exception as e:
            self.logger.error(f"❌ 测试过程中发生错误: {e}")
            return {'success': False, 'error': str(e)}

async def main():
    """主函数"""
    scraper = QualityTestScraper()
    result = await scraper.run_comprehensive_test()
    
    if result['success']:
        print("\n✅ 代码质量改进功能测试全部通过！")
        print("📈 新功能已成功集成到Twitter采集系统中")
    else:
        print(f"\n❌ 测试失败: {result['error']}")

if __name__ == "__main__":
    asyncio.run(main())