# -*- coding: utf-8 -*-
"""
性能中间件
提供缓存、性能监控和响应时间测量功能
"""

import time
import functools
import logging
from flask import request, g, jsonify
from typing import Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)

class PerformanceMiddleware:
    """性能监控中间件"""
    
    def __init__(self, app=None):
        self.app = app
        self.response_times = []
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化应用"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def before_request(self):
        """请求开始前记录时间"""
        g.start_time = time.time()
    
    def after_request(self, response):
        """请求结束后记录响应时间"""
        if hasattr(g, 'start_time'):
            response_time = time.time() - g.start_time
            self.response_times.append(response_time)
            
            # 保持最近1000条记录
            if len(self.response_times) > 1000:
                self.response_times = self.response_times[-1000:]
            
            # 记录慢请求
            if response_time > 1.0:
                logger.warning(f"Slow request: {request.path} took {response_time:.2f}s")
            
            # 添加响应时间头
            response.headers['X-Response-Time'] = f"{response_time:.3f}s"
        
        return response
    
    def get_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        if not self.response_times:
            return {
                'avg_response_time': 0,
                'max_response_time': 0,
                'min_response_time': 0,
                'total_requests': 0
            }
        
        return {
            'avg_response_time': sum(self.response_times) / len(self.response_times),
            'max_response_time': max(self.response_times),
            'min_response_time': min(self.response_times),
            'total_requests': len(self.response_times)
        }

# 简单的内存缓存
_cache = {}

def cache_response(timeout: int = 300):
    """缓存装饰器"""
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{f.__name__}:{request.path}:{request.query_string.decode()}"
            
            # 检查缓存
            if cache_key in _cache:
                cached_data, cached_time = _cache[cache_key]
                if time.time() - cached_time < timeout:
                    return cached_data
            
            # 执行函数并缓存结果
            result = f(*args, **kwargs)
            _cache[cache_key] = (result, time.time())
            
            # 清理过期缓存
            current_time = time.time()
            expired_keys = [
                key for key, (_, cached_time) in _cache.items()
                if current_time - cached_time > timeout
            ]
            for key in expired_keys:
                del _cache[key]
            
            return result
        return wrapper
    return decorator

def measure_time(f):
    """测量函数执行时间的装饰器"""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = f(*args, **kwargs)
        execution_time = time.time() - start_time
        
        logger.debug(f"{f.__name__} executed in {execution_time:.3f}s")
        return result
    return wrapper

def clear_cache():
    """清空缓存"""
    global _cache
    _cache.clear()
    logger.info("Cache cleared")

def get_cache_stats() -> Dict[str, Any]:
    """获取缓存统计"""
    return {
        'cache_size': len(_cache),
        'cache_keys': list(_cache.keys())
    }