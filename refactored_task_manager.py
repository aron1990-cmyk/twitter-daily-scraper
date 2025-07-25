#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重构的TaskManager - 解决死锁问题
主要改进：
1. 使用队列和异步处理避免锁竞争
2. 分离状态管理和任务执行
3. 使用原子操作和状态机模式
4. 减少数据库查询在锁内的执行
"""

import threading
import queue
import time
import json
import tempfile
import subprocess
import os
import logging
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple

# 配置日志
logger = logging.getLogger(__name__)

class TaskState(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"

@dataclass
class TaskRequest:
    """任务请求数据结构"""
    task_id: int
    use_background_process: bool = True
    priority: int = 0
    retry_count: int = 0
    max_retries: int = 3
    scheduled_time: Optional[datetime] = None  # 计划开始时间
    queued_at: Optional[datetime] = None  # 加入队列时间

@dataclass
class TaskSlot:
    """任务槽位数据结构"""
    task_id: int
    user_id: str
    process: Optional[subprocess.Popen] = None
    thread: Optional[threading.Thread] = None
    config_file: Optional[str] = None
    start_time: Optional[datetime] = None
    is_background: bool = True

class RefactoredTaskManager:
    """重构的任务管理器 - 无锁设计"""
    
    def __init__(self, max_concurrent_tasks=1, user_ids=None):
        # 确保用户ID池正确设置
        if user_ids and isinstance(user_ids, list) and len(user_ids) > 0:
            self.user_id_pool = list(user_ids)
            self.available_user_ids = list(user_ids)  # 兼容原API
            logger.info(f"[RefactoredTaskManager] 初始化用户ID池: {user_ids}")
        else:
            self.user_id_pool = ['default']
            self.available_user_ids = ['default']
            logger.warning(f"[RefactoredTaskManager] 使用默认用户ID: ['default']")
        
        # 修复并发控制逻辑：最大并发数不能超过可用用户ID数量
        actual_max_concurrent = min(max_concurrent_tasks, len(self.user_id_pool))
        if actual_max_concurrent != max_concurrent_tasks:
            logger.warning(f"[RefactoredTaskManager] 最大并发数从 {max_concurrent_tasks} 调整为 {actual_max_concurrent}（受用户ID数量限制）")
        
        self.max_concurrent_tasks = actual_max_concurrent
        
        logger.info(f"[RefactoredTaskManager] 最大并发任务数: {self.max_concurrent_tasks}")
        logger.info(f"[RefactoredTaskManager] 可用用户ID数量: {len(self.user_id_pool)}")
        logger.info(f"[RefactoredTaskManager] 用户ID列表: {self.user_id_pool}")
        
        # 使用线程安全的队列替代普通列表
        self.task_request_queue = queue.PriorityQueue()
        self.completion_queue = queue.Queue()
        
        # 使用原子操作的字典来管理状态
        self.active_slots: Dict[int, TaskSlot] = {}
        self.available_users = set(self.user_id_pool)
        
        # 状态锁 - 只用于关键状态更新
        self._state_lock = threading.RLock()
        
        # 启动后台处理线程
        self._running = True
        self._processor_thread = threading.Thread(target=self._process_requests, daemon=True)
        self._cleanup_thread = threading.Thread(target=self._process_completions, daemon=True)
        
        self._processor_thread.start()
        self._cleanup_thread.start()
        
        print(f"[RefactoredTaskManager] 初始化完成，最大并发: {max_concurrent_tasks}")
    
    def start_task(self, task_id: int, use_background_process: bool = True, priority: int = 0, scheduled_time: Optional[datetime] = None) -> Tuple[bool, str]:
        """启动任务（异步）"""
        try:
            # 快速检查任务是否已存在
            if task_id in self.active_slots:
                return False, "任务已在运行中"
            
            # 预检查任务是否存在（在应用上下文中进行）
            from web_app import app, ScrapingTask, db
            with app.app_context():
                task = ScrapingTask.query.get(task_id)
                if not task:
                    return False, f"任务 {task_id} 不存在"
                
                # 检查是否可以立即启动任务
                can_start_immediately = self._can_start_task()
                
                # 如果不能立即启动，设置任务状态为排队中
                if not can_start_immediately:
                    task.status = 'queued'
                    db.session.commit()
                    print(f"[RefactoredTaskManager] 任务 {task_id} 进入排队状态")
            
            # 创建任务请求并加入队列
            current_time = datetime.utcnow()
            task_request = TaskRequest(
                task_id=task_id,
                use_background_process=use_background_process,
                priority=priority,
                scheduled_time=scheduled_time or current_time,
                queued_at=current_time
            )
            
            # 使用优先级队列，按照计划时间排序
            queue_priority = (priority, task_request.scheduled_time.timestamp(), time.time())
            self.task_request_queue.put((queue_priority, task_request))
            
            queue_position = self.task_request_queue.qsize()
            if can_start_immediately:
                print(f"[RefactoredTaskManager] 任务 {task_id} 已加入处理队列，将立即执行")
                return True, "任务已加入处理队列，将立即执行"
            else:
                print(f"[RefactoredTaskManager] 任务 {task_id} 已加入排队，队列位置: {queue_position}")
                return True, f"任务已加入排队，队列位置: {queue_position}"
            
        except Exception as e:
            return False, f"任务启动失败: {str(e)}"
    
    def _process_requests(self):
        """后台线程处理任务请求"""
        while self._running:
            try:
                # 等待任务请求，超时1秒
                try:
                    queue_priority, task_request = self.task_request_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # 处理任务请求
                self._handle_task_request(task_request)
                
            except Exception as e:
                print(f"[RefactoredTaskManager] 处理请求时出错: {str(e)}")
                time.sleep(0.1)
    
    def _handle_task_request(self, task_request: TaskRequest):
        """处理单个任务请求"""
        task_id = task_request.task_id
        
        try:
            # 检查是否有可用资源
            if not self._can_start_task():
                # 重新加入队列，稍后重试（无限重试，直到有资源可用）
                task_request.retry_count += 1
                retry_delay = min(2.0 * task_request.retry_count, 10.0)  # 指数退避，最大10秒
                time.sleep(retry_delay)
                queue_priority = (task_request.priority, task_request.scheduled_time.timestamp(), time.time())
                self.task_request_queue.put((queue_priority, task_request))
                print(f"[RefactoredTaskManager] 任务 {task_id} 资源不足，重新排队 (重试 {task_request.retry_count}，延迟 {retry_delay}s)")
                return
            
            # 获取可用用户ID
            user_id = self._get_available_user_id()
            if not user_id:
                # 如果没有可用用户ID，说明所有用户ID都在使用中
                # 将任务重新排队，等待用户ID释放
                # 增加重试间隔，避免频繁重试
                retry_delay = min(2.0 * (task_request.retry_count + 1), 10.0)  # 指数退避，最大10秒
                task_request.retry_count += 1
                time.sleep(retry_delay)
                queue_priority = (task_request.priority, task_request.scheduled_time.timestamp(), time.time())
                self.task_request_queue.put((queue_priority, task_request))
                print(f"[RefactoredTaskManager] 任务 {task_id} 等待用户ID释放，重新排队 (重试 {task_request.retry_count}，延迟 {retry_delay}s)")
                return
            
            # 在应用上下文中启动任务
            from web_app import app
            from flask import has_app_context
            
            print(f"[RefactoredTaskManager] 准备启动任务 {task_id}，当前应用上下文: {has_app_context()}")
            
            with app.app_context():
                print(f"[RefactoredTaskManager] 进入应用上下文，当前应用上下文: {has_app_context()}")
                success = self._start_task_with_user(task_id, user_id, task_request.use_background_process)
            
            if not success:
                # 归还用户ID
                self._return_user_id(user_id)
                print(f"[RefactoredTaskManager] 任务 {task_id} 启动失败")
                self._update_task_status(task_id, 'failed', '任务启动失败')
            else:
                print(f"[RefactoredTaskManager] 任务 {task_id} 启动成功，用户ID: {user_id}")
            
        except Exception as e:
            print(f"[RefactoredTaskManager] 处理任务 {task_id} 时出错: {str(e)}")
            self._update_task_status(task_id, 'failed', f'处理任务时出错: {str(e)}')
    
    def _can_start_task(self) -> bool:
        """检查是否可以启动新任务"""
        return len(self.active_slots) < self.max_concurrent_tasks
    
    def can_start_task(self) -> bool:
        """检查是否可以启动新任务（公有方法，兼容原API）"""
        return self._can_start_task()
    
    def _get_available_user_id(self) -> Optional[str]:
        """获取可用的用户ID"""
        with self._state_lock:
            if self.available_users:
                user_id = self.available_users.pop()
                logger.info(f"[RefactoredTaskManager] 分配用户ID: {user_id}，剩余可用: {len(self.available_users)}")
                return user_id
            logger.warning(f"[RefactoredTaskManager] 没有可用的用户ID，当前活跃任务: {len(self.active_slots)}")
            return None
    
    def _return_user_id(self, user_id: str):
        """归还用户ID"""
        with self._state_lock:
            if user_id in self.user_id_pool:  # 确保只归还有效的用户ID
                self.available_users.add(user_id)
                logger.info(f"[RefactoredTaskManager] 归还用户ID: {user_id}，当前可用: {len(self.available_users)}")
            else:
                logger.warning(f"[RefactoredTaskManager] 尝试归还无效用户ID: {user_id}")
    
    def _start_task_with_user(self, task_id: int, user_id: str, use_background_process: bool) -> bool:
        """使用指定用户ID启动任务（需要在应用上下文中调用）"""
        try:
            # 获取任务信息（在锁外进行）
            from web_app import ScrapingTask, db
            from flask import has_app_context
            
            print(f"[RefactoredTaskManager] 检查应用上下文: {has_app_context()}")
            
            task = ScrapingTask.query.get(task_id)
            if not task:
                return False
            
            # 更新任务状态为运行中
            task.status = 'running'
            task.started_at = datetime.utcnow()
            db.session.commit()
            
            print(f"[RefactoredTaskManager] 开始启动任务 {task_id}，用户ID: {user_id}")
            
            if use_background_process:
                return self._start_background_process(task_id, user_id)
            else:
                return self._start_thread_task(task_id, user_id)
                
        except Exception as e:
            print(f"[RefactoredTaskManager] 启动任务 {task_id} 失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def _start_background_process(self, task_id: int, user_id: str) -> bool:
        """启动后台进程"""
        try:
            # 创建配置文件
            config_data = {
                'task_id': task_id,
                'task_type': 'daily',
                'kwargs': {'user_id': user_id}
            }
            
            config_file = tempfile.NamedTemporaryFile(
                mode='w', suffix='.json', delete=False, encoding='utf-8'
            )
            json.dump(config_data, config_file, ensure_ascii=False, indent=2)
            config_file.close()
            
            # 启动进程
            cmd = ['python3', 'background_task_runner.py', config_file.name]
            process = subprocess.Popen(
                cmd,
                cwd=os.path.dirname(os.path.abspath(__file__)),
                text=True
            )
            
            # 创建任务槽位
            slot = TaskSlot(
                task_id=task_id,
                user_id=user_id,
                process=process,
                config_file=config_file.name,
                start_time=datetime.utcnow(),
                is_background=True
            )
            
            # 原子性地添加到活动槽位
            with self._state_lock:
                self.active_slots[task_id] = slot
            
            print(f"[RefactoredTaskManager] 后台任务 {task_id} 启动成功，PID: {process.pid}，用户ID: {user_id}")
            logger.info(f"[RefactoredTaskManager] 当前活跃任务数: {len(self.active_slots)}/{self.max_concurrent_tasks}")
            
            # 启动监控线程
            monitor_thread = threading.Thread(
                target=self._monitor_background_task,
                args=(task_id,),
                daemon=True
            )
            monitor_thread.start()
            
            return True
            
        except Exception as e:
            print(f"[RefactoredTaskManager] 后台进程启动失败: {str(e)}")
            return False
    
    def _start_thread_task(self, task_id: int, user_id: str) -> bool:
        """启动线程任务"""
        try:
            from web_app import ScrapingTaskExecutor, app, ScrapingTask
            import asyncio
            
            def run_task():
                try:
                    with app.app_context():
                        # 在方法内部获取任务信息
                        task = ScrapingTask.query.get(task_id)
                        if not task:
                            print(f"[RefactoredTaskManager] 任务 {task_id} 不存在")
                            return
                        
                        executor = ScrapingTaskExecutor(user_id)
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(executor.execute_task(task_id))
                        loop.close()
                finally:
                    # 任务完成，加入完成队列
                    self.completion_queue.put(('thread', task_id))
            
            task_thread = threading.Thread(target=run_task, daemon=True)
            task_thread.start()
            
            # 创建任务槽位
            slot = TaskSlot(
                task_id=task_id,
                user_id=user_id,
                thread=task_thread,
                start_time=datetime.utcnow(),
                is_background=False
            )
            
            # 原子性地添加到活动槽位
            with self._state_lock:
                self.active_slots[task_id] = slot
            
            print(f"[RefactoredTaskManager] 线程任务 {task_id} 启动成功")
            return True
            
        except Exception as e:
            print(f"[RefactoredTaskManager] 线程任务启动失败: {str(e)}")
            return False
    
    def _monitor_background_task(self, task_id: int):
        """监控后台任务状态"""
        slot = self.active_slots.get(task_id)
        if not slot or not slot.process:
            return
        
        try:
            # 等待进程完成
            slot.process.wait()
            
            # 任务完成，加入完成队列
            self.completion_queue.put(('background', task_id))
            
        except Exception as e:
            print(f"[RefactoredTaskManager] 监控任务 {task_id} 时出错: {str(e)}")
            self.completion_queue.put(('background', task_id))
    
    def _process_completions(self):
        """处理任务完成事件"""
        while self._running:
            try:
                # 等待完成事件
                try:
                    task_type, task_id = self.completion_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                self._cleanup_task(task_id)
                
            except Exception as e:
                print(f"[RefactoredTaskManager] 处理完成事件时出错: {str(e)}")
    
    def _update_task_status(self, task_id: int, status: str, error_message: str = None):
        """更新任务状态"""
        try:
            from web_app import app, ScrapingTask, db
            with app.app_context():
                task = ScrapingTask.query.get(task_id)
                if task:
                    task.status = status
                    if status in ['completed', 'failed', 'stopped']:
                        task.completed_at = datetime.utcnow()
                    if error_message:
                        task.error_message = error_message
                    db.session.commit()
                    print(f"[RefactoredTaskManager] 任务 {task_id} 状态更新为: {status}")
        except Exception as e:
            print(f"[RefactoredTaskManager] 更新任务状态失败: {str(e)}")
    
    def _cleanup_task(self, task_id: int):
        """清理已完成的任务"""
        try:
            slot = self.active_slots.get(task_id)
            if not slot:
                return
            
            # 清理资源
            if slot.config_file and os.path.exists(slot.config_file):
                try:
                    os.unlink(slot.config_file)
                except:
                    pass
            
            # 归还用户ID
            self._return_user_id(slot.user_id)
            
            # 从活动槽位中移除
            with self._state_lock:
                if task_id in self.active_slots:
                    del self.active_slots[task_id]
            
            print(f"[RefactoredTaskManager] 任务 {task_id} 清理完成")
            print(f"[RefactoredTaskManager] 当前活跃任务数: {len(self.active_slots)}/{self.max_concurrent_tasks}")
            
        except Exception as e:
            print(f"[RefactoredTaskManager] 清理任务 {task_id} 时出错: {str(e)}")
    
    def stop_task(self, task_id: int) -> Tuple[bool, str]:
        """停止任务"""
        slot = self.active_slots.get(task_id)
        if not slot:
            return False, "任务未在运行中"
        
        try:
            if slot.is_background and slot.process:
                # 停止后台进程
                print(f"[RefactoredTaskManager] 停止后台进程任务 {task_id}")
                slot.process.terminate()
                try:
                    slot.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print(f"[RefactoredTaskManager] 强制杀死进程任务 {task_id}")
                    slot.process.kill()
            elif not slot.is_background and slot.thread:
                # 停止线程任务
                print(f"[RefactoredTaskManager] 停止线程任务 {task_id}")
                # 注意：Python线程无法直接强制停止，但我们可以标记任务为停止状态
                # 线程会在下次检查时自然结束
                pass
            
            # 更新数据库中的任务状态为已停止
            try:
                from web_app import ScrapingTask, db, app
                with app.app_context():
                    task = ScrapingTask.query.get(task_id)
                    if task:
                        task.status = 'stopped'
                        task.completed_at = datetime.utcnow()
                        db.session.commit()
                        print(f"[RefactoredTaskManager] 任务 {task_id} 状态已更新为停止")
            except Exception as db_e:
                print(f"[RefactoredTaskManager] 更新任务状态失败: {str(db_e)}")
            
            # 加入完成队列进行清理
            self.completion_queue.put(('stopped', task_id))
            
            print(f"[RefactoredTaskManager] 任务 {task_id} 停止请求已处理")
            return True, "任务已停止"
            
        except Exception as e:
            print(f"[RefactoredTaskManager] 停止任务 {task_id} 失败: {str(e)}")
            return False, f"停止任务失败: {str(e)}"
    
    def get_status(self) -> Dict:
        """获取管理器状态"""
        with self._state_lock:
            active_count = len(self.active_slots)
            available_users = len(self.available_users)
            queue_size = self.task_request_queue.qsize()
            
        return {
            'active_tasks': active_count,
            'max_concurrent': self.max_concurrent_tasks,
            'available_slots': self.max_concurrent_tasks - active_count,
            'available_users': available_users,
            'queue_size': queue_size,
            'active_task_ids': list(self.active_slots.keys()),
            'is_queue_active': queue_size > 0,
            'queue_status': 'active' if queue_size > 0 else 'empty'
        }
    
    def get_task_status(self) -> Dict:
        """获取任务状态（兼容原API）"""
        with self._state_lock:
            active_count = len(self.active_slots)
            available_users = len(self.available_users)
            queue_size = self.task_request_queue.qsize()
            
        return {
            'running_count': active_count,
            'thread_tasks': 0,  # 新架构中不区分线程和进程任务
            'background_tasks': active_count,
            'max_concurrent': self.max_concurrent_tasks,
            'available_slots': self.max_concurrent_tasks - active_count,
            'available_browsers': available_users,
            'running_tasks': list(self.active_slots.keys()),
            'background_task_ids': list(self.active_slots.keys()),
            'queued_tasks': queue_size,
            'queue_info': {
                'total_queued': queue_size,
                'is_processing': queue_size > 0 and active_count < self.max_concurrent_tasks,
                'queue_status': 'processing' if queue_size > 0 and active_count < self.max_concurrent_tasks else 'waiting' if queue_size > 0 else 'empty'
            }
        }
    
    def is_task_running(self, task_id: int) -> bool:
        """检查特定任务是否正在运行（兼容原API）"""
        return task_id in self.active_slots
    
    def get_running_task_count(self) -> int:
        """获取正在运行的任务数量（兼容原API）"""
        return len(self.active_slots)
    
    def get_queue_status(self) -> Dict:
        """获取队列状态（兼容原API）"""
        queue_size = self.task_request_queue.qsize()
        active_count = len(self.active_slots)
        
        return {
            'queue_length': queue_size,
            'queued_task_ids': [],  # 新架构中无法直接获取队列中的任务ID
            'estimated_wait_time': queue_size * 30 if queue_size > 0 else 0,  # 估算等待时间（秒）
            'queue_position_info': f'队列中有 {queue_size} 个任务等待执行' if queue_size > 0 else '队列为空',
            'concurrent_info': f'当前运行 {active_count}/{self.max_concurrent_tasks} 个任务'
        }
    
    def clear_queue(self):
        """清空队列（兼容原API）"""
        # 清空优先级队列
        while not self.task_request_queue.empty():
            try:
                self.task_request_queue.get_nowait()
            except queue.Empty:
                break
        print(f"[RefactoredTaskManager] 任务队列已清空")
    
    def shutdown(self):
        """关闭管理器"""
        self._running = False
        
        # 停止所有活动任务
        for task_id in list(self.active_slots.keys()):
            self.stop_task(task_id)
        
        print(f"[RefactoredTaskManager] 管理器已关闭")