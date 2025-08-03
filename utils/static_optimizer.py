# -*- coding: utf-8 -*-
"""
静态资源优化器
处理CSS、JS、图片等静态资源的压缩、缓存和CDN配置
"""

import os
import gzip
import hashlib
import logging
from typing import Dict, List, Optional
from flask import Flask, request, make_response, send_from_directory
from werkzeug.middleware.http_proxy import ProxyMiddleware

logger = logging.getLogger(__name__)

class StaticResourceOptimizer:
    """静态资源优化器"""
    
    def __init__(self, app: Flask = None):
        self.app = app
        self.static_cache = {}
        self.gzip_cache = {}
        self.version_cache = {}
        
        # CDN配置
        self.cdn_config = {
            'enabled': False,
            'base_url': 'https://cdn.jsdelivr.net/npm',
            'fallback_enabled': True,
            'libraries': {
                'bootstrap': {
                    'css': 'bootstrap@5.3.0/dist/css/bootstrap.min.css',
                    'js': 'bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js'
                },
                'fontawesome': {
                    'css': '@fortawesome/fontawesome-free@6.4.0/css/all.min.css'
                },
                'jquery': {
                    'js': 'jquery@3.7.0/dist/jquery.min.js'
                }
            }
        }
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """初始化应用"""
        self.app = app
        
        # 配置静态文件缓存
        app.config.setdefault('STATIC_CACHE_TIMEOUT', 604800)  # 7天
        app.config.setdefault('STATIC_GZIP_ENABLED', True)
        app.config.setdefault('STATIC_VERSION_ENABLED', True)
        
        # 注册静态文件处理器
        self._setup_static_handlers()
        
        # 设置响应头优化
        self._setup_response_headers()
    
    def _setup_static_handlers(self):
        """设置静态文件处理器"""
        @self.app.route('/static/<path:filename>')
        def optimized_static(filename):
            return self._serve_static_file(filename)
        
        @self.app.route('/static/js/<path:filename>')
        def optimized_js(filename):
            return self._serve_static_file(f'js/{filename}', 'application/javascript')
        
        @self.app.route('/static/css/<path:filename>')
        def optimized_css(filename):
            return self._serve_static_file(f'css/{filename}', 'text/css')
        
        @self.app.route('/static/img/<path:filename>')
        def optimized_images(filename):
            return self._serve_static_file(f'img/{filename}')
    
    def _serve_static_file(self, filename: str, content_type: str = None):
        """优化的静态文件服务"""
        try:
            static_folder = self.app.static_folder
            file_path = os.path.join(static_folder, filename)
            
            if not os.path.exists(file_path):
                return 'File not found', 404
            
            # 检查文件修改时间
            file_mtime = os.path.getmtime(file_path)
            
            # 生成ETag
            etag = self._generate_etag(file_path, file_mtime)
            
            # 检查客户端缓存
            if request.headers.get('If-None-Match') == etag:
                return '', 304
            
            # 读取文件内容
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # 创建响应
            response = make_response(content)
            
            # 设置内容类型
            if content_type:
                response.headers['Content-Type'] = content_type
            elif filename.endswith('.css'):
                response.headers['Content-Type'] = 'text/css; charset=utf-8'
            elif filename.endswith('.js'):
                response.headers['Content-Type'] = 'application/javascript; charset=utf-8'
            elif filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg')):
                response.headers['Content-Type'] = f'image/{filename.split(".")[-1]}'
            
            # 设置缓存头
            cache_timeout = self.app.config['STATIC_CACHE_TIMEOUT']
            response.headers['Cache-Control'] = f'public, max-age={cache_timeout}'
            response.headers['ETag'] = etag
            response.headers['Expires'] = self._get_expires_header(cache_timeout)
            
            # GZIP压缩
            if (self.app.config['STATIC_GZIP_ENABLED'] and 
                self._should_compress(filename) and 
                'gzip' in request.headers.get('Accept-Encoding', '')):
                
                compressed_content = self._compress_content(content, filename)
                if compressed_content:
                    response.data = compressed_content
                    response.headers['Content-Encoding'] = 'gzip'
                    response.headers['Vary'] = 'Accept-Encoding'
            
            return response
            
        except Exception as e:
            logger.error(f'Error serving static file {filename}: {e}')
            return 'Internal Server Error', 500
    
    def _generate_etag(self, file_path: str, mtime: float) -> str:
        """生成ETag"""
        etag_data = f'{file_path}:{mtime}'.encode()
        return hashlib.md5(etag_data).hexdigest()
    
    def _get_expires_header(self, cache_timeout: int) -> str:
        """生成Expires头"""
        from datetime import datetime, timedelta
        expires = datetime.utcnow() + timedelta(seconds=cache_timeout)
        return expires.strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    def _should_compress(self, filename: str) -> bool:
        """判断是否应该压缩文件"""
        compressible_extensions = ['.css', '.js', '.html', '.json', '.xml', '.svg']
        return any(filename.endswith(ext) for ext in compressible_extensions)
    
    def _compress_content(self, content: bytes, filename: str) -> Optional[bytes]:
        """压缩内容"""
        try:
            # 检查缓存
            content_hash = hashlib.md5(content).hexdigest()
            cache_key = f'{filename}:{content_hash}'
            
            if cache_key in self.gzip_cache:
                return self.gzip_cache[cache_key]
            
            # 只压缩大于1KB的文件
            if len(content) < 1024:
                return None
            
            # GZIP压缩
            compressed = gzip.compress(content, compresslevel=6)
            
            # 只有压缩率超过10%才使用压缩版本
            if len(compressed) < len(content) * 0.9:
                self.gzip_cache[cache_key] = compressed
                return compressed
            
            return None
            
        except Exception as e:
            logger.error(f'Error compressing {filename}: {e}')
            return None
    
    def _setup_response_headers(self):
        """设置响应头优化"""
        @self.app.after_request
        def add_security_headers(response):
            # 安全头
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            
            # 性能头
            if request.path.startswith('/static/'):
                response.headers['X-Static-Optimized'] = 'true'
            
            return response
    
    def generate_asset_url(self, filename: str, with_version: bool = True) -> str:
        """生成资源URL（带版本号）"""
        if not with_version or not self.app.config.get('STATIC_VERSION_ENABLED'):
            return f'/static/{filename}'
        
        # 生成版本号
        version = self._get_file_version(filename)
        return f'/static/{filename}?v={version}'
    
    def _get_file_version(self, filename: str) -> str:
        """获取文件版本号"""
        if filename in self.version_cache:
            return self.version_cache[filename]
        
        try:
            static_folder = self.app.static_folder
            file_path = os.path.join(static_folder, filename)
            
            if os.path.exists(file_path):
                mtime = os.path.getmtime(file_path)
                version = hashlib.md5(str(mtime).encode()).hexdigest()[:8]
            else:
                version = 'unknown'
            
            self.version_cache[filename] = version
            return version
            
        except Exception as e:
            logger.error(f'Error getting version for {filename}: {e}')
            return 'error'
    
    def get_cdn_url(self, library: str, resource_type: str) -> Optional[str]:
        """获取CDN URL"""
        if not self.cdn_config['enabled']:
            return None
        
        lib_config = self.cdn_config['libraries'].get(library)
        if not lib_config:
            return None
        
        resource_path = lib_config.get(resource_type)
        if not resource_path:
            return None
        
        return f"{self.cdn_config['base_url']}/{resource_path}"
    
    def minify_css(self, css_content: str) -> str:
        """简单的CSS压缩"""
        try:
            # 移除注释
            import re
            css_content = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
            
            # 移除多余空白
            css_content = re.sub(r'\s+', ' ', css_content)
            css_content = re.sub(r';\s*}', '}', css_content)
            css_content = re.sub(r'\s*{\s*', '{', css_content)
            css_content = re.sub(r';\s*', ';', css_content)
            
            return css_content.strip()
            
        except Exception as e:
            logger.error(f'Error minifying CSS: {e}')
            return css_content
    
    def minify_js(self, js_content: str) -> str:
        """简单的JS压缩"""
        try:
            import re
            
            # 移除单行注释（保留URL中的//）
            js_content = re.sub(r'(?<!:)//.*$', '', js_content, flags=re.MULTILINE)
            
            # 移除多行注释
            js_content = re.sub(r'/\*.*?\*/', '', js_content, flags=re.DOTALL)
            
            # 移除多余空白（保留字符串中的空白）
            js_content = re.sub(r'\s+', ' ', js_content)
            
            return js_content.strip()
            
        except Exception as e:
            logger.error(f'Error minifying JS: {e}')
            return js_content
    
    def preload_critical_resources(self) -> List[str]:
        """生成关键资源预加载标签"""
        preload_tags = []
        
        # 预加载关键CSS
        critical_css = ['css/main.css', 'css/bootstrap.min.css']
        for css_file in critical_css:
            url = self.generate_asset_url(css_file)
            preload_tags.append(f'<link rel="preload" href="{url}" as="style">')
        
        # 预加载关键JS
        critical_js = ['js/main.js']
        for js_file in critical_js:
            url = self.generate_asset_url(js_file)
            preload_tags.append(f'<link rel="preload" href="{url}" as="script">')
        
        return preload_tags
    
    def get_optimization_stats(self) -> Dict[str, any]:
        """获取优化统计信息"""
        return {
            'gzip_cache_size': len(self.gzip_cache),
            'version_cache_size': len(self.version_cache),
            'cdn_enabled': self.cdn_config['enabled'],
            'available_libraries': list(self.cdn_config['libraries'].keys())
        }

# 全局静态资源优化器实例
static_optimizer = None

def init_static_optimizer(app: Flask):
    """初始化静态资源优化器"""
    global static_optimizer
    static_optimizer = StaticResourceOptimizer(app)
    logger.info('Static resource optimizer initialized')
    return static_optimizer

def asset_url(filename: str, with_version: bool = True) -> str:
    """模板函数：生成资源URL"""
    if static_optimizer:
        return static_optimizer.generate_asset_url(filename, with_version)
    return f'/static/{filename}'

def cdn_url(library: str, resource_type: str) -> Optional[str]:
    """模板函数：获取CDN URL"""
    if static_optimizer:
        return static_optimizer.get_cdn_url(library, resource_type)
    return None