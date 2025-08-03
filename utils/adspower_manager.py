# -*- coding: utf-8 -*-
"""
AdsPower 管理器
提供多用户支持、配置检测和统一管理功能
"""

import json
import os
import requests
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class AdsPowerConfig:
    """AdsPower配置数据类"""
    host: str = "localhost"
    port: int = 50325
    headless: bool = False
    user_ids: List[str] = None
    api_key: str = ""
    
    def __post_init__(self):
        if self.user_ids is None:
            self.user_ids = []
    
    @property
    def api_url(self) -> str:
        """获取API基础URL"""
        return f"http://{self.host}:{self.port}"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AdsPowerConfig':
        """从字典创建配置"""
        return cls(**data)


class AdsPowerManager:
    """AdsPower管理器 - 支持多用户和配置检测"""
    
    def __init__(self, config: Optional[AdsPowerConfig] = None):
        self.config = config or AdsPowerConfig()
        self.logger = logging.getLogger(__name__)
        self.active_browsers: Dict[str, Dict[str, Any]] = {}
        self.config_file_path = "./config/adspower_config.json"
        
        # 确保配置目录存在
        os.makedirs(os.path.dirname(self.config_file_path), exist_ok=True)
        
        # 只有在没有传入配置时才加载配置文件
        if config is None:
            self.load_config_from_file()
    
    def load_config_from_file(self) -> bool:
        """从配置文件加载配置"""
        try:
            if os.path.exists(self.config_file_path):
                with open(self.config_file_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    self.config = AdsPowerConfig.from_dict(config_data)
                    self.logger.info(f"已加载AdsPower配置: {len(self.config.user_ids)}个用户ID")
                    return True
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
        return False
    
    def save_config_to_file(self) -> bool:
        """保存配置到文件"""
        try:
            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.config.to_dict(), f, ensure_ascii=False, indent=2)
                self.logger.info("AdsPower配置已保存")
                return True
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {e}")
            return False
    
    def update_config(self, **kwargs) -> bool:
        """更新配置"""
        try:
            for key, value in kwargs.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
            return self.save_config_to_file()
        except Exception as e:
            self.logger.error(f"更新配置失败: {e}")
            return False
    
    def is_adspower_available(self) -> Tuple[bool, str]:
        """检查AdsPower是否可用"""
        try:
            # 检查状态接口
            status_url = f"{self.config.api_url}/status"
            headers = {}
            if self.config.api_key:
                headers['Authorization'] = f'Bearer {self.config.api_key}'
            
            response = requests.get(status_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    return True, "AdsPower运行正常"
                else:
                    return False, f"AdsPower状态异常: {result.get('msg', '未知错误')}"
            else:
                return False, f"HTTP错误: {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            return False, f"连接失败: 无法连接到 {self.config.api_url}，请确保AdsPower已启动"
        except requests.exceptions.Timeout:
            return False, "连接超时: AdsPower响应超时"
        except Exception as e:
            return False, f"检查失败: {str(e)}"
    
    def get_user_list(self) -> Tuple[bool, List[Dict[str, Any]], str]:
        """获取用户列表"""
        try:
            list_url = f"{self.config.api_url}/api/v1/user/list"
            headers = {}
            if self.config.api_key:
                headers['Authorization'] = f'Bearer {self.config.api_key}'
            
            response = requests.get(list_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    users = result.get('data', {}).get('list', [])
                    return True, users, "获取用户列表成功"
                else:
                    return False, [], f"API错误: {result.get('msg', '未知错误')}"
            else:
                return False, [], f"HTTP错误: {response.status_code}"
                
        except Exception as e:
            return False, [], f"获取用户列表失败: {str(e)}"
    
    def check_browser_status(self, user_id: str) -> Tuple[bool, Dict[str, Any], str]:
        """检查指定用户的浏览器状态
        
        Args:
            user_id: 用户ID
            
        Returns:
            Tuple[bool, Dict[str, Any], str]: (成功状态, 状态数据, 消息)
        """
        try:
            status_url = f"{self.config.api_url}/api/v1/browser/active"
            params = {'user_id': user_id}
            headers = {}
            if self.config.api_key:
                headers['Authorization'] = f'Bearer {self.config.api_key}'
            
            response = requests.get(status_url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    data = result.get('data', {})
                    return True, data, "状态检查成功"
                else:
                    return False, {}, f"API错误: {result.get('msg', '未知错误')}"
            else:
                return False, {}, f"HTTP错误: {response.status_code}"
                
        except Exception as e:
            return False, {}, f"状态检查失败: {str(e)}"
    
    def get_local_active_browsers(self) -> Tuple[bool, List[Dict[str, Any]], str]:
        """获取当前设备所有已启动的浏览器
        
        Returns:
            Tuple[bool, List[Dict[str, Any]], str]: (成功状态, 浏览器列表, 消息)
        """
        try:
            active_url = f"{self.config.api_url}/api/v1/browser/local-active"
            headers = {}
            if self.config.api_key:
                headers['Authorization'] = f'Bearer {self.config.api_key}'
            
            response = requests.get(active_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    browsers = result.get('data', {}).get('list', [])
                    return True, browsers, "获取活跃浏览器成功"
                else:
                    return False, [], f"API错误: {result.get('msg', '未知错误')}"
            else:
                return False, [], f"HTTP错误: {response.status_code}"
                
        except Exception as e:
            return False, [], f"获取活跃浏览器失败: {str(e)}"
    
    def validate_user_ids(self) -> Tuple[bool, List[str], List[str]]:
        """验证配置的用户ID是否存在
        
        优化后的验证逻辑：
        1. 首先尝试通过browser/active API检查每个用户ID
        2. 如果失败，回退到user/list API
        """
        valid_ids = []
        invalid_ids = []
        
        # 方法1：通过browser/active API逐个检查用户ID
        for user_id in self.config.user_ids:
            success, data, message = self.check_browser_status(user_id)
            if success:
                # 用户ID存在（无论浏览器是否启动）
                valid_ids.append(user_id)
            else:
                # 检查错误消息，如果是用户不存在的错误
                if "用户" in message or "user" in message.lower() or "not found" in message.lower():
                    invalid_ids.append(user_id)
                else:
                    # 其他错误，可能是网络问题，回退到user/list方法
                    break
        
        # 如果所有用户ID都检查完毕，返回结果
        if len(valid_ids) + len(invalid_ids) == len(self.config.user_ids):
            return True, valid_ids, invalid_ids
        
        # 方法2：回退到原有的user/list API方法
        success, users, message = self.get_user_list()
        if not success:
            return False, [], [message]
        
        existing_user_ids = [user.get('user_id', '') for user in users]
        valid_ids = []
        invalid_ids = []
        
        for user_id in self.config.user_ids:
            if user_id in existing_user_ids:
                valid_ids.append(user_id)
            else:
                invalid_ids.append(user_id)
        
        return True, valid_ids, invalid_ids
    
    def launch_browser_by_user_id(self, user_id: str, **kwargs) -> Tuple[bool, Dict[str, Any], str]:
        """启动指定用户ID的浏览器"""
        try:
            start_url = f"{self.config.api_url}/api/v1/browser/start"
            params = {
                'user_id': user_id,
                'headless': kwargs.get('headless', self.config.headless)
            }
            
            headers = {}
            if self.config.api_key:
                headers['Authorization'] = f'Bearer {self.config.api_key}'
            
            response = requests.get(start_url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    browser_info = result.get('data', {})
                    self.active_browsers[user_id] = {
                        'browser_info': browser_info,
                        'started_at': time.time(),
                        'status': 'running'
                    }
                    return True, browser_info, f"用户 {user_id} 浏览器启动成功"
                else:
                    return False, {}, f"启动失败: {result.get('msg', '未知错误')}"
            else:
                return False, {}, f"HTTP错误: {response.status_code}"
                
        except Exception as e:
            return False, {}, f"启动浏览器失败: {str(e)}"
    
    def stop_browser_by_user_id(self, user_id: str) -> Tuple[bool, str]:
        """停止指定用户ID的浏览器"""
        try:
            stop_url = f"{self.config.api_url}/api/v1/browser/stop"
            params = {'user_id': user_id}
            
            headers = {}
            if self.config.api_key:
                headers['Authorization'] = f'Bearer {self.config.api_key}'
            
            response = requests.get(stop_url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    if user_id in self.active_browsers:
                        del self.active_browsers[user_id]
                    return True, f"用户 {user_id} 浏览器停止成功"
                else:
                    return False, f"停止失败: {result.get('msg', '未知错误')}"
            else:
                return False, f"HTTP错误: {response.status_code}"
                
        except Exception as e:
            return False, f"停止浏览器失败: {str(e)}"
    
    def launch_all_browsers(self, **kwargs) -> Dict[str, Tuple[bool, str]]:
        """启动所有配置的用户浏览器"""
        results = {}
        
        if not self.config.user_ids:
            return {'error': (False, "没有配置用户ID")}
        
        # 使用线程池并发启动
        with ThreadPoolExecutor(max_workers=min(len(self.config.user_ids), 3)) as executor:
            future_to_user = {
                executor.submit(self.launch_browser_by_user_id, user_id, **kwargs): user_id 
                for user_id in self.config.user_ids
            }
            
            for future in as_completed(future_to_user):
                user_id = future_to_user[future]
                try:
                    success, browser_info, message = future.result()
                    results[user_id] = (success, message)
                except Exception as e:
                    results[user_id] = (False, f"启动异常: {str(e)}")
        
        return results
    
    def stop_all_browsers(self) -> Dict[str, Tuple[bool, str]]:
        """停止所有活动的浏览器"""
        results = {}
        
        if not self.active_browsers:
            return {'info': (True, "没有活动的浏览器")}
        
        for user_id in list(self.active_browsers.keys()):
            success, message = self.stop_browser_by_user_id(user_id)
            results[user_id] = (success, message)
        
        return results
    
    def get_browser_status(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """获取浏览器状态"""
        if user_id:
            return self.active_browsers.get(user_id, {'status': 'stopped'})
        else:
            return {
                'total_browsers': len(self.active_browsers),
                'active_browsers': list(self.active_browsers.keys()),
                'browsers': self.active_browsers
            }
    
    def perform_health_check(self) -> Dict[str, Any]:
        """执行完整的健康检查"""
        health_report = {
            'timestamp': time.time(),
            'adspower_available': False,
            'user_validation': {
                'valid_ids': [],
                'invalid_ids': [],
                'total_configured': len(self.config.user_ids)
            },
            'active_browsers': [],
            'browser_status': {},
            'diagnosis': {
                'api_enabled_check': False,
                'tried_hosts': [],
                'suggestions': []
            },
            'recommendations': [],
            'status': 'unknown',
            'message': ''
        }
        
        # 1. 检查AdsPower可用性
        available, message = self.is_adspower_available()
        health_report['adspower_available'] = available
        health_report['message'] = message
        health_report['diagnosis']['api_enabled_check'] = available
        
        if not available:
            health_report['status'] = 'error'
            health_report['recommendations'].append('请启动AdsPower应用程序')
            health_report['diagnosis']['tried_hosts'].append(f"{self.config.host}:{self.config.port}")
            
            if 'localhost' in self.config.host or '127.0.0.1' in self.config.host:
                health_report['recommendations'].append('如尚未安装AdsPower，请点击下载')
                health_report['diagnosis']['suggestions'].append('检查AdsPower是否已启动')
                health_report['diagnosis']['suggestions'].append('确认本地API服务已开启（端口50325）')
            else:
                health_report['diagnosis']['suggestions'].append('检查远程AdsPower服务器连接')
                health_report['diagnosis']['suggestions'].append('验证API地址和端口配置')
            
            return health_report
        
        # 2. 获取活跃浏览器信息
        success, active_browsers, _ = self.get_local_active_browsers()
        if success:
            health_report['active_browsers'] = active_browsers
            active_user_ids = [browser.get('user_id') for browser in active_browsers]
            health_report['diagnosis']['suggestions'].append(f'当前有{len(active_browsers)}个活跃浏览器')
        
        # 3. 验证用户ID
        if self.config.user_ids:
            success, valid_ids, invalid_ids = self.validate_user_ids()
            if success:
                health_report['user_validation']['valid_ids'] = valid_ids
                health_report['user_validation']['invalid_ids'] = invalid_ids
                
                # 检查每个用户ID的浏览器状态
                for user_id in valid_ids:
                    status_success, status_data, status_msg = self.check_browser_status(user_id)
                    if status_success:
                        browser_status = status_data.get('status', 'Unknown')
                        health_report['browser_status'][user_id] = {
                            'status': browser_status,
                            'active': browser_status == 'Active'
                        }
                        if 'ws' in status_data:
                            health_report['browser_status'][user_id]['ws'] = status_data['ws']
                
                if invalid_ids:
                    health_report['recommendations'].append(f'用户ID验证失败，以下用户ID不存在: {", ".join(invalid_ids)}')
                    health_report['diagnosis']['suggestions'].append('请在AdsPower中创建对应的用户配置')
                    health_report['diagnosis']['suggestions'].append('或更新配置文件中的用户ID列表')
                
                if valid_ids:
                    active_count = sum(1 for uid in valid_ids if health_report['browser_status'].get(uid, {}).get('active', False))
                    health_report['diagnosis']['suggestions'].append(f'{len(valid_ids)}个有效用户ID中，{active_count}个浏览器处于活跃状态')
        else:
            health_report['recommendations'].append('请配置至少一个用户ID')
            health_report['diagnosis']['suggestions'].append('在config/adspower_config.py中添加用户ID')
        
        # 4. 确定整体状态
        if health_report['adspower_available'] and health_report['user_validation']['valid_ids']:
            if health_report['user_validation']['invalid_ids']:
                health_report['status'] = 'warning'
                health_report['message'] = f"AdsPower连接正常，但有{len(health_report['user_validation']['invalid_ids'])}个用户ID无效"
            else:
                health_report['status'] = 'healthy'
                health_report['message'] = f"AdsPower环境健康，{len(health_report['user_validation']['valid_ids'])}个用户ID全部有效"
        elif health_report['adspower_available']:
            health_report['status'] = 'warning'
            health_report['message'] = "AdsPower连接正常，但用户ID配置有问题"
        else:
            health_report['status'] = 'error'
            health_report['message'] = "无法连接到AdsPower服务"
        
        return health_report
    
    def get_download_url(self) -> str:
        """获取AdsPower下载链接"""
        return "https://www.adspower.net/share/hftJaRHMQl1r7jw"


# 全局实例
_adspower_manager = None


def get_adspower_manager() -> AdsPowerManager:
    """获取全局AdsPower管理器实例"""
    global _adspower_manager
    if _adspower_manager is None:
        _adspower_manager = AdsPowerManager()
    return _adspower_manager


def init_adspower_manager(config: Optional[AdsPowerConfig] = None) -> AdsPowerManager:
    """初始化AdsPower管理器"""
    global _adspower_manager
    _adspower_manager = AdsPowerManager(config)
    return _adspower_manager


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    # 创建测试配置
    config = AdsPowerConfig(
        host="localhost",
        port=50325,
        user_ids=["test_user_1", "test_user_2"]
    )
    
    manager = AdsPowerManager(config)
    
    print("=== AdsPower管理器测试 ===")
    
    # 健康检查
    print("\n1. 执行健康检查...")
    health = manager.perform_health_check()
    print(f"状态: {health['status']}")
    print(f"消息: {health['message']}")
    print(f"建议: {health['recommendations']}")
    
    # 检查可用性
    print("\n2. 检查AdsPower可用性...")
    available, message = manager.is_adspower_available()
    print(f"可用: {available}, 消息: {message}")
    
    if available:
        # 获取用户列表
        print("\n3. 获取用户列表...")
        success, users, msg = manager.get_user_list()
        if success:
            print(f"找到 {len(users)} 个用户")
            for user in users[:3]:  # 只显示前3个
                print(f"  - {user.get('user_id', 'N/A')}: {user.get('name', 'N/A')}")
        else:
            print(f"获取失败: {msg}")