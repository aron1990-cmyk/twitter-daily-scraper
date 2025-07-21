#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter抓取引擎 - 首次抓取逻辑核心模块
负责协调整个批量抓取流程
"""

import asyncio
import logging
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from ads_browser_launcher import AdsPowerLauncher
from twitter_parser import TwitterParser
from enhanced_twitter_parser import EnhancedTwitterParser, MultiWindowEnhancedScraper
from optimized_scraping_engine import OptimizedScrapingEngine
from data_storage import DataStorage
from cloud_sync import CloudSyncManager
from config import ADS_POWER_CONFIG, CLOUD_SYNC_CONFIG
from exceptions import ScrapingException, TwitterScrapingError


@dataclass
class ScrapingResult:
    """抓取结果数据模型"""
    total_users: int = 0
    successful_users: int = 0
    failed_users: int = 0
    total_tweets: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    errors: List[Dict[str, Any]] = field(default_factory=list)
    success_details: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_success(self, username: str, tweet_count: int):
        """添加成功记录"""
        self.successful_users += 1
        self.total_tweets += tweet_count
        self.success_details.append({
            'username': username,
            'tweet_count': tweet_count,
            'timestamp': datetime.now()
        })
    
    def add_error(self, username: str, error_type: str, error_message: str):
        """添加错误记录"""
        self.failed_users += 1
        self.errors.append({
            'username': username,
            'error_type': error_type,
            'error_message': error_message,
            'timestamp': datetime.now()
        })
    
    def finalize(self):
        """完成抓取，设置结束时间"""
        self.end_time = datetime.now()
    
    @property
    def duration(self) -> float:
        """抓取持续时间（秒）"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_users == 0:
            return 0.0
        return (self.successful_users / self.total_users) * 100


@dataclass
class AccountState:
    """账号状态模型"""
    username: str
    last_fetched_id: Optional[str] = None
    last_fetched_time: Optional[datetime] = None
    status: str = "pending"  # pending/success/failed/rate_limited
    total_tweets_fetched: int = 0
    last_error: Optional[str] = None
    retry_count: int = 0
    next_retry_time: Optional[datetime] = None


class TwitterScrapingEngine:
    """Twitter抓取引擎 - 首次抓取逻辑核心
    集成优化抓取引擎，支持多线程和实时抓取
    """
    
    def __init__(self, user_id: str = None, enable_optimized: bool = True, max_workers: int = 4):
        self.user_id = user_id
        self.launcher = AdsPowerLauncher()
        self.parser: Optional[TwitterParser] = None
        self.logger = logging.getLogger(__name__)
        
        # 抓取配置
        self.max_tweets_per_user = 20
        self.max_retry_count = 3
        self.base_delay = 3  # 基础延迟时间（秒）
        self.max_delay = 8   # 最大延迟时间（秒）
        
        # 状态跟踪
        self.account_states: Dict[str, AccountState] = {}
        
        # 数据存储和云同步
        self.data_storage = DataStorage()
        self.cloud_sync = CloudSyncManager(CLOUD_SYNC_CONFIG)
        
        # 优化抓取引擎
        self.enable_optimized = enable_optimized
        if enable_optimized:
            self.optimized_scraper = MultiWindowEnhancedScraper(max_workers=max_workers)
            self.logger.info(f"已启用优化抓取引擎，最大工作线程: {max_workers}")
        else:
            self.optimized_scraper = None
            self.logger.info("使用传统抓取模式")
        
    async def initialize_browser(self) -> bool:
        """初始化浏览器环境"""
        try:
            self.logger.info("开始初始化AdsPower浏览器...")
            
            # 启动AdsPower浏览器
            browser_info = self.launcher.start_browser(self.user_id)
            
            # 等待浏览器准备就绪
            if not self.launcher.wait_for_browser_ready():
                raise Exception("浏览器启动超时")
            
            # 获取调试端口
            debug_port = self.launcher.get_debug_port()
            if not debug_port:
                raise Exception("无法获取浏览器调试端口")
            
            self.logger.info(f"浏览器调试端口: {debug_port}")
            
            # 创建Twitter解析器并连接浏览器
            self.parser = TwitterParser(debug_port)
            await self.parser.connect_browser()
            
            # 导航到Twitter
            await self.parser.navigate_to_twitter()
            
            self.logger.info("浏览器初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"浏览器初始化失败: {e}")
            return False
    
    async def batch_scrape_first_time(self, usernames: List[str]) -> ScrapingResult:
        """
        首次批量抓取流程
        
        Args:
            usernames: 用户名列表
            
        Returns:
            抓取结果
        """
        result = ScrapingResult()
        result.total_users = len(usernames)
        
        self.logger.info(f"开始首次批量抓取，目标用户数: {len(usernames)}")
        
        # 如果启用优化模式且用户数量较多，使用优化抓取引擎
        if self.enable_optimized and len(usernames) > 1:
            return await self._optimized_batch_scrape_first_time(usernames)
        
        # 传统单线程抓取模式
        return await self._traditional_batch_scrape_first_time(usernames)
    
    async def _optimized_batch_scrape_first_time(self, usernames: List[str]) -> ScrapingResult:
        """优化的首次批量抓取流程"""
        result = ScrapingResult()
        result.total_users = len(usernames)
        
        try:
            self.logger.info(f"使用优化模式进行首次批量抓取 {len(usernames)} 个用户")
            
            # 为每个用户创建抓取配置
            scraping_configs = []
            for username in usernames:
                scraping_configs.append({
                    'target_type': 'user',
                    'target_value': username,
                    'max_tweets': self.max_tweets_per_user,
                    'enable_enhanced': False  # 首次抓取使用基础模式
                })
            
            # 执行并发抓取
            scraping_results = await self.optimized_scraper.scrape_multiple_targets(scraping_configs)
            
            # 处理结果
            all_tweets = []
            for window_id, tweets in scraping_results.items():
                if tweets:
                    all_tweets.extend(tweets)
                    # 从推文中提取用户名并更新状态
                    for tweet in tweets:
                        username = tweet.get('username')
                        if username:
                            self._update_account_state(
                                username=username,
                                status="success",
                                last_fetched_id=tweet.get('tweet_id'),
                                total_tweets=len([t for t in tweets if t.get('username') == username])
                            )
                            result.add_success(username, len([t for t in tweets if t.get('username') == username]))
            
            # 保存数据
            if all_tweets:
                self.data_storage.save_tweets(all_tweets)
                
                # 同步到云端
                try:
                    await self.cloud_sync.sync_tweets(all_tweets)
                    self.logger.info("数据已同步到云端")
                except Exception as e:
                    self.logger.warning(f"云端同步失败: {e}")
            
            result.finalize()
            self.logger.info(f"优化批量抓取完成，成功: {result.successful_users}/{result.total_users}, "
                            f"总推文: {result.total_tweets}, 耗时: {result.duration:.1f}秒")
            
            return result
            
        except Exception as e:
            self.logger.error(f"优化批量抓取失败: {e}")
            result.finalize()
            return result
    
    async def _traditional_batch_scrape_first_time(self, usernames: List[str]) -> ScrapingResult:
        """传统的首次批量抓取流程"""
        result = ScrapingResult()
        result.total_users = len(usernames)
        
        self.logger.info(f"使用传统模式进行首次批量抓取，目标用户数: {len(usernames)}")
        
        # 初始化浏览器
        if not await self.initialize_browser():
            self.logger.error("浏览器初始化失败，终止抓取")
            result.finalize()
            return result
        
        all_tweets = []
        
        # 遍历用户列表
        for i, username in enumerate(usernames, 1):
            try:
                self.logger.info(f"[{i}/{len(usernames)}] 开始抓取用户: @{username}")
                
                # 检查账号状态
                account_state = self._get_account_state(username)
                if self._should_skip_user(account_state):
                    self.logger.info(f"跳过用户 @{username}，原因: {account_state.status}")
                    continue
                
                # 执行单用户抓取
                tweets = await self._scrape_single_user(username)
                
                if tweets:
                    all_tweets.extend(tweets)
                    # 更新账号状态为成功
                    self._update_account_state(
                        username=username,
                        status="success",
                        last_fetched_id=tweets[0].get('tweet_id') if tweets else None,
                        total_tweets=len(tweets)
                    )
                    
                    result.add_success(username, len(tweets))
                    self.logger.info(f"用户 @{username} 抓取成功，获得 {len(tweets)} 条推文")
                else:
                    # 没有获得推文，但不算错误
                    self._update_account_state(
                        username=username,
                        status="success",
                        total_tweets=0
                    )
                    result.add_success(username, 0)
                    self.logger.warning(f"用户 @{username} 没有获得推文")
                
            except TwitterScrapingError as e:
                # Twitter特定错误
                self.logger.error(f"抓取用户 @{username} 失败: {e}")
                self._update_account_state(
                    username=username,
                    status="failed",
                    last_error=str(e)
                )
                result.add_error(username, "twitter_error", str(e))
                
            except Exception as e:
                # 通用错误
                self.logger.error(f"抓取用户 @{username} 时发生未知错误: {e}")
                self._update_account_state(
                    username=username,
                    status="failed",
                    last_error=str(e)
                )
                result.add_error(username, "unknown_error", str(e))
                
            finally:
                # 添加随机延迟，模拟人工行为
                delay = random.uniform(self.base_delay, self.max_delay)
                self.logger.debug(f"等待 {delay:.1f} 秒后继续...")
                await asyncio.sleep(delay)
        
        # 保存数据
        if all_tweets:
            self.data_storage.save_tweets(all_tweets)
            
            # 同步到云端
            try:
                await self.cloud_sync.sync_tweets(all_tweets)
                self.logger.info("数据已同步到云端")
            except Exception as e:
                self.logger.warning(f"云端同步失败: {e}")
        
        result.finalize()
        self.logger.info(f"传统批量抓取完成，成功: {result.successful_users}/{result.total_users}, "
                        f"总推文: {result.total_tweets}, 耗时: {result.duration:.1f}秒")
        
        return result
    
    async def _scrape_single_user(self, username: str) -> List[Dict[str, Any]]:
        """
        抓取单个用户的推文
        
        Args:
            username: 用户名
            
        Returns:
            推文数据列表
        """
        try:
            # 导航到用户主页
            await self.parser.navigate_to_profile(username)
            
            # 抓取推文
            tweets = await self.parser.scrape_user_tweets(
                username=username,
                max_tweets=self.max_tweets_per_user,
                enable_enhanced=False  # 首次抓取使用基础模式
            )
            
            return tweets
            
        except Exception as e:
            self.logger.error(f"抓取用户 @{username} 的推文失败: {e}")
            raise TwitterScrapingError(f"抓取用户 @{username} 失败: {e}")
    
    def _get_account_state(self, username: str) -> AccountState:
        """获取账号状态"""
        if username not in self.account_states:
            self.account_states[username] = AccountState(username=username)
        return self.account_states[username]
    
    def _should_skip_user(self, account_state: AccountState) -> bool:
        """
        判断是否应该跳过用户
        
        Args:
            account_state: 账号状态
            
        Returns:
            是否跳过
        """
        # 首次抓取不跳过任何用户
        # 这里可以根据需要添加跳过逻辑，比如：
        # - 如果用户已经成功抓取过且时间很近
        # - 如果用户处于限流状态且还在冷却期
        return False
    
    def _update_account_state(self, username: str, status: str, 
                            last_fetched_id: str = None, 
                            total_tweets: int = None,
                            last_error: str = None):
        """
        更新账号状态
        
        Args:
            username: 用户名
            status: 状态
            last_fetched_id: 最后抓取的推文ID
            total_tweets: 抓取的推文总数
            last_error: 错误信息
        """
        account_state = self._get_account_state(username)
        account_state.status = status
        account_state.last_fetched_time = datetime.now()
        
        if last_fetched_id:
            account_state.last_fetched_id = last_fetched_id
        
        if total_tweets is not None:
            account_state.total_tweets_fetched = total_tweets
        
        if last_error:
            account_state.last_error = last_error
            account_state.retry_count += 1
    
    async def cleanup(self):
        """清理资源"""
        try:
            if self.parser:
                # 这里可以添加parser的清理逻辑
                pass
            
            # 停止浏览器
            self.launcher.stop_browser()
            self.logger.info("资源清理完成")
            
        except Exception as e:
            self.logger.error(f"清理资源时发生错误: {e}")
    
    def get_scraping_summary(self) -> Dict[str, Any]:
        """
        获取抓取摘要信息
        
        Returns:
            抓取摘要
        """
        total_accounts = len(self.account_states)
        successful_accounts = sum(1 for state in self.account_states.values() 
                                if state.status == "success")
        failed_accounts = sum(1 for state in self.account_states.values() 
                            if state.status == "failed")
        total_tweets = sum(state.total_tweets_fetched for state in self.account_states.values())
        
        return {
            'total_accounts': total_accounts,
            'successful_accounts': successful_accounts,
            'failed_accounts': failed_accounts,
            'success_rate': (successful_accounts / total_accounts * 100) if total_accounts > 0 else 0,
            'total_tweets': total_tweets,
            'average_tweets_per_account': total_tweets / successful_accounts if successful_accounts > 0 else 0,
            'account_states': {username: {
                'status': state.status,
                'tweets_count': state.total_tweets_fetched,
                'last_fetched_time': state.last_fetched_time.isoformat() if state.last_fetched_time else None,
                'last_error': state.last_error
            } for username, state in self.account_states.items()}
        }