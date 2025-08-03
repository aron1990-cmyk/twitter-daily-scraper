#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多博主并行抓取任务系统
支持在单个任务中同时抓取多个博主，自动拆分为子任务并行执行

功能特性：
1. 单任务多博主：一个任务可以包含多个博主
2. 自动任务拆分：根据博主数量自动创建子任务
3. 并行执行：多个子任务使用不同浏览器窗口并行抓取
4. 队列管理：当窗口不足时，子任务进入队列等待
5. 进度统计：实时统计主任务和子任务的进度
6. 失败重试：子任务失败时可以单独重试
"""

import json
import logging
import threading
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskType(Enum):
    """任务类型"""
    SINGLE_BLOGGER = "single_blogger"  # 单博主任务
    MULTI_BLOGGER = "multi_blogger"    # 多博主任务
    SUB_TASK = "sub_task"              # 子任务

class SubTaskStatus(Enum):
    """子任务状态"""
    PENDING = "pending"      # 等待中
    QUEUED = "queued"        # 排队中
    RUNNING = "running"      # 运行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 失败
    STOPPED = "stopped"      # 已停止

@dataclass
class BloggerTarget:
    """博主目标配置"""
    username: str           # 博主用户名
    display_name: str = "" # 显示名称
    max_tweets: int = 100   # 该博主的最大抓取数量
    min_likes: int = 0      # 最小点赞数
    min_retweets: int = 0   # 最小转发数
    keywords: List[str] = None  # 该博主特定的关键词过滤
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if not self.display_name:
            self.display_name = self.username

@dataclass
class SubTask:
    """子任务数据结构"""
    id: int                    # 子任务ID
    parent_task_id: int        # 父任务ID
    blogger: BloggerTarget     # 目标博主
    status: SubTaskStatus      # 状态
    user_id: Optional[str] = None  # 分配的用户ID
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    tweets_collected: int = 0  # 已收集推文数
    error_message: str = ""    # 错误信息
    retry_count: int = 0       # 重试次数
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class MultiTaskProgress:
    """多任务进度统计"""
    total_bloggers: int = 0        # 总博主数
    completed_bloggers: int = 0    # 已完成博主数
    failed_bloggers: int = 0       # 失败博主数
    running_bloggers: int = 0      # 运行中博主数
    queued_bloggers: int = 0       # 排队中博主数
    total_tweets: int = 0          # 总推文数
    collected_tweets: int = 0      # 已收集推文数
    
    @property
    def completion_rate(self) -> float:
        """完成率"""
        if self.total_bloggers == 0:
            return 0.0
        return (self.completed_bloggers / self.total_bloggers) * 100
    
    @property
    def tweet_collection_rate(self) -> float:
        """推文收集率"""
        if self.total_tweets == 0:
            return 0.0
        return (self.collected_tweets / self.total_tweets) * 100

class MultiBloggerTaskManager:
    """多博主任务管理器"""
    
    def __init__(self, base_task_manager):
        """
        初始化多博主任务管理器
        
        Args:
            base_task_manager: 基础任务管理器实例（RefactoredTaskManager）
        """
        self.base_task_manager = base_task_manager
        self.multi_tasks: Dict[int, Dict] = {}  # {parent_task_id: task_info}
        self.sub_tasks: Dict[int, SubTask] = {}  # {sub_task_id: SubTask}
        self.task_id_counter = 10000  # 子任务ID计数器，从10000开始避免冲突
        self.lock = threading.RLock()
        
        logger.info("多博主任务管理器初始化完成")
    
    def create_multi_blogger_task(self, 
                                  task_name: str,
                                  bloggers: List[BloggerTarget],
                                  global_keywords: List[str] = None,
                                  description: str = "") -> Tuple[bool, str, Optional[int]]:
        """
        创建多博主任务
        
        Args:
            task_name: 任务名称
            bloggers: 博主列表
            global_keywords: 全局关键词（应用于所有博主）
            description: 任务描述
            
        Returns:
            (success, message, parent_task_id)
        """
        try:
            if not bloggers:
                return False, "博主列表不能为空", None
            
            if len(bloggers) == 1:
                return False, "单个博主请使用普通任务创建方式", None
            
            # 创建父任务记录
            from web_app_optimized import app, ScrapingTask, db
            
            with app.app_context():
                # 计算总推文数
                total_tweets = sum(blogger.max_tweets for blogger in bloggers)
                
                # 创建父任务
                parent_task = ScrapingTask(
                    name=task_name,
                    description=f"{description}\n[多博主任务] 包含 {len(bloggers)} 个博主",
                    target_accounts=json.dumps([blogger.username for blogger in bloggers]),
                    target_keywords=json.dumps(global_keywords or []),
                    max_tweets=total_tweets,
                    task_type='multi_blogger',
                    status='pending'
                )
                
                db.session.add(parent_task)
                db.session.commit()
                
                parent_task_id = parent_task.id
            
            # 创建子任务
            sub_tasks = []
            with self.lock:
                for blogger in bloggers:
                    self.task_id_counter += 1
                    sub_task = SubTask(
                        id=self.task_id_counter,
                        parent_task_id=parent_task_id,
                        blogger=blogger,
                        status=SubTaskStatus.PENDING
                    )
                    sub_tasks.append(sub_task)
                    self.sub_tasks[sub_task.id] = sub_task
                
                # 记录多任务信息
                self.multi_tasks[parent_task_id] = {
                    'name': task_name,
                    'description': description,
                    'bloggers': bloggers,
                    'global_keywords': global_keywords or [],
                    'sub_task_ids': [st.id for st in sub_tasks],
                    'created_at': datetime.now(),
                    'status': 'pending'
                }
            
            logger.info(f"多博主任务创建成功: {task_name}, 父任务ID: {parent_task_id}, 子任务数: {len(sub_tasks)}")
            return True, f"成功创建多博主任务，包含 {len(bloggers)} 个博主", parent_task_id
            
        except Exception as e:
            logger.error(f"创建多博主任务失败: {e}")
            return False, f"创建失败: {str(e)}", None
    
    def start_multi_blogger_task(self, parent_task_id: int) -> Tuple[bool, str]:
        """
        启动多博主任务
        
        Args:
            parent_task_id: 父任务ID
            
        Returns:
            (success, message)
        """
        try:
            if parent_task_id not in self.multi_tasks:
                return False, "多博主任务不存在"
            
            task_info = self.multi_tasks[parent_task_id]
            sub_task_ids = task_info['sub_task_ids']
            
            # 更新父任务状态
            self._update_parent_task_status(parent_task_id, 'running')
            task_info['status'] = 'running'
            
            # 启动所有子任务
            started_count = 0
            queued_count = 0
            
            for sub_task_id in sub_task_ids:
                success, message = self._start_sub_task(sub_task_id)
                if success:
                    if "排队" in message:
                        queued_count += 1
                    else:
                        started_count += 1
                else:
                    logger.warning(f"子任务 {sub_task_id} 启动失败: {message}")
            
            total_sub_tasks = len(sub_task_ids)
            result_message = f"多博主任务启动完成: {started_count} 个子任务立即启动, {queued_count} 个子任务进入队列, 共 {total_sub_tasks} 个子任务"
            
            logger.info(result_message)
            return True, result_message
            
        except Exception as e:
            logger.error(f"启动多博主任务失败: {e}")
            return False, f"启动失败: {str(e)}"
    
    def _start_sub_task(self, sub_task_id: int) -> Tuple[bool, str]:
        """
        启动单个子任务
        
        Args:
            sub_task_id: 子任务ID
            
        Returns:
            (success, message)
        """
        try:
            if sub_task_id not in self.sub_tasks:
                return False, "子任务不存在"
            
            sub_task = self.sub_tasks[sub_task_id]
            
            if sub_task.status != SubTaskStatus.PENDING:
                return False, f"子任务状态不正确: {sub_task.status.value}"
            
            # 创建子任务的数据库记录
            success, db_task_id = self._create_sub_task_db_record(sub_task)
            if not success:
                return False, "创建子任务数据库记录失败"
            
            # 使用基础任务管理器启动子任务
            success, message = self.base_task_manager.start_task(db_task_id)
            
            if success:
                if "排队" in message:
                    sub_task.status = SubTaskStatus.QUEUED
                    logger.info(f"子任务 {sub_task_id} ({sub_task.blogger.username}) 进入队列")
                    return True, f"子任务 {sub_task.blogger.username} 已加入队列"
                else:
                    sub_task.status = SubTaskStatus.RUNNING
                    sub_task.started_at = datetime.now()
                    logger.info(f"子任务 {sub_task_id} ({sub_task.blogger.username}) 启动成功")
                    return True, f"子任务 {sub_task.blogger.username} 启动成功"
            else:
                sub_task.status = SubTaskStatus.FAILED
                sub_task.error_message = message
                logger.error(f"子任务 {sub_task_id} ({sub_task.blogger.username}) 启动失败: {message}")
                return False, f"子任务 {sub_task.blogger.username} 启动失败: {message}"
                
        except Exception as e:
            logger.error(f"启动子任务失败: {e}")
            return False, f"启动失败: {str(e)}"
    
    def _create_sub_task_db_record(self, sub_task: SubTask) -> Tuple[bool, Optional[int]]:
        """
        为子任务创建数据库记录
        
        Args:
            sub_task: 子任务对象
            
        Returns:
            (success, db_task_id)
        """
        try:
            from web_app_optimized import app, ScrapingTask, db
            
            with app.app_context():
                # 合并全局关键词和博主特定关键词
                parent_info = self.multi_tasks[sub_task.parent_task_id]
                all_keywords = list(set(parent_info['global_keywords'] + sub_task.blogger.keywords))
                
                db_task = ScrapingTask(
                    name=f"[子任务] {parent_info['name']} - {sub_task.blogger.display_name}",
                    description=f"多博主任务的子任务，目标博主: {sub_task.blogger.username}",
                    target_accounts=json.dumps([sub_task.blogger.username]),
                    target_keywords=json.dumps(all_keywords),
                    max_tweets=sub_task.blogger.max_tweets,
                    min_likes=sub_task.blogger.min_likes,
                    min_retweets=sub_task.blogger.min_retweets,
                    task_type='sub_task',
                    parent_task_id=sub_task.parent_task_id,
                    status='pending'
                )
                
                db.session.add(db_task)
                db.session.commit()
                
                return True, db_task.id
                
        except Exception as e:
            logger.error(f"创建子任务数据库记录失败: {e}")
            return False, None
    
    def get_multi_task_progress(self, parent_task_id: int) -> Optional[MultiTaskProgress]:
        """
        获取多任务进度
        
        Args:
            parent_task_id: 父任务ID
            
        Returns:
            MultiTaskProgress对象或None
        """
        try:
            if parent_task_id not in self.multi_tasks:
                return None
            
            task_info = self.multi_tasks[parent_task_id]
            sub_task_ids = task_info['sub_task_ids']
            
            progress = MultiTaskProgress()
            progress.total_bloggers = len(sub_task_ids)
            
            for sub_task_id in sub_task_ids:
                sub_task = self.sub_tasks[sub_task_id]
                
                # 统计状态
                if sub_task.status == SubTaskStatus.COMPLETED:
                    progress.completed_bloggers += 1
                elif sub_task.status == SubTaskStatus.FAILED:
                    progress.failed_bloggers += 1
                elif sub_task.status == SubTaskStatus.RUNNING:
                    progress.running_bloggers += 1
                elif sub_task.status in [SubTaskStatus.QUEUED, SubTaskStatus.PENDING]:
                    progress.queued_bloggers += 1
                
                # 统计推文
                progress.total_tweets += sub_task.blogger.max_tweets
                progress.collected_tweets += sub_task.tweets_collected
            
            return progress
            
        except Exception as e:
            logger.error(f"获取多任务进度失败: {e}")
            return None
    
    def stop_multi_blogger_task(self, parent_task_id: int) -> Tuple[bool, str]:
        """
        停止多博主任务
        
        Args:
            parent_task_id: 父任务ID
            
        Returns:
            (success, message)
        """
        try:
            if parent_task_id not in self.multi_tasks:
                return False, "多博主任务不存在"
            
            task_info = self.multi_tasks[parent_task_id]
            sub_task_ids = task_info['sub_task_ids']
            
            stopped_count = 0
            for sub_task_id in sub_task_ids:
                sub_task = self.sub_tasks[sub_task_id]
                if sub_task.status in [SubTaskStatus.RUNNING, SubTaskStatus.QUEUED]:
                    # 这里需要实现停止子任务的逻辑
                    # 可以通过基础任务管理器停止对应的数据库任务
                    sub_task.status = SubTaskStatus.STOPPED
                    stopped_count += 1
            
            # 更新父任务状态
            self._update_parent_task_status(parent_task_id, 'stopped')
            task_info['status'] = 'stopped'
            
            message = f"多博主任务已停止，共停止 {stopped_count} 个子任务"
            logger.info(message)
            return True, message
            
        except Exception as e:
            logger.error(f"停止多博主任务失败: {e}")
            return False, f"停止失败: {str(e)}"
    
    def _update_parent_task_status(self, parent_task_id: int, status: str):
        """
        更新父任务状态
        
        Args:
            parent_task_id: 父任务ID
            status: 新状态
        """
        try:
            from web_app_optimized import app, ScrapingTask, db
            
            with app.app_context():
                task = ScrapingTask.query.get(parent_task_id)
                if task:
                    task.status = status
                    if status in ['completed', 'failed', 'stopped']:
                        task.completed_at = datetime.now()
                    elif status == 'running':
                        task.started_at = datetime.now()
                    db.session.commit()
                    
        except Exception as e:
            logger.error(f"更新父任务状态失败: {e}")
    
    def get_multi_task_list(self) -> List[Dict]:
        """
        获取所有多博主任务列表
        
        Returns:
            任务列表
        """
        result = []
        
        for parent_task_id, task_info in self.multi_tasks.items():
            progress = self.get_multi_task_progress(parent_task_id)
            
            result.append({
                'parent_task_id': parent_task_id,
                'name': task_info['name'],
                'description': task_info['description'],
                'status': task_info['status'],
                'created_at': task_info['created_at'],
                'blogger_count': len(task_info['bloggers']),
                'bloggers': [blogger.username for blogger in task_info['bloggers']],
                'progress': {
                    'completion_rate': progress.completion_rate if progress else 0,
                    'tweet_collection_rate': progress.tweet_collection_rate if progress else 0,
                    'completed_bloggers': progress.completed_bloggers if progress else 0,
                    'total_bloggers': progress.total_bloggers if progress else 0,
                    'collected_tweets': progress.collected_tweets if progress else 0,
                    'total_tweets': progress.total_tweets if progress else 0
                }
            })
        
        return result
    
    def retry_failed_sub_task(self, sub_task_id: int) -> Tuple[bool, str]:
        """
        重试失败的子任务
        
        Args:
            sub_task_id: 子任务ID
            
        Returns:
            (success, message)
        """
        try:
            if sub_task_id not in self.sub_tasks:
                return False, "子任务不存在"
            
            sub_task = self.sub_tasks[sub_task_id]
            
            if sub_task.status != SubTaskStatus.FAILED:
                return False, f"子任务状态不是失败状态: {sub_task.status.value}"
            
            # 重置子任务状态
            sub_task.status = SubTaskStatus.PENDING
            sub_task.retry_count += 1
            sub_task.error_message = ""
            sub_task.started_at = None
            sub_task.completed_at = None
            
            # 重新启动子任务
            return self._start_sub_task(sub_task_id)
            
        except Exception as e:
            logger.error(f"重试子任务失败: {e}")
            return False, f"重试失败: {str(e)}"

# 全局多博主任务管理器实例
multi_blogger_manager = None

def init_multi_blogger_manager(base_task_manager):
    """
    初始化多博主任务管理器
    
    Args:
        base_task_manager: 基础任务管理器实例
    """
    global multi_blogger_manager
    
    if multi_blogger_manager is None:
        multi_blogger_manager = MultiBloggerTaskManager(base_task_manager)
        logger.info("多博主任务管理器已初始化")
    else:
        logger.warning("多博主任务管理器已存在，跳过初始化")

def get_multi_blogger_manager() -> Optional[MultiBloggerTaskManager]:
    """
    获取多博主任务管理器实例
    
    Returns:
        MultiBloggerTaskManager实例或None
    """
    return multi_blogger_manager

if __name__ == "__main__":
    # 测试代码
    print("多博主并行抓取任务系统")
    print("支持功能:")
    print("1. 单任务多博主配置")
    print("2. 自动任务拆分")
    print("3. 并行执行管理")
    print("4. 队列调度")
    print("5. 进度统计")
    print("6. 失败重试")