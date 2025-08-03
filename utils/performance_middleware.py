# -*- coding: utf-8 -*-
"""
性能优化中间件
实现GZIP压缩、缓存控制、响应时间监控等功能
"""

import gzip
import time
import json
import logging
from functools import wraps
from io import BytesIO
from flask import request, Response, g, current_app
from werkzeug.exceptions import RequestEntityTooLarge

logger = logging.getLogger(__name__)

class PerformanceMiddleware:
    """性能优化中间件"""
    
    def __init__(self, app=None):
        self.app = app
        self.cache = {}  # 简单内存缓存
        self.cache_timeouts = {}  # 缓存超时时间
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化Flask应用"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        
        # 注册性能监控路由
        app.add_url_rule('/api/performance/stats', 'performance_stats', 
                        self.get_performance_stats, methods=['GET'])
    
    def before_request(self):
        """请求前处理"""
        g.start_time = time.time()
        
        # 检查请求大小
        if request.content_length and request.content_length > current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024):
            raise RequestEntityTooLarge()
    
    def after_request(self, response):
        """请求后处理"""
        # 计算响应时间
        if hasattr(g, 'start_time'):
            response_time = time.time() - g.start_time
            response.headers['X-Response-Time'] = f'{response_time:.3f}s'
            
            # 记录慢请求
            if response_time > 1.0:  # 超过1秒的请求
                logger.warning(f'Slow request: {request.path} took {response_time:.3f}s')
        
        # 应用GZIP压缩
        response = self.apply_gzip_compression(response)
        
        # 设置缓存头
        response = self.set_cache_headers(response)
        
        # 设置安全头
        response = self.set_security_headers(response)
        
        return response
    
    def apply_gzip_compression(self, response):
        """应用GZIP压缩"""
        # 检查是否支持gzip
        accept_encoding = request.headers.get('Accept-Encoding', '')
        if 'gzip' not in accept_encoding.lower():
            return response
        
        # 检查内容类型
        content_type = response.headers.get('Content-Type', '')
        compressible_types = [
            'text/html', 'text/css', 'text/javascript', 'text/xml',
            'application/json', 'application/javascript', 'application/xml',
            'image/svg+xml'
        ]
        
        if not any(ct in content_type for ct in compressible_types):
            return response
        
        # 检查内容大小
        if len(response.data) < 500:  # 小于500字节不压缩
            return response
        
        # 执行压缩
        try:
            gzip_buffer = BytesIO()
            with gzip.GzipFile(fileobj=gzip_buffer, mode='wb', compresslevel=6) as gzip_file:
                gzip_file.write(response.data)
            
            compressed_data = gzip_buffer.getvalue()
            
            # 只有压缩效果明显时才使用
            if len(compressed_data) < len(response.data) * 0.9:
                response.data = compressed_data
                response.headers['Content-Encoding'] = 'gzip'
                response.headers['Content-Length'] = len(compressed_data)
                response.headers['Vary'] = 'Accept-Encoding'
                
        except Exception as e:
            logger.error(f'GZIP compression failed: {e}')
        
        return response
    
    def set_cache_headers(self, response):
        """设置缓存头"""
        path = request.path
        
        # 静态资源缓存
        if path.startswith('/static/'):
            response.headers['Cache-Control'] = 'public, max-age=604800'  # 7天
            response.headers['Expires'] = 'Thu, 31 Dec 2025 23:59:59 GMT'
            return response
        
        # API接口缓存
        if path.startswith('/api/'):
            # 状态接口短缓存
            if '/status' in path:
                response.headers['Cache-Control'] = 'public, max-age=30'
            # 配置接口长缓存
            elif '/config' in path:
                response.headers['Cache-Control'] = 'public, max-age=600'
            # 其他API中等缓存
            else:
                response.headers['Cache-Control'] = 'public, max-age=60'
        else:
            # 页面不缓存
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        
        return response
    
    def set_security_headers(self, response):
        """设置安全头"""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response
    
    def get_performance_stats(self):
        """获取性能统计"""
        import psutil
        import gc
        
        # 系统资源使用情况
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 垃圾回收统计
        gc_stats = gc.get_stats()
        
        stats = {
            'system': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_mb': memory.available // 1024 // 1024,
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free // 1024 // 1024 // 1024
            },
            'cache': {
                'entries': len(self.cache),
                'hit_rate': getattr(self, 'cache_hit_rate', 0)
            },
            'gc': {
                'collections': sum(stat['collections'] for stat in gc_stats),
                'collected': sum(stat['collected'] for stat in gc_stats),
                'uncollectable': sum(stat['uncollectable'] for stat in gc_stats)
            }
        }
        
        return Response(
            json.dumps(stats, ensure_ascii=False, indent=2),
            mimetype='application/json'
        )


def cache_response(timeout=300, key_func=None):
    """响应缓存装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{request.path}?{request.query_string.decode()}"
            
            # 检查缓存
            middleware = current_app.extensions.get('performance_middleware')
            if middleware and cache_key in middleware.cache:
                cached_time = middleware.cache_timeouts.get(cache_key, 0)
                if time.time() - cached_time < timeout:
                    return middleware.cache[cache_key]
            
            # 执行函数
            result = f(*args, **kwargs)
            
            # 存储到缓存
            if middleware:
                middleware.cache[cache_key] = result
                middleware.cache_timeouts[cache_key] = time.time()
                
                # 清理过期缓存
                current_time = time.time()
                expired_keys = [
                    key for key, cached_time in middleware.cache_timeouts.items()
                    if current_time - cached_time > timeout
                ]
                for key in expired_keys:
                    middleware.cache.pop(key, None)
                    middleware.cache_timeouts.pop(key, None)
            
            return result
        return decorated_function
    return decorator


def measure_time(func_name=None):
    """性能测量装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            try:
                result = f(*args, **kwargs)
                return result
            finally:
                end_time = time.time()
                duration = end_time - start_time
                name = func_name or f.__name__
                logger.info(f'Function {name} took {duration:.3f}s')
        return decorated_function
    return decorator