# -*- coding: utf-8 -*-
"""
增强防封号机制
提供完整的反检测和人类行为模拟功能
包括智能延时、指纹伪装、行为模拟、错误恢复等
"""

import asyncio
import random
import time
import json
import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from playwright.async_api import Page, Browser, BrowserContext
import numpy as np


class DetectionLevel(Enum):
    """检测风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class BehaviorPattern(Enum):
    """行为模式"""
    CASUAL_READER = "casual_reader"      # 休闲阅读者
    ACTIVE_USER = "active_user"          # 活跃用户
    RESEARCHER = "researcher"            # 研究者
    POWER_USER = "power_user"            # 重度用户


@dataclass
class MouseTrajectory:
    """鼠标轨迹数据"""
    points: List[Tuple[float, float]] = field(default_factory=list)
    duration: float = 0.0
    curve_factor: float = 0.3
    noise_factor: float = 0.1


@dataclass
class BehaviorProfile:
    """行为档案"""
    pattern: BehaviorPattern
    reading_speed_wpm: int = 200  # 每分钟阅读字数
    scroll_speed: float = 1.0     # 滚动速度倍数
    interaction_probability: float = 0.3  # 交互概率
    attention_span_seconds: int = 30      # 注意力持续时间
    break_frequency_minutes: int = 15     # 休息频率
    
    # 延时参数
    min_action_delay: float = 0.5
    max_action_delay: float = 3.0
    min_page_delay: float = 2.0
    max_page_delay: float = 8.0


class EnhancedAntiBlocking:
    """增强防封号机制"""
    
    def __init__(self, page: Page, behavior_pattern: BehaviorPattern = BehaviorPattern.CASUAL_READER):
        self.page = page
        self.logger = logging.getLogger(__name__)
        
        # 行为配置
        self.behavior_profile = self._create_behavior_profile(behavior_pattern)
        self.session_start_time = datetime.now()
        self.last_action_time = datetime.now()
        self.action_count = 0
        self.detection_level = DetectionLevel.LOW
        
        # 用户代理池
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0'
        ]
        
        # 指纹伪装配置
        self.fingerprint_config = {
            'screen_resolutions': [
                (1920, 1080), (1366, 768), (1440, 900), (1536, 864),
                (1280, 720), (1600, 900), (2560, 1440), (1920, 1200)
            ],
            'timezones': [
                'America/New_York', 'America/Los_Angeles', 'Europe/London',
                'Europe/Paris', 'Asia/Tokyo', 'Asia/Shanghai', 'Australia/Sydney'
            ],
            'languages': [
                'en-US,en;q=0.9', 'zh-CN,zh;q=0.9,en;q=0.8',
                'en-GB,en;q=0.9', 'ja-JP,ja;q=0.9,en;q=0.8'
            ]
        }
        
        # 状态跟踪
        self.page_load_times = []
        self.scroll_positions = []
        self.interaction_history = []
        self.error_count = 0
        self.last_error_time = None
        
        # 反检测策略
        self.anti_detection_strategies = {
            'rate_limiting': True,
            'behavior_randomization': True,
            'fingerprint_rotation': True,
            'session_management': True,
            'error_recovery': True
        }
    
    def _create_behavior_profile(self, pattern: BehaviorPattern) -> BehaviorProfile:
        """创建行为档案"""
        profiles = {
            BehaviorPattern.CASUAL_READER: BehaviorProfile(
                pattern=pattern,
                reading_speed_wpm=180,
                scroll_speed=0.8,
                interaction_probability=0.2,
                attention_span_seconds=25,
                break_frequency_minutes=20,
                min_action_delay=1.0,
                max_action_delay=4.0,
                min_page_delay=3.0,
                max_page_delay=10.0
            ),
            BehaviorPattern.ACTIVE_USER: BehaviorProfile(
                pattern=pattern,
                reading_speed_wpm=220,
                scroll_speed=1.2,
                interaction_probability=0.4,
                attention_span_seconds=45,
                break_frequency_minutes=15,
                min_action_delay=0.5,
                max_action_delay=2.5,
                min_page_delay=2.0,
                max_page_delay=6.0
            ),
            BehaviorPattern.RESEARCHER: BehaviorProfile(
                pattern=pattern,
                reading_speed_wpm=160,
                scroll_speed=0.6,
                interaction_probability=0.6,
                attention_span_seconds=90,
                break_frequency_minutes=30,
                min_action_delay=1.5,
                max_action_delay=5.0,
                min_page_delay=4.0,
                max_page_delay=12.0
            ),
            BehaviorPattern.POWER_USER: BehaviorProfile(
                pattern=pattern,
                reading_speed_wpm=280,
                scroll_speed=1.5,
                interaction_probability=0.3,
                attention_span_seconds=60,
                break_frequency_minutes=10,
                min_action_delay=0.3,
                max_action_delay=1.5,
                min_page_delay=1.0,
                max_page_delay=4.0
            )
        }
        return profiles.get(pattern, profiles[BehaviorPattern.CASUAL_READER])
    
    async def initialize_session(self) -> None:
        """初始化会话"""
        try:
            self.logger.info(f"初始化防封号会话，行为模式: {self.behavior_profile.pattern.value}")
            
            # 设置基础指纹
            await self._setup_browser_fingerprint()
            
            # 注入反检测脚本
            await self._inject_anti_detection_scripts()
            
            # 设置事件监听
            await self._setup_event_listeners()
            
            self.logger.info("防封号会话初始化完成")
            
        except Exception as e:
            self.logger.error(f"会话初始化失败: {e}")
            raise
    
    async def _setup_browser_fingerprint(self) -> None:
        """设置浏览器指纹"""
        try:
            # 随机选择屏幕分辨率
            width, height = random.choice(self.fingerprint_config['screen_resolutions'])
            await self.page.set_viewport_size({"width": width, "height": height})
            
            # 设置随机用户代理
            user_agent = random.choice(self.user_agents)
            await self.page.set_extra_http_headers({
                'User-Agent': user_agent,
                'Accept-Language': random.choice(self.fingerprint_config['languages']),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            })
            
            # 设置时区
            timezone = random.choice(self.fingerprint_config['timezones'])
            await self.page.emulate_timezone(timezone)
            
            self.logger.debug(f"浏览器指纹设置完成: {width}x{height}, {user_agent[:50]}...")
            
        except Exception as e:
            self.logger.error(f"指纹设置失败: {e}")
    
    async def _inject_anti_detection_scripts(self) -> None:
        """注入反检测脚本"""
        try:
            # 反自动化检测
            await self.page.add_init_script("""
                // 移除webdriver标识
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                // 伪造插件信息
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                // 伪造语言信息
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
                
                // 移除自动化相关属性
                window.chrome = {
                    runtime: {},
                };
                
                // 伪造权限API
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            """)
            
            # 鼠标和键盘事件伪造
            await self.page.add_init_script("""
                // 添加真实的鼠标移动事件
                let mouseX = 0, mouseY = 0;
                document.addEventListener('mousemove', (e) => {
                    mouseX = e.clientX;
                    mouseY = e.clientY;
                });
                
                // 伪造触摸事件支持
                Object.defineProperty(navigator, 'maxTouchPoints', {
                    get: () => 1,
                });
            """)
            
            self.logger.debug("反检测脚本注入完成")
            
        except Exception as e:
            self.logger.error(f"脚本注入失败: {e}")
    
    async def _setup_event_listeners(self) -> None:
        """设置事件监听器"""
        try:
            # 监听页面加载事件
            self.page.on('load', self._on_page_load)
            self.page.on('response', self._on_response)
            
        except Exception as e:
            self.logger.error(f"事件监听器设置失败: {e}")
    
    def _on_page_load(self, page) -> None:
        """页面加载事件处理"""
        load_time = time.time()
        self.page_load_times.append(load_time)
        self.logger.debug(f"页面加载完成: {page.url}")
    
    def _on_response(self, response) -> None:
        """响应事件处理"""
        if response.status >= 400:
            self.error_count += 1
            self.last_error_time = datetime.now()
            if response.status in [429, 503, 403]:
                self.detection_level = DetectionLevel.HIGH
                self.logger.warning(f"检测到可能的封禁响应: {response.status}")
    
    async def smart_delay(self, action_type: str = "default", content_length: int = 0) -> None:
        """智能延时策略"""
        try:
            base_delay = self._calculate_base_delay(action_type, content_length)
            
            # 根据检测风险等级调整延时
            risk_multiplier = {
                DetectionLevel.LOW: 1.0,
                DetectionLevel.MEDIUM: 1.5,
                DetectionLevel.HIGH: 2.5,
                DetectionLevel.CRITICAL: 4.0
            }.get(self.detection_level, 1.0)
            
            # 添加随机性
            randomness = random.uniform(0.7, 1.3)
            
            # 考虑行为模式
            pattern_multiplier = {
                BehaviorPattern.CASUAL_READER: 1.2,
                BehaviorPattern.ACTIVE_USER: 0.8,
                BehaviorPattern.RESEARCHER: 1.5,
                BehaviorPattern.POWER_USER: 0.6
            }.get(self.behavior_profile.pattern, 1.0)
            
            final_delay = base_delay * risk_multiplier * randomness * pattern_multiplier
            
            # 限制延时范围
            min_delay = self.behavior_profile.min_action_delay
            max_delay = self.behavior_profile.max_action_delay
            final_delay = max(min_delay, min(max_delay, final_delay))
            
            self.logger.debug(f"智能延时: {final_delay:.2f}s (类型: {action_type}, 风险: {self.detection_level.value})")
            
            await asyncio.sleep(final_delay)
            self.last_action_time = datetime.now()
            self.action_count += 1
            
        except Exception as e:
            self.logger.error(f"智能延时失败: {e}")
            await asyncio.sleep(1.0)  # fallback延时
    
    def _calculate_base_delay(