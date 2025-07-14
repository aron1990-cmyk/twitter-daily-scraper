
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
监控和指标收集系统 - 简化版本
"""

import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from collections import defaultdict, deque
from dataclasses import dataclass, field
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# 简化版本，不依赖外部包
PROMETHEUS_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available, system metrics will be limited")

from models import HealthStatus, PerformanceMetrics

# 简化版本监控系统
class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)
        self.histograms = defaultdict(list)
        self._lock = threading.Lock()
    
    def increment_counter(self, name: str, value: int = 1):
        """增加计数器"""
        with self._lock:
            self.counters[name] += value
    
    def set_gauge(self, name: str, value: float):
        """设置仪表值"""
        with self._lock:
            self.gauges[name] = value
    
    def record_histogram(self, name: str, value: float):
        """记录直方图值"""
        with self._lock:
            self.histograms[name].append(value)
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取所有指标"""
        with self._lock:
            return {
                'counters': dict(self.counters),
                'gauges': dict(self.gauges),
                'histograms': {k: list(v) for k, v in self.histograms.items()}
            }

class HealthChecker:
    """健康检查器"""
    
    def __init__(self):
        self.checks = {}
        self._lock = threading.Lock()
    
    def register_check(self, name: str, check_func: Callable[[], bool]):
        """注册健康检查"""
        with self._lock:
            self.checks[name] = check_func
    
    def run_checks(self) -> Dict[str, HealthStatus]:
        """运行所有健康检查"""
        results = {}
        
        for name, check_func in self.checks.items():
            start_time = time.time()
            try:
                is_healthy = check_func()
                response_time = time.time() - start_time
                status = 'healthy' if is_healthy else 'unhealthy'
                
                results[name] = HealthStatus(
                    service_name=name,
                    status=status,
                    response_time=response_time
                )
            except Exception as e:
                response_time = time.time() - start_time
                results[name] = HealthStatus(
                    service_name=name,
                    status='unknown',
                    response_time=response_time,
                    details={'error': str(e)}
                )
        
        return results

# 配置简化日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class MonitoringSystem:
    """监控系统主类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics_collector = MetricsCollector()
        self.health_checker = HealthChecker()
        self._start_time = time.time()
    
    def start(self):
        """启动监控系统"""
        self.logger.info("监控系统已启动")
    
    def get_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            'uptime': time.time() - self._start_time,
            'metrics': self.metrics_collector.get_metrics(),
            'health': self.health_checker.run_checks()
        }
    
    def record_tweet_scraped(self, source: str, success: bool = True):
        """记录推文采集"""
        self.metrics_collector.increment_counter(f'tweets_scraped_{source}', 1)
        if success:
            self.metrics_collector.increment_counter('tweets_success', 1)
        else:
            self.metrics_collector.increment_counter('tweets_failed', 1)
        
        self.logger.info(f"推文采集记录: {source}, 成功: {success}")
    
    @contextmanager
    def measure_duration(self, operation: str):
        """测量操作耗时"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.metrics_collector.record_histogram(f'duration_{operation}', duration)
            self.logger.info(f"操作 {operation} 耗时: {duration:.2f}s")
    
    def update_system_metrics(self):
        """更新系统指标"""
        try:
            if psutil:
                # CPU使用率
                cpu_percent = psutil.cpu_percent(interval=1)
                self.metrics_collector.set_gauge('cpu_usage', cpu_percent)
                
                # 内存使用率
                memory = psutil.virtual_memory()
                self.metrics_collector.set_gauge('memory_usage', memory.percent)
                
                self.logger.debug(f"系统指标更新: CPU {cpu_percent}%, 内存 {memory.percent}%")
        except Exception as e:
            self.logger.error(f"系统指标更新失败: {e}")

# 全局实例
monitoring_system = MonitoringSystem()
