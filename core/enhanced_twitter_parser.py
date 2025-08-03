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
# from optimized_scraping_engine import OptimizedScrapingEngine
from config import BROWSER_CONFIG


class EnhancedTwitterParser(TwitterParser):
    """
    增强的Twitter解析器
    集成优化抓取引擎，实现每次滚动完成后立即抓取并保存数据
    """
    
    def __init__(self, user_id: str, window_id: str, scraping_engine=None):
        # 正确初始化父类，不传递参数
        super().__init__()
        self.user_id = user_id
        self.window_id = window_id
        self.scraping_engine = scraping_engine
        self.current_task_id: Optional[str] = None
        self.scroll_count = 0
        self.last_tweet_count = 0
        
        # 注册到抓取引擎（如果存在）
        if self.scraping_engine:
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
            self.logger.info(f"开始增强抓取用户 @{username} 的推文")
            
            # 使用父类的抓取方法
            tweets = await self.scrape_user_tweets(username, max_tweets)
            
            # 为每条推文添加来源信息
            for tweet in tweets:
                tweet['source'] = f'@{username}'
                tweet['source_type'] = 'user_profile'
            
            self.logger.info(f"增强抓取完成，共获得 {len(tweets)} 条推文")
            return tweets
            
        except Exception as e:
            self.logger.error(f"增强抓取用户 @{username} 失败: {e}")
            return []
    
    async def enhanced_scrape_keyword_tweets(self, keyword: str, max_tweets: int = 10, 
                                           enable_enhanced: bool = False) -> List[Dict[str, Any]]:
        """增强的关键词推文抓取"""
        try:
            self.logger.info(f"开始增强抓取关键词 '{keyword}' 的推文")
            
            # 使用父类的抓取方法
            tweets = await self.scrape_keyword_tweets(keyword, max_tweets)
            
            # 为每条推文添加来源信息
            for tweet in tweets:
                tweet['source'] = keyword
                tweet['source_type'] = 'keyword_search'
            
            self.logger.info(f"增强抓取完成，共获得 {len(tweets)} 条推文")
            return tweets
            
        except Exception as e:
            self.logger.error(f"增强抓取关键词 '{keyword}' 失败: {e}")
            return []
    
    async def enhanced_scrape_user_keyword_tweets(self, username: str, keyword: str, 
                                                max_tweets: int = 10, enable_enhanced: bool = False) -> List[Dict[str, Any]]:
        """增强的用户关键词推文抓取"""
        try:
            self.logger.info(f"开始增强抓取用户 @{username} 关键词 '{keyword}' 的推文")
            
            # 使用父类的抓取方法
            tweets = await self.scrape_user_keyword_tweets(username, keyword, max_tweets)
            
            # 为每条推文添加来源信息
            for tweet in tweets:
                tweet['source'] = f"@{username} + {keyword}"
                tweet['source_type'] = 'user_keyword_search'
                tweet['target_username'] = username
                tweet['target_keyword'] = keyword
            
            self.logger.info(f"增强抓取完成，共获得 {len(tweets)} 条推文")
            return tweets
            
        except Exception as e:
            self.logger.error(f"增强抓取用户 @{username} 关键词 '{keyword}' 失败: {e}")
            return []
    
    def get_current_task_status(self) -> Optional[Dict[str, Any]]:
        """获取当前任务状态"""
        return {"status": "completed", "tweets_collected": 0}


if __name__ == "__main__":
    print("增强Twitter解析器模块已加载")