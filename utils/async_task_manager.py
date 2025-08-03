#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异步任务管理器
负责处理Excel写入、飞书同步、SQLite插入等异步任务
"""

import asyncio
import threading
import logging
import time
import uuid
import json
import sqlite3
from typing import Dict, List, Optional, Callable, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import aiofiles
import aiofiles.os
from queue import Queue, PriorityQueue
import traceback
from cachetools import LRUCache  # P0优化：引入LRU缓存
import gc  # P0优化：引入垃圾回收

# P0+优化：Redis存储支持
try:
    import redis
    import aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None
    aioredis = None

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"      # 等待执行
    RUNNING = "running"      # 正在执行
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 执行失败
    CANCELLED = "cancelled"  # 已取消
    RETRYING = "retrying"    # 重试中

class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 3
    NORMAL = 2
    HIGH = 1
    URGENT = 0

class TaskType(Enum):
    """任务类型枚举"""
    EXCEL_WRITE = "excel_write"
    FEISHU_SYNC = "feishu_sync"
    SQLITE_INSERT = "sqlite_insert"
    FILE_OPERATION = "file_operation"
    DATA_PROCESSING = "data_processing"
    CUSTOM = "custom"

@dataclass
class AsyncTask:
    """异步任务数据结构"""
    task_id: str
    task_type: TaskType
    priority: TaskPriority
    func: Callable
    args: tuple = ()
    kwargs: dict = None
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: Optional[float] = None
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    retry_count: int = 0
    progress: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = {}
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}
    
    def __lt__(self, other):
        """用于优先级队列排序"""
        return self.priority.value < other.priority.value
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        # 处理不可序列化的字段
        data['func'] = f"{self.func.__module__}.{self.func.__name__}"
        data['task_type'] = self.task_type.value
        data['priority'] = self.priority.value
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat() if self.created_at else None
        data['started_at'] = self.started_at.isoformat() if self.started_at else None
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        return data

class AsyncTaskManager:
    """
    异步任务管理器
    支持优先级队列、重试机制、进度跟踪、并发控制
    """
    
    def __init__(self, max_workers: int = 4, max_concurrent_tasks: int = 10):
        self.logger = logging.getLogger('AsyncTaskManager')
        self.max_workers = max_workers
        self.max_concurrent_tasks = max_concurrent_tasks
        
        # 任务队列和存储
        self.task_queue = PriorityQueue()
        self.active_tasks: Dict[str, AsyncTask] = {}
        # P0+优化：进一步压缩LRU缓存大小
        self.completed_tasks = LRUCache(maxsize=500)  # P0+优化：从1000压缩到500条
        self.failed_tasks = LRUCache(maxsize=200)  # P0+优化：从500压缩到200条
        
        # 线程池和事件循环
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self.event_loop = None
        self.loop_thread = None
        
        # 控制标志
        self.is_running = False
        self.is_paused = False
        self._shutdown_event = threading.Event()
        
        # P0+优化：增强清理配置
        self.cleanup_interval_hours = 0.5  # P0+优化：每30分钟清理一次
        self.last_cleanup_time = datetime.now()
        self.memory_cleanup_threshold_mb = 50  # P0+优化：内存清理阈值降低到50MB
        
        # P0+优化：Redis存储配置
        self.redis_enabled = REDIS_AVAILABLE
        self.redis_client = None
        self.redis_key_prefix = "twitter_tasks:"
        self.redis_ttl = 3600  # Redis键过期时间（秒）
        
        # 统计信息
        self.stats = {
            'total_submitted': 0,
            'total_completed': 0,
            'total_failed': 0,
            'total_cancelled': 0,
            'total_retries': 0,
            'average_execution_time': 0.0,
            'peak_concurrent_tasks': 0,
            'start_time': None
        }
        
        # 任务回调
        self.task_callbacks: Dict[str, List[Callable]] = {
            'on_task_start': [],
            'on_task_complete': [],
            'on_task_fail': [],
            'on_task_retry': []
        }
        
        self.logger.info(f"异步任务管理器初始化完成 (最大工作线程: {max_workers}, 最大并发任务: {max_concurrent_tasks})")
    
    def start(self):
        """启动任务管理器"""
        if self.is_running:
            self.logger.warning("任务管理器已在运行")
            return
        
        self.is_running = True
        self.stats['start_time'] = datetime.now()
        
        # 启动事件循环线程
        self.loop_thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.loop_thread.start()
        
        # P0+优化：初始化Redis连接
        if self.redis_enabled:
            try:
                self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
                # 测试连接
                self.redis_client.ping()
                self.logger.info("Redis连接成功，启用任务持久化存储")
            except Exception as e:
                self.logger.warning(f"Redis连接失败，禁用持久化存储: {e}")
                self.redis_enabled = False
                self.redis_client = None
        
        # P0+优化：启动定期清理任务
        if self.event_loop:
            asyncio.run_coroutine_threadsafe(self._periodic_cleanup(), self.event_loop)
        
        self.logger.info("异步任务管理器已启动")
    
    def stop(self, timeout: float = 30.0):
        """停止任务管理器"""
        if not self.is_running:
            return
        
        self.logger.info("正在停止异步任务管理器...")
        self.is_running = False
        self._shutdown_event.set()
        
        # 等待所有活跃任务完成
        start_time = time.time()
        while self.active_tasks and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        # 关闭线程池
        self.thread_pool.shutdown(wait=True)
        
        # 停止事件循环
        if self.event_loop and self.event_loop.is_running():
            self.event_loop.call_soon_threadsafe(self.event_loop.stop)
        
        if self.loop_thread and self.loop_thread.is_alive():
            self.loop_thread.join(timeout=5.0)
        
        self.logger.info("异步任务管理器已停止")
    
    def _run_event_loop(self):
        """运行事件循环"""
        self.event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.event_loop)
        
        try:
            # 启动任务处理协程和定期清理协程
            self.event_loop.run_until_complete(
                asyncio.gather(
                    self._process_tasks(),
                    self._periodic_cleanup()
                )
            )
        except Exception as e:
            self.logger.error(f"事件循环异常: {e}")
        finally:
            self.event_loop.close()
    
    async def _process_tasks(self):
        """处理任务队列"""
        while self.is_running:
            try:
                # 检查是否暂停
                if self.is_paused:
                    await asyncio.sleep(0.1)
                    continue
                
                # 检查并发限制
                if len(self.active_tasks) >= self.max_concurrent_tasks:
                    await asyncio.sleep(0.1)
                    continue
                
                # 获取任务
                if self.task_queue.empty():
                    await asyncio.sleep(0.1)
                    continue
                
                try:
                    task = self.task_queue.get_nowait()
                    await self._execute_task(task)
                except:
                    await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"任务处理异常: {e}")
                await asyncio.sleep(1.0)
    
    async def _execute_task(self, task: AsyncTask):
        """执行单个任务"""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        self.active_tasks[task.task_id] = task
        
        # 更新统计
        self.stats['peak_concurrent_tasks'] = max(
            self.stats['peak_concurrent_tasks'], 
            len(self.active_tasks)
        )
        
        # 触发开始回调
        self._trigger_callbacks('on_task_start', task)
        
        try:
            # 在线程池中执行任务
            if asyncio.iscoroutinefunction(task.func):
                # 异步函数
                if task.timeout:
                    result = await asyncio.wait_for(
                        task.func(*task.args, **task.kwargs),
                        timeout=task.timeout
                    )
                else:
                    result = await task.func(*task.args, **task.kwargs)
            else:
                # 同步函数
                loop = asyncio.get_event_loop()
                if task.timeout:
                    result = await asyncio.wait_for(
                        loop.run_in_executor(
                            self.thread_pool,
                            lambda: task.func(*task.args, **task.kwargs)
                        ),
                        timeout=task.timeout
                    )
                else:
                    result = await loop.run_in_executor(
                        self.thread_pool,
                        lambda: task.func(*task.args, **task.kwargs)
                    )
            
            # 任务成功完成
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.progress = 100.0
            
            # 移动到完成列表
            self.completed_tasks[task.task_id] = task
            self.stats['total_completed'] += 1
            
            # 更新平均执行时间
            execution_time = (task.completed_at - task.started_at).total_seconds()
            self._update_average_execution_time(execution_time)
            
            # 触发完成回调
            self._trigger_callbacks('on_task_complete', task)
            
            self.logger.debug(f"任务完成: {task.task_id} ({task.task_type.value})")
            
        except asyncio.TimeoutError:
            await self._handle_task_failure(task, "任务执行超时")
        except Exception as e:
            await self._handle_task_failure(task, str(e))
        finally:
            # 从活跃任务中移除
            self.active_tasks.pop(task.task_id, None)
    
    async def _handle_task_failure(self, task: AsyncTask, error_msg: str):
        """处理任务失败"""
        task.error = error_msg
        task.retry_count += 1
        
        # 检查是否需要重试
        if task.retry_count <= task.max_retries:
            task.status = TaskStatus.RETRYING
            self.stats['total_retries'] += 1
            
            # 触发重试回调
            self._trigger_callbacks('on_task_retry', task)
            
            self.logger.warning(f"任务重试 ({task.retry_count}/{task.max_retries}): {task.task_id}, 错误: {error_msg}")
            
            # 延迟后重新加入队列
            await asyncio.sleep(task.retry_delay * task.retry_count)
            task.status = TaskStatus.PENDING
            self.task_queue.put(task)
        else:
            # 重试次数用尽，标记为失败
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            
            self.failed_tasks[task.task_id] = task
            self.stats['total_failed'] += 1
            
            # 触发失败回调
            self._trigger_callbacks('on_task_fail', task)
            
            self.logger.error(f"任务失败: {task.task_id}, 最终错误: {error_msg}")
    
    def submit_task(self, 
                   func: Callable,
                   args: tuple = (),
                   kwargs: dict = None,
                   task_type: TaskType = TaskType.CUSTOM,
                   priority: TaskPriority = TaskPriority.NORMAL,
                   max_retries: int = 3,
                   retry_delay: float = 1.0,
                   timeout: Optional[float] = None,
                   metadata: Dict[str, Any] = None) -> str:
        """
        提交任务到队列
        
        Args:
            func: 要执行的函数
            args: 函数参数
            kwargs: 函数关键字参数
            task_type: 任务类型
            priority: 任务优先级
            max_retries: 最大重试次数
            retry_delay: 重试延迟
            timeout: 超时时间
            metadata: 元数据
            
        Returns:
            任务ID
        """
        task_id = str(uuid.uuid4())
        
        task = AsyncTask(
            task_id=task_id,
            task_type=task_type,
            priority=priority,
            func=func,
            args=args,
            kwargs=kwargs or {},
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout,
            metadata=metadata or {}
        )
        
        self.task_queue.put(task)
        self.stats['total_submitted'] += 1
        
        self.logger.debug(f"任务已提交: {task_id} ({task_type.value}, 优先级: {priority.value})")
        return task_id
    
    def submit_excel_write(self, file_path: str, data: Any, **kwargs) -> str:
        """提交Excel写入任务"""
        return self.submit_task(
            func=self._write_excel,
            args=(file_path, data),
            kwargs=kwargs,
            task_type=TaskType.EXCEL_WRITE,
            priority=TaskPriority.NORMAL,
            timeout=60.0,
            metadata={'file_path': file_path, 'data_size': len(str(data))}
        )
    
    def submit_feishu_sync(self, data: Any, **kwargs) -> str:
        """提交飞书同步任务"""
        return self.submit_task(
            func=self._sync_to_feishu,
            args=(data,),
            kwargs=kwargs,
            task_type=TaskType.FEISHU_SYNC,
            priority=TaskPriority.HIGH,
            timeout=120.0,
            metadata={'data_size': len(str(data))}
        )
    
    def submit_sqlite_insert(self, db_path: str, table: str, data: Any, **kwargs) -> str:
        """提交SQLite插入任务"""
        return self.submit_task(
            func=self._insert_to_sqlite,
            args=(db_path, table, data),
            kwargs=kwargs,
            task_type=TaskType.SQLITE_INSERT,
            priority=TaskPriority.NORMAL,
            timeout=30.0,
            metadata={'db_path': db_path, 'table': table, 'data_size': len(str(data))}
        )
    
    async def _write_excel(self, file_path: str, data: Any, **kwargs):
        """P0+优化：使用openpyxl流式处理异步写入Excel文件，减少内存占用"""
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment
            
            # 确保目录存在
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # P0+优化：标准化数据格式，避免Pandas大对象
            if hasattr(data, 'to_dict'):
                # Pandas DataFrame
                data_list = data.to_dict('records')
                columns = list(data.columns)
            elif isinstance(data, list):
                data_list = data
                columns = list(data[0].keys()) if data else []
            elif isinstance(data, dict):
                data_list = [data]
                columns = list(data.keys())
            else:
                raise ValueError(f"不支持的数据类型: {type(data)}")
            
            # P0+优化：分块处理大数据集
            chunk_size = kwargs.get('chunk_size', 1000)
            sheet_name = kwargs.get('sheet_name', 'Sheet1')
            
            # 异步写入文件
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._write_excel_streaming,
                file_path, data_list, columns, sheet_name, chunk_size
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Excel写入失败: {file_path}, 错误: {e}")
            raise
    
    def _write_excel_streaming(self, file_path: str, data_list: list, columns: list, sheet_name: str, chunk_size: int):
        """P0+优化：流式写入Excel，分块处理以减少内存占用"""
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment
        
        wb = Workbook()
        ws = wb.active
        ws.title = sheet_name
        
        # 写入表头
        for col_idx, column in enumerate(columns, 1):
            cell = ws.cell(row=1, column=col_idx, value=column)
            # P0+优化：简化样式以减少内存
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color='CCCCCC', end_color='CCCCCC', fill_type='solid')
        
        # P0+优化：分块写入数据，及时释放内存
        total_rows = 0
        for chunk_start in range(0, len(data_list), chunk_size):
            chunk_end = min(chunk_start + chunk_size, len(data_list))
            chunk_data = data_list[chunk_start:chunk_end]
            
            for row_idx, row_data in enumerate(chunk_data, start=total_rows + 2):
                for col_idx, column in enumerate(columns, 1):
                    value = row_data.get(column, '')
                    # P0+优化：限制单元格内容长度以减少内存
                    if isinstance(value, str) and len(value) > 1000:
                        value = value[:1000] + '...'
                    ws.cell(row=row_idx, column=col_idx, value=value)
            
            total_rows += len(chunk_data)
            
            # P0+优化：每处理一个chunk后强制垃圾回收
            if chunk_start > 0 and chunk_start % (chunk_size * 5) == 0:
                import gc
                gc.collect()
        
        # 保存文件
        wb.save(file_path)
        
        # P0+优化：及时释放工作簿对象
        wb.close()
        del wb
        
        return {'file_path': file_path, 'rows': total_rows}
    
    async def _sync_to_feishu(self, data: Any, **kwargs):
        """异步同步到飞书"""
        try:
            # 这里应该调用实际的飞书同步逻辑
            # 暂时模拟异步操作
            await asyncio.sleep(1.0)  # 模拟网络请求
            
            # 实际实现应该调用飞书API
            # from async_feishu_sync import AsyncFeishuSyncManager
            # sync_manager = AsyncFeishuSyncManager()
            # result = await sync_manager.sync_data(data, **kwargs)
            
            return {'status': 'success', 'data_size': len(str(data))}
            
        except Exception as e:
            self.logger.error(f"飞书同步失败: {e}")
            raise
    
    async def _insert_to_sqlite(self, db_path: str, table: str, data: Any, **kwargs):
        """异步插入SQLite数据库"""
        try:
            # 确保数据库目录存在
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            
            loop = asyncio.get_event_loop()
            
            def _sync_insert():
                conn = sqlite3.connect(db_path)
                try:
                    cursor = conn.cursor()
                    
                    if isinstance(data, list):
                        # 批量插入
                        if data and isinstance(data[0], dict):
                            columns = list(data[0].keys())
                            placeholders = ','.join(['?' for _ in columns])
                            sql = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})"
                            
                            values = [tuple(row[col] for col in columns) for row in data]
                            cursor.executemany(sql, values)
                        else:
                            raise ValueError("列表数据必须包含字典")
                    elif isinstance(data, dict):
                        # 单条插入
                        columns = list(data.keys())
                        placeholders = ','.join(['?' for _ in columns])
                        sql = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})"
                        
                        values = tuple(data[col] for col in columns)
                        cursor.execute(sql, values)
                    else:
                        raise ValueError(f"不支持的数据类型: {type(data)}")
                    
                    conn.commit()
                    return cursor.rowcount
                    
                finally:
                    conn.close()
            
            rows_affected = await loop.run_in_executor(None, _sync_insert)
            return {'db_path': db_path, 'table': table, 'rows_affected': rows_affected}
            
        except Exception as e:
            self.logger.error(f"SQLite插入失败: {db_path}.{table}, 错误: {e}")
            raise
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        # 检查活跃任务
        if task_id in self.active_tasks:
            return self.active_tasks[task_id].to_dict()
        
        # 检查完成任务
        if task_id in self.completed_tasks:
            return self.completed_tasks[task_id].to_dict()
        
        # 检查失败任务
        if task_id in self.failed_tasks:
            return self.failed_tasks[task_id].to_dict()
        
        # 检查队列中的任务
        with self.task_queue.mutex:
            for task in self.task_queue.queue:
                if task.task_id == task_id:
                    return task.to_dict()
        
        return None
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        # 检查队列中的任务
        with self.task_queue.mutex:
            queue_items = list(self.task_queue.queue)
            self.task_queue.queue.clear()
            
            cancelled = False
            for task in queue_items:
                if task.task_id == task_id:
                    task.status = TaskStatus.CANCELLED
                    task.completed_at = datetime.now()
                    self.stats['total_cancelled'] += 1
                    cancelled = True
                    self.logger.info(f"任务已取消: {task_id}")
                else:
                    self.task_queue.put(task)
            
            return cancelled
        
        # 活跃任务无法取消（已在执行中）
        return False
    
    def pause(self):
        """暂停任务处理"""
        self.is_paused = True
        self.logger.info("任务处理已暂停")
    
    def resume(self):
        """恢复任务处理"""
        self.is_paused = False
        self.logger.info("任务处理已恢复")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        current_time = datetime.now()
        uptime = (current_time - self.stats['start_time']).total_seconds() if self.stats['start_time'] else 0
        
        return {
            'uptime_seconds': uptime,
            'is_running': self.is_running,
            'is_paused': self.is_paused,
            'queue_size': self.task_queue.qsize(),
            'active_tasks': len(self.active_tasks),
            'completed_tasks': len(self.completed_tasks),
            'failed_tasks': len(self.failed_tasks),
            'total_submitted': self.stats['total_submitted'],
            'total_completed': self.stats['total_completed'],
            'total_failed': self.stats['total_failed'],
            'total_cancelled': self.stats['total_cancelled'],
            'total_retries': self.stats['total_retries'],
            'success_rate': (self.stats['total_completed'] / max(1, self.stats['total_submitted'])) * 100,
            'average_execution_time': self.stats['average_execution_time'],
            'peak_concurrent_tasks': self.stats['peak_concurrent_tasks'],
            'current_concurrent_tasks': len(self.active_tasks)
        }
    
    def get_task_list(self, status: Optional[TaskStatus] = None, 
                     task_type: Optional[TaskType] = None,
                     limit: int = 100) -> List[Dict[str, Any]]:
        """获取任务列表"""
        tasks = []
        
        # 收集所有任务
        all_tasks = []
        all_tasks.extend(self.active_tasks.values())
        all_tasks.extend(self.completed_tasks.values())
        all_tasks.extend(self.failed_tasks.values())
        
        # 添加队列中的任务
        with self.task_queue.mutex:
            all_tasks.extend(list(self.task_queue.queue))
        
        # 过滤任务
        for task in all_tasks:
            if status and task.status != status:
                continue
            if task_type and task.task_type != task_type:
                continue
            
            tasks.append(task.to_dict())
        
        # 按创建时间排序并限制数量
        tasks.sort(key=lambda x: x['created_at'], reverse=True)
        return tasks[:limit]
    
    def add_callback(self, event: str, callback: Callable):
        """添加任务回调"""
        if event in self.task_callbacks:
            self.task_callbacks[event].append(callback)
        else:
            self.logger.warning(f"未知的回调事件: {event}")
    
    def _trigger_callbacks(self, event: str, task: AsyncTask):
        """触发回调函数"""
        for callback in self.task_callbacks.get(event, []):
            try:
                callback(task)
            except Exception as e:
                self.logger.error(f"回调函数执行失败: {event}, 错误: {e}")
    
    def _update_average_execution_time(self, execution_time: float):
        """更新平均执行时间"""
        if self.stats['total_completed'] == 1:
            self.stats['average_execution_time'] = execution_time
        else:
            # 使用移动平均
            alpha = 0.1  # 平滑因子
            self.stats['average_execution_time'] = (
                alpha * execution_time + 
                (1 - alpha) * self.stats['average_execution_time']
            )
    
    async def clear_completed_tasks(self, older_than_hours: int = 0.5):  # P0+优化：默认0.5小时
        """P0+优化：清理已完成和失败的任务，增加Redis存储和激进内存清理"""
        try:
            import psutil
            memory_before = psutil.virtual_memory().percent
        except ImportError:
            memory_before = 0
            
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        
        # P0+优化：记录清理前的任务数量
        initial_completed = len(self.completed_tasks)
        initial_failed = len(self.failed_tasks)
        
        # P0+优化：将重要任务存储到Redis（如果可用）
        redis_stored = 0
        if self.redis_enabled and self.redis_client:
            try:
                for task_id in list(self.completed_tasks.keys()):
                    task = self.completed_tasks.get(task_id)
                    if task and task.completed_at and task.completed_at < cutoff_time:
                        # 存储重要任务到Redis
                        if task.task_type in [TaskType.EXCEL_WRITE, TaskType.FEISHU_SYNC]:
                            redis_key = f"{self.redis_key_prefix}:completed:{task_id}"
                            task_data = json.dumps(task.to_dict(), default=str)
                            self.redis_client.setex(redis_key, self.redis_ttl, task_data)
                            redis_stored += 1
            except Exception as e:
                self.logger.warning(f"Redis存储失败: {e}")
        
        # P0+优化：激进清理超时任务
        completed_to_remove = []
        for task_id in list(self.completed_tasks.keys()):
            task = self.completed_tasks.get(task_id)
            if task and task.completed_at and task.completed_at < cutoff_time:
                completed_to_remove.append(task_id)
        
        for task_id in completed_to_remove:
            if task_id in self.completed_tasks:
                del self.completed_tasks[task_id]
        
        failed_to_remove = []
        for task_id in list(self.failed_tasks.keys()):
            task = self.failed_tasks.get(task_id)
            if task and task.completed_at and task.completed_at < cutoff_time:
                failed_to_remove.append(task_id)
        
        for task_id in failed_to_remove:
            if task_id in self.failed_tasks:
                del self.failed_tasks[task_id]
        
        # P0+优化：清理内存中的大对象
        for task_list in [self.completed_tasks, self.failed_tasks]:
            for task in task_list.values():
                if hasattr(task, 'result') and task.result:
                    # 清理大结果对象
                    if isinstance(task.result, (list, dict)) and len(str(task.result)) > 1000:
                        task.result = "[已清理大对象以节省内存]"
        
        # P0+优化：多次强制垃圾回收
        for _ in range(3):
            gc.collect()
        
        # P0+优化：记录清理后的内存使用
        try:
            import psutil
            memory_after = psutil.virtual_memory().percent
            memory_saved = memory_before - memory_after
        except ImportError:
            memory_after = 0
            memory_saved = 0
        
        self.logger.info(
            f"[P0+优化] 任务清理完成: 已完成任务 {initial_completed}→{len(self.completed_tasks)}, "
            f"失败任务 {initial_failed}→{len(self.failed_tasks)}, Redis存储 {redis_stored}条, "
            f"内存使用 {memory_before:.1f}%→{memory_after:.1f}% (节省 {memory_saved:.1f}%)"
        )
        
        self.last_cleanup_time = datetime.now()
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
    
    async def _periodic_cleanup(self):
        """P0优化：定期清理任务，增加内存监控"""
        while self.is_running:
            try:
                # P0优化：缩短检查间隔从1小时到30分钟
                await asyncio.sleep(1800)  # 每30分钟检查一次
                
                try:
                    import psutil
                    current_memory = psutil.virtual_memory().percent
                except ImportError:
                    current_memory = 0
                
                # P0优化：检查是否需要清理（时间或内存阈值）
                time_condition = (datetime.now() - self.last_cleanup_time).total_seconds() >= self.cleanup_interval_hours * 3600
                memory_condition = current_memory > 70  # 内存使用超过70%时强制清理
                
                if time_condition or memory_condition:
                    reason = "定时清理" if time_condition else f"内存清理(当前{current_memory:.1f}%)"
                    self.logger.info(f"[P0优化] 触发{reason}")
                    await self.clear_completed_tasks()
                    
            except Exception as e:
                self.logger.error(f"[P0优化] 定期清理任务出错: {e}")


# 全局任务管理器实例
_task_manager = None

def get_task_manager() -> AsyncTaskManager:
    """获取全局任务管理器实例"""
    global _task_manager
    if _task_manager is None:
        _task_manager = AsyncTaskManager()
        _task_manager.start()
    return _task_manager


# 使用示例
if __name__ == "__main__":
    import pandas as pd
    
    # 创建任务管理器
    with AsyncTaskManager(max_workers=2) as task_manager:
        # 提交Excel写入任务
        data = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
        excel_task_id = task_manager.submit_excel_write('/tmp/test.xlsx', data)
        
        # 提交SQLite插入任务
        sqlite_data = [{'name': 'Alice', 'age': 25}, {'name': 'Bob', 'age': 30}]
        sqlite_task_id = task_manager.submit_sqlite_insert('/tmp/test.db', 'users', sqlite_data)
        
        # 等待任务完成
        time.sleep(5)
        
        # 获取统计信息
        stats = task_manager.get_statistics()
        print(f"统计信息: {stats}")
        
        # 获取任务状态
        excel_status = task_manager.get_task_status(excel_task_id)
        print(f"Excel任务状态: {excel_status['status'] if excel_status else 'Not found'}")