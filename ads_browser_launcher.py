# -*- coding: utf-8 -*-
"""
AdsPower 浏览器启动器
用于启动 AdsPower 虚拟浏览器并获取控制端口
"""

import requests
import time
import logging
from typing import Optional, Dict, Any
from config import ADS_POWER_CONFIG

class AdsPowerLauncher:
    def __init__(self):
        self.api_url = ADS_POWER_CONFIG['local_api_url']
        self.user_id = ADS_POWER_CONFIG['user_id']
        self.group_id = ADS_POWER_CONFIG.get('group_id', '')
        self.browser_info = None
        self.logger = logging.getLogger(__name__)
    
    def start_browser(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        启动 AdsPower 浏览器
        
        Args:
            user_id: AdsPower 用户ID，如果不提供则使用配置文件中的默认值
            
        Returns:
            包含浏览器信息的字典，包括调试端口等
        """
        target_user_id = user_id or self.user_id
        
        if not target_user_id:
            raise ValueError("用户ID不能为空，请在配置文件中设置或作为参数传入")
        
        try:
            # 构建启动请求
            start_url = f"{self.api_url}/api/v1/browser/start"
            params = {
                'user_id': target_user_id
            }
            
            if self.group_id:
                params['group_id'] = self.group_id
            
            self.logger.info(f"正在启动 AdsPower 浏览器，用户ID: {target_user_id}")
            
            # 发送启动请求
            response = requests.get(start_url, params=params)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('code') == 0:
                self.browser_info = result.get('data', {})
                self.logger.info(f"浏览器启动成功，调试端口: {self.browser_info.get('ws', {}).get('puppeteer')}")
                return self.browser_info
            else:
                error_msg = result.get('msg', '未知错误')
                raise Exception(f"启动浏览器失败: {error_msg}")
                
        except requests.RequestException as e:
            self.logger.error(f"请求 AdsPower API 失败: {e}")
            raise Exception(f"无法连接到 AdsPower API: {e}")
        except Exception as e:
            self.logger.error(f"启动浏览器时发生错误: {e}")
            raise
    
    def stop_browser(self, user_id: Optional[str] = None) -> bool:
        """
        停止 AdsPower 浏览器
        
        Args:
            user_id: AdsPower 用户ID
            
        Returns:
            是否成功停止
        """
        target_user_id = user_id or self.user_id
        
        if not target_user_id:
            self.logger.warning("用户ID为空，无法停止浏览器")
            return False
        
        try:
            stop_url = f"{self.api_url}/api/v1/browser/stop"
            params = {'user_id': target_user_id}
            
            self.logger.info(f"正在停止 AdsPower 浏览器，用户ID: {target_user_id}")
            
            response = requests.get(stop_url, params=params)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('code') == 0:
                self.logger.info("浏览器停止成功")
                self.browser_info = None
                return True
            else:
                error_msg = result.get('msg', '未知错误')
                self.logger.error(f"停止浏览器失败: {error_msg}")
                return False
                
        except requests.RequestException as e:
            self.logger.error(f"请求 AdsPower API 失败: {e}")
            return False
        except Exception as e:
            self.logger.error(f"停止浏览器时发生错误: {e}")
            return False
    
    def get_browser_status(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取浏览器状态
        
        Args:
            user_id: AdsPower 用户ID
            
        Returns:
            浏览器状态信息
        """
        target_user_id = user_id or self.user_id
        
        if not target_user_id:
            raise ValueError("用户ID不能为空")
        
        try:
            status_url = f"{self.api_url}/api/v1/browser/active"
            params = {'user_id': target_user_id}
            
            response = requests.get(status_url, params=params)
            response.raise_for_status()
            
            result = response.json()
            return result
            
        except requests.RequestException as e:
            self.logger.error(f"获取浏览器状态失败: {e}")
            raise Exception(f"无法获取浏览器状态: {e}")
    
    def get_debug_port(self) -> Optional[str]:
        """
        获取浏览器调试端口
        
        Returns:
            调试端口URL，如果浏览器未启动则返回None
        """
        if not self.browser_info:
            return None
        
        ws_info = self.browser_info.get('ws', {})
        return ws_info.get('puppeteer') or ws_info.get('playwright')
    
    def wait_for_browser_ready(self, timeout: int = 30) -> bool:
        """
        等待浏览器准备就绪
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            是否准备就绪
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                status = self.get_browser_status()
                if status.get('code') == 0 and status.get('data', {}).get('status') == 'Active':
                    self.logger.info("浏览器已准备就绪")
                    return True
            except Exception:
                pass
            
            time.sleep(1)
        
        self.logger.error(f"等待浏览器准备就绪超时（{timeout}秒）")
        return False

# 使用示例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    launcher = AdsPowerLauncher()
    
    try:
        # 启动浏览器
        browser_info = launcher.start_browser()
        print(f"浏览器信息: {browser_info}")
        
        # 获取调试端口
        debug_port = launcher.get_debug_port()
        print(f"调试端口: {debug_port}")
        
        # 等待用户操作
        input("按回车键停止浏览器...")
        
        # 停止浏览器
        launcher.stop_browser()
        
    except Exception as e:
        print(f"错误: {e}")