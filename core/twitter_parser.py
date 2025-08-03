# -*- coding: utf-8 -*-
"""
Twitter 解析器
使用 Playwright 控制浏览器并抓取推文数据
"""

import asyncio
import logging
import random
import re
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from playwright.async_api import async_playwright, Browser, Page
# 配置将从调用方传入或使用默认配置
from utils.human_behavior_simulator import HumanBehaviorSimulator
# from performance_optimizer import EnhancedSearchOptimizer

class TwitterParser:
    def __init__(self, debug_port: str = None):
        self.debug_port = debug_port
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.behavior_simulator = None
        # self.search_optimizer = EnhancedSearchOptimizer()
        self.logger = logging.getLogger(__name__)
        self.config = None
        
        # 优化功能属性
        self.seen_tweet_ids: Set[str] = set()
        self.content_cache: Dict[str, str] = {}
        self.optimization_enabled = True
    
    async def initialize(self, debug_port: str = None):
        """初始化TwitterParser
        
        Args:
            debug_port: 浏览器调试端口
        """
        if debug_port:
            self.debug_port = debug_port
        
        if not self.debug_port:
            raise ValueError("debug_port is required for initialization")
        
        self.logger.info(f"Initializing TwitterParser with debug_port: {self.debug_port}")
        
        # 连接浏览器
        await self.connect_browser()
        
        self.logger.info("TwitterParser initialization completed")
        
    async def connect_browser(self):
        """
        连接到 AdsPower 浏览器
        """
        try:
            self.logger.info("开始启动 Playwright...")
            playwright = await async_playwright().start()
            
            self.logger.info(f"开始连接到浏览器调试端口: {self.debug_port}")
            # 连接到现有的浏览器实例
            self.browser = await playwright.chromium.connect_over_cdp(self.debug_port)
            self.logger.info("成功连接到浏览器实例")
            
            # 获取现有上下文和页面
            contexts = self.browser.contexts
            self.logger.info(f"找到 {len(contexts)} 个浏览器上下文")
            
            if contexts:
                context = contexts[0]
                pages = context.pages
                self.logger.info(f"在上下文中找到 {len(pages)} 个页面")
                
                if pages:
                    # 使用现有页面
                    self.page = pages[0]
                    try:
                        current_url = self.page.url
                        self.logger.info(f"使用现有页面，当前URL: {current_url}")
                    except Exception as url_error:
                        self.logger.warning(f"无法获取页面URL: {url_error}")
                        # 创建新页面作为备选
                        self.page = await context.new_page()
                        self.logger.info("创建新页面作为备选")
                else:
                    # 在现有上下文中创建新页面
                    self.page = await context.new_page()
                    self.logger.info("在现有上下文中创建新页面")
            else:
                # 创建新的浏览器上下文，设置用户代理和其他选项
                self.logger.info("创建新的浏览器上下文...")
                context = await self.browser.new_context(
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080},
                    extra_http_headers={
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
                    }
                )
                self.page = await context.new_page()
                self.logger.info("创建新的浏览器上下文和页面")
            
            # 设置页面默认超时时间
            default_timeout = 30000
            self.page.set_default_timeout(default_timeout)
            self.logger.info(f"设置页面超时时间: {default_timeout}ms")
            
            # 设置页面导航超时时间
            navigation_timeout = 60000
            self.page.set_default_navigation_timeout(navigation_timeout)
            self.logger.info(f"设置导航超时时间: {navigation_timeout}ms")
            
            # 初始化人工行为模拟器
            self.behavior_simulator = HumanBehaviorSimulator(self.page)
            self.logger.info("人工行为模拟器初始化完成")
            
            self.logger.info("成功连接到浏览器")
            
        except Exception as e:
            self.logger.error(f"连接浏览器失败: {e}")
            raise
    
    async def navigate_to_twitter(self, max_retries: int = 3):
        """
        导航到 Twitter 主页
        
        Args:
            max_retries: 最大重试次数
        """
        for attempt in range(max_retries):
            try:
                # 确保页面焦点
                await self.ensure_page_focus()
                
                current_url = self.page.url
                self.logger.info(f"当前页面URL: {current_url}")
                
                # 检查是否已经在 x.com
                if 'x.com' not in current_url:
                    self.logger.info(f"页面不在 x.com，开始导航... (第{attempt + 1}次尝试)")
                    
                    # 使用更长的超时时间
                    await self.page.goto('https://x.com', timeout=60000)
                    
                    # 分步等待加载
                    try:
                        await self.page.wait_for_load_state('domcontentloaded', timeout=30000)
                        await self.page.wait_for_load_state('networkidle', timeout=30000)
                    except Exception as load_error:
                        self.logger.warning(f"等待加载状态失败: {load_error}，继续尝试")
                    
                    self.logger.info("成功导航到 X (Twitter)")
                else:
                    self.logger.info("页面已经在 X (Twitter)，跳过导航")
                
                # 确保页面焦点后再进行测试
                await self.ensure_page_focus()
                
                # 测试页面交互 - 执行几次下拉操作
                self.logger.info("开始测试页面下拉功能...")
                for i in range(3):
                    # 向下滚动
                    await self.page.evaluate('window.scrollBy(0, 500)')
                    await asyncio.sleep(2)
                    self.logger.info(f"执行第 {i+1} 次下拉")
                
                # 滚动回顶部
                await self.page.evaluate('window.scrollTo(0, 0)')
                await asyncio.sleep(2)
                self.logger.info("页面下拉测试完成，已滚动回顶部")
                return
                
            except Exception as e:
                self.logger.warning(f"第{attempt + 1}次导航尝试失败: {e}")
                
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5
                    self.logger.info(f"等待{wait_time}秒后重试...")
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error(f"导航到 X (Twitter) 失败，已尝试{max_retries}次")
                    raise Exception(f"导航到 X (Twitter) 失败: {e}")
    
    async def navigate_to_profile(self, username: str, max_retries: int = 3):
        """
        导航到指定用户的个人资料页面
        
        Args:
            username: Twitter 用户名（不包含@符号）
            max_retries: 最大重试次数
        """
        profile_url = f'https://x.com/{username}'
        
        for attempt in range(max_retries):
            try:
                # 确保页面焦点
                await self.ensure_page_focus()
                
                self.logger.info(f"尝试导航到 @{username} 的个人资料页面 (第{attempt + 1}次)")
                
                # 使用更长的超时时间进行导航
                await self.page.goto(profile_url, timeout=60000)
                
                # 分步等待加载状态
                try:
                    await self.page.wait_for_load_state('domcontentloaded', timeout=30000)
                    self.logger.info("DOM内容加载完成")
                    
                    await self.page.wait_for_load_state('networkidle', timeout=30000)
                    self.logger.info("网络空闲状态达到")
                except Exception as load_error:
                    self.logger.warning(f"等待加载状态失败: {load_error}，继续尝试")
                
                # 确保页面焦点后再等待
                await self.ensure_page_focus()
                
                # 额外等待时间确保页面完全加载
                await asyncio.sleep(2)
                
                # 检测是否遇到封控
                is_blocked = await self.detect_twitter_blocking()
                if is_blocked:
                    self.logger.warning(f"检测到封控，尝试反封控刷新")
                    await self.anti_blocking_refresh()
                    # 重新等待页面加载
                    await asyncio.sleep(3)
                
                # 验证页面是否正确加载
                current_url = self.page.url
                if username.lower() in current_url.lower():
                    # 再次检查是否有推文元素，如果没有可能需要刷新
                    tweet_elements = await self.page.query_selector_all('[data-testid="tweet"]')
                    if len(tweet_elements) == 0:
                        self.logger.warning(f"页面加载成功但无推文元素，可能需要刷新")
                        await self.anti_blocking_refresh()
                        await asyncio.sleep(2)
                    
                    self.logger.info(f"成功导航到 @{username} 的个人资料页面")
                    return
                else:
                    raise Exception(f"页面URL不匹配，期望包含'{username}'，实际为'{current_url}'")
                
            except Exception as e:
                self.logger.warning(f"第{attempt + 1}次导航尝试失败: {e}")
                
                if attempt < max_retries - 1:
                    # 等待后重试（极速模式）
                    wait_time = (attempt + 1) * 1  # 极短递增等待时间
                    self.logger.info(f"等待{wait_time}秒后重试...")
                    await asyncio.sleep(wait_time)
                else:
                    # 最后一次尝试失败
                    self.logger.error(f"导航到 @{username} 个人资料页面失败，已尝试{max_retries}次")
                    raise Exception(f"导航到 @{username} 个人资料页面失败: {e}")
    
    async def search_tweets(self, keyword: str, max_retries: int = 2):
        """
        搜索包含指定关键词的推文
        
        Args:
            keyword: 搜索关键词
            max_retries: 最大重试次数
        """
        for attempt in range(max_retries + 1):
            try:
                # 确保页面焦点
                await self.ensure_page_focus()
                
                self.logger.info(f"开始搜索关键词 '{keyword}' (第{attempt + 1}次尝试)")
                
                # 构建搜索URL，使用URL编码
                import urllib.parse
                encoded_keyword = urllib.parse.quote(keyword)
                search_url = f'https://x.com/search?q={encoded_keyword}&src=typed_query&f=live'
                self.logger.info(f"搜索URL: {search_url}")
                
                # 导航到搜索页面
                self.logger.info("正在导航到搜索页面...")
                await self.page.goto(search_url, timeout=30000)
                self.logger.info("导航完成，等待页面加载...")
                
                # 简化等待策略
                try:
                    await self.page.wait_for_load_state('domcontentloaded', timeout=10000)
                    self.logger.info("DOM内容加载完成")
                except Exception as load_error:
                    self.logger.warning(f"DOM加载超时: {load_error}")
                
                # 确保页面焦点后再等待搜索结果
                await self.ensure_page_focus()
                
                # 等待搜索结果加载（极速模式）
                self.logger.info("等待搜索结果加载...")
                await asyncio.sleep(2)  # 极短等待时间
                
                # 检查是否有搜索结果
                try:
                    # 等待推文元素出现
                    await self.page.wait_for_selector('[data-testid="tweet"]', timeout=10000)
                    self.logger.info("找到推文元素")
                except Exception:
                    self.logger.warning("未找到推文元素，可能没有搜索结果")
                
                self.logger.info(f"成功搜索关键词: {keyword}")
                return
                
            except Exception as e:
                self.logger.warning(f"第{attempt + 1}次搜索尝试失败: {e}")
                
                if attempt < max_retries:
                    wait_time = (attempt + 1) * 0.8  # 极短重试等待时间
                    self.logger.info(f"等待{wait_time}秒后重试...")
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error(f"搜索关键词 '{keyword}' 失败，已尝试{max_retries + 1}次")
                    raise Exception(f"搜索关键词 '{keyword}' 失败: {e}")
    
    async def ensure_page_focus(self):
        """
        确保页面获得焦点，处理页面被切换出去的情况
        """
        try:
            # 检查页面是否可见
            is_visible = await self.page.evaluate('!document.hidden')
            if not is_visible:
                self.logger.info("检测到页面失去焦点，尝试恢复...")
                
                # 尝试将页面带到前台
                await self.page.bring_to_front()
                await asyncio.sleep(0.3)              
                # 使用更安全的方式恢复焦点，避免误点击链接
                try:
                    # 方法1：直接聚焦到页面
                    await self.page.evaluate('window.focus()')
                    await asyncio.sleep(0.1)
                    
                    # 方法2：如果还是没有焦点，尝试点击一个安全的区域（页面边缘）
                    is_visible = await self.page.evaluate('!document.hidden')
                    if not is_visible:
                        # 点击页面左上角的安全区域，避免点击到链接
                        await self.page.mouse.click(10, 10)
                        await asyncio.sleep(0.1)
                except Exception as focus_error:
                    self.logger.debug(f"焦点恢复操作失败: {focus_error}")
                
                # 再次检查
                is_visible = await self.page.evaluate('!document.hidden')
                if is_visible:
                    self.logger.info("页面焦点已恢复")
                else:
                    self.logger.warning("页面仍然失去焦点，但继续执行")
                    
        except Exception as e:
            self.logger.warning(f"页面焦点检查失败: {e}，继续执行")
            
    async def dismiss_translate_popup(self):
        """
        检测并关闭页面上的翻译弹窗，确保滚动和抓取不被中断
        """
        try:
            # 检查是否存在翻译弹窗
            # 常见的翻译弹窗选择器，根据实际情况可能需要调整
            popup_selectors = [
                'div[role="dialog"][aria-modal="true"]',  # 通用对话框
                'div.translate-dialog',                  # 可能的翻译对话框类名
                'div[aria-label*="translate"]',          # 带有translate字样的对话框
                'div[data-testid="translatePrompt"]',    # Twitter特定的翻译提示
                'div.r-1upvrn0',                        # Twitter常用的弹窗类
                'div[role="button"][tabindex="0"][aria-label*="关闭"]',  # 关闭按钮
                'div[role="button"][tabindex="0"][aria-label*="Close"]'   # 英文关闭按钮
            ]
            
            for selector in popup_selectors:
                popup_elements = await self.page.query_selector_all(selector)
                if popup_elements:
                    self.logger.info(f"检测到可能的翻译弹窗: {selector}，尝试关闭")
                    
                    # 尝试方法1：点击关闭按钮
                    close_button_selectors = [
                        'div[role="button"][aria-label*="关闭"]',
                        'div[role="button"][aria-label*="Close"]',
                        'div[role="button"][aria-label*="Dismiss"]',
                        'div[role="button"][aria-label*="取消"]',
                        'div[role="button"][aria-label*="Cancel"]',
                        'button[aria-label*="关闭"]',
                        'button[aria-label*="Close"]',
                        'svg[aria-label*="关闭"]',
                        'svg[aria-label*="Close"]'
                    ]
                    
                    for close_selector in close_button_selectors:
                        try:
                            close_button = await self.page.query_selector(close_selector)
                            if close_button:
                                await close_button.click()
                                self.logger.info(f"成功点击关闭按钮: {close_selector}")
                                await asyncio.sleep(0.5)  # 等待弹窗消失
                                return True
                        except Exception as click_error:
                            self.logger.debug(f"点击关闭按钮失败: {click_error}")
                    
                    # 尝试方法2：点击弹窗外部区域
                    try:
                        # 获取弹窗位置
                        popup = popup_elements[0]
                        popup_box = await popup.bounding_box()
                        if popup_box:
                            # 点击弹窗外的区域（页面左上角）
                            await self.page.mouse.click(10, 10)
                            self.logger.info("尝试通过点击页面其他区域关闭弹窗")
                            await asyncio.sleep(0.5)  # 等待弹窗消失
                            return True
                    except Exception as outside_click_error:
                        self.logger.debug(f"点击弹窗外部区域失败: {outside_click_error}")
                    
                    # 尝试方法3：使用键盘ESC键
                    try:
                        await self.page.keyboard.press('Escape')
                        self.logger.info("尝试通过ESC键关闭弹窗")
                        await asyncio.sleep(0.5)  # 等待弹窗消失
                        return True
                    except Exception as key_error:
                        self.logger.debug(f"使用ESC键关闭弹窗失败: {key_error}")
                    
                    # 尝试方法4：使用JavaScript关闭弹窗
                    try:
                        await self.page.evaluate('''
                        document.querySelectorAll('div[role="dialog"]').forEach(dialog => {
                            dialog.style.display = 'none';
                        });
                        ''')
                        self.logger.info("尝试通过JavaScript隐藏弹窗")
                        await asyncio.sleep(0.5)  # 等待弹窗消失
                        return True
                    except Exception as js_error:
                        self.logger.debug(f"使用JavaScript隐藏弹窗失败: {js_error}")
            
            return False  # 没有发现弹窗或关闭失败
        except Exception as e:
            self.logger.warning(f"处理翻译弹窗时出错: {e}")
            return False
    
    async def scroll_and_load_tweets(self, max_tweets: int = 10):
        """
        使用优化的滚动策略加载更多推文
        
        Args:
            max_tweets: 最大加载推文数量
        """
        if self.optimization_enabled:
            self.logger.info(f"🔧 使用优化滚动策略，目标推文数: {max_tweets}")
            result = await self.scroll_and_load_tweets_optimized(max_tweets)
            self.logger.info(f"🔧 优化滚动策略完成，返回结果: {result}")
            return result
        
        try:
            # 确保页面焦点
            await self.ensure_page_focus()
            
            scroll_attempts = 0
            current_tweets = 0
            last_tweet_count = 0
            stagnant_count = 0
            
            self.logger.info(f"开始优化滚动加载推文，目标: {max_tweets} 条")
            
            while current_tweets < max_tweets:
                # 获取当前推文数量
                tweets = await self.page.query_selector_all('[data-testid="tweet"]')
                current_tweets = len(tweets)
                
                # 检查是否有新推文加载
                if current_tweets == last_tweet_count:
                    stagnant_count += 1
                else:
                    stagnant_count = 0
                last_tweet_count = current_tweets
                
                # 检查并处理可能出现的翻译弹窗
                popup_dismissed = await self.dismiss_translate_popup()
                if popup_dismissed:
                    self.logger.info("已处理翻译弹窗，继续滚动")
                    # 弹窗处理后重置停滞计数，避免因弹窗导致的误判
                    stagnant_count = max(0, stagnant_count - 1)
                
                # 使用简化的滚动策略（修复search_optimizer缺失问题）
                scroll_distance = 800
                wait_time = 1.5
                max_scrolls = 20
                
                # 如果连续多次没有新内容，启用激进模式
                if stagnant_count >= 3:
                    scroll_distance = 3000
                    wait_time = 1.0
                    self.logger.debug("检测到内容停滞，启用激进滚动模式")
                
                # 检查是否应该继续滚动
                if scroll_attempts >= max_scrolls:
                    self.logger.info(f"达到最大滚动次数 {max_scrolls}，停止滚动")
                    break
                
                if stagnant_count >= 8:
                    self.logger.info(f"内容长时间停滞 ({stagnant_count} 次)，停止滚动")
                    break
                
                # 执行滚动
                self.logger.debug(f"执行滚动，距离: {scroll_distance}px，等待时间: {wait_time}s")
                
                await self.ensure_page_focus()
                await self.page.evaluate(f'window.scrollBy(0, {scroll_distance})')
                await asyncio.sleep(wait_time)
                
                # 再次检查是否有翻译弹窗出现
                await self.dismiss_translate_popup()
                
                scroll_attempts += 1
                
                # 增强的反封控机制：更早和更频繁的页面刷新
                if stagnant_count >= 3:  # 从8降低到3，更早触发刷新
                    # 检测是否可能遇到封控
                    is_blocked = await self.detect_twitter_blocking()
                    if is_blocked or stagnant_count >= 5:
                        self.logger.info(f"检测到可能的封控或长时间无新内容(停滞次数:{stagnant_count})，执行反封控刷新")
                        await self.anti_blocking_refresh()
                        stagnant_count = 0
                        # 刷新页面后也检查是否有翻译弹窗
                        await self.dismiss_translate_popup()
            
            # 如果有人工行为模拟器且效果不佳，作为补充
            if self.behavior_simulator and current_tweets < max_tweets * 0.7:
                self.logger.info("当前效果不佳，使用人工行为模拟器作为补充")
                try:
                    # 使用人工行为模拟器前先处理可能的弹窗
                    await self.dismiss_translate_popup()
                    await self.behavior_simulator.smart_scroll_and_collect(
                        max_tweets=max_tweets - current_tweets,
                        target_selector='[data-testid="tweet"]'
                    )
                except Exception as e:
                    self.logger.warning(f"人工行为模拟器补充失败: {e}")
                    # 出错时也尝试处理可能的弹窗
                    await self.dismiss_translate_popup()
            
            # 获取最终的推文数量
            final_tweets = await self.page.query_selector_all('[data-testid="tweet"]')
            efficiency = len(final_tweets) / max(scroll_attempts, 1)
            self.logger.info(f"优化滚动完成，滚动 {scroll_attempts} 次，最终推文数量: {len(final_tweets)}，效率: {efficiency:.2f} 推文/滚动")
            
        except Exception as e:
            self.logger.error(f"优化滚动失败: {e}")
            # 出错时也尝试处理可能的弹窗
            await self.dismiss_translate_popup()
            raise
    
    def extract_number(self, text: str) -> int:
        """
        从文本中提取数字（处理K、M等单位）
        
        Args:
            text: 包含数字的文本
            
        Returns:
            提取的数字
        """
        if not text:
            return 0
        
        # 记录原始文本用于调试
        original_text = text
        
        # 移除多余的空格和特殊字符，但保留数字、单位和分隔符
        text = re.sub(r'[^\d\.KkMmBb万千百十,\s]', '', text)
        
        # 查找数字模式，按优先级排序
        patterns = [
            (r'([\d,]+(?:\.\d+)?)\s*[Bb]', 1000000000),  # 1.2B, 1,234B
            (r'([\d,]+(?:\.\d+)?)\s*[Mm]', 1000000),     # 1.2M, 1,234M
            (r'([\d,]+(?:\.\d+)?)\s*[Kk]', 1000),        # 1.2K, 1,234K
            (r'([\d,]+(?:\.\d+)?)\s*万', 10000),          # 1.2万
            (r'([\d,]+(?:\.\d+)?)\s*千', 1000),           # 1.2千
            (r'([\d,]+(?:\.\d+)?)\s*百', 100),            # 1.2百
            (r'([\d,]+(?:\.\d+)?)\s*十', 10),             # 1.2十
            (r'([\d,]+(?:\.\d+)?)', 1),                   # 普通数字
        ]
        
        for pattern, multiplier in patterns:
            match = re.search(pattern, text)
            if match:
                number_str = match.group(1).replace(',', '')
                try:
                    number = float(number_str)
                    result = int(number * multiplier)
                    
                    # 调试日志
                    if result > 0:
                        self.logger.debug(f"数字提取成功: '{original_text}' -> '{number_str}' * {multiplier} = {result}")
                    
                    return result
                except ValueError:
                    continue
        
        # 如果没有匹配到，尝试更宽松的匹配
        loose_match = re.search(r'(\d+)', text)
        if loose_match:
            try:
                result = int(loose_match.group(1))
                if result > 0:
                    self.logger.debug(f"宽松匹配数字提取: '{original_text}' -> {result}")
                return result
            except ValueError:
                pass
        
        self.logger.debug(f"数字提取失败: '{original_text}' -> 0")
        return 0
    
    async def parse_tweet_element(self, tweet_element) -> Optional[Dict[str, Any]]:
        """
        解析单个推文元素
        
        Args:
            tweet_element: 推文DOM元素
            
        Returns:
            推文数据字典
        """
        # 如果启用了优化功能，使用优化版本
        if self.optimization_enabled:
            self.logger.info(f"🔧 调用优化版本解析方法，optimization_enabled={self.optimization_enabled}")
            result = await self.parse_tweet_element_optimized(tweet_element)
            self.logger.info(f"🔧 优化版本解析结果: {result is not None}")
            return result
        
        try:
            tweet_data = {}
            
            # 检查元素是否仍然有效
            try:
                await tweet_element.is_visible()
            except Exception:
                self.logger.warning("推文元素已失效，跳过解析")
                return None
            
            # 使用更稳定的方式提取用户名
            try:
                # 尝试多种选择器
                username_selectors = [
                    '[data-testid="User-Name"] a',
                    '[data-testid="User-Names"] a',
                    'a[href^="/"][role="link"]'
                ]
                
                username_element = None
                for selector in username_selectors:
                    try:
                        username_element = await tweet_element.query_selector(selector)
                        if username_element:
                            break
                    except Exception:
                        continue
                
                if username_element:
                    username_href = await username_element.get_attribute('href')
                    if username_href and '/' in username_href:
                        tweet_data['username'] = username_href.split('/')[-1]
            except Exception as e:
                self.logger.debug(f"提取用户名失败: {e}")
            
            # 使用更稳定的方式提取推文内容
            try:
                content_selectors = [
                    '[data-testid="tweetText"]',
                    '[data-testid="tweetText"] span',
                    'div[lang] span',
                    'div[dir="auto"] span',
                    'div[dir="ltr"] span',
                    'div[dir="rtl"] span',
                    '[lang] span',
                    'span[dir="auto"]',
                    'div[data-testid="tweetText"] > span',
                    'article div[lang] span',
                    'article span[dir]'
                ]
                
                content_text = ''
                # 尝试多种方式提取内容
                for selector in content_selectors:
                    try:
                        content_elements = await tweet_element.query_selector_all(selector)
                        if content_elements:
                            # 收集所有文本内容
                            text_parts = []
                            for elem in content_elements:
                                text = await elem.inner_text()
                                if text and text.strip():
                                    text_parts.append(text.strip())
                            
                            if text_parts:
                                content_text = ' '.join(text_parts)
                                break
                    except Exception:
                        continue
                
                # 如果还是没有内容，尝试获取整个推文区域的文本
                if not content_text:
                    try:
                        # 尝试从整个推文元素中提取文本，但排除用户名、时间等
                        all_text = await tweet_element.inner_text()
                        if all_text:
                            # 简单过滤，移除明显的非内容文本
                            lines = all_text.split('\n')
                            filtered_lines = []
                            for line in lines:
                                line = line.strip()
                                # 跳过空行、用户名、时间戳等
                                if (line and 
                                    not line.startswith('@') and 
                                    not line.endswith('h') and 
                                    not line.endswith('m') and 
                                    not line.endswith('s') and
                                    not line.isdigit() and
                                    len(line) > 3):
                                    filtered_lines.append(line)
                            
                            if filtered_lines:
                                content_text = ' '.join(filtered_lines[:3])  # 取前3行作为内容
                    except Exception:
                        pass
                
                if content_text and content_text.strip():
                    tweet_data['content'] = content_text.strip()
                    
            except Exception as e:
                self.logger.debug(f"提取推文内容失败: {e}")
            
            # 使用更稳定的方式提取发布时间
            try:
                time_element = await tweet_element.query_selector('time')
                if time_element:
                    datetime_attr = await time_element.get_attribute('datetime')
                    if datetime_attr:
                        tweet_data['publish_time'] = datetime_attr
            except Exception as e:
                self.logger.debug(f"提取发布时间失败: {e}")
            
            # 使用更稳定的方式提取推文链接
            try:
                link_elements = await tweet_element.query_selector_all('a[href*="/status/"]')
                if link_elements:
                    href = await link_elements[0].get_attribute('href')
                    if href:
                        if href.startswith('/'):
                            tweet_data['link'] = f"https://x.com{href}"
                        else:
                            tweet_data['link'] = href
            except Exception as e:
                self.logger.debug(f"提取推文链接失败: {e}")
            
            # 使用更稳定的方式提取互动数据
            interaction_data = {'likes': 0, 'comments': 0, 'retweets': 0}
            
            # 点赞数 - 增强版提取
            try:
                like_selectors = [
                    '[data-testid="like"]',
                    '[aria-label*="like"]',
                    '[aria-label*="Like"]',
                    '[aria-label*="喜欢"]',
                    '[aria-label*="赞"]',
                    'div[role="group"] div:first-child button',
                    'div[role="group"] > div:nth-child(4) button',
                    '[data-testid="tweet"] div[role="group"] button:nth-child(3)',
                    'button[aria-label*="heart"]',
                    'button[aria-label*="favorite"]'
                ]
                
                for selector in like_selectors:
                    try:
                        like_element = await tweet_element.query_selector(selector)
                        if like_element:
                            # 尝试从 aria-label 获取
                            like_text = await like_element.get_attribute('aria-label') or ''
                            if like_text:
                                extracted_likes = self.extract_number(like_text)
                                if extracted_likes > 0:
                                    interaction_data['likes'] = extracted_likes
                                    self.logger.debug(f"从aria-label提取点赞数: {extracted_likes}")
                                    break
                            
                            # 尝试从内部文本获取
                            inner_text = await like_element.inner_text()
                            if inner_text and inner_text.strip():
                                extracted_likes = self.extract_number(inner_text)
                                if extracted_likes > 0:
                                    interaction_data['likes'] = extracted_likes
                                    self.logger.debug(f"从内部文本提取点赞数: {extracted_likes}")
                                    break
                    except Exception:
                        continue
            except Exception as e:
                self.logger.debug(f"提取点赞数失败: {e}")
            
            # 评论数 - 增强版提取
            try:
                reply_selectors = [
                    '[data-testid="reply"]',
                    '[aria-label*="repl"]',
                    '[aria-label*="Reply"]',
                    '[aria-label*="回复"]',
                    '[aria-label*="评论"]',
                    'div[role="group"] div:first-child button',
                    'div[role="group"] > div:nth-child(1) button',
                    '[data-testid="tweet"] div[role="group"] button:first-child',
                    'button[aria-label*="comment"]'
                ]
                
                for selector in reply_selectors:
                    try:
                        reply_element = await tweet_element.query_selector(selector)
                        if reply_element:
                            # 尝试从 aria-label 获取
                            reply_text = await reply_element.get_attribute('aria-label') or ''
                            if reply_text:
                                extracted_replies = self.extract_number(reply_text)
                                if extracted_replies > 0:
                                    interaction_data['comments'] = extracted_replies
                                    self.logger.debug(f"从aria-label提取评论数: {extracted_replies}")
                                    break
                            
                            # 尝试从内部文本获取
                            inner_text = await reply_element.inner_text()
                            if inner_text and inner_text.strip():
                                extracted_replies = self.extract_number(inner_text)
                                if extracted_replies > 0:
                                    interaction_data['comments'] = extracted_replies
                                    self.logger.debug(f"从内部文本提取评论数: {extracted_replies}")
                                    break
                    except Exception:
                        continue
            except Exception as e:
                self.logger.debug(f"提取评论数失败: {e}")
            
            # 转发数 - 增强版提取
            try:
                retweet_selectors = [
                    '[data-testid="retweet"]',
                    '[aria-label*="retweet"]',
                    '[aria-label*="Retweet"]',
                    '[aria-label*="转发"]',
                    '[aria-label*="转推"]',
                    'div[role="group"] div:nth-child(2) button',
                    'div[role="group"] > div:nth-child(2) button',
                    '[data-testid="tweet"] div[role="group"] button:nth-child(2)',
                    'button[aria-label*="repost"]'
                ]
                
                for selector in retweet_selectors:
                    try:
                        retweet_element = await tweet_element.query_selector(selector)
                        if retweet_element:
                            # 尝试从 aria-label 获取
                            retweet_text = await retweet_element.get_attribute('aria-label') or ''
                            if retweet_text:
                                extracted_retweets = self.extract_number(retweet_text)
                                if extracted_retweets > 0:
                                    interaction_data['retweets'] = extracted_retweets
                                    self.logger.debug(f"从aria-label提取转发数: {extracted_retweets}")
                                    break
                            
                            # 尝试从内部文本获取
                            inner_text = await retweet_element.inner_text()
                            if inner_text and inner_text.strip():
                                extracted_retweets = self.extract_number(inner_text)
                                if extracted_retweets > 0:
                                    interaction_data['retweets'] = extracted_retweets
                                    self.logger.debug(f"从内部文本提取转发数: {extracted_retweets}")
                                    break
                    except Exception:
                        continue
            except Exception as e:
                self.logger.debug(f"提取转发数失败: {e}")
            
            # 通用方法：尝试从推文底部的统计区域提取数据
            try:
                # 查找包含统计数据的区域
                stats_elements = await tweet_element.query_selector_all('div[role="group"] button')
                if stats_elements and len(stats_elements) >= 3:
                    for i, button in enumerate(stats_elements[:4]):  # 通常前4个按钮是回复、转发、点赞、分享
                        try:
                            aria_label = await button.get_attribute('aria-label') or ''
                            inner_text = await button.inner_text() or ''
                            
                            # 组合文本进行分析
                            combined_text = f"{aria_label} {inner_text}".lower()
                            
                            if any(keyword in combined_text for keyword in ['reply', 'repl', '回复', '评论']) and interaction_data['comments'] == 0:
                                extracted_num = self.extract_number(combined_text)
                                if extracted_num > 0:
                                    interaction_data['comments'] = extracted_num
                                    self.logger.debug(f"通用方法提取评论数: {extracted_num}")
                            
                            elif any(keyword in combined_text for keyword in ['retweet', 'repost', '转发', '转推']) and interaction_data['retweets'] == 0:
                                extracted_num = self.extract_number(combined_text)
                                if extracted_num > 0:
                                    interaction_data['retweets'] = extracted_num
                                    self.logger.debug(f"通用方法提取转发数: {extracted_num}")
                            
                            elif any(keyword in combined_text for keyword in ['like', 'heart', 'favorite', '喜欢', '赞']) and interaction_data['likes'] == 0:
                                extracted_num = self.extract_number(combined_text)
                                if extracted_num > 0:
                                    interaction_data['likes'] = extracted_num
                                    self.logger.debug(f"通用方法提取点赞数: {extracted_num}")
                        except Exception:
                            continue
            except Exception as e:
                self.logger.debug(f"通用统计数据提取失败: {e}")
            
            # 合并互动数据
            tweet_data.update(interaction_data)
            
            # 提取媒体内容（图片和视频）
            try:
                media_content = await self.extract_media_content(tweet_element)
                if media_content:
                    tweet_data['media'] = media_content
                    self.logger.debug(f"提取到媒体内容: {len(media_content.get('images', []))} 张图片, {len(media_content.get('videos', []))} 个视频")
            except Exception as e:
                self.logger.debug(f"提取媒体内容失败: {e}")
            
            # 设置默认值
            tweet_data.setdefault('username', 'unknown')
            tweet_data.setdefault('content', '')
            tweet_data.setdefault('publish_time', datetime.now().isoformat())
            tweet_data.setdefault('link', '')
            tweet_data.setdefault('likes', 0)
            tweet_data.setdefault('comments', 0)
            tweet_data.setdefault('retweets', 0)
            tweet_data.setdefault('media', {'images': [], 'videos': []})
            
            # 识别帖子类型
            try:
                tweet_data['post_type'] = self.identify_tweet_type(tweet_data)
                self.logger.debug(f"识别帖子类型: {tweet_data['post_type']}")
            except Exception as e:
                self.logger.debug(f"识别帖子类型失败: {e}")
                tweet_data['post_type'] = '文字'
            
            # 验证推文数据的有效性 - 进一步放宽验证条件
            # 只要满足以下任一条件就认为是有效推文：
            # 1. 有用户名
            # 2. 有内容
            # 3. 有链接
            # 4. 有媒体内容
            # 5. 有互动数据（点赞、评论、转发）
            has_username = tweet_data.get('username', '') and tweet_data.get('username', '') != 'unknown'
            has_content = tweet_data.get('content', '').strip()
            has_link = tweet_data.get('link', '').strip()
            has_media = (tweet_data.get('media', {}).get('images', []) or 
                        tweet_data.get('media', {}).get('videos', []))
            has_interactions = (tweet_data.get('likes', 0) > 0 or 
                              tweet_data.get('comments', 0) > 0 or 
                              tweet_data.get('retweets', 0) > 0)
            
            # 只要有任何一项有效信息就保留推文
            if not (has_username or has_content or has_link or has_media or has_interactions):
                self.logger.debug(f"推文数据无效，跳过 - 用户名: {tweet_data.get('username', 'None')}, 内容长度: {len(tweet_data.get('content', ''))}, 链接: {bool(tweet_data.get('link', ''))}, 媒体: {bool(has_media)}, 互动: {bool(has_interactions)}")
                return None
            
            self.logger.debug(f"推文验证通过 - 用户名: {tweet_data.get('username', 'None')}, 内容长度: {len(tweet_data.get('content', ''))}, 链接: {bool(tweet_data.get('link', ''))}")
            
            return tweet_data
            
        except Exception as e:
            self.logger.error(f"解析推文元素失败: {e}")
            return None
    
    async def scrape_tweets(self, max_tweets: int = 10, enable_enhanced: bool = False, filter_criteria: dict = None) -> List[Dict[str, Any]]:
        """
        抓取当前页面的推文数据
        
        Args:
            max_tweets: 最大抓取推文数量
            enable_enhanced: 是否启用增强抓取（包含详情页内容）
            filter_criteria: 筛选条件 {'min_likes': int, 'min_comments': int, 'min_retweets': int}
            
        Returns:
            推文数据列表
        """
        if enable_enhanced:
            return await self.enhanced_tweet_scraping(max_tweets, filter_criteria=filter_criteria)
        
        tweets_data = []
        max_scroll_attempts = 200  # 增加最大滚动次数以确保能抓取足够满足条件的推文
        scroll_attempts = 0
        last_tweet_count = 0
        no_new_tweets_count = 0
        consecutive_empty_scrolls = 0  # 连续空滚动计数器
        total_parsed_tweets = 0  # 总解析推文数（包括不满足条件的）
        
        try:
            self.logger.info(f"开始抓取推文，目标数量: {max_tweets}")
            
            # 初始化封控检测计数器
            blocking_detection_count = 0
            last_blocking_check = 0
            recovery_attempts = 0
            max_recovery_attempts = 3
            
            while len(tweets_data) < max_tweets and scroll_attempts < max_scroll_attempts:
                # 每隔一定次数检测封控状态
                if scroll_attempts - last_blocking_check >= 10:
                    is_blocked = await self.detect_twitter_blocking()
                    if is_blocked:
                        blocking_detection_count += 1
                        self.logger.warning(f"检测到封控状态 (第 {blocking_detection_count} 次)")
                        
                        if recovery_attempts < max_recovery_attempts:
                            # 根据检测次数选择恢复策略
                            if blocking_detection_count == 1:
                                severity = 'light'
                            elif blocking_detection_count == 2:
                                severity = 'medium'
                            else:
                                severity = 'heavy'
                            
                            self.logger.info(f"执行封控恢复策略: {severity}")
                            recovery_success = await self.anti_blocking_refresh(severity)
                            recovery_attempts += 1
                            
                            if recovery_success:
                                self.logger.info("封控恢复成功，继续抓取")
                                blocking_detection_count = 0  # 重置计数器
                                # 重新等待页面稳定
                                await asyncio.sleep(5)
                            else:
                                self.logger.warning("封控恢复失败")
                        else:
                            self.logger.error("达到最大恢复尝试次数，停止抓取")
                            break
                    
                    last_blocking_check = scroll_attempts
                
                # 等待推文加载
                try:
                    await self.page.wait_for_selector('[data-testid="tweet"]', timeout=5000)
                except Exception:
                    self.logger.warning(f"等待推文元素超时，当前滚动次数: {scroll_attempts}")
                    if scroll_attempts == 0:  # 第一次就没找到推文，可能页面有问题
                        # 检查是否是封控导致的
                        is_blocked = await self.detect_twitter_blocking()
                        if is_blocked:
                            self.logger.warning("初始页面加载失败可能由于封控，尝试恢复")
                            await self.anti_blocking_refresh('medium')
                            continue
                        break
                
                # 获取当前页面的推文元素
                tweet_elements = await self.page.query_selector_all('[data-testid="tweet"]')
                current_tweet_count = len(tweet_elements)
                
                self.logger.info(f"滚动第 {scroll_attempts + 1} 次，页面推文数: {current_tweet_count}，已抓取: {len(tweets_data)}")
                
                # 解析新的推文
                new_tweets_parsed = 0
                new_valid_tweets = 0  # 新增：满足筛选条件的推文数
                for i, tweet_element in enumerate(tweet_elements):
                    if len(tweets_data) >= max_tweets:
                        break
                    
                    # 每隔几条推文检查页面焦点
                    if i % 5 == 0:
                        await self.ensure_page_focus()
                    
                    tweet_data = await self.parse_tweet_element(tweet_element)
                    if tweet_data:
                        total_parsed_tweets += 1
                        
                        # 检查是否已经抓取过这条推文（去重）
                        tweet_link = tweet_data.get('link', '')
                        if tweet_link:
                            # 优先使用推文链接作为唯一标识
                            tweet_id = tweet_link
                        else:
                            # 如果没有链接，使用内容的哈希值作为标识（更宽松的去重）
                            content = tweet_data.get('content', '').strip()
                            if len(content) > 20:  # 只对有足够内容的推文进行去重
                                content_hash = hash(content[:100])  # 只使用前100个字符
                                tweet_id = f"content_{content_hash}"
                            else:
                                # 对于短内容，使用更详细的标识避免误判
                                detail_hash = hash(f"{tweet_data.get('username', '')}{content}{tweet_data.get('timestamp', '')}{i}")
                                tweet_id = f"detail_{detail_hash}"
                        
                        if tweet_id not in self.seen_tweet_ids:
                            self.seen_tweet_ids.add(tweet_id)
                            new_tweets_parsed += 1
                            
                            # 应用筛选条件
                            if self._meets_filter_criteria(tweet_data, filter_criteria):
                                tweets_data.append(tweet_data)
                                new_valid_tweets += 1
                                self.logger.debug(f"新抓取有效推文: @{tweet_data.get('username', 'unknown')} (点赞:{tweet_data.get('likes', 0)}, 转发:{tweet_data.get('retweets', 0)})")
                            else:
                                self.logger.debug(f"推文不满足筛选条件: @{tweet_data.get('username', 'unknown')} (点赞:{tweet_data.get('likes', 0)}, 转发:{tweet_data.get('retweets', 0)})")
                        else:
                            self.logger.debug(f"跳过重复推文: {tweet_id[:50]}...")
                
                self.logger.info(f"本次滚动新解析推文: {new_tweets_parsed}，满足条件: {new_valid_tweets}，累计有效: {len(tweets_data)}/{max_tweets}，总解析: {total_parsed_tweets}")
                
                # 检查是否有新推文
                if current_tweet_count <= last_tweet_count:
                    no_new_tweets_count += 1
                    self.logger.info(f"页面推文数量未增加，连续次数: {no_new_tweets_count}")
                else:
                    no_new_tweets_count = 0
                
                # 检查本次滚动是否解析到新的有效推文
                if new_valid_tweets == 0:
                    consecutive_empty_scrolls += 1
                    self.logger.info(f"本次滚动未获得满足条件的推文，连续空滚动次数: {consecutive_empty_scrolls}")
                    
                    # 如果连续很多次没有获得有效推文，且页面推文数量也不增加，则停止
                    if consecutive_empty_scrolls >= 20 and no_new_tweets_count >= 10:
                        self.logger.info("连续多次滚动未获得满足条件的推文且页面无新推文，可能已到页面底部或无更多满足条件的推文")
                        break
                else:
                    consecutive_empty_scrolls = 0
                
                last_tweet_count = current_tweet_count
                
                # 如果已达到目标数量，停止滚动
                if len(tweets_data) >= max_tweets:
                    self.logger.info(f"已达到目标推文数量: {len(tweets_data)}/{max_tweets}")
                    break
                
                # 智能滚动策略
                scroll_attempts += 1
                if scroll_attempts < max_scroll_attempts:
                    # 使用人类行为模拟器进行智能滚动
                    if self.behavior_simulator:
                        try:
                            # 根据连续空滚动次数调整滚动行为
                            if consecutive_empty_scrolls > 5:
                                # 多次空滚动时，模拟用户可能的行为
                                await self.behavior_simulator.simulate_page_exploration(duration=random.uniform(2, 5))
                                scroll_distance = random.randint(800, 1200)
                            elif consecutive_empty_scrolls > 3:
                                # 适度的探索性滚动
                                scroll_distance = random.randint(1200, 1800)
                            else:
                                # 正常滚动
                                scroll_distance = random.randint(1000, 1500)
                            
                            # 使用人类行为模拟器的智能滚动
                            await self.behavior_simulator.human_like_scroll(scroll_distance)
                            
                            # 智能等待时间
                            if consecutive_empty_scrolls > 8:
                                # 长时间无新内容时，增加等待时间
                                wait_time = random.uniform(4, 8)
                            elif consecutive_empty_scrolls > 5:
                                wait_time = random.uniform(3, 6)
                            else:
                                wait_time = random.uniform(2, 4)
                            
                            await asyncio.sleep(wait_time)
                            
                        except Exception as e:
                            self.logger.debug(f"智能滚动失败，使用基础滚动: {e}")
                            # 回退到基础滚动
                            scroll_distance = 1500 if consecutive_empty_scrolls > 3 else 1200
                            await self.page.evaluate(f'window.scrollBy(0, {scroll_distance})')
                            wait_time = 3 if consecutive_empty_scrolls > 5 else 2
                            await asyncio.sleep(wait_time)
                    else:
                        # 没有行为模拟器时的基础滚动
                        scroll_distance = 1500 if consecutive_empty_scrolls > 3 else 1200
                        await self.page.evaluate(f'window.scrollBy(0, {scroll_distance})')
                        wait_time = 3 if consecutive_empty_scrolls > 5 else 2
                        await asyncio.sleep(wait_time)
                    
                    # 处理可能的弹窗和干扰
                    try:
                        await self.dismiss_translate_popup()
                        
                        # 检查页面是否出现异常
                        page_title = await self.page.title()
                        if 'error' in page_title.lower() or 'blocked' in page_title.lower():
                            self.logger.warning(f"检测到页面标题异常: {page_title}")
                            await self.anti_blocking_refresh('light')
                        
                    except Exception as e:
                        self.logger.debug(f"处理页面干扰失败: {e}")
                    
                    # 每隔一定滚动次数进行页面健康检查
                    if scroll_attempts % 15 == 0:
                        try:
                            # 检查页面响应性
                            await self.page.evaluate('document.readyState')
                            
                            # 模拟用户暂停阅读
                            if self.behavior_simulator:
                                await self.behavior_simulator.simulate_reading_behavior(duration=random.uniform(1, 3))
                            
                        except Exception as e:
                            self.logger.warning(f"页面健康检查失败: {e}")
                            # 尝试轻度恢复
                            await self.anti_blocking_refresh('light')
            
            # 只返回目标数量的推文
            final_tweets = tweets_data[:max_tweets]
            filter_info = f"（筛选条件: {filter_criteria}）" if filter_criteria else "（无筛选条件）"
            self.logger.info(f"推文抓取完成{filter_info}，目标: {max_tweets}，实际获取: {len(final_tweets)}，总解析: {total_parsed_tweets}，滚动次数: {scroll_attempts}")
            
            if len(final_tweets) < max_tweets:
                shortage = max_tweets - len(final_tweets)
                self.logger.warning(f"满足条件的推文数量不足，缺少 {shortage} 条推文（总共解析了 {total_parsed_tweets} 条推文）")
            
            return final_tweets
            
        except Exception as e:
            self.logger.error(f"抓取推文失败: {e}")
            return tweets_data[:max_tweets] if tweets_data else []
    
    def _meets_filter_criteria(self, tweet_data: Dict[str, Any], filter_criteria: dict = None) -> bool:
        """
        检查推文是否满足筛选条件
        
        Args:
            tweet_data: 推文数据
            filter_criteria: 筛选条件字典
            
        Returns:
            是否满足筛选条件
        """
        if not filter_criteria:
            return True
        
        # 获取推文的互动数据
        likes = tweet_data.get('likes', 0)
        comments = tweet_data.get('comments', 0)
        retweets = tweet_data.get('retweets', 0)
        
        # 检查最小点赞数
        min_likes = filter_criteria.get('min_likes', 0)
        if likes < min_likes:
            return False
        
        # 检查最小评论数
        min_comments = filter_criteria.get('min_comments', 0)
        if comments < min_comments:
            return False
        
        # 检查最小转发数
        min_retweets = filter_criteria.get('min_retweets', 0)
        if retweets < min_retweets:
            return False
        
        return True
    
    async def scrape_user_tweets(self, username: str, max_tweets: int = 10, enable_enhanced: bool = False, filter_criteria: dict = None) -> List[Dict[str, Any]]:
        """
        抓取指定用户的推文
        
        Args:
            username: Twitter 用户名
            max_tweets: 最大抓取推文数量
            enable_enhanced: 是否启用增强抓取（包含详情页内容）
            filter_criteria: 筛选条件 {'min_likes': int, 'min_comments': int, 'min_retweets': int}
            
        Returns:
            推文数据列表
        """
        try:
            # 确保页面焦点
            await self.ensure_page_focus()
            
            await self.navigate_to_profile(username)
            
            # 使用人工行为模拟器进行页面探索
            if self.behavior_simulator:
                self.logger.info(f"开始模拟用户浏览 @{username} 的页面")
                await self.behavior_simulator.simulate_page_exploration()
                
                # 模拟阅读行为
                await self.behavior_simulator.simulate_reading_behavior()
            else:
                await asyncio.sleep(0.8)  # 极速回退等待
            
            tweets = await self.scrape_tweets(max_tweets, enable_enhanced, filter_criteria)
            
            # 模拟用户会话结束行为
            if self.behavior_simulator:
                await self.behavior_simulator.simulate_natural_browsing([f"https://twitter.com/{username}"])
            
            # 为每条推文添加来源信息
            for tweet in tweets:
                tweet['source'] = f'@{username}'
                tweet['source_type'] = 'user_profile'
            
            return tweets
            
        except Exception as e:
            self.logger.error(f"抓取用户 @{username} 的推文失败: {e}")
            return []
    
    async def scrape_keyword_tweets(self, keyword: str, max_tweets: int = 10, enable_enhanced: bool = False, filter_criteria: dict = None) -> List[Dict[str, Any]]:
        """
        抓取包含指定关键词的推文
        
        Args:
            keyword: 搜索关键词
            max_tweets: 最大抓取推文数量
            enable_enhanced: 是否启用增强抓取（包含详情页内容）
            filter_criteria: 筛选条件 {'min_likes': int, 'min_comments': int, 'min_retweets': int}
            
        Returns:
            推文数据列表
        """
        try:
            # 确保页面焦点
            await self.ensure_page_focus()
            
            await self.search_tweets(keyword)
            
            # 使用人工行为模拟器进行搜索页面探索
            if self.behavior_simulator:
                self.logger.info(f"开始模拟用户浏览关键词 '{keyword}' 的搜索结果")
                await self.behavior_simulator.simulate_page_exploration()
                
                # 模拟阅读搜索结果
                await self.behavior_simulator.simulate_reading_behavior()
            else:
                await asyncio.sleep(0.8)  # 极速回退等待
            
            tweets = await self.scrape_tweets(max_tweets, enable_enhanced, filter_criteria)
            
            # 模拟搜索会话结束行为
            if self.behavior_simulator:
                await self.behavior_simulator.simulate_natural_browsing([f"https://twitter.com/search?q={keyword}"])
            
            # 为每条推文添加来源信息
            for tweet in tweets:
                tweet['source'] = keyword
                tweet['source_type'] = 'keyword_search'
            
            return tweets
            
        except Exception as e:
            self.logger.error(f"抓取关键词 '{keyword}' 的推文失败: {e}")
            return []
    
    async def scrape_user_keyword_tweets(self, username: str, keyword: str, max_tweets: int = 10, enable_enhanced: bool = False) -> List[Dict[str, Any]]:
        """
        在指定用户下搜索包含关键词的推文
        
        Args:
            username: Twitter 用户名
            keyword: 搜索关键词
            max_tweets: 最大抓取推文数量
            enable_enhanced: 是否启用增强抓取（包含详情页内容）
            
        Returns:
            推文数据列表
        """
        try:
            # 确保页面焦点
            await self.ensure_page_focus()
            
            self.logger.info(f"开始在用户 @{username} 下搜索关键词 '{keyword}'")
            
            # 构建用户特定的搜索URL
            import urllib.parse
            encoded_keyword = urllib.parse.quote(keyword)
            encoded_username = urllib.parse.quote(username)
            # 使用 from:username 语法在特定用户下搜索
            search_query = f"from:{encoded_username} {encoded_keyword}"
            search_url = f'https://x.com/search?q={urllib.parse.quote(search_query)}&src=typed_query&f=live'
            
            self.logger.info(f"用户关键词搜索URL: {search_url}")
            
            # 导航到搜索页面
            await self.page.goto(search_url, timeout=BROWSER_CONFIG['timeout'])
            
            # 等待页面加载
            try:
                await self.page.wait_for_load_state('domcontentloaded', timeout=10000)
                self.logger.info("DOM内容加载完成")
            except Exception as load_error:
                self.logger.warning(f"DOM加载超时: {load_error}")
            
            # 确保页面焦点后再等待搜索结果
            await self.ensure_page_focus()
            
            # 等待搜索结果加载（极速模式）
            self.logger.info("等待搜索结果加载...")
            await asyncio.sleep(0.8)
            
            # 检查是否有搜索结果
            try:
                await self.page.wait_for_selector('[data-testid="tweet"]', timeout=10000)
                self.logger.info("找到推文元素")
            except Exception:
                self.logger.warning("未找到推文元素，可能没有搜索结果")
            
            # 使用人工行为模拟器进行搜索页面探索
            if self.behavior_simulator:
                self.logger.info(f"开始模拟用户浏览 @{username} 下关键词 '{keyword}' 的搜索结果")
                await self.behavior_simulator.simulate_page_exploration()
                await self.behavior_simulator.simulate_reading_behavior()
            else:
                await asyncio.sleep(0.8)  # 极速回退等待
            
            tweets = await self.scrape_tweets(max_tweets, enable_enhanced)
            
            # 为每条推文添加来源信息
            for tweet in tweets:
                tweet['source'] = f"@{username} + {keyword}"
                tweet['source_type'] = 'user_keyword_search'
                tweet['target_username'] = username
                tweet['target_keyword'] = keyword
            
            self.logger.info(f"在用户 @{username} 下搜索关键词 '{keyword}' 完成，获得 {len(tweets)} 条推文")
            return tweets
            
        except Exception as e:
            self.logger.error(f"在用户 @{username} 下搜索关键词 '{keyword}' 失败: {e}")
            return []
    
    async def scrape_tweet_details(self, tweet_url: str) -> Dict[str, Any]:
        """
        抓取推文详情页的完整内容
        
        Args:
            tweet_url: 推文详情页URL
            
        Returns:
            包含完整内容的推文数据
        """
        try:
            self.logger.info(f"开始抓取推文详情: {tweet_url}")
            
            # 导航到推文详情页
            await self.page.goto(tweet_url, timeout=BROWSER_CONFIG['navigation_timeout'])
            await self.page.wait_for_load_state('domcontentloaded', timeout=30000)
            
            # 等待内容加载（极速模式）
            await asyncio.sleep(2)
            
            # 抓取完整的推文内容
            full_content = await self.extract_full_tweet_content()
            
            # 抓取多媒体内容
            media_content = await self.extract_media_content()
            
            # 抓取推文线程
            thread_tweets = await self.extract_tweet_thread()
            
            # 抓取引用推文
            quoted_tweet = await self.extract_quoted_tweet()
            
            return {
                'full_content': full_content,
                'media': media_content,
                'thread': thread_tweets,
                'quoted_tweet': quoted_tweet,
                'has_detailed_content': True
            }
            
        except Exception as e:
            self.logger.error(f"抓取推文详情失败: {e}")
            return {'has_detailed_content': False}
    
    async def extract_full_tweet_content(self) -> str:
        """
        提取推文的完整内容文本
        
        Returns:
            完整的推文内容
        """
        try:
            # 尝试多种选择器获取完整内容
            content_selectors = [
                '[data-testid="tweetText"]',
                '[lang] span',
                'div[dir="auto"] span',
                'article div[lang] span'
            ]
            
            full_content = ""
            for selector in content_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        content_parts = []
                        for element in elements:
                            text = await element.inner_text()
                            if text and text.strip():
                                content_parts.append(text.strip())
                        
                        if content_parts:
                            full_content = ' '.join(content_parts)
                            break
                except Exception:
                    continue
            
            return full_content
            
        except Exception as e:
            self.logger.error(f"提取完整推文内容失败: {e}")
            return ""
    
    def identify_tweet_type(self, tweet_data: Dict[str, Any]) -> str:
        """
        识别推文的类型
        
        Args:
            tweet_data: 推文数据
            
        Returns:
            推文类型: '文字', '图文', '视频', '嵌套视频', '嵌套图文'
        """
        try:
            content = tweet_data.get('content', '')
            media = tweet_data.get('media', {})
            quoted_tweet = tweet_data.get('quoted_tweet')
            
            # 获取媒体数量
            image_count = len(media.get('images', []))
            video_count = len(media.get('videos', []))
            
            # 检查是否有引用推文（嵌套）
            has_quoted = quoted_tweet is not None
            
            # 判断类型
            if has_quoted:
                # 嵌套推文
                if video_count > 0:
                    return '嵌套视频'
                elif image_count > 0:
                    return '嵌套图文'
                else:
                    return '嵌套文字'
            else:
                # 普通推文
                if video_count > 0:
                    return '视频'
                elif image_count > 0:
                    return '图文'
                else:
                    return '文字'
                    
        except Exception as e:
            self.logger.error(f"识别推文类型失败: {e}")
            return '文字'  # 默认返回文字类型
    
    async def extract_media_content(self, tweet_element=None) -> Dict[str, List[Dict[str, Any]]]:
        """
        提取推文中的图片、视频等多媒体内容
        
        Args:
            tweet_element: 推文元素，如果为None则在整个页面中搜索
        
        Returns:
            包含images和videos列表的字典
        """
        media_content = {'images': [], 'videos': []}
        
        try:
            # 确定搜索范围
            search_context = tweet_element if tweet_element else self.page
            
            # 抓取图片
            image_selectors = [
                '[data-testid="tweetPhoto"] img',
                'img[src*="pbs.twimg.com"]',
                'div[data-testid="tweetPhoto"] img',
                '[data-testid="card.layoutLarge.media"] img'
            ]
            
            for selector in image_selectors:
                try:
                    images = await search_context.query_selector_all(selector)
                    for img in images:
                        src = await img.get_attribute('src')
                        alt = await img.get_attribute('alt') or ''
                        if src and ('pbs.twimg.com' in src or 'twimg.com' in src):
                            media_content['images'].append({
                                'type': 'image',
                                'url': src,
                                'description': alt,
                                'original_url': src.replace(':small', ':orig').replace(':medium', ':orig').replace(':large', ':orig')
                            })
                    if images:
                        break
                except Exception:
                    continue
            
            # 抓取视频
            video_selectors = [
                'video',
                '[data-testid="videoPlayer"] video',
                'div[data-testid="videoComponent"] video',
                '[data-testid="previewInterstitial"] video'
            ]
            
            for selector in video_selectors:
                try:
                    videos = await search_context.query_selector_all(selector)
                    for video in videos:
                        poster = await video.get_attribute('poster')
                        src = await video.get_attribute('src')
                        media_content['videos'].append({
                            'type': 'video',
                            'poster': poster,
                            'url': src,
                            'description': '视频内容'
                        })
                    if videos:
                        break
                except Exception:
                    continue
            
            # 抓取GIF（作为特殊的图片类型）
            gif_selectors = [
                'img[src*="video.twimg.com"]',
                '[data-testid="tweetPhoto"] img[src*=".gif"]'
            ]
            
            for selector in gif_selectors:
                try:
                    gifs = await search_context.query_selector_all(selector)
                    for gif in gifs:
                        src = await gif.get_attribute('src')
                        alt = await gif.get_attribute('alt') or ''
                        if src:
                            media_content['images'].append({
                                'type': 'gif',
                                'url': src,
                                'description': alt
                            })
                    if gifs:
                        break
                except Exception:
                    continue
            
            total_media = len(media_content['images']) + len(media_content['videos'])
            if total_media > 0:
                self.logger.debug(f"提取到 {len(media_content['images'])} 张图片, {len(media_content['videos'])} 个视频")
            
            return media_content
            
        except Exception as e:
            self.logger.error(f"提取多媒体内容失败: {e}")
            return {'images': [], 'videos': []}
    
    async def extract_tweet_thread(self) -> List[Dict[str, Any]]:
        """
        提取推文线程（连续的相关推文）
        
        Returns:
            推文线程列表
        """
        thread_tweets = []
        
        try:
            # 查找线程中的其他推文
            thread_selectors = [
                'article[data-testid="tweet"]',
                '[data-testid="tweet"]'
            ]
            
            for selector in thread_selectors:
                try:
                    tweet_elements = await self.page.query_selector_all(selector)
                    
                    # 如果找到多条推文，说明可能是线程
                    if len(tweet_elements) > 1:
                        for i, element in enumerate(tweet_elements[1:], 1):  # 跳过第一条（主推文）
                            thread_tweet = await self.parse_tweet_element(element)
                            if thread_tweet:
                                thread_tweet['thread_position'] = i
                                thread_tweets.append(thread_tweet)
                    
                    break
                except Exception:
                    continue
            
            self.logger.info(f"提取到 {len(thread_tweets)} 条线程推文")
            return thread_tweets
            
        except Exception as e:
            self.logger.error(f"提取推文线程失败: {e}")
            return []
    
    async def extract_quoted_tweet(self) -> Optional[Dict[str, Any]]:
        """
        提取引用的推文内容
        
        Returns:
            引用推文数据
        """
        try:
            # 查找引用推文
            quoted_selectors = [
                '[data-testid="quoteTweet"]',
                'div[role="blockquote"]',
                'blockquote'
            ]
            
            for selector in quoted_selectors:
                try:
                    quoted_element = await self.page.query_selector(selector)
                    if quoted_element:
                        quoted_tweet = await self.parse_tweet_element(quoted_element)
                        if quoted_tweet:
                            quoted_tweet['is_quoted'] = True
                            self.logger.info("提取到引用推文")
                            return quoted_tweet
                except Exception:
                    continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"提取引用推文失败: {e}")
            return None
    
    def is_content_truncated(self, content: str) -> bool:
        """
        检测内容是否被截断
        
        Args:
            content: 推文内容
            
        Returns:
            是否被截断
        """
        truncation_indicators = [
            content.endswith('...'),
            content.endswith('…'),
            len(content) > 280 and not content.endswith('.'),
            '显示更多' in content,
            'Show more' in content,
            '查看更多' in content,
            'See more' in content
        ]
        return any(truncation_indicators)
    
    def has_rich_media(self, tweet: Dict[str, Any]) -> bool:
        """
        检测是否包含丰富媒体内容
        
        Args:
            tweet: 推文数据
            
        Returns:
            是否包含媒体内容
        """
        content = tweet.get('content', '')
        media_indicators = [
            '📷' in content,
            '🎥' in content,
            '📸' in content,
            '🎬' in content,
            '图片' in content,
            '视频' in content,
            '照片' in content,
            'photo' in content.lower(),
            'video' in content.lower(),
            'image' in content.lower(),
            tweet.get('media_count', 0) > 0
        ]
        return any(media_indicators)
    
    def is_thread_content(self, content: str) -> bool:
        """
        识别推文线程
        
        Args:
            content: 推文内容
            
        Returns:
            是否为线程内容
        """
        import re
        
        thread_patterns = [
            r'\d+/\d+',  # 1/5, 2/10 等格式
            r'\d+/',     # 1/, 2/ 等格式
            r'\(\d+/\d+\)',  # (1/5) 格式
        ]
        
        thread_indicators = [
            '🧵', '📝', '👇', '⬇️',
            'Thread', 'thread', '线程',
            '接下来', '继续', 'continued',
            '下一条', 'next tweet'
        ]
        
        # 检查正则模式
        for pattern in thread_patterns:
            if re.search(pattern, content):
                return True
        
        # 检查线程指示词
        return any(indicator in content for indicator in thread_indicators)
    
    def is_high_value_content(self, tweet: Dict[str, Any]) -> bool:
        """
        判断是否为高价值内容
        
        Args:
            tweet: 推文数据
            
        Returns:
            是否为高价值内容
        """
        content = tweet.get('content', '').lower()
        
        # 计算互动分数
        engagement_score = (
            tweet.get('likes', 0) * 1 +
            tweet.get('retweets', 0) * 2 +
            tweet.get('comments', 0) * 3
        )
        
        # 高价值关键词
        value_keywords = [
            '教程', '方法', '技巧', '经验', '分享', '干货',
            'tutorial', 'guide', 'tips', 'how to', 'method',
            '攻略', '秘籍', '心得', '总结', '复盘',
            '工具', '资源', '推荐', 'tools', 'resources'
        ]
        
        value_indicators = [
            engagement_score > 50,  # 高互动
            len(tweet.get('content', '')) > 200,  # 长内容
            any(keyword in content for keyword in value_keywords),
            tweet.get('comments', 0) > 20,  # 高评论数
            tweet.get('retweets', 0) > 10   # 高转发数
        ]
        
        return any(value_indicators)
    
    def get_scraping_strategy(self, account_type: str = 'general', follower_count: int = 0) -> Dict[str, Any]:
        """
        根据账号类型获取抓取策略
        
        Args:
            account_type: 账号类型
            follower_count: 粉丝数量
            
        Returns:
            抓取策略配置
        """
        strategies = {
            '技术博主': {
                'detail_threshold': 0.4,
                'engagement_threshold': 30,
                'content_length_threshold': 150,
                'priority_keywords': ['代码', '技术', '开发', 'code', 'tech']
            },
            '营销博主': {
                'detail_threshold': 0.6,
                'engagement_threshold': 15,
                'content_length_threshold': 100,
                'priority_keywords': ['营销', '推广', '变现', 'marketing']
            },
            '投资博主': {
                'detail_threshold': 0.5,
                'engagement_threshold': 25,
                'content_length_threshold': 120,
                'priority_keywords': ['投资', '理财', '股票', 'investment']
            },
            'general': {
                'detail_threshold': 0.3,
                'engagement_threshold': 20,
                'content_length_threshold': 150,
                'priority_keywords': []
            }
        }
        
        # 根据粉丝数调整策略
        strategy = strategies.get(account_type, strategies['general']).copy()
        if follower_count > 100000:  # 大V账号
            strategy['detail_threshold'] *= 1.2
            strategy['engagement_threshold'] *= 0.8
        
        return strategy
    
    def should_scrape_details(self, tweet: Dict[str, Any], account_type: str = 'general') -> bool:
        """
        智能判断是否需要抓取推文详情
        
        Args:
            tweet: 基础推文数据
            account_type: 账号类型
            
        Returns:
            是否需要深度抓取
        """
        content = tweet.get('content', '')
        strategy = self.get_scraping_strategy(account_type)
        
        # 必须深度抓取的条件
        must_scrape = [
            self.is_content_truncated(content),  # 内容被截断
            self.is_thread_content(content),     # 线程内容
            self.has_rich_media(tweet)           # 包含多媒体
        ]
        
        if any(must_scrape):
            return True
        
        # 选择性深度抓取的条件
        optional_scrape = [
            self.is_high_value_content(tweet),   # 高价值内容
            len(content) > strategy['content_length_threshold'],  # 长内容
            tweet.get('comments', 0) > strategy['engagement_threshold'],  # 高互动
            any(keyword in content.lower() for keyword in strategy['priority_keywords'])  # 优先关键词
        ]
        
        # 根据策略阈值决定
        score = sum(optional_scrape) / len(optional_scrape) if optional_scrape else 0
        return score >= strategy['detail_threshold']
    
    async def enhanced_tweet_scraping(self, max_tweets: int = 10, enable_details: bool = True) -> List[Dict[str, Any]]:
        """
        增强的推文抓取，包含详情页内容
        
        Args:
            max_tweets: 最大抓取推文数量
            enable_details: 是否启用详情页抓取
            
        Returns:
            增强的推文数据列表
        """
        try:
            # 先抓取时间线上的基本推文
            basic_tweets = await self.scrape_tweets(max_tweets)
            
            if not enable_details:
                return basic_tweets
            
            enhanced_tweets = []
            details_scraped = 0
            max_details = min(5, max_tweets // 2)  # 限制详情页抓取数量
            
            for i, tweet in enumerate(basic_tweets):
                enhanced_tweet = tweet.copy()
                
                # 检查是否需要深度抓取
                if (details_scraped < max_details and 
                    tweet.get('link') and 
                    self.should_scrape_details(tweet, 'general')):
                    
                    self.logger.info(f"对第 {i+1} 条推文进行详情抓取")
                    
                    try:
                        # 抓取详情页内容
                        details = await self.scrape_tweet_details(tweet['link'])
                        enhanced_tweet.update(details)
                        details_scraped += 1
                        
                        # 模拟人工浏览间隔
                        if self.behavior_simulator:
                            await self.behavior_simulator.random_pause(2, 5)
                        else:
                            await asyncio.sleep(3)
                            
                    except Exception as e:
                        self.logger.warning(f"详情抓取失败: {e}")
                        enhanced_tweet['detail_error'] = str(e)
                
                enhanced_tweets.append(enhanced_tweet)
            
            self.logger.info(f"增强抓取完成，共处理 {len(enhanced_tweets)} 条推文，其中 {details_scraped} 条进行了详情抓取")
            return enhanced_tweets
            
        except Exception as e:
            self.logger.error(f"增强推文抓取失败: {e}")
            return basic_tweets if 'basic_tweets' in locals() else []
    
    def parse_tweets(self, tweet_elements: List[Any]) -> List[Dict[str, Any]]:
        """
        解析推文元素列表
        
        Args:
            tweet_elements: 推文DOM元素列表
            
        Returns:
            解析后的推文数据列表
        """
        parsed_tweets = []
        
        for element in tweet_elements:
            try:
                tweet_data = self.extract_tweet_data(element)
                if tweet_data:
                    parsed_tweets.append(tweet_data)
            except Exception as e:
                self.logger.warning(f"解析推文失败: {e}")
                continue
        
        return parsed_tweets
    
    def parse_user_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析用户个人资料数据
        
        Args:
            profile_data: 原始个人资料数据
            
        Returns:
            解析后的用户资料
        """
        try:
            parsed_profile = {
                'username': profile_data.get('username', ''),
                'display_name': profile_data.get('display_name', ''),
                'bio': profile_data.get('bio', ''),
                'followers_count': self._parse_count(profile_data.get('followers', '0')),
                'following_count': self._parse_count(profile_data.get('following', '0')),
                'tweets_count': self._parse_count(profile_data.get('tweets', '0')),
                'verified': profile_data.get('verified', False),
                'profile_image': profile_data.get('profile_image', ''),
                'banner_image': profile_data.get('banner_image', ''),
                'location': profile_data.get('location', ''),
                'website': profile_data.get('website', ''),
                'joined_date': profile_data.get('joined_date', ''),
                'parsed_at': datetime.now().isoformat()
            }
            
            return parsed_profile
            
        except Exception as e:
            self.logger.error(f"解析用户资料失败: {e}")
            return {}
    
    def extract_tweet_data(self, tweet_element: Any) -> Dict[str, Any]:
        """
        从推文元素中提取数据
        
        Args:
            tweet_element: 推文DOM元素
            
        Returns:
            提取的推文数据
        """
        try:
            # 这里应该根据实际的DOM结构来提取数据
            # 由于这是一个通用方法，返回基本结构
            tweet_data = {
                'id': '',
                'username': '',
                'display_name': '',
                'content': '',
                'timestamp': '',
                'likes': 0,
                'retweets': 0,
                'comments': 0,
                'link': '',
                'images': [],
                'videos': [],
                'extracted_at': datetime.now().isoformat()
            }
            
            # 如果tweet_element是字典类型（已解析的数据）
            if isinstance(tweet_element, dict):
                tweet_data.update(tweet_element)
            
            return tweet_data
            
        except Exception as e:
            self.logger.error(f"提取推文数据失败: {e}")
            return {}
    
    def _parse_count(self, count_str: str) -> int:
        """
        解析计数字符串（如1.2K, 5.6M等）
        
        Args:
            count_str: 计数字符串
            
        Returns:
            解析后的数字
        """
        try:
            if not count_str or count_str == '-':
                return 0
            
            count_str = count_str.strip().replace(',', '')
            
            if count_str.endswith('K'):
                return int(float(count_str[:-1]) * 1000)
            elif count_str.endswith('M'):
                return int(float(count_str[:-1]) * 1000000)
            elif count_str.endswith('B'):
                return int(float(count_str[:-1]) * 1000000000)
            else:
                return int(count_str)
                
        except (ValueError, AttributeError):
            return 0

    # ==================== 优化功能方法 ====================
    
    def clean_tweet_content(self, content: str) -> str:
        """优化的推文内容清理 - 修复过度清理问题"""
        if not content:
            return ""
        
        # 缓存检查
        if content in self.content_cache:
            return self.content_cache[content]
        
        original_content = content
        
        # 基础清理：去除多余的空白字符
        content = re.sub(r'\s+', ' ', content.strip())
        
        # 只进行必要的清理，避免过度删除内容
        # 1. 去除明显的重复用户名模式 (完全相同的连续重复)
        content = re.sub(r'\b(\w+)\s+\1\b', r'\1', content)
        
        # 2. 去除末尾的统计数据模式（但保留主要内容）
        content = re.sub(r'\s*·\s*[\d,KMB.\s]+$', '', content)
        
        # 3. 去除开头可能的用户名重复（但只删除明显重复的部分）
        content = re.sub(r'^(@?\w+)\s+\1\s+', r'\1 ', content)
        
        # 4. 清理末尾的多余符号
        content = re.sub(r'\s*[·…]+\s*$', '', content)
        
        # 保留原始内容的主体部分，只做最小必要的清理
        cleaned_content = content.strip()
        
        # 如果清理后内容太短且原内容较长，则返回原内容
        if len(cleaned_content) < len(original_content) * 0.3 and len(original_content) > 20:
            cleaned_content = original_content.strip()
        
        # 缓存结果
        self.content_cache[original_content] = cleaned_content
        
        return cleaned_content
    
    def extract_tweet_id(self, tweet_link: str) -> str:
        """从推文链接中提取ID"""
        try:
            if '/status/' in tweet_link:
                return tweet_link.split('/status/')[-1].split('?')[0]
            return ''
        except Exception:
            return ''
    
    def is_duplicate_tweet(self, tweet_link: str) -> bool:
        """检查是否为重复推文"""
        if not tweet_link:
            return False
            
        # 统一使用seen_tweet_ids进行去重
        if tweet_link in self.seen_tweet_ids:
            return True
            
        # 提取推文ID进行更精确的去重
        tweet_id = self.extract_tweet_id(tweet_link)
        if tweet_id:
            # 检查是否已经有相同ID的推文
            for seen_id in self.seen_tweet_ids:
                if tweet_id in seen_id:
                    return True
                    
        return False
    
    def parse_engagement_number(self, num_str: str) -> int:
        """解析互动数字 (如: 1.2K -> 1200)"""
        try:
            if not num_str:
                return 0
            
            num_str = num_str.replace(',', '').replace(' ', '')
            
            if num_str.endswith('K'):
                return int(float(num_str[:-1]) * 1000)
            elif num_str.endswith('M'):
                return int(float(num_str[:-1]) * 1000000)
            elif num_str.endswith('B'):
                return int(float(num_str[:-1]) * 1000000000)
            else:
                return int(num_str)
        except (ValueError, IndexError):
            return 0
    
    async def scroll_and_load_tweets_optimized(self, target_tweets: int = 15, max_attempts: int = 20) -> Dict[str, Any]:
        """优化的滚动策略"""
        self.logger.info(f"🚀 开始优化滚动策略，目标: {target_tweets} 条推文")
        
        scroll_attempt = 0
        stagnant_rounds = 0
        last_unique_count = 0
        
        # 动态调整参数
        base_scroll_distance = 800
        base_wait_time = 1.5
        
        while scroll_attempt < max_attempts:
            # 获取当前推文数量
            try:
                await self.page.wait_for_selector('[data-testid="tweet"]', timeout=5000)
                current_elements = await self.page.query_selector_all('[data-testid="tweet"]')
                current_unique_tweets = len(self.seen_tweet_ids)
            except Exception:
                current_elements = []
                current_unique_tweets = 0
            
            self.logger.debug(f"📊 滚动尝试 {scroll_attempt + 1}/{max_attempts}，当前唯一推文: {current_unique_tweets}/{target_tweets}")
            
            # 检查是否达到目标
            if current_unique_tweets >= target_tweets:
                self.logger.info(f"🎯 达到目标推文数量: {current_unique_tweets}")
                break
            
            # 检查停滞情况
            if current_unique_tweets == last_unique_count:
                stagnant_rounds += 1
            else:
                stagnant_rounds = 0
            
            last_unique_count = current_unique_tweets
            
            # 检查并处理可能出现的翻译弹窗
            popup_dismissed = await self.dismiss_translate_popup()
            if popup_dismissed:
                self.logger.info("已处理翻译弹窗，继续滚动")
                # 弹窗处理后重置停滞计数，避免因弹窗导致的误判
                stagnant_rounds = max(0, stagnant_rounds - 1)
            
            # 根据停滞情况调整策略
            if stagnant_rounds >= 3:
                # 激进模式：增加滚动距离，减少等待时间
                scroll_distance = base_scroll_distance * 2
                wait_time = base_wait_time * 0.7
                self.logger.debug(f"🔥 激进模式：滚动距离 {scroll_distance}，等待时间 {wait_time:.1f}s")
            elif stagnant_rounds >= 6:
                # 超激进模式：大幅滚动
                scroll_distance = base_scroll_distance * 3
                wait_time = base_wait_time * 0.5
                self.logger.debug(f"⚡ 超激进模式：滚动距离 {scroll_distance}，等待时间 {wait_time:.1f}s")
            else:
                # 正常模式
                scroll_distance = base_scroll_distance
                wait_time = base_wait_time
            
            # 执行滚动
            try:
                # 确保页面焦点
                await self.ensure_page_focus()
                
                # 平滑滚动
                current_scroll = await self.page.evaluate('window.pageYOffset')
                await self.page.evaluate(f'''
                    window.scrollTo({{
                        top: {current_scroll + scroll_distance},
                        behavior: 'smooth'
                    }});
                ''')
                
                # 等待滚动完成和内容加载
                await asyncio.sleep(wait_time)
                
                # 再次检查是否有翻译弹窗出现
                await self.dismiss_translate_popup()
                
                # 检查新推文并更新seen_tweet_ids
                await self.update_seen_tweets()
                
            except Exception as e:
                self.logger.warning(f"滚动失败: {e}")
                await asyncio.sleep(2)
                # 出错时也尝试处理可能的弹窗
                await self.dismiss_translate_popup()
            
            # 增强的反封控机制：更早和更智能的页面刷新
            if stagnant_rounds >= 3:  # 从8降低到3，更早触发
                # 检测是否可能遇到封控
                is_blocked = await self.detect_twitter_blocking()
                if is_blocked or stagnant_rounds >= 5:
                    self.logger.info(f"🔄 检测到可能的封控或长时间无新内容(停滞轮数:{stagnant_rounds})，执行反封控刷新")
                    try:
                        await self.anti_blocking_refresh()
                        stagnant_rounds = 0
                        # 重新收集已见过的推文ID
                        await self.rebuild_seen_tweets()
                    except Exception as e:
                        self.logger.warning(f"反封控刷新失败: {e}")
                        # 如果反封控失败，至少执行基本刷新
                        try:
                            await self.page.reload(wait_until='domcontentloaded')
                            await asyncio.sleep(3)
                            stagnant_rounds = 0
                            await self.rebuild_seen_tweets()
                        except Exception as reload_error:
                            self.logger.error(f"基本页面刷新也失败: {reload_error}")
            
            scroll_attempt += 1
        
        final_unique_tweets = len(self.seen_tweet_ids)
        self.logger.info(f"📊 滚动策略完成: {final_unique_tweets} 条唯一推文，{scroll_attempt} 次滚动")
        
        return {
            'final_tweet_count': final_unique_tweets,
            'scroll_attempts': scroll_attempt,
            'target_reached': final_unique_tweets >= target_tweets,
            'efficiency': final_unique_tweets / max(scroll_attempt, 1)
        }
    
    async def update_seen_tweets(self):
        """更新已见推文ID集合"""
        try:
            current_elements = await self.page.query_selector_all('[data-testid="tweet"]')
            
            for element in current_elements:
                try:
                    link_element = await element.query_selector('a[href*="/status/"]')
                    if link_element:
                        href = await link_element.get_attribute('href')
                        if href:
                            tweet_id = self.extract_tweet_id(href)
                            if tweet_id:
                                self.seen_tweet_ids.add(tweet_id)
                except Exception:
                    continue
        except Exception as e:
            self.logger.debug(f"更新已见推文ID失败: {e}")
    
    async def rebuild_seen_tweets(self):
        """重新构建已见推文ID集合"""
        try:
            self.seen_tweet_ids.clear()
            await self.update_seen_tweets()
            self.logger.debug(f"重建已见推文ID集合: {len(self.seen_tweet_ids)} 条")
        except Exception as e:
            self.logger.warning(f"重建已见推文ID失败: {e}")
    
    
    async def parse_tweet_element_enhanced(self, element) -> Optional[Dict[str, Any]]:
        """增强的推文元素解析 - 解决数量不足问题"""
        try:
            # 首先检查是否为有效的推文元素
            if not await self.is_valid_tweet_element(element):
                return None
            
            # 提取基础信息
            tweet_data = {
                'username': await self.extract_username_enhanced(element),
                'content': await self.extract_content_enhanced(element),
                'link': await self.extract_tweet_link_enhanced(element),
                'publish_time': await self.extract_publish_time_enhanced(element),
                'likes': 0,
                'comments': 0,
                'retweets': 0,
                'media': {'images': [], 'videos': []}
            }
            
            # 提取互动数据
            engagement = await self.extract_engagement_enhanced(element)
            tweet_data.update(engagement)
            
            # 提取媒体内容
            media = await self.extract_media_content_enhanced(element)
            tweet_data['media'] = media
            
            # 改进的去重检查
            if await self.is_duplicate_tweet_enhanced(tweet_data):
                self.logger.debug(f"推文重复，跳过: {tweet_data.get('link', 'no_link')}")
                return None
            
            # 放宽验证条件 - 只要有基本信息就保留
            if self.is_valid_tweet_data_enhanced(tweet_data):
                return tweet_data
            
            return None
            
        except Exception as e:
            self.logger.debug(f"解析推文元素失败: {e}")
            return None
    
    async def is_valid_tweet_element(self, element) -> bool:
        """检查是否为有效的推文元素"""
        try:
            # 检查是否包含推文的基本结构
            has_user_info = await element.query_selector('[data-testid="User-Name"]') is not None
            has_content_area = await element.query_selector('[data-testid="tweetText"]') is not None
            has_time = await element.query_selector('time') is not None
            has_actions = await element.query_selector('[role="group"]') is not None
            
            # 排除广告和推荐内容
            element_text = await element.text_content()
            is_ad = any(keyword in element_text.lower() for keyword in ['promoted', '推广', 'ad', '广告'])
            
            # 至少要有用户信息或内容区域，且不是广告
            return (has_user_info or has_content_area or has_time or has_actions) and not is_ad
            
        except Exception:
            return True  # 出错时保守处理，认为是有效元素
    
    async def extract_username_enhanced(self, element) -> str:
        """增强的用户名提取"""
        try:
            # 扩展选择器列表
            selectors = [
                '[data-testid="User-Name"] [dir="ltr"]',
                '[data-testid="User-Name"] span',
                '[data-testid="User-Names"] [dir="ltr"]',
                '[data-testid="User-Names"] span',
                'a[href^="/"][role="link"] span',
                '[dir="ltr"] span',
                'div[dir="ltr"] span',
                'span[dir="ltr"]'
            ]
            
            for selector in selectors:
                try:
                    elements = await element.query_selector_all(selector)
                    for elem in elements:
                        text = await elem.text_content()
                        if text and text.strip():
                            username = self.clean_username(text.strip())
                            if username and username != 'unknown':
                                return username
                except Exception:
                    continue
            
            # 从链接中提取
            try:
                link_elem = await element.query_selector('a[href^="/"][role="link"]')
                if link_elem:
                    href = await link_elem.get_attribute('href')
                    if href:
                        match = re.match(r'^/([^/]+)', href)
                        if match:
                            return match.group(1)
            except Exception:
                pass
            
            return 'unknown'
            
        except Exception:
            return 'unknown'
    
    def clean_username(self, text: str) -> str:
        """清理用户名"""
        if not text:
            return 'unknown'
        
        # 移除@符号
        text = re.sub(r'^@+', '', text)
        
        # 只保留第一个单词
        text = text.split()[0] if text.split() else text
        
        # 移除特殊字符，只保留字母数字和下划线
        text = re.sub(r'[^a-zA-Z0-9_]', '', text)
        
        # 排除明显的数字（如点赞数等）
        if re.match(r'^\d+[KMB]?$', text):
            return 'unknown'
        
        return text if text else 'unknown'
    
    async def extract_content_enhanced(self, element) -> str:
        """增强的内容提取"""
        try:
            content_parts = []
            
            # 扩展内容选择器
            selectors = [
                '[data-testid="tweetText"]',
                '[data-testid="tweetText"] span',
                '[lang] span',
                'div[dir="auto"] span',
                'div[dir="ltr"] span',
                'div[dir="rtl"] span',
                'span[dir="auto"]',
                'span[dir="ltr"]',
                'span[dir="rtl"]',
                'div[lang] span'
            ]
            
            for selector in selectors:
                try:
                    elements = await element.query_selector_all(selector)
                    for elem in elements:
                        text = await elem.text_content()
                        if text and text.strip():
                            clean_text = text.strip()
                            if clean_text not in content_parts and len(clean_text) > 2:
                                content_parts.append(clean_text)
                except Exception:
                    continue
            
            if content_parts:
                content = ' '.join(content_parts)
                return self.clean_tweet_content_enhanced(content)
            
            # 如果没有找到内容，尝试从整个元素提取
            try:
                full_text = await element.text_content()
                if full_text:
                    lines = [line.strip() for line in full_text.split('\n') if line.strip()]
                    # 过滤掉用户名、时间等信息，保留主要内容
                    content_lines = []
                    for line in lines:
                        if (len(line) > 10 and 
                            not line.startswith('@') and 
                            not re.match(r'^\d+[hms]$', line) and
                            not re.match(r'^\d+[KMB]?$', line)):
                            content_lines.append(line)
                    
                    if content_lines:
                        return ' '.join(content_lines[:3])  # 取前3行
            except Exception:
                pass
            
            return 'No content available'
            
        except Exception:
            return 'No content available'
    
    def clean_tweet_content_enhanced(self, content: str) -> str:
        """增强的内容清理"""
        if not content:
            return ""
        
        # 基础清理
        content = re.sub(r'\s+', ' ', content.strip())
        
        # 移除明显的重复模式
        content = re.sub(r'(\w+)\s+', r'', content)
        
        # 移除末尾的统计信息
        content = re.sub(r'\s*[·…]+\s*\d+[KMB]?\s*$', '', content)
        
        # 移除开头的重复用户名
        content = re.sub(r'^(@?\w+)\s+\s+', r' ', content)
        
        return content.strip()
    
    async def extract_tweet_link_enhanced(self, element) -> str:
        """增强的链接提取"""
        try:
            # 多种链接选择器
            selectors = [
                'a[href*="/status/"]',
                'a[href*="/status/"][role="link"]',
                'time[datetime] a',
                'time a'
            ]
            
            for selector in selectors:
                try:
                    link_elem = await element.query_selector(selector)
                    if link_elem:
                        href = await link_elem.get_attribute('href')
                        if href and '/status/' in href:
                            if href.startswith('/'):
                                return f'https://x.com{href}'
                            return href
                except Exception:
                    continue
            
            return ''
            
        except Exception:
            return ''
    
    async def is_duplicate_tweet_enhanced(self, tweet_data: Dict[str, Any]) -> bool:
        """增强的去重检查"""
        try:
            # 优先使用链接去重
            link = tweet_data.get('link', '')
            if link:
                tweet_id = self.extract_tweet_id(link)
                if tweet_id:
                    if not hasattr(self, 'seen_tweet_ids_enhanced'):
                        self.seen_tweet_ids_enhanced = set()
                    
                    if tweet_id in self.seen_tweet_ids_enhanced:
                        return True
                    self.seen_tweet_ids_enhanced.add(tweet_id)
                    return False
            
            # 如果没有链接，使用内容去重（更宽松的策略）
            content = tweet_data.get('content', '')
            if content and len(content) > 20:
                # 使用内容的哈希值而不是前50字符
                import hashlib
                content_hash = hashlib.md5(content.encode()).hexdigest()
                
                if not hasattr(self, 'seen_content_hashes'):
                    self.seen_content_hashes = set()
                
                if content_hash in self.seen_content_hashes:
                    return True
                self.seen_content_hashes.add(content_hash)
            
            return False
            
        except Exception:
            return False
    
    def is_valid_tweet_data_enhanced(self, tweet_data: Dict[str, Any]) -> bool:
        """增强的推文数据验证 - 更宽松的条件"""
        try:
            username = tweet_data.get('username', '')
            content = tweet_data.get('content', '')
            link = tweet_data.get('link', '')
            
            # 只要满足以下任一条件就认为有效：
            # 1. 有用户名且不是unknown
            # 2. 有内容且长度大于5
            # 3. 有有效链接
            # 4. 有媒体内容
            # 5. 有任何互动数据
            
            has_username = username and username != 'unknown'
            has_content = content and content != 'No content available' and len(content.strip()) > 5
            has_link = link and '/status/' in link
            has_media = (tweet_data.get('media', {}).get('images') or 
                        tweet_data.get('media', {}).get('videos'))
            has_engagement = (tweet_data.get('likes', 0) > 0 or 
                            tweet_data.get('comments', 0) > 0 or 
                            tweet_data.get('retweets', 0) > 0)
            
            return has_username or has_content or has_link or has_media or has_engagement
            
        except Exception:
            return False


    async def parse_tweet_element_optimized(self, element) -> Optional[Dict[str, Any]]:
        """优化的推文元素解析"""
        try:
            self.logger.info("🔧 开始解析推文元素（优化版本）")
            # 提取用户名
            username = await self.extract_clean_username(element)
            
            # 提取内容
            content = await self.extract_clean_content(element)
            
            # 提取链接
            link = await self.extract_tweet_link(element)
            
            # 检查重复
            if self.is_duplicate_tweet(link):
                self.logger.info(f"🔧 推文重复，跳过 - 链接: {link}")
                return None
            
            self.logger.info(f"🔧 推文不重复，继续解析 - 链接: {link}")
            
            # 提取时间
            publish_time = await self.extract_publish_time(element)
            
            # 提取互动数据
            engagement = await self.extract_engagement_data(element)
            
            # 提取媒体内容
            media = await self.extract_media_content(element)
            
            # 确定帖子类型
            post_type = '纯文本'
            if media['images']:
                post_type = '图文'
            elif media['videos']:
                post_type = '视频'
            
            # 构建推文数据
            tweet_data = {
                'username': username,
                'content': content,
                'publish_time': publish_time,
                'link': link,
                'likes': engagement['likes'],
                'comments': engagement['comments'],
                'retweets': engagement['retweets'],
                'media': media,
                'post_type': post_type
            }
            
            # 验证数据有效性 - 进一步放宽验证条件
            # 只要满足以下任一条件就认为是有效推文：
            # 1. 有有效用户名
            # 2. 有内容（长度大于3个字符）
            # 3. 有链接
            # 4. 有媒体内容
            # 5. 有互动数据
            has_username = username and username != 'unknown'
            has_content = content and content != 'No content available' and len(content.strip()) > 3
            has_link = link and link.strip()
            has_media = media['images'] or media['videos']
            has_engagement = engagement['likes'] > 0 or engagement['comments'] > 0 or engagement['retweets'] > 0
            
            # 详细记录验证信息
            self.logger.info(f"🔧 推文验证详情:")
            self.logger.info(f"   - 用户名: '{username}' (有效: {has_username})")
            self.logger.info(f"   - 内容: '{content[:50] if content else 'None'}...' (长度: {len(content) if content else 0}, 有效: {has_content})")
            self.logger.info(f"   - 链接: '{link}' (有效: {has_link})")
            self.logger.info(f"   - 媒体: {media} (有效: {has_media})")
            self.logger.info(f"   - 互动: {engagement} (有效: {has_engagement})")
            
            # 只要有任何一项有效信息就保留推文
            if has_username or has_content or has_link or has_media or has_engagement:
                self.logger.info(f"🔧 推文验证通过 - 至少有一项有效信息")
                return tweet_data
            
            self.logger.info(f"🔧 推文数据无效，跳过 - 所有验证项都失败")
            return None
            
        except Exception as e:
            self.logger.debug(f"解析推文元素失败: {e}")
            return None
    
    async def extract_clean_username(self, element) -> str:
        """提取干净的用户名"""
        try:
            # 尝试多种选择器
            username_selectors = [
                '[data-testid="User-Name"] [dir="ltr"]',
                '[data-testid="User-Name"] span',
                'a[href^="/"][role="link"] span',
                '[dir="ltr"] span'
            ]
            
            for selector in username_selectors:
                username_element = await element.query_selector(selector)
                if username_element:
                    username = await username_element.text_content()
                    username = username.strip()
                    self.logger.info(f"找到用户名原始文本: '{username}' (选择器: {selector})")
                    # 清理用户名
                    username = re.sub(r'^@', '', username)
                    username = re.sub(r'\s.*', '', username)  # 只保留第一个词
                    if username and not re.match(r'^\d+[KMB]?$', username):
                        self.logger.info(f"提取到有效用户名: '{username}'")
                        return username
            
            # 从链接中提取用户名
            link_element = await element.query_selector('a[href^="/"][role="link"]')
            if link_element:
                href = await link_element.get_attribute('href')
                if href:
                    self.logger.info(f"找到链接: {href}")
                    match = re.match(r'^/([^/]+)', href)
                    if match:
                        username = match.group(1)
                        self.logger.info(f"从链接提取用户名: '{username}'")
                        return username
            
            self.logger.info("未找到有效用户名，返回 'unknown'")
            return 'unknown'
            
        except Exception as e:
            self.logger.debug(f"提取用户名失败: {e}")
            return 'unknown'
    
    async def extract_clean_content(self, element) -> str:
        """提取干净的推文内容"""
        try:
            # 尝试多种内容选择器
            content_selectors = [
                '[data-testid="tweetText"]',
                '[lang] span',
                'div[dir="auto"] span'
            ]
            
            content_parts = []
            
            for selector in content_selectors:
                content_elements = await element.query_selector_all(selector)
                self.logger.info(f"选择器 '{selector}' 找到 {len(content_elements)} 个内容元素")
                for content_element in content_elements:
                    text = await content_element.text_content()
                    text = text.strip()
                    if text and text not in content_parts:
                        self.logger.info(f"找到内容片段: '{text[:50]}...'")
                        content_parts.append(text)
            
            # 合并内容
            raw_content = ' '.join(content_parts)
            self.logger.info(f"合并后的原始内容: '{raw_content[:100]}...'")
            
            # 清理内容
            clean_content = self.clean_tweet_content(raw_content)
            self.logger.info(f"清理后的内容: '{clean_content[:100]}...'")
            
            result = clean_content if clean_content else 'No content available'
            self.logger.info(f"最终返回内容: '{result[:50]}...'")
            return result
            
        except Exception as e:
            self.logger.debug(f"提取推文内容失败: {e}")
            return 'No content available'
    
    async def extract_tweet_link(self, element) -> str:
        """提取推文链接"""
        try:
            link_element = await element.query_selector('a[href*="/status/"]')
            if link_element:
                href = await link_element.get_attribute('href')
                if href:
                    if href.startswith('/'):
                        return f'https://x.com{href}'
                    else:
                        return href
            return ''
        except Exception:
            return ''
    
    async def extract_publish_time(self, element) -> str:
        """提取发布时间"""
        try:
            time_element = await element.query_selector('time')
            if time_element:
                datetime_attr = await time_element.get_attribute('datetime')
                if datetime_attr:
                    return datetime_attr
            return ''
        except Exception:
            return ''
    
    async def extract_engagement_data(self, element) -> Dict[str, int]:
        """提取互动数据"""
        engagement = {'likes': 0, 'comments': 0, 'retweets': 0}
        
        try:
            # 查找互动数据
            engagement_selectors = {
                'likes': ['[data-testid="like"]', '[aria-label*="like"]'],
                'comments': ['[data-testid="reply"]', '[aria-label*="repl"]'],
                'retweets': ['[data-testid="retweet"]', '[aria-label*="repost"]']
            }
            
            for metric, selectors in engagement_selectors.items():
                for selector in selectors:
                    metric_element = await element.query_selector(selector)
                    if metric_element:
                        # 查找数字
                        text = await metric_element.text_content()
                        numbers = re.findall(r'[\d,]+[KMB]?', text)
                        if numbers:
                            engagement[metric] = self.parse_engagement_number(numbers[0])
                            break
            
            return engagement
            
        except Exception as e:
            self.logger.debug(f"提取互动数据失败: {e}")
            return engagement
    
    async def extract_media_content(self, element) -> Dict[str, List[Dict]]:
        """提取媒体内容"""
        media = {'images': [], 'videos': []}
        
        try:
            # 提取图片
            img_elements = await element.query_selector_all('img[src*="pbs.twimg.com"]')
            for img in img_elements:
                src = await img.get_attribute('src')
                alt = await img.get_attribute('alt') or 'Image'
                if src:
                    media['images'].append({
                        'type': 'image',
                        'url': src,
                        'description': alt,
                        'original_url': src
                    })
            
            # 提取视频
            video_elements = await element.query_selector_all('video, [data-testid="videoPlayer"]')
            for video in video_elements:
                poster = await video.get_attribute('poster')
                if poster:
                    media['videos'].append({
                        'type': 'video',
                        'poster': poster,
                        'description': 'Video content'
                    })
            
            return media
            
        except Exception as e:
            self.logger.debug(f"提取媒体内容失败: {e}")
            return media
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """获取优化摘要"""
        return {
            'unique_tweets_processed': len(self.seen_tweet_ids),
            'content_cache_size': len(self.content_cache),
            'optimization_enabled': self.optimization_enabled,
            'optimizations_applied': [
                'intelligent_scroll_strategy',
                'content_deduplication',
                'enhanced_text_cleaning',
                'improved_element_extraction',
                'engagement_data_parsing',
                'media_content_detection'
            ]
        }
    
    def enable_optimizations(self):
        """启用优化功能"""
        self.optimization_enabled = True
        # 清空之前的缓存，确保每次任务都是全新开始
        self.seen_tweet_ids.clear()
        self.content_cache.clear()
        # 清空解析阶段的去重集合
        if hasattr(self, 'parsed_tweet_ids'):
            self.parsed_tweet_ids.clear()
        self.logger.info("✅ 优化功能已启用")
        self.logger.info("🔄 已清空推文ID缓存、内容缓存和解析去重集合")
    
    def disable_optimizations(self):
        """禁用优化功能"""
        self.optimization_enabled = False
        self.logger.info("❌ 优化功能已禁用")
    
    def clear_optimization_cache(self):
        """清理优化缓存"""
        self.seen_tweet_ids.clear()
        self.content_cache.clear()
        self.logger.info("🧹 优化缓存已清理")
    
    async def detect_twitter_blocking(self) -> bool:
        """增强的Twitter封控检测机制"""
        try:
            blocking_score = 0
            detected_issues = []
            
            # 1. 检测明显的封控指示器
            blocking_indicators = [
                ('text="Something went wrong"', 10, '系统错误提示'),
                ('text="出了点问题"', 10, '系统错误提示(中文)'),
                ('text="Try again"', 8, '重试提示'),
                ('text="重试"', 8, '重试提示(中文)'),
                ('text="Rate limit exceeded"', 15, '速率限制'),
                ('text="请稍后再试"', 15, '速率限制(中文)'),
                ('text="Log in"', 12, '强制登录'),
                ('text="登录"', 12, '强制登录(中文)'),
                ('[data-testid="error"]', 10, '错误状态'),
                ('[data-testid="emptyState"]', 8, '空状态页面'),
                ('text="验证"', 15, '验证要求'),
                ('text="Verify"', 15, '验证要求(英文)'),
                ('text="captcha"', 20, '验证码'),
                ('text="Challenge"', 18, '挑战验证'),
                ('text="Suspicious"', 16, '可疑活动检测'),
                ('text="Automated"', 14, '自动化检测'),
                ('text="Robot"', 14, '机器人检测'),
            ]
            
            for selector, score, description in blocking_indicators:
                try:
                    element = await self.page.query_selector(f'[{selector}]')
                    if element:
                        blocking_score += score
                        detected_issues.append(description)
                        self.logger.warning(f"检测到封控指示器: {description} (权重: {score})")
                except Exception:
                    continue
            
            # 2. 检查页面内容异常
            current_url = self.page.url
            
            # 检查URL重定向
            suspicious_urls = ['login', 'signin', 'challenge', 'verify', 'suspended', 'locked']
            for suspicious in suspicious_urls:
                if suspicious in current_url.lower():
                    blocking_score += 12
                    detected_issues.append(f'URL重定向到{suspicious}页面')
                    self.logger.warning(f"检测到可疑URL重定向: {current_url}")
            
            # 3. 检查推文元素状态
            tweet_elements = await self.page.query_selector_all('[data-testid="tweet"]')
            page_loaded = await self.page.evaluate('document.readyState === "complete"')
            
            if page_loaded:
                if len(tweet_elements) == 0:
                    # 页面已加载但无推文
                    blocking_score += 8
                    detected_issues.append('页面无推文内容')
                elif len(tweet_elements) < 3:
                    # 推文数量异常少
                    blocking_score += 4
                    detected_issues.append('推文数量异常少')
            
            # 4. 检查页面加载时间异常
            page_load_time = await self.page.evaluate('performance.timing.loadEventEnd - performance.timing.navigationStart')
            if page_load_time > 30000:  # 超过30秒
                blocking_score += 6
                detected_issues.append('页面加载时间异常')
            
            # 5. 检查JavaScript错误
            try:
                js_errors = await self.page.evaluate("""
                    () => {
                        const errors = window.jsErrors || [];
                        return errors.filter(err => 
                            err.includes('blocked') || 
                            err.includes('forbidden') || 
                            err.includes('unauthorized')
                        ).length;
                    }
                """)
                if js_errors > 0:
                    blocking_score += js_errors * 3
                    detected_issues.append(f'检测到{js_errors}个相关JS错误')
            except Exception:
                pass
            
            # 6. 检查网络请求状态
            try:
                failed_requests = await self.page.evaluate("""
                    () => {
                        const resources = performance.getEntriesByType('resource');
                        return resources.filter(r => 
                            r.name.includes('twitter.com') && 
                            (r.transferSize === 0 || r.duration > 10000)
                        ).length;
                    }
                """)
                if failed_requests > 5:
                    blocking_score += 5
                    detected_issues.append(f'{failed_requests}个网络请求异常')
            except Exception:
                pass
            
            # 判断是否被封控
            is_blocked = blocking_score >= 15
            
            if is_blocked:
                self.logger.warning(f"检测到封控 (得分: {blocking_score}/100)")
                self.logger.warning(f"检测到的问题: {', '.join(detected_issues)}")
            elif blocking_score > 8:
                self.logger.info(f"检测到轻微异常 (得分: {blocking_score}/100): {', '.join(detected_issues)}")
            
            return is_blocked
            
        except Exception as e:
            self.logger.debug(f"封控检测失败: {e}")
            return False
    
    async def anti_blocking_refresh(self, severity_level: str = 'medium') -> bool:
        """增强的反封控刷新策略"""
        try:
            self.logger.info(f"🔄 执行反封控刷新策略 (严重程度: {severity_level})")
            
            # 根据严重程度选择不同的恢复策略
            if severity_level == 'light':
                return await self._light_recovery()
            elif severity_level == 'medium':
                return await self._medium_recovery()
            elif severity_level == 'heavy':
                return await self._heavy_recovery()
            else:
                return await self._medium_recovery()
                
        except Exception as e:
            self.logger.error(f"反封控刷新失败: {e}")
            # 如果反封控策略失败，至少执行基本刷新
            await self.page.reload()
            await asyncio.sleep(2)
            return False
    
    async def _light_recovery(self) -> bool:
        """轻度恢复策略"""
        try:
            # 1. 简单的页面刷新
            await self.page.reload(wait_until='networkidle')
            
            # 2. 短暂等待
            import random
            wait_time = random.uniform(2, 5)
            await asyncio.sleep(wait_time)
            
            # 3. 模拟轻微的用户行为
            if self.behavior_simulator:
                await self.behavior_simulator.simulate_page_exploration(duration=random.uniform(3, 6))
            
            return True
            
        except Exception as e:
            self.logger.error(f"轻度恢复失败: {e}")
            return False
    
    async def _medium_recovery(self) -> bool:
        """中度恢复策略"""
        try:
            import random
            
            # 1. 随机化用户代理和指纹
            await self.randomize_user_agent()
            
            # 2. 清除追踪数据
            await self.clear_tracking_data()
            
            # 3. 模拟人类行为的页面刷新
            await self.human_like_refresh()
            
            # 4. 中等时长等待
            wait_time = random.uniform(5, 12)
            self.logger.info(f"等待 {wait_time:.1f} 秒避免检测")
            await asyncio.sleep(wait_time)
            
            # 5. 模拟自然浏览行为
            if self.behavior_simulator:
                await self.behavior_simulator.simulate_natural_browsing(pages=1, session_duration=random.uniform(10, 20))
            
            return True
            
        except Exception as e:
            self.logger.error(f"中度恢复失败: {e}")
            return False
    
    async def _heavy_recovery(self) -> bool:
        """重度恢复策略"""
        try:
            import random
            
            # 1. 完全重置浏览器环境
            await self._reset_browser_environment()
            
            # 2. 长时间等待
            wait_time = random.uniform(30, 60)
            self.logger.info(f"执行长时间等待 {wait_time:.1f} 秒")
            await asyncio.sleep(wait_time)
            
            # 3. 模拟完整的用户会话
            if self.behavior_simulator:
                await self.behavior_simulator.simulate_user_session(duration=random.uniform(60, 120))
            
            # 4. 访问其他页面建立正常浏览模式
            await self._establish_normal_browsing_pattern()
            
            return True
            
        except Exception as e:
            self.logger.error(f"重度恢复失败: {e}")
            return False
    
    async def _reset_browser_environment(self) -> bool:
        """完全重置浏览器环境"""
        try:
            import random
            
            # 1. 清除所有存储数据
            await self.page.evaluate("""
                () => {
                    // 清除所有存储
                    localStorage.clear();
                    sessionStorage.clear();
                    
                    // 清除IndexedDB
                    if (window.indexedDB) {
                        indexedDB.databases().then(databases => {
                            databases.forEach(db => {
                                indexedDB.deleteDatabase(db.name);
                            });
                        });
                    }
                    
                    // 清除缓存
                    if ('caches' in window) {
                        caches.keys().then(names => {
                            names.forEach(name => {
                                caches.delete(name);
                            });
                        });
                    }
                }
            """)
            
            # 2. 重新设置完整的浏览器指纹
            await self.randomize_user_agent()
            
            # 3. 设置新的请求头
            await self.page.set_extra_http_headers({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': random.choice(['en-US,en;q=0.9', 'zh-CN,zh;q=0.9,en;q=0.8']),
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': str(random.choice([0, 1])),
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0'
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"浏览器环境重置失败: {e}")
            return False
    
    async def _establish_normal_browsing_pattern(self) -> bool:
        """建立正常的浏览模式"""
        try:
            import random
            
            # 访问一些正常页面建立浏览历史
            normal_pages = [
                'https://twitter.com',
                'https://twitter.com/explore',
                'https://twitter.com/notifications'
            ]
            
            for page_url in random.sample(normal_pages, min(2, len(normal_pages))):
                try:
                    await self.page.goto(page_url, wait_until='networkidle')
                    
                    # 模拟正常浏览
                    if self.behavior_simulator:
                        await self.behavior_simulator.simulate_page_exploration(duration=random.uniform(5, 15))
                    
                    # 随机等待
                    await asyncio.sleep(random.uniform(3, 8))
                    
                except Exception as e:
                    self.logger.debug(f"访问页面 {page_url} 失败: {e}")
                    continue
            
            return True
            
        except Exception as e:
            self.logger.error(f"建立正常浏览模式失败: {e}")
            return False
    
    async def randomize_user_agent(self):
        """增强的用户代理随机化和浏览器指纹伪装"""
        try:
            # 更丰富的用户代理池
            user_agents = [
                # Chrome on macOS
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                # Chrome on Windows
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                # Firefox
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
                # Safari
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
                # Edge
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
            ]
            
            import random
            selected_ua = random.choice(user_agents)
            
            # 设置完整的请求头，模拟真实浏览器
            headers = {
                'User-Agent': selected_ua,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': random.choice([
                    'en-US,en;q=0.9',
                    'zh-CN,zh;q=0.9,en;q=0.8',
                    'ja-JP,ja;q=0.9,en;q=0.8'
                ]),
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0'
            }
            
            await self.page.set_extra_http_headers(headers)
            
            # 设置浏览器指纹伪装
            await self._set_browser_fingerprint(selected_ua)
            
            self.logger.debug(f"已更新用户代理和浏览器指纹: {selected_ua[:50]}...")
            
        except Exception as e:
            self.logger.debug(f"用户代理随机化失败: {e}")
    
    async def _set_browser_fingerprint(self, user_agent: str):
        """设置浏览器指纹伪装"""
        try:
            # 根据用户代理确定操作系统和浏览器类型
            is_mac = 'Macintosh' in user_agent
            is_windows = 'Windows' in user_agent
            is_chrome = 'Chrome' in user_agent
            is_firefox = 'Firefox' in user_agent
            is_safari = 'Safari' in user_agent and 'Chrome' not in user_agent
            
            # 设置屏幕分辨率
            screen_resolutions = {
                'mac': [(1920, 1080), (2560, 1440), (1440, 900), (1680, 1050)],
                'windows': [(1920, 1080), (1366, 768), (1536, 864), (1280, 720)],
                'default': [(1920, 1080), (1366, 768), (1440, 900)]
            }
            
            if is_mac:
                resolution = random.choice(screen_resolutions['mac'])
            elif is_windows:
                resolution = random.choice(screen_resolutions['windows'])
            else:
                resolution = random.choice(screen_resolutions['default'])
            
            # 设置时区
            timezones = [
                'Asia/Shanghai', 'America/New_York', 'Europe/London',
                'Asia/Tokyo', 'America/Los_Angeles', 'Europe/Berlin'
            ]
            timezone = random.choice(timezones)
            
            # 执行浏览器指纹伪装脚本
            fingerprint_script = f"""
            // 重写屏幕属性
            Object.defineProperty(screen, 'width', {{
                get: () => {resolution[0]}
            }});
            Object.defineProperty(screen, 'height', {{
                get: () => {resolution[1]}
            }});
            Object.defineProperty(screen, 'availWidth', {{
                get: () => {resolution[0]}
            }});
            Object.defineProperty(screen, 'availHeight', {{
                get: () => {resolution[1] - 40}
            }});
            
            // 重写时区
            Date.prototype.getTimezoneOffset = function() {{
                return {random.randint(-720, 720)};
            }};
            
            // 重写语言属性
            Object.defineProperty(navigator, 'language', {{
                get: () => '{random.choice(['en-US', 'zh-CN', 'ja-JP'])}'
            }});
            
            // 重写平台属性
            Object.defineProperty(navigator, 'platform', {{
                get: () => '{'MacIntel' if is_mac else 'Win32' if is_windows else 'Linux x86_64'}'
            }});
            
            // 重写硬件并发数
            Object.defineProperty(navigator, 'hardwareConcurrency', {{
                get: () => {random.choice([4, 8, 12, 16])}
            }});
            
            // 重写内存信息
            if (navigator.deviceMemory) {{
                Object.defineProperty(navigator, 'deviceMemory', {{
                    get: () => {random.choice([4, 8, 16])}
                }});
            }}
            
            // 隐藏自动化特征
            Object.defineProperty(navigator, 'webdriver', {{
                get: () => undefined
            }});
            
            // 重写插件信息
            Object.defineProperty(navigator, 'plugins', {{
                get: () => {{
                    const plugins = [];
                    plugins.length = {random.randint(3, 8)};
                    return plugins;
                }}
            }});
            """
            
            await self.page.evaluate(fingerprint_script)
            
        except Exception as e:
            self.logger.debug(f"浏览器指纹设置失败: {e}")
    
    async def clear_tracking_data(self):
        """清除可能的追踪数据"""
        try:
            # 清除localStorage
            await self.page.evaluate('localStorage.clear()')
            
            # 清除sessionStorage
            await self.page.evaluate('sessionStorage.clear()')
            
            self.logger.debug("已清除本地存储数据")
            
        except Exception as e:
            self.logger.debug(f"清除追踪数据失败: {e}")
    
    async def human_like_refresh(self):
        """模拟人类行为的页面刷新"""
        try:
            # 模拟按F5刷新
            await self.page.keyboard.press('F5')
            await asyncio.sleep(1)
            
            # 等待页面加载
            try:
                await self.page.wait_for_load_state('domcontentloaded', timeout=10000)
            except Exception:
                self.logger.debug("等待页面加载超时，继续执行")
            
            # 确保页面焦点
            await self.ensure_page_focus()
            
            self.logger.debug("完成人类行为模拟刷新")
            
        except Exception as e:
            self.logger.debug(f"人类行为刷新失败，使用普通刷新: {e}")
            await self.page.reload()
            await asyncio.sleep(2)

    async def close(self):
        """
        关闭浏览器连接
        """
        try:
            if self.browser:
                await self.browser.close()
                self.logger.info("浏览器连接已关闭")
        except Exception as e:
            self.logger.error(f"关闭浏览器连接失败: {e}")

# 使用示例
if __name__ == "__main__":
    async def main():
        # 配置日志
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        
        # 这里需要替换为实际的调试端口
        debug_port = "ws://127.0.0.1:9222"
        
        parser = TwitterParser(debug_port)
        
        try:
            await parser.connect_browser()
            await parser.navigate_to_twitter()
            
            # 抓取指定用户的推文
            tweets = await parser.scrape_user_tweets('elonmusk', 5)
            
            # 推文抓取完成
            pass
                
        except Exception as e:
            pass
        finally:
            await parser.close()
    
    asyncio.run(main())
    def detect_tweet_quality(self, tweet_data: Dict[str, Any]) -> Dict[str, Any]:
        """检测推文质量并添加质量标记"""
        try:
            quality_score = 0
            quality_issues = []
            
            # 检查用户名
            username = tweet_data.get('username', '')
            if username and username != 'unknown':
                quality_score += 20
            else:
                quality_issues.append('缺少用户名')
            
            # 检查内容
            content = tweet_data.get('content', '')
            if content and content != 'No content available':
                if len(content) > 10:
                    quality_score += 30
                elif len(content) > 5:
                    quality_score += 15
                    quality_issues.append('内容过短')
                else:
                    quality_issues.append('内容太短')
            else:
                quality_issues.append('缺少内容')
            
            # 检查链接
            link = tweet_data.get('link', '')
            if link and '/status/' in link:
                quality_score += 25
            else:
                quality_issues.append('缺少有效链接')
            
            # 检查时间
            if tweet_data.get('publish_time'):
                quality_score += 10
            else:
                quality_issues.append('缺少发布时间')
            
            # 检查互动数据
            has_engagement = (tweet_data.get('likes', 0) > 0 or 
                            tweet_data.get('comments', 0) > 0 or 
                            tweet_data.get('retweets', 0) > 0)
            if has_engagement:
                quality_score += 15
            else:
                quality_issues.append('缺少互动数据')
            
            # 添加质量信息
            tweet_data['quality_score'] = quality_score
            tweet_data['quality_issues'] = quality_issues
            tweet_data['quality_level'] = (
                'high' if quality_score >= 80 else
                'medium' if quality_score >= 50 else
                'low'
            )
            
            return tweet_data
            
        except Exception as e:
            self.logger.debug(f"质量检测失败: {e}")
            tweet_data['quality_score'] = 0
            tweet_data['quality_issues'] = ['质量检测失败']
            tweet_data['quality_level'] = 'unknown'
            return tweet_data

