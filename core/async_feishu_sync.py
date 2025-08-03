#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异步飞书同步模块

功能:
1. 异步处理飞书数据同步
2. 任务队列管理
3. 进度跟踪和状态监控
4. 错误处理和重试机制
5. 并发控制和频率限制
"""

import asyncio
import json
import time
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
from queue import Queue, Empty
import logging
from concurrent.futures import ThreadPoolExecutor

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SyncStatus(Enum):
    """同步状态枚举"""
    PENDING = "pending"      # 等待中
    RUNNING = "running"      # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 失败
    CANCELLED = "cancelled"  # 已取消
    RETRYING = "retrying"    # 重试中

@dataclass
class SyncTask:
    """同步任务数据结构"""
    task_id: str
    data: List[Dict[str, Any]]
    spreadsheet_token: str
    table_id: str
    priority: int = 1  # 优先级，数字越小优先级越高
    max_retries: int = 3
    retry_count: int = 0
    created_at: float = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    status: SyncStatus = SyncStatus.PENDING
    error_message: Optional[str] = None
    progress: float = 0.0  # 进度百分比 0-100
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = asdict(self)
        result['status'] = self.status.value
        return result

class AsyncFeishuSyncManager:
    """异步飞书同步管理器"""
    
    def __init__(self, max_workers: int = 2, max_queue_size: int = 100):
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        self.task_queue = Queue(maxsize=max_queue_size)
        self.active_tasks: Dict[str, SyncTask] = {}
        self.completed_tasks: Dict[str, SyncTask] = {}
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.is_running = False
        self.worker_threads = []
        self._lock = threading.Lock()
        
        # 统计信息
        self.stats = {
            'total_submitted': 0,
            'total_completed': 0,
            'total_failed': 0,
            'total_cancelled': 0,
            'current_queue_size': 0,
            'active_workers': 0
        }
        
        logger.info(f"异步飞书同步管理器初始化完成，最大工作线程数: {max_workers}")
    
    def start(self):
        """启动异步同步服务"""
        if self.is_running:
            logger.warning("异步同步服务已在运行中")
            return
        
        self.is_running = True
        
        # 启动工作线程
        for i in range(self.max_workers):
            worker_thread = threading.Thread(
                target=self._worker_loop,
                name=f"FeishuSyncWorker-{i+1}",
                daemon=True
            )
            worker_thread.start()
            self.worker_threads.append(worker_thread)
        
        logger.info(f"异步飞书同步服务已启动，工作线程数: {len(self.worker_threads)}")
    
    def stop(self):
        """停止异步同步服务"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # 等待所有工作线程结束
        for thread in self.worker_threads:
            thread.join(timeout=5.0)
        
        # 关闭线程池
        self.executor.shutdown(wait=True)
        
        logger.info("异步飞书同步服务已停止")
    
    def submit_sync_task(self, 
                        task_id: str,
                        data: List[Dict[str, Any]],
                        spreadsheet_token: str,
                        table_id: str,
                        priority: int = 1,
                        max_retries: int = 3) -> bool:
        """提交同步任务到队列"""
        try:
            # 检查任务是否已存在
            if task_id in self.active_tasks or task_id in self.completed_tasks:
                logger.warning(f"任务 {task_id} 已存在，跳过提交")
                return False
            
            # 创建同步任务
            sync_task = SyncTask(
                task_id=task_id,
                data=data,
                spreadsheet_token=spreadsheet_token,
                table_id=table_id,
                priority=priority,
                max_retries=max_retries
            )
            
            # 检查队列是否已满
            if self.task_queue.qsize() >= self.max_queue_size:
                logger.error(f"任务队列已满 ({self.max_queue_size})，无法提交新任务")
                return False
            
            # 添加到队列
            self.task_queue.put(sync_task, block=False)
            
            with self._lock:
                self.active_tasks[task_id] = sync_task
                self.stats['total_submitted'] += 1
                self.stats['current_queue_size'] = self.task_queue.qsize()
            
            logger.info(f"任务 {task_id} 已提交到异步队列，数据量: {len(data)} 条")
            return True
            
        except Exception as e:
            logger.error(f"提交同步任务失败: {e}")
            return False
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        with self._lock:
            if task_id in self.active_tasks:
                return self.active_tasks[task_id].to_dict()
            elif task_id in self.completed_tasks:
                return self.completed_tasks[task_id].to_dict()
            else:
                return None
    
    def get_all_tasks_status(self) -> Dict[str, Any]:
        """获取所有任务状态"""
        with self._lock:
            active_tasks = {tid: task.to_dict() for tid, task in self.active_tasks.items()}
            completed_tasks = {tid: task.to_dict() for tid, task in self.completed_tasks.items()}
            
            return {
                'active_tasks': active_tasks,
                'completed_tasks': completed_tasks,
                'stats': self.stats.copy(),
                'service_status': {
                    'is_running': self.is_running,
                    'worker_count': len(self.worker_threads),
                    'queue_size': self.task_queue.qsize()
                }
            }
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        with self._lock:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                if task.status == SyncStatus.PENDING:
                    task.status = SyncStatus.CANCELLED
                    task.completed_at = time.time()
                    self.completed_tasks[task_id] = task
                    del self.active_tasks[task_id]
                    self.stats['total_cancelled'] += 1
                    logger.info(f"任务 {task_id} 已取消")
                    return True
                else:
                    logger.warning(f"任务 {task_id} 正在执行中，无法取消")
                    return False
            else:
                logger.warning(f"任务 {task_id} 不存在或已完成")
                return False
    
    def _worker_loop(self):
        """工作线程主循环"""
        worker_name = threading.current_thread().name
        logger.info(f"工作线程 {worker_name} 已启动")
        
        while self.is_running:
            try:
                # 从队列获取任务（超时1秒）
                try:
                    task = self.task_queue.get(timeout=1.0)
                except Empty:
                    continue
                
                # 检查任务是否被取消
                if task.status == SyncStatus.CANCELLED:
                    self.task_queue.task_done()
                    continue
                
                # 执行同步任务
                self._execute_sync_task(task, worker_name)
                self.task_queue.task_done()
                
            except Exception as e:
                logger.error(f"工作线程 {worker_name} 发生异常: {e}")
        
        logger.info(f"工作线程 {worker_name} 已停止")
    
    def _execute_sync_task(self, task: SyncTask, worker_name: str):
        """执行同步任务"""
        task_id = task.task_id
        logger.info(f"[{worker_name}] 开始执行任务 {task_id}")
        
        try:
            # 更新任务状态
            task.status = SyncStatus.RUNNING
            task.started_at = time.time()
            task.progress = 0.0
            
            with self._lock:
                self.stats['active_workers'] += 1
            
            # 导入云同步管理器
            from cloud_sync import CloudSyncManager
            from config.feishu_config import get_config as get_feishu_config
            
            # 获取飞书配置
            feishu_config = get_feishu_config()
            
            # 检查飞书配置
            if not feishu_config.get('enabled'):
                raise Exception("飞书同步未启用")
            
            required_fields = ['app_id', 'app_secret']
            missing_fields = [field for field in required_fields if not feishu_config.get(field)]
            if missing_fields:
                raise Exception(f"飞书配置不完整，缺少字段: {', '.join(missing_fields)}")
            
            # 创建同步配置
            sync_config = {
                'feishu': {
                    'enabled': True,
                    'app_id': feishu_config['app_id'],
                    'app_secret': feishu_config['app_secret'],
                    'spreadsheet_token': task.spreadsheet_token,
                    'table_id': task.table_id,
                    'base_url': 'https://open.feishu.cn/open-apis'
                }
            }
            
            # 创建同步管理器
            sync_manager = CloudSyncManager(sync_config)
            
            # 更新进度
            task.progress = 10.0
            
            # 执行同步
            logger.info(f"[{worker_name}] 任务 {task_id} 开始同步 {len(task.data)} 条数据")
            
            success = sync_manager.sync_to_feishu(
                task.data,
                task.spreadsheet_token,
                task.table_id
            )
            
            if success:
                # 同步成功
                task.status = SyncStatus.COMPLETED
                task.progress = 100.0
                task.completed_at = time.time()
                
                # 更新数据库中的同步状态
                self._update_database_sync_status(task_id)
                
                logger.info(f"[{worker_name}] 任务 {task_id} 同步成功")
                
                with self._lock:
                    self.stats['total_completed'] += 1
            else:
                # 同步失败，检查是否需要重试
                if task.retry_count < task.max_retries:
                    task.retry_count += 1
                    task.status = SyncStatus.RETRYING
                    task.progress = 0.0
                    
                    # 重新加入队列
                    self.task_queue.put(task)
                    logger.warning(f"[{worker_name}] 任务 {task_id} 同步失败，进行第 {task.retry_count} 次重试")
                    return
                else:
                    # 重试次数用完，标记为失败
                    task.status = SyncStatus.FAILED
                    task.error_message = "同步失败，已达到最大重试次数"
                    task.completed_at = time.time()
                    
                    logger.error(f"[{worker_name}] 任务 {task_id} 同步失败，已达到最大重试次数")
                    
                    with self._lock:
                        self.stats['total_failed'] += 1
            
        except Exception as e:
            # 处理异常
            task.status = SyncStatus.FAILED
            task.error_message = str(e)
            task.completed_at = time.time()
            
            logger.error(f"[{worker_name}] 任务 {task_id} 执行异常: {e}")
            
            with self._lock:
                self.stats['total_failed'] += 1
        
        finally:
            # 移动任务到完成列表
            with self._lock:
                if task_id in self.active_tasks:
                    self.completed_tasks[task_id] = self.active_tasks.pop(task_id)
                self.stats['active_workers'] -= 1
                self.stats['current_queue_size'] = self.task_queue.qsize()
    
    def _update_database_sync_status(self, task_id: str):
        """更新数据库中的同步状态"""
        try:
            from web_app_optimized import db, TweetData
            
            # 解析任务ID（可能包含前缀）
            if task_id.startswith('task_'):
                actual_task_id = int(task_id.replace('task_', ''))
            else:
                actual_task_id = int(task_id)
            
            # 更新对应任务的推文同步状态
            tweets = TweetData.query.filter_by(task_id=actual_task_id).all()
            for tweet in tweets:
                tweet.synced_to_feishu = True
            
            db.session.commit()
            logger.info(f"已更新任务 {actual_task_id} 的 {len(tweets)} 条推文同步状态")
            
        except Exception as e:
            logger.error(f"更新数据库同步状态失败: {e}")

# 全局异步同步管理器实例
_async_sync_manager: Optional[AsyncFeishuSyncManager] = None

def get_async_sync_manager() -> AsyncFeishuSyncManager:
    """获取全局异步同步管理器实例"""
    global _async_sync_manager
    if _async_sync_manager is None:
        _async_sync_manager = AsyncFeishuSyncManager(max_workers=2, max_queue_size=100)
        _async_sync_manager.start()
    return _async_sync_manager

def init_async_sync_service(max_workers_count=3, max_queue_size=100, max_retries=3):
    """初始化异步同步服务"""
    global _async_sync_manager
    if _async_sync_manager is None:
        _async_sync_manager = AsyncFeishuSyncManager(
            max_workers=max_workers_count, 
            max_queue_size=max_queue_size
        )
        _async_sync_manager.start()
        logger.info(f"异步飞书同步服务已启动，工作线程数: {max_workers_count}")
    return _async_sync_manager

def shutdown_async_sync_service():
    """关闭异步同步服务"""
    global _async_sync_manager
    if _async_sync_manager:
        _async_sync_manager.stop()
        _async_sync_manager = None
        logger.info("异步飞书同步服务已关闭")