#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多账号轮换管理器
管理多个AdsPower账号的轮换使用，提高采集效率和降低风险
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class AccountStatus(Enum):
    """账号状态枚举"""
    AVAILABLE = "available"      # 可用
    IN_USE = "in_use"           # 使用中
    COOLING_DOWN = "cooling_down" # 冷却中
    BLOCKED = "blocked"         # 被封禁
    ERROR = "error"             # 错误状态

@dataclass
class AccountInfo:
    """账号信息数据类"""
    user_id: str
    name: str
    status: AccountStatus
    last_used: Optional[datetime] = None
    usage_count: int = 0
    error_count: int = 0
    cooldown_until: Optional[datetime] = None
    daily_usage_limit: int = 50
    daily_usage_count: int = 0
    last_reset_date: Optional[str] = None
    priority: int = 1  # 优先级，数字越小优先级越高
    notes: str = ""

class AccountManager:
    """
    多账号轮换管理器
    """
    
    def __init__(self, accounts_config: List[Dict[str, Any]]):
        self.logger = logging.getLogger('AccountManager')
        self.accounts: List[AccountInfo] = []
        self.current_account: Optional[AccountInfo] = None
        
        # 配置参数
        self.cooldown_minutes = 30  # 账号使用后的冷却时间（分钟）
        self.max_daily_usage = 50   # 每个账号每日最大使用次数
        self.max_error_count = 3    # 最大错误次数，超过后暂时禁用
        self.rotation_strategy = 'round_robin'  # 轮换策略：round_robin, priority, random
        
        # 初始化账号列表
        self._initialize_accounts(accounts_config)
        
        self.logger.info(f"账号管理器初始化完成，共加载 {len(self.accounts)} 个账号")
    
    def _initialize_accounts(self, accounts_config: List[Dict[str, Any]]):
        """
        初始化账号列表
        
        Args:
            accounts_config: 账号配置列表
        """
        for config in accounts_config:
            account = AccountInfo(
                user_id=config['user_id'],
                name=config.get('name', f"Account_{config['user_id']}"),
                status=AccountStatus.AVAILABLE,
                daily_usage_limit=config.get('daily_limit', self.max_daily_usage),
                priority=config.get('priority', 1),
                notes=config.get('notes', '')
            )
            self.accounts.append(account)
        
        # 按优先级排序
        self.accounts.sort(key=lambda x: x.priority)
    
    def get_available_account(self) -> Optional[AccountInfo]:
        """
        获取可用的账号
        
        Returns:
            可用的账号信息，如果没有可用账号则返回None
        """
        # 更新账号状态
        self._update_account_statuses()
        
        # 筛选可用账号
        available_accounts = [
            account for account in self.accounts 
            if account.status == AccountStatus.AVAILABLE
        ]
        
        if not available_accounts:
            self.logger.warning("没有可用的账号")
            return None
        
        # 根据轮换策略选择账号
        if self.rotation_strategy == 'priority':
            selected_account = min(available_accounts, key=lambda x: x.priority)
        elif self.rotation_strategy == 'random':
            selected_account = random.choice(available_accounts)
        else:  # round_robin
            # 选择使用次数最少的账号
            selected_account = min(available_accounts, key=lambda x: x.usage_count)
        
        return selected_account
    
    def use_account(self, account: AccountInfo) -> bool:
        """
        使用指定账号
        
        Args:
            account: 要使用的账号
            
        Returns:
            是否成功使用账号
        """
        if account.status != AccountStatus.AVAILABLE:
            self.logger.warning(f"账号 {account.name} 不可用，状态: {account.status.value}")
            return False
        
        # 检查日使用限制
        if account.daily_usage_count >= account.daily_usage_limit:
            self.logger.warning(f"账号 {account.name} 已达到日使用限制")
            account.status = AccountStatus.COOLING_DOWN
            account.cooldown_until = datetime.now() + timedelta(hours=24)
            return False
        
        # 标记账号为使用中
        account.status = AccountStatus.IN_USE
        account.last_used = datetime.now()
        account.usage_count += 1
        account.daily_usage_count += 1
        self.current_account = account
        
        self.logger.info(f"开始使用账号: {account.name} (ID: {account.user_id})")
        return True
    
    def release_account(self, account: AccountInfo, success: bool = True):
        """
        释放账号使用
        
        Args:
            account: 要释放的账号
            success: 是否成功完成任务
        """
        if success:
            # 成功完成任务，设置冷却时间
            account.status = AccountStatus.COOLING_DOWN
            account.cooldown_until = datetime.now() + timedelta(minutes=self.cooldown_minutes)
            account.error_count = 0  # 重置错误计数
            self.logger.info(f"账号 {account.name} 任务完成，进入冷却期 {self.cooldown_minutes} 分钟")
        else:
            # 任务失败，增加错误计数
            account.error_count += 1
            if account.error_count >= self.max_error_count:
                account.status = AccountStatus.BLOCKED
                account.cooldown_until = datetime.now() + timedelta(hours=2)  # 错误过多，冷却2小时
                self.logger.warning(f"账号 {account.name} 错误次数过多，暂时禁用2小时")
            else:
                account.status = AccountStatus.COOLING_DOWN
                account.cooldown_until = datetime.now() + timedelta(minutes=self.cooldown_minutes * 2)
                self.logger.warning(f"账号 {account.name} 任务失败，延长冷却时间")
        
        if self.current_account == account:
            self.current_account = None
    
    def _update_account_statuses(self):
        """
        更新所有账号的状态
        """
        current_time = datetime.now()
        current_date = current_time.strftime('%Y-%m-%d')
        
        for account in self.accounts:
            # 重置日使用计数
            if account.last_reset_date != current_date:
                account.daily_usage_count = 0
                account.last_reset_date = current_date
            
            # 检查冷却时间
            if (account.status in [AccountStatus.COOLING_DOWN, AccountStatus.BLOCKED] and 
                account.cooldown_until and current_time >= account.cooldown_until):
                account.status = AccountStatus.AVAILABLE
                account.cooldown_until = None
                self.logger.info(f"账号 {account.name} 冷却完成，重新可用")
    
    def get_account_statistics(self) -> Dict[str, Any]:
        """
        获取账号使用统计
        
        Returns:
            账号统计信息
        """
        self._update_account_statuses()
        
        status_counts = {}
        for status in AccountStatus:
            status_counts[status.value] = sum(1 for account in self.accounts if account.status == status)
        
        total_usage = sum(account.usage_count for account in self.accounts)
        total_daily_usage = sum(account.daily_usage_count for account in self.accounts)
        
        return {
            'total_accounts': len(self.accounts),
            'status_distribution': status_counts,
            'total_usage_count': total_usage,
            'total_daily_usage': total_daily_usage,
            'current_account': self.current_account.name if self.current_account else None,
            'accounts_detail': [
                {
                    'name': account.name,
                    'user_id': account.user_id,
                    'status': account.status.value,
                    'usage_count': account.usage_count,
                    'daily_usage': account.daily_usage_count,
                    'error_count': account.error_count,
                    'last_used': account.last_used.isoformat() if account.last_used else None,
                    'cooldown_until': account.cooldown_until.isoformat() if account.cooldown_until else None
                }
                for account in self.accounts
            ]
        }
    
    def reset_account_errors(self, user_id: str) -> bool:
        """
        重置指定账号的错误计数
        
        Args:
            user_id: 账号ID
            
        Returns:
            是否成功重置
        """
        for account in self.accounts:
            if account.user_id == user_id:
                account.error_count = 0
                if account.status == AccountStatus.BLOCKED:
                    account.status = AccountStatus.AVAILABLE
                    account.cooldown_until = None
                self.logger.info(f"已重置账号 {account.name} 的错误计数")
                return True
        
        self.logger.warning(f"未找到账号 ID: {user_id}")
        return False
    
    def set_account_priority(self, user_id: str, priority: int) -> bool:
        """
        设置账号优先级
        
        Args:
            user_id: 账号ID
            priority: 优先级（数字越小优先级越高）
            
        Returns:
            是否成功设置
        """
        for account in self.accounts:
            if account.user_id == user_id:
                account.priority = priority
                self.logger.info(f"已设置账号 {account.name} 的优先级为 {priority}")
                # 重新排序
                self.accounts.sort(key=lambda x: x.priority)
                return True
        
        self.logger.warning(f"未找到账号 ID: {user_id}")
        return False
    
    def disable_account(self, user_id: str, reason: str = "") -> bool:
        """
        禁用指定账号
        
        Args:
            user_id: 账号ID
            reason: 禁用原因
            
        Returns:
            是否成功禁用
        """
        for account in self.accounts:
            if account.user_id == user_id:
                account.status = AccountStatus.BLOCKED
                account.cooldown_until = datetime.now() + timedelta(days=1)  # 禁用24小时
                if reason:
                    account.notes = f"禁用原因: {reason}"
                self.logger.info(f"已禁用账号 {account.name}，原因: {reason}")
                return True
        
        self.logger.warning(f"未找到账号 ID: {user_id}")
        return False
    
    def enable_account(self, user_id: str) -> bool:
        """
        启用指定账号
        
        Args:
            user_id: 账号ID
            
        Returns:
            是否成功启用
        """
        for account in self.accounts:
            if account.user_id == user_id:
                account.status = AccountStatus.AVAILABLE
                account.cooldown_until = None
                account.error_count = 0
                self.logger.info(f"已启用账号 {account.name}")
                return True
        
        self.logger.warning(f"未找到账号 ID: {user_id}")
        return False
    
    def get_next_available_time(self) -> Optional[datetime]:
        """
        获取下一个账号可用的时间
        
        Returns:
            下一个账号可用的时间，如果有账号立即可用则返回None
        """
        self._update_account_statuses()
        
        available_accounts = [
            account for account in self.accounts 
            if account.status == AccountStatus.AVAILABLE
        ]
        
        if available_accounts:
            return None  # 有账号立即可用
        
        # 找到最早可用的时间
        cooling_accounts = [
            account for account in self.accounts 
            if account.cooldown_until is not None
        ]
        
        if not cooling_accounts:
            return None  # 没有冷却中的账号
        
        return min(account.cooldown_until for account in cooling_accounts)
    
    def wait_for_available_account(self, max_wait_minutes: int = 60) -> Optional[AccountInfo]:
        """
        等待可用账号
        
        Args:
            max_wait_minutes: 最大等待时间（分钟）
            
        Returns:
            可用的账号，如果超时则返回None
        """
        start_time = datetime.now()
        max_wait_time = start_time + timedelta(minutes=max_wait_minutes)
        
        while datetime.now() < max_wait_time:
            account = self.get_available_account()
            if account:
                return account
            
            # 计算下一次检查的时间
            next_available = self.get_next_available_time()
            if next_available:
                wait_seconds = min(
                    (next_available - datetime.now()).total_seconds(),
                    60  # 最多等待60秒后重新检查
                )
                if wait_seconds > 0:
                    self.logger.info(f"等待账号可用，预计 {wait_seconds:.0f} 秒后重试")
                    import time
                    time.sleep(wait_seconds)
            else:
                # 没有冷却中的账号，等待1分钟后重试
                import time
                time.sleep(60)
        
        self.logger.warning(f"等待账号超时（{max_wait_minutes}分钟）")
        return None
    
    def export_account_report(self) -> Dict[str, Any]:
        """
        导出账号使用报告
        
        Returns:
            详细的账号使用报告
        """
        statistics = self.get_account_statistics()
        
        # 计算效率指标
        total_usage = statistics['total_usage_count']
        total_errors = sum(account.error_count for account in self.accounts)
        success_rate = (total_usage - total_errors) / total_usage if total_usage > 0 else 0
        
        # 找出最活跃和最不活跃的账号
        most_active = max(self.accounts, key=lambda x: x.usage_count) if self.accounts else None
        least_active = min(self.accounts, key=lambda x: x.usage_count) if self.accounts else None
        
        return {
            'report_generated_at': datetime.now().isoformat(),
            'summary': statistics,
            'performance_metrics': {
                'total_usage': total_usage,
                'total_errors': total_errors,
                'success_rate': round(success_rate, 3),
                'average_usage_per_account': round(total_usage / len(self.accounts), 2) if self.accounts else 0
            },
            'account_ranking': {
                'most_active': {
                    'name': most_active.name,
                    'usage_count': most_active.usage_count
                } if most_active else None,
                'least_active': {
                    'name': least_active.name,
                    'usage_count': least_active.usage_count
                } if least_active else None
            },
            'recommendations': self._generate_account_recommendations()
        }
    
    def _generate_account_recommendations(self) -> List[str]:
        """
        生成账号管理建议
        
        Returns:
            建议列表
        """
        recommendations = []
        
        # 检查错误率高的账号
        high_error_accounts = [
            account for account in self.accounts 
            if account.error_count >= self.max_error_count - 1
        ]
        if high_error_accounts:
            recommendations.append(f"有 {len(high_error_accounts)} 个账号错误率较高，建议检查账号状态")
        
        # 检查使用不均衡
        if len(self.accounts) > 1:
            usage_counts = [account.usage_count for account in self.accounts]
            max_usage = max(usage_counts)
            min_usage = min(usage_counts)
            if max_usage > min_usage * 3:  # 使用差异超过3倍
                recommendations.append("账号使用不均衡，建议调整轮换策略或账号优先级")
        
        # 检查可用账号数量
        available_count = sum(1 for account in self.accounts if account.status == AccountStatus.AVAILABLE)
        if available_count < len(self.accounts) * 0.5:  # 可用账号少于50%
            recommendations.append("可用账号数量较少，建议增加账号或调整使用频率")
        
        return recommendations
    
    def mark_account_used(self, user_id: str) -> bool:
        """
        标记账号为已使用状态
        
        Args:
            user_id: 账号ID
            
        Returns:
            是否成功标记
        """
        for account in self.accounts:
            if account.user_id == user_id:
                account.status = AccountStatus.IN_USE
                account.last_used = datetime.now()
                account.usage_count += 1
                self.logger.info(f"账号 {account.name} 已标记为使用中")
                return True
        
        self.logger.warning(f"未找到账号 ID: {user_id}")
        return False
    
    def save_accounts(self):
        """
        保存账号状态（占位方法）
        在实际应用中，这里应该将账号状态保存到文件或数据库
        """
        try:
            self.logger.info("保存账号状态...")
            # 这里可以添加实际的保存逻辑，比如保存到JSON文件
            # 目前只是一个占位实现
            self.logger.info(f"已保存 {len(self.accounts)} 个账号的状态")
        except Exception as e:
            self.logger.error(f"保存账号状态失败: {e}")