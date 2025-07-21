#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化的Twitter抓取引擎
实现每次滚动完成后立即抓取并保存数据的多线程架构
"""

import asyncio
import threading
import queue
import time
import logging
from typing import List, Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
import json

from twitter_parser import TwitterParser
from storage_manager import StorageManager
from cloud_sync import CloudSyncManager
from config import CLOUD_SYNC_CONFIG


@dataclass
class ScrollEvent:
    """滚动事件数据"""
    window_id: str
    task_id: str
    scroll_count: int
    tweets_found: int
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ScrapingTask:
    """抓取任务数据"""
    task_id: str
    window_id: str
    target_type: str  # 'user', 'keyword', 'user_keyword'
    target_value: str
    max_tweets: int
    enable_enhanced: bool = False
    progress: int = 0
    status: str = 'pending'  # pending, running, completed, failed
    tweets_collected: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


class OptimizedScrapingEngine:
    """
    优化的抓取引擎
    实现每次滚动完成后立即抓取并保存数据的多线程架构
    """
    
    def __init__(self, max_workers: int = 4):
        self.logger = logging.getLogger(__name__)
        self.max_workers = max_workers
        
        # 线程池
        self.scraping_executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="scraping")
        self.saving_executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="saving")
        
        # 数据队列
        self.scroll_event_queue = queue.Queue()
        self.scraping_queue = queue.Queue()
        self.saving_queue = queue.Queue()
        
        # 任务管理
        self.active_tasks: Dict[str, ScrapingTask] = {}
        self.window_parsers: Dict[str, TwitterParser] = {}
        
        # 数据存储
        self.data_storage = StorageManager()
        self.cloud_sync = CloudSyncManager(CLOUD_SYNC_CONFIG)
        
        # 控制标志
        self.is_running = False
        self.stop_event = threading.Event()
        
        # 回调函数
        self.on_scroll_complete: Optional[Callable] = None
        self.on_tweets_scraped: Optional[Callable] = None
        self.on_data_saved: Optional[Callable] = None
        
    def start_engine(self):
        """启动抓取引擎"""
        if self.is_running:
            self.logger.warning("抓取引擎已在运行")
            return
            
        self.is_running = True
        self.stop_event.clear()
        
        # 启动工作线程
        threading.Thread(target=self._scroll_event_processor, daemon=True).start()
        threading.Thread(target=self._scraping_coordinator, daemon=True).start()
        threading.Thread(target=self._saving_coordinator, daemon=True).start()
        
        self.logger.info(f"优化抓取引擎已启动，工作线程数: {self.max_workers}")
    
    def stop_engine(self):
        """停止抓取引擎"""
        self.is_running = False
        self.stop_event.set()
        
        # 关闭线程池
        self.scraping_executor.shutdown(wait=True)
        self.saving_executor.shutdown(wait=True)
        
        self.logger.info("优化抓取引擎已停止")
    
    def register_window_parser(self, window_id: str, parser: TwitterParser):
        """注册窗口解析器"""
        self.window_parsers[window_id] = parser
        self.logger.info(f"已注册窗口 {window_id} 的解析器")
    
    def create_scraping_task(self, task_id: str, window_id: str, target_type: str, 
                           target_value: str, max_tweets: int, enable_enhanced: bool = False) -> ScrapingTask:
        """创建抓取任务"""
        task = ScrapingTask(
            task_id=task_id,
            window_id=window_id,
            target_type=target_type,
            target_value=target_value,
            max_tweets=max_tweets,
            enable_enhanced=enable_enhanced
        )
        
        self.active_tasks[task_id] = task
        self.logger.info(f"创建抓取任务: {task_id} (窗口: {window_id}, 类型: {target_type}, 目标: {target_value})")
        
        return task
    
    def trigger_scroll_event(self, window_id: str, task_id: str, scroll_count: int, tweets_found: int):
        """触发滚动事件"""
        event = ScrollEvent(
            window_id=window_id,
            task_id=task_id,
            scroll_count=scroll_count,
            tweets_found=tweets_found
        )
        
        self.scroll_event_queue.put(event)
        self.logger.debug(f"触发滚动事件: 窗口 {window_id}, 任务 {task_id}, 滚动次数 {scroll_count}, 发现推文 {tweets_found}")
    
    def _scroll_event_processor(self):
        """滚动事件处理器"""
        self.logger.info("滚动事件处理器已启动")
        
        while self.is_running and not self.stop_event.is_set():
            try:
                # 获取滚动事件
                event = self.scroll_event_queue.get(timeout=1.0)
                
                # 检查任务是否存在
                if event.task_id not in self.active_tasks:
                    self.logger.warning(f"任务 {event.task_id} 不存在，跳过处理")
                    continue
                
                task = self.active_tasks[event.task_id]
                
                # 检查是否需要继续抓取
                if len(task.tweets_collected) >= task.max_tweets:
                    self.logger.info(f"任务 {event.task_id} 已达到目标推文数量，跳过抓取")
                    continue
                
                # 将抓取任务加入队列
                self.scraping_queue.put((event, task))
                
                # 回调通知
                if self.on_scroll_complete:
                    self.on_scroll_complete(event)
                    
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"滚动事件处理失败: {e}")
    
    def _scraping_coordinator(self):
        """抓取协调器"""
        self.logger.info("抓取协调器已启动")
        
        while self.is_running and not self.stop_event.is_set():
            try:
                # 获取抓取任务
                event, task = self.scraping_queue.get(timeout=1.0)
                
                # 提交抓取任务到线程池
                future = self.scraping_executor.submit(self._execute_scraping, event, task)
                
                # 异步处理结果
                threading.Thread(
                    target=self._handle_scraping_result,
                    args=(future, event, task),
                    daemon=True
                ).start()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"抓取协调失败: {e}")
    
    def _execute_scraping(self, event: ScrollEvent, task: ScrapingTask) -> List[Dict[str, Any]]:
        """执行抓取任务"""
        try:
            self.logger.info(f"开始执行抓取任务: {task.task_id} (窗口: {event.window_id})")
            
            # 获取对应窗口的解析器
            parser = self.window_parsers.get(event.window_id)
            if not parser:
                raise Exception(f"窗口 {event.window_id} 的解析器不存在")
            
            # 根据任务类型执行不同的抓取逻辑
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # 确保解析器知道当前任务ID
                if hasattr(parser, 'current_task_id'):
                    parser.current_task_id = task.task_id
                
                if task.target_type == 'user':
                    tweets = loop.run_until_complete(
                        self._scrape_current_page_tweets(parser, task.max_tweets - len(task.tweets_collected))
                    )
                elif task.target_type == 'keyword':
                    tweets = loop.run_until_complete(
                        self._scrape_current_page_tweets(parser, task.max_tweets - len(task.tweets_collected))
                    )
                elif task.target_type == 'user_keyword':
                    tweets = loop.run_until_complete(
                        self._scrape_current_page_tweets(parser, task.max_tweets - len(task.tweets_collected))
                    )
                else:
                    raise Exception(f"不支持的任务类型: {task.target_type}")
                
                self.logger.info(f"抓取任务 {task.task_id} 完成，获得 {len(tweets)} 条新推文")
                return tweets
                
            finally:
                loop.close()
                
        except Exception as e:
            self.logger.error(f"执行抓取任务失败: {e}")
            return []
    
    async def _scrape_current_page_tweets(self, parser: TwitterParser, max_tweets: int) -> List[Dict[str, Any]]:
        """抓取当前页面的推文（带去重）"""
        try:
            self.logger.info(f"开始抓取当前页面推文，目标数量: {max_tweets}")
            
            # 等待页面充分加载
            self.logger.info("等待页面加载...")
            await asyncio.sleep(3)
            
            # 尝试等待推文元素出现
            try:
                await parser.page.wait_for_selector('article[role="article"]', timeout=15000)
                self.logger.info("推文元素已出现")
            except Exception as e:
                self.logger.warning(f"等待推文元素超时: {e}，继续尝试查找")
            
            # 再等待一段时间确保内容完全加载
            await asyncio.sleep(2)
            
            # 获取当前页面的推文元素
            self.logger.info("正在查找推文元素...")
            tweet_elements = []
            
            try:
                # 使用正确的推文选择器
                tweet_elements = await asyncio.wait_for(
                    parser.page.query_selector_all('article[role="article"]'),
                    timeout=10.0
                )
                self.logger.info(f"找到 {len(tweet_elements)} 个推文元素")
            except asyncio.TimeoutError:
                self.logger.warning("查找推文元素超时，尝试备用选择器")
                try:
                    tweet_elements = await asyncio.wait_for(
                        parser.page.query_selector_all('section[aria-labelledby] article'),
                        timeout=10.0
                    )
                    self.logger.info(f"使用备用选择器找到 {len(tweet_elements)} 个推文元素")
                except asyncio.TimeoutError:
                    self.logger.error("备用选择器也超时")
                    return []
                except Exception as e2:
                    self.logger.error(f"备用选择器失败: {e2}")
                    return []
            except Exception as e:
                self.logger.error(f"查找推文元素失败: {e}")
                return []
            
            if not tweet_elements:
                self.logger.warning("页面上没有找到推文元素")
                return []
            
            # 获取当前任务的已抓取推文ID集合
            current_task_id = getattr(parser, 'current_task_id', None)
            task = self.active_tasks.get(current_task_id) if current_task_id else None
            existing_tweet_ids = set()
            if task:
                existing_tweet_ids = {tweet.get('tweet_id', tweet.get('link', '')) for tweet in task.tweets_collected}
            
            self.logger.info(f"当前任务ID: {current_task_id}, 已有推文数: {len(existing_tweet_ids) if task else 0}")
            
            tweets_data = []
            processed_count = 0
            
            for i, tweet_element in enumerate(tweet_elements):
                if processed_count >= max_tweets:
                    break
                    
                try:
                    self.logger.debug(f"正在解析第 {i+1} 个推文元素")
                    tweet_data = await parser.parse_tweet_element(tweet_element)
                    
                    if tweet_data:
                        self.logger.debug(f"成功解析推文: 用户={tweet_data.get('username', 'unknown')}, 内容长度={len(tweet_data.get('content', ''))}")
                        
                        # 检查推文是否已存在（去重）
                        tweet_id = tweet_data.get('tweet_id', tweet_data.get('link', ''))
                        if tweet_id and tweet_id not in existing_tweet_ids:
                            tweets_data.append(tweet_data)
                            existing_tweet_ids.add(tweet_id)
                            processed_count += 1
                            
                            self.logger.info(f"新推文已抓取 ({processed_count}/{max_tweets}): @{tweet_data.get('username', 'unknown')}")
                        else:
                            self.logger.debug(f"跳过重复推文: {tweet_id[:50] if tweet_id else 'no_id'}")
                    else:
                        self.logger.debug(f"第 {i+1} 个推文元素解析结果为空")
                            
                except Exception as e:
                    self.logger.warning(f"解析第 {i+1} 个推文元素失败: {e}")
                    continue
                    
                # 避免过快处理
                if i % 3 == 0:
                    await asyncio.sleep(0.1)
            
            self.logger.info(f"本次抓取完成，获得 {len(tweets_data)} 条新推文（去重后）")
            return tweets_data
            
        except Exception as e:
            self.logger.error(f"抓取当前页面推文失败: {e}", exc_info=True)
            return []
    
    def _handle_scraping_result(self, future, event: ScrollEvent, task: ScrapingTask):
        """处理抓取结果"""
        try:
            tweets = future.result(timeout=60)  # 增加到60秒超时
            
            if tweets:
                # 更新任务数据
                task.tweets_collected.extend(tweets)
                task.progress = len(task.tweets_collected)
                task.status = 'running'
                
                # 立即将数据加入保存队列（实时保存）
                self.saving_queue.put((task.task_id, tweets))
                
                # 回调通知
                if self.on_tweets_scraped:
                    self.on_tweets_scraped(task.task_id, tweets)
                
                self.logger.info(f"任务 {task.task_id} 抓取结果处理完成，新增 {len(tweets)} 条推文，立即保存")
            
        except TimeoutError:
            self.logger.warning(f"任务 {task.task_id} 抓取超时，将重试")
            # 不设置为失败，允许继续尝试
        except Exception as e:
            self.logger.error(f"处理抓取结果失败: {e}", exc_info=True)
            task.status = 'failed'
    
    def _saving_coordinator(self):
        """保存协调器"""
        self.logger.info("保存协调器已启动")
        
        while self.is_running and not self.stop_event.is_set():
            try:
                # 获取保存任务
                task_id, tweets = self.saving_queue.get(timeout=1.0)
                
                # 提交保存任务到线程池
                future = self.saving_executor.submit(self._execute_saving, task_id, tweets)
                
                # 异步处理结果
                threading.Thread(
                    target=self._handle_saving_result,
                    args=(future, task_id, len(tweets)),
                    daemon=True
                ).start()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"保存协调失败: {e}")
    
    def _execute_saving(self, task_id: str, tweets: List[Dict[str, Any]]) -> bool:
        """执行保存任务"""
        try:
            self.logger.info(f"开始保存任务 {task_id} 的 {len(tweets)} 条推文")
            
            # 保存到本地数据库
            # 按用户名分组保存推文
            tweets_by_user = {}
            for tweet in tweets:
                username = tweet.get('username', 'unknown')
                if username not in tweets_by_user:
                    tweets_by_user[username] = []
                tweets_by_user[username].append(tweet)
            
            # 为每个用户保存推文
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                for username, user_tweets in tweets_by_user.items():
                    loop.run_until_complete(
                        self.data_storage.save_user_tweets(
                            username, 
                            user_tweets, 
                            {'task_id': task_id, 'batch_size': len(user_tweets)}
                        )
                    )
            finally:
                loop.close()
            
            # 同步到云端
            try:
                self.cloud_sync.sync_tweets(tweets)
                self.logger.info(f"任务 {task_id} 数据已同步到云端")
            except Exception as e:
                self.logger.warning(f"任务 {task_id} 云端同步失败: {e}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"保存任务 {task_id} 失败: {e}")
            return False
    
    def _handle_saving_result(self, future, task_id: str, tweet_count: int):
        """处理保存结果"""
        try:
            success = future.result(timeout=60)  # 增加到60秒超时
            
            if success:
                self.logger.info(f"任务 {task_id} 的 {tweet_count} 条推文保存成功")
                
                # 回调通知
                if self.on_data_saved:
                    self.on_data_saved(task_id, tweet_count)
            else:
                self.logger.error(f"任务 {task_id} 的 {tweet_count} 条推文保存失败")
            
        except Exception as e:
            self.logger.error(f"处理保存结果失败: {e}", exc_info=True)
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        task = self.active_tasks.get(task_id)
        if not task:
            return None
        
        return {
            'task_id': task.task_id,
            'window_id': task.window_id,
            'target_type': task.target_type,
            'target_value': task.target_value,
            'max_tweets': task.max_tweets,
            'progress': task.progress,
            'status': task.status,
            'tweets_collected': len(task.tweets_collected),
            'created_at': task.created_at.isoformat()
        }
    
    def get_all_tasks_status(self) -> List[Dict[str, Any]]:
        """获取所有任务状态"""
        return [self.get_task_status(task_id) for task_id in self.active_tasks.keys()]
    
    def complete_task(self, task_id: str):
        """完成任务"""
        if task_id in self.active_tasks:
            self.active_tasks[task_id].status = 'completed'
            self.logger.info(f"任务 {task_id} 已完成")
    
    def cancel_task(self, task_id: str):
        """取消任务"""
        if task_id in self.active_tasks:
            self.active_tasks[task_id].status = 'cancelled'
            self.logger.info(f"任务 {task_id} 已取消")
    
    def cleanup_completed_tasks(self):
        """清理已完成的任务"""
        completed_tasks = [task_id for task_id, task in self.active_tasks.items() 
                          if task.status in ['completed', 'cancelled', 'failed']]
        
        for task_id in completed_tasks:
            del self.active_tasks[task_id]
        
        self.logger.info(f"清理了 {len(completed_tasks)} 个已完成的任务")
    
    def get_engine_stats(self) -> Dict[str, Any]:
        """获取引擎统计信息"""
        return {
            'is_running': self.is_running,
            'active_tasks': len(self.active_tasks),
            'registered_windows': len(self.window_parsers),
            'scroll_queue_size': self.scroll_event_queue.qsize(),
            'scraping_queue_size': self.scraping_queue.qsize(),
            'saving_queue_size': self.saving_queue.qsize(),
            'max_workers': self.max_workers
        }


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    engine = OptimizedScrapingEngine(max_workers=2)
    engine.start_engine()
    
    print("优化抓取引擎测试启动")
    print(f"引擎状态: {engine.get_engine_stats()}")
    
    # 模拟创建任务
    task = engine.create_scraping_task(
        task_id="test_task_1",
        window_id="window_1",
        target_type="user",
        target_value="elonmusk",
        max_tweets=10
    )
    
    print(f"创建任务: {engine.get_task_status('test_task_1')}")
    
    # 模拟滚动事件
    engine.trigger_scroll_event("window_1", "test_task_1", 1, 5)
    
    time.sleep(2)
    
    print(f"任务状态: {engine.get_task_status('test_task_1')}")
    print(f"引擎状态: {engine.get_engine_stats()}")
    
    engine.stop_engine()
    print("优化抓取引擎测试完成")