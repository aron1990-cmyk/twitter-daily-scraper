#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务调度器
实现自动化日报采集的定时任务管理
"""

import asyncio
import logging
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Callable, Optional
from threading import Thread
import json
import os
from dataclasses import dataclass
from enum import Enum

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"      # 等待执行
    RUNNING = "running"      # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 执行失败
    CANCELLED = "cancelled"  # 已取消

@dataclass
class ScheduledTask:
    """定时任务数据类"""
    task_id: str
    name: str
    schedule_time: str  # cron格式或简单时间格式
    task_function: Callable
    status: TaskStatus = TaskStatus.PENDING
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    last_result: Optional[str] = None
    last_error: Optional[str] = None
    enabled: bool = True
    max_retries: int = 3
    retry_count: int = 0
    timeout_minutes: int = 60
    description: str = ""

class TaskScheduler:
    """
    定时任务调度器
    """
    
    def __init__(self, config_file: str = "scheduler_config.json"):
        self.logger = logging.getLogger('TaskScheduler')
        self.tasks: Dict[str, ScheduledTask] = {}
        self.config_file = config_file
        self.is_running = False
        self.scheduler_thread: Optional[Thread] = None
        
        # 加载配置
        self.load_config()
        
        self.logger.info("任务调度器初始化完成")
    
    def load_config(self):
        """
        加载调度器配置
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.logger.info(f"已加载调度器配置: {self.config_file}")
            except Exception as e:
                self.logger.error(f"加载配置文件失败: {e}")
        else:
            self.logger.info("配置文件不存在，使用默认配置")
    
    def save_config(self):
        """
        保存调度器配置
        """
        try:
            config = {
                'tasks': {
                    task_id: {
                        'name': task.name,
                        'schedule_time': task.schedule_time,
                        'enabled': task.enabled,
                        'max_retries': task.max_retries,
                        'timeout_minutes': task.timeout_minutes,
                        'description': task.description,
                        'run_count': task.run_count,
                        'success_count': task.success_count,
                        'failure_count': task.failure_count,
                        'last_run': task.last_run.isoformat() if task.last_run else None,
                        'last_result': task.last_result,
                        'last_error': task.last_error
                    }
                    for task_id, task in self.tasks.items()
                }
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"配置已保存到: {self.config_file}")
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {e}")
    
    def add_task(self, 
                 task_id: str,
                 name: str,
                 schedule_time: str,
                 task_function: Callable,
                 description: str = "",
                 max_retries: int = 3,
                 timeout_minutes: int = 60) -> bool:
        """
        添加定时任务
        
        Args:
            task_id: 任务唯一标识
            name: 任务名称
            schedule_time: 调度时间（支持cron格式或简单格式如"09:00"）
            task_function: 任务执行函数
            description: 任务描述
            max_retries: 最大重试次数
            timeout_minutes: 超时时间（分钟）
            
        Returns:
            是否成功添加任务
        """
        if task_id in self.tasks:
            self.logger.warning(f"任务 {task_id} 已存在")
            return False
        
        task = ScheduledTask(
            task_id=task_id,
            name=name,
            schedule_time=schedule_time,
            task_function=task_function,
            description=description,
            max_retries=max_retries,
            timeout_minutes=timeout_minutes
        )
        
        self.tasks[task_id] = task
        
        # 注册到schedule库
        self._register_schedule(task)
        
        self.logger.info(f"已添加任务: {name} ({task_id})，调度时间: {schedule_time}")
        return True
    
    def _register_schedule(self, task: ScheduledTask):
        """
        注册任务到schedule库
        
        Args:
            task: 任务对象
        """
        schedule_time = task.schedule_time.strip()
        
        try:
            if ':' in schedule_time and len(schedule_time.split(':')) == 2:
                # 简单时间格式，如 "09:00"
                schedule.every().day.at(schedule_time).do(self._execute_task, task.task_id)
                task.next_run = self._calculate_next_run(schedule_time)
            elif schedule_time.startswith('every'):
                # 间隔格式，如 "every 2 hours"
                parts = schedule_time.split()
                if len(parts) >= 3:
                    interval = int(parts[1])
                    unit = parts[2].lower()
                    
                    if unit.startswith('minute'):
                        schedule.every(interval).minutes.do(self._execute_task, task.task_id)
                    elif unit.startswith('hour'):
                        schedule.every(interval).hours.do(self._execute_task, task.task_id)
                    elif unit.startswith('day'):
                        schedule.every(interval).days.do(self._execute_task, task.task_id)
                    
                    task.next_run = datetime.now() + timedelta(minutes=interval if unit.startswith('minute') else 
                                                              interval*60 if unit.startswith('hour') else 
                                                              interval*24*60)
            else:
                self.logger.error(f"不支持的调度时间格式: {schedule_time}")
                
        except Exception as e:
            self.logger.error(f"注册任务调度失败: {e}")
    
    def _calculate_next_run(self, time_str: str) -> datetime:
        """
        计算下次执行时间
        
        Args:
            time_str: 时间字符串，如 "09:00"
            
        Returns:
            下次执行时间
        """
        try:
            hour, minute = map(int, time_str.split(':'))
            now = datetime.now()
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # 如果今天的时间已过，则安排到明天
            if next_run <= now:
                next_run += timedelta(days=1)
                
            return next_run
        except Exception as e:
            self.logger.error(f"计算下次执行时间失败: {e}")
            return datetime.now() + timedelta(hours=24)
    
    def _execute_task(self, task_id: str):
        """
        执行任务
        
        Args:
            task_id: 任务ID
        """
        if task_id not in self.tasks:
            self.logger.error(f"任务 {task_id} 不存在")
            return
        
        task = self.tasks[task_id]
        
        if not task.enabled:
            self.logger.info(f"任务 {task.name} 已禁用，跳过执行")
            return
        
        if task.status == TaskStatus.RUNNING:
            self.logger.warning(f"任务 {task.name} 正在执行中，跳过本次调度")
            return
        
        self.logger.info(f"开始执行任务: {task.name}")
        
        task.status = TaskStatus.RUNNING
        task.last_run = datetime.now()
        task.run_count += 1
        task.retry_count = 0
        
        # 异步执行任务
        asyncio.create_task(self._run_task_async(task))
    
    async def _run_task_async(self, task: ScheduledTask):
        """
        异步执行任务
        
        Args:
            task: 任务对象
        """
        try:
            # 设置超时
            result = await asyncio.wait_for(
                self._call_task_function(task),
                timeout=task.timeout_minutes * 60
            )
            
            task.status = TaskStatus.COMPLETED
            task.success_count += 1
            task.last_result = str(result) if result else "任务执行成功"
            task.last_error = None
            
            self.logger.info(f"任务 {task.name} 执行成功")
            
        except asyncio.TimeoutError:
            error_msg = f"任务 {task.name} 执行超时（{task.timeout_minutes}分钟）"
            self.logger.error(error_msg)
            await self._handle_task_failure(task, error_msg)
            
        except Exception as e:
            error_msg = f"任务 {task.name} 执行失败: {str(e)}"
            self.logger.error(error_msg)
            await self._handle_task_failure(task, error_msg)
        
        finally:
            # 更新下次执行时间
            task.next_run = self._calculate_next_run(task.schedule_time)
            
            # 保存配置
            self.save_config()
    
    async def _call_task_function(self, task: ScheduledTask):
        """
        调用任务函数
        
        Args:
            task: 任务对象
            
        Returns:
            任务执行结果
        """
        if asyncio.iscoroutinefunction(task.task_function):
            return await task.task_function()
        else:
            return task.task_function()
    
    async def _handle_task_failure(self, task: ScheduledTask, error_msg: str):
        """
        处理任务失败
        
        Args:
            task: 任务对象
            error_msg: 错误信息
        """
        task.last_error = error_msg
        task.retry_count += 1
        
        if task.retry_count <= task.max_retries:
            self.logger.info(f"任务 {task.name} 将在5分钟后重试（{task.retry_count}/{task.max_retries}）")
            task.status = TaskStatus.PENDING
            
            # 5分钟后重试
            await asyncio.sleep(300)
            await self._run_task_async(task)
        else:
            task.status = TaskStatus.FAILED
            task.failure_count += 1
            self.logger.error(f"任务 {task.name} 重试次数已达上限，标记为失败")
    
    def start_scheduler(self):
        """
        启动调度器
        """
        if self.is_running:
            self.logger.warning("调度器已在运行中")
            return
        
        self.is_running = True
        self.scheduler_thread = Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info("任务调度器已启动")
    
    def _run_scheduler(self):
        """
        运行调度器主循环
        """
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"调度器运行异常: {e}")
                time.sleep(10)
    
    def stop_scheduler(self):
        """
        停止调度器
        """
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        self.logger.info("任务调度器已停止")
    
    def remove_task(self, task_id: str) -> bool:
        """
        移除任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功移除
        """
        if task_id not in self.tasks:
            self.logger.warning(f"任务 {task_id} 不存在")
            return False
        
        task = self.tasks[task_id]
        
        # 如果任务正在运行，先取消
        if task.status == TaskStatus.RUNNING:
            task.status = TaskStatus.CANCELLED
        
        del self.tasks[task_id]
        
        # 清除schedule中的任务
        schedule.clear(task_id)
        
        self.logger.info(f"已移除任务: {task.name}")
        return True
    
    def enable_task(self, task_id: str) -> bool:
        """
        启用任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功启用
        """
        if task_id not in self.tasks:
            return False
        
        self.tasks[task_id].enabled = True
        self.logger.info(f"已启用任务: {self.tasks[task_id].name}")
        return True
    
    def disable_task(self, task_id: str) -> bool:
        """
        禁用任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功禁用
        """
        if task_id not in self.tasks:
            return False
        
        self.tasks[task_id].enabled = False
        self.logger.info(f"已禁用任务: {self.tasks[task_id].name}")
        return True
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态信息
        """
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        return {
            'task_id': task.task_id,
            'name': task.name,
            'status': task.status.value,
            'enabled': task.enabled,
            'schedule_time': task.schedule_time,
            'last_run': task.last_run.isoformat() if task.last_run else None,
            'next_run': task.next_run.isoformat() if task.next_run else None,
            'run_count': task.run_count,
            'success_count': task.success_count,
            'failure_count': task.failure_count,
            'success_rate': task.success_count / task.run_count if task.run_count > 0 else 0,
            'last_result': task.last_result,
            'last_error': task.last_error,
            'description': task.description
        }
    
    def get_all_tasks_status(self) -> List[Dict[str, Any]]:
        """
        获取所有任务状态
        
        Returns:
            所有任务状态列表
        """
        return [self.get_task_status(task_id) for task_id in self.tasks.keys()]
    
    def run_task_now(self, task_id: str) -> bool:
        """
        立即执行任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功启动任务
        """
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        
        if task.status == TaskStatus.RUNNING:
            self.logger.warning(f"任务 {task.name} 正在执行中")
            return False
        
        self.logger.info(f"手动执行任务: {task.name}")
        self._execute_task(task_id)
        return True
    
    def get_scheduler_statistics(self) -> Dict[str, Any]:
        """
        获取调度器统计信息
        
        Returns:
            调度器统计信息
        """
        total_tasks = len(self.tasks)
        enabled_tasks = sum(1 for task in self.tasks.values() if task.enabled)
        running_tasks = sum(1 for task in self.tasks.values() if task.status == TaskStatus.RUNNING)
        
        total_runs = sum(task.run_count for task in self.tasks.values())
        total_successes = sum(task.success_count for task in self.tasks.values())
        total_failures = sum(task.failure_count for task in self.tasks.values())
        
        success_rate = total_successes / total_runs if total_runs > 0 else 0
        
        # 找出下次执行的任务
        next_tasks = [
            task for task in self.tasks.values() 
            if task.enabled and task.next_run and task.status != TaskStatus.RUNNING
        ]
        next_task = min(next_tasks, key=lambda x: x.next_run) if next_tasks else None
        
        return {
            'total_tasks': total_tasks,
            'enabled_tasks': enabled_tasks,
            'running_tasks': running_tasks,
            'total_runs': total_runs,
            'total_successes': total_successes,
            'total_failures': total_failures,
            'overall_success_rate': round(success_rate, 3),
            'scheduler_running': self.is_running,
            'next_task': {
                'name': next_task.name,
                'next_run': next_task.next_run.isoformat()
            } if next_task else None
        }
    
    def export_task_report(self) -> Dict[str, Any]:
        """
        导出任务执行报告
        
        Returns:
            详细的任务执行报告
        """
        statistics = self.get_scheduler_statistics()
        task_details = self.get_all_tasks_status()
        
        # 按成功率排序任务
        task_details.sort(key=lambda x: x['success_rate'], reverse=True)
        
        return {
            'report_generated_at': datetime.now().isoformat(),
            'scheduler_statistics': statistics,
            'task_details': task_details,
            'recommendations': self._generate_scheduler_recommendations()
        }
    
    def _generate_scheduler_recommendations(self) -> List[str]:
        """
        生成调度器优化建议
        
        Returns:
            建议列表
        """
        recommendations = []
        
        # 检查失败率高的任务
        high_failure_tasks = [
            task for task in self.tasks.values()
            if task.run_count > 0 and task.failure_count / task.run_count > 0.3
        ]
        if high_failure_tasks:
            recommendations.append(f"有 {len(high_failure_tasks)} 个任务失败率较高，建议检查任务配置")
        
        # 检查长时间未运行的任务
        stale_tasks = [
            task for task in self.tasks.values()
            if task.enabled and task.last_run and 
            (datetime.now() - task.last_run).days > 7
        ]
        if stale_tasks:
            recommendations.append(f"有 {len(stale_tasks)} 个任务超过7天未运行，建议检查调度配置")
        
        # 检查禁用的任务
        disabled_tasks = [task for task in self.tasks.values() if not task.enabled]
        if disabled_tasks:
            recommendations.append(f"有 {len(disabled_tasks)} 个任务被禁用，如不需要可考虑删除")
        
        return recommendations

# 预定义的任务函数
class PredefinedTasks:
    """
    预定义的常用任务
    """
    
    @staticmethod
    async def daily_twitter_scraping():
        """
        每日Twitter采集任务
        """
        from main import TwitterDailyScraper
        
        scraper = TwitterDailyScraper()
        try:
            output_file = await scraper.run_scraping_task()
            return f"采集完成，输出文件: {output_file}"
        except Exception as e:
            raise Exception(f"采集任务失败: {e}")
    
    @staticmethod
    async def weekly_report_generation():
        """
        每周报告生成任务
        """
        # 这里可以实现周报生成逻辑
        return "周报生成完成"
    
    @staticmethod
    async def system_health_check():
        """
        系统健康检查任务
        """
        # 检查系统状态、磁盘空间、日志文件等
        return "系统健康检查完成"
    
    @staticmethod
    async def data_backup():
        """
        数据备份任务
        """
        # 实现数据备份逻辑
        return "数据备份完成"