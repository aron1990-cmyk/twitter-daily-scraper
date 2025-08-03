# -*- coding: utf-8 -*-
"""
性能优化配置文件
包含所有性能相关的配置和优化设置
"""

import os
from datetime import timedelta

# ============ 缓存配置 ============
CACHE_CONFIG = {
    'CACHE_TYPE': 'simple',  # 使用内存缓存
    'CACHE_DEFAULT_TIMEOUT': 300,  # 默认缓存5分钟
    'CACHE_THRESHOLD': 500,  # 最大缓存条目数
}

# API接口缓存时间配置（秒）
API_CACHE_TIMEOUTS = {
    '/api/status': 30,  # 系统状态缓存30秒
    '/api/influencers': 60,  # 博主列表缓存1分钟
    '/api/influencers/stats': 120,  # 博主统计缓存2分钟
    '/api/influencers/categories': 300,  # 分类列表缓存5分钟
    '/api/tasks': 30,  # 任务列表缓存30秒
    '/api/config': 600,  # 配置信息缓存10分钟
}

# ============ 压缩配置 ============
COMPRESSION_CONFIG = {
    'COMPRESS_MIMETYPES': [
        'text/html',
        'text/css',
        'text/xml',
        'text/javascript',
        'application/json',
        'application/javascript',
        'application/xml+rss',
        'application/atom+xml',
        'image/svg+xml'
    ],
    'COMPRESS_LEVEL': 6,  # 压缩级别 1-9
    'COMPRESS_MIN_SIZE': 500,  # 最小压缩文件大小（字节）
}

# ============ 静态资源配置 ============
STATIC_CONFIG = {
    'SEND_FILE_MAX_AGE_DEFAULT': timedelta(days=7),  # 静态文件缓存7天
    'STATIC_CACHE_TIMEOUT': 604800,  # 7天（秒）
    'STATIC_CACHE_CONTROL': 'public, max-age=604800',
}

# ============ 数据库优化配置 ============
DATABASE_CONFIG = {
    'SQLALCHEMY_ENGINE_OPTIONS': {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'max_overflow': 0,
        'echo': False,  # 生产环境关闭SQL日志
    },
    'SQLALCHEMY_RECORD_QUERIES': False,  # 关闭查询记录以提升性能
}

# ============ 分页配置 ============
PAGINATION_CONFIG = {
    'DEFAULT_PER_PAGE': 20,  # 默认每页条数
    'MAX_PER_PAGE': 100,  # 最大每页条数
    'TASKS_PER_PAGE': 20,
    'INFLUENCERS_PER_PAGE': 20,
    'TWEETS_PER_PAGE': 50,
}

# ============ 异步任务配置 ============
ASYNC_CONFIG = {
    'MAX_WORKERS': 4,  # 最大工作线程数
    'TASK_TIMEOUT': 300,  # 任务超时时间（秒）
    'QUEUE_SIZE': 100,  # 队列大小
}

# ============ 前端优化配置 ============
FRONTEND_CONFIG = {
    'POLLING_INTERVALS': {
        'status_update': 60000,  # 状态更新间隔（毫秒）
        'task_refresh': 30000,   # 任务刷新间隔
        'data_refresh': 60000,   # 数据刷新间隔
    },
    'LAZY_LOADING': True,  # 启用懒加载
    'VIRTUAL_SCROLLING': True,  # 启用虚拟滚动
    'DEBOUNCE_DELAY': 300,  # 防抖延迟（毫秒）
}

# ============ CDN配置 ============
CDN_CONFIG = {
    'USE_CDN': True,
    'CDN_DOMAIN': 'https://cdn.jsdelivr.net',
    'FALLBACK_LOCAL': True,  # CDN失败时回退到本地资源
    'RESOURCES': {
        'bootstrap_css': 'npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
        'bootstrap_js': 'npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
        'fontawesome': 'npm/@fortawesome/fontawesome-free@6.4.0/css/all.min.css',
        'jquery': 'npm/jquery@3.7.0/dist/jquery.min.js',
    }
}

# ============ 监控配置 ============
MONITORING_CONFIG = {
    'ENABLE_PROFILING': False,  # 生产环境关闭性能分析
    'LOG_SLOW_QUERIES': True,  # 记录慢查询
    'SLOW_QUERY_THRESHOLD': 1.0,  # 慢查询阈值（秒）
    'RESPONSE_TIME_LOGGING': True,  # 记录响应时间
}

# ============ 内存优化配置 ============
MEMORY_CONFIG = {
    'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB最大请求大小
    'GC_THRESHOLD': (700, 10, 10),  # 垃圾回收阈值
    'MEMORY_LIMIT_MB': 512,  # 内存限制
}

# ============ 安全配置 ============
SECURITY_CONFIG = {
    'SESSION_COOKIE_SECURE': False,  # 开发环境设为False
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SAMESITE': 'Lax',
    'PERMANENT_SESSION_LIFETIME': timedelta(hours=24),
}

# ============ 整合所有配置 ============
PERFORMANCE_CONFIG = {
    **CACHE_CONFIG,
    **COMPRESSION_CONFIG,
    **STATIC_CONFIG,
    **DATABASE_CONFIG,
    **PAGINATION_CONFIG,
    **ASYNC_CONFIG,
    **FRONTEND_CONFIG,
    **CDN_CONFIG,
    **MONITORING_CONFIG,
    **MEMORY_CONFIG,
    **SECURITY_CONFIG,
    'API_CACHE_TIMEOUTS': API_CACHE_TIMEOUTS,
}