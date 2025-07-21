#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强的Twitter解析器
集成优化的滚动和抓取逻辑，支持每次滚动完成后立即抓取
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

from twitter_parser import TwitterParser
from optimized_scraping_engine import OptimizedScrapingEngine
from config import BROWSER_CONFIG


class EnhancedTwitterParser(TwitterParser):
    """
    增强的Twitter解析器
    集成优化抓取引擎，实现每次滚动完成后立即抓取并保存数据
    """
    
    def __init__(self, user_id: str, window_id: str, scraping_engine: OptimizedScrapingEngine):
        # 正确初始化父类，不传递参数
        super().__init__()
        self.user_id = user_id
        self.window_id = window_id
        self.scraping_engine = scraping_engine
        self.current_task_id: Optional[str] = None
        self.scroll_count = 0
        self.last_tweet_count = 0
        
        # 注册到抓取引擎
        self.scraping_engine.register_window_parser(self.window_id, self)
        
        self.logger.info(f"增强Twitter解析器已初始化 (窗口: {window_id})")
    
    async def initialize_with_debug_port(self, debug_port: str):
        """使用调试端口初始化解析器"""
        try:
            await self.initialize(debug_port)
            self.logger.info(f"窗口 {self.window_id} 的解析器已成功连接到浏览器")
        except Exception as e:
            self.logger.error(f"窗口 {self.window_id} 的解析器初始化失败: {e}")
            raise
    
    async def enhanced_scrape_user_tweets(self, username: str, max_tweets: int = 10, 
                                        enable_enhanced: bool = False) -> List[Dict[str, Any]]:
        """增强的用户推文抓取"""
        try:
            # 创建抓取任务
            task_id = f"user_{username}_{self.window_id}_{int(time.time())}"
            task = self.scraping_engine.create_scraping_task(
                task_id=task_id,
                window_id=self.window_id,
                target_type='user',
                target_value=username,
                max_tweets=max_tweets,
                enable_enhanced=enable_enhanced
            )
            
            self.current_task_id = task_id
            self.scroll_count = 0
            self.last_tweet_count = 0
            
            self.logger.info(f"开始增强抓取用户 @{username} 的推文 (任务: {task_id})")
            
            # 导航到用户页面
            await self.navigate_to_profile(username)
            
            # 使用优化的滚动和抓取策略
            await self._enhanced_scroll_and_scrape(max_tweets)
            
            # 获取最终结果
            final_task = self.scraping_engine.active_tasks.get(task_id)
            if final_task:
                tweets = final_task.tweets_collected
                self.scraping_engine.complete_task(task_id)
                
                # 为每条推文添加来源信息
                for tweet in tweets:
                    tweet['source'] = f'@{username}'
                    tweet['source_type'] = 'user_profile'
                
                self.logger.info(f"增强抓取完成，共获得 {len(tweets)} 条推文")
                return tweets
            
            return []
            
        except Exception as e:
            self.logger.error(f"增强抓取用户 @{username} 失败: {e}")
            if self.current_task_id:
                self.scraping_engine.cancel_task(self.current_task_id)
            return []
    
    async def enhanced_scrape_keyword_tweets(self, keyword: str, max_tweets: int = 10, 
                                           enable_enhanced: bool = False) -> List[Dict[str, Any]]:
        """增强的关键词推文抓取"""
        try:
            # 创建抓取任务
            task_id = f"keyword_{keyword}_{self.window_id}_{int(time.time())}"
            task = self.scraping_engine.create_scraping_task(
                task_id=task_id,
                window_id=self.window_id,
                target_type='keyword',
                target_value=keyword,
                max_tweets=max_tweets,
                enable_enhanced=enable_enhanced
            )
            
            self.current_task_id = task_id
            self.scroll_count = 0
            self.last_tweet_count = 0
            
            self.logger.info(f"开始增强抓取关键词 '{keyword}' 的推文 (任务: {task_id})")
            
            # 搜索关键词
            await self.search_tweets(keyword)
            
            # 使用优化的滚动和抓取策略
            await self._enhanced_scroll_and_scrape(max_tweets)
            
            # 获取最终结果
            final_task = self.scraping_engine.active_tasks.get(task_id)
            if final_task:
                tweets = final_task.tweets_collected
                self.scraping_engine.complete_task(task_id)
                
                # 为每条推文添加来源信息
                for tweet in tweets:
                    tweet['source'] = keyword
                    tweet['source_type'] = 'keyword_search'
                
                self.logger.info(f"增强抓取完成，共获得 {len(tweets)} 条推文")
                return tweets
            
            return []
            
        except Exception as e:
            self.logger.error(f"增强抓取关键词 '{keyword}' 失败: {e}")
            if self.current_task_id:
                self.scraping_engine.cancel_task(self.current_task_id)
            return []
    
    async def enhanced_scrape_user_keyword_tweets(self, username: str, keyword: str, 
                                                max_tweets: int = 10, enable_enhanced: bool = False) -> List[Dict[str, Any]]:
        """增强的用户关键词推文抓取"""
        try:
            # 创建抓取任务
            task_id = f"user_keyword_{username}_{keyword}_{self.window_id}_{int(time.time())}"
            task = self.scraping_engine.create_scraping_task(
                task_id=task_id,
                window_id=self.window_id,
                target_type='user_keyword',
                target_value=f"{username}+{keyword}",
                max_tweets=max_tweets,
                enable_enhanced=enable_enhanced
            )
            
            self.current_task_id = task_id
            self.scroll_count = 0
            self.last_tweet_count = 0
            
            self.logger.info(f"开始增强抓取用户 @{username} 关键词 '{keyword}' 的推文 (任务: {task_id})")
            
            # 构建搜索URL
            import urllib.parse
            search_query = f"from:{username} {keyword}"
            search_url = f'https://x.com/search?q={urllib.parse.quote(search_query)}&src=typed_query&f=live'
            
            # 导航到搜索页面
            await self.page.goto(search_url, timeout=BROWSER_CONFIG['timeout'])
            await self.page.wait_for_load_state('domcontentloaded', timeout=10000)
            await self.ensure_page_focus()
            await asyncio.sleep(1)
            
            # 使用优化的滚动和抓取策略
            await self._enhanced_scroll_and_scrape(max_tweets)
            
            # 获取最终结果
            final_task = self.scraping_engine.active_tasks.get(task_id)
            if final_task:
                tweets = final_task.tweets_collected
                self.scraping_engine.complete_task(task_id)
                
                # 为每条推文添加来源信息
                for tweet in tweets:
                    tweet['source'] = f"@{username} + {keyword}"
                    tweet['source_type'] = 'user_keyword_search'
                    tweet['target_username'] = username
                    tweet['target_keyword'] = keyword
                
                self.logger.info(f"增强抓取完成，共获得 {len(tweets)} 条推文")
                return tweets
            
            return []
            
        except Exception as e:
            self.logger.error(f"增强抓取用户 @{username} 关键词 '{keyword}' 失败: {e}")
            if self.current_task_id:
                self.scraping_engine.cancel_task(self.current_task_id)
            return []
    
    async def _enhanced_scroll_and_scrape(self, max_tweets: int):
        """增强的滚动和抓取逻辑"""
        try:
            self.logger.info(f"开始增强滚动和抓取，目标: {max_tweets} 条推文")
            
            # 等待初始内容加载
            await asyncio.sleep(1)
            
            # 获取当前任务
            task = self.scraping_engine.active_tasks.get(self.current_task_id)
            if not task:
                raise Exception(f"任务 {self.current_task_id} 不存在")
            
            scroll_attempts = 0
            max_scroll_attempts = max_tweets * 3  # 最大滚动次数
            stagnant_count = 0
            
            while len(task.tweets_collected) < max_tweets and scroll_attempts < max_scroll_attempts:
                # 获取当前推文数量
                current_tweets = await self.page.query_selector_all('[data-testid="tweet"]')
                current_tweet_count = len(current_tweets)
                
                # 检查是否有新推文
                if current_tweet_count == self.last_tweet_count:
                    stagnant_count += 1
                else:
                    stagnant_count = 0
                
                self.last_tweet_count = current_tweet_count
                
                # 每次滚动前都触发抓取事件（确保每次滚动都保存数据）
                self.scraping_engine.trigger_scroll_event(
                    window_id=self.window_id,
                    task_id=self.current_task_id,
                    scroll_count=self.scroll_count,
                    tweets_found=current_tweet_count
                )
                
                # 等待抓取完成
                await asyncio.sleep(0.5)
                
                # 获取当前滚动位置
                current_scroll_position = await self.page.evaluate("window.pageYOffset")
                
                # 如果连续多次没有新内容，使用激进滚动
                if stagnant_count >= 3:
                    scroll_distance = 3000
                    wait_time = 1.0
                    self.logger.debug("启用激进滚动模式")
                else:
                    scroll_distance = 1500
                    wait_time = 0.5
                
                # 执行滚动
                await self.ensure_page_focus()
                await self.page.evaluate(f'window.scrollBy(0, {scroll_distance})')
                await asyncio.sleep(wait_time)
                
                # 检查滚动后的位置
                new_scroll_position = await self.page.evaluate("window.pageYOffset")
                
                # 如果滚动位置没有变化，说明已到底部
                if abs(new_scroll_position - current_scroll_position) < 50:
                    self.logger.info("检测到滚动位置无变化，可能已到达页面底部")
                    stagnant_count += 2  # 加速退出条件
                
                self.scroll_count += 1
                scroll_attempts += 1
                
                # 滚动完成后再次触发抓取事件（确保滚动后的新内容被抓取）
                post_scroll_tweets = await self.page.query_selector_all('[data-testid="tweet"]')
                post_scroll_count = len(post_scroll_tweets)
                
                self.scraping_engine.trigger_scroll_event(
                    window_id=self.window_id,
                    task_id=self.current_task_id,
                    scroll_count=self.scroll_count,
                    tweets_found=post_scroll_count
                )
                
                # 等待滚动后抓取完成
                await asyncio.sleep(0.5)
                
                # 检查任务进度
                if len(task.tweets_collected) >= max_tweets:
                    self.logger.info(f"已达到目标推文数量: {len(task.tweets_collected)}")
                    break
                
                # 如果长时间没有新内容，退出循环
                if stagnant_count >= 8:
                    self.logger.info("长时间无新内容，停止滚动")
                    break
            
            # 最后一次抓取
            final_tweets = await self.page.query_selector_all('[data-testid="tweet"]')
            if len(final_tweets) > self.last_tweet_count:
                self.scraping_engine.trigger_scroll_event(
                    window_id=self.window_id,
                    task_id=self.current_task_id,
                    scroll_count=self.scroll_count,
                    tweets_found=len(final_tweets)
                )
                # 等待最后的抓取完成
                await asyncio.sleep(1)
            
            self.logger.info(f"增强滚动完成，总滚动次数: {self.scroll_count}，最终推文数: {len(task.tweets_collected)}")
            
        except Exception as e:
            self.logger.error(f"增强滚动和抓取失败: {e}")
            raise
    
    def get_current_task_status(self) -> Optional[Dict[str, Any]]:
        """获取当前任务状态"""
        if not self.current_task_id:
            return None
        return self.scraping_engine.get_task_status(self.current_task_id)
    
    def set_scroll_callback(self, callback: Callable):
        """设置滚动回调函数"""
        self.scraping_engine.on_scroll_complete = callback
    
    def set_scraping_callback(self, callback: Callable):
        """设置抓取回调函数"""
        self.scraping_engine.on_tweets_scraped = callback
    
    def set_saving_callback(self, callback: Callable):
        """设置保存回调函数"""
        self.scraping_engine.on_data_saved = callback


