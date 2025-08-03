# -*- coding: utf-8 -*-
"""
AdsPower 浏览器启动器
用于启动 AdsPower 虚拟浏览器并获取控制端口
"""

import requests
import time
import logging
import psutil
import subprocess
import os
from typing import Optional, Dict, Any, List
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.adspower_manager import AdsPowerManager
# 配置将从调用方传入，不再直接导入

class AdsPowerLauncher:
    def __init__(self, config=None):
        # 如果没有传入配置，使用默认配置
        if config is None:
            config = {
                'local_api_url': 'http://local.adspower.net:50325',
                'user_id': '',
                'group_id': '',
                'api_key': ''
            }
        
        self.api_url = config.get('local_api_url', 'http://local.adspower.net:50325')
        self.user_id = config.get('user_id', '')
        self.group_id = config.get('group_id', '')
        self.api_key = config.get('api_key', '')
        self.browser_info = None
        self.logger = logging.getLogger(__name__)
        self.max_cpu_threshold = 80.0  # CPU使用率阈值
        self.max_memory_threshold = 85.0  # 内存使用率阈值
        self.rpa_process_check_enabled = True  # 是否启用RPA进程检查
        
        # 初始化AdsPowerManager
        self.adspower_manager = AdsPowerManager()
        
        # 尝试从配置文件加载配置
        try:
            manager_config = self.adspower_manager.load_config()
            if manager_config:
                self.api_url = f"http://{manager_config.host}:{manager_config.port}"
                # 如果没有指定user_id，使用配置中的第一个
                if not self.user_id and manager_config.user_ids:
                    self.user_id = manager_config.user_ids[0]
        except Exception as e:
            self.logger.warning(f"加载AdsPower配置失败，使用默认配置: {e}")
    
    def start_browser_selenium(self, user_id: Optional[str] = None, skip_health_check: bool = False) -> Optional[webdriver.Chrome]:
        """启动AdsPower浏览器并返回Selenium WebDriver
        
        Args:
            user_id: 用户ID，如果不提供则使用初始化时的user_id
            skip_health_check: 是否跳过健康检查
            
        Returns:
            webdriver.Chrome: Chrome浏览器驱动实例，失败时返回None
        """
        target_user_id = user_id or self.user_id
        if not target_user_id:
            self.logger.error("未提供用户ID")
            return None
            
        try:
            # 使用AdsPowerManager进行环境检查
            is_available, message = self.adspower_manager.check_availability()
            if not is_available:
                self.logger.error(f"AdsPower环境检查失败: {message}")
                return None
            
            # 验证用户ID
            if not self.adspower_manager.validate_user_id(target_user_id):
                self.logger.error(f"用户ID {target_user_id} 无效")
                return None
            
            # 系统资源检查
            if not self.check_system_resources():
                return None
            
            # 自动优化
            self.auto_optimize_system()
            
            # 使用AdsPowerManager启动浏览器
            self.logger.info(f"正在启动AdsPower浏览器，用户ID: {target_user_id}")
            
            driver = self.adspower_manager.start_browser(target_user_id)
            
            if driver:
                # 健康检查
                if not skip_health_check and not self._health_check(driver):
                    driver.quit()
                    return None
                
                self.logger.info(f"AdsPower浏览器启动成功，用户ID: {target_user_id}")
                return driver
            else:
                self.logger.error(f"启动浏览器失败，用户ID: {target_user_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"启动浏览器时发生未知错误: {str(e)}")
            return None
    
    def start_multiple_browsers(self, user_ids: List[str] = None, skip_health_check: bool = False) -> Dict[str, Optional[webdriver.Chrome]]:
        """启动多个AdsPower浏览器
        
        Args:
            user_ids: 用户ID列表，如果不提供则使用配置文件中的所有用户ID
            skip_health_check: 是否跳过健康检查
            
        Returns:
            Dict[str, Optional[webdriver.Chrome]]: 用户ID到浏览器驱动的映射
        """
        if not user_ids:
            try:
                config = self.adspower_manager.load_config()
                user_ids = config.user_ids if config else []
            except Exception as e:
                self.logger.error(f"加载用户ID列表失败: {e}")
                return {}
        
        if not user_ids:
            self.logger.error("未提供用户ID列表")
            return {}
        
        browsers = {}
        
        for user_id in user_ids:
            self.logger.info(f"正在启动浏览器，用户ID: {user_id}")
            try:
                browser = self.start_browser_selenium(user_id, skip_health_check)
                browsers[user_id] = browser
                
                if browser:
                    self.logger.info(f"用户 {user_id} 的浏览器启动成功")
                else:
                    self.logger.warning(f"用户 {user_id} 的浏览器启动失败")
                    
                # 添加延迟避免并发问题
                time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"启动用户 {user_id} 的浏览器时发生错误: {e}")
                browsers[user_id] = None
        
        successful_count = sum(1 for browser in browsers.values() if browser is not None)
        self.logger.info(f"多浏览器启动完成，成功: {successful_count}/{len(user_ids)}")
        
        return browsers
    
    def _health_check(self, driver: webdriver.Chrome) -> bool:
        """对浏览器进行健康检查
        
        Args:
            driver: Chrome浏览器驱动实例
            
        Returns:
            bool: 健康检查是否通过
        """
        try:
            # 检查浏览器是否响应
            driver.get("about:blank")
            
            # 检查页面是否加载
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            self.logger.info("浏览器健康检查通过")
            return True
            
        except Exception as e:
            self.logger.error(f"浏览器健康检查失败: {e}")
            return False
    
    def start_browser(self, user_id: Optional[str] = None, skip_health_check: bool = True) -> Dict[str, Any]:
        """
        启动 AdsPower 浏览器
        
        Args:
            user_id: AdsPower 用户ID，如果不提供则使用配置文件中的默认值
            skip_health_check: 是否跳过健康检查（用于紧急情况）
            
        Returns:
            包含浏览器信息的字典，包括调试端口等
        """
        target_user_id = user_id or self.user_id
        
        if not target_user_id:
            raise ValueError("用户ID不能为空，请在配置文件中设置或作为参数传入")
        
        # 启动前健康检查
        if not skip_health_check:
            self.logger.info("正在进行启动前健康检查...")
            
            # 1. 检查系统资源
            if not self.check_system_resources():
                raise Exception("系统资源不足，无法启动浏览器。请关闭其他应用程序或等待系统负载降低。")
            
            # 2. 检查并修复AdsPower进程
            if not self.restart_adspower_if_needed():
                raise Exception("AdsPower进程异常，无法自动修复。请手动重启AdsPower应用程序。")
            
            # 3. 等待系统稳定
            time.sleep(2)
            
            self.logger.info("健康检查通过，开始启动浏览器...")
        
        try:
            # 构建启动请求
            start_url = f"{self.api_url}/api/v1/browser/start"
            params = {
                'user_id': target_user_id
            }
            
            if self.group_id:
                params['group_id'] = self.group_id
            
            # 添加快速模式配置
            # 使用默认的浏览器配置
            browser_config = {
                'fast_mode': True,
                'skip_images': True,
                'disable_animations': True
            }
            if browser_config.get('fast_mode', False):
                # 快速模式下的浏览器参数
                launch_args = []
                
                if browser_config.get('skip_images', False):
                    launch_args.extend([
                        '--blink-settings=imagesEnabled=false',
                        '--disable-images'
                    ])
                
                if browser_config.get('disable_animations', False):
                    launch_args.extend([
                        '--disable-background-timer-throttling',
                        '--disable-renderer-backgrounding',
                        '--disable-backgrounding-occluded-windows',
                        '--disable-features=TranslateUI',
                        '--disable-ipc-flooding-protection'
                    ])
                
                # 通用性能优化参数
                launch_args.extend([
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ])
                
                if launch_args:
                    # AdsPower API需要launch_args为JSON字符串格式
                    import json
                    params['launch_args'] = json.dumps(launch_args)
                    self.logger.info(f"启用快速模式，浏览器参数: {launch_args}")
            
            self.logger.info(f"正在启动 AdsPower 浏览器，用户ID: {target_user_id}")
            
            # 准备请求头
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            # 发送启动请求
            response = requests.get(start_url, params=params, headers=headers, timeout=30)
            self.logger.info(f"AdsPower API Response: {response.text}")
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('code') == 0:
                self.browser_info = result.get('data', {})
                self.logger.info(f"浏览器启动成功，调试端口: {self.browser_info.get('ws', {}).get('puppeteer')}")
                
                # 启动后验证
                if not skip_health_check:
                    if self.wait_for_browser_ready(timeout=15):
                        self.logger.info("浏览器启动并验证成功")
                    else:
                        self.logger.warning("浏览器启动成功但验证失败，可能存在稳定性问题")
                
                return self.browser_info
            else:
                error_msg = result.get('msg', '未知错误')
                
                # 如果启动失败，尝试自动修复
                if not skip_health_check and "profile" in error_msg.lower():
                    self.logger.warning(f"启动失败可能由于配置文件问题: {error_msg}，尝试修复...")
                    if self.restart_adspower_if_needed():
                        time.sleep(5)
                        return self.start_browser(target_user_id, skip_health_check=True)
                
                raise Exception(f"启动浏览器失败: {error_msg}")
                
        except requests.RequestException as e:
            self.logger.error(f"请求 AdsPower API 失败: {e}")
            
            # 如果API请求失败，尝试重启AdsPower
            if not skip_health_check:
                self.logger.info("API请求失败，尝试重启AdsPower...")
                if self.restart_adspower_if_needed():
                    time.sleep(10)
                    return self.start_browser(target_user_id, skip_health_check=True)
            
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
            
            # 准备请求头
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            response = requests.get(stop_url, params=params, headers=headers)
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
    
    def start_browser_with_monitoring(self, user_id: Optional[str] = None, monitor_duration: int = 60) -> Dict[str, Any]:
        """
        启动浏览器并进行持续监控
        
        Args:
            user_id: AdsPower 用户ID
            monitor_duration: 监控持续时间（秒），0表示不监控
            
        Returns:
            浏览器信息
        """
        # 启动浏览器
        browser_info = self.start_browser(user_id)
        
        # 如果需要监控
        if monitor_duration > 0:
            self.logger.info(f"开始监控浏览器状态，持续时间: {monitor_duration}秒")
            
            start_time = time.time()
            check_interval = 10  # 每10秒检查一次
            
            while time.time() - start_time < monitor_duration:
                try:
                    # 检查浏览器状态
                    status = self.get_browser_status(user_id)
                    if status.get('code') != 0 or status.get('data', {}).get('status') != 'Active':
                        self.logger.warning("检测到浏览器状态异常，尝试修复...")
                        
                        # 尝试重新启动
                        self.stop_browser(user_id)
                        time.sleep(3)
                        browser_info = self.start_browser(user_id, skip_health_check=True)
                        
                    # 检查系统资源和进程
                    if not self.check_system_resources():
                        self.logger.warning("系统资源紧张，建议暂停操作")
                    
                    self.terminate_high_cpu_rpa_processes()
                    
                except Exception as e:
                    self.logger.error(f"监控过程中发生错误: {e}")
                
                time.sleep(check_interval)
            
            self.logger.info("浏览器监控完成")
        
        return browser_info
    
    def get_health_report(self) -> Dict[str, Any]:
        """
        获取系统健康报告
        
        Returns:
            健康状态报告
        """
        report = {
            'timestamp': time.time(),
            'system_resources': {},
            'adspower_processes': {},
            'recommendations': []
        }
        
        try:
            # 系统资源信息
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            report['system_resources'] = {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / (1024**3),
                'disk_free_gb': disk.free / (1024**3),
                'cpu_healthy': cpu_percent < self.max_cpu_threshold,
                'memory_healthy': memory.percent < self.max_memory_threshold,
                'disk_healthy': disk.free / (1024**3) > 1.0
            }
            
            # AdsPower进程信息
            process_info = self.check_adspower_processes()
            report['adspower_processes'] = process_info
            
            # 生成建议
            if cpu_percent > self.max_cpu_threshold:
                report['recommendations'].append(f"CPU使用率过高({cpu_percent:.1f}%)，建议关闭其他应用程序")
            
            if memory.percent > self.max_memory_threshold:
                report['recommendations'].append(f"内存使用率过高({memory.percent:.1f}%)，建议释放内存")
            
            if process_info['high_cpu_processes']:
                report['recommendations'].append(f"发现{len(process_info['high_cpu_processes'])}个高CPU使用率的RPA进程，建议终止")
            
            if not process_info['adspower_running']:
                report['recommendations'].append("AdsPower未运行，建议启动应用程序")
            
            if not report['recommendations']:
                report['recommendations'].append("系统状态良好")
            
        except Exception as e:
            report['error'] = str(e)
            report['recommendations'].append("获取健康报告时发生错误，建议检查系统状态")
        
        return report
    
    def auto_optimize_system(self) -> bool:
        """
        自动优化系统性能
        
        Returns:
            是否成功优化
        """
        try:
            self.logger.info("开始自动优化系统...")
            
            # 1. 终止异常RPA进程
            if self.terminate_high_cpu_rpa_processes():
                self.logger.info("✅ 已清理异常RPA进程")
            
            # 2. 清理系统缓存（macOS）
            try:
                subprocess.run(['sudo', 'purge'], check=False, capture_output=True)
                self.logger.info("✅ 已清理系统缓存")
            except:
                pass
            
            # 3. 清理AdsPower缓存
            try:
                cache_path = os.path.expanduser("~/Library/Application Support/adspower_global/cache")
                if os.path.exists(cache_path):
                    subprocess.run(['rm', '-rf', f"{cache_path}/*"], shell=True, check=False)
                    self.logger.info("✅ 已清理AdsPower缓存")
            except:
                pass
            
            # 4. 等待系统稳定
            time.sleep(3)
            
            # 5. 验证优化效果
            if self.check_system_resources():
                self.logger.info("✅ 系统优化完成，资源状态良好")
                return True
            else:
                self.logger.warning("⚠️ 系统优化完成，但资源仍然紧张")
                return False
            
        except Exception as e:
            self.logger.error(f"自动优化系统时发生错误: {e}")
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
    
    def check_system_resources(self) -> bool:
        """
        检查系统资源是否充足
        
        Returns:
            系统资源是否充足
        """
        try:
            # 检查CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > self.max_cpu_threshold:
                self.logger.warning(f"CPU使用率过高: {cpu_percent:.1f}% (阈值: {self.max_cpu_threshold}%)")
                return False
            
            # 检查内存使用率
            memory = psutil.virtual_memory()
            if memory.percent > self.max_memory_threshold:
                self.logger.warning(f"内存使用率过高: {memory.percent:.1f}% (阈值: {self.max_memory_threshold}%)")
                return False
            
            # 检查可用磁盘空间（至少需要1GB）
            disk = psutil.disk_usage('/')
            free_gb = disk.free / (1024**3)
            if free_gb < 1.0:
                self.logger.warning(f"磁盘空间不足: {free_gb:.1f}GB")
                return False
            
            self.logger.debug(f"系统资源检查通过 - CPU: {cpu_percent:.1f}%, 内存: {memory.percent:.1f}%, 磁盘: {free_gb:.1f}GB")
            return True
            
        except Exception as e:
            self.logger.error(f"检查系统资源时发生错误: {e}")
            return False
    
    def check_adspower_processes(self) -> Dict[str, Any]:
        """
        检查AdsPower相关进程状态
        
        Returns:
            进程状态信息
        """
        process_info = {
            'adspower_running': False,
            'rpa_processes': [],
            'high_cpu_processes': [],
            'total_processes': 0
        }
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    pinfo = proc.info
                    if 'adspower' in pinfo['name'].lower() or 'AdsPower' in pinfo['name']:
                        process_info['adspower_running'] = True
                        process_info['total_processes'] += 1
                        
                        # 检查RPA进程
                        if 'rpa' in pinfo['name'].lower():
                            process_info['rpa_processes'].append({
                                'pid': pinfo['pid'],
                                'name': pinfo['name'],
                                'cpu_percent': pinfo['cpu_percent'],
                                'memory_percent': pinfo['memory_percent']
                            })
                            
                            # 检查高CPU使用率的RPA进程
                            if pinfo['cpu_percent'] > self.max_cpu_threshold:
                                process_info['high_cpu_processes'].append(pinfo['pid'])
                                self.logger.warning(f"发现高CPU使用率RPA进程: PID {pinfo['pid']}, CPU: {pinfo['cpu_percent']:.1f}%")
                                
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return process_info
            
        except Exception as e:
            self.logger.error(f"检查AdsPower进程时发生错误: {e}")
            return process_info
    
    def terminate_high_cpu_rpa_processes(self) -> bool:
        """
        终止高CPU使用率的RPA进程
        
        Returns:
            是否成功终止异常进程
        """
        if not self.rpa_process_check_enabled:
            return True
            
        try:
            process_info = self.check_adspower_processes()
            
            if process_info['high_cpu_processes']:
                self.logger.info(f"发现 {len(process_info['high_cpu_processes'])} 个高CPU使用率的RPA进程，正在终止...")
                
                for pid in process_info['high_cpu_processes']:
                    try:
                        proc = psutil.Process(pid)
                        proc.terminate()  # 优雅终止
                        
                        # 等待进程终止
                        try:
                            proc.wait(timeout=5)
                            self.logger.info(f"成功终止RPA进程: PID {pid}")
                        except psutil.TimeoutExpired:
                            # 如果优雅终止失败，强制终止
                            proc.kill()
                            self.logger.warning(f"强制终止RPA进程: PID {pid}")
                            
                    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                        self.logger.warning(f"无法终止进程 {pid}: {e}")
                        
                return True
            
            return True
            
        except Exception as e:
            self.logger.error(f"终止RPA进程时发生错误: {e}")
            return False
    
    def restart_adspower_if_needed(self) -> bool:
        """
        如果检测到AdsPower异常，尝试重启
        
        Returns:
            是否成功重启
        """
        try:
            process_info = self.check_adspower_processes()
            
            # 如果有高CPU进程，先尝试终止
            if process_info['high_cpu_processes']:
                self.logger.info("检测到异常RPA进程，尝试修复...")
                if not self.terminate_high_cpu_rpa_processes():
                    return False
                
                # 等待一段时间让系统稳定
                time.sleep(3)
            
            # 检查AdsPower是否仍在运行
            if not process_info['adspower_running']:
                self.logger.warning("AdsPower未运行，尝试启动...")
                try:
                    # 尝试启动AdsPower（macOS）
                    subprocess.Popen(['open', '/Applications/AdsPower Global.app'], 
                                   stdout=subprocess.DEVNULL, 
                                   stderr=subprocess.DEVNULL)
                    
                    # 等待AdsPower启动
                    time.sleep(10)
                    
                    # 验证是否启动成功
                    new_process_info = self.check_adspower_processes()
                    if new_process_info['adspower_running']:
                        self.logger.info("AdsPower启动成功")
                        return True
                    else:
                        self.logger.error("AdsPower启动失败")
                        return False
                        
                except Exception as e:
                    self.logger.error(f"启动AdsPower时发生错误: {e}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"重启AdsPower时发生错误: {e}")
            return False

# 使用示例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    launcher = AdsPowerLauncher()
    
    try:
        print("=== AdsPower 增强启动器演示 ===")
        
        # 1. 获取系统健康报告
        print("\n📊 获取系统健康报告...")
        health_report = launcher.get_health_report()
        print(f"CPU: {health_report['system_resources']['cpu_percent']:.1f}%")
        print(f"内存: {health_report['system_resources']['memory_percent']:.1f}%")
        print(f"磁盘: {health_report['system_resources']['disk_free_gb']:.1f}GB")
        print(f"建议: {', '.join(health_report['recommendations'])}")
        
        # 2. 自动优化系统（如果需要）
        if not all([
            health_report['system_resources']['cpu_healthy'],
            health_report['system_resources']['memory_healthy']
        ]):
            print("\n🔧 检测到系统资源紧张，正在自动优化...")
            launcher.auto_optimize_system()
        
        # 3. 启动浏览器（带健康检查）
        print("\n🚀 启动浏览器（带健康检查）...")
        browser_info = launcher.start_browser()
        print(f"✅ 浏览器启动成功")
        print(f"调试端口: {launcher.get_debug_port()}")
        
        # 4. 可选：启动监控模式
        monitor_choice = input("\n是否启用浏览器监控？(y/n): ").lower()
        if monitor_choice == 'y':
            print("\n👁️ 启动监控模式（30秒）...")
            launcher.start_browser_with_monitoring(monitor_duration=30)
        
        # 等待用户操作
        input("\n按回车键停止浏览器...")
        
        # 停止浏览器
        print("\n🛑 停止浏览器...")
        launcher.stop_browser()
        print("✅ 浏览器已停止")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        
        # 尝试自动修复
        print("\n🔄 尝试自动修复...")
        if launcher.auto_optimize_system():
            print("✅ 自动修复成功，可以重试")
        else:
            print("❌ 自动修复失败，请手动检查系统状态")