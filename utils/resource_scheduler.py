#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统资源调度管理器
基于CPU/内存/硬盘使用情况的智能任务调度
"""

import psutil
import logging
import time
import threading
import asyncio
from typing import Dict, List, Optional, Callable, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
import statistics
from collections import deque

class ResourceLevel(Enum):
    """资源使用级别"""
    LOW = "low"          # 低使用率 (0-40%)
    MODERATE = "moderate" # 中等使用率 (40-70%)
    HIGH = "high"        # 高使用率 (70-85%)
    CRITICAL = "critical" # 临界使用率 (85-100%)

class ScheduleAction(Enum):
    """调度动作"""
    ALLOW = "allow"           # 允许执行
    THROTTLE = "throttle"     # 限流执行
    PAUSE = "pause"           # 暂停执行
    EMERGENCY_STOP = "stop"   # 紧急停止

@dataclass
class ResourceThresholds:
    """P0+优化：资源阈值配置（降低内存阈值）"""
    cpu_low: float = 40.0
    cpu_moderate: float = 70.0
    cpu_high: float = 85.0
    cpu_critical: float = 95.0
    
    # P0+优化：降低内存阈值以更早触发清理
    memory_low: float = 35.0      # 从40.0降低到35.0
    memory_moderate: float = 60.0  # 从70.0降低到60.0
    memory_high: float = 75.0      # 从85.0降低到75.0
    memory_critical: float = 85.0  # 从95.0降低到85.0
    
    disk_low: float = 60.0
    disk_moderate: float = 80.0
    disk_high: float = 90.0
    disk_critical: float = 95.0
    
    # 网络阈值 (MB/s)
    network_low: float = 10.0
    network_moderate: float = 50.0
    network_high: float = 100.0
    network_critical: float = 200.0

@dataclass
class ResourceMetrics:
    """资源指标"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    load_average: Tuple[float, float, float]
    process_count: int
    temperature: Optional[float] = None
    
    def get_overall_level(self, thresholds: ResourceThresholds) -> ResourceLevel:
        """获取整体资源使用级别"""
        levels = [
            self._get_cpu_level(thresholds),
            self._get_memory_level(thresholds),
            self._get_disk_level(thresholds)
        ]
        
        # 取最高级别
        if ResourceLevel.CRITICAL in levels:
            return ResourceLevel.CRITICAL
        elif ResourceLevel.HIGH in levels:
            return ResourceLevel.HIGH
        elif ResourceLevel.MODERATE in levels:
            return ResourceLevel.MODERATE
        else:
            return ResourceLevel.LOW
    
    def _get_cpu_level(self, thresholds: ResourceThresholds) -> ResourceLevel:
        if self.cpu_percent >= thresholds.cpu_critical:
            return ResourceLevel.CRITICAL
        elif self.cpu_percent >= thresholds.cpu_high:
            return ResourceLevel.HIGH
        elif self.cpu_percent >= thresholds.cpu_moderate:
            return ResourceLevel.MODERATE
        else:
            return ResourceLevel.LOW
    
    def _get_memory_level(self, thresholds: ResourceThresholds) -> ResourceLevel:
        if self.memory_percent >= thresholds.memory_critical:
            return ResourceLevel.CRITICAL
        elif self.memory_percent >= thresholds.memory_high:
            return ResourceLevel.HIGH
        elif self.memory_percent >= thresholds.memory_moderate:
            return ResourceLevel.MODERATE
        else:
            return ResourceLevel.LOW
    
    def _get_disk_level(self, thresholds: ResourceThresholds) -> ResourceLevel:
        if self.disk_percent >= thresholds.disk_critical:
            return ResourceLevel.CRITICAL
        elif self.disk_percent >= thresholds.disk_high:
            return ResourceLevel.HIGH
        elif self.disk_percent >= thresholds.disk_moderate:
            return ResourceLevel.MODERATE
        else:
            return ResourceLevel.LOW

@dataclass
class ScheduleDecision:
    """调度决策"""
    action: ScheduleAction
    reason: str
    resource_level: ResourceLevel
    max_concurrent_tasks: int
    delay_seconds: float
    priority_boost: bool = False
    
