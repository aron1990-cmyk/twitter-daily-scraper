
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一异常处理模块
"""

from datetime import datetime
from typing import Optional, Dict, Any

class ScrapingException(Exception):
    """采集异常基类"""
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()

# 为了向后兼容，添加别名
TwitterScrapingError = ScrapingException
BrowserError = NetworkException = ScrapingException
ConfigurationError = ConfigurationException = ScrapingException
DataValidationError = DataValidationException = ScrapingException
RetryExhaustedError = ScrapingException

class NetworkException(ScrapingException):
    """网络异常"""
    pass

class ParsingException(ScrapingException):
    """解析异常"""
    pass

class AuthenticationException(ScrapingException):
    """认证异常"""
    pass

class RateLimitException(ScrapingException):
    """频率限制异常"""
    pass

class ConfigurationException(ScrapingException):
    """配置异常"""
    pass

class DataValidationException(ScrapingException):
    """数据验证异常"""
    pass

# 添加具体的异常类
class TwitterScrapingError(ScrapingException):
    """Twitter采集异常"""
    pass

class BrowserError(ScrapingException):
    """浏览器异常"""
    pass

class ConfigurationError(ScrapingException):
    """配置错误"""
    pass

class DataValidationError(ScrapingException):
    """数据验证错误"""
    pass

class RetryExhaustedError(ScrapingException):
    """重试次数耗尽异常"""
    pass
