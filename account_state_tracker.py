#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
账号状态跟踪模块 - 管理推特账号的抓取状态
支持增量抓取、错误恢复、重试机制
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field, asdict
from enum import Enum


class AccountStatus(str, Enum):
    """账号状态枚举"""
    PENDING = "pending"          # 待抓取
    SUCCESS = "success"          # 抓取成功
    FAILED = "failed"            # 抓取失败
    RATE_LIMITED = "rate_limited" # 被限流
    SKIPPED = "skipped"          # 跳过
    RETRYING = "retrying"        # 重试中


@dataclass
class AccountState:
    """账号状态数据模型"""
    username: str
    status: AccountStatus = AccountStatus.PENDING
    
    # 抓取历史
    last_fetched_id: Optional[str] = None
    last_fetched_time: Optional[datetime] = None
    total_tweets_fetched: int = 0
    
    # 错误处理
    last_error: Optional[str] = None
    retry_count: int = 0
    max_retry_count: int = 3
    next_retry_time: Optional[datetime] = None
    
    # 统计信息
    total_attempts: int = 0
    successful_attempts: int = 0
    first_attempt_time: Optional[datetime] = None
    last_attempt_time: Optional[datetime] = None
    
    # 配置
    priority: int = 1  # 优先级，数字越小优先级越高
    enabled: bool = True
    
    def __post_init__(self):
        """初始化后处理"""
        if isinstance(self.status, str):
            self.status = AccountStatus(self.status)
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_attempts == 0:
            return 0.0
        return (self.successful_attempts / self.total_attempts) * 100
    
    @property
    def is_ready_for_retry(self) -> bool:
        """是否准备好重试"""
        if self.status != AccountStatus.FAILED:
            return False
        if self.retry_count >= self.max_retry_count:
            return False
        if self.next_retry_time and datetime.now() < self.next_retry_time:
            return False
        return True
    
    @property
    def should_skip(self) -> bool:
        """是否应该跳过"""
        if not self.enabled:
            return True
        if self.status == AccountStatus.SKIPPED:
            return True
        if self.retry_count >= self.max_retry_count and self.status == AccountStatus.FAILED:
            return True
        return False
    
    def mark_attempt_start(self):
        """标记开始尝试"""
        self.total_attempts += 1
        self.last_attempt_time = datetime.now()
        if self.first_attempt_time is None:
            self.first_attempt_time = self.last_attempt_time
        self.status = AccountStatus.PENDING
    
    def mark_success(self, fetched_id: str = None, tweets_count: int = 0):
        """标记成功"""
        self.status = AccountStatus.SUCCESS
        self.successful_attempts += 1
        self.last_fetched_time = datetime.now()
        self.retry_count = 0  # 重置重试计数
        self.last_error = None
        self.next_retry_time = None
        
        if fetched_id:
            self.last_fetched_id = fetched_id
        if tweets_count > 0:
            self.total_tweets_fetched += tweets_count
    
    def mark_failure(self, error_message: str, retry_delay_minutes: int = 30):
        """标记失败"""
        self.status = AccountStatus.FAILED
        self.last_error = error_message
        self.retry_count += 1
        
        # 计算下次重试时间（指数退避）
        delay_minutes = retry_delay_minutes * (2 ** (self.retry_count - 1))
        self.next_retry_time = datetime.now() + timedelta(minutes=delay_minutes)
    
    def mark_rate_limited(self, retry_delay_minutes: int = 60):
        """标记被限流"""
        self.status = AccountStatus.RATE_LIMITED
        self.last_error = "Rate limited by Twitter"
        self.retry_count += 1
        
        # 限流的重试时间更长
        delay_minutes = retry_delay_minutes * self.retry_count
        self.next_retry_time = datetime.now() + timedelta(minutes=delay_minutes)
    
    def reset_retry_state(self):
        """重置重试状态"""
        self.retry_count = 0
        self.last_error = None
        self.next_retry_time = None
        self.status = AccountStatus.PENDING


