#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AdsPower 管理器模块
提供 AdsPower 浏览器的统一管理功能，包括多用户支持、配置检测和环境验证
"""

import json
import os
import requests
import logging
import subprocess
import platform
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


@dataclass
class AdsPowerConfig:
    """AdsPower 配置数据类"""
    host: str = "localhost"
    port: int = 50325
    headless: bool = False
    user_ids: List[str] = None
    api_key: str = ""
    
    def __post_init__(self):
        if self.user_ids is None:
            self.user_ids = []


class AdsPowerManager:
    """AdsPower 管理器
    
    提供 AdsPower 浏览器的统一管理功能：
    - 配置管理
    - 环境检测
    - 多用户支持
    - 浏览器启动/停止
    """
    
    def __init__(self, config_file: str = "adspower_config.json"):
        """初始化 AdsPower 管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.logger = logging.getLogger(__name__)
        self._config: Optional[AdsPowerConfig] = None
    
    def load_config(self) -> AdsPowerConfig:
        """加载配置文件
        
        Returns:
            AdsPowerConfig: 配置对象
        """
        if self._config is not None:
            return self._config
            
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._config = AdsPowerConfig(
                        host=data.get('host', 'localhost'),
                        port=data.get('port', 50325),
                        headless=data.get('headless', False),
                        user_ids=data.get('user_ids', []),
                        api_key=data.get('api_key', '')
                    )
            else:
                # 创建默认配置
                self._config = AdsPowerConfig()
                self.save_config(self._config)
                
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
            self._config = AdsPowerConfig()
            
        return self._config
    
    def save_config(self, config: AdsPowerConfig) -> bool:
        """保存配置到文件
        
        Args:
            config: 配置对象
            
        Returns:
            bool: 是否保存成功
        """
        try:
            data = {
                'host': config.host,
                'port': config.port,
                'headless': config.headless,
                'user_ids': config.user_ids,
                'api_key': config.api_key
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self._config = config
            self.logger.info(f"配置已保存到 {self.config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {e}")
            return False
    
    def check_availability(self) -> Tuple[bool, str]:
        """检查 AdsPower 是否可用
        
        Returns:
            Tuple[bool, str]: (是否可用, 消息)
        """
        config = self.load_config()
        return self.check_adspower_alive(config.host, config.port)
    
    def check_adspower_alive(self, host: str, port: int) -> Tuple[bool, str]:
        """检查 AdsPower 是否运行（支持多主机尝试）
        
        Args:
            host: 主机地址
            port: 端口号
            
        Returns:
            Tuple[bool, str]: (是否可用, 消息)
        """
        # 构建要尝试的URL列表 - 使用正确的AdsPower API端点
        base_urls = [f"http://{host}:{port}"]
        if host == "localhost":
            base_urls.append(f"http://127.0.0.1:{port}")
        elif host == "127.0.0.1":
            base_urls.append(f"http://localhost:{port}")
        
        last_error = None
        
        for base_url in base_urls:
            # 使用正确的AdsPower API端点
            test_url = f"{base_url}/api/v1/user/list"
            try:
                # 准备请求头
                headers = {}
                config = self.load_config()
                if config.api_key:
                    headers['Authorization'] = f'Bearer {config.api_key}'
                
                response = requests.get(test_url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if data.get('code') == 0:
                            return True, f"AdsPower 运行正常 ({base_url})"
                        else:
                            return False, f"AdsPower API返回错误: {data.get('msg', '未知错误')} ({base_url})"
                    except ValueError:
                        return False, f"端口 {port} 被其他服务占用 ({base_url})"
                elif response.status_code == 401:
                    return False, f"API Key验证失败，请检查API Key是否正确 ({base_url})"
                else:
                    last_error = f"HTTP错误: {response.status_code} ({base_url})"
                    
            except requests.exceptions.ConnectionError as e:
                last_error = f"连接被拒绝: {base_url} - 请确保AdsPower已启动并开启本地API服务"
                self.logger.warning(f"AdsPower 连接失败: {test_url}, 错误: {e}")
            except requests.exceptions.Timeout as e:
                last_error = f"连接超时: {base_url} - AdsPower响应超时"
                self.logger.warning(f"AdsPower 连接失败: {test_url}, 错误: {e}")
            except Exception as e:
                last_error = f"连接错误: {base_url} - {type(e).__name__}: {str(e)}"
                self.logger.warning(f"AdsPower 连接失败: {test_url}, 错误: {e}")
        
        return False, last_error or f"无法连接到 AdsPower ({host}:{port})，请检查 AdsPower 是否已启动并开启本地API服务"
    
    def get_user_list(self) -> List[Dict[str, Any]]:
        """获取用户列表
        
        Returns:
            List[Dict[str, Any]]: 用户列表
        """
        try:
            config = self.load_config()
            base_url = f"http://{config.host}:{config.port}"
            
            headers = {}
            if config.api_key:
                headers['Authorization'] = f'Bearer {config.api_key}'
            
            response = requests.get(
                f"{base_url}/api/v1/user/list",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    return data.get('data', {}).get('list', [])
                else:
                    self.logger.error(f"获取用户列表失败: {data.get('msg', '未知错误')}")
                    return []
            else:
                self.logger.error(f"获取用户列表失败，状态码: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"获取用户列表时发生错误: {e}")
            return []
    
    def get_valid_user_ids(self, user_ids: List[str]) -> List[str]:
        """获取有效的用户ID列表
        
        Args:
            user_ids: 要验证的用户ID列表
            
        Returns:
            List[str]: 有效的用户ID列表
        """
        if not user_ids:
            return []
            
        users = self.get_user_list()
        existing_user_ids = {user.get('user_id') for user in users}
        
        return [uid for uid in user_ids if uid in existing_user_ids]
    
    def validate_user_id(self, user_id: str) -> bool:
        """验证单个用户ID是否有效
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 是否有效
        """
        return len(self.get_valid_user_ids([user_id])) > 0
    
    def start_browser(self, user_id: str) -> Optional[webdriver.Chrome]:
        """启动指定用户的浏览器
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[webdriver.Chrome]: 浏览器驱动实例
        """
        try:
            config = self.load_config()
            base_url = f"http://{config.host}:{config.port}"
            
            # 启动浏览器
            start_url = f"{base_url}/api/v1/browser/start"
            params = {'user_id': user_id}
            
            response = requests.get(start_url, params=params, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    data = result.get('data', {})
                    ws_endpoint = data.get('ws', {}).get('selenium')
                    
                    if ws_endpoint:
                        # 连接到现有浏览器实例
                        options = Options()
                        
                        # 解析 WebSocket 端点
                        if 'ws://' in ws_endpoint:
                            debug_address = ws_endpoint.replace('ws://', '').split('/')[0]
                            options.add_experimental_option("debuggerAddress", debug_address)
                        else:
                            # 备用方法
                            chrome_driver = data.get('webdriver')
                            if chrome_driver:
                                options.add_experimental_option("debuggerAddress", chrome_driver)
                        
                        # 设置无头模式
                        if config.headless:
                            options.add_argument('--headless')
                        
                        driver = webdriver.Chrome(options=options)
                        self.logger.info(f"浏览器启动成功，用户ID: {user_id}")
                        return driver
                    else:
                        self.logger.error(f"未获取到 WebSocket 端点，用户ID: {user_id}")
                        return None
                else:
                    self.logger.error(f"启动浏览器失败: {result.get('msg', '未知错误')}，用户ID: {user_id}")
                    return None
            else:
                self.logger.error(f"API 请求失败，状态码: {response.status_code}，用户ID: {user_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"启动浏览器时发生错误: {e}，用户ID: {user_id}")
            return None
    
    def stop_browser(self, user_id: str) -> bool:
        """停止指定用户的浏览器
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 是否停止成功
        """
        try:
            config = self.load_config()
            base_url = f"http://{config.host}:{config.port}"
            
            stop_url = f"{base_url}/api/v1/browser/stop"
            params = {'user_id': user_id}
            
            response = requests.get(stop_url, params=params, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    self.logger.info(f"浏览器停止成功，用户ID: {user_id}")
                    return True
                else:
                    self.logger.error(f"停止浏览器失败: {result.get('msg', '未知错误')}，用户ID: {user_id}")
                    return False
            else:
                self.logger.error(f"API 请求失败，状态码: {response.status_code}，用户ID: {user_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"停止浏览器时发生错误: {e}，用户ID: {user_id}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """执行健康检查
        
        Returns:
            Dict[str, Any]: 健康检查结果
        """
        result = {
            'adspower_available': False,
            'config_valid': False,
            'user_ids_valid': [],
            'user_ids_invalid': [],
            'message': ''
        }
        
        try:
            # 检查 AdsPower 可用性
            is_available, message = self.check_availability()
            result['adspower_available'] = is_available
            result['message'] = message
            
            if not is_available:
                return result
            
            # 检查配置
            config = self.load_config()
            result['config_valid'] = True
            
            # 检查用户ID
            if config.user_ids:
                valid_ids = self.get_valid_user_ids(config.user_ids)
                invalid_ids = [uid for uid in config.user_ids if uid not in valid_ids]
                
                result['user_ids_valid'] = valid_ids
                result['user_ids_invalid'] = invalid_ids
                
                if invalid_ids:
                    result['message'] += f" 无效用户ID: {', '.join(invalid_ids)}"
                else:
                    result['message'] = f"健康检查通过，{len(valid_ids)} 个用户ID可用"
            else:
                result['message'] += " 未配置用户ID"
                
        except Exception as e:
            result['message'] = f"健康检查失败: {str(e)}"
            
        return result
    
    def check_port_listening(self, port: int) -> Dict[str, Any]:
        """检查端口是否被监听
        
        Args:
            port: 端口号
            
        Returns:
            Dict[str, Any]: 端口检查结果
        """
        port_info = {
            'listening': False,
            'process': None,
            'command': None,
            'error': None
        }
        
        try:
            system = platform.system().lower()
            
            if system == 'darwin':  # macOS
                # 使用 lsof 检查端口
                cmd = ['lsof', '-i', f':{port}', '-P', '-n']
            elif system == 'linux':
                # 使用 netstat 检查端口
                cmd = ['netstat', '-tlnp']
            else:
                # Windows
                cmd = ['netstat', '-an']
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if system == 'darwin':
                if result.returncode == 0 and result.stdout.strip():
                    lines = result.stdout.strip().split('\n')
                    for line in lines[1:]:  # 跳过标题行
                        parts = line.split()
                        if len(parts) >= 2:
                            port_info['listening'] = True
                            port_info['process'] = parts[1] if len(parts) > 1 else 'Unknown'
                            port_info['command'] = parts[0] if len(parts) > 0 else 'Unknown'
                            break
            elif system == 'linux':
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if f':{port} ' in line and 'LISTEN' in line:
                            port_info['listening'] = True
                            parts = line.split()
                            if len(parts) > 6:
                                port_info['process'] = parts[6]
                            break
            else:  # Windows
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if f':{port} ' in line and 'LISTENING' in line:
                            port_info['listening'] = True
                            break
                            
        except subprocess.TimeoutExpired:
            port_info['error'] = '端口检查超时'
        except FileNotFoundError:
            port_info['error'] = '系统命令不可用'
        except Exception as e:
            port_info['error'] = f'端口检查失败: {str(e)}'
            
        return port_info
    
    def diagnose_adspower(self) -> Dict[str, Any]:
        """诊断 AdsPower 连接问题（增强版）
        
        Returns:
            Dict[str, Any]: 诊断结果
        """
        config = self.load_config()
        
        result = {
            'reachable': False,
            'tried_hosts': [],
            'port_open': False,
            'port_listening': False,
            'port_process': None,
            'error': '',
            'error_type': '',
            'recommendation': '',
            'suggestions': [],
            'api_enabled_check': [],
            'system_info': {},
            'download_url': 'https://www.adspower.net/share/hftJaRHMQl1r7jw'
        }
        
        # 系统信息
        result['system_info'] = {
            'platform': platform.system(),
            'version': platform.version(),
            'port': config.port
        }
        
        # 检查端口是否被监听
        port_info = self.check_port_listening(config.port)
        result['port_listening'] = port_info['listening']
        result['port_process'] = port_info['process']
        
        if port_info['error']:
            self.logger.warning(f"端口检查失败: {port_info['error']}")
        
        # 构建要尝试的主机列表
        hosts_to_try = [config.host]
        if config.host == "localhost":
            hosts_to_try.append("127.0.0.1")
        elif config.host == "127.0.0.1":
            hosts_to_try.append("localhost")
        
        result['tried_hosts'] = hosts_to_try
        
        # 尝试连接每个主机
        for host in hosts_to_try:
            try:
                url = f"http://{host}:{config.port}/status"
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if data.get('code') == 0:
                            result['reachable'] = True
                            result['port_open'] = True
                            return result
                        else:
                            result['error'] = f"AdsPower 状态异常: {data.get('msg', '未知错误')}"
                            result['error_type'] = 'StatusError'
                            result['port_open'] = True
                    except ValueError:
                        result['error'] = f"端口 {config.port} 被其他服务占用"
                        result['error_type'] = 'PortOccupied'
                        result['port_open'] = True
                else:
                    result['error'] = f"HTTP错误: {response.status_code}"
                    result['error_type'] = 'HttpError'
                    result['port_open'] = True
                    
            except requests.exceptions.ConnectionError as e:
                result['error'] = f"连接被拒绝: {type(e).__name__}"
                result['error_type'] = 'ConnectionRefusedError'
            except requests.exceptions.Timeout as e:
                result['error'] = f"连接超时: {type(e).__name__}"
                result['error_type'] = 'TimeoutError'
            except Exception as e:
                result['error'] = f"连接错误: {type(e).__name__}: {str(e)}"
                result['error_type'] = type(e).__name__
        
        # API 启用检查项
        result['api_enabled_check'] = [
            {
                'item': 'AdsPower 已启动并登录',
                'status': 'unknown',
                'description': '确保 AdsPower 应用程序已打开并成功登录账户'
            },
            {
                'item': '启用本地 API 服务',
                'status': 'failed' if result['error_type'] == 'ConnectionRefusedError' else 'unknown',
                'description': '在 AdsPower 设置中启用本地API服务（默认端口 50325）'
            },
            {
                'item': '启用 HTTP 请求支持',
                'status': 'unknown',
                'description': '确保允许 HTTP 接口访问（非 HTTPS）'
            },
            {
                'item': '放通 127.0.0.1 访问权限',
                'status': 'failed' if not result['port_listening'] else 'unknown',
                'description': '允许本地回环地址访问 API 接口'
            }
        ]
        
        # 生成建议
        result['suggestions'] = [
            "✅ AdsPower 是否已启动并登录？",
            "✅ 是否启用了【本地 API 服务】？",
            "✅ 是否允许 HTTP 接口（非 HTTPS）？",
            "✅ 当前端口是否已被系统占用或被防火墙拦截？"
        ]
        
        # 根据错误类型和端口状态生成具体建议
        if result['error_type'] == 'ConnectionRefusedError':
            if not result['port_listening']:
                result['recommendation'] = "API端口未开启或未监听，请在 AdsPower 设置中开启本地API服务监听。"
            else:
                result['recommendation'] = "端口已监听但连接被拒绝，请检查 AdsPower API 配置是否允许本地访问。"
        elif result['error_type'] == 'TimeoutError':
            result['recommendation'] = "AdsPower 响应超时，请检查网络连接或重启 AdsPower。"
        elif result['error_type'] == 'PortOccupied':
            result['recommendation'] = f"端口 {config.port} 被其他服务占用，请检查 AdsPower 端口配置。"
        elif result['error_type'] == 'StatusError':
            result['recommendation'] = "AdsPower 运行异常，请重启 AdsPower 或检查配置。"
        else:
            if not result['port_listening']:
                result['recommendation'] = "AdsPower API 端口未监听，请检查是否已在设置中开启本地 API 功能，或被系统防火墙屏蔽。"
            else:
                result['recommendation'] = "请确保 AdsPower 开启本地 API 端口，并未被防火墙阻拦。"
        
        return result


# 便捷函数
def is_adspower_available() -> bool:
    """检查 AdsPower 是否可用
    
    Returns:
        bool: 是否可用
    """
    manager = AdsPowerManager()
    is_available, _ = manager.check_availability()
    return is_available


def launch_browser_by_user_id(user_id: str) -> Optional[webdriver.Chrome]:
    """根据用户ID启动浏览器
    
    Args:
        user_id: 用户ID
        
    Returns:
        Optional[webdriver.Chrome]: 浏览器驱动实例
    """
    manager = AdsPowerManager()
    return manager.start_browser(user_id)