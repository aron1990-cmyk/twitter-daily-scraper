#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异常处理模块 - 统一的错误处理、重试机制和异常分类
提供智能的异常恢复策略和详细的错误日志
"""

import logging
import time
import traceback
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Type
from functools import wraps
from enum import Enum
from dataclasses import dataclass
import asyncio
import random


class ErrorSeverity(str, Enum):
    """错误严重程度"""
    LOW = "low"          # 轻微错误，可以继续
    MEDIUM = "medium"    # 中等错误，需要重试
    HIGH = "high"        # 严重错误，需要人工干预
    CRITICAL = "critical" # 致命错误，停止所有操作


class ErrorCategory(str, Enum):
    """错误分类"""
    NETWORK = "network"              # 网络相关错误
    BROWSER = "browser"              # 浏览器相关错误
    PARSING = "parsing"              # 数据解析错误
    RATE_LIMIT = "rate_limit"        # 限流错误
    AUTHENTICATION = "authentication" # 认证错误
    STORAGE = "storage"              # 存储错误
    VALIDATION = "validation"        # 数据验证错误
    TIMEOUT = "timeout"              # 超时错误
    UNKNOWN = "unknown"              # 未知错误


@dataclass
class ErrorInfo:
    """错误信息数据模型"""
    error_type: str
    error_message: str
    category: ErrorCategory
    severity: ErrorSeverity
    timestamp: datetime
    context: Dict[str, Any]
    traceback_info: str
    retry_count: int = 0
    max_retries: int = 3
    retry_delay: float = 1.0
    
    @property
    def should_retry(self) -> bool:
        """是否应该重试"""
        return (
            self.retry_count < self.max_retries and
            self.severity in [ErrorSeverity.LOW, ErrorSeverity.MEDIUM]
        )
    
    @property
    def next_retry_delay(self) -> float:
        """下次重试延迟时间（指数退避）"""
        base_delay = self.retry_delay
        exponential_delay = base_delay * (2 ** self.retry_count)
        # 添加随机抖动，避免雷群效应
        jitter = random.uniform(0.1, 0.3) * exponential_delay
        return exponential_delay + jitter


class TwitterScrapingException(Exception):
    """推特抓取异常基类"""
    
    def __init__(self, message: str, category: ErrorCategory = ErrorCategory.UNKNOWN, 
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM, context: Dict[str, Any] = None):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.context = context or {}
        self.timestamp = datetime.now()


class NetworkException(TwitterScrapingException):
    """网络异常"""
    
    def __init__(self, message: str, status_code: int = None, **kwargs):
        super().__init__(message, ErrorCategory.NETWORK, ErrorSeverity.MEDIUM, **kwargs)
        self.status_code = status_code


class BrowserException(TwitterScrapingException):
    """浏览器异常"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCategory.BROWSER, ErrorSeverity.HIGH, **kwargs)


class ParsingException(TwitterScrapingException):
    """解析异常"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCategory.PARSING, ErrorSeverity.LOW, **kwargs)


class RateLimitException(TwitterScrapingException):
    """限流异常"""
    
    def __init__(self, message: str, retry_after: int = None, **kwargs):
        super().__init__(message, ErrorCategory.RATE_LIMIT, ErrorSeverity.MEDIUM, **kwargs)
        self.retry_after = retry_after


class AuthenticationException(TwitterScrapingException):
    """认证异常"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCategory.AUTHENTICATION, ErrorSeverity.HIGH, **kwargs)


class StorageException(TwitterScrapingException):
    """存储异常"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCategory.STORAGE, ErrorSeverity.MEDIUM, **kwargs)


class ValidationException(TwitterScrapingException):
    """验证异常"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCategory.VALIDATION, ErrorSeverity.LOW, **kwargs)


class TimeoutException(TwitterScrapingException):
    """超时异常"""
    
    def __init__(self, message: str, timeout_duration: float = None, **kwargs):
        super().__init__(message, ErrorCategory.TIMEOUT, ErrorSeverity.MEDIUM, **kwargs)
        self.timeout_duration = timeout_duration


