#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统监控模块
监控系统性能、资源使用情况和运行状态
"""

import psutil
import logging
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import threading
from collections import deque
import statistics

@dataclass
class SystemMetrics:
    """系统指标数据类"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    network_sent_mb: float
    network_recv_mb: float
    process_count: int
    load_average: List[float]
    temperature: Optional[float] = None

@dataclass
class ProcessMetrics:
    """进程指标数据类"""
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    status: str
    create_time: str
    num_threads: int
    num_fds: int
    io_read_mb: float
    io_write_mb: float

@dataclass
class AlertRule:
    """告警规则数据类"""
    rule_id: str
    name: str
    metric: str  # cpu, memory, disk, etc.
    operator: str  # >, <, >=, <=, ==
    threshold: float
    duration_seconds: int  # 持续时间
    enabled: bool = True
    callback: Optional[Callable] = None
    description: str = ""

class SystemMonitor:
    """
    系统监控器
    提供系统性能监控、告警、历史数据记录等功能
    """
    
    def __init__(self, 
                 data_retention_hours: int = 24,
                 collection_interval_seconds: int = 30,
                 alert_check_interval_seconds: int = 60):
        self.logger = logging.getLogger('SystemMonitor')
        
        # 配置参数
        self.data_retention_hours = data_retention_hours
        self.collection_interval = collection_interval_seconds
        self.alert_check_interval = alert_check_interval_seconds
        
        # 数据存储
        self.metrics_history: deque = deque(maxlen=int(data_retention_hours * 3600 / collection_interval_seconds))
        self.process_metrics: Dict[int, ProcessMetrics] = {}
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Dict[str, Any]] = {}
        
        # 运行状态
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.alert_thread: Optional[threading.Thread] = None
        
        # 网络基准值（用于计算增量）
        self.network_baseline = None
        
        # 数据文件路径
        self.data_dir = Path("monitoring_data")
        self.data_dir.mkdir(exist_ok=True)
        
        self.logger.info("系统监控器初始化完成")
    
    def start_monitoring(self):
        """
        启动系统监控
        """
        if self.is_monitoring:
            self.logger.warning("监控已在运行中")
            return
        
        self.is_monitoring = True
        
        # 启动数据收集线程
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        # 启动告警检查线程
        self.alert_thread = threading.Thread(target=self._alert_loop, daemon=True)
        self.alert_thread.start()
        
        self.logger.info("系统监控已启动")
    
    def stop_monitoring(self):
        """
        停止系统监控
        """
        self.is_monitoring = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        if self.alert_thread:
            self.alert_thread.join(timeout=5)
        
        self.logger.info("系统监控已停止")
    
    def _monitoring_loop(self):
        """
        监控主循环
        """
        while self.is_monitoring:
            try:
                # 收集系统指标
                metrics = self._collect_system_metrics()
                if metrics:
                    self.metrics_history.append(metrics)
                
                # 收集进程指标
                self._collect_process_metrics()
                
                # 定期保存数据
                if len(self.metrics_history) % 10 == 0:
                    self._save_metrics_to_file()
                
                time.sleep(self.collection_interval)
                
            except Exception as e:
                self.logger.error(f"监控数据收集异常: {e}")
                time.sleep(self.collection_interval)
    
    def _alert_loop(self):
        """
        告警检查循环
        """
        while self.is_monitoring:
            try:
                self._check_alerts()
                time.sleep(self.alert_check_interval)
                
            except Exception as e:
                self.logger.error(f"告警检查异常: {e}")
                time.sleep(self.alert_check_interval)
    
    def _collect_system_metrics(self) -> Optional[SystemMetrics]:
        """
        收集系统指标
        
        Returns:
            系统指标对象
        """
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存信息
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_gb = memory.used / (1024**3)
            memory_total_gb = memory.total / (1024**3)
            
            # 磁盘信息
            disk = psutil.disk_usage('/')
            disk_percent = disk.used / disk.total * 100
            disk_used_gb = disk.used / (1024**3)
            disk_total_gb = disk.total / (1024**3)
            
            # 网络信息
            network = psutil.net_io_counters()
            if self.network_baseline is None:
                self.network_baseline = network
                network_sent_mb = 0
                network_recv_mb = 0
            else:
                network_sent_mb = (network.bytes_sent - self.network_baseline.bytes_sent) / (1024**2)
                network_recv_mb = (network.bytes_recv - self.network_baseline.bytes_recv) / (1024**2)
            
            # 进程数量
            process_count = len(psutil.pids())
            
            # 系统负载
            try:
                load_average = list(psutil.getloadavg())
            except AttributeError:
                # Windows系统不支持getloadavg
                load_average = [0.0, 0.0, 0.0]
            
            # CPU温度（如果可用）
            temperature = None
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    # 取第一个传感器的温度
                    for name, entries in temps.items():
                        if entries:
                            temperature = entries[0].current
                            break
            except (AttributeError, OSError):
                pass
            
            return SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_gb=round(memory_used_gb, 2),
                memory_total_gb=round(memory_total_gb, 2),
                disk_percent=round(disk_percent, 2),
                disk_used_gb=round(disk_used_gb, 2),
                disk_total_gb=round(disk_total_gb, 2),
                network_sent_mb=round(network_sent_mb, 2),
                network_recv_mb=round(network_recv_mb, 2),
                process_count=process_count,
                load_average=load_average,
                temperature=temperature
            )
            
        except Exception as e:
            self.logger.error(f"收集系统指标失败: {e}")
            return None
    
    def _collect_process_metrics(self):
        """
        收集进程指标
        """
        try:
            current_processes = {}
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 
                                           'memory_info', 'status', 'create_time', 
                                           'num_threads', 'num_fds']):
                try:
                    pinfo = proc.info
                    
                    # 只收集相关进程的详细信息
                    if self._is_relevant_process(pinfo['name']):
                        # IO信息
                        try:
                            io_counters = proc.io_counters()
                            io_read_mb = io_counters.read_bytes / (1024**2)
                            io_write_mb = io_counters.write_bytes / (1024**2)
                        except (psutil.AccessDenied, AttributeError):
                            io_read_mb = 0
                            io_write_mb = 0
                        
                        process_metrics = ProcessMetrics(
                            pid=pinfo['pid'],
                            name=pinfo['name'],
                            cpu_percent=pinfo['cpu_percent'] or 0,
                            memory_percent=pinfo['memory_percent'] or 0,
                            memory_mb=round((pinfo['memory_info'].rss if pinfo['memory_info'] else 0) / (1024**2), 2),
                            status=pinfo['status'],
                            create_time=datetime.fromtimestamp(pinfo['create_time']).isoformat(),
                            num_threads=pinfo['num_threads'] or 0,
                            num_fds=pinfo['num_fds'] or 0,
                            io_read_mb=round(io_read_mb, 2),
                            io_write_mb=round(io_write_mb, 2)
                        )
                        
                        current_processes[pinfo['pid']] = process_metrics
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            self.process_metrics = current_processes
            
        except Exception as e:
            self.logger.error(f"收集进程指标失败: {e}")
    
    def _is_relevant_process(self, process_name: str) -> bool:
        """
        判断是否是相关进程
        
        Args:
            process_name: 进程名称
            
        Returns:
            是否是相关进程
        """
        relevant_keywords = [
            'python', 'twitter', 'scraper', 'chrome', 'chromium',
            'node', 'npm', 'java', 'mysql', 'postgres', 'redis'
        ]
        
        process_name_lower = process_name.lower()
        return any(keyword in process_name_lower for keyword in relevant_keywords)
    
    def add_alert_rule(self, 
                      rule_id: str,
                      name: str,
                      metric: str,
                      operator: str,
                      threshold: float,
                      duration_seconds: int = 300,
                      callback: Optional[Callable] = None,
                      description: str = "") -> bool:
        """
        添加告警规则
        
        Args:
            rule_id: 规则唯一标识
            name: 规则名称
            metric: 监控指标（cpu_percent, memory_percent, disk_percent等）
            operator: 比较操作符（>, <, >=, <=, ==）
            threshold: 阈值
            duration_seconds: 持续时间（秒）
            callback: 告警回调函数
            description: 规则描述
            
        Returns:
            是否添加成功
        """
        if rule_id in self.alert_rules:
            self.logger.warning(f"告警规则已存在: {rule_id}")
            return False
        
        if operator not in ['>', '<', '>=', '<=', '==']:
            self.logger.error(f"不支持的操作符: {operator}")
            return False
        
        rule = AlertRule(
            rule_id=rule_id,
            name=name,
            metric=metric,
            operator=operator,
            threshold=threshold,
            duration_seconds=duration_seconds,
            callback=callback,
            description=description
        )
        
        self.alert_rules[rule_id] = rule
        self.logger.info(f"已添加告警规则: {name} ({rule_id})")
        return True
    
    def _check_alerts(self):
        """
        检查告警规则
        """
        if not self.metrics_history:
            return
        
        current_time = datetime.now()
        latest_metrics = self.metrics_history[-1]
        
        for rule_id, rule in self.alert_rules.items():
            if not rule.enabled:
                continue
            
            try:
                # 获取指标值
                metric_value = getattr(latest_metrics, rule.metric, None)
                if metric_value is None:
                    continue
                
                # 检查阈值
                is_triggered = self._evaluate_condition(metric_value, rule.operator, rule.threshold)
                
                if is_triggered:
                    # 检查是否已有活跃告警
                    if rule_id in self.active_alerts:
                        alert_info = self.active_alerts[rule_id]
                        start_time = datetime.fromisoformat(alert_info['start_time'])
                        duration = (current_time - start_time).total_seconds()
                        
                        # 更新告警信息
                        alert_info['duration_seconds'] = duration
                        alert_info['last_triggered'] = current_time.isoformat()
                        alert_info['current_value'] = metric_value
                        
                        # 检查是否达到持续时间阈值
                        if duration >= rule.duration_seconds and not alert_info['notified']:
                            self._trigger_alert(rule, alert_info)
                            alert_info['notified'] = True
                    else:
                        # 创建新告警
                        alert_info = {
                            'rule_id': rule_id,
                            'rule_name': rule.name,
                            'metric': rule.metric,
                            'threshold': rule.threshold,
                            'current_value': metric_value,
                            'start_time': current_time.isoformat(),
                            'last_triggered': current_time.isoformat(),
                            'duration_seconds': 0,
                            'notified': False
                        }
                        self.active_alerts[rule_id] = alert_info
                else:
                    # 告警恢复
                    if rule_id in self.active_alerts:
                        alert_info = self.active_alerts[rule_id]
                        if alert_info['notified']:
                            self._resolve_alert(rule, alert_info)
                        del self.active_alerts[rule_id]
                        
            except Exception as e:
                self.logger.error(f"检查告警规则 {rule_id} 时出错: {e}")
    
    def _evaluate_condition(self, value: float, operator: str, threshold: float) -> bool:
        """
        评估条件
        
        Args:
            value: 当前值
            operator: 操作符
            threshold: 阈值
            
        Returns:
            是否满足条件
        """
        if operator == '>':
            return value > threshold
        elif operator == '<':
            return value < threshold
        elif operator == '>=':
            return value >= threshold
        elif operator == '<=':
            return value <= threshold
        elif operator == '==':
            return abs(value - threshold) < 0.001  # 浮点数比较
        else:
            return False
    
    def _trigger_alert(self, rule: AlertRule, alert_info: Dict[str, Any]):
        """
        触发告警
        
        Args:
            rule: 告警规则
            alert_info: 告警信息
        """
        self.logger.warning(
            f"告警触发: {rule.name} - {rule.metric} {rule.operator} {rule.threshold}, "
            f"当前值: {alert_info['current_value']}, 持续时间: {alert_info['duration_seconds']}秒"
        )
        
        # 调用回调函数
        if rule.callback:
            try:
                rule.callback(rule, alert_info)
            except Exception as e:
                self.logger.error(f"告警回调函数执行失败: {e}")
    
    def _resolve_alert(self, rule: AlertRule, alert_info: Dict[str, Any]):
        """
        告警恢复
        
        Args:
            rule: 告警规则
            alert_info: 告警信息
        """
        self.logger.info(
            f"告警恢复: {rule.name} - 持续时间: {alert_info['duration_seconds']}秒"
        )
    
    def get_current_metrics(self) -> Optional[SystemMetrics]:
        """
        获取当前系统指标
        
        Returns:
            当前系统指标
        """
        if self.metrics_history:
            return self.metrics_history[-1]
        return None
    
    def get_metrics_history(self, hours: int = 1) -> List[SystemMetrics]:
        """
        获取历史指标数据
        
        Args:
            hours: 获取最近几小时的数据
            
        Returns:
            历史指标列表
        """
        if not self.metrics_history:
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        filtered_metrics = []
        for metrics in self.metrics_history:
            metrics_time = datetime.fromisoformat(metrics.timestamp)
            if metrics_time >= cutoff_time:
                filtered_metrics.append(metrics)
        
        return filtered_metrics
    
    def get_process_metrics(self) -> List[ProcessMetrics]:
        """
        获取进程指标
        
        Returns:
            进程指标列表
        """
        return list(self.process_metrics.values())
    
    def get_system_statistics(self, hours: int = 1) -> Dict[str, Any]:
        """
        获取系统统计信息
        
        Args:
            hours: 统计时间范围（小时）
            
        Returns:
            统计信息
        """
        metrics_list = self.get_metrics_history(hours)
        
        if not metrics_list:
            return {}
        
        # 提取各项指标
        cpu_values = [m.cpu_percent for m in metrics_list]
        memory_values = [m.memory_percent for m in metrics_list]
        disk_values = [m.disk_percent for m in metrics_list]
        
        statistics_data = {
            'time_range_hours': hours,
            'data_points': len(metrics_list),
            'cpu': {
                'current': cpu_values[-1] if cpu_values else 0,
                'average': round(statistics.mean(cpu_values), 2) if cpu_values else 0,
                'max': round(max(cpu_values), 2) if cpu_values else 0,
                'min': round(min(cpu_values), 2) if cpu_values else 0
            },
            'memory': {
                'current': memory_values[-1] if memory_values else 0,
                'average': round(statistics.mean(memory_values), 2) if memory_values else 0,
                'max': round(max(memory_values), 2) if memory_values else 0,
                'min': round(min(memory_values), 2) if memory_values else 0
            },
            'disk': {
                'current': disk_values[-1] if disk_values else 0,
                'average': round(statistics.mean(disk_values), 2) if disk_values else 0,
                'max': round(max(disk_values), 2) if disk_values else 0,
                'min': round(min(disk_values), 2) if disk_values else 0
            },
            'active_alerts': len(self.active_alerts),
            'total_processes': len(self.process_metrics)
        }
        
        return statistics_data
    
    def _save_metrics_to_file(self):
        """
        保存指标数据到文件
        """
        try:
            # 保存最近的指标数据
            metrics_file = self.data_dir / f"metrics_{datetime.now().strftime('%Y%m%d')}.json"
            
            # 只保存最近100条记录到文件
            recent_metrics = list(self.metrics_history)[-100:]
            metrics_data = [asdict(m) for m in recent_metrics]
            
            with open(metrics_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'metrics': metrics_data
                }, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"保存指标数据失败: {e}")
    
    def export_monitoring_report(self, hours: int = 24) -> Dict[str, Any]:
        """
        导出监控报告
        
        Args:
            hours: 报告时间范围（小时）
            
        Returns:
            监控报告
        """
        report = {
            'report_generated_at': datetime.now().isoformat(),
            'time_range_hours': hours,
            'system_statistics': self.get_system_statistics(hours),
            'current_metrics': asdict(self.get_current_metrics()) if self.get_current_metrics() else None,
            'process_metrics': [asdict(p) for p in self.get_process_metrics()],
            'alert_rules': {
                rule_id: {
                    'name': rule.name,
                    'metric': rule.metric,
                    'operator': rule.operator,
                    'threshold': rule.threshold,
                    'enabled': rule.enabled,
                    'description': rule.description
                }
                for rule_id, rule in self.alert_rules.items()
            },
            'active_alerts': self.active_alerts.copy(),
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """
        生成系统优化建议
        
        Returns:
            建议列表
        """
        recommendations = []
        
        current_metrics = self.get_current_metrics()
        if not current_metrics:
            return recommendations
        
        # CPU使用率建议
        if current_metrics.cpu_percent > 80:
            recommendations.append("CPU使用率较高，建议检查高CPU占用的进程")
        
        # 内存使用率建议
        if current_metrics.memory_percent > 85:
            recommendations.append("内存使用率较高，建议释放不必要的进程或增加内存")
        
        # 磁盘使用率建议
        if current_metrics.disk_percent > 90:
            recommendations.append("磁盘空间不足，建议清理临时文件或扩展存储空间")
        
        # 进程数量建议
        if current_metrics.process_count > 500:
            recommendations.append("系统进程数量较多，建议检查是否有异常进程")
        
        # 活跃告警建议
        if len(self.active_alerts) > 0:
            recommendations.append(f"当前有 {len(self.active_alerts)} 个活跃告警，建议及时处理")
        
        return recommendations
    
    def cleanup_old_data(self, days: int = 7) -> int:
        """
        清理旧的监控数据文件
        
        Args:
            days: 保留天数
            
        Returns:
            清理的文件数量
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        cleaned_count = 0
        
        try:
            for file_path in self.data_dir.glob("metrics_*.json"):
                # 从文件名提取日期
                date_str = file_path.stem.split('_')[1]
                file_date = datetime.strptime(date_str, '%Y%m%d')
                
                if file_date < cutoff_date:
                    file_path.unlink()
                    cleaned_count += 1
                    self.logger.info(f"已删除旧监控数据: {file_path.name}")
            
            self.logger.info(f"清理完成，删除了 {cleaned_count} 个旧数据文件")
            
        except Exception as e:
            self.logger.error(f"清理旧数据失败: {e}")
        
        return cleaned_count

# 预定义的告警回调函数
class AlertCallbacks:
    """
    预定义的告警回调函数
    """
    
    @staticmethod
    def log_alert(rule: AlertRule, alert_info: Dict[str, Any]):
        """
        记录告警到日志
        
        Args:
            rule: 告警规则
            alert_info: 告警信息
        """
        logger = logging.getLogger('AlertCallback')
        logger.critical(
            f"系统告警: {rule.name} | "
            f"指标: {rule.metric} | "
            f"阈值: {rule.threshold} | "
            f"当前值: {alert_info['current_value']} | "
            f"持续时间: {alert_info['duration_seconds']}秒"
        )
    
    @staticmethod
    def send_email_alert(rule: AlertRule, alert_info: Dict[str, Any]):
        """
        发送邮件告警（需要配置邮件服务）
        
        Args:
            rule: 告警规则
            alert_info: 告警信息
        """
        # 这里可以实现邮件发送逻辑
        logger = logging.getLogger('AlertCallback')
        logger.info(f"邮件告警已发送: {rule.name}")
    
    @staticmethod
    def restart_service_alert(rule: AlertRule, alert_info: Dict[str, Any]):
        """
        重启服务告警（谨慎使用）
        
        Args:
            rule: 告警规则
            alert_info: 告警信息
        """
        logger = logging.getLogger('AlertCallback')
        logger.warning(f"服务重启告警触发: {rule.name}")
        # 这里可以实现服务重启逻辑