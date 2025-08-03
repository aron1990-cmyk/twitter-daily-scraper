# -*- coding: utf-8 -*-
"""
API缓存管理器
专门处理API接口的缓存逻辑，提升响应速度
"""

import time
import json
import hashlib
import logging
from functools import wraps
from typing import Dict, Any, Optional, Callable
from flask import request, jsonify, current_app

logger = logging.getLogger(__name__)

class APICacheManager:
    """API缓存管理器"""
    
    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.hit_count = 0
        self.miss_count = 0
        self.max_cache_size = 1000  # 最大缓存条目数
        
        # 默认缓存配置
        self.default_timeouts = {
            '/api/status': 30,
            '/api/influencers': 60,
            '/api/influencers/stats': 120,
            '/api/influencers/categories': 300,
            '/api/tasks': 30,
            '/api/config': 600,
        }
    
    def generate_cache_key(self, endpoint: str, params: Dict = None, user_id: str = None) -> str:
        """生成缓存键"""
        key_parts = [endpoint]
        
        if params:
            # 排序参数以确保一致性
            sorted_params = sorted(params.items())
            params_str = '&'.join(f'{k}={v}' for k, v in sorted_params)
            key_parts.append(params_str)
        
        if user_id:
            key_parts.append(f'user:{user_id}')
        
        key_string = '|'.join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, cache_key: str) -> Optional[Any]:
        """获取缓存数据"""
        if cache_key not in self.cache:
            self.miss_count += 1
            return None
        
        cache_entry = self.cache[cache_key]
        current_time = time.time()
        
        # 检查是否过期
        if current_time > cache_entry['expires_at']:
            del self.cache[cache_key]
            self.miss_count += 1
            return None
        
        self.hit_count += 1
        return cache_entry['data']
    
    def set(self, cache_key: str, data: Any, timeout: int = 300) -> None:
        """设置缓存数据"""
        # 检查缓存大小限制
        if len(self.cache) >= self.max_cache_size:
            self._cleanup_expired()
            
            # 如果清理后仍然超限，删除最旧的条目
            if len(self.cache) >= self.max_cache_size:
                oldest_key = min(self.cache.keys(), 
                               key=lambda k: self.cache[k]['created_at'])
                del self.cache[oldest_key]
        
        current_time = time.time()
        self.cache[cache_key] = {
            'data': data,
            'created_at': current_time,
            'expires_at': current_time + timeout,
            'access_count': 0
        }
    
    def invalidate(self, pattern: str = None) -> None:
        """清除缓存"""
        if pattern:
            # 清除匹配模式的缓存
            keys_to_remove = [key for key in self.cache.keys() if pattern in key]
            for key in keys_to_remove:
                del self.cache[key]
        else:
            # 清除所有缓存
            self.cache.clear()
    
    def _cleanup_expired(self) -> None:
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time > entry['expires_at']
        ]
        
        for key in expired_keys:
            del self.cache[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'cache_entries': len(self.cache),
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate': round(hit_rate, 2),
            'max_cache_size': self.max_cache_size
        }

# 全局缓存管理器实例
api_cache = APICacheManager()

def cached_api(timeout: int = None, key_func: Callable = None, 
               invalidate_on: list = None):
    """API缓存装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 确定缓存超时时间
            cache_timeout = timeout
            if cache_timeout is None:
                endpoint = request.endpoint or request.path
                cache_timeout = api_cache.default_timeouts.get(endpoint, 300)
            
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                params = dict(request.args)
                cache_key = api_cache.generate_cache_key(
                    request.path, params
                )
            
            # 尝试从缓存获取
            cached_data = api_cache.get(cache_key)
            if cached_data is not None:
                logger.debug(f'Cache hit for {request.path}')
                return cached_data
            
            # 执行原函数
            logger.debug(f'Cache miss for {request.path}')
            result = f(*args, **kwargs)
            
            # 只缓存成功的响应
            if hasattr(result, 'status_code') and result.status_code == 200:
                api_cache.set(cache_key, result, cache_timeout)
            elif isinstance(result, tuple) and len(result) == 2:
                # 处理 (data, status_code) 格式
                data, status_code = result
                if status_code == 200:
                    api_cache.set(cache_key, result, cache_timeout)
            elif not hasattr(result, 'status_code'):
                # 假设是成功的响应
                api_cache.set(cache_key, result, cache_timeout)
            
            return result
        
        return decorated_function
    return decorator

def invalidate_cache(patterns: list):
    """缓存失效装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            result = f(*args, **kwargs)
            
            # 执行成功后清除相关缓存
            if hasattr(result, 'status_code') and result.status_code in [200, 201]:
                for pattern in patterns:
                    api_cache.invalidate(pattern)
                    logger.debug(f'Invalidated cache for pattern: {pattern}')
            
            return result
        return decorated_function
    return decorator

def get_cache_stats():
    """获取缓存统计信息的API端点"""
    stats = api_cache.get_stats()
    return jsonify({
        'success': True,
        'data': stats
    })

def clear_cache():
    """清除所有缓存的API端点"""
    api_cache.invalidate()
    return jsonify({
        'success': True,
        'message': '缓存已清除'
    })

# 预热缓存函数
def warm_up_cache():
    """预热关键接口缓存"""
    try:
        from web_app_optimized import app
        
        with app.test_client() as client:
            # 预热关键接口
            endpoints_to_warm = [
                '/api/status',
                '/api/influencers/stats',
                '/api/influencers/categories',
            ]
            
            for endpoint in endpoints_to_warm:
                try:
                    client.get(endpoint)
                    logger.info(f'Warmed up cache for {endpoint}')
                except Exception as e:
                    logger.error(f'Failed to warm up {endpoint}: {e}')
                    
    except Exception as e:
        logger.error(f'Cache warm-up failed: {e}')