class MultiWindowEnhancedScraper:
    """
    多窗口增强抓取器
    管理多个窗口的并发抓取任务
    """
    
    def __init__(self, max_workers: int = 4):
        self.logger = logging.getLogger(__name__)
        self.scraping_engine = OptimizedScrapingEngine(max_workers=max_workers)
        self.window_parsers: Dict[str, EnhancedTwitterParser] = {}
        self.active_tasks: Dict[str, str] = {}  # task_id -> window_id
        
        # 启动抓取引擎
        self.scraping_engine.start_engine()
        
        self.logger.info(f"多窗口增强抓取器已初始化，最大工作线程: {max_workers}")
    
    def add_window_parser(self, window_id: str, user_id: str) -> EnhancedTwitterParser:
        """添加窗口解析器"""
        parser = EnhancedTwitterParser(user_id, window_id, self.scraping_engine)
        self.window_parsers[window_id] = parser
        
        self.logger.info(f"添加窗口解析器: {window_id} (用户: {user_id})")
        return parser
    
    async def scrape_multiple_targets(self, scraping_configs: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        并发抓取多个目标
        
        Args:
            scraping_configs: 抓取配置列表，每个配置包含:
                - window_id: 窗口ID
                - target_type: 目标类型 ('user', 'keyword', 'user_keyword')
                - target_value: 目标值
                - max_tweets: 最大推文数
                - enable_enhanced: 是否启用增强抓取
        
        Returns:
            各窗口的抓取结果
        """
        try:
            self.logger.info(f"开始并发抓取 {len(scraping_configs)} 个目标")
            
            # 创建抓取任务
            tasks = []
            for config in scraping_configs:
                window_id = config['window_id']
                parser = self.window_parsers.get(window_id)
                
                if not parser:
                    self.logger.error(f"窗口 {window_id} 的解析器不存在")
                    continue
                
                # 根据目标类型创建不同的抓取任务
                if config['target_type'] == 'user':
                    task = parser.enhanced_scrape_user_tweets(
                        username=config['target_value'],
                        max_tweets=config.get('max_tweets', 10),
                        enable_enhanced=config.get('enable_enhanced', False)
                    )
                elif config['target_type'] == 'keyword':
                    task = parser.enhanced_scrape_keyword_tweets(
                        keyword=config['target_value'],
                        max_tweets=config.get('max_tweets', 10),
                        enable_enhanced=config.get('enable_enhanced', False)
                    )
                elif config['target_type'] == 'user_keyword':
                    username, keyword = config['target_value'].split('+', 1)
                    task = parser.enhanced_scrape_user_keyword_tweets(
                        username=username,
                        keyword=keyword,
                        max_tweets=config.get('max_tweets', 10),
                        enable_enhanced=config.get('enable_enhanced', False)
                    )
                else:
                    self.logger.error(f"不支持的目标类型: {config['target_type']}")
                    continue
                
                tasks.append((window_id, task))
            
            # 并发执行所有任务
            results = {}
            completed_tasks = await asyncio.gather(
                *[task for _, task in tasks],
                return_exceptions=True
            )
            
            # 处理结果
            for i, (window_id, _) in enumerate(tasks):
                result = completed_tasks[i]
                if isinstance(result, Exception):
                    self.logger.error(f"窗口 {window_id} 抓取失败: {result}")
                    results[window_id] = []
                else:
                    results[window_id] = result
            
            # 统计结果
            total_tweets = sum(len(tweets) for tweets in results.values())
            self.logger.info(f"并发抓取完成，共获得 {total_tweets} 条推文")
            
            return results
            
        except Exception as e:
            self.logger.error(f"并发抓取失败: {e}")
            return {}
    
    def get_all_tasks_status(self) -> Dict[str, Any]:
        """获取所有任务状态"""
        return {
            'engine_stats': self.scraping_engine.get_engine_stats(),
            'tasks': self.scraping_engine.get_all_tasks_status(),
            'windows': list(self.window_parsers.keys())
        }
    
    def cleanup(self):
        """清理资源"""
        self.scraping_engine.cleanup_completed_tasks()
        self.scraping_engine.stop_engine()
        
        for parser in self.window_parsers.values():
            try:
                if hasattr(parser, 'cleanup'):
                    asyncio.create_task(parser.cleanup())
            except Exception as e:
                self.logger.warning(f"清理解析器失败: {e}")
        
        self.logger.info("多窗口增强抓取器已清理")


if __name__ == "__main__":
    # 测试代码
    import asyncio
    logging.basicConfig(level=logging.INFO)
    
    async def test_enhanced_scraper():
        scraper = MultiWindowEnhancedScraper(max_workers=2)
        
        # 模拟添加窗口解析器
        parser1 = scraper.add_window_parser("window_1", "user_1")
        parser2 = scraper.add_window_parser("window_2", "user_2")
        
        print(f"抓取器状态: {scraper.get_all_tasks_status()}")
        
        # 模拟抓取配置
        configs = [
            {
                'window_id': 'window_1',
                'target_type': 'user',
                'target_value': 'elonmusk',
                'max_tweets': 5
            },
            {
                'window_id': 'window_2',
                'target_type': 'keyword',
                'target_value': 'AI',
                'max_tweets': 5
            }
        ]
        
        print("开始测试并发抓取...")
        # results = await scraper.scrape_multiple_targets(configs)
        # print(f"抓取结果: {results}")
        
        scraper.cleanup()
        print("测试完成")
    
    # asyncio.run(test_enhanced_scraper())
    print("增强Twitter解析器模块已加载")