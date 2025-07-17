#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量抓取协调器 - 整合所有组件，实现完整的批量抓取流程
支持并发抓取、进度监控、错误恢复和增量更新
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json

from twitter_scraping_engine import TwitterScrapingEngine, AccountState
from browser_manager import BrowserManager, BrowserInstance
from data_extractor import DataExtractor, TweetData, UserData
from storage_manager import StorageManager
from account_state_tracker import AccountStateTracker, AccountStatus
from exception_handler import (
    ExceptionHandler, TwitterScrapingException, RateLimitException,
    async_retry_on_error, handle_exception
)


class BatchStatus(str, Enum):
    """批量抓取状态"""
    PENDING = "pending"        # 待开始
    RUNNING = "running"        # 运行中
    PAUSED = "paused"          # 暂停
    COMPLETED = "completed"    # 完成
    FAILED = "failed"          # 失败
    CANCELLED = "cancelled"    # 取消


@dataclass
class BatchConfig:
    """批量抓取配置"""
    # 目标账号
    target_accounts: List[str] = field(default_factory=list)
    
    # 抓取参数
    max_tweets_per_account: int = 50
    max_concurrent_accounts: int = 3
    delay_between_accounts: float = 5.0
    
    # 过滤条件
    filters: Dict[str, Any] = field(default_factory=dict)
    
    # 存储配置
    output_formats: List[str] = field(default_factory=lambda: ['json', 'csv'])
    output_directory: str = "./data/batch_results"
    
    # 浏览器配置
    headless: bool = True
    max_browser_instances: int = 3
    
    # 重试配置
    max_retries_per_account: int = 3
    retry_delay_minutes: int = 30
    
    # 监控配置
    enable_progress_callback: bool = True
    save_intermediate_results: bool = True
    
    # 高级配置
    advanced: Dict[str, Any] = field(default_factory=dict)
    
    # 日志配置
    logging: Dict[str, Any] = field(default_factory=dict)
    
    # 通知配置
    notifications: Dict[str, Any] = field(default_factory=dict)
    
    # 数据库配置
    database: Dict[str, Any] = field(default_factory=dict)
    
    # API配置
    api: Dict[str, Any] = field(default_factory=dict)
    
    # 云存储配置
    cloud_storage: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> bool:
        """验证配置"""
        if not self.target_accounts:
            return False
        if self.max_tweets_per_account <= 0:
            return False
        if self.max_concurrent_accounts <= 0:
            return False
        return True


@dataclass
class BatchProgress:
    """批量抓取进度"""
    batch_id: str
    status: BatchStatus = BatchStatus.PENDING
    
    # 进度统计
    total_accounts: int = 0
    completed_accounts: int = 0
    failed_accounts: int = 0
    skipped_accounts: int = 0
    
    # 数据统计
    total_tweets: int = 0
    successful_tweets: int = 0
    
    # 时间统计
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    
    # 错误统计
    error_count: int = 0
    rate_limit_count: int = 0
    
    # 当前状态
    current_account: Optional[str] = None
    current_account_progress: float = 0.0
    
    @property
    def overall_progress(self) -> float:
        """总体进度百分比"""
        if self.total_accounts == 0:
            return 0.0
        return (self.completed_accounts / self.total_accounts) * 100
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        processed = self.completed_accounts + self.failed_accounts
        if processed == 0:
            return 0.0
        return (self.completed_accounts / processed) * 100
    
    @property
    def elapsed_time(self) -> timedelta:
        """已用时间"""
        if not self.start_time:
            return timedelta(0)
        end = self.end_time or datetime.now()
        return end - self.start_time
    
    @property
    def estimated_remaining_time(self) -> Optional[timedelta]:
        """预估剩余时间"""
        if self.completed_accounts == 0 or not self.start_time:
            return None
        
        elapsed = self.elapsed_time.total_seconds()
        avg_time_per_account = elapsed / self.completed_accounts
        remaining_accounts = self.total_accounts - self.completed_accounts
        
        return timedelta(seconds=avg_time_per_account * remaining_accounts)


@dataclass
class ScrapingResult:
    """抓取结果类"""
    success: bool = False
    tweets: List[TweetData] = field(default_factory=list)
    user_data: Optional[UserData] = None
    error_message: str = ""
    last_tweet_id: Optional[str] = None
    
    def add_success(self, username: str, tweets: List[TweetData], user_data: Optional[UserData] = None):
        """添加成功结果"""
        self.success = True
        self.tweets = tweets
        self.user_data = user_data
        if tweets:
            self.last_tweet_id = tweets[0].tweet_id if hasattr(tweets[0], 'tweet_id') else None
    
    def add_error(self, username: str, error_type: str, error_message: str):
        """添加错误结果"""
        self.success = False
        self.error_message = f"{error_type}: {error_message}"