class ResourceScheduler:
    """
    系统资源调度管理器
    监控系统资源并做出智能调度决策
    """
    
    def __init__(self, 
                 monitor_interval: float = 5.0,
                 history_size: int = 100,
                 thresholds: Optional[ResourceThresholds] = None):
        self.logger = logging.getLogger('ResourceScheduler')
        self.monitor_interval = monitor_interval
        self.history_size = history_size
        self.thresholds = thresholds or ResourceThresholds()
        
        # 资源监控数据
        self.metrics_history: deque = deque(maxlen=history_size)
        self.current_metrics: Optional[ResourceMetrics] = None
        
        # 监控控制
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # P0+优化：调度策略配置（降低并发任务数）
        self.schedule_config = {
            ResourceLevel.LOW: {
                'max_concurrent_tasks': 6,  # 从10降低到6
                'delay_seconds': 0.0,
                'action': ScheduleAction.ALLOW
            },
            ResourceLevel.MODERATE: {
                'max_concurrent_tasks': 4,  # 从6降低到4
                'delay_seconds': 2.0,        # 从1.0增加到2.0
                'action': ScheduleAction.THROTTLE
            },
            ResourceLevel.HIGH: {
                'max_concurrent_tasks': 2,  # 从3降低到2
                'delay_seconds': 5.0,        # 从3.0增加到5.0
                'action': ScheduleAction.THROTTLE
            },
            ResourceLevel.CRITICAL: {
                'max_concurrent_tasks': 1,  # 保持1不变
                'delay_seconds': 15.0,       # 从10.0增加到15.0
                'action': ScheduleAction.PAUSE
            }
        }
        
        # 统计信息
        self.stats = {
            'total_decisions': 0,
            'allow_count': 0,
            'throttle_count': 0,
            'pause_count': 0,
            'emergency_stop_count': 0,
            'average_cpu': 0.0,
            'average_memory': 0.0,
            'average_disk': 0.0,
            'peak_cpu': 0.0,
            'peak_memory': 0.0,
            'peak_disk': 0.0,
            'start_time': None
        }
        
        # 回调函数
        self.callbacks = {
            'on_resource_critical': [],
            'on_resource_normal': [],
            'on_schedule_decision': []
        }
        
        # 初始化网络IO基线
        self._network_baseline = self._get_network_io()
        self._disk_baseline = self._get_disk_io()
        
        self.logger.info("资源调度管理器初始化完成")
    
    def start_monitoring(self):
        """启动资源监控"""
        if self.is_monitoring:
            self.logger.warning("资源监控已在运行")
            return
        
        self.is_monitoring = True
        self.stats['start_time'] = datetime.now()
        self._stop_event.clear()
        
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        self.logger.info("资源监控已启动")
    
    def stop_monitoring(self):
        """停止资源监控"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        self._stop_event.set()
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=10.0)
        
        self.logger.info("资源监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.is_monitoring and not self._stop_event.is_set():
            try:
                # 收集资源指标
                metrics = self._collect_metrics()
                self.current_metrics = metrics
                self.metrics_history.append(metrics)
                
                # 更新统计信息
                self._update_statistics(metrics)
                
                # 检查资源状态变化
                self._check_resource_alerts(metrics)
                
                # 等待下次监控
                self._stop_event.wait(self.monitor_interval)
                
            except Exception as e:
                self.logger.error(f"资源监控异常: {e}")
                time.sleep(self.monitor_interval)
    
    def _collect_metrics(self) -> ResourceMetrics:
        """收集系统资源指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1.0)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # 磁盘使用率
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # 磁盘IO
            disk_io = self._get_disk_io()
            disk_io_read_mb = (disk_io.read_bytes - self._disk_baseline.read_bytes) / 1024 / 1024
            disk_io_write_mb = (disk_io.write_bytes - self._disk_baseline.write_bytes) / 1024 / 1024
            
            # 网络IO
            network_io = self._get_network_io()
            network_sent_mb = (network_io.bytes_sent - self._network_baseline.bytes_sent) / 1024 / 1024
            network_recv_mb = (network_io.bytes_recv - self._network_baseline.bytes_recv) / 1024 / 1024
            
            # 系统负载
            try:
                load_average = psutil.getloadavg()
            except AttributeError:
                # Windows系统不支持getloadavg
                load_average = (0.0, 0.0, 0.0)
            
            # 进程数量
            process_count = len(psutil.pids())
            
            # CPU温度（如果可用）
            temperature = self._get_cpu_temperature()
            
            return ResourceMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_percent=disk_percent,
                disk_io_read_mb=max(0, disk_io_read_mb),
                disk_io_write_mb=max(0, disk_io_write_mb),
                network_sent_mb=max(0, network_sent_mb),
                network_recv_mb=max(0, network_recv_mb),
                load_average=load_average,
                process_count=process_count,
                temperature=temperature
            )
            
        except Exception as e:
            self.logger.error(f"收集资源指标失败: {e}")
            # 返回默认值
            return ResourceMetrics(
                timestamp=datetime.now(),
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_percent=0.0,
                disk_io_read_mb=0.0,
                disk_io_write_mb=0.0,
                network_sent_mb=0.0,
                network_recv_mb=0.0,
                load_average=(0.0, 0.0, 0.0),
                process_count=0
            )
    
    def _get_disk_io(self):
        """获取磁盘IO统计"""
        try:
            return psutil.disk_io_counters()
        except:
            # 创建默认对象
            from collections import namedtuple
            DiskIO = namedtuple('DiskIO', ['read_bytes', 'write_bytes'])
            return DiskIO(0, 0)
    
    def _get_network_io(self):
        """获取网络IO统计"""
        try:
            return psutil.net_io_counters()
        except:
            # 创建默认对象
            from collections import namedtuple
            NetworkIO = namedtuple('NetworkIO', ['bytes_sent', 'bytes_recv'])
            return NetworkIO(0, 0)
    
    def _get_cpu_temperature(self) -> Optional[float]:
        """获取CPU温度"""
        try:
            if hasattr(psutil, 'sensors_temperatures'):
                temps = psutil.sensors_temperatures()
                if temps:
                    # 尝试获取CPU温度
                    for name, entries in temps.items():
                        if 'cpu' in name.lower() or 'core' in name.lower():
                            if entries:
                                return entries[0].current
            return None
        except:
            return None
    
    def _update_statistics(self, metrics: ResourceMetrics):
        """更新统计信息"""
        if len(self.metrics_history) > 1:
            cpu_values = [m.cpu_percent for m in self.metrics_history]
            memory_values = [m.memory_percent for m in self.metrics_history]
            disk_values = [m.disk_percent for m in self.metrics_history]
            
            self.stats['average_cpu'] = statistics.mean(cpu_values)
            self.stats['average_memory'] = statistics.mean(memory_values)
            self.stats['average_disk'] = statistics.mean(disk_values)
            
            self.stats['peak_cpu'] = max(cpu_values)
            self.stats['peak_memory'] = max(memory_values)
            self.stats['peak_disk'] = max(disk_values)
    
    def _check_resource_alerts(self, metrics: ResourceMetrics):
        """检查资源告警"""
        resource_level = metrics.get_overall_level(self.thresholds)
        
        # 触发相应回调
        if resource_level == ResourceLevel.CRITICAL:
            self._trigger_callbacks('on_resource_critical', metrics)
        elif resource_level == ResourceLevel.LOW:
            self._trigger_callbacks('on_resource_normal', metrics)
    
    def make_schedule_decision(self, task_type: str = "default", 
                             task_priority: int = 1) -> ScheduleDecision:
        """
        做出调度决策
        
        Args:
            task_type: 任务类型
            task_priority: 任务优先级 (1=高, 2=中, 3=低)
            
        Returns:
            调度决策
        """
        if not self.current_metrics:
            # 没有监控数据，允许执行
            decision = ScheduleDecision(
                action=ScheduleAction.ALLOW,
                reason="无监控数据",
                resource_level=ResourceLevel.LOW,
                max_concurrent_tasks=5,
                delay_seconds=0.0
            )
        else:
            resource_level = self.current_metrics.get_overall_level(self.thresholds)
            config = self.schedule_config[resource_level]
            
            # 根据任务优先级调整
            max_tasks = config['max_concurrent_tasks']
            delay = config['delay_seconds']
            
            if task_priority == 1:  # 高优先级
                max_tasks = min(max_tasks + 2, 10)
                delay = max(delay - 1.0, 0.0)
            elif task_priority == 3:  # 低优先级
                max_tasks = max(max_tasks - 1, 1)
                delay = delay + 1.0
            
            # 特殊情况处理
            action = config['action']
            reason = f"资源使用率: CPU {self.current_metrics.cpu_percent:.1f}%, 内存 {self.current_metrics.memory_percent:.1f}%, 磁盘 {self.current_metrics.disk_percent:.1f}%"
            
            # P0+优化：降低紧急情况触发阈值，增强内存压力响应
            if (self.current_metrics.cpu_percent > 95 or 
                self.current_metrics.memory_percent > 90 or  # 从98降低到90
                self.current_metrics.disk_percent > 95):
                action = ScheduleAction.EMERGENCY_STOP
                reason += " - 系统资源极度紧张"
                max_tasks = 0
                delay = 60.0
            # P0+优化：内存压力下的额外限制
            elif self.current_metrics.memory_percent > 80:
                if action == ScheduleAction.ALLOW:
                    action = ScheduleAction.THROTTLE
                max_tasks = max(max_tasks - 2, 1)  # 进一步减少并发任务
                delay = max(delay + 2.0, 5.0)  # 增加延迟
                reason += " - 内存压力较大，限制任务执行"
            
            decision = ScheduleDecision(
                action=action,
                reason=reason,
                resource_level=resource_level,
                max_concurrent_tasks=max_tasks,
                delay_seconds=delay,
                priority_boost=(task_priority == 1 and resource_level != ResourceLevel.CRITICAL)
            )
        
        # 更新统计
        self.stats['total_decisions'] += 1
        if decision.action == ScheduleAction.ALLOW:
            self.stats['allow_count'] += 1
        elif decision.action == ScheduleAction.THROTTLE:
            self.stats['throttle_count'] += 1
        elif decision.action == ScheduleAction.PAUSE:
            self.stats['pause_count'] += 1
        elif decision.action == ScheduleAction.EMERGENCY_STOP:
            self.stats['emergency_stop_count'] += 1
        
        # 触发决策回调
        self._trigger_callbacks('on_schedule_decision', decision)
        
        self.logger.debug(f"调度决策: {decision.action.value}, 原因: {decision.reason}")
        return decision
    
    def get_resource_status(self) -> Dict[str, Any]:
        """获取当前资源状态"""
        if not self.current_metrics:
            return {'status': 'no_data', 'message': '暂无监控数据'}
        
        resource_level = self.current_metrics.get_overall_level(self.thresholds)
        
        return {
            'status': 'ok',
            'timestamp': self.current_metrics.timestamp.isoformat(),
            'resource_level': resource_level.value,
            'cpu_percent': self.current_metrics.cpu_percent,
            'memory_percent': self.current_metrics.memory_percent,
            'disk_percent': self.current_metrics.disk_percent,
            'load_average': self.current_metrics.load_average,
            'process_count': self.current_metrics.process_count,
            'temperature': self.current_metrics.temperature,
            'disk_io': {
                'read_mb': self.current_metrics.disk_io_read_mb,
                'write_mb': self.current_metrics.disk_io_write_mb
            },
            'network_io': {
                'sent_mb': self.current_metrics.network_sent_mb,
                'recv_mb': self.current_metrics.network_recv_mb
            },
            'recommendations': self._get_recommendations()
        }
    
    def _get_recommendations(self) -> List[str]:
        """获取优化建议"""
        if not self.current_metrics:
            return []
        
        recommendations = []
        
        if self.current_metrics.cpu_percent > 80:
            recommendations.append("CPU使用率过高，建议减少并发任务")
        
        if self.current_metrics.memory_percent > 80:
            recommendations.append("内存使用率过高，建议清理内存或重启浏览器实例")
        
        if self.current_metrics.disk_percent > 85:
            recommendations.append("磁盘空间不足，建议清理临时文件")
        
        if self.current_metrics.process_count > 500:
            recommendations.append("进程数量过多，建议检查是否有僵尸进程")
        
        if self.current_metrics.temperature and self.current_metrics.temperature > 80:
            recommendations.append("CPU温度过高，建议降低系统负载")
        
        if not recommendations:
            recommendations.append("系统运行状态良好")
        
        return recommendations
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        uptime = 0
        if self.stats['start_time']:
            uptime = (datetime.now() - self.stats['start_time']).total_seconds()
        
        return {
            'uptime_seconds': uptime,
            'is_monitoring': self.is_monitoring,
            'metrics_count': len(self.metrics_history),
            'total_decisions': self.stats['total_decisions'],
            'decision_distribution': {
                'allow': self.stats['allow_count'],
                'throttle': self.stats['throttle_count'],
                'pause': self.stats['pause_count'],
                'emergency_stop': self.stats['emergency_stop_count']
            },
            'resource_averages': {
                'cpu': round(self.stats['average_cpu'], 2),
                'memory': round(self.stats['average_memory'], 2),
                'disk': round(self.stats['average_disk'], 2)
            },
            'resource_peaks': {
                'cpu': round(self.stats['peak_cpu'], 2),
                'memory': round(self.stats['peak_memory'], 2),
                'disk': round(self.stats['peak_disk'], 2)
            },
            'current_status': self.get_resource_status()
        }
    
    def get_resource_history(self, minutes: int = 60) -> List[Dict[str, Any]]:
        """获取资源历史数据"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        history = []
        for metrics in self.metrics_history:
            if metrics.timestamp >= cutoff_time:
                history.append({
                    'timestamp': metrics.timestamp.isoformat(),
                    'cpu_percent': metrics.cpu_percent,
                    'memory_percent': metrics.memory_percent,
                    'disk_percent': metrics.disk_percent,
                    'load_average': metrics.load_average,
                    'process_count': metrics.process_count,
                    'resource_level': metrics.get_overall_level(self.thresholds).value
                })
        
        return history
    
    def update_thresholds(self, **kwargs):
        """更新资源阈值"""
        for key, value in kwargs.items():
            if hasattr(self.thresholds, key):
                setattr(self.thresholds, key, value)
                self.logger.info(f"已更新阈值: {key} = {value}")
            else:
                self.logger.warning(f"未知的阈值参数: {key}")
    
    def update_schedule_config(self, resource_level: ResourceLevel, **kwargs):
        """更新调度配置"""
        if resource_level in self.schedule_config:
            self.schedule_config[resource_level].update(kwargs)
            self.logger.info(f"已更新调度配置: {resource_level.value} = {kwargs}")
        else:
            self.logger.warning(f"未知的资源级别: {resource_level}")
    
    def add_callback(self, event: str, callback: Callable):
        """添加回调函数"""
        if event in self.callbacks:
            self.callbacks[event].append(callback)
        else:
            self.logger.warning(f"未知的回调事件: {event}")
    
    def _trigger_callbacks(self, event: str, data: Any):
        """触发回调函数"""
        for callback in self.callbacks.get(event, []):
            try:
                callback(data)
            except Exception as e:
                self.logger.error(f"回调函数执行失败: {event}, 错误: {e}")
    
    def force_gc(self):
        """强制垃圾回收"""
        import gc
        collected = gc.collect()
        self.logger.info(f"强制垃圾回收完成，回收对象数: {collected}")
        return collected
    
    def __enter__(self):
        self.start_monitoring()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_monitoring()


# 全局调度器实例
_scheduler = None

def get_resource_scheduler() -> ResourceScheduler:
    """获取全局资源调度器实例"""
    global _scheduler
    if _scheduler is None:
        _scheduler = ResourceScheduler()
        _scheduler.start_monitoring()
    return _scheduler


# 使用示例
if __name__ == "__main__":
    # 创建资源调度器
    with ResourceScheduler(monitor_interval=2.0) as scheduler:
        # 等待收集一些数据
        time.sleep(10)
        
        # 做出调度决策
        decision = scheduler.make_schedule_decision("excel_write", priority=1)
        print(f"调度决策: {decision.action.value}, 最大并发: {decision.max_concurrent_tasks}")
        
        # 获取资源状态
        status = scheduler.get_resource_status()
        print(f"资源状态: {status['resource_level']}, CPU: {status['cpu_percent']:.1f}%")
        
        # 获取统计信息
        stats = scheduler.get_statistics()
        print(f"统计信息: {stats}")