class ExceptionHandler:
    """异常处理器"""
    
    def __init__(self, log_file: str = None):
        self.logger = logging.getLogger(__name__)
        self.error_history: List[ErrorInfo] = []
        self.error_patterns: Dict[str, ErrorCategory] = self._init_error_patterns()
        self.recovery_strategies: Dict[ErrorCategory, Callable] = self._init_recovery_strategies()
        self.checkpoint_manager = CheckpointManager()
        
        # 配置日志
        if log_file:
            handler = logging.FileHandler(log_file, encoding='utf-8')
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def _init_error_patterns(self) -> Dict[str, ErrorCategory]:
        """初始化错误模式匹配"""
        return {
            # 网络错误
            'connection': ErrorCategory.NETWORK,
            'timeout': ErrorCategory.TIMEOUT,
            'dns': ErrorCategory.NETWORK,
            'ssl': ErrorCategory.NETWORK,
            'http': ErrorCategory.NETWORK,
            'socket': ErrorCategory.NETWORK,
            
            # 浏览器错误
            'browser': ErrorCategory.BROWSER,
            'playwright': ErrorCategory.BROWSER,
            'selenium': ErrorCategory.BROWSER,
            'page': ErrorCategory.BROWSER,
            'element': ErrorCategory.BROWSER,
            'navigation': ErrorCategory.BROWSER,
            
            # 限流错误
            'rate limit': ErrorCategory.RATE_LIMIT,
            'too many requests': ErrorCategory.RATE_LIMIT,
            '429': ErrorCategory.RATE_LIMIT,
            'quota': ErrorCategory.RATE_LIMIT,
            
            # 认证错误
            'unauthorized': ErrorCategory.AUTHENTICATION,
            'forbidden': ErrorCategory.AUTHENTICATION,
            'login': ErrorCategory.AUTHENTICATION,
            'authentication': ErrorCategory.AUTHENTICATION,
            '401': ErrorCategory.AUTHENTICATION,
            '403': ErrorCategory.AUTHENTICATION,
            
            # 解析错误
            'json': ErrorCategory.PARSING,
            'parse': ErrorCategory.PARSING,
            'decode': ErrorCategory.PARSING,
            'format': ErrorCategory.PARSING,
            
            # 存储错误
            'file': ErrorCategory.STORAGE,
            'disk': ErrorCategory.STORAGE,
            'permission': ErrorCategory.STORAGE,
            'space': ErrorCategory.STORAGE,
        }
    
    def _init_recovery_strategies(self) -> Dict[ErrorCategory, Callable]:
        """初始化恢复策略"""
        return {
            ErrorCategory.NETWORK: self._recover_network_error,
            ErrorCategory.BROWSER: self._recover_browser_error,
            ErrorCategory.RATE_LIMIT: self._recover_rate_limit_error,
            ErrorCategory.TIMEOUT: self._recover_timeout_error,
            ErrorCategory.PARSING: self._recover_parsing_error,
            ErrorCategory.STORAGE: self._recover_storage_error,
        }
    
    def classify_error(self, error: Exception) -> ErrorCategory:
        """分类错误"""
        error_message = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # 检查自定义异常
        if isinstance(error, TwitterScrapingException):
            return error.category
        
        # 模式匹配
        for pattern, category in self.error_patterns.items():
            if pattern in error_message or pattern in error_type:
                return category
        
        return ErrorCategory.UNKNOWN
    
    def determine_severity(self, error: Exception, category: ErrorCategory) -> ErrorSeverity:
        """确定错误严重程度"""
        if isinstance(error, TwitterScrapingException):
            return error.severity
        
        # 根据分类确定严重程度
        severity_map = {
            ErrorCategory.NETWORK: ErrorSeverity.MEDIUM,
            ErrorCategory.BROWSER: ErrorSeverity.HIGH,
            ErrorCategory.PARSING: ErrorSeverity.LOW,
            ErrorCategory.RATE_LIMIT: ErrorSeverity.MEDIUM,
            ErrorCategory.AUTHENTICATION: ErrorSeverity.HIGH,
            ErrorCategory.STORAGE: ErrorSeverity.MEDIUM,
            ErrorCategory.VALIDATION: ErrorSeverity.LOW,
            ErrorCategory.TIMEOUT: ErrorSeverity.MEDIUM,
            ErrorCategory.UNKNOWN: ErrorSeverity.MEDIUM,
        }
        
        return severity_map.get(category, ErrorSeverity.MEDIUM)
    
    def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> ErrorInfo:
        """处理错误"""
        category = self.classify_error(error)
        severity = self.determine_severity(error, category)
        
        error_info = ErrorInfo(
            error_type=type(error).__name__,
            error_message=str(error),
            category=category,
            severity=severity,
            timestamp=datetime.now(),
            context=context or {},
            traceback_info=traceback.format_exc()
        )
        
        # 记录错误
        self.error_history.append(error_info)
        self._log_error(error_info)
        
        # 尝试恢复
        if category in self.recovery_strategies:
            try:
                self.recovery_strategies[category](error_info)
            except Exception as recovery_error:
                self.logger.error(f"恢复策略执行失败: {recovery_error}")
        
        return error_info
    
    def _log_error(self, error_info: ErrorInfo):
        """记录错误日志"""
        log_message = (
            f"错误处理 - 类型: {error_info.error_type}, "
            f"分类: {error_info.category.value}, "
            f"严重程度: {error_info.severity.value}, "
            f"消息: {error_info.error_message}"
        )
        
        if error_info.context:
            log_message += f", 上下文: {error_info.context}"
        
        if error_info.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif error_info.severity == ErrorSeverity.HIGH:
            self.logger.error(log_message)
        elif error_info.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
        
        # 记录详细的堆栈信息
        if error_info.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            self.logger.debug(f"堆栈信息:\n{error_info.traceback_info}")
    
    def _recover_network_error(self, error_info: ErrorInfo):
        """网络错误恢复策略"""
        self.logger.info("执行网络错误恢复策略")
        # 增加重试延迟
        error_info.retry_delay = max(error_info.retry_delay * 2, 30)
        error_info.max_retries = 5
    
    def _recover_browser_error(self, error_info: ErrorInfo):
        """浏览器错误恢复策略"""
        self.logger.info("执行浏览器错误恢复策略")
        # 建议重启浏览器
        error_info.context['recovery_action'] = 'restart_browser'
        error_info.max_retries = 2
    
    def _recover_rate_limit_error(self, error_info: ErrorInfo):
        """限流错误恢复策略"""
        self.logger.info("执行限流错误恢复策略")
        # 大幅增加延迟时间
        error_info.retry_delay = 300  # 5分钟
        error_info.max_retries = 10
        error_info.context['recovery_action'] = 'long_delay'
    
    def _recover_timeout_error(self, error_info: ErrorInfo):
        """超时错误恢复策略"""
        self.logger.info("执行超时错误恢复策略")
        # 增加超时时间
        error_info.retry_delay = 60
        error_info.context['recovery_action'] = 'increase_timeout'
    
    def _recover_parsing_error(self, error_info: ErrorInfo):
        """解析错误恢复策略"""
        self.logger.info("执行解析错误恢复策略")
        # 解析错误通常不需要重试太多次
        error_info.max_retries = 2
        error_info.context['recovery_action'] = 'skip_item'
    
    def _recover_storage_error(self, error_info: ErrorInfo):
        """存储错误恢复策略"""
        self.logger.info("执行存储错误恢复策略")
        # 检查磁盘空间和权限
        error_info.context['recovery_action'] = 'check_storage'
        error_info.max_retries = 3
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计信息"""
        if not self.error_history:
            return {"total_errors": 0}
        
        # 按分类统计
        category_counts = {}
        for category in ErrorCategory:
            category_counts[category.value] = sum(
                1 for error in self.error_history if error.category == category
            )
        
        # 按严重程度统计
        severity_counts = {}
        for severity in ErrorSeverity:
            severity_counts[severity.value] = sum(
                1 for error in self.error_history if error.severity == severity
            )
        
        # 最近24小时的错误
        recent_cutoff = datetime.now() - timedelta(hours=24)
        recent_errors = [
            error for error in self.error_history
            if error.timestamp >= recent_cutoff
        ]
        
        return {
            "total_errors": len(self.error_history),
            "category_distribution": category_counts,
            "severity_distribution": severity_counts,
            "recent_24h_errors": len(recent_errors),
            "most_common_category": max(category_counts, key=category_counts.get) if category_counts else None,
            "most_common_severity": max(severity_counts, key=severity_counts.get) if severity_counts else None,
        }
    
    def clear_old_errors(self, hours_to_keep: int = 72):
        """清理旧的错误记录"""
        cutoff_time = datetime.now() - timedelta(hours=hours_to_keep)
        original_count = len(self.error_history)
        
        self.error_history = [
            error for error in self.error_history
            if error.timestamp >= cutoff_time
        ]
        
        removed_count = original_count - len(self.error_history)
        if removed_count > 0:
            self.logger.info(f"清理了 {removed_count} 条旧错误记录")


class CheckpointManager:
    """断点续传管理器"""
    
    def __init__(self, checkpoint_dir: str = "checkpoints"):
        self.checkpoint_dir = checkpoint_dir
        self.logger = logging.getLogger('CheckpointManager')
        
        # 确保检查点目录存在
        os.makedirs(checkpoint_dir, exist_ok=True)
    
    def save_checkpoint(self, task_id: str, checkpoint_data: Dict[str, Any]) -> bool:
        """保存检查点数据"""
        try:
            checkpoint_file = os.path.join(self.checkpoint_dir, f"task_{task_id}.json")
            
            checkpoint_info = {
                'task_id': task_id,
                'timestamp': datetime.now().isoformat(),
                'data': checkpoint_data
            }
            
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_info, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"检查点已保存: {checkpoint_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存检查点失败: {e}")
            return False
    
    def load_checkpoint(self, task_id: str) -> Optional[Dict[str, Any]]:
        """加载检查点数据"""
        try:
            checkpoint_file = os.path.join(self.checkpoint_dir, f"task_{task_id}.json")
            
            if not os.path.exists(checkpoint_file):
                return None
            
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint_info = json.load(f)
            
            self.logger.info(f"检查点已加载: {checkpoint_file}")
            return checkpoint_info.get('data')
            
        except Exception as e:
            self.logger.error(f"加载检查点失败: {e}")
            return None
    
    def delete_checkpoint(self, task_id: str) -> bool:
        """删除检查点文件"""
        try:
            checkpoint_file = os.path.join(self.checkpoint_dir, f"task_{task_id}.json")
            
            if os.path.exists(checkpoint_file):
                os.remove(checkpoint_file)
                self.logger.info(f"检查点已删除: {checkpoint_file}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"删除检查点失败: {e}")
            return False
    
    def list_checkpoints(self) -> List[str]:
        """列出所有可用的检查点"""
        try:
            checkpoints = []
            for filename in os.listdir(self.checkpoint_dir):
                if filename.startswith('task_') and filename.endswith('.json'):
                    task_id = filename[5:-5]  # 移除 'task_' 前缀和 '.json' 后缀
                    checkpoints.append(task_id)
            
            return checkpoints
            
        except Exception as e:
            self.logger.error(f"列出检查点失败: {e}")
            return []


def retry_on_error(max_retries: int = 3, delay: float = 1.0, 
                  backoff_factor: float = 2.0, exceptions: tuple = None):
    """重试装饰器"""
    if exceptions is None:
        exceptions = (Exception,)
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        raise e
                    
                    # 计算延迟时间
                    current_delay = delay * (backoff_factor ** attempt)
                    # 添加随机抖动
                    jitter = random.uniform(0.1, 0.3) * current_delay
                    sleep_time = current_delay + jitter
                    
                    logging.getLogger(__name__).warning(
                        f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败: {e}, "
                        f"{sleep_time:.2f}秒后重试"
                    )
                    
                    time.sleep(sleep_time)
            
            raise last_exception
        
        return wrapper
    return decorator


def resilient_task_execution(checkpoint_manager: CheckpointManager = None):
    """弹性任务执行装饰器，支持断点续传和错误恢复"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            task_id = kwargs.get('task_id') or str(int(time.time()))
            logger = logging.getLogger('ResilientTask')
            
            # 尝试从检查点恢复
            if checkpoint_manager:
                checkpoint_data = checkpoint_manager.load_checkpoint(task_id)
                if checkpoint_data:
                    logger.info(f"从检查点恢复任务 {task_id}")
                    kwargs.update(checkpoint_data)
            
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    # 执行任务
                    result = await func(*args, **kwargs)
                    
                    # 任务成功完成，删除检查点
                    if checkpoint_manager:
                        checkpoint_manager.delete_checkpoint(task_id)
                    
                    return result
                    
                except Exception as e:
                    logger.error(f"任务执行失败 (尝试 {attempt + 1}/{max_attempts}): {e}")
                    
                    if attempt < max_attempts - 1:
                        # 保存检查点
                        if checkpoint_manager:
                            checkpoint_data = {
                                'attempt': attempt + 1,
                                'last_error': str(e),
                                'kwargs': kwargs
                            }
                            checkpoint_manager.save_checkpoint(task_id, checkpoint_data)
                        
                        # 等待后重试
                        await asyncio.sleep(30 * (attempt + 1))
                    else:
                        # 最后一次尝试失败
                        raise e
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            task_id = kwargs.get('task_id') or str(int(time.time()))
            logger = logging.getLogger('ResilientTask')
            
            # 尝试从检查点恢复
            if checkpoint_manager:
                checkpoint_data = checkpoint_manager.load_checkpoint(task_id)
                if checkpoint_data:
                    logger.info(f"从检查点恢复任务 {task_id}")
                    kwargs.update(checkpoint_data)
            
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    # 执行任务
                    result = func(*args, **kwargs)
                    
                    # 任务成功完成，删除检查点
                    if checkpoint_manager:
                        checkpoint_manager.delete_checkpoint(task_id)
                    
                    return result
                    
                except Exception as e:
                    logger.error(f"任务执行失败 (尝试 {attempt + 1}/{max_attempts}): {e}")
                    
                    if attempt < max_attempts - 1:
                        # 保存检查点
                        if checkpoint_manager:
                            checkpoint_data = {
                                'attempt': attempt + 1,
                                'last_error': str(e),
                                'kwargs': kwargs
                            }
                            checkpoint_manager.save_checkpoint(task_id, checkpoint_data)
                        
                        # 等待后重试
                        time.sleep(30 * (attempt + 1))
                    else:
                        # 最后一次尝试失败
                        raise e
        
        # 根据函数类型返回相应的包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def async_retry_on_error(max_retries: int = 3, delay: float = 1.0, 
                        backoff_factor: float = 2.0, exceptions: tuple = None):
    """异步重试装饰器"""
    if exceptions is None:
        exceptions = (Exception,)
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        raise e
                    
                    # 计算延迟时间
                    current_delay = delay * (backoff_factor ** attempt)
                    # 添加随机抖动
                    jitter = random.uniform(0.1, 0.3) * current_delay
                    sleep_time = current_delay + jitter
                    
                    logging.getLogger(__name__).warning(
                        f"异步函数 {func.__name__} 第 {attempt + 1} 次尝试失败: {e}, "
                        f"{sleep_time:.2f}秒后重试"
                    )
                    
                    await asyncio.sleep(sleep_time)
            
            raise last_exception
        
        return wrapper
    return decorator


class CircuitBreaker:
    """熔断器模式实现"""
    
    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
        self.logger = logging.getLogger(__name__)
    
    def call(self, func, *args, **kwargs):
        """调用函数，应用熔断器逻辑"""
        if self.state == 'OPEN':
            if self._should_attempt_reset():
                self.state = 'HALF_OPEN'
                self.logger.info("熔断器进入半开状态")
            else:
                raise Exception("熔断器开启，拒绝调用")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """是否应该尝试重置"""
        return (
            self.last_failure_time and
            time.time() - self.last_failure_time >= self.timeout
        )
    
    def _on_success(self):
        """成功时的处理"""
        self.failure_count = 0
        self.state = 'CLOSED'
        if self.state != 'CLOSED':
            self.logger.info("熔断器重置为关闭状态")
    
    def _on_failure(self):
        """失败时的处理"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
            self.logger.warning(f"熔断器开启，失败次数: {self.failure_count}")


# 全局异常处理器实例
global_exception_handler = ExceptionHandler()


def handle_exception(error: Exception, context: Dict[str, Any] = None) -> ErrorInfo:
    """全局异常处理函数"""
    return global_exception_handler.handle_error(error, context)