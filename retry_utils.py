
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重试机制工具
"""

import time
import random
import logging
import asyncio
from typing import Callable, Any, Optional, Type, Tuple
from functools import wraps
from dataclasses import dataclass
from exceptions import RetryExhaustedError, RateLimitException, NetworkException

logger = logging.getLogger(__name__)

@dataclass
class RetryConfig:
    """重试配置"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    
def exponential_backoff(attempt: int, exponential_base: float = 2.0, base_delay: float = 1.0, max_delay: float = 60.0, jitter: bool = True) -> float:
    """计算指数退避延迟"""
    delay = base_delay * (exponential_base ** (attempt - 1))
    delay = min(delay, max_delay)
    
    if jitter:
        delay *= (0.5 + random.random() * 0.5)
    
    return delay

def exponential_backoff_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    指数退避重试装饰器
    
    Args:
        max_retries: 最大重试次数
        base_delay: 基础延迟时间（秒）
        max_delay: 最大延迟时间（秒）
        exponential_base: 指数基数
        jitter: 是否添加随机抖动
        exceptions: 需要重试的异常类型
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"函数 {func.__name__} 重试 {max_retries} 次后仍然失败")
                        raise e
                    
                    # 计算延迟时间
                    delay = min(
                        base_delay * (exponential_base ** attempt),
                        max_delay
                    )
                    
                    # 添加随机抖动
                    if jitter:
                        delay *= (0.5 + random.random() * 0.5)
                    
                    logger.warning(
                        f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败: {e}, "
                        f"{delay:.2f}秒后重试"
                    )
                    
                    time.sleep(delay)
            
            # 这行代码理论上不会执行到
            raise last_exception
        
        return wrapper
    return decorator

def rate_limit_retry(
    max_retries: int = 5,
    base_delay: float = 60.0,
    exceptions: Tuple[Type[Exception], ...] = (RateLimitException,)
):
    """
    频率限制重试装饰器
    """
    return exponential_backoff_retry(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=300.0,  # 最大等待5分钟
        exponential_base=1.5,
        exceptions=exceptions
    )

def network_retry(
    max_retries: int = 3,
    exceptions: Tuple[Type[Exception], ...] = (NetworkException,)
):
    """
    网络错误重试装饰器
    """
    return exponential_backoff_retry(
        max_retries=max_retries,
        base_delay=2.0,
        max_delay=30.0,
        exceptions=exceptions
    )

def retry_with_backoff(
    func: Optional[Callable] = None,
    *,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    异步重试装饰器，支持指数退避
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        logger.error(f"函数 {func.__name__} 重试 {max_attempts} 次后仍然失败")
                        raise e
                    
                    # 计算延迟时间
                    delay = exponential_backoff(
                        attempt + 1, 
                        backoff_factor, 
                        base_delay, 
                        max_delay
                    )
                    
                    logger.warning(
                        f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败: {e}, "
                        f"{delay:.2f}秒后重试"
                    )
                    
                    await asyncio.sleep(delay)
            
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        logger.error(f"函数 {func.__name__} 重试 {max_attempts} 次后仍然失败")
                        raise e
                    
                    # 计算延迟时间
                    delay = exponential_backoff(
                        attempt + 1, 
                        backoff_factor, 
                        base_delay, 
                        max_delay
                    )
                    
                    logger.warning(
                        f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败: {e}, "
                        f"{delay:.2f}秒后重试"
                    )
                    
                    time.sleep(delay)
            
            raise last_exception
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    if func is None:
        return decorator
    else:
        return decorator(func)
