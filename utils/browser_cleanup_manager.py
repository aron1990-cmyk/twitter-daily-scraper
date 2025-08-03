#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
浏览器清理管理器
负责强制清理浏览器实例，防止资源泄露和僵尸进程
"""

import psutil
import logging
import asyncio
import time
import signal
import subprocess
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path
import json
import threading

@dataclass
class BrowserProcess:
    """浏览器进程信息"""
    pid: int
    name: str
    cmdline: List[str]
    create_time: float
    memory_mb: float
    cpu_percent: float
    status: str
    parent_pid: Optional[int] = None
    children_pids: List[int] = None

class BrowserCleanupManager:
    """
    浏览器清理管理器
    提供强制清理、健康检查、资源监控等功能
    """
    
    def __init__(self, cleanup_interval_minutes: int = 30):
        self.logger = logging.getLogger('BrowserCleanup')
        self.cleanup_interval = cleanup_interval_minutes * 60
        self.last_cleanup_time = time.time()
        
        # 浏览器进程关键词
        self.browser_keywords = [
            'chrome', 'chromium', 'firefox', 'safari', 'edge',
            'playwright', 'selenium', 'adspower', 'browser'
        ]
        
        # AdsPower相关进程
        self.adspower_keywords = [
            'adspower', 'ads_power', 'adspowerlocal', 'chrome.exe'
        ]
        
        # 清理统计
        self.cleanup_stats = {
            'total_cleanups': 0,
            'processes_killed': 0,
            'memory_freed_mb': 0,
            'last_cleanup_time': None,
            'failed_cleanups': 0
        }
        
        # 进程白名单（不清理的进程）
        self.process_whitelist = {
            'system', 'kernel', 'init', 'systemd', 'launchd'
        }
        
        self.logger.info("浏览器清理管理器初始化完成")
    
    def get_browser_processes(self) -> List[BrowserProcess]:
        """
        获取所有浏览器相关进程
        
        Returns:
            浏览器进程列表
        """
        browser_processes = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 
                                           'memory_info', 'cpu_percent', 'status', 'ppid']):
                try:
                    pinfo = proc.info
                    process_name = pinfo['name'].lower()
                    cmdline = ' '.join(pinfo['cmdline'] or []).lower()
                    
                    # 检查是否是浏览器进程
                    is_browser = any(keyword in process_name or keyword in cmdline 
                                   for keyword in self.browser_keywords)
                    
                    if is_browser and process_name not in self.process_whitelist:
                        # 获取子进程
                        children_pids = []
                        try:
                            children = proc.children(recursive=True)
                            children_pids = [child.pid for child in children]
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                        
                        browser_proc = BrowserProcess(
                            pid=pinfo['pid'],
                            name=pinfo['name'],
                            cmdline=pinfo['cmdline'] or [],
                            create_time=pinfo['create_time'],
                            memory_mb=round((pinfo['memory_info'].rss if pinfo['memory_info'] else 0) / 1024 / 1024, 2),
                            cpu_percent=pinfo['cpu_percent'] or 0,
                            status=pinfo['status'],
                            parent_pid=pinfo['ppid'],
                            children_pids=children_pids
                        )
                        
                        browser_processes.append(browser_proc)
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                    
        except Exception as e:
            self.logger.error(f"获取浏览器进程失败: {e}")
        
        return browser_processes
    
    def get_zombie_processes(self) -> List[BrowserProcess]:
        """
        获取僵尸浏览器进程
        
        Returns:
            僵尸进程列表
        """
        zombie_processes = []
        browser_processes = self.get_browser_processes()
        current_time = time.time()
        
        for proc in browser_processes:
            # 检查进程是否为僵尸状态
            if proc.status in ['zombie', 'dead']:
                zombie_processes.append(proc)
                continue
            
            # 检查进程是否长时间运行且占用大量资源
            running_hours = (current_time - proc.create_time) / 3600
            if running_hours > 6 and proc.memory_mb > 1000:  # 运行超过6小时且占用超过1GB内存
                zombie_processes.append(proc)
                continue
            
            # 检查进程是否无响应（CPU使用率为0且内存占用异常）
            if proc.cpu_percent == 0 and proc.memory_mb > 500 and running_hours > 1:
                zombie_processes.append(proc)
        
        return zombie_processes
    
    def force_kill_process(self, pid: int, timeout: int = 10) -> bool:
        """
        强制终止进程
        
        Args:
            pid: 进程ID
            timeout: 超时时间（秒）
            
        Returns:
            是否成功终止
        """
        try:
            proc = psutil.Process(pid)
            proc_name = proc.name()
            
            self.logger.info(f"正在终止进程: {proc_name} (PID: {pid})")
            
            # 首先尝试优雅终止
            proc.terminate()
            
            # 等待进程结束
            try:
                proc.wait(timeout=timeout)
                self.logger.info(f"进程已优雅终止: {proc_name} (PID: {pid})")
                return True
            except psutil.TimeoutExpired:
                # 优雅终止失败，强制杀死
                self.logger.warning(f"优雅终止超时，强制杀死进程: {proc_name} (PID: {pid})")
                proc.kill()
                proc.wait(timeout=5)
                self.logger.info(f"进程已强制终止: {proc_name} (PID: {pid})")
                return True
                
        except psutil.NoSuchProcess:
            self.logger.debug(f"进程不存在: PID {pid}")
            return True
        except psutil.AccessDenied:
            self.logger.error(f"无权限终止进程: PID {pid}")
            return False
        except Exception as e:
            self.logger.error(f"终止进程失败: PID {pid}, 错误: {e}")
            return False
    
    def cleanup_adspower_processes(self) -> int:
        """
        清理AdsPower相关进程
        
        Returns:
            清理的进程数量
        """
        cleaned_count = 0
        
        try:
            # 获取所有AdsPower进程
            adspower_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    pinfo = proc.info
                    process_name = pinfo['name'].lower()
                    cmdline = ' '.join(pinfo['cmdline'] or []).lower()
                    
                    if any(keyword in process_name or keyword in cmdline 
                          for keyword in self.adspower_keywords):
                        adspower_processes.append(proc)
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # 终止AdsPower进程
            for proc in adspower_processes:
                try:
                    if self.force_kill_process(proc.pid):
                        cleaned_count += 1
                except Exception as e:
                    self.logger.error(f"清理AdsPower进程失败: {e}")
            
            if cleaned_count > 0:
                self.logger.info(f"已清理 {cleaned_count} 个AdsPower进程")
                
        except Exception as e:
            self.logger.error(f"清理AdsPower进程异常: {e}")
        
        return cleaned_count
    
    def cleanup_zombie_processes(self) -> Dict[str, int]:
        """
        清理僵尸浏览器进程
        
        Returns:
            清理统计信息
        """
        cleanup_result = {
            'total_found': 0,
            'successfully_killed': 0,
            'failed_to_kill': 0,
            'memory_freed_mb': 0
        }
        
        try:
            zombie_processes = self.get_zombie_processes()
            cleanup_result['total_found'] = len(zombie_processes)
            
            if not zombie_processes:
                self.logger.info("未发现僵尸浏览器进程")
                return cleanup_result
            
            self.logger.info(f"发现 {len(zombie_processes)} 个僵尸浏览器进程")
            
            for proc in zombie_processes:
                try:
                    memory_before = proc.memory_mb
                    
                    # 先终止子进程
                    if proc.children_pids:
                        for child_pid in proc.children_pids:
                            self.force_kill_process(child_pid, timeout=5)
                    
                    # 终止主进程
                    if self.force_kill_process(proc.pid):
                        cleanup_result['successfully_killed'] += 1
                        cleanup_result['memory_freed_mb'] += memory_before
                        self.logger.info(f"已清理僵尸进程: {proc.name} (PID: {proc.pid}, 内存: {memory_before}MB)")
                    else:
                        cleanup_result['failed_to_kill'] += 1
                        
                except Exception as e:
                    cleanup_result['failed_to_kill'] += 1
                    self.logger.error(f"清理僵尸进程失败: {proc.name} (PID: {proc.pid}), 错误: {e}")
            
            # 更新统计信息
            self.cleanup_stats['total_cleanups'] += 1
            self.cleanup_stats['processes_killed'] += cleanup_result['successfully_killed']
            self.cleanup_stats['memory_freed_mb'] += cleanup_result['memory_freed_mb']
            self.cleanup_stats['last_cleanup_time'] = datetime.now().isoformat()
            
            if cleanup_result['failed_to_kill'] > 0:
                self.cleanup_stats['failed_cleanups'] += 1
            
            self.logger.info(f"僵尸进程清理完成: 成功 {cleanup_result['successfully_killed']}, 失败 {cleanup_result['failed_to_kill']}, 释放内存 {cleanup_result['memory_freed_mb']:.2f}MB")
            
        except Exception as e:
            self.logger.error(f"清理僵尸进程异常: {e}")
            self.cleanup_stats['failed_cleanups'] += 1
        
        return cleanup_result
    
    def force_cleanup_all_browsers(self) -> Dict[str, int]:
        """
        强制清理所有浏览器进程（紧急情况使用）
        
        Returns:
            清理统计信息
        """
        self.logger.warning("执行强制清理所有浏览器进程")
        
        cleanup_result = {
            'total_found': 0,
            'successfully_killed': 0,
            'failed_to_kill': 0,
            'memory_freed_mb': 0
        }
        
        try:
            browser_processes = self.get_browser_processes()
            cleanup_result['total_found'] = len(browser_processes)
            
            for proc in browser_processes:
                try:
                    memory_before = proc.memory_mb
                    
                    if self.force_kill_process(proc.pid):
                        cleanup_result['successfully_killed'] += 1
                        cleanup_result['memory_freed_mb'] += memory_before
                    else:
                        cleanup_result['failed_to_kill'] += 1
                        
                except Exception as e:
                    cleanup_result['failed_to_kill'] += 1
                    self.logger.error(f"强制清理进程失败: {proc.name} (PID: {proc.pid}), 错误: {e}")
            
            self.logger.warning(f"强制清理完成: 成功 {cleanup_result['successfully_killed']}, 失败 {cleanup_result['failed_to_kill']}")
            
        except Exception as e:
            self.logger.error(f"强制清理异常: {e}")
        
        return cleanup_result
    
    def auto_cleanup(self) -> bool:
        """
        自动清理（定期调用）
        
        Returns:
            是否执行了清理
        """
        current_time = time.time()
        
        # 检查是否需要清理
        if current_time - self.last_cleanup_time < self.cleanup_interval:
            return False
        
        self.logger.info("开始自动清理浏览器进程")
        
        try:
            # 清理僵尸进程
            zombie_result = self.cleanup_zombie_processes()
            
            # 清理AdsPower进程
            adspower_count = self.cleanup_adspower_processes()
            
            self.last_cleanup_time = current_time
            
            self.logger.info(f"自动清理完成: 僵尸进程 {zombie_result['successfully_killed']}, AdsPower进程 {adspower_count}")
            return True
            
        except Exception as e:
            self.logger.error(f"自动清理异常: {e}")
            return False
    
    def get_browser_health_status(self) -> Dict[str, any]:
        """
        获取浏览器健康状态
        
        Returns:
            健康状态信息
        """
        try:
            browser_processes = self.get_browser_processes()
            zombie_processes = self.get_zombie_processes()
            
            total_memory = sum(proc.memory_mb for proc in browser_processes)
            total_cpu = sum(proc.cpu_percent for proc in browser_processes)
            
            return {
                'total_browser_processes': len(browser_processes),
                'zombie_processes': len(zombie_processes),
                'total_memory_mb': round(total_memory, 2),
                'total_cpu_percent': round(total_cpu, 2),
                'cleanup_stats': self.cleanup_stats.copy(),
                'health_score': self._calculate_health_score(browser_processes, zombie_processes),
                'recommendations': self._get_health_recommendations(browser_processes, zombie_processes)
            }
            
        except Exception as e:
            self.logger.error(f"获取健康状态失败: {e}")
            return {'error': str(e)}
    
    def _calculate_health_score(self, browser_processes: List[BrowserProcess], 
                               zombie_processes: List[BrowserProcess]) -> int:
        """
        计算健康分数（0-100）
        
        Args:
            browser_processes: 浏览器进程列表
            zombie_processes: 僵尸进程列表
            
        Returns:
            健康分数
        """
        if not browser_processes:
            return 100
        
        score = 100
        
        # 僵尸进程扣分
        zombie_ratio = len(zombie_processes) / len(browser_processes)
        score -= zombie_ratio * 50
        
        # 内存使用扣分
        total_memory = sum(proc.memory_mb for proc in browser_processes)
        if total_memory > 4000:  # 超过4GB
            score -= 30
        elif total_memory > 2000:  # 超过2GB
            score -= 15
        
        # 进程数量扣分
        if len(browser_processes) > 20:
            score -= 20
        elif len(browser_processes) > 10:
            score -= 10
        
        return max(0, int(score))
    
    def _get_health_recommendations(self, browser_processes: List[BrowserProcess], 
                                   zombie_processes: List[BrowserProcess]) -> List[str]:
        """
        获取健康建议
        
        Args:
            browser_processes: 浏览器进程列表
            zombie_processes: 僵尸进程列表
            
        Returns:
            建议列表
        """
        recommendations = []
        
        if zombie_processes:
            recommendations.append(f"发现 {len(zombie_processes)} 个僵尸进程，建议立即清理")
        
        total_memory = sum(proc.memory_mb for proc in browser_processes)
        if total_memory > 4000:
            recommendations.append("浏览器内存使用过高，建议重启浏览器实例")
        
        if len(browser_processes) > 15:
            recommendations.append("浏览器进程数量过多，建议减少并发数")
        
        long_running = [proc for proc in browser_processes 
                       if (time.time() - proc.create_time) / 3600 > 8]
        if long_running:
            recommendations.append(f"发现 {len(long_running)} 个长时间运行的进程，建议重启")
        
        if not recommendations:
            recommendations.append("浏览器运行状态良好")
        
        return recommendations


# 全局清理管理器实例
_cleanup_manager = None

def get_cleanup_manager() -> BrowserCleanupManager:
    """获取全局清理管理器实例"""
    global _cleanup_manager
    if _cleanup_manager is None:
        _cleanup_manager = BrowserCleanupManager()
    return _cleanup_manager


# 使用示例
if __name__ == "__main__":
    # 创建清理管理器
    cleanup_manager = BrowserCleanupManager()
    
    # 获取浏览器进程
    processes = cleanup_manager.get_browser_processes()
    print(f"发现 {len(processes)} 个浏览器进程")
    
    # 获取健康状态
    health = cleanup_manager.get_browser_health_status()
    print(f"健康分数: {health['health_score']}")
    print(f"建议: {health['recommendations']}")
    
    # 执行自动清理
    cleanup_manager.auto_cleanup()