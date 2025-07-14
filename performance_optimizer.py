
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能优化器 - 简化版本
"""

import asyncio
import time
import threading
import logging
from typing import List, Any, Callable, Optional, Dict
from contextlib import asynccontextmanager
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor

# 简化版本，不依赖aiohttp
AIOHTTP_AVAILABLE = False

from models import PerformanceMetrics

logger = logging.getLogger(__name__)



class AsyncBatchProcessor:
    """异步批处理器"""
    
    def __init__(self, max_workers: int = 10, batch_size: int = 50):
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.semaphore = asyncio.Semaphore(max_workers)
    
    async def process_batch(self, items: List[Any], processor: Callable) -> List[Any]:
        """批量处理项目"""
        results = []
        
        # 分批处理
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batch_tasks = [self._process_item(item, processor) for item in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            results.extend(batch_results)
        
        return results
    
    async def _process_item(self, item: Any, processor: Callable) -> Any:
        """处理单个项目"""
        async with self.semaphore:
            try:
                if asyncio.iscoroutinefunction(processor):
                    return await processor(item)
                else:
                    loop = asyncio.get_event_loop()
                    return await loop.run_in_executor(None, processor, item)
            except Exception as e:
                logger.error(f"处理项目失败: {e}")
                return e



class MemoryOptimizer:
    """内存优化器"""
    
    def __init__(self, max_memory_mb: int = 1024):
        self.max_memory_mb = max_memory_mb
        self._data_cache = {}
        self._cache_size = 0
    
    def cache_data(self, key: str, data: Any, size_mb: float):
        """缓存数据"""
        # 检查内存限制
        if self._cache_size + size_mb > self.max_memory_mb:
            self._evict_cache()
        
        self._data_cache[key] = data
        self._cache_size += size_mb
    
    def get_cached_data(self, key: str) -> Optional[Any]:
        """获取缓存数据"""
        return self._data_cache.get(key)
    
    def get_memory_usage(self) -> float:
        """获取当前内存使用量（MB）"""
        return self._cache_size
    
    def _evict_cache(self):
        """清理缓存"""
        # 简单的LRU策略：清理一半缓存
        keys_to_remove = list(self._data_cache.keys())[:len(self._data_cache) // 2]
        for key in keys_to_remove:
            del self._data_cache[key]
        
        self._cache_size = self._cache_size // 2
        logger.info(f"缓存清理完成，当前大小: {self._cache_size}MB")

class ThreadSafeQueue:
    """线程安全队列"""
    
    def __init__(self, maxsize: int = 1000):
        self._queue = Queue(maxsize=maxsize)
        self._shutdown = threading.Event()
    
    def put(self, item: Any, timeout: Optional[float] = None):
        """添加项目到队列"""
        if not self._shutdown.is_set():
            self._queue.put(item, timeout=timeout)
    
    def get(self, timeout: Optional[float] = None) -> Optional[Any]:
        """从队列获取项目"""
        try:
            return self._queue.get(timeout=timeout)
        except Empty:
            return None
    
    def shutdown(self):
        """关闭队列"""
        self._shutdown.set()
    
    def is_shutdown(self) -> bool:
        """检查是否已关闭"""
        return self._shutdown.is_set()

class PerformanceProfiler:
    """性能分析器"""
    
    def __init__(self):
        self.metrics: List[PerformanceMetrics] = []
    
    @asynccontextmanager
    async def profile(self, operation_name: str):
        """性能分析上下文管理器"""
        import psutil
        
        start_time = time.time()
        start_memory = psutil.virtual_memory().percent
        start_cpu = psutil.cpu_percent()
        
        success_count = 0
        error_count = 0
        
        def _create_counter():
            """创建计数器"""
            nonlocal success_count, error_count
            
            class Counter:
                def success(self):
                    nonlocal success_count
                    success_count += 1
                
                def error(self):
                    nonlocal error_count
                    error_count += 1
            
            return Counter()
        
        try:
            yield _create_counter()
        finally:
            end_time = time.time()
            end_memory = psutil.virtual_memory().percent
            end_cpu = psutil.cpu_percent()
            
            metrics = PerformanceMetrics(
                start_time=start_time,
                end_time=end_time,
                duration=end_time - start_time,
                memory_usage=end_memory - start_memory,
                cpu_usage=end_cpu - start_cpu,
                success_count=success_count,
                error_count=error_count
            )
            
            self.metrics.append(metrics)
            
            logger.info(
                f"性能分析 - {operation_name}",
                extra={
                    'duration': metrics.duration,
                    'memory_delta': metrics.memory_usage,
                    'cpu_delta': metrics.cpu_usage,
                    'success_rate': metrics.success_rate
                }
            )
    
    def get_average_metrics(self) -> Optional[Dict[str, float]]:
        """获取平均性能指标"""
        if not self.metrics:
            return None
        
        return {
            'avg_duration': sum(m.duration for m in self.metrics) / len(self.metrics),
            'avg_memory_usage': sum(m.memory_usage for m in self.metrics) / len(self.metrics),
            'avg_cpu_usage': sum(m.cpu_usage for m in self.metrics) / len(self.metrics),
            'avg_success_rate': sum(m.success_rate for m in self.metrics) / len(self.metrics)
        }

# 全局实例
batch_processor = AsyncBatchProcessor()
memory_optimizer = MemoryOptimizer()
performance_profiler = PerformanceProfiler()
