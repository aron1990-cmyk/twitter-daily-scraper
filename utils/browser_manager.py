#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
浏览器管理模块 - 负责浏览器实例的创建、管理、会话保持和资源清理
支持多浏览器实例、会话复用、自动重启和性能监控
集成资源调度和智能清理功能
"""

import asyncio
import logging
import time
import psutil
import gc  # P0+优化：添加垃圾回收模块
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

# 导入新的管理器
from .browser_cleanup_manager import get_cleanup_manager
from .resource_scheduler import get_resource_scheduler, ScheduleAction
from .async_task_manager import get_task_manager, TaskType, TaskPriority


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
    
    def __init__(self, max_instances: int = 2, headless: bool = True, 
                 user_data_dir: str = None, proxy_config: Dict[str, str] = None):
        self.max_instances = max_instances  # P0+优化：限制为2个实例
        self.headless = headless
        self.user_data_dir = Path(user_data_dir) if user_data_dir else None
        self.proxy_config = proxy_config
        
        self.logger = logging.getLogger(__name__)
        self.playwright = None
        self.instances: Dict[str, BrowserInstance] = {}
        self.instance_pool: List[str] = []  # 可用实例池
        
        # 集成资源管理器
        self.cleanup_manager = get_cleanup_manager()
        self.resource_scheduler = get_resource_scheduler()
        self.task_manager = get_task_manager()
        
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
        
        # 性能监控 - P0+优化增强
        self.monitoring_enabled = True
        self.last_cleanup_time = datetime.now()
        self.cleanup_interval_hours = 0.25  # P0+优化：进一步缩短到15分钟
        self.max_idle_minutes = 1  # P0+优化：最大空闲时间缩短到1分钟
        self.max_runtime_hours = 3  # P0+优化：最大运行时间缩短到3小时
        self.memory_threshold_mb = 200  # P0+优化：内存阈值降低到200MB
        
        # P0+新增：懒加载和强制清理配置
        self.lazy_loading = True  # 启用懒加载
        self.force_gc_interval = 300  # 强制GC间隔（秒）
        self.last_gc_time = datetime.now()
        self.idle_detection_interval = 30  # 空闲检测间隔（秒）
    
    async def initialize(self):
        """初始化浏览器管理器"""
        try:
            self.playwright = await async_playwright().start()
            self.logger.info("浏览器管理器初始化成功")
            
            # P0+优化：启动定期清理和GC任务
            if self.lazy_loading:
                asyncio.create_task(self._periodic_gc_and_cleanup())
            
            # 创建初始实例（懒加载模式下只创建1个）
            initial_count = 1 if self.lazy_loading else 1
            await self._create_initial_instances(initial_count)
            
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
    
    async def get_available_instance(self, timeout: float = 30.0, task_priority: int = 2) -> Optional[BrowserInstance]:
        """获取可用的浏览器实例（集成资源调度）"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # 获取资源调度决策
            schedule_decision = self.resource_scheduler.make_schedule_decision(
                task_type="browser_task", 
                task_priority=task_priority
            )
            
            # 根据调度决策处理
            if schedule_decision.action == ScheduleAction.EMERGENCY_STOP:
                self.logger.warning(f"系统资源紧张，停止分配浏览器实例: {schedule_decision.reason}")
                return None
            elif schedule_decision.action == ScheduleAction.PAUSE:
                self.logger.info(f"系统资源不足，暂停分配实例: {schedule_decision.reason}")
                await asyncio.sleep(schedule_decision.delay_seconds)
                continue
            elif schedule_decision.action == ScheduleAction.THROTTLE:
                self.logger.debug(f"系统资源紧张，限流处理: {schedule_decision.reason}")
                # 调整最大实例数
                effective_max_instances = min(self.max_instances, schedule_decision.max_concurrent_tasks)
            else:
                effective_max_instances = self.max_instances
            
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
            
            # 如果没有可用实例且未达到有效最大数量，创建新实例
            if len(self.instances) < effective_max_instances:
                try:
                    instance_id = f"browser_{int(time.time())}_{len(self.instances)}"
                    instance = await self._create_browser_instance(instance_id)
                    instance.status = BrowserStatus.BUSY
                    instance.last_used_at = datetime.now()
                    return instance
                except Exception as e:
                    self.logger.error(f"创建新实例失败: {e}")
            
            # 应用调度延迟
            delay = max(1.0, schedule_decision.delay_seconds)
            await asyncio.sleep(delay)
        
        self.logger.warning("获取可用浏览器实例超时")
        return None
    
    async def release_instance(self, instance: BrowserInstance, force_cleanup: bool = False):
        """释放浏览器实例（集成清理管理器）"""
        if not instance or instance.instance_id not in self.instances:
            return
        
        try:
            # 更新性能指标
            if self.monitoring_enabled:
                await self._update_performance_metrics(instance)
            
            # 执行清理检查
            if force_cleanup or not instance.is_healthy:
                self.logger.info(f"对实例 {instance.instance_id} 执行强制清理")
                
                # 异步执行清理任务
                cleanup_task = self.task_manager.submit_task(
                    func=self._cleanup_instance,
                    args=(instance.instance_id,),
                    kwargs={
                        'browser_pid': getattr(instance.browser, '_impl_obj', {}).get('_connection', {}).get('_transport', {}).get('_proc', {}).get('pid') if instance.browser else None
                    },
                    task_type=TaskType.CUSTOM,
                    priority=TaskPriority.HIGH,
                    metadata={'description': f"清理浏览器实例 {instance.instance_id}"}
                )
                
                # 执行清理
                await self._execute_cleanup(instance)
                return
            
            # 检查实例健康状态
            health_status = self.cleanup_manager.get_browser_health_status()
            if health_status['zombie_processes'] > 0 or health_status['memory_usage_mb'] > 1000:
                self.logger.warning(f"检测到系统资源异常，对实例 {instance.instance_id} 执行预防性清理")
                await self._execute_cleanup(instance)
                return
            
            # 标记为空闲并加入可用池
            instance.status = BrowserStatus.IDLE
            instance.last_used_at = datetime.now()
            
            if instance.instance_id not in self.instance_pool:
                self.instance_pool.append(instance.instance_id)
            
            self.logger.debug(f"释放浏览器实例: {instance.instance_id}")
            
        except Exception as e:
            self.logger.error(f"释放实例失败: {e}")
            # 如果释放失败，执行强制清理
            await self._execute_cleanup(instance)
    
    async def _execute_cleanup(self, instance: BrowserInstance):
        """执行实例清理"""
        try:
            # 使用清理管理器清理实例
            await self.cleanup_manager.cleanup_browser_instance(instance.instance_id)
            
            # 从实例池中移除
            if instance.instance_id in self.instance_pool:
                self.instance_pool.remove(instance.instance_id)
            
            # 关闭实例
            await self._close_instance(instance)
            
            # 从实例字典中移除
            if instance.instance_id in self.instances:
                del self.instances[instance.instance_id]
            
            self.logger.info(f"实例清理完成: {instance.instance_id}")
            
        except Exception as e:
            self.logger.error(f"执行清理失败: {e}")
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
        """清理实例（集成清理管理器功能）"""
        try:
            current_time = datetime.now()
            
            # 检查是否需要清理
            if not force and (current_time - self.last_cleanup_time).total_seconds() < self.cleanup_interval_hours * 3600:
                return
            
            self.logger.info("开始清理浏览器实例")
            
            # 获取系统健康状态
            health_status = self.cleanup_manager.get_browser_health_status()
            system_health = self.resource_scheduler.get_resource_status()
            
            # 如果系统资源紧张，更积极地清理实例
            aggressive_cleanup = (
                system_health.memory_usage > 80 or 
                system_health.cpu_usage > 85 or
                health_status['zombie_processes'] > 0
            )
            
            instances_to_remove = []
            
            for instance_id, instance in self.instances.items():
                should_remove = False
                
                # 检查不健康的实例
                if not instance.is_healthy:
                    should_remove = True
                    self.logger.info(f"移除不健康实例: {instance_id}")
                
                # P0优化：检查内存使用过高的实例
                elif instance.memory_usage_mb and instance.memory_usage_mb > self.memory_threshold_mb:
                    should_remove = True
                    self.logger.info(f"[P0优化] 移除高内存使用实例: {instance_id} (内存使用: {instance.memory_usage_mb:.1f}MB)")
                
                # P0优化：检查长时间未使用的实例（改为分钟级别）
                elif instance.last_used_at:
                    idle_minutes = (current_time - instance.last_used_at).total_seconds() / 60
                    idle_threshold = self.max_idle_minutes if aggressive_cleanup else self.max_idle_minutes * 2
                    if idle_minutes > idle_threshold:
                        should_remove = True
                        self.logger.info(f"[P0优化] 移除长时间未使用实例: {instance_id} (空闲 {idle_minutes:.1f} 分钟)")
                
                # P0优化：检查运行时间过长的实例（从12小时改为6小时）
                elif instance.uptime_hours > self.max_runtime_hours:
                    should_remove = True
                    self.logger.info(f"[P0优化] 移除长时间运行实例: {instance_id} (运行时间: {instance.uptime_hours:.1f}小时)")
                
                # P0优化：资源紧张时的额外清理条件（从5分钟改为2分钟）
                elif aggressive_cleanup and instance.status == BrowserStatus.IDLE:
                    idle_minutes = (current_time - instance.last_used_at).total_seconds() / 60 if instance.last_used_at else 0
                    if idle_minutes > self.max_idle_minutes:  # P0优化：使用配置的清理阈值
                        should_remove = True
                        self.logger.info(f"[P0优化] 资源紧张，移除空闲实例: {instance_id} (空闲 {idle_minutes:.1f} 分钟)")
                
                if should_remove:
                    instances_to_remove.append(instance_id)
            
            # 异步清理标记的实例
            cleanup_tasks = []
            for instance_id in instances_to_remove:
                if instance_id in self.instances:
                    instance = self.instances[instance_id]
                    
                    # 提交异步清理任务
                    cleanup_task = self.task_manager.submit_task(
                        func=self._cleanup_instance,
                        args=(instance_id,),
                        kwargs={'reason': 'scheduled_cleanup'},
                        task_type=TaskType.CUSTOM,
                        priority=TaskPriority.MEDIUM,
                        metadata={'description': f"定期清理实例 {instance_id}"}
                    )
                    cleanup_tasks.append(self._execute_cleanup(instance))
            
            # 等待所有清理任务完成
            if cleanup_tasks:
                await asyncio.gather(*cleanup_tasks, return_exceptions=True)
            
            # 执行系统级清理
            if aggressive_cleanup:
                self.logger.info("执行系统级浏览器清理")
                await self.cleanup_manager.auto_cleanup()
            
            self.last_cleanup_time = current_time
            
            if instances_to_remove:
                self.logger.info(f"清理完成，移除了 {len(instances_to_remove)} 个实例")
            
            self.logger.debug(f"清理完成，剩余实例数: {len(self.instances)}，系统健康状态: CPU {system_health.cpu_usage:.1f}%, 内存 {system_health.memory_usage:.1f}%")
            
        except Exception as e:
            self.logger.error(f"清理实例失败: {e}")
    
    async def _periodic_gc_and_cleanup(self):
        """P0+优化：定期垃圾回收和清理任务"""
        self.logger.info("启动定期GC和清理任务")
        
        while True:
            try:
                current_time = datetime.now()
                
                # 强制垃圾回收
                if (current_time - self.last_gc_time).total_seconds() >= self.force_gc_interval:
                    await self._force_garbage_collection()
                    self.last_gc_time = current_time
                
                # 空闲检测和清理
                await self._idle_detection_cleanup()
                
                # 等待下一次检查
                await asyncio.sleep(self.idle_detection_interval)
                
            except Exception as e:
                self.logger.error(f"定期GC和清理任务异常: {e}")
                await asyncio.sleep(60)  # 出错时等待1分钟再重试
    
    async def _force_garbage_collection(self):
        """P0+优化：强制垃圾回收"""
        try:
            # 记录GC前的内存使用
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024
            
            # 执行垃圾回收
            collected = gc.collect()
            
            # 记录GC后的内存使用
            memory_after = process.memory_info().rss / 1024 / 1024
            memory_freed = memory_before - memory_after
            
            self.logger.info(f"[P0+优化] 强制GC完成: 回收对象 {collected} 个，释放内存 {memory_freed:.2f}MB")
            
        except Exception as e:
            self.logger.error(f"强制GC失败: {e}")
    
    async def _idle_detection_cleanup(self):
        """P0+优化：空闲检测和清理"""
        try:
            current_time = datetime.now()
            idle_instances = []
            
            for instance_id, instance in self.instances.items():
                if instance.status == BrowserStatus.IDLE and instance.last_used_at:
                    idle_minutes = (current_time - instance.last_used_at).total_seconds() / 60
                    
                    # 检查是否超过空闲阈值
                    if idle_minutes > self.max_idle_minutes:
                        idle_instances.append((instance_id, instance, idle_minutes))
            
            # 清理超时空闲实例
            for instance_id, instance, idle_minutes in idle_instances:
                self.logger.info(f"[P0+优化] 清理超时空闲实例: {instance_id} (空闲 {idle_minutes:.1f} 分钟)")
                await self._execute_cleanup(instance)
            
            # 检查系统内存压力
            system_memory = psutil.virtual_memory()
            if system_memory.percent > 75:  # 内存使用超过75%时积极清理
                self.logger.warning(f"[P0+优化] 系统内存压力过高 ({system_memory.percent:.1f}%)，执行积极清理")
                await self.cleanup_instances(force=True)
                
        except Exception as e:
            self.logger.error(f"空闲检测清理失败: {e}")
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息（集成资源调度信息）"""
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
        
        # 获取资源调度器统计信息
        resource_stats = self.resource_scheduler.get_resource_status()
        schedule_stats = self.resource_scheduler.get_statistics()
        
        # 获取清理管理器健康状态
        health_status = self.cleanup_manager.get_browser_health_status()
        
        # 获取任务管理器统计信息
        task_stats = self.task_manager.get_statistics()
        
        return {
            # 基础统计
            "total_instances": total_instances,
            "available_instances": len(self.instance_pool),
            "status_distribution": status_counts,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "success_rate": (successful_requests / total_requests * 100) if total_requests > 0 else 0,
            "total_memory_mb": total_memory,
            "average_cpu_percent": avg_cpu,
            "average_uptime_hours": sum(instance.uptime_hours for instance in self.instances.values()) / total_instances,
            
            # 资源调度统计
            "resource_status": {
                "cpu_usage": resource_stats.cpu_usage,
                "memory_usage": resource_stats.memory_usage,
                "disk_usage": resource_stats.disk_usage,
                "network_usage": resource_stats.network_usage,
                "resource_level": resource_stats.level.value
            },
            "schedule_statistics": {
                "total_decisions": schedule_stats['total_decisions'],
                "action_counts": schedule_stats['action_counts'],
                "average_decision_time": schedule_stats['average_decision_time']
            },
            
            # 健康状态
            "health_status": health_status,
            
            # 任务管理统计
            "task_statistics": {
                "pending_tasks": task_stats['pending_tasks'],
                "running_tasks": task_stats['running_tasks'],
                "completed_tasks": task_stats['completed_tasks'],
                "failed_tasks": task_stats['failed_tasks']
            }
        }
    
    async def close_all(self):
        """关闭所有浏览器实例（集成清理管理器）"""
        try:
            self.logger.info("开始关闭所有浏览器实例")
            
            # 停止任务管理器
            await self.task_manager.stop()
            
            # 关闭所有实例
            close_tasks = []
            for instance in list(self.instances.values()):
                try:
                    close_tasks.append(self._close_instance(instance))
                except Exception as e:
                    self.logger.error(f"准备关闭实例 {instance.instance_id} 失败: {e}")
            
            # 并行关闭所有实例
            if close_tasks:
                await asyncio.gather(*close_tasks, return_exceptions=True)
            
            # 执行系统级清理
            self.logger.info("执行系统级浏览器清理")
            await self.cleanup_manager.auto_cleanup()
            
            # 强制清理所有相关进程
            await self.cleanup_manager.cleanup_adspower_processes()
            
            # 清空数据
            self.instances.clear()
            self.instance_pool.clear()
            
            # 关闭 Playwright
            if self.playwright:
                try:
                    await self.playwright.stop()
                    self.playwright = None
                except Exception as e:
                    self.logger.error(f"关闭 Playwright 失败: {e}")
            
            # 停止资源调度器
            self.resource_scheduler.stop()
            
            self.logger.info("所有浏览器实例已关闭，系统清理完成")
            
        except Exception as e:
            self.logger.error(f"关闭所有实例时发生错误: {e}")
            # 即使出错也要尝试强制清理
            try:
                await self.cleanup_manager.auto_cleanup()
            except Exception as cleanup_error:
                self.logger.error(f"强制清理失败: {cleanup_error}")
    
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