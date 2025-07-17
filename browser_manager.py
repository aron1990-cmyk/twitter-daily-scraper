#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
浏览器管理模块 - 负责浏览器实例的创建、管理、会话保持和资源清理
支持多浏览器实例、会话复用、自动重启和性能监控
"""

import asyncio
import logging
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import random

try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
except ImportError:
    print("请安装 playwright: pip install playwright")
    Browser = BrowserContext = Page = None

from exception_handler import (
    BrowserException, NetworkException, TimeoutException,
    async_retry_on_error, handle_exception
)


class BrowserStatus(str, Enum):
    """浏览器状态枚举"""
    IDLE = "idle"              # 空闲
    BUSY = "busy"              # 忙碌
    ERROR = "error"            # 错误
    RESTARTING = "restarting"  # 重启中
    CLOSED = "closed"          # 已关闭


@dataclass
class BrowserInstance:
    """浏览器实例数据模型"""
    instance_id: str
    browser: Optional[Browser] = None
    context: Optional[BrowserContext] = None
    page: Optional[Page] = None
    status: BrowserStatus = BrowserStatus.IDLE
    
    # 使用统计
    created_at: datetime = field(default_factory=datetime.now)
    last_used_at: Optional[datetime] = None
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    
    # 性能指标
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    page_load_time: float = 0.0
    
    # 错误信息
    last_error: Optional[str] = None
    error_count: int = 0
    restart_count: int = 0
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    @property
    def uptime_hours(self) -> float:
        """运行时间（小时）"""
        return (datetime.now() - self.created_at).total_seconds() / 3600
    
    @property
    def is_healthy(self) -> bool:
        """是否健康"""
        return (
            self.status not in [BrowserStatus.ERROR, BrowserStatus.CLOSED] and
            self.error_count < 10 and
            self.memory_usage_mb < 2000  # 2GB内存限制
        )


class BrowserManager:
    """浏览器管理器"""
    
    def __init__(self, max_instances: int = 3, headless: bool = True, 
                 user_data_dir: str = None, proxy_config: Dict[str, str] = None):
        self.max_instances = max_instances
        self.headless = headless
        self.user_data_dir = Path(user_data_dir) if user_data_dir else None
        self.proxy_config = proxy_config
        
        self.logger = logging.getLogger(__name__)
        self.playwright = None
        self.instances: Dict[str, BrowserInstance] = {}
        self.instance_pool: List[str] = []  # 可用实例池
        
        # 配置参数
        self.browser_config = {
            'headless': self.headless,
            'args': [
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-extensions',
                '--disable-plugins',
                '--mute-audio',  # 静音所有音频
                '--autoplay-policy=no-user-gesture-required',  # 允许自动播放但静音
                '--disable-background-timer-throttling',  # 禁用后台定时器限制
                '--disable-renderer-backgrounding',  # 禁用渲染器后台化
                '--disable-backgrounding-occluded-windows',  # 禁用被遮挡窗口的后台化
                '--disable-ipc-flooding-protection',  # 禁用IPC洪水保护
                '--disable-dev-shm-usage',  # 禁用/dev/shm使用
                '--no-first-run',  # 跳过首次运行
                '--no-default-browser-check',  # 跳过默认浏览器检查
                '--disable-default-apps',  # 禁用默认应用
            ]
        }
        
        # 用户代理池
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        
        # 性能监控
        self.monitoring_enabled = True
        self.last_cleanup_time = datetime.now()
        self.cleanup_interval_hours = 2
    
    async def initialize(self):
        """初始化浏览器管理器"""
        try:
            self.playwright = await async_playwright().start()
            self.logger.info("浏览器管理器初始化成功")
            
            # 创建初始实例
            await self._create_initial_instances()
            
        except Exception as e:
            self.logger.error(f"浏览器管理器初始化失败: {e}")
            raise BrowserException(f"初始化失败: {e}")
    
    async def _create_initial_instances(self, count: int = 1):
        """创建初始浏览器实例"""
        for i in range(min(count, self.max_instances)):
            try:
                instance_id = f"browser_{int(time.time())}_{i}"
                await self._create_browser_instance(instance_id)
                self.logger.info(f"创建初始浏览器实例: {instance_id}")
            except Exception as e:
                self.logger.error(f"创建初始实例失败: {e}")
    
    @async_retry_on_error(max_retries=3, delay=2.0)
    async def _create_browser_instance(self, instance_id: str) -> BrowserInstance:
        """创建浏览器实例"""
        try:
            # 配置浏览器选项
            browser_options = self.browser_config.copy()
            
            # 添加代理配置
            if self.proxy_config:
                browser_options['proxy'] = self.proxy_config
            
            # 创建浏览器
            browser = await self.playwright.chromium.launch(**browser_options)
            
            # 创建上下文
            context_options = {
                'user_agent': random.choice(self.user_agents),
                'viewport': {'width': 1920, 'height': 1080},
                'locale': 'en-US',
                'timezone_id': 'America/New_York',
                'permissions': [],  # 不授予任何权限
                'extra_http_headers': {
                    'Accept-Language': 'en-US,en;q=0.9',
                },
            }
            
            # 添加用户数据目录
            if self.user_data_dir:
                user_dir = self.user_data_dir / instance_id
                user_dir.mkdir(parents=True, exist_ok=True)
                # 注意：Playwright 的用户数据目录需要在启动时指定
            
            context = await browser.new_context(**context_options)
            
            # 创建页面
            page = await context.new_page()
            
            # 设置页面配置
            await self._configure_page(page)
            
            # 创建实例对象
            instance = BrowserInstance(
                instance_id=instance_id,
                browser=browser,
                context=context,
                page=page,
                status=BrowserStatus.IDLE
            )
            
            # 注册实例
            self.instances[instance_id] = instance
            self.instance_pool.append(instance_id)
            
            self.logger.info(f"浏览器实例创建成功: {instance_id}")
            return instance
            
        except Exception as e:
            self.logger.error(f"创建浏览器实例失败: {e}")
            raise BrowserException(f"创建实例失败: {e}")
    
    async def _configure_page(self, page: Page):
        """配置页面设置"""
        try:
            # 设置超时（缩短超时时间）
            page.set_default_timeout(15000)  # 15秒
            page.set_default_navigation_timeout(30000)  # 30秒
            
            # 拦截不必要的资源（保留图片但拦截其他资源）
            await page.route("**/*.{woff,woff2,ttf,eot}", lambda route: route.abort())
            await page.route("**/analytics**", lambda route: route.abort())
            await page.route("**/ads**", lambda route: route.abort())
            await page.route("**/tracking**", lambda route: route.abort())
            
            # 注入反检测和音频控制脚本
            await page.add_init_script("""
                // 移除 webdriver 属性
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                // 修改 plugins 长度
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                // 修改 languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
                
                // 静音所有音频和视频
                const originalPlay = HTMLMediaElement.prototype.play;
                HTMLMediaElement.prototype.play = function() {
                    this.muted = true;
                    this.volume = 0;
                    return originalPlay.call(this);
                };
                
                // 监听新添加的媒体元素
                const observer = new MutationObserver(function(mutations) {
                    mutations.forEach(function(mutation) {
                        mutation.addedNodes.forEach(function(node) {
                            if (node.tagName === 'VIDEO' || node.tagName === 'AUDIO') {
                                node.muted = true;
                                node.volume = 0;
                            }
                        });
                    });
                });
                observer.observe(document.body, { childList: true, subtree: true });
            """)
            
        except Exception as e:
            self.logger.warning(f"页面配置失败: {e}")
    
    async def get_available_instance(self, timeout: float = 30.0) -> Optional[BrowserInstance]:
        """获取可用的浏览器实例"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # 检查现有可用实例
            for instance_id in self.instance_pool.copy():
                if instance_id in self.instances:
                    instance = self.instances[instance_id]
                    if instance.status == BrowserStatus.IDLE and instance.is_healthy:
                        # 标记为忙碌
                        instance.status = BrowserStatus.BUSY
                        instance.last_used_at = datetime.now()
                        self.instance_pool.remove(instance_id)
                        
                        self.logger.debug(f"分配浏览器实例: {instance_id}")
                        return instance
            
            # 如果没有可用实例且未达到最大数量，创建新实例
            if len(self.instances) < self.max_instances:
                try:
                    instance_id = f"browser_{int(time.time())}_{len(self.instances)}"
                    instance = await self._create_browser_instance(instance_id)
                    instance.status = BrowserStatus.BUSY
                    instance.last_used_at = datetime.now()
                    return instance
                except Exception as e:
                    self.logger.error(f"创建新实例失败: {e}")
            
            # 等待一段时间后重试
            await asyncio.sleep(1.0)
        
        self.logger.warning("获取可用浏览器实例超时")
        return None
    
    async def release_instance(self, instance: BrowserInstance):
        """释放浏览器实例"""
        try:
            if instance.instance_id in self.instances:
                instance.status = BrowserStatus.IDLE
                
                # 更新性能指标
                await self._update_performance_metrics(instance)
                
                # 检查实例健康状态
                if instance.is_healthy:
                    if instance.instance_id not in self.instance_pool:
                        self.instance_pool.append(instance.instance_id)
                    self.logger.debug(f"释放浏览器实例: {instance.instance_id}")
                else:
                    # 不健康的实例需要重启
                    await self._restart_instance(instance)
            
        except Exception as e:
            self.logger.error(f"释放实例失败: {e}")
            handle_exception(e, {"instance_id": instance.instance_id})
    
    async def _update_performance_metrics(self, instance: BrowserInstance):
        """更新性能指标"""
        try:
            if not self.monitoring_enabled:
                return
            
            # 获取内存使用情况
            process = psutil.Process()
            memory_info = process.memory_info()
            instance.memory_usage_mb = memory_info.rss / 1024 / 1024
            
            # 获取CPU使用情况
            instance.cpu_usage_percent = process.cpu_percent()
            
        except Exception as e:
            self.logger.debug(f"更新性能指标失败: {e}")
    
    async def _restart_instance(self, instance: BrowserInstance):
        """重启浏览器实例"""
        try:
            instance.status = BrowserStatus.RESTARTING
            instance.restart_count += 1
            
            self.logger.info(f"重启浏览器实例: {instance.instance_id}")
            
            # 关闭现有实例
            await self._close_instance(instance)
            
            # 创建新实例
            new_instance = await self._create_browser_instance(instance.instance_id)
            
            # 保留统计信息
            new_instance.total_requests = instance.total_requests
            new_instance.successful_requests = instance.successful_requests
            new_instance.failed_requests = instance.failed_requests
            new_instance.restart_count = instance.restart_count
            
            self.logger.info(f"浏览器实例重启成功: {instance.instance_id}")
            
        except Exception as e:
            self.logger.error(f"重启实例失败: {e}")
            # 从池中移除失败的实例
            if instance.instance_id in self.instances:
                del self.instances[instance.instance_id]
            if instance.instance_id in self.instance_pool:
                self.instance_pool.remove(instance.instance_id)
    
    async def _close_instance(self, instance: BrowserInstance):
        """关闭浏览器实例"""
        try:
            instance.status = BrowserStatus.CLOSED
            
            if instance.page:
                await instance.page.close()
            if instance.context:
                await instance.context.close()
            if instance.browser:
                await instance.browser.close()
            
            self.logger.debug(f"浏览器实例已关闭: {instance.instance_id}")
            
        except Exception as e:
            self.logger.warning(f"关闭实例时出错: {e}")
    
    async def navigate_to_page(self, instance: BrowserInstance, url: str, 
                              wait_for: str = None, timeout: float = 30.0) -> bool:
        """导航到指定页面"""
        try:
            start_time = time.time()
            
            # 记录请求
            instance.total_requests += 1
            
            # 导航到页面
            response = await instance.page.goto(url, timeout=timeout * 1000)
            
            # 等待特定元素或条件
            if wait_for:
                await instance.page.wait_for_selector(wait_for, timeout=timeout * 1000)
            else:
                await instance.page.wait_for_load_state('networkidle', timeout=timeout * 1000)
            
            # 记录页面加载时间
            instance.page_load_time = time.time() - start_time
            
            # 检查响应状态
            if response and response.status >= 400:
                raise NetworkException(f"HTTP错误: {response.status}")
            
            instance.successful_requests += 1
            self.logger.debug(f"成功导航到: {url}")
            return True
            
        except Exception as e:
            instance.failed_requests += 1
            instance.last_error = str(e)
            instance.error_count += 1
            
            self.logger.error(f"导航失败 {url}: {e}")
            handle_exception(e, {"url": url, "instance_id": instance.instance_id})
            return False
    
    async def execute_script(self, instance: BrowserInstance, script: str) -> Any:
        """执行JavaScript脚本"""
        try:
            result = await instance.page.evaluate(script)
            return result
        except Exception as e:
            self.logger.error(f"脚本执行失败: {e}")
            handle_exception(e, {"script": script[:100], "instance_id": instance.instance_id})
            return None
    
    async def wait_for_element(self, instance: BrowserInstance, selector: str, 
                              timeout: float = 10.0) -> bool:
        """等待元素出现"""
        try:
            await instance.page.wait_for_selector(selector, timeout=timeout * 1000)
            return True
        except Exception as e:
            self.logger.debug(f"等待元素超时: {selector}")
            return False
    
    async def get_page_content(self, instance: BrowserInstance) -> str:
        """获取页面内容"""
        try:
            return await instance.page.content()
        except Exception as e:
            self.logger.error(f"获取页面内容失败: {e}")
            return ""
    
    async def take_screenshot(self, instance: BrowserInstance, path: str = None) -> bytes:
        """截图"""
        try:
            screenshot_options = {'full_page': True}
            if path:
                screenshot_options['path'] = path
            
            return await instance.page.screenshot(**screenshot_options)
        except Exception as e:
            self.logger.error(f"截图失败: {e}")
            return b''
    
    async def cleanup_instances(self, force: bool = False):
        """清理实例"""
        try:
            current_time = datetime.now()
            
            # 检查是否需要清理
            if not force and (current_time - self.last_cleanup_time).total_seconds() < self.cleanup_interval_hours * 3600:
                return
            
            self.logger.info("开始清理浏览器实例")
            
            instances_to_remove = []
            
            for instance_id, instance in self.instances.items():
                should_remove = False
                
                # 检查不健康的实例
                if not instance.is_healthy:
                    should_remove = True
                    self.logger.info(f"移除不健康实例: {instance_id}")
                
                # 检查长时间未使用的实例
                elif instance.last_used_at:
                    idle_hours = (current_time - instance.last_used_at).total_seconds() / 3600
                    if idle_hours > 4:  # 4小时未使用
                        should_remove = True
                        self.logger.info(f"移除长时间未使用实例: {instance_id}")
                
                # 检查运行时间过长的实例
                elif instance.uptime_hours > 12:  # 运行超过12小时
                    should_remove = True
                    self.logger.info(f"移除长时间运行实例: {instance_id}")
                
                if should_remove:
                    instances_to_remove.append(instance_id)
            
            # 移除实例
            for instance_id in instances_to_remove:
                if instance_id in self.instances:
                    await self._close_instance(self.instances[instance_id])
                    del self.instances[instance_id]
                
                if instance_id in self.instance_pool:
                    self.instance_pool.remove(instance_id)
            
            self.last_cleanup_time = current_time
            
            if instances_to_remove:
                self.logger.info(f"清理完成，移除了 {len(instances_to_remove)} 个实例")
            
        except Exception as e:
            self.logger.error(f"清理实例失败: {e}")
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_instances = len(self.instances)
        if total_instances == 0:
            return {"total_instances": 0}
        
        # 状态分布
        status_counts = {}
        for status in BrowserStatus:
            status_counts[status.value] = sum(
                1 for instance in self.instances.values()
                if instance.status == status
            )
        
        # 性能统计
        total_requests = sum(instance.total_requests for instance in self.instances.values())
        successful_requests = sum(instance.successful_requests for instance in self.instances.values())
        total_memory = sum(instance.memory_usage_mb for instance in self.instances.values())
        avg_cpu = sum(instance.cpu_usage_percent for instance in self.instances.values()) / total_instances
        
        return {
            "total_instances": total_instances,
            "available_instances": len(self.instance_pool),
            "status_distribution": status_counts,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "success_rate": (successful_requests / total_requests * 100) if total_requests > 0 else 0,
            "total_memory_mb": total_memory,
            "average_cpu_percent": avg_cpu,
            "average_uptime_hours": sum(instance.uptime_hours for instance in self.instances.values()) / total_instances,
        }
    
    async def close_all(self):
        """关闭所有浏览器实例"""
        try:
            self.logger.info("关闭所有浏览器实例")
            
            # 关闭所有实例
            for instance in self.instances.values():
                await self._close_instance(instance)
            
            # 清空数据
            self.instances.clear()
            self.instance_pool.clear()
            
            # 关闭 Playwright
            if self.playwright:
                await self.playwright.stop()
            
            self.logger.info("所有浏览器实例已关闭")
            
        except Exception as e:
            self.logger.error(f"关闭浏览器实例失败: {e}")
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close_all()


# 使用示例
if __name__ == "__main__":
    async def test_browser_manager():
        async with BrowserManager(max_instances=2, headless=True) as manager:
            # 获取浏览器实例
            instance = await manager.get_available_instance()
            if instance:
                # 导航到页面
                success = await manager.navigate_to_page(instance, "https://twitter.com")
                if success:
                    print("导航成功")
                
                # 释放实例
                await manager.release_instance(instance)
            
            # 获取统计信息
            stats = await manager.get_statistics()
            print(f"统计信息: {stats}")
    
    # 运行测试
    # asyncio.run(test_browser_manager())