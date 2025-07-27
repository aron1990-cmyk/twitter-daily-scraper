#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云端同步模块 - 支持Google Sheets和飞书文档API同步
"""

import requests
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import asyncio
import random
import os
import threading
import traceback

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    gspread = None
    Credentials = None

class FeishuRateLimiter:
    """
    飞书API频率限制控制器
    实现每秒3次调用限制和指数退避算法
    """
    
    def __init__(self):
        self.app_call_times = []  # 应用级调用时间记录
        self.doc_call_times = {}  # 文档级调用时间记录
        self.max_app_calls_per_second = 3  # 应用级每秒最大调用次数
        self.max_doc_calls_per_second = 3  # 文档级每秒最大调用次数
        self.base_delay = 1.0  # 基础延迟时间（秒）
        self.max_delay = 60.0  # 最大延迟时间（秒）
        self.logger = logging.getLogger(__name__)
    
    def _clean_old_calls(self, call_times: list, current_time: float):
        """清理1秒前的调用记录"""
        print(f"\n🧹 [RateLimit] 清理旧调用记录:")
        print(f"   - 方法: _clean_old_calls")
        print(f"   - call_times 参数类型: {type(call_times)}")
        print(f"   - call_times 参数长度: {len(call_times)}")
        print(f"   - call_times 参数内容: {call_times}")
        print(f"   - current_time 参数: {current_time} (类型: {type(current_time)})")
        print(f"   - current_time 格式化: {datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S.%f')}")
        print(f"   - 清理开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
        
        removed_count = 0
        original_length = len(call_times)
        
        while call_times and current_time - call_times[0] > 1.0:
            removed_time = call_times.pop(0)
            removed_count += 1
            print(f"   - 移除第 {removed_count} 个旧记录: {removed_time} ({datetime.fromtimestamp(removed_time).strftime('%Y-%m-%d %H:%M:%S.%f')})")
            print(f"     * 时间差: {current_time - removed_time:.6f} 秒")
            print(f"     * 是否超过1秒: {current_time - removed_time > 1.0}")
            print(f"     * 剩余记录数: {len(call_times)}")
        
        print(f"   - 清理结果:")
        print(f"     * 原始记录数: {original_length}")
        print(f"     * 移除记录数: {removed_count}")
        print(f"     * 剩余记录数: {len(call_times)}")
        print(f"     * 剩余记录内容: {call_times}")
        print(f"   - 清理完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
    
    def can_make_app_call(self) -> bool:
        """检查是否可以进行应用级API调用"""
        print(f"\n🔍 [RateLimit] 检查应用级API调用权限:")
        print(f"   - 方法: can_make_app_call")
        print(f"   - 检查开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
        
        current_time = time.time()
        print(f"   - 当前时间戳: {current_time} (类型: {type(current_time)})")
        print(f"   - 当前时间格式化: {datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S.%f')}")
        print(f"   - 应用级调用记录 (清理前): {self.app_call_times}")
        print(f"   - 应用级调用记录长度 (清理前): {len(self.app_call_times)}")
        print(f"   - 最大应用级调用数/秒: {self.max_app_calls_per_second}")
        
        print(f"\n🧹 [RateLimit] 调用清理方法...")
        self._clean_old_calls(self.app_call_times, current_time)
        
        print(f"\n📊 [RateLimit] 清理后状态检查:")
        print(f"   - 应用级调用记录 (清理后): {self.app_call_times}")
        print(f"   - 应用级调用记录长度 (清理后): {len(self.app_call_times)}")
        print(f"   - 当前调用数: {len(self.app_call_times)}")
        print(f"   - 最大允许调用数: {self.max_app_calls_per_second}")
        print(f"   - 比较结果: {len(self.app_call_times)} < {self.max_app_calls_per_second} = {len(self.app_call_times) < self.max_app_calls_per_second}")
        
        result = len(self.app_call_times) < self.max_app_calls_per_second
        print(f"   - 最终结果: {result} (类型: {type(result)})")
        print(f"   - 检查完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
        
        return result
    
    def can_make_doc_call(self, doc_id: str) -> bool:
        """检查是否可以进行文档级API调用"""
        print(f"\n🔍 [RateLimit] 检查文档级API调用权限:")
        print(f"   - 方法: can_make_doc_call")
        print(f"   - doc_id 参数: '{doc_id}' (类型: {type(doc_id)}, 长度: {len(doc_id)})")
        print(f"   - 检查开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
        
        current_time = time.time()
        print(f"   - 当前时间戳: {current_time} (类型: {type(current_time)})")
        print(f"   - 当前时间格式化: {datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S.%f')}")
        print(f"   - 文档调用记录字典: {self.doc_call_times}")
        print(f"   - 文档调用记录字典长度: {len(self.doc_call_times)}")
        print(f"   - 文档调用记录字典键: {list(self.doc_call_times.keys())}")
        print(f"   - doc_id 是否在记录中: {doc_id in self.doc_call_times}")
        
        if doc_id not in self.doc_call_times:
            print(f"   - 🆕 文档ID不存在，创建新记录")
            self.doc_call_times[doc_id] = []
            print(f"   - 创建后文档调用记录: {self.doc_call_times[doc_id]}")
        else:
            print(f"   - ✅ 文档ID已存在")
        
        print(f"   - 当前文档调用记录 (清理前): {self.doc_call_times[doc_id]}")
        print(f"   - 当前文档调用记录长度 (清理前): {len(self.doc_call_times[doc_id])}")
        print(f"   - 最大文档级调用数/秒: {self.max_doc_calls_per_second}")
        
        print(f"\n🧹 [RateLimit] 调用清理方法...")
        self._clean_old_calls(self.doc_call_times[doc_id], current_time)
        
        print(f"\n📊 [RateLimit] 清理后状态检查:")
        print(f"   - 当前文档调用记录 (清理后): {self.doc_call_times[doc_id]}")
        print(f"   - 当前文档调用记录长度 (清理后): {len(self.doc_call_times[doc_id])}")
        print(f"   - 当前调用数: {len(self.doc_call_times[doc_id])}")
        print(f"   - 最大允许调用数: {self.max_doc_calls_per_second}")
        print(f"   - 比较结果: {len(self.doc_call_times[doc_id])} < {self.max_doc_calls_per_second} = {len(self.doc_call_times[doc_id]) < self.max_doc_calls_per_second}")
        
        result = len(self.doc_call_times[doc_id]) < self.max_doc_calls_per_second
        print(f"   - 最终结果: {result} (类型: {type(result)})")
        print(f"   - 检查完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
        
        return result
    
    def record_app_call(self):
        """记录应用级API调用"""
        print(f"\n📝 [RateLimit] 记录应用级API调用:")
        print(f"   - 方法: record_app_call")
        print(f"   - 记录开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
        
        current_time = time.time()
        print(f"   - 当前时间戳: {current_time} (类型: {type(current_time)})")
        print(f"   - 当前时间格式化: {datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S.%f')}")
        print(f"   - 应用级调用记录 (添加前): {self.app_call_times}")
        print(f"   - 应用级调用记录长度 (添加前): {len(self.app_call_times)}")
        
        self.app_call_times.append(current_time)
        
        print(f"   - 应用级调用记录 (添加后): {self.app_call_times}")
        print(f"   - 应用级调用记录长度 (添加后): {len(self.app_call_times)}")
        print(f"   - 新增记录: {current_time} ({datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S.%f')})")
        print(f"   - 记录完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
    
    def record_doc_call(self, doc_id: str):
        """记录文档级API调用"""
        print(f"\n📝 [RateLimit] 记录文档级API调用:")
        print(f"   - 方法: record_doc_call")
        print(f"   - doc_id 参数: '{doc_id}' (类型: {type(doc_id)}, 长度: {len(doc_id)})")
        print(f"   - 记录开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
        
        current_time = time.time()
        print(f"   - 当前时间戳: {current_time} (类型: {type(current_time)})")
        print(f"   - 当前时间格式化: {datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S.%f')}")
        print(f"   - 文档调用记录字典: {self.doc_call_times}")
        print(f"   - 文档调用记录字典长度: {len(self.doc_call_times)}")
        print(f"   - doc_id 是否在记录中: {doc_id in self.doc_call_times}")
        
        if doc_id not in self.doc_call_times:
            print(f"   - 🆕 文档ID不存在，创建新记录")
            self.doc_call_times[doc_id] = []
            print(f"   - 创建后文档调用记录: {self.doc_call_times[doc_id]}")
        else:
            print(f"   - ✅ 文档ID已存在")
        
        print(f"   - 当前文档调用记录 (添加前): {self.doc_call_times[doc_id]}")
        print(f"   - 当前文档调用记录长度 (添加前): {len(self.doc_call_times[doc_id])}")
        
        self.doc_call_times[doc_id].append(current_time)
        
        print(f"   - 当前文档调用记录 (添加后): {self.doc_call_times[doc_id]}")
        print(f"   - 当前文档调用记录长度 (添加后): {len(self.doc_call_times[doc_id])}")
        print(f"   - 新增记录: {current_time} ({datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S.%f')})")
        print(f"   - 记录完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
    
    def wait_for_app_call(self):
        """等待直到可以进行应用级API调用"""
        print(f"\n⏳ [RateLimit] 等待应用级API调用权限:")
        print(f"   - 方法: wait_for_app_call")
        print(f"   - 等待开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
        
        wait_count = 0
        total_wait_time = 0.0
        
        while not self.can_make_app_call():
            wait_count += 1
            current_time = time.time()
            
            print(f"\n   等待循环 {wait_count}:")
            print(f"     - 当前时间: {datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S.%f')}")
            print(f"     - 应用级调用记录: {self.app_call_times}")
            print(f"     - 应用级调用记录长度: {len(self.app_call_times)}")
            
            if self.app_call_times:
                oldest_call = self.app_call_times[0]
                time_since_oldest = current_time - oldest_call
                sleep_time = 1.0 - time_since_oldest
                
                print(f"     - 最早调用时间: {oldest_call} ({datetime.fromtimestamp(oldest_call).strftime('%Y-%m-%d %H:%M:%S.%f')})")
                print(f"     - 距离最早调用时间: {time_since_oldest:.6f} 秒")
                print(f"     - 计算等待时间: 1.0 - {time_since_oldest:.6f} = {sleep_time:.6f} 秒")
            else:
                sleep_time = 0.1
                print(f"     - 无调用记录，使用默认等待时间: {sleep_time} 秒")
            
            if sleep_time > 0:
                print(f"     - 实际等待时间: {sleep_time:.6f} 秒")
                print(f"     - 等待开始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
                print(f"⏳ [RateLimit] 应用级频率限制，等待 {sleep_time:.2f} 秒")
                self.logger.debug(f"应用级频率限制，等待 {sleep_time:.2f} 秒")
                
                time.sleep(sleep_time)
                total_wait_time += sleep_time
                
                print(f"     - 等待结束: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
            else:
                print(f"     - 无需等待 (sleep_time <= 0)")
                time.sleep(0.01)  # 短暂休眠避免忙等待
        
        print(f"\n✅ [RateLimit] 应用级API调用权限获得:")
        print(f"   - 总等待次数: {wait_count}")
        print(f"   - 总等待时间: {total_wait_time:.6f} 秒")
        print(f"   - 等待完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
    
    def wait_for_doc_call(self, doc_id: str):
        """等待直到可以进行文档级API调用"""
        print(f"\n⏳ [RateLimit] 等待文档级API调用权限:")
        print(f"   - 方法: wait_for_doc_call")
        print(f"   - doc_id 参数: '{doc_id}' (类型: {type(doc_id)}, 长度: {len(doc_id)})")
        print(f"   - 等待开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
        
        wait_count = 0
        total_wait_time = 0.0
        
        while not self.can_make_doc_call(doc_id):
            wait_count += 1
            current_time = time.time()
            
            print(f"\n   等待循环 {wait_count}:")
            print(f"     - 当前时间: {datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S.%f')}")
            print(f"     - 文档调用记录字典: {self.doc_call_times}")
            print(f"     - doc_id 是否在记录中: {doc_id in self.doc_call_times}")
            
            if doc_id in self.doc_call_times and self.doc_call_times[doc_id]:
                doc_calls = self.doc_call_times[doc_id]
                oldest_call = doc_calls[0]
                time_since_oldest = current_time - oldest_call
                sleep_time = 1.0 - time_since_oldest
                
                print(f"     - 文档调用记录: {doc_calls}")
                print(f"     - 文档调用记录长度: {len(doc_calls)}")
                print(f"     - 最早调用时间: {oldest_call} ({datetime.fromtimestamp(oldest_call).strftime('%Y-%m-%d %H:%M:%S.%f')})")
                print(f"     - 距离最早调用时间: {time_since_oldest:.6f} 秒")
                print(f"     - 计算等待时间: 1.0 - {time_since_oldest:.6f} = {sleep_time:.6f} 秒")
                
                if sleep_time > 0:
                    print(f"     - 实际等待时间: {sleep_time:.6f} 秒")
                    print(f"     - 等待开始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
                    print(f"⏳ [RateLimit] 文档级频率限制，等待 {sleep_time:.2f} 秒")
                    self.logger.debug(f"文档级频率限制，等待 {sleep_time:.2f} 秒")
                    
                    time.sleep(sleep_time)
                    total_wait_time += sleep_time
                    
                    print(f"     - 等待结束: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
                else:
                    print(f"     - 无需等待 (sleep_time <= 0)")
                    time.sleep(0.01)  # 短暂休眠避免忙等待
            else:
                print(f"     - 无文档调用记录，使用默认等待时间: 0.1 秒")
                time.sleep(0.1)
                total_wait_time += 0.1
        
        print(f"\n✅ [RateLimit] 文档级API调用权限获得:")
        print(f"   - 总等待次数: {wait_count}")
        print(f"   - 总等待时间: {total_wait_time:.6f} 秒")
        print(f"   - 等待完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
    
    def exponential_backoff(self, attempt: int, base_delay: float = None) -> float:
        """指数退避算法"""
        print(f"\n📈 [RateLimit] 计算指数退避延迟:")
        print(f"   - 方法: exponential_backoff")
        print(f"   - attempt 参数: {attempt} (类型: {type(attempt)})")
        print(f"   - base_delay 参数: {base_delay} (类型: {type(base_delay)})")
        print(f"   - 计算开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
        
        if base_delay is None:
            base_delay = self.base_delay
            print(f"   - 使用默认基础延迟: {base_delay} 秒")
        else:
            print(f"   - 使用传入基础延迟: {base_delay} 秒")
        
        print(f"   - 实例配置:")
        print(f"     * self.base_delay: {self.base_delay} 秒")
        print(f"     * self.max_delay: {self.max_delay} 秒")
        print(f"     * 最终使用的 base_delay: {base_delay} 秒")
        
        # 指数退避：delay = base_delay * (2 ^ attempt) + random_jitter
        print(f"\n🧮 [RateLimit] 指数退避计算过程:")
        power_result = 2 ** attempt
        print(f"   - 指数计算: 2 ^ {attempt} = {power_result}")
        
        delay = base_delay * power_result
        print(f"   - 基础延迟计算: {base_delay} * {power_result} = {delay} 秒")
        
        # 添加随机抖动，避免雷群效应
        jitter_range = delay * 0.1
        print(f"   - 抖动范围计算: {delay} * 0.1 = {jitter_range}")
        
        jitter = random.uniform(0, jitter_range)
        print(f"   - 随机抖动值: random.uniform(0, {jitter_range}) = {jitter} 秒")
        
        delay_with_jitter = delay + jitter
        print(f"   - 加抖动延迟: {delay} + {jitter} = {delay_with_jitter} 秒")
        
        total_delay = min(delay_with_jitter, self.max_delay)
        print(f"   - 最终延迟: min({delay_with_jitter}, {self.max_delay}) = {total_delay} 秒")
        
        print(f"\n📊 [RateLimit] 指数退避结果:")
        print(f"   - 尝试次数: {attempt + 1}")
        print(f"   - 基础延迟: {base_delay} 秒")
        print(f"   - 指数倍数: {power_result}")
        print(f"   - 基础计算延迟: {delay} 秒")
        print(f"   - 随机抖动: {jitter} 秒")
        print(f"   - 最大允许延迟: {self.max_delay} 秒")
        print(f"   - 最终延迟: {total_delay} 秒")
        print(f"   - 延迟类型: {type(total_delay)}")
        print(f"   - 计算完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
        
        print(f"⏳ [RateLimit] 指数退避延迟: {total_delay:.2f} 秒 (尝试次数: {attempt + 1})")
        self.logger.info(f"指数退避延迟: {total_delay:.2f} 秒 (尝试次数: {attempt + 1})")
        return total_delay

try:
    import requests
except ImportError:
    requests = None

class CloudSyncManager:
    """
    云端同步管理器
    支持Google Sheets和飞书文档的数据同步
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        print(f"\n🚀 [CloudSync] 初始化云端同步管理器:")
        print(f"   - 类: CloudSyncManager")
        print(f"   - 方法: __init__")
        print(f"   - config 参数: {config} (类型: {type(config)})")
        print(f"   - config 是否为 None: {config is None}")
        print(f"   - 初始化开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
        print(f"   - 当前工作目录: {os.getcwd()}")
        print(f"   - 进程ID: {os.getpid() if 'os' in globals() else 'N/A'}")
        print(f"   - 线程ID: {threading.current_thread().ident if 'threading' in globals() else 'N/A'}")
        
        print(f"\n📋 [CloudSync] 处理配置参数...")
        if config is None:
            print(f"   - config 为 None，使用空字典")
            self.config = {}
        else:
            print(f"   - config 不为 None，使用传入配置")
            self.config = config
        
        print(f"   - 设置 self.config: {self.config} (类型: {type(self.config)})")
        print(f"   - 配置键数量: {len(self.config) if isinstance(self.config, dict) else 'N/A'}")
        print(f"   - 配置键列表: {list(self.config.keys()) if isinstance(self.config, dict) else 'N/A'}")
        
        print(f"\n📝 [CloudSync] 设置日志记录器...")
        self.logger = logging.getLogger('CloudSync')
        print(f"   - 日志记录器类型: {type(self.logger)}")
        print(f"   - 日志记录器名称: {self.logger.name if hasattr(self.logger, 'name') else 'N/A'}")
        print(f"   - 日志记录器级别: {self.logger.level if hasattr(self.logger, 'level') else 'N/A'}")
        print(f"   - 日志记录器处理器数量: {len(self.logger.handlers) if hasattr(self.logger, 'handlers') else 'N/A'}")
        
        print(f"\n🔗 [CloudSync] 初始化Google客户端...")
        self.google_client = None
        print(f"   - 设置 self.google_client: {self.google_client} (类型: {type(self.google_client)})")
        
        print(f"\n🚁 [CloudSync] 提取飞书配置...")
        feishu_config_raw = self.config.get('feishu', {})
        print(f"   - 原始飞书配置: {feishu_config_raw} (类型: {type(feishu_config_raw)})")
        print(f"   - 飞书配置键: {list(feishu_config_raw.keys()) if isinstance(feishu_config_raw, dict) else 'N/A'}")
        print(f"   - 飞书配置长度: {len(feishu_config_raw) if isinstance(feishu_config_raw, dict) else 'N/A'}")
        
        self.feishu_config = feishu_config_raw
        print(f"   - 设置 self.feishu_config: {self.feishu_config}")
        
        if isinstance(self.feishu_config, dict):
            print(f"   - 飞书配置详情:")
            for key, value in self.feishu_config.items():
                if 'secret' in key.lower() or 'token' in key.lower():
                    print(f"     * {key}: '{str(value)[:10]}...' (长度: {len(str(value))})")
                else:
                    print(f"     * {key}: '{value}' (类型: {type(value)})")
        
        print(f"\n⏱️ [CloudSync] 初始化频率限制器...")
        self.rate_limiter = FeishuRateLimiter()  # 添加频率限制器
        print(f"   - 频率限制器类型: {type(self.rate_limiter)}")
        print(f"   - 频率限制器配置:")
        print(f"     * 最大应用级调用数/秒: {self.rate_limiter.max_app_calls_per_second}")
        print(f"     * 最大文档级调用数/秒: {self.rate_limiter.max_doc_calls_per_second}")
        print(f"     * 基础延迟: {self.rate_limiter.base_delay} 秒")
        print(f"     * 最大延迟: {self.rate_limiter.max_delay} 秒")
        print(f"     * 应用调用记录: {self.rate_limiter.app_call_times}")
        print(f"     * 文档调用记录: {self.rate_limiter.doc_call_times}")
        
        print(f"\n🎉 [CloudSync] 云端同步管理器初始化完成:")
        print(f"   - 配置状态: 已设置 ({len(self.config)} 个配置项)")
        print(f"   - 日志记录器: 已设置 (名称: {self.logger.name})")
        print(f"   - Google客户端: 已初始化为 None")
        print(f"   - 飞书配置: 已设置 ({len(self.feishu_config)} 个配置项)")
        print(f"   - 频率限制器: 已初始化")
        print(f"   - 初始化完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
        print(f"   - 实例ID: {id(self)}")
        print(f"   - 实例类型: {type(self)}")
        print(f"   - 实例属性: {[attr for attr in dir(self) if not attr.startswith('_')]}")
        print(f"="*100)
        
    def setup_google_sheets(self, credentials_file: str, scopes: List[str] = None) -> bool:
        """
        设置Google Sheets连接
        
        Args:
            credentials_file: Google服务账号凭证文件路径
            scopes: API权限范围
            
        Returns:
            是否设置成功
        """
        print(f"\n📊 [CloudSync] 设置Google Sheets连接:")
        print(f"   - 方法: setup_google_sheets")
        print(f"   - credentials_file 参数: '{credentials_file}' (类型: {type(credentials_file)}, 长度: {len(credentials_file)})")
        print(f"   - scopes 参数: {scopes} (类型: {type(scopes)})")
        print(f"   - scopes 是否为 None: {scopes is None}")
        print(f"   - 设置开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
        print(f"   - 凭证文件绝对路径: {os.path.abspath(credentials_file)}")
        print(f"   - 凭证文件是否存在: {os.path.exists(credentials_file)}")
        
        print(f"\n🔍 [CloudSync] 检查依赖模块...")
        print(f"   - gspread 模块: {gspread} (类型: {type(gspread)})")
        print(f"   - gspread 是否可用: {gspread is not None}")
        print(f"   - Credentials 模块: {Credentials} (类型: {type(Credentials)})")
        print(f"   - Credentials 是否可用: {Credentials is not None}")
        
        if not gspread or not Credentials:
            print(f"❌ [CloudSync] 依赖检查失败")
            print(f"   - gspread 可用: {gspread is not None}")
            print(f"   - Credentials 可用: {Credentials is not None}")
            print(f"   - 错误消息: Google Sheets依赖未安装")
            print(f"   - 建议操作: pip install gspread google-auth")
            self.logger.error("Google Sheets依赖未安装，请运行: pip install gspread google-auth")
            return False
        
        print(f"✅ [CloudSync] 依赖检查通过")
        
        try:
            print(f"\n🔧 [CloudSync] 处理权限范围...")
            if scopes is None:
                print(f"   - scopes 为 None，使用默认权限范围")
                scopes = [
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive'
                ]
                print(f"   - 默认权限范围: {scopes}")
            else:
                print(f"   - 使用传入的权限范围: {scopes}")
            
            print(f"   - 最终权限范围:")
            for i, scope in enumerate(scopes, 1):
                print(f"     {i}. {scope}")
            print(f"   - 权限范围数量: {len(scopes)}")
            
            print(f"\n🔑 [CloudSync] 加载服务账号凭证...")
            print(f"   - 凭证文件: {credentials_file}")
            print(f"   - 权限范围: {scopes}")
            print(f"   - 加载开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
            
            credentials = Credentials.from_service_account_file(
                credentials_file, scopes=scopes
            )
            
            print(f"   - 凭证加载成功")
            print(f"   - 凭证类型: {type(credentials)}")
            print(f"   - 凭证有效: {credentials.valid if hasattr(credentials, 'valid') else 'N/A'}")
            print(f"   - 凭证过期: {credentials.expired if hasattr(credentials, 'expired') else 'N/A'}")
            print(f"   - 加载完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
            
            print(f"\n🔗 [CloudSync] 授权Google客户端...")
            print(f"   - 授权开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
            
            self.google_client = gspread.authorize(credentials)
            
            print(f"   - 授权成功")
            print(f"   - Google客户端类型: {type(self.google_client)}")
            print(f"   - Google客户端: {self.google_client}")
            print(f"   - 授权完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
            
            print(f"\n✅ [CloudSync] Google Sheets设置成功:")
            print(f"   - 凭证文件: {credentials_file}")
            print(f"   - 权限范围数量: {len(scopes)}")
            print(f"   - 客户端状态: 已授权")
            print(f"   - 设置完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
            
            self.logger.info("Google Sheets连接设置成功")
            return True
            
        except Exception as e:
            print(f"\n❌ [CloudSync] Google Sheets设置失败:")
            print(f"   - 异常类型: {type(e).__name__}")
            print(f"   - 异常消息: {str(e)}")
            print(f"   - 异常详情: {repr(e)}")
            print(f"   - 凭证文件: {credentials_file}")
            print(f"   - 权限范围: {scopes}")
            print(f"   - 失败时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
            
            if hasattr(e, '__traceback__'):
                import traceback
                print(f"   - 堆栈跟踪:")
                traceback.print_exc()
            
            self.logger.error(f"Google Sheets设置失败: {e}")
            return False
    
    def sync_to_google_sheets(self, data: List[Dict[str, Any]], 
                             spreadsheet_id: str, 
                             worksheet_name: str = None) -> bool:
        """
        同步数据到Google Sheets
        
        Args:
            data: 要同步的数据
            spreadsheet_id: Google表格ID
            worksheet_name: 工作表名称
            
        Returns:
            是否同步成功
        """
        print(f"\n📊 [CloudSync] 同步数据到Google Sheets:")
        print(f"   - 方法: sync_to_google_sheets")
        print(f"   - data 参数: {type(data)} (长度: {len(data) if data else 0})")
        print(f"   - spreadsheet_id 参数: '{spreadsheet_id}' (类型: {type(spreadsheet_id)}, 长度: {len(spreadsheet_id)})")
        print(f"   - worksheet_name 参数: '{worksheet_name}' (类型: {type(worksheet_name)})")
        print(f"   - worksheet_name 是否为 None: {worksheet_name is None}")
        print(f"   - 同步开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
        
        if data:
            print(f"   - 数据示例 (前3条):")
            for i, item in enumerate(data[:3], 1):
                print(f"     {i}. {item} (类型: {type(item)})")
        else:
            print(f"   - 数据为空或None")
        
        print(f"\n🔍 [CloudSync] 检查Google客户端状态...")
        print(f"   - self.google_client: {self.google_client} (类型: {type(self.google_client)})")
        print(f"   - Google客户端是否已初始化: {self.google_client is not None}")
        
        if not self.google_client:
            print(f"❌ [CloudSync] Google客户端检查失败")
            print(f"   - 错误: Google Sheets未初始化")
            print(f"   - 建议: 先调用 setup_google_sheets() 方法")
            print(f"   - 失败时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
            self.logger.error("Google Sheets未初始化")
            return False
        
        print(f"✅ [CloudSync] Google客户端检查通过")
        
        try:
            print(f"\n📋 [CloudSync] 打开Google表格...")
            print(f"   - 表格ID: {spreadsheet_id}")
            print(f"   - 打开开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
            
            # 打开表格
            spreadsheet = self.google_client.open_by_key(spreadsheet_id)
            
            print(f"   - 表格打开成功")
            print(f"   - 表格对象: {spreadsheet} (类型: {type(spreadsheet)})")
            print(f"   - 表格标题: {spreadsheet.title if hasattr(spreadsheet, 'title') else 'N/A'}")
            print(f"   - 打开完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
            
            print(f"\n📄 [CloudSync] 获取或创建工作表...")
            print(f"   - 工作表名称: '{worksheet_name}'")
            print(f"   - 是否指定工作表名称: {worksheet_name is not None}")
            
            # 获取或创建工作表
            if worksheet_name:
                print(f"   - 尝试获取指定工作表: '{worksheet_name}'")
                try:
                    worksheet = spreadsheet.worksheet(worksheet_name)
                    print(f"   - 工作表获取成功: '{worksheet_name}'")
                    print(f"   - 工作表对象: {worksheet} (类型: {type(worksheet)})")
                except Exception as worksheet_error:
                    print(f"   - 工作表不存在，创建新工作表")
                    print(f"   - 获取失败原因: {worksheet_error}")
                    print(f"   - 创建参数: title='{worksheet_name}', rows=1000, cols=20")
                    
                    worksheet = spreadsheet.add_worksheet(
                        title=worksheet_name, rows=1000, cols=20
                    )
                    
                    print(f"   - 工作表创建成功: '{worksheet_name}'")
                    print(f"   - 新工作表对象: {worksheet} (类型: {type(worksheet)})")
            else:
                print(f"   - 使用默认工作表 (sheet1)")
                worksheet = spreadsheet.sheet1
                print(f"   - 默认工作表获取成功")
                print(f"   - 工作表对象: {worksheet} (类型: {type(worksheet)})")
            
            print(f"   - 最终工作表: {worksheet}")
            print(f"   - 工作表标题: {worksheet.title if hasattr(worksheet, 'title') else 'N/A'}")
            
            print(f"\n🧹 [CloudSync] 清空现有数据...")
            print(f"   - 清空开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
            
            # 清空现有数据
            worksheet.clear()
            
            print(f"   - 数据清空成功")
            print(f"   - 清空完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
            
            print(f"\n📊 [CloudSync] 检查数据状态...")
            print(f"   - 数据是否为空: {not data}")
            print(f"   - 数据长度: {len(data) if data else 0}")
            
            if not data:
                print(f"⚠️ [CloudSync] 没有数据需要同步")
                print(f"   - 数据状态: 空")
                print(f"   - 处理结果: 返回成功 (无数据同步)")
                print(f"   - 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
                self.logger.warning("没有数据需要同步")
                return True
            
            print(f"✅ [CloudSync] 数据检查通过，开始处理")
            
            print(f"\n📋 [CloudSync] 准备表头...")
            # 准备表头
            headers = [
                '序号', '用户名', '推文内容', '发布时间', '点赞数', 
                '评论数', '转发数', '链接', '标签', '筛选状态'
            ]
            
            print(f"   - 表头列表: {headers}")
            print(f"   - 表头数量: {len(headers)}")
            print(f"   - 表头类型: {type(headers)}")
            
            print(f"\n📝 [CloudSync] 准备数据行...")
            print(f"   - 数据处理开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
            
            # 准备数据行
            rows = [headers]
            print(f"   - 初始化行数据，包含表头: {len(rows)} 行")
            
            for i, tweet in enumerate(data, 1):
                row = [
                    i,
                    tweet.get('username', ''),
                    tweet.get('content', ''),
                    tweet.get('timestamp', ''),
                    tweet.get('likes', 0),
                    tweet.get('comments', 0),
                    tweet.get('retweets', 0),
                    tweet.get('link', ''),
                    ', '.join(tweet.get('tags', [])),
                    tweet.get('filter_status', '')
                ]
                rows.append(row)
                
                if i <= 3:  # 只打印前3行的详细信息
                    print(f"   - 第 {i} 行数据:")
                    print(f"     * 原始推文: {tweet}")
                    print(f"     * 处理后行: {row}")
                    print(f"     * 行长度: {len(row)}")
            
            print(f"   - 数据行处理完成")
            print(f"   - 总行数 (含表头): {len(rows)}")
            print(f"   - 数据行数: {len(rows) - 1}")
            print(f"   - 数据处理完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
            
            print(f"\n📤 [CloudSync] 批量更新数据到工作表...")
            print(f"   - 更新范围: A1")
            print(f"   - 更新行数: {len(rows)}")
            print(f"   - 更新列数: {len(headers)}")
            print(f"   - 更新开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
            
            # 批量更新数据
            worksheet.update('A1', rows)
            
            print(f"   - 数据更新成功")
            print(f"   - 更新完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
            
            print(f"\n🕒 [CloudSync] 添加同步时间戳...")
            # 添加同步时间戳
            timestamp_cell = f"A{len(rows) + 2}"
            timestamp_value = f"最后同步时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            print(f"   - 时间戳单元格: {timestamp_cell}")
            print(f"   - 时间戳内容: '{timestamp_value}'")
            print(f"   - 时间戳添加开始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
            
            worksheet.update(timestamp_cell, timestamp_value)
            
            print(f"   - 时间戳添加成功")
            print(f"   - 时间戳添加完成: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
            
            print(f"\n✅ [CloudSync] Google Sheets同步成功:")
            print(f"   - 表格ID: {spreadsheet_id}")
            print(f"   - 工作表: {worksheet.title if hasattr(worksheet, 'title') else worksheet_name or 'sheet1'}")
            print(f"   - 同步数据量: {len(data)} 条")
            print(f"   - 总行数: {len(rows)} 行 (含表头)")
            print(f"   - 同步完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
            
            self.logger.info(f"成功同步 {len(data)} 条数据到Google Sheets")
            return True
            
        except Exception as e:
            print(f"\n❌ [CloudSync] Google Sheets同步失败:")
            print(f"   - 异常类型: {type(e).__name__}")
            print(f"   - 异常消息: {str(e)}")
            print(f"   - 异常详情: {repr(e)}")
            print(f"   - 表格ID: {spreadsheet_id}")
            print(f"   - 工作表名称: {worksheet_name}")
            print(f"   - 数据长度: {len(data) if data else 0}")
            print(f"   - 失败时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
            
            if hasattr(e, '__traceback__'):
                import traceback
                print(f"   - 堆栈跟踪:")
                traceback.print_exc()
            
            self.logger.error(f"Google Sheets同步失败: {e}")
            return False
    
    def setup_feishu(self, app_id: str, app_secret: str) -> bool:
        """
        设置飞书应用配置
        
        Args:
            app_id: 飞书应用ID
            app_secret: 飞书应用密钥
            
        Returns:
            是否设置成功
        """
        print(f"\n🚁 [CloudSync] 设置飞书应用配置:")
        print(f"   - 方法: setup_feishu")
        print(f"   - app_id 参数: '{app_id}' (类型: {type(app_id)}, 长度: {len(app_id)})")
        print(f"   - app_secret 参数: '{app_secret[:10]}...' (类型: {type(app_secret)}, 长度: {len(app_secret)})")
        print(f"   - 设置开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
        
        print(f"\n🔍 [CloudSync] 检查requests依赖...")
        print(f"   - requests 模块: {requests} (类型: {type(requests)})")
        print(f"   - requests 是否可用: {requests is not None}")
        
        if not requests:
            print(f"❌ [CloudSync] requests依赖检查失败")
            print(f"   - requests 可用: {requests is not None}")
            print(f"   - 错误消息: requests依赖未安装")
            print(f"   - 建议操作: pip install requests")
            print(f"   - 失败时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
            self.logger.error("requests依赖未安装，请运行: pip install requests")
            return False
        
        print(f"✅ [CloudSync] requests依赖检查通过")
        
        print(f"\n🔧 [CloudSync] 构建飞书配置...")
        print(f"   - 原始 self.feishu_config: {self.feishu_config}")
        
        new_config = {
            'app_id': app_id,
            'app_secret': app_secret,
            'base_url': 'https://open.feishu.cn/open-apis'
        }
        
        print(f"   - 新配置构建:")
        print(f"     * app_id: '{new_config['app_id']}' (长度: {len(new_config['app_id'])})")
        print(f"     * app_secret: '{new_config['app_secret'][:10]}...' (长度: {len(new_config['app_secret'])})")
        print(f"     * base_url: '{new_config['base_url']}' (长度: {len(new_config['base_url'])})")
        print(f"   - 新配置键数量: {len(new_config)}")
        print(f"   - 新配置类型: {type(new_config)}")
        
        print(f"\n💾 [CloudSync] 保存飞书配置...")
        self.feishu_config = new_config
        
        print(f"   - 配置保存成功")
        print(f"   - 更新后 self.feishu_config: {self.feishu_config}")
        print(f"   - 配置验证:")
        print(f"     * app_id 存在: {bool(self.feishu_config.get('app_id'))}")
        print(f"     * app_secret 存在: {bool(self.feishu_config.get('app_secret'))}")
        print(f"     * base_url 存在: {bool(self.feishu_config.get('base_url'))}")
        print(f"     * 配置完整: {all([self.feishu_config.get('app_id'), self.feishu_config.get('app_secret'), self.feishu_config.get('base_url')])}")
        
        print(f"\n✅ [CloudSync] 飞书配置设置成功:")
        print(f"   - App ID: '{self.feishu_config['app_id']}'")
        print(f"   - App Secret: 已设置 (长度: {len(self.feishu_config['app_secret'])})")
        print(f"   - Base URL: '{self.feishu_config['base_url']}'")
        print(f"   - 设置完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
        
        self.logger.info("飞书配置设置成功")
        return True
    
    def get_feishu_access_token(self, max_retries: int = 3) -> Optional[str]:
        """
        获取飞书访问令牌（带频率限制和重试机制）
        
        Args:
            max_retries: 最大重试次数
            
        Returns:
            访问令牌或None
        """
        print(f"\n" + "="*100)
        print(f"🔑 [CloudSync] 开始获取飞书访问令牌 - 详细流程")
        print(f"📋 [CloudSync] 函数调用参数详情:")
        print(f"   - 函数名: get_feishu_access_token")
        print(f"   - max_retries 参数: {max_retries} (类型: {type(max_retries)})")
        print(f"   - self.feishu_config 状态: {type(self.feishu_config)}")
        print(f"   - self.feishu_config 内容: {json.dumps(self.feishu_config, indent=4, ensure_ascii=False)}")
        print(f"   - self.rate_limiter 状态: {type(self.rate_limiter)}")
        print(f"   - 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
        print(f"   - 进程ID: {os.getpid() if 'os' in globals() else 'N/A'}")
        print(f"   - 线程ID: {threading.current_thread().ident if 'threading' in globals() else 'N/A'}")
        
        if not self.feishu_config.get('app_id'):
            print(f"❌ [CloudSync] 飞书配置检查失败")
            print(f"   - app_id 存在: {bool(self.feishu_config.get('app_id'))}")
            print(f"   - app_id 值: '{self.feishu_config.get('app_id', 'N/A')}'")
            print(f"   - app_secret 存在: {bool(self.feishu_config.get('app_secret'))}")
            print(f"   - base_url 存在: {bool(self.feishu_config.get('base_url'))}")
            print(f"   - 完整配置: {self.feishu_config}")
            self.logger.error("飞书配置未设置")
            return None
        
        print(f"✅ [CloudSync] 飞书配置检查通过")
        print(f"   - App ID: '{self.feishu_config['app_id']}' (长度: {len(self.feishu_config['app_id'])})")
        print(f"   - App Secret: '{self.feishu_config['app_secret'][:10]}...' (长度: {len(self.feishu_config['app_secret'])})")
        print(f"   - Base URL: '{self.feishu_config['base_url']}' (长度: {len(self.feishu_config['base_url'])})")
        print(f"   - 最大重试次数: {max_retries}")
        print(f"   - 配置完整性: {all([self.feishu_config.get('app_id'), self.feishu_config.get('app_secret'), self.feishu_config.get('base_url')])}")
        
        print(f"\n🔄 [CloudSync] 开始令牌获取重试循环")
        print(f"   - 重试范围: range({max_retries}) = {list(range(max_retries))}")
        print(f"   - 循环类型: for attempt in range(max_retries)")
        
        for attempt in range(max_retries):
            try:
                print(f"\n" + "-"*80)
                print(f"🔄 [CloudSync] 开始第 {attempt + 1}/{max_retries} 次尝试")
                print(f"📊 [CloudSync] 尝试详细信息:")
                print(f"   - attempt 变量: {attempt} (类型: {type(attempt)})")
                print(f"   - 尝试编号: {attempt + 1}")
                print(f"   - 总尝试次数: {max_retries}")
                print(f"   - 剩余尝试次数: {max_retries - attempt - 1}")
                print(f"   - 是否最后一次尝试: {attempt == max_retries - 1}")
                print(f"   - 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
                
                # 应用频率限制控制
                print(f"\n⏱️ [CloudSync] 应用级频率限制检查详情")
                print(f"   - rate_limiter 对象: {self.rate_limiter}")
                print(f"   - app_call_times 列表: {self.rate_limiter.app_call_times}")
                print(f"   - 当前应用调用记录数: {len(self.rate_limiter.app_call_times)}")
                print(f"   - 应用级最大调用数: {self.rate_limiter.max_app_calls_per_second}")
                print(f"   - 可以调用: {self.rate_limiter.can_make_app_call()}")
                print(f"   - 当前时间戳: {time.time()}")
                
                if self.rate_limiter.app_call_times:
                    print(f"   - 最早调用时间: {self.rate_limiter.app_call_times[0]}")
                    print(f"   - 最晚调用时间: {self.rate_limiter.app_call_times[-1]}")
                    print(f"   - 时间差: {time.time() - self.rate_limiter.app_call_times[0]:.3f} 秒")
                
                self.rate_limiter.wait_for_app_call()
                print(f"   - ✅ 频率限制检查通过")
                print(f"   - 检查后调用记录数: {len(self.rate_limiter.app_call_times)}")
                
                print(f"\n🔧 [CloudSync] 构建API请求参数")
                base_url = self.feishu_config['base_url']
                endpoint = "/auth/v3/tenant_access_token/internal"
                url = f"{base_url}{endpoint}"
                
                print(f"   - base_url: '{base_url}' (长度: {len(base_url)})")
                print(f"   - endpoint: '{endpoint}' (长度: {len(endpoint)})")
                print(f"   - 完整URL: '{url}' (长度: {len(url)})")
                print(f"   - URL构建方式: f\"{base_url}{endpoint}\"")
                
                headers = {
                    'Content-Type': 'application/json'
                }
                print(f"   - 请求头构建: {json.dumps(headers, indent=6, ensure_ascii=False)}")
                print(f"   - Content-Type: {headers['Content-Type']}")
                
                app_id = self.feishu_config['app_id']
                app_secret = self.feishu_config['app_secret']
                payload = {
                    'app_id': app_id,
                    'app_secret': app_secret
                }
                
                print(f"   - 载荷构建详情:")
                print(f"     - app_id 来源: self.feishu_config['app_id']")
                print(f"     - app_id 值: '{app_id}' (长度: {len(app_id)})")
                print(f"     - app_secret 来源: self.feishu_config['app_secret']")
                print(f"     - app_secret 长度: {len(app_secret)}")
                print(f"     - app_secret 前缀: '{app_secret[:10]}...'")
                print(f"     - 载荷字典: {json.dumps({'app_id': app_id, 'app_secret': '***'}, indent=6, ensure_ascii=False)}")
                print(f"     - 载荷大小: {len(str(payload))} 字符")
                
                print(f"\n🌐 [CloudSync] 发送令牌请求详情 (尝试 {attempt + 1}/{max_retries})")
                print(f"   - 请求时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
                print(f"   - 请求URL: '{url}'")
                print(f"   - 请求方法: POST")
                print(f"   - 请求头: {json.dumps(headers, indent=4, ensure_ascii=False)}")
                print(f"   - 请求载荷: {json.dumps({'app_id': payload['app_id'], 'app_secret': '***'}, indent=4, ensure_ascii=False)}")
                print(f"   - 超时设置: 30秒")
                print(f"   - requests 模块: {requests}")
                print(f"   - requests.post 方法: {requests.post}")
                
                # 记录API调用
                print(f"\n📝 [CloudSync] 记录API调用")
                print(f"   - 调用前记录数: {len(self.rate_limiter.app_call_times)}")
                print(f"   - 调用前记录列表: {self.rate_limiter.app_call_times}")
                call_time = time.time()
                print(f"   - 当前时间戳: {call_time}")
                
                self.rate_limiter.record_app_call()
                
                print(f"   - 调用后记录数: {len(self.rate_limiter.app_call_times)}")
                print(f"   - 调用后记录列表: {self.rate_limiter.app_call_times}")
                print(f"   - 记录成功: {call_time in self.rate_limiter.app_call_times}")
                
                print(f"\n🚀 [CloudSync] 执行HTTP请求")
                print(f"   - 请求参数详情:")
                print(f"     - url: '{url}'")
                print(f"     - headers: {headers}")
                print(f"     - json: {json.dumps({'app_id': payload['app_id'], 'app_secret': '***'}, ensure_ascii=False)}")
                print(f"     - timeout: 30")
                print(f"   - 请求执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
                
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                
                print(f"\n📊 [CloudSync] HTTP响应接收完成")
                print(f"   - 响应接收时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
                print(f"   - 响应对象类型: {type(response)}")
                print(f"   - 响应状态码: {response.status_code} (类型: {type(response.status_code)})")
                print(f"   - 响应状态文本: '{response.reason}'")
                print(f"   - 响应URL: '{response.url}'")
                print(f"   - 响应编码: '{response.encoding}'")
                print(f"   - 响应头数量: {len(response.headers)}")
                print(f"   - 响应头详情: {json.dumps(dict(response.headers), indent=4, ensure_ascii=False)}")
                print(f"   - 响应内容长度: {len(response.text)} 字符")
                print(f"   - 响应内容类型: {type(response.text)}")
                print(f"   - 响应原始内容: '{response.text}'")
                print(f"   - 响应是否成功: {response.ok}")
                print(f"   - 响应历史: {response.history}")
                
                # 处理频率限制错误
                if response.status_code == 400:
                    result = response.json()
                    if result.get('code') == 99991400:  # 应用频率限制
                        print(f"⚠️ [CloudSync] 应用频率限制触发，使用指数退避")
                        self.logger.warning(f"⚠️ 应用频率限制触发，使用指数退避")
                        delay = self.rate_limiter.exponential_backoff(attempt)
                        time.sleep(delay)
                        continue
                elif response.status_code == 429:
                    print(f"⚠️ [CloudSync] 服务器返回429，使用指数退避")
                    self.logger.warning(f"⚠️ 服务器返回429，使用指数退避")
                    delay = self.rate_limiter.exponential_backoff(attempt)
                    time.sleep(delay)
                    continue
                
                print(f"\n🔍 [CloudSync] 检查HTTP状态")
                print(f"   - 状态码检查: {response.status_code}")
                print(f"   - 是否需要raise_for_status: {not response.ok}")
                
                try:
                    response.raise_for_status()
                    print(f"   - ✅ HTTP状态检查通过")
                except Exception as status_error:
                    print(f"   - ❌ HTTP状态检查失败: {status_error}")
                    raise status_error
                
                print(f"\n📊 [CloudSync] 解析JSON响应")
                print(f"   - 响应文本: '{response.text}'")
                print(f"   - 文本长度: {len(response.text)}")
                print(f"   - 文本类型: {type(response.text)}")
                
                try:
                    result = response.json()
                    print(f"   - ✅ JSON解析成功")
                    print(f"   - 解析结果类型: {type(result)}")
                    print(f"   - 解析结果: {json.dumps(result, indent=4, ensure_ascii=False)}")
                except json.JSONDecodeError as json_error:
                    print(f"   - ❌ JSON解析失败: {json_error}")
                    print(f"   - 原始响应: '{response.text}'")
                    raise json_error
                
                print(f"\n🔍 [CloudSync] 分析API响应")
                response_code = result.get('code')
                response_msg = result.get('msg', 'N/A')
                print(f"   - 响应代码: {response_code} (类型: {type(response_code)})")
                print(f"   - 响应消息: '{response_msg}' (类型: {type(response_msg)})")
                print(f"   - 代码是否为0: {response_code == 0}")
                print(f"   - 响应字段: {list(result.keys())}")
                
                if response_code == 0:
                    print(f"\n✅ [CloudSync] API调用成功，提取令牌")
                    token = result.get('tenant_access_token')
                    print(f"   - 令牌字段: 'tenant_access_token'")
                    print(f"   - 令牌值: '{token}'")
                    print(f"   - 令牌类型: {type(token)}")
                    print(f"   - 令牌长度: {len(token) if token else 0} 字符")
                    print(f"   - 令牌前缀: '{token[:10] if token else 'N/A'}...'")
                    print(f"   - 令牌是否有效: {bool(token and len(token) > 0)}")
                    
                    if token:
                        print(f"✅ [CloudSync] 成功获取飞书访问令牌")
                        print(f"   - 完整令牌: '{token}'")
                        print(f"   - 令牌摘要: '{token[:10]}...'")
                        print(f"   - 令牌完整长度: {len(token)} 字符")
                        print(f"   - 令牌类型: {type(token)}")
                        print(f"   - 返回时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
                        return token
                    else:
                        print(f"❌ [CloudSync] 令牌为空")
                        return None
                else:
                    error_msg = f"获取飞书令牌失败: {result.get('msg')}"
                    print(f"❌ [CloudSync] {error_msg}")
                    print(f"❌ [CloudSync] 错误代码: {result.get('code')}")
                    print(f"❌ [CloudSync] 完整错误信息: {json.dumps(result, indent=4, ensure_ascii=False)}")
                    self.logger.error(error_msg)
                    
                    # 如果是权限或配置错误，不需要重试
                    if result.get('code') in [99991663, 99991664, 99991665]:  # 权限相关错误
                        print(f"❌ [CloudSync] 权限相关错误，不进行重试")
                        return None
                    
                    if attempt < max_retries - 1:
                        delay = self.rate_limiter.exponential_backoff(attempt, 2.0)
                        print(f"   - {delay:.2f}秒后重试...")
                        time.sleep(delay)
                        continue
                    return None
                    
            except requests.exceptions.RequestException as e:
                error_msg = f"获取飞书令牌网络异常: {e}"
                print(f"❌ [CloudSync] {error_msg}")
                print(f"❌ [CloudSync] 异常类型: {type(e).__name__}")
                print(f"❌ [CloudSync] 异常详情: {str(e)}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"❌ [CloudSync] 响应状态码: {e.response.status_code}")
                    print(f"❌ [CloudSync] 响应内容: {e.response.text[:500]}...")
                self.logger.error(error_msg)
                
                if attempt < max_retries - 1:
                    delay = self.rate_limiter.exponential_backoff(attempt, 3.0)
                    print(f"   - {delay:.2f}秒后重试...")
                    time.sleep(delay)
                    continue
                return None
                
            except Exception as e:
                error_msg = f"获取飞书令牌异常: {e}"
                print(f"❌ [CloudSync] {error_msg}")
                print(f"❌ [CloudSync] 异常类型: {type(e).__name__}")
                print(f"❌ [CloudSync] 异常详情: {str(e)}")
                self.logger.error(error_msg)
                import traceback
                print(f"   - 异常堆栈: {traceback.format_exc()}")
                
                if attempt < max_retries - 1:
                    delay = self.rate_limiter.exponential_backoff(attempt, 5.0)
                    print(f"   - {delay:.2f}秒后重试...")
                    time.sleep(delay)
                    continue
                return None
        
        print(f"❌ [CloudSync] 获取飞书访问令牌失败，已用尽所有重试次数")
        self.logger.error(f"❌ 获取飞书访问令牌失败，已用尽所有重试次数")
        return None
    
    def sync_to_feishu(self, data: List[Dict[str, Any]], 
                      spreadsheet_token: str, 
                      table_id: str = None,
                      max_retries: int = 3,
                      continue_on_failure: bool = True) -> bool:
        """
        同步数据到飞书多维表格
        
        Args:
            data: 要同步的数据
            spreadsheet_token: 飞书表格token
            table_id: 多维表格ID
            max_retries: 最大重试次数
            continue_on_failure: 失败时是否继续（不抛出异常）
            
        Returns:
            是否同步成功
        """
        print(f"\n" + "="*100)
        print(f"🚀 [CloudSync] 开始飞书多维表格同步流程 - 详细参数")
        print(f"📋 [CloudSync] 函数调用参数详情:")
        print(f"   - 函数名: sync_to_feishu")
        print(f"   - data 参数类型: {type(data)}")
        print(f"   - data 参数长度: {len(data)}")
        print(f"   - spreadsheet_token 参数: '{spreadsheet_token}' (类型: {type(spreadsheet_token)}, 长度: {len(spreadsheet_token)})")
        print(f"   - table_id 参数: '{table_id}' (类型: {type(table_id)})")
        print(f"   - max_retries 参数: {max_retries} (类型: {type(max_retries)})")
        print(f"   - continue_on_failure 参数: {continue_on_failure} (类型: {type(continue_on_failure)})")
        print(f"   - 调用时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
        print(f"   - 进程ID: {os.getpid()}")
        print(f"   - 线程ID: {threading.current_thread().ident}")
        
        # 详细打印前3条数据
        print(f"\n📝 [CloudSync] 输入数据详细分析:")
        for i, item in enumerate(data[:3]):
            print(f"   数据项 {i+1}:")
            print(f"     - 数据类型: {type(item)}")
            print(f"     - 数据字段数: {len(item) if isinstance(item, dict) else 'N/A'}")
            if isinstance(item, dict):
                print(f"     - 所有字段: {list(item.keys())}")
                for key, value in item.items():
                    print(f"       * {key}: '{str(value)[:100]}...' (类型: {type(value)}, 长度: {len(str(value))})")
            else:
                print(f"     - 数据内容: {str(item)[:200]}...")
        if len(data) > 3:
            print(f"   ... 还有 {len(data) - 3} 条数据项")
        
        self.logger.info(f"🚀 [CloudSync] 开始飞书同步流程")
        self.logger.info(f"   - 数据条数: {len(data)}")
        self.logger.info(f"   - 表格Token: {spreadsheet_token[:10]}...")
        self.logger.info(f"   - 表格ID: {table_id}")
        self.logger.info(f"   - 最大重试次数: {max_retries}")
        self.logger.info(f"   - 失败时继续执行: {continue_on_failure}")
        
        print(f"\n🔄 [CloudSync] 开始飞书同步重试循环")
        print(f"   - 重试范围: range({max_retries}) = {list(range(max_retries))}")
        print(f"   - 循环类型: for attempt in range(max_retries)")
        
        for attempt in range(max_retries):
            try:
                print(f"\n" + "-"*80)
                print(f"🔑 [CloudSync] 尝试获取飞书访问令牌 (第{attempt + 1}/{max_retries}次)")
                print(f"📊 [CloudSync] 令牌获取尝试详情:")
                print(f"   - attempt 变量: {attempt} (类型: {type(attempt)})")
                print(f"   - 尝试编号: {attempt + 1}")
                print(f"   - 总尝试次数: {max_retries}")
                print(f"   - 剩余尝试次数: {max_retries - attempt - 1}")
                print(f"   - 是否最后一次尝试: {attempt == max_retries - 1}")
                print(f"   - 令牌获取重试次数: 2")
                print(f"   - 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
                
                self.logger.info(f"🔑 [CloudSync] 尝试获取飞书访问令牌 (第{attempt + 1}次)")
                
                print(f"\n🚀 [CloudSync] 调用 get_feishu_access_token 方法")
                print(f"   - 方法参数: max_retries=2")
                print(f"   - 调用时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
                
                access_token = self.get_feishu_access_token(max_retries=2)  # 令牌获取使用较少重试次数
                
                print(f"\n📊 [CloudSync] 令牌获取结果分析")
                print(f"   - 返回值: '{access_token}' (类型: {type(access_token)})")
                print(f"   - 令牌长度: {len(access_token) if access_token else 0}")
                print(f"   - 令牌是否有效: {bool(access_token)}")
                print(f"   - 返回时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
                
                if not access_token:
                    print(f"\n❌ [CloudSync] 令牌获取失败处理")
                    print(f"   - 当前尝试: {attempt + 1}/{max_retries}")
                    print(f"   - 是否还有重试机会: {attempt < max_retries - 1}")
                    
                    if attempt < max_retries - 1:
                        print(f"   - 🔄 准备重试")
                        delay = self.rate_limiter.exponential_backoff(attempt, 5.0)
                        print(f"   - 计算延迟: {delay:.2f}秒")
                        print(f"   - 延迟类型: {type(delay)}")
                        self.logger.warning(f"⚠️ [CloudSync] 获取飞书令牌失败，{delay:.2f}秒后重试 (尝试 {attempt + 1}/{max_retries})")
                        print(f"   - 开始等待: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
                        time.sleep(delay)
                        print(f"   - 等待结束: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
                        continue
                    else:
                        print(f"   - ❌ 已用尽所有重试机会")
                        print(f"   - continue_on_failure: {continue_on_failure}")
                        if continue_on_failure:
                            print(f"   - 选择: 继续执行任务")
                            self.logger.error("❌ [CloudSync] 飞书令牌获取失败，但继续执行任务")
                            return False
                        else:
                            print(f"   - 选择: 抛出异常")
                            self.logger.error("❌ [CloudSync] 飞书令牌获取失败，抛出异常")
                            raise Exception("无法获取飞书访问令牌")
                
                print(f"\n✅ [CloudSync] 飞书访问令牌获取成功")
                print(f"   - 令牌摘要: '{access_token[:10]}...'")
                print(f"   - 令牌完整长度: {len(access_token)}")
                self.logger.info(f"✅ [CloudSync] 飞书访问令牌获取成功")
                
                print(f"\n🚀 [CloudSync] 调用 _execute_feishu_sync 方法")
                print(f"   - 方法参数详情:")
                print(f"     - data: {type(data)} (长度: {len(data)})")
                print(f"     - spreadsheet_token: '{spreadsheet_token}'")
                print(f"     - table_id: '{table_id}'")
                print(f"     - access_token: '{access_token[:10]}...'")
                print(f"   - 调用时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
                
                result = self._execute_feishu_sync(data, spreadsheet_token, table_id, access_token)
                
                print(f"\n📊 [CloudSync] 同步执行结果分析")
                print(f"   - 返回值: {result} (类型: {type(result)})")
                print(f"   - 是否成功: {bool(result)}")
                print(f"   - 返回时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
                self.logger.info(f"📊 [CloudSync] 同步执行结果: {result}")
                return result
                
            except requests.exceptions.RequestException as e:
                error_msg = str(e)
                self.logger.error(f"❌ [CloudSync] 飞书同步网络异常 (尝试 {attempt + 1}/{max_retries}): {error_msg}")
                
                # 检查是否为频率限制错误
                is_rate_limit = "频率限制" in error_msg or "429" in error_msg or "99991400" in error_msg
                
                if attempt < max_retries - 1:
                    if is_rate_limit:
                        # 频率限制使用指数退避
                        delay = self.rate_limiter.exponential_backoff(attempt, 3.0)
                        self.logger.info(f"⏳ [CloudSync] 频率限制触发，{delay:.2f}秒后重试")
                    else:
                        # 其他网络错误使用较短延迟
                        delay = min(5 * (attempt + 1), 30)
                        self.logger.info(f"⏳ [CloudSync] 网络错误，{delay}秒后重试")
                    time.sleep(delay)
                else:
                    if continue_on_failure:
                        self.logger.error("❌ [CloudSync] 飞书同步最终失败，但继续执行任务")
                        return False
                    else:
                        self.logger.error("❌ [CloudSync] 飞书同步最终失败，抛出异常")
                        raise e
                        
            except Exception as e:
                self.logger.error(f"❌ [CloudSync] 飞书同步失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                
                if attempt < max_retries - 1:
                    delay = self.rate_limiter.exponential_backoff(attempt, 10.0)
                    self.logger.info(f"⏳ [CloudSync] {delay:.2f}秒后重试飞书同步")
                    time.sleep(delay)
                else:
                    if continue_on_failure:
                        self.logger.error("❌ [CloudSync] 飞书同步最终失败，但继续执行任务")
                        return False
                    else:
                        self.logger.error("❌ [CloudSync] 飞书同步最终失败，抛出异常")
                        raise e
        
        self.logger.error("❌ [CloudSync] 所有重试尝试都已用尽")
        return False
    
    def _execute_feishu_sync(self, data: List[Dict[str, Any]], 
                           spreadsheet_token: str, 
                           table_id: str,
                           access_token: str) -> bool:
        """
        执行飞书同步的核心逻辑
        
        Args:
            data: 要同步的数据
            spreadsheet_token: 飞书表格token
            table_id: 多维表格ID
            access_token: 访问令牌
            
        Returns:
            是否同步成功
        """
        try:
             print("\n" + "="*80)
             print("🔧 [CloudSync] 开始执行飞书同步核心逻辑")
             print(f"📋 [CloudSync] 输入参数详细信息:")
             print(f"   - data 参数类型: {type(data)}")
             print(f"   - data 参数长度: {len(data)}")
             print(f"   - spreadsheet_token 参数: '{spreadsheet_token}' (类型: {type(spreadsheet_token)}, 长度: {len(spreadsheet_token)})")
             print(f"   - table_id 参数: '{table_id}' (类型: {type(table_id)})")
             print(f"   - access_token 参数: '{access_token[:15]}...' (类型: {type(access_token)}, 长度: {len(access_token)})")
             
             # 详细打印前3条数据
             print(f"\n📝 [CloudSync] 输入数据详细内容:")
             for i, item in enumerate(data[:3]):
                 print(f"   数据项 {i+1}:")
                 print(f"     - 数据类型: {type(item)}")
                 print(f"     - 数据字段数: {len(item) if isinstance(item, dict) else 'N/A'}")
                 if isinstance(item, dict):
                     print(f"     - 所有字段: {list(item.keys())}")
                     for key, value in item.items():
                         print(f"       * {key}: '{str(value)[:100]}...' (类型: {type(value)})")
                 else:
                     print(f"     - 数据内容: {str(item)[:200]}...")
             if len(data) > 3:
                 print(f"   ... 还有 {len(data) - 3} 条数据项")
             print("="*80)
             
             self.logger.info(f"🔧 [CloudSync] 开始执行飞书同步核心逻辑")
             self.logger.info(f"   - 数据条数: {len(data)}")
             self.logger.info(f"   - 表格Token: {spreadsheet_token[:10]}...")
             self.logger.info(f"   - 表格ID: {table_id}")
             
             # 打印前3条数据的详细信息用于调试
             self.logger.info(f"📋 [CloudSync] 输入数据示例:")
             for i, item in enumerate(data[:3]):
                 self.logger.info(f"   - 第{i+1}条数据字段: {list(item.keys())}")
                 self.logger.info(f"   - 第{i+1}条数据内容: {str(item)[:200]}...")
             
             # 设置请求头
             headers = {
                 'Authorization': f'Bearer {access_token}',
                 'Content-Type': 'application/json'
             }
             print(f"\n🔑 [CloudSync] 请求头设置完成")
             print(f"   - Authorization: Bearer {access_token[:10]}...")
             self.logger.info(f"🔑 [CloudSync] 请求头设置完成")
             
             # 获取表格字段信息以确定字段类型
             print(f"\n📋 [CloudSync] 开始获取飞书表格字段信息")
             fields_url = f"{self.feishu_config['base_url']}/bitable/v1/apps/{spreadsheet_token}/tables/{table_id}/fields"
             print(f"📋 [CloudSync] 字段查询详细参数:")
             print(f"   - base_url: {self.feishu_config['base_url']}")
             print(f"   - spreadsheet_token: {spreadsheet_token}")
             print(f"   - table_id: {table_id}")
             print(f"   - 完整URL: {fields_url}")
             print(f"   - URL长度: {len(fields_url)} 字符")
             print(f"   - 请求方法: GET")
             print(f"   - 请求头: {json.dumps(headers, indent=4, ensure_ascii=False)}")
             print(f"   - 超时设置: 30秒")
             self.logger.info(f"📋 [CloudSync] 开始获取飞书表格字段信息")
             self.logger.info(f"   - 字段查询URL: {fields_url}")
             
             # 应用文档级频率限制
             print(f"\n⏱️ [CloudSync] 应用文档级频率限制检查...")
             print(f"   - 文档Token: {spreadsheet_token}")
             print(f"   - 当前文档调用记录: {self.rate_limiter.doc_call_times.get(spreadsheet_token, [])}")
             print(f"   - 文档级最大调用数: {self.rate_limiter.max_doc_calls_per_second}")
             self.rate_limiter.wait_for_doc_call(spreadsheet_token)
             print(f"   - 频率限制检查通过")
             
             print(f"\n🌐 [CloudSync] 发送字段查询请求...")
             print(f"   - 请求时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
             self.logger.info(f"🌐 发送字段查询请求...")
             # 记录文档级API调用
             self.rate_limiter.record_doc_call(spreadsheet_token)
             print(f"   - 已记录文档级API调用")
             print(f"   - 更新后文档调用记录: {self.rate_limiter.doc_call_times.get(spreadsheet_token, [])}")
             
             fields_response = requests.get(fields_url, headers=headers, timeout=30)
             print(f"\n📊 [CloudSync] 字段查询响应详情:")
             print(f"   - 响应状态码: {fields_response.status_code}")
             print(f"   - 响应状态文本: {fields_response.reason}")
             print(f"   - 响应头: {json.dumps(dict(fields_response.headers), indent=4, ensure_ascii=False)}")
             print(f"   - 响应内容长度: {len(fields_response.text)} 字符")
             print(f"   - 响应内容: {fields_response.text}")
             print(f"   - 响应时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
             self.logger.info(f"   - 字段查询响应状态: {fields_response.status_code}")
             
             # 处理频率限制错误
             if fields_response.status_code == 429:
                 self.logger.warning(f"⚠️ 文档级频率限制触发 (HTTP 429)")
                 raise requests.exceptions.RequestException(f"文档频率限制: {fields_response.text}")
             elif fields_response.status_code == 400:
                 result = fields_response.json()
                 if result.get('code') == 99991400:
                     self.logger.warning(f"⚠️ 应用级频率限制触发 (HTTP 400)")
                     raise requests.exceptions.RequestException(f"应用频率限制: {result.get('msg')}")
             
             field_types = {}
             available_fields = []
             field_name_to_id = {}
             
             if fields_response.status_code == 200:
                 print(f"\n✅ [CloudSync] 字段查询请求成功，开始解析响应...")
                 try:
                     fields_result = fields_response.json()
                     print(f"📊 [CloudSync] 字段响应JSON解析成功:")
                     print(f"   - 响应类型: {type(fields_result)}")
                     print(f"   - 响应代码: {fields_result.get('code')}")
                     print(f"   - 响应消息: {fields_result.get('msg', 'N/A')}")
                     print(f"   - 完整响应: {json.dumps(fields_result, indent=4, ensure_ascii=False)}")
                     self.logger.info(f"   - 字段查询响应解析: code={fields_result.get('code')}, msg={fields_result.get('msg', 'N/A')}")
                     
                     if fields_result.get('code') == 0:
                         print(f"\n🔍 [CloudSync] 解析字段数据...")
                         data_section = fields_result.get('data', {})
                         print(f"   - data 部分类型: {type(data_section)}")
                         print(f"   - data 部分内容: {json.dumps(data_section, indent=4, ensure_ascii=False)}")
                         
                         fields_data = data_section.get('items', [])
                         print(f"   - items 部分类型: {type(fields_data)}")
                         print(f"   - items 部分长度: {len(fields_data)}")
                         
                         field_types = {}
                         available_fields = []
                         field_name_to_id = {}
                         
                         print(f"\n📋 [CloudSync] 逐个解析字段信息:")
                         for i, field in enumerate(fields_data):
                             field_name = field.get('field_name')
                             field_id = field.get('field_id')
                             field_type = field.get('type')
                             
                             print(f"   字段 {i+1}:")
                             print(f"     - 原始字段数据: {json.dumps(field, indent=6, ensure_ascii=False)}")
                             print(f"     - 字段名: '{field_name}' (类型: {type(field_name)})")
                             print(f"     - 字段ID: '{field_id}' (类型: {type(field_id)})")
                             print(f"     - 字段类型: {field_type} (类型: {type(field_type)})")
                             
                             field_types[field_name] = field_type
                             available_fields.append(field_name)
                             field_name_to_id[field_name] = field_id
                         
                         print(f"\n✅ [CloudSync] 字段信息解析完成:")
                         print(f"   - 字段总数: {len(available_fields)}")
                         print(f"   - 可用字段列表: {available_fields}")
                         print(f"   - 字段类型映射: {json.dumps(field_types, indent=4, ensure_ascii=False)}")
                         print(f"   - 字段名到ID映射: {json.dumps(field_name_to_id, indent=4, ensure_ascii=False)}")
                         
                         self.logger.info(f"✅ 飞书表格字段信息获取成功:")
                         self.logger.info(f"   - 可用字段数量: {len(available_fields)}")
                         self.logger.info(f"   - 可用字段列表: {available_fields}")
                         self.logger.info(f"   - 字段类型映射: {field_types}")
                         self.logger.info(f"   - 字段名到ID映射: {field_name_to_id}")
                     else:
                         print(f"\n❌ [CloudSync] 字段查询API返回错误:")
                         print(f"   - 错误代码: {fields_result.get('code')}")
                         print(f"   - 错误消息: {fields_result.get('msg')}")
                         print(f"   - 完整错误响应: {json.dumps(fields_result, indent=4, ensure_ascii=False)}")
                         self.logger.error(f"❌ 获取字段信息失败: {fields_result.get('msg')}")
                 except json.JSONDecodeError as e:
                     print(f"\n❌ [CloudSync] 字段响应JSON解析失败:")
                     print(f"   - JSON错误: {str(e)}")
                     print(f"   - 原始响应内容: {fields_response.text}")
                     self.logger.error(f"❌ 字段响应JSON解析失败: {str(e)}")
             else:
                 print(f"\n❌ [CloudSync] 字段查询请求失败:")
                 print(f"   - HTTP状态码: {fields_response.status_code}")
                 print(f"   - 状态文本: {fields_response.reason}")
                 print(f"   - 响应头: {json.dumps(dict(fields_response.headers), indent=4, ensure_ascii=False)}")
                 print(f"   - 响应内容: {fields_response.text}")
                 self.logger.error(f"❌ 获取字段信息请求失败: HTTP {fields_response.status_code}")
                 self.logger.error(f"   - 响应内容: {fields_response.text[:200]}...")
             
             # 准备数据记录
             print(f"\n🔄 [CloudSync] 开始准备数据记录")
             print(f"📝 [CloudSync] 数据记录准备参数:")
             print(f"   - 待处理数据条数: {len(data)}")
             print(f"   - 数据类型: {type(data)}")
             print(f"   - 可用字段: {available_fields if 'available_fields' in locals() else 'N/A'}")
             print(f"   - 字段类型映射: {field_types if 'field_types' in locals() else 'N/A'}")
             print(f"   - 字段名到ID映射: {field_name_to_id if 'field_name_to_id' in locals() else 'N/A'}")
             self.logger.info(f"🔄 开始准备数据记录")
             self.logger.info(f"   - 待处理数据条数: {len(data)}")
             
             records = []
             skipped_fields = set()
             processed_fields = set()
             
             print(f"\n📋 [CloudSync] 逐条处理数据记录:")
             for idx, tweet in enumerate(data):
                 print(f"\n   处理数据项 {idx + 1}/{len(data)}:")
                 print(f"     - 数据类型: {type(tweet)}")
                 print(f"     - 数据字段数: {len(tweet) if isinstance(tweet, dict) else 'N/A'}")
                 if isinstance(tweet, dict):
                     print(f"     - 原始数据字段: {list(tweet.keys())}")
                     print(f"     - 原始数据内容: {json.dumps(tweet, indent=8, ensure_ascii=False)[:500]}...")
                     for key, value in tweet.items():
                         print(f"       * {key}: '{str(value)[:100]}...' (类型: {type(value)})")
                 else:
                     print(f"     - 数据内容: {str(tweet)[:200]}...")
                 
                 self.logger.info(f"   - 处理第 {idx + 1}/{len(data)} 条数据")
                 self.logger.debug(f"     - 原始数据字段: {list(tweet.keys()) if isinstance(tweet, dict) else 'N/A'}")
                 
                 # 数据已经在web_app.py中正确处理，直接使用传入的数据
                 print(f"     - 📋 使用已处理的数据字段")
                 print(f"       - 推文原文内容: '{str(tweet.get('推文原文内容', ''))[:100]}...' (长度: {len(str(tweet.get('推文原文内容', '')))})")
                 print(f"       - 作者: '{tweet.get('作者（账号）', '')}' (类型: {type(tweet.get('作者（账号）', ''))})")
                 print(f"       - 发布时间: {tweet.get('发布时间', 0)} (类型: {type(tweet.get('发布时间', 0))})")
                 self.logger.info(f"     - 📋 使用已处理的数据字段")
                 self.logger.debug(f"       - 推文原文内容: {str(tweet.get('推文原文内容', ''))[:50]}...")
                 self.logger.debug(f"       - 作者: {tweet.get('作者（账号）', '')}")
                 self.logger.debug(f"       - 发布时间: {tweet.get('发布时间', 0)}")
                 
                 # 处理数值字段 - 确保数值字段为有效数字
                 def safe_int(value, default=0):
                     """安全转换为整数"""
                     try:
                         if value is None or value == '':
                             return default
                         return int(float(str(value)))
                     except (ValueError, TypeError):
                         return default
                 
                 # 构建记录数据，只包含飞书表格中存在的字段
                 # 直接使用飞书表格中的实际字段名称进行映射
                 
                 # 构建字段值，根据字段类型使用正确的格式
                 def format_field_value(field_name, value, field_type):
                     """根据字段类型格式化字段值"""
                     if field_type == 1:  # 文本字段
                         return str(value) if value is not None else ''
                     elif field_type == 2:  # 数字字段
                         return safe_int(value, 0)
                     elif field_type == 5:  # 日期时间字段
                         # 飞书API需要毫秒级时间戳
                         if isinstance(value, (int, float)) and value > 0:
                             # 直接使用传入的值（web_app.py已经处理为毫秒级）
                             return int(value)
                         return 0
                     else:
                         # 默认处理为文本
                         return str(value) if value is not None else ''
                 
                 # 构建所有字段值
                 print(f"     - 🔧 构建字段值...")
                 
                 all_possible_fields = {
                     '推文原文内容': format_field_value('推文原文内容', tweet.get('推文原文内容', ''), field_types.get('推文原文内容', 1) if 'field_types' in locals() else 1),
                     '作者（账号）': format_field_value('作者（账号）', tweet.get('作者（账号）', ''), field_types.get('作者（账号）', 1) if 'field_types' in locals() else 1),
                     '推文链接': format_field_value('推文链接', tweet.get('推文链接', ''), field_types.get('推文链接', 1) if 'field_types' in locals() else 1),
                     '话题标签（Hashtag）': format_field_value('话题标签（Hashtag）', tweet.get('话题标签（Hashtag）', ''), field_types.get('话题标签（Hashtag）', 1) if 'field_types' in locals() else 1),
                     '类型标签': format_field_value('类型标签', tweet.get('类型标签', ''), field_types.get('类型标签', 1) if 'field_types' in locals() else 1),
                     '评论': format_field_value('评论', tweet.get('评论', 0), field_types.get('评论', 2) if 'field_types' in locals() else 2),
                     '点赞': format_field_value('点赞', tweet.get('点赞', 0), field_types.get('点赞', 2) if 'field_types' in locals() else 2),
                     '转发': format_field_value('转发', tweet.get('转发', 0), field_types.get('转发', 2) if 'field_types' in locals() else 2)
                 }
                 
                 print(f"     - 📋 所有可能字段: {json.dumps(all_possible_fields, indent=8, ensure_ascii=False)[:300]}...")
                 
                 # 只保留飞书表格中实际存在的字段，使用字段名作为键
                 # 根据飞书API文档，应该使用字段名而不是字段ID
                 print(f"     - 🔍 检查字段是否存在于飞书表格...")
                 record_fields = {}
                 for field_name, field_value in all_possible_fields.items():
                     print(f"       检查字段 '{field_name}':")
                     print(f"         - 字段值: '{str(field_value)[:100]}...'")
                     print(f"         - 可用字段列表: {available_fields if 'available_fields' in locals() else 'N/A'}")
                     
                     if 'available_fields' in locals() and field_name in available_fields:
                         # 直接使用字段名作为键
                         record_fields[field_name] = field_value
                         processed_fields.add(field_name)
                         print(f"         - ✅ 字段存在，已添加到记录")
                         print(f"         - 添加的值: '{str(field_value)[:100]}...'")
                         self.logger.debug(f"     - 字段 {field_name}: {str(field_value)[:50]}...")
                     else:
                         skipped_fields.add(field_name)
                         print(f"         - ❌ 字段不存在于飞书表格，跳过")
                         self.logger.debug(f"     - 跳过字段 '{field_name}' (不存在于飞书表格)")
                 
                 print(f"     - 📊 记录字段处理结果:")
                 print(f"       - 使用字段数: {len(record_fields)}")
                 print(f"       - 使用字段列表: {list(record_fields.keys())}")
                 print(f"       - 记录字段内容: {json.dumps(record_fields, indent=8, ensure_ascii=False)}")
                 
                 self.logger.info(f"     - 第 {idx + 1} 条记录使用字段数: {len(record_fields)}")
                 self.logger.debug(f"     - 使用字段: {list(record_fields.keys())}")
                 
                 if record_fields:
                     record = {'fields': record_fields}
                     records.append(record)
                     print(f"     - ✅ 记录已添加到批量列表")
                     print(f"       - 记录结构: {json.dumps(record, indent=8, ensure_ascii=False)}")
                 else:
                     print(f"     - ⚠️ 没有匹配的字段，跳过此记录")
                     self.logger.warning(f"⚠️ 第 {idx + 1} 条数据没有匹配的字段，跳过")
             
             self.logger.info(f"✅ 数据记录准备完成:")
             self.logger.info(f"   - 原始数据条数: {len(data)}")
             self.logger.info(f"   - 有效记录数: {len(records)}")
             self.logger.info(f"   - 成功处理率: {len(records)/len(data)*100:.1f}%")
             self.logger.info(f"   - 处理的字段: {list(processed_fields)}")
             if skipped_fields:
                 self.logger.warning(f"⚠️ 跳过的字段 (不存在于飞书表格): {list(skipped_fields)}")
             
             # 检查是否有有效记录
             if not records:
                 self.logger.warning(f"⚠️ 没有有效的数据记录可以同步")
                 return False
             
             # 批量创建记录
             print(f"\n📤 [CloudSync] 开始批量创建飞书记录")
             url = f"{self.feishu_config['base_url']}/bitable/v1/apps/{spreadsheet_token}/tables/{table_id}/records/batch_create"
             print(f"📤 [CloudSync] 批量创建API详细参数:")
             print(f"   - base_url: {self.feishu_config['base_url']}")
             print(f"   - spreadsheet_token: {spreadsheet_token}")
             print(f"   - table_id: {table_id}")
             print(f"   - 完整URL: {url}")
             print(f"   - URL长度: {len(url)} 字符")
             print(f"   - 请求方法: POST")
             print(f"   - 请求头: {json.dumps(headers, indent=4, ensure_ascii=False)}")
             print(f"   - 超时设置: 60秒")
             self.logger.info(f"📤 [CloudSync] 开始批量创建飞书记录")
             self.logger.info(f"   - 创建URL: {url}")
             
             payload = {
                 'records': records
             }
             print(f"\n📋 [CloudSync] 请求载荷详细信息:")
             print(f"   - 载荷类型: {type(payload)}")
             print(f"   - 记录数量: {len(records)}")
             print(f"   - 载荷大小: {len(str(payload))} 字符")
             print(f"   - 载荷JSON大小: {len(json.dumps(payload, ensure_ascii=False))} 字符")
             print(f"   - 完整载荷内容: {json.dumps(payload, indent=4, ensure_ascii=False)}")
             
             # 详细打印每条记录
             print(f"\n📝 [CloudSync] 载荷中的记录详情:")
             for i, record in enumerate(records):
                 print(f"   记录 {i+1}:")
                 print(f"     - 记录类型: {type(record)}")
                 print(f"     - 记录结构: {json.dumps(record, indent=6, ensure_ascii=False)}")
                 if 'fields' in record:
                     print(f"     - 字段数量: {len(record['fields'])}")
                     for field_name, field_value in record['fields'].items():
                         print(f"       * {field_name}: '{str(field_value)[:100]}...' (类型: {type(field_value)})")
             
             self.logger.info(f"   - 记录数量: {len(records)}")
             self.logger.info(f"   - 载荷大小: {len(str(payload))} 字符")
             self.logger.info(f"   - 载荷示例: {str(payload)[:500]}...")
             
             # 应用文档级频率限制
             print(f"\n⏱️ [CloudSync] 应用文档级频率限制检查...")
             print(f"   - 文档Token: {spreadsheet_token}")
             print(f"   - 当前文档调用记录: {self.rate_limiter.doc_call_times.get(spreadsheet_token, [])}")
             print(f"   - 文档级最大调用数: {self.rate_limiter.max_doc_calls_per_second}")
             self.rate_limiter.wait_for_doc_call(spreadsheet_token)
             print(f"   - 频率限制检查通过")
             
             print(f"\n🌐 [CloudSync] 发送飞书API请求...")
             print(f"   - 请求时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
             self.logger.info(f"🌐 [CloudSync] 发送飞书API请求...")
             # 记录文档级API调用
             self.rate_limiter.record_doc_call(spreadsheet_token)
             print(f"   - 已记录文档级API调用")
             print(f"   - 更新后文档调用记录: {self.rate_limiter.doc_call_times.get(spreadsheet_token, [])}")
             
             response = requests.post(url, headers=headers, json=payload, timeout=60)
             print(f"\n📊 [CloudSync] 批量创建API响应详情:")
             print(f"   - 响应状态码: {response.status_code}")
             print(f"   - 响应状态文本: {response.reason}")
             print(f"   - 响应头: {json.dumps(dict(response.headers), indent=4, ensure_ascii=False)}")
             print(f"   - 响应内容长度: {len(response.text)} 字符")
             print(f"   - 响应内容: {response.text}")
             print(f"   - 响应时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
             self.logger.info(f"📊 [CloudSync] 飞书API响应状态码: {response.status_code}")
             
             # 处理频率限制错误
             if response.status_code == 429:
                 self.logger.warning(f"⚠️ 文档级频率限制触发 (HTTP 429)")
                 raise requests.exceptions.RequestException(f"文档频率限制: {response.text}")
             elif response.status_code == 400:
                 result = response.json()
                 if result.get('code') == 99991400:
                     self.logger.warning(f"⚠️ 应用级频率限制触发 (HTTP 400)")
                     raise requests.exceptions.RequestException(f"应用频率限制: {result.get('msg')}")
             
             print(f"\n🔍 [CloudSync] 检查HTTP响应状态...")
             try:
                 response.raise_for_status()
                 print(f"   - ✅ HTTP状态检查通过")
             except requests.exceptions.HTTPError as e:
                 print(f"   - ❌ HTTP状态检查失败: {str(e)}")
                 print(f"   - 响应状态码: {response.status_code}")
                 print(f"   - 响应内容: {response.text}")
                 raise e
             
             print(f"\n📊 [CloudSync] 解析响应JSON...")
             try:
                 result = response.json()
                 print(f"   - ✅ JSON解析成功")
                 print(f"   - 响应类型: {type(result)}")
                 print(f"   - 响应代码: {result.get('code')}")
                 print(f"   - 响应消息: {result.get('msg', 'N/A')}")
                 print(f"   - 完整响应: {json.dumps(result, indent=4, ensure_ascii=False)}")
             except json.JSONDecodeError as e:
                 print(f"   - ❌ JSON解析失败: {str(e)}")
                 print(f"   - 原始响应内容: {response.text}")
                 raise e
             
             self.logger.info(f"📊 [CloudSync] 飞书API响应解析: code={result.get('code')}, msg={result.get('msg', 'N/A')}")
             
             print(f"\n🔍 [CloudSync] 检查API响应结果...")
             if result.get('code') == 0:
                 print(f"   - ✅ API调用成功 (code=0)")
                 data_section = result.get('data', {})
                 print(f"   - data 部分类型: {type(data_section)}")
                 print(f"   - data 部分内容: {json.dumps(data_section, indent=4, ensure_ascii=False)}")
                 
                 created_records = data_section.get('records', [])
                 print(f"   - 创建的记录类型: {type(created_records)}")
                 print(f"   - 创建的记录数量: {len(created_records)}")
                 
                 # 详细打印创建的记录
                 print(f"\n📝 [CloudSync] 创建的记录详情:")
                 for i, created_record in enumerate(created_records[:3]):  # 只打印前3条
                     print(f"   创建记录 {i+1}:")
                     print(f"     - 记录类型: {type(created_record)}")
                     print(f"     - 记录内容: {json.dumps(created_record, indent=6, ensure_ascii=False)}")
                 if len(created_records) > 3:
                     print(f"   ... 还有 {len(created_records) - 3} 条创建记录")
                 
                 print(f"\n✅ [CloudSync] 成功同步到飞书多维表格:")
                 print(f"   - 原始数据条数: {len(data)}")
                 print(f"   - 有效记录数: {len(records)}")
                 print(f"   - 创建成功数: {len(created_records)}")
                 print(f"   - 成功率: {len(created_records)/len(data)*100:.1f}%")
                 print("="*80)
                 self.logger.info(f"✅ [CloudSync] 成功同步到飞书多维表格:")
                 self.logger.info(f"   - 原始数据条数: {len(data)}")
                 self.logger.info(f"   - 有效记录数: {len(records)}")
                 self.logger.info(f"   - 创建成功数: {len(created_records)}")
                 return True
             else:
                 print(f"   - ❌ API调用失败 (code={result.get('code')})")
                 print(f"   - 错误代码: {result.get('code')}")
                 print(f"   - 错误消息: {result.get('msg')}")
                 print(f"   - 完整错误响应: {json.dumps(result, indent=4, ensure_ascii=False)}")
                 
                 print(f"\n❌ [CloudSync] 飞书同步失败: {result.get('msg')}")
                 print(f"   - 错误详情: {result}")
                 print("="*80)
                 self.logger.error(f"❌ [CloudSync] 飞书同步失败: {result.get('msg')}")
                 self.logger.error(f"   - 错误详情: {result}")
                 return False
                 
        except requests.exceptions.RequestException as e:
            print(f"\n❌ [CloudSync] 飞书同步网络请求异常详情:")
            print(f"   - 异常类型: {type(e).__name__}")
            print(f"   - 异常模块: {type(e).__module__}")
            print(f"   - 异常消息: {str(e)}")
            print(f"   - 异常参数: {e.args}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   - 响应状态码: {e.response.status_code}")
                print(f"   - 响应状态文本: {e.response.reason}")
                print(f"   - 响应头: {dict(e.response.headers)}")
                print(f"   - 响应内容长度: {len(e.response.text)}")
                print(f"   - 响应内容: {e.response.text[:1000]}...")
            if hasattr(e, 'request') and e.request is not None:
                print(f"   - 请求方法: {e.request.method}")
                print(f"   - 请求URL: {e.request.url}")
                print(f"   - 请求头: {dict(e.request.headers)}")
                if hasattr(e.request, 'body') and e.request.body:
                    print(f"   - 请求体长度: {len(str(e.request.body))}")
                    print(f"   - 请求体内容: {str(e.request.body)[:500]}...")
            print(f"   - 异常堆栈: {traceback.format_exc()}")
            print("="*80)
            
            self.logger.error(f"❌ 飞书同步网络请求异常:")
            self.logger.error(f"   - 异常类型: {type(e).__name__}")
            self.logger.error(f"   - 异常详情: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                self.logger.error(f"   - 响应状态码: {e.response.status_code}")
                self.logger.error(f"   - 响应内容: {e.response.text[:500]}...")
            raise e  # 重新抛出异常，让上层处理重试逻辑
        except Exception as e:
            print(f"\n❌ [CloudSync] 飞书同步未知异常详情:")
            print(f"   - 异常类型: {type(e).__name__}")
            print(f"   - 异常模块: {type(e).__module__}")
            print(f"   - 异常消息: {str(e)}")
            print(f"   - 异常参数: {e.args}")
            print(f"   - 异常属性: {[attr for attr in dir(e) if not attr.startswith('_')]}")
            print(f"   - 异常堆栈: {traceback.format_exc()}")
            print(f"   - 当前变量状态:")
            print(f"     - data 长度: {len(data) if 'data' in locals() else 'N/A'}")
            print(f"     - records 长度: {len(records) if 'records' in locals() else 'N/A'}")
            print(f"     - access_token 长度: {len(access_token) if 'access_token' in locals() else 'N/A'}")
            print(f"     - spreadsheet_token: {spreadsheet_token if 'spreadsheet_token' in locals() else 'N/A'}")
            print(f"     - table_id: {table_id if 'table_id' in locals() else 'N/A'}")
            print("="*80)
            
            self.logger.error(f"❌ 飞书同步过程中发生未知错误:")
            self.logger.error(f"   - 异常类型: {type(e).__name__}")
            self.logger.error(f"   - 异常详情: {str(e)}")
            import traceback
            self.logger.error(f"   - 异常堆栈: {traceback.format_exc()}")
            raise e  # 重新抛出异常，让上层处理重试逻辑
    
    def sync_to_feishu_sheet(self, data: List[Dict[str, Any]], 
                            spreadsheet_token: str, 
                            sheet_id: str = None) -> bool:
        """
        同步数据到飞书表格
        
        Args:
            data: 要同步的数据
            spreadsheet_token: 飞书表格token
            sheet_id: 工作表ID
            
        Returns:
            是否同步成功
        """
        print("\n" + "="*60)
        print("📊 开始飞书表格同步流程")
        print(f"   - 表格Token: {spreadsheet_token[:10]}...")
        print(f"   - 工作表ID: {sheet_id}")
        print(f"   - 数据条数: {len(data)}")
        print("="*60)
        
        self.logger.info(f"📊 开始飞书表格同步流程")
        self.logger.info(f"   - 表格Token: {spreadsheet_token[:10]}...")
        self.logger.info(f"   - 工作表ID: {sheet_id}")
        self.logger.info(f"   - 数据条数: {len(data)}")
        
        print("\n🔑 获取飞书访问令牌...")
        self.logger.info(f"🔑 获取飞书访问令牌")
        access_token = self.get_feishu_access_token()
        if not access_token:
            print("❌ 飞书访问令牌获取失败")
            self.logger.error(f"❌ 飞书访问令牌获取失败")
            return False
        print("✅ 飞书访问令牌获取成功")
        self.logger.info(f"✅ 飞书访问令牌获取成功")
            
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            print("✅ 请求头设置完成")
            self.logger.info(f"✅ 请求头设置完成")
            
            # 如果没有指定sheet_id，获取第一个工作表
            if not sheet_id:
                print("\n🔍 未指定工作表ID，获取第一个工作表")
                self.logger.info(f"🔍 未指定工作表ID，获取第一个工作表")
                url = f"{self.feishu_config['base_url']}/sheets/v3/spreadsheets/{spreadsheet_token}/sheets/query"
                print(f"   - 查询URL: {url}")
                self.logger.info(f"   - 查询URL: {url}")
                
                response = requests.get(url, headers=headers)
                print(f"   - 响应状态码: {response.status_code}")
                self.logger.info(f"   - 响应状态码: {response.status_code}")
                response.raise_for_status()
                
                result = response.json()
                print(f"   - 响应结果: code={result.get('code')}")
                self.logger.info(f"   - 响应结果: code={result.get('code')}")
                
                if result.get('code') == 0 and result.get('data', {}).get('sheets'):
                    sheet_id = result['data']['sheets'][0]['sheet_id']
                    print(f"✅ 获取到工作表ID: {sheet_id}")
                    self.logger.info(f"✅ 获取到工作表ID: {sheet_id}")
                else:
                    print(f"❌ 无法获取飞书工作表信息: {result.get('msg')}")
                    self.logger.error(f"❌ 无法获取飞书工作表信息: {result.get('msg')}")
                    return False
            else:
                print(f"ℹ️ 使用指定的工作表ID: {sheet_id}")
                self.logger.info(f"ℹ️ 使用指定的工作表ID: {sheet_id}")
            
            # 清空现有数据
            print("\n🧹 清空现有数据")
            self.logger.info(f"🧹 清空现有数据")
            clear_url = f"{self.feishu_config['base_url']}/sheets/v2/spreadsheets/{spreadsheet_token}/values_batch_clear"
            clear_payload = {
                'ranges': [f'{sheet_id}!A:Z']
            }
            print(f"   - 清空URL: {clear_url}")
            print(f"   - 清空范围: {clear_payload['ranges']}")
            self.logger.info(f"   - 清空URL: {clear_url}")
            self.logger.info(f"   - 清空范围: {clear_payload['ranges']}")
            
            clear_response = requests.post(clear_url, headers=headers, json=clear_payload)
            print(f"   - 清空响应状态码: {clear_response.status_code}")
            self.logger.info(f"   - 清空响应状态码: {clear_response.status_code}")
            
            if not data:
                print("⚠️ 没有数据需要同步")
                self.logger.warning(f"⚠️ 没有数据需要同步")
                return True
            
            # 准备数据
            print("\n🔄 开始准备表格数据")
            self.logger.info(f"🔄 开始准备表格数据")
            values = [[
                '序号', '用户名', '推文内容', '发布时间', '评论数', 
                '转发数', '点赞数', '链接', '标签', '筛选状态'
            ]]
            print(f"   - 表头设置完成: {values[0]}")
            self.logger.info(f"   - 表头设置完成: {values[0]}")
            
            for i, tweet in enumerate(data, 1):
                row = [
                    str(i),
                    tweet.get('username', ''),
                    tweet.get('content', ''),
                    tweet.get('timestamp', ''),
                    str(tweet.get('comments', 0)),
                    str(tweet.get('retweets', 0)),
                    str(tweet.get('likes', 0)),
                    tweet.get('link', ''),
                    ', '.join(tweet.get('tags', [])),
                    tweet.get('filter_status', '')
                ]
                values.append(row)
                if i <= 3:  # 只记录前3行的详细信息
                    print(f"   - 第 {i} 行数据: {row[:3]}...")  # 只显示前3个字段
                    self.logger.debug(f"   - 第 {i} 行数据: {row[:3]}...")  # 只显示前3个字段
            
            print(f"\n✅ 表格数据准备完成:")
            print(f"   - 总行数: {len(values)} (包含表头)")
            print(f"   - 数据行数: {len(values) - 1}")
            self.logger.info(f"✅ 表格数据准备完成:")
            self.logger.info(f"   - 总行数: {len(values)} (包含表头)")
            self.logger.info(f"   - 数据行数: {len(values) - 1}")
            
            # 批量更新数据
            print("\n📤 开始批量更新表格数据")
            self.logger.info(f"📤 开始批量更新表格数据")
            update_url = f"{self.feishu_config['base_url']}/sheets/v2/spreadsheets/{spreadsheet_token}/values_batch_update"
            update_payload = {
                'value_ranges': [{
                    'range': f'{sheet_id}!A1:J{len(values)}',
                    'values': values
                }]
            }
            
            print(f"   - 更新URL: {update_url}")
            print(f"   - 更新范围: {update_payload['value_ranges'][0]['range']}")
            print(f"   - 载荷大小: {len(values)} 行数据")
            self.logger.info(f"   - 更新URL: {update_url}")
            self.logger.info(f"   - 更新范围: {update_payload['value_ranges'][0]['range']}")
            self.logger.info(f"   - 载荷大小: {len(values)} 行数据")
            
            print("\n🌐 发送表格更新请求...")
            self.logger.info(f"🌐 发送表格更新请求...")
            response = requests.post(update_url, headers=headers, json=update_payload)
            print(f"   - 响应状态码: {response.status_code}")
            self.logger.info(f"   - 响应状态码: {response.status_code}")
            response.raise_for_status()
            
            result = response.json()
            print(f"   - 响应结果: code={result.get('code')}, msg={result.get('msg', 'N/A')}")
            self.logger.info(f"   - 响应结果: code={result.get('code')}, msg={result.get('msg', 'N/A')}")
            
            if result.get('code') == 0:
                print(f"\n✅ 成功同步 {len(data)} 条数据到飞书表格")
                print("="*60)
                self.logger.info(f"✅ 成功同步 {len(data)} 条数据到飞书表格")
                return True
            else:
                print(f"\n❌ 飞书表格同步失败: {result.get('msg')}")
                print("="*60)
                self.logger.error(f"❌ 飞书表格同步失败: {result.get('msg')}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"\n❌ [CloudSync] 飞书表格同步网络请求异常详情:")
            print(f"   - 异常类型: {type(e).__name__}")
            print(f"   - 异常模块: {type(e).__module__}")
            print(f"   - 异常消息: {str(e)}")
            print(f"   - 异常参数: {e.args}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   - 响应状态码: {e.response.status_code}")
                print(f"   - 响应状态文本: {e.response.reason}")
                print(f"   - 响应头: {dict(e.response.headers)}")
                print(f"   - 响应内容长度: {len(e.response.text)}")
                print(f"   - 响应内容: {e.response.text[:1000]}...")
            if hasattr(e, 'request') and e.request is not None:
                print(f"   - 请求方法: {e.request.method}")
                print(f"   - 请求URL: {e.request.url}")
                print(f"   - 请求头: {dict(e.request.headers)}")
                if hasattr(e.request, 'body') and e.request.body:
                    print(f"   - 请求体长度: {len(str(e.request.body))}")
                    print(f"   - 请求体内容: {str(e.request.body)[:500]}...")
            print(f"   - 异常堆栈: {traceback.format_exc()}")
            print(f"   - 当前变量状态:")
            print(f"     - data 长度: {len(data) if 'data' in locals() else 'N/A'}")
            print(f"     - spreadsheet_token: {spreadsheet_token if 'spreadsheet_token' in locals() else 'N/A'}")
            print(f"     - sheet_id: {sheet_id if 'sheet_id' in locals() else 'N/A'}")
            print(f"     - access_token 长度: {len(access_token) if 'access_token' in locals() else 'N/A'}")
            print("="*80)
            
            self.logger.error(f"❌ 飞书表格同步网络请求异常:")
            self.logger.error(f"   - 异常类型: {type(e).__name__}")
            self.logger.error(f"   - 异常详情: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                self.logger.error(f"   - 响应状态码: {e.response.status_code}")
                self.logger.error(f"   - 响应内容: {e.response.text[:500]}...")
            return False
        except Exception as e:
            print(f"\n❌ [CloudSync] 飞书表格同步未知异常详情:")
            print(f"   - 异常类型: {type(e).__name__}")
            print(f"   - 异常模块: {type(e).__module__}")
            print(f"   - 异常消息: {str(e)}")
            print(f"   - 异常参数: {e.args}")
            print(f"   - 异常属性: {[attr for attr in dir(e) if not attr.startswith('_')]}")
            print(f"   - 异常堆栈: {traceback.format_exc()}")
            print(f"   - 当前变量状态:")
            print(f"     - data 长度: {len(data) if 'data' in locals() else 'N/A'}")
            print(f"     - spreadsheet_token: {spreadsheet_token if 'spreadsheet_token' in locals() else 'N/A'}")
            print(f"     - sheet_id: {sheet_id if 'sheet_id' in locals() else 'N/A'}")
            print(f"     - access_token 长度: {len(access_token) if 'access_token' in locals() else 'N/A'}")
            print(f"     - values 长度: {len(values) if 'values' in locals() else 'N/A'}")
            print("="*80)
            
            self.logger.error(f"❌ 飞书表格同步过程中发生未知错误:")
            self.logger.error(f"   - 异常类型: {type(e).__name__}")
            self.logger.error(f"   - 异常详情: {str(e)}")
            import traceback
            self.logger.error(f"   - 异常堆栈: {traceback.format_exc()}")
            return False
    
    async def sync_all_platforms(self, data: List[Dict[str, Any]], 
                                sync_config: Dict[str, Any]) -> Dict[str, bool]:
        """
        同步到所有配置的平台
        
        Args:
            data: 要同步的数据
            sync_config: 同步配置
            
        Returns:
            各平台同步结果
        """
        print("\n" + "="*80)
        print("🌐 [CloudSync] 开始多平台同步流程详情")
        print(f"   - 输入参数类型:")
        print(f"     - data 类型: {type(data)}")
        print(f"     - data 长度: {len(data)}")
        print(f"     - sync_config 类型: {type(sync_config)}")
        print(f"     - sync_config 键: {list(sync_config.keys())}")
        print(f"   - 数据详情:")
        for i, item in enumerate(data[:3]):  # 只显示前3条
            print(f"     数据项 {i+1}: {type(item)} - {list(item.keys()) if isinstance(item, dict) else 'N/A'}")
        if len(data) > 3:
            print(f"     ... 还有 {len(data) - 3} 条数据")
        print(f"   - 配置详情:")
        for platform, config in sync_config.items():
            print(f"     {platform}: {type(config)} - enabled={config.get('enabled', False) if isinstance(config, dict) else 'N/A'}")
        print("="*80)
        
        results = {}
        
        # Google Sheets同步
        print("\n🔍 [CloudSync] 检查 Google Sheets 配置...")
        google_config = sync_config.get('google_sheets', {})
        print(f"   - google_config 类型: {type(google_config)}")
        print(f"   - google_config 内容: {google_config}")
        print(f"   - enabled 状态: {google_config.get('enabled', False)}")
        
        if google_config.get('enabled', False):
            print("\n📊 [CloudSync] Google Sheets 同步开始...")
            credentials_file = google_config.get('credentials_file')
            spreadsheet_id = google_config.get('spreadsheet_id')
            worksheet_name = google_config.get('worksheet_name')
            
            print(f"   - 凭证文件: {credentials_file}")
            print(f"   - 表格ID: {spreadsheet_id}")
            print(f"   - 工作表名: {worksheet_name}")
            
            print(f"\n🔧 [CloudSync] 设置 Google Sheets 配置...")
            setup_result = self.setup_google_sheets(credentials_file)
            print(f"   - 配置结果: {setup_result}")
            
            if setup_result:
                print("   - ✅ Google Sheets 配置成功")
                print(f"\n🚀 [CloudSync] 执行 Google Sheets 同步...")
                print(f"   - 传入参数:")
                print(f"     - data 长度: {len(data)}")
                print(f"     - spreadsheet_id: {spreadsheet_id}")
                print(f"     - worksheet_name: {worksheet_name}")
                
                sync_result = self.sync_to_google_sheets(data, spreadsheet_id, worksheet_name)
                results['google_sheets'] = sync_result
                print(f"   - ✅ Google Sheets 同步结果: {'成功' if sync_result else '失败'}")
            else:
                print("   - ❌ Google Sheets 配置失败")
                results['google_sheets'] = False
        else:
            print("\n📊 [CloudSync] Google Sheets 同步已禁用")
            print(f"   - 原因: enabled={google_config.get('enabled', False)}")
        
        # 飞书同步
        print("\n🔍 [CloudSync] 检查飞书配置...")
        feishu_config = sync_config.get('feishu', {})
        print(f"   - feishu_config 类型: {type(feishu_config)}")
        print(f"   - feishu_config 内容: {feishu_config}")
        print(f"   - enabled 状态: {feishu_config.get('enabled', False)}")
        
        if feishu_config.get('enabled', False):
            print("\n🚀 [CloudSync] 飞书同步开始...")
            app_id = feishu_config.get('app_id', '')
            app_secret = feishu_config.get('app_secret', '')
            spreadsheet_token = feishu_config.get('spreadsheet_token', '')
            sheet_id = feishu_config.get('sheet_id')
            
            print(f"   - App ID: {app_id[:10] if app_id else 'N/A'}...")
            print(f"   - App Secret: {app_secret[:10] if app_secret else 'N/A'}...")
            print(f"   - 表格Token: {spreadsheet_token[:10] if spreadsheet_token else 'N/A'}...")
            print(f"   - 工作表ID: {sheet_id}")
            
            print(f"\n🔧 [CloudSync] 设置飞书配置...")
            print(f"   - 传入参数:")
            print(f"     - app_id 长度: {len(app_id) if app_id else 0}")
            print(f"     - app_secret 长度: {len(app_secret) if app_secret else 0}")
            
            setup_result = self.setup_feishu(app_id, app_secret)
            print(f"   - 配置结果: {setup_result}")
            
            if setup_result:
                print("   - ✅ 飞书配置成功")
                print(f"\n🚀 [CloudSync] 执行飞书同步...")
                print(f"   - 传入参数:")
                print(f"     - data 长度: {len(data)}")
                print(f"     - spreadsheet_token: {spreadsheet_token}")
                print(f"     - sheet_id: {sheet_id}")
                
                sync_result = self.sync_to_feishu_sheet(data, spreadsheet_token, sheet_id)
                results['feishu'] = sync_result
                print(f"   - ✅ 飞书同步结果: {'成功' if sync_result else '失败'}")
            else:
                print("   - ❌ 飞书配置失败")
                results['feishu'] = False
        else:
            print("\n🚀 [CloudSync] 飞书同步已禁用")
            print(f"   - 原因: enabled={feishu_config.get('enabled', False)}")
        
        print("\n" + "="*80)
        print("🏁 [CloudSync] 多平台同步完成详情")
        print(f"   - 结果类型: {type(results)}")
        print(f"   - 结果内容: {results}")
        print(f"   - 详细结果分析:")
        
        success_count = 0
        total_count = len(results)
        
        for platform, result in results.items():
            status = "✅ 成功" if result else "❌ 失败"
            print(f"     {platform}: {status} (值: {result}, 类型: {type(result)})")
            if result:
                success_count += 1
        
        print(f"   - 统计信息:")
        print(f"     - 成功平台数: {success_count}")
        print(f"     - 总平台数: {total_count}")
        print(f"     - 成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}% if total_count > 0 else 0)")
        print(f"   - 返回值类型: {type(results)}")
        print(f"   - 返回值内容: {results}")
        print("="*80)
        
        return results

# 使用示例
if __name__ == "__main__":
    # 示例配置
    sync_config = {
        'google_sheets': {
            'enabled': True,
            'credentials_file': 'path/to/google-credentials.json',
            'spreadsheet_id': 'your-google-spreadsheet-id',
            'worksheet_name': 'Twitter数据'
        },
        'feishu': {
            'enabled': True,
            'app_id': 'your-feishu-app-id',
            'app_secret': 'your-feishu-app-secret',
            'spreadsheet_token': 'your-feishu-spreadsheet-token',
            'sheet_id': 'your-sheet-id'  # 可选
        }
    }
    
    # 示例数据
    sample_data = [
        {
            'username': 'elonmusk',
            'content': 'Sample tweet content',
            'timestamp': '2024-01-01 12:00:00',
            'likes': 1000,
            'comments': 100,
            'retweets': 500,
            'link': 'https://twitter.com/elonmusk/status/123',
            'tags': ['AI', 'Technology'],
            'filter_status': 'passed'
        }
    ]
    
    # 创建同步管理器并执行同步
    sync_manager = CloudSyncManager()
    
    async def main():
        results = await sync_manager.sync_all_platforms(sample_data, sync_config)
        print(f"同步结果: {results}")
    
    asyncio.run(main())