class BatchScraper:
    """批量抓取协调器"""
    
    def __init__(self, config: BatchConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 验证配置
        if not self.config.validate():
            raise ValueError("批量抓取配置无效")
        
        # 初始化组件
        self.browser_manager = None
        self.data_extractor = DataExtractor()
        self.storage_manager = StorageManager(base_dir=self.config.output_directory)
        self.state_tracker = AccountStateTracker()
        self.exception_handler = ExceptionHandler()
        
        # 状态管理
        self.batch_id = f"batch_{int(time.time())}"
        self.progress = BatchProgress(batch_id=self.batch_id)
        self.is_cancelled = False
        self.is_paused = False
        
        # 回调函数
        self.progress_callback: Optional[Callable] = None
        self.completion_callback: Optional[Callable] = None
        self.error_callback: Optional[Callable] = None
        
        # 并发控制
        self.semaphore = asyncio.Semaphore(self.config.max_concurrent_accounts)
        self.active_tasks: Dict[str, asyncio.Task] = {}
        
        # 结果存储
        self.batch_results: Dict[str, ScrapingResult] = {}
        self.all_tweets: List[TweetData] = []
    
    def set_progress_callback(self, callback: Callable[[BatchProgress], None]):
        """设置进度回调函数"""
        self.progress_callback = callback
    
    def set_completion_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """设置完成回调函数"""
        self.completion_callback = callback
    
    def set_error_callback(self, callback: Callable[[Exception, str], None]):
        """设置错误回调函数"""
        self.error_callback = callback
    
    async def start_batch_scraping(self) -> Dict[str, Any]:
        """开始批量抓取"""
        try:
            self.logger.info(f"开始批量抓取，批次ID: {self.batch_id}")
            
            # 初始化进度
            self.progress.status = BatchStatus.RUNNING
            self.progress.start_time = datetime.now()
            self.progress.total_accounts = len(self.config.target_accounts)
            
            # 初始化浏览器管理器
            self.browser_manager = BrowserManager(
                max_instances=self.config.max_browser_instances,
                headless=self.config.headless
            )
            await self.browser_manager.initialize()
            
            # 准备账号状态
            await self._prepare_account_states()
            
            # 执行批量抓取
            await self._execute_batch_scraping()
            
            # 完成处理
            await self._finalize_batch()
            
            return await self._generate_batch_summary()
            
        except Exception as e:
            self.logger.error(f"批量抓取失败: {e}")
            self.progress.status = BatchStatus.FAILED
            
            if self.error_callback:
                self.error_callback(e, self.batch_id)
            
            raise e
        
        finally:
            # 清理资源
            await self._cleanup_resources()
    
    async def _prepare_account_states(self):
        """准备账号状态"""
        try:
            self.logger.info("准备账号状态")
            
            for username in self.config.target_accounts:
                # 获取或创建账号状态
                state = self.state_tracker.get_account_state(username)
                
                # 设置优先级（可以根据需要调整）
                if not hasattr(state, 'priority') or state.priority == 1:
                    # 根据账号的历史成功率设置优先级
                    if state.success_rate > 80:
                        state.priority = 1  # 高优先级
                    elif state.success_rate > 50:
                        state.priority = 2  # 中优先级
                    else:
                        state.priority = 3  # 低优先级
            
            # 保存状态
            self.state_tracker.save_states()
            
        except Exception as e:
            self.logger.error(f"准备账号状态失败: {e}")
            raise e
    
    async def _execute_batch_scraping(self):
        """执行批量抓取"""
        try:
            self.logger.info("开始执行批量抓取")
            
            # 获取准备好的账号列表
            ready_accounts = self.state_tracker.get_ready_accounts()
            target_accounts = [acc for acc in self.config.target_accounts if acc in ready_accounts]
            
            if not target_accounts:
                self.logger.warning("没有准备好的账号可以抓取")
                return
            
            # 创建抓取任务
            tasks = []
            for username in target_accounts:
                if self.is_cancelled:
                    break
                
                task = asyncio.create_task(self._scrape_single_account(username))
                tasks.append(task)
                self.active_tasks[username] = task
                
                # 控制并发数量
                if len(tasks) >= self.config.max_concurrent_accounts:
                    # 等待一些任务完成
                    done, pending = await asyncio.wait(
                        tasks, return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    # 处理完成的任务
                    for task in done:
                        tasks.remove(task)
                        # 从active_tasks中移除
                        for user, user_task in list(self.active_tasks.items()):
                            if user_task == task:
                                del self.active_tasks[user]
                                break
            
            # 等待所有剩余任务完成
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            self.logger.error(f"执行批量抓取失败: {e}")
            raise e
    
    async def _scrape_single_account(self, username: str) -> Optional[ScrapingResult]:
        """抓取单个账号"""
        async with self.semaphore:  # 控制并发
            try:
                if self.is_cancelled:
                    return None
                
                self.logger.info(f"开始抓取账号: @{username}")
                self.progress.current_account = username
                
                # 标记开始尝试
                self.state_tracker.mark_attempt_start(username)
                
                # 等待暂停
                while self.is_paused and not self.is_cancelled:
                    await asyncio.sleep(1)
                
                if self.is_cancelled:
                    return None
                
                # 获取浏览器实例
                browser_instance = await self.browser_manager.get_available_instance(timeout=60)
                if not browser_instance:
                    raise TwitterScrapingException("无法获取可用的浏览器实例")
                
                try:
                    # 执行抓取
                    result = await self._perform_account_scraping(username, browser_instance)
                    
                    if result and result.success:
                        # 标记成功
                        self.state_tracker.mark_success(
                            username, 
                            result.last_tweet_id, 
                            len(result.tweets)
                        )
                        
                        self.progress.completed_accounts += 1
                        self.progress.total_tweets += len(result.tweets)
                        self.progress.successful_tweets += len(result.tweets)
                        
                        # 存储结果
                        self.batch_results[username] = result
                        self.all_tweets.extend(result.tweets)
                        
                        # 保存中间结果
                        if self.config.save_intermediate_results:
                            await self._save_intermediate_result(username, result)
                        
                        self.logger.info(f"账号 @{username} 抓取成功，获得 {len(result.tweets)} 条推文")
                    
                    else:
                        # 标记失败
                        error_msg = result.error_message if result else "抓取失败"
                        self.state_tracker.mark_failure(username, error_msg)
                        self.progress.failed_accounts += 1
                        self.progress.error_count += 1
                        
                        self.logger.warning(f"账号 @{username} 抓取失败: {error_msg}")
                    
                    return result
                
                finally:
                    # 释放浏览器实例
                    await self.browser_manager.release_instance(browser_instance)
                
            except RateLimitException as e:
                # 处理限流
                self.state_tracker.mark_rate_limited(username)
                self.progress.rate_limit_count += 1
                self.logger.warning(f"账号 @{username} 被限流: {e}")
                
            except Exception as e:
                # 处理其他错误
                error_info = self.exception_handler.handle_error(e, {"username": username})
                self.state_tracker.mark_failure(username, str(e))
                self.progress.failed_accounts += 1
                self.progress.error_count += 1
                
                self.logger.error(f"抓取账号 @{username} 时发生错误: {e}")
                
                if self.error_callback:
                    self.error_callback(e, username)
            
            finally:
                # 更新进度
                await self._update_progress()
                
                # 账号间延迟
                if not self.is_cancelled and self.config.delay_between_accounts > 0:
                    await asyncio.sleep(self.config.delay_between_accounts)
            
            return None
    
    async def _perform_account_scraping(self, username: str, 
                                       browser_instance: BrowserInstance) -> ScrapingResult:
        """执行账号抓取"""
        try:
            # 构建URL
            url = f"https://twitter.com/{username}"
            
            # 导航到用户页面
            success = await self.browser_manager.navigate_to_page(
                browser_instance, url, 
                wait_for='[data-testid="tweet"]',
                timeout=30
            )
            
            if not success:
                result = ScrapingResult()
                result.add_error(username, "navigation_error", "无法导航到用户页面")
                return result
            
            # 提取推文数据
            tweets = await self.data_extractor.extract_tweets_from_page(
                browser_instance, 
                max_tweets=self.config.max_tweets_per_account
            )
            
            # 应用过滤条件
            if self.config.filters:
                tweets = self.data_extractor.filter_tweets(tweets, self.config.filters)
            
            # 提取用户信息
            user_data = await self.data_extractor.extract_user_profile(browser_instance)
            
            # 创建结果
            result = ScrapingResult()
            result.success = True
            result.tweets = tweets
            result.user_data = user_data
            if tweets:
                result.last_tweet_id = tweets[0].tweet_id if hasattr(tweets[0], 'tweet_id') else None
            
            return result
            
        except Exception as e:
            self.logger.error(f"执行账号抓取失败 @{username}: {e}")
            result = ScrapingResult()
            result.add_error(username, "scraping_error", str(e))
            return result
    
    async def _save_intermediate_result(self, username: str, result: ScrapingResult):
        """保存中间结果"""
        try:
            # 保存用户推文
            if result.tweets:
                await self.storage_manager.save_user_tweets(
                    username, result.tweets, self.batch_id
                )
            
            # 保存用户信息
            if result.user_data:
                user_file = Path(self.config.output_directory) / f"users/{username}_profile.json"
                user_file.parent.mkdir(parents=True, exist_ok=True)
                
                with open(user_file, 'w', encoding='utf-8') as f:
                    json.dump(result.user_data.to_dict(), f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            self.logger.warning(f"保存中间结果失败 @{username}: {e}")
    
    async def _update_progress(self):
        """更新进度"""
        try:
            # 计算预估完成时间
            if self.progress.completed_accounts > 0:
                elapsed = self.progress.elapsed_time.total_seconds()
                avg_time = elapsed / self.progress.completed_accounts
                remaining = self.progress.total_accounts - self.progress.completed_accounts
                
                if remaining > 0:
                    eta_seconds = avg_time * remaining
                    self.progress.estimated_completion = datetime.now() + timedelta(seconds=eta_seconds)
            
            # 调用进度回调
            if self.progress_callback:
                self.progress_callback(self.progress)
            
            # 保存进度到文件
            progress_file = Path(self.config.output_directory) / f"{self.batch_id}_progress.json"
            progress_file.parent.mkdir(parents=True, exist_ok=True)
            
            progress_data = {
                "batch_id": self.progress.batch_id,
                "status": self.progress.status.value,
                "overall_progress": self.progress.overall_progress,
                "completed_accounts": self.progress.completed_accounts,
                "total_accounts": self.progress.total_accounts,
                "failed_accounts": self.progress.failed_accounts,
                "total_tweets": self.progress.total_tweets,
                "success_rate": self.progress.success_rate,
                "elapsed_time": str(self.progress.elapsed_time),
                "estimated_remaining": str(self.progress.estimated_remaining_time) if self.progress.estimated_remaining_time else None,
                "current_account": self.progress.current_account,
                "updated_at": datetime.now().isoformat()
            }
            
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            self.logger.warning(f"更新进度失败: {e}")
    
    async def _finalize_batch(self):
        """完成批量抓取"""
        try:
            self.progress.status = BatchStatus.COMPLETED
            self.progress.end_time = datetime.now()
            self.progress.current_account = None
            
            # 保存最终结果
            await self._save_final_results()
            
            # 保存账号状态
            self.state_tracker.save_states()
            
            # 生成摘要报告
            summary = await self._generate_batch_summary()
            
            # 调用完成回调
            if self.completion_callback:
                self.completion_callback(summary)
            
            self.logger.info(f"批量抓取完成，批次ID: {self.batch_id}")
            
        except Exception as e:
            self.logger.error(f"完成批量抓取时发生错误: {e}")
            raise e
    
    async def _save_final_results(self):
        """保存最终结果"""
        try:
            # 保存所有推文
            if self.all_tweets:
                for format_type in self.config.output_formats:
                    await self.storage_manager.export_data(
                        self.all_tweets, 
                        format_type, 
                        f"{self.batch_id}_all_tweets"
                    )
            
            # 保存批次摘要
            summary = await self._generate_batch_summary()
            await self.storage_manager.save_batch_summary(self.batch_id, summary)
            
            self.logger.info(f"最终结果已保存，格式: {self.config.output_formats}")
            
        except Exception as e:
            self.logger.error(f"保存最终结果失败: {e}")
            raise e
    
    async def _generate_batch_summary(self) -> Dict[str, Any]:
        """生成批次摘要"""
        try:
            # 统计信息
            stats = self.state_tracker.get_statistics()
            browser_stats = await self.browser_manager.get_statistics() if self.browser_manager else {}
            error_stats = self.exception_handler.get_error_statistics()
            
            summary = {
                "batch_info": {
                    "batch_id": self.batch_id,
                    "status": self.progress.status.value,
                    "start_time": self.progress.start_time.isoformat() if self.progress.start_time else None,
                    "end_time": self.progress.end_time.isoformat() if self.progress.end_time else None,
                    "duration": str(self.progress.elapsed_time),
                },
                
                "configuration": {
                    "target_accounts": self.config.target_accounts,
                    "max_tweets_per_account": self.config.max_tweets_per_account,
                    "max_concurrent_accounts": self.config.max_concurrent_accounts,
                    "output_formats": self.config.output_formats,
                    "filters": self.config.filters,
                },
                
                "results": {
                    "total_accounts": self.progress.total_accounts,
                    "completed_accounts": self.progress.completed_accounts,
                    "failed_accounts": self.progress.failed_accounts,
                    "skipped_accounts": self.progress.skipped_accounts,
                    "success_rate": self.progress.success_rate,
                    "total_tweets": self.progress.total_tweets,
                    "successful_tweets": self.progress.successful_tweets,
                },
                
                "performance": {
                    "average_tweets_per_account": self.progress.total_tweets / max(self.progress.completed_accounts, 1),
                    "average_time_per_account": self.progress.elapsed_time.total_seconds() / max(self.progress.completed_accounts, 1),
                    "tweets_per_minute": self.progress.total_tweets / max(self.progress.elapsed_time.total_seconds() / 60, 1),
                },
                
                "errors": {
                    "total_errors": self.progress.error_count,
                    "rate_limit_errors": self.progress.rate_limit_count,
                    "error_distribution": error_stats.get("category_distribution", {}),
                },
                
                "account_states": stats,
                "browser_performance": browser_stats,
                
                "generated_at": datetime.now().isoformat()
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"生成批次摘要失败: {e}")
            return {"error": str(e)}
    
    async def _cleanup_resources(self):
        """清理资源"""
        try:
            # 取消所有活动任务
            for task in self.active_tasks.values():
                if not task.done():
                    task.cancel()
            
            # 等待任务完成
            if self.active_tasks:
                await asyncio.gather(*self.active_tasks.values(), return_exceptions=True)
            
            # 关闭浏览器管理器
            if self.browser_manager:
                await self.browser_manager.close_all()
            
            # 清理异常处理器
            self.exception_handler.clear_old_errors()
            
            self.logger.info("资源清理完成")
            
        except Exception as e:
            self.logger.error(f"清理资源失败: {e}")
    
    def pause(self):
        """暂停批量抓取"""
        self.is_paused = True
        self.progress.status = BatchStatus.PAUSED
        self.logger.info("批量抓取已暂停")
    
    def resume(self):
        """恢复批量抓取"""
        self.is_paused = False
        self.progress.status = BatchStatus.RUNNING
        self.logger.info("批量抓取已恢复")
    
    def cancel(self):
        """取消批量抓取"""
        self.is_cancelled = True
        self.progress.status = BatchStatus.CANCELLED
        self.logger.info("批量抓取已取消")
    
    def get_progress(self) -> BatchProgress:
        """获取当前进度"""
        return self.progress
    
    def get_results(self) -> Dict[str, ScrapingResult]:
        """获取抓取结果"""
        return self.batch_results.copy()
    
    async def stop_scraping(self):
        """停止批量抓取"""
        try:
            self.logger.info("正在停止批量抓取...")
            
            # 设置取消标志
            self.cancel()
            
            # 等待当前任务完成
            if self.active_tasks:
                self.logger.info(f"等待 {len(self.active_tasks)} 个活动任务完成...")
                await asyncio.gather(*self.active_tasks.values(), return_exceptions=True)
            
            # 清理资源
            await self._cleanup_resources()
            
            # 保存当前进度和结果
            if self.progress.total_tweets > 0:
                await self._save_final_results()
            
            self.logger.info("批量抓取已停止")
            
        except Exception as e:
            self.logger.error(f"停止抓取时发生错误: {e}")
            raise e


# 使用示例
if __name__ == "__main__":
    import asyncio
    
    async def progress_callback(progress: BatchProgress):
        print(f"进度: {progress.overall_progress:.1f}% - {progress.current_account}")
    
    async def completion_callback(summary: Dict[str, Any]):
        print(f"批量抓取完成: {summary['results']['total_tweets']} 条推文")
    
    async def test_batch_scraper():
        # 配置
        config = BatchConfig(
            target_accounts=["elonmusk", "openai", "github"],
            max_tweets_per_account=20,
            max_concurrent_accounts=2,
            output_formats=["json", "csv"],
            filters={
                "min_likes": 10,
                "exclude_retweets": True
            }
        )
        
        # 创建批量抓取器
        scraper = BatchScraper(config)
        scraper.set_progress_callback(progress_callback)
        scraper.set_completion_callback(completion_callback)
        
        try:
            # 开始抓取
            summary = await scraper.start_batch_scraping()
            print(f"抓取完成: {summary}")
            
        except Exception as e:
            print(f"抓取失败: {e}")
    
    # 运行测试
    asyncio.run(test_batch_scraper())