class AccountStateTracker:
    """账号状态跟踪器"""
    
    def __init__(self, storage_dir: str = "./data/accounts"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.states_file = self.storage_dir / "account_states.json"
        self.history_file = self.storage_dir / "account_history.json"
        
        self.logger = logging.getLogger(__name__)
        self.account_states: Dict[str, AccountState] = {}
        
        # 加载现有状态
        self.load_states()
    
    def get_account_state(self, username: str) -> AccountState:
        """
        获取账号状态，如果不存在则创建新的
        
        Args:
            username: 用户名
            
        Returns:
            账号状态对象
        """
        if username not in self.account_states:
            self.account_states[username] = AccountState(username=username)
            self.logger.debug(f"为用户 @{username} 创建新的状态记录")
        
        return self.account_states[username]
    
    def update_account_state(self, username: str, **kwargs):
        """
        更新账号状态
        
        Args:
            username: 用户名
            **kwargs: 要更新的字段
        """
        state = self.get_account_state(username)
        
        for key, value in kwargs.items():
            if hasattr(state, key):
                setattr(state, key, value)
            else:
                self.logger.warning(f"账号状态不存在字段: {key}")
        
        self.logger.debug(f"更新用户 @{username} 的状态: {kwargs}")
    
    def mark_attempt_start(self, username: str):
        """标记开始抓取尝试"""
        state = self.get_account_state(username)
        state.mark_attempt_start()
        self.logger.info(f"开始抓取用户 @{username}，第 {state.total_attempts} 次尝试")
    
    def mark_success(self, username: str, fetched_id: str = None, tweets_count: int = 0):
        """标记抓取成功"""
        state = self.get_account_state(username)
        state.mark_success(fetched_id, tweets_count)
        self.logger.info(f"用户 @{username} 抓取成功，获得 {tweets_count} 条推文")
        
        # 记录历史
        self._record_history(username, "success", {
            "tweets_count": tweets_count,
            "fetched_id": fetched_id
        })
    
    def mark_failure(self, username: str, error_message: str, retry_delay_minutes: int = 30):
        """标记抓取失败"""
        state = self.get_account_state(username)
        state.mark_failure(error_message, retry_delay_minutes)
        
        self.logger.warning(f"用户 @{username} 抓取失败 (第{state.retry_count}次): {error_message}")
        if state.next_retry_time:
            self.logger.info(f"下次重试时间: {state.next_retry_time}")
        
        # 记录历史
        self._record_history(username, "failure", {
            "error_message": error_message,
            "retry_count": state.retry_count
        })
    
    def mark_rate_limited(self, username: str, retry_delay_minutes: int = 60):
        """标记被限流"""
        state = self.get_account_state(username)
        state.mark_rate_limited(retry_delay_minutes)
        
        self.logger.warning(f"用户 @{username} 被限流，下次重试时间: {state.next_retry_time}")
        
        # 记录历史
        self._record_history(username, "rate_limited", {
            "retry_delay_minutes": retry_delay_minutes
        })
    
    def get_ready_accounts(self, max_count: int = None) -> List[str]:
        """
        获取准备好抓取的账号列表
        
        Args:
            max_count: 最大返回数量
            
        Returns:
            准备好的账号用户名列表
        """
        ready_accounts = []
        
        # 按优先级排序
        sorted_accounts = sorted(
            self.account_states.items(),
            key=lambda x: (x[1].priority, x[1].last_attempt_time or datetime.min)
        )
        
        for username, state in sorted_accounts:
            if state.should_skip:
                continue
            
            # 检查是否准备好
            if state.status == AccountStatus.PENDING or state.is_ready_for_retry:
                ready_accounts.append(username)
                
                if max_count and len(ready_accounts) >= max_count:
                    break
        
        return ready_accounts
    
    def get_failed_accounts(self) -> List[str]:
        """获取失败的账号列表"""
        return [
            username for username, state in self.account_states.items()
            if state.status == AccountStatus.FAILED
        ]
    
    def get_rate_limited_accounts(self) -> List[str]:
        """获取被限流的账号列表"""
        return [
            username for username, state in self.account_states.items()
            if state.status == AccountStatus.RATE_LIMITED
        ]
    
    def reset_account_state(self, username: str):
        """重置账号状态"""
        if username in self.account_states:
            state = self.account_states[username]
            state.reset_retry_state()
            self.logger.info(f"重置用户 @{username} 的状态")
        else:
            self.logger.warning(f"用户 @{username} 不存在，无法重置状态")
    
    def disable_account(self, username: str):
        """禁用账号"""
        state = self.get_account_state(username)
        state.enabled = False
        state.status = AccountStatus.SKIPPED
        self.logger.info(f"禁用用户 @{username}")
    
    def enable_account(self, username: str):
        """启用账号"""
        state = self.get_account_state(username)
        state.enabled = True
        if state.status == AccountStatus.SKIPPED:
            state.status = AccountStatus.PENDING
        self.logger.info(f"启用用户 @{username}")
    
    def set_account_priority(self, username: str, priority: int):
        """设置账号优先级"""
        state = self.get_account_state(username)
        state.priority = priority
        self.logger.info(f"设置用户 @{username} 的优先级为 {priority}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_accounts = len(self.account_states)
        if total_accounts == 0:
            return {"total_accounts": 0}
        
        status_counts = {}
        for status in AccountStatus:
            status_counts[status.value] = sum(
                1 for state in self.account_states.values()
                if state.status == status
            )
        
        total_tweets = sum(state.total_tweets_fetched for state in self.account_states.values())
        total_attempts = sum(state.total_attempts for state in self.account_states.values())
        successful_attempts = sum(state.successful_attempts for state in self.account_states.values())
        
        return {
            "total_accounts": total_accounts,
            "status_distribution": status_counts,
            "total_tweets_fetched": total_tweets,
            "total_attempts": total_attempts,
            "successful_attempts": successful_attempts,
            "overall_success_rate": (successful_attempts / total_attempts * 100) if total_attempts > 0 else 0,
            "average_tweets_per_account": total_tweets / total_accounts,
            "ready_for_retry": len(self.get_ready_accounts()),
            "failed_accounts": len(self.get_failed_accounts()),
            "rate_limited_accounts": len(self.get_rate_limited_accounts())
        }
    
    def save_states(self):
        """保存状态到文件"""
        try:
            # 转换为可序列化的格式
            serializable_states = {}
            for username, state in self.account_states.items():
                state_dict = asdict(state)
                # 处理datetime对象
                for key, value in state_dict.items():
                    if isinstance(value, datetime):
                        state_dict[key] = value.isoformat()
                    elif isinstance(value, AccountStatus):
                        state_dict[key] = value.value
                serializable_states[username] = state_dict
            
            # 保存到文件
            save_data = {
                "updated_at": datetime.now().isoformat(),
                "total_accounts": len(self.account_states),
                "account_states": serializable_states
            }
            
            with open(self.states_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            self.logger.debug(f"账号状态已保存到: {self.states_file}")
            
        except Exception as e:
            self.logger.error(f"保存账号状态失败: {e}")
    
    def load_states(self):
        """从文件加载状态"""
        try:
            if not self.states_file.exists():
                self.logger.info("账号状态文件不存在，使用空状态")
                return
            
            with open(self.states_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            account_states_data = data.get("account_states", {})
            
            for username, state_dict in account_states_data.items():
                # 处理datetime字段
                for key in ['last_fetched_time', 'next_retry_time', 'first_attempt_time', 'last_attempt_time']:
                    if state_dict.get(key):
                        try:
                            state_dict[key] = datetime.fromisoformat(state_dict[key])
                        except ValueError:
                            state_dict[key] = None
                
                # 处理枚举字段
                if 'status' in state_dict:
                    try:
                        state_dict['status'] = AccountStatus(state_dict['status'])
                    except ValueError:
                        state_dict['status'] = AccountStatus.PENDING
                
                # 创建AccountState对象
                self.account_states[username] = AccountState(**state_dict)
            
            self.logger.info(f"加载了 {len(self.account_states)} 个账号的状态")
            
        except Exception as e:
            self.logger.error(f"加载账号状态失败: {e}")
            self.account_states = {}
    
    def _record_history(self, username: str, event_type: str, details: Dict[str, Any]):
        """记录历史事件"""
        try:
            history_entry = {
                "timestamp": datetime.now().isoformat(),
                "username": username,
                "event_type": event_type,
                "details": details
            }
            
            # 读取现有历史
            history = []
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            
            # 添加新记录
            history.append(history_entry)
            
            # 保持最近1000条记录
            if len(history) > 1000:
                history = history[-1000:]
            
            # 保存历史
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            self.logger.error(f"记录历史事件失败: {e}")
    
    def get_account_history(self, username: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取账号历史记录"""
        try:
            if not self.history_file.exists():
                return []
            
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            # 过滤特定用户
            if username:
                history = [entry for entry in history if entry.get("username") == username]
            
            # 返回最近的记录
            return history[-limit:] if limit else history
            
        except Exception as e:
            self.logger.error(f"获取账号历史失败: {e}")
            return []
    
    def cleanup_old_history(self, days_to_keep: int = 30):
        """清理旧的历史记录"""
        try:
            if not self.history_file.exists():
                return
            
            cutoff_time = datetime.now() - timedelta(days=days_to_keep)
            
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            # 过滤旧记录
            filtered_history = []
            for entry in history:
                try:
                    entry_time = datetime.fromisoformat(entry["timestamp"])
                    if entry_time >= cutoff_time:
                        filtered_history.append(entry)
                except (ValueError, KeyError):
                    # 保留无法解析时间的记录
                    filtered_history.append(entry)
            
            # 保存过滤后的历史
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(filtered_history, f, ensure_ascii=False, indent=2)
            
            removed_count = len(history) - len(filtered_history)
            self.logger.info(f"清理了 {removed_count} 条旧历史记录")
            
        except Exception as e:
            self.logger.error(f"清理历史记录失败: {e}")