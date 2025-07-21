# -*- coding: utf-8 -*-
"""
Twitter 解析器
使用 Playwright 控制浏览器并抓取推文数据
"""

import asyncio
import logging
import re
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from playwright.async_api import async_playwright, Browser, Page
# 配置将从调用方传入或使用默认配置
from human_behavior_simulator import HumanBehaviorSimulator
from performance_optimizer import EnhancedSearchOptimizer

class TwitterParser:
    def __init__(self, debug_port: str = None):
        self.debug_port = debug_port
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.behavior_simulator = None
        self.search_optimizer = EnhancedSearchOptimizer()
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
                    await asyncio.sleep(1)
                    self.logger.info(f"执行第 {i+1} 次下拉")
                
                # 滚动回顶部
                await self.page.evaluate('window.scrollTo(0, 0)')
                await asyncio.sleep(1)
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
                
                # 验证页面是否正确加载
                current_url = self.page.url
                if username.lower() in current_url.lower():
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
                await asyncio.sleep(1)  # 极短等待时间
                
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
                
                # 使用优化的滚动策略
                strategy = self.search_optimizer.optimize_scroll_strategy(
                    current_tweets, max_tweets, scroll_attempts
                )
                
                if not strategy['should_continue']:
                    self.logger.info(f"滚动策略建议停止，当前推文数: {current_tweets}")
                    break
                
                # 如果连续多次没有新内容，启用激进模式
                if stagnant_count >= 3:
                    strategy['scroll_distance'] = 3000
                    strategy['wait_time'] = 1.0
                    strategy['aggressive_mode'] = True
                    self.logger.debug("检测到内容停滞，启用激进滚动模式")
                
                # 执行滚动
                if strategy['aggressive_mode']:
                    self.logger.debug(f"激进滚动模式，距离: {strategy['scroll_distance']}")
                
                await self.ensure_page_focus()
                await self.page.evaluate(f'window.scrollBy(0, {strategy["scroll_distance"]})')
                await asyncio.sleep(strategy['wait_time'])
                
                scroll_attempts += 1
                
                # 防止无限滚动
                if scroll_attempts >= strategy['max_scrolls']:
                    self.logger.warning(f"达到最大滚动次数 {strategy['max_scrolls']}，停止滚动")
                    break
                
                # 如果长时间没有新内容，尝试刷新页面
                if stagnant_count >= 8:
                    self.logger.info("长时间无新内容，尝试页面刷新")
                    await self.page.reload()
                    await asyncio.sleep(2)
                    stagnant_count = 0
            
            # 如果有人工行为模拟器且效果不佳，作为补充
            if self.behavior_simulator and current_tweets < max_tweets * 0.7:
                self.logger.info("当前效果不佳，使用人工行为模拟器作为补充")
                try:
                    await self.behavior_simulator.smart_scroll_and_collect(
                        max_tweets=max_tweets - current_tweets,
                        target_selector='[data-testid="tweet"]'
                    )
                except Exception as e:
                    self.logger.warning(f"人工行为模拟器补充失败: {e}")
            
            # 获取最终的推文数量
            final_tweets = await self.page.query_selector_all('[data-testid="tweet"]')
            efficiency = len(final_tweets) / max(scroll_attempts, 1)
            self.logger.info(f"优化滚动完成，滚动 {scroll_attempts} 次，最终推文数量: {len(final_tweets)}，效率: {efficiency:.2f} 推文/滚动")
            
        except Exception as e:
            self.logger.error(f"优化滚动失败: {e}")
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
        
        # 移除逗号和空格
        text = text.replace(',', '').replace(' ', '').lower()
        
        # 提取数字和单位
        match = re.search(r'([0-9.]+)([km]?)', text)
        if not match:
            return 0
        
        number = float(match.group(1))
        unit = match.group(2)
        
        if unit == 'k':
            return int(number * 1000)
        elif unit == 'm':
            return int(number * 1000000)
        else:
            return int(number)
    
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
            
            # 点赞数
            try:
                like_selectors = [
                    '[data-testid="like"]',
                    '[aria-label*="like"]',
                    '[aria-label*="Like"]'
                ]
                
                for selector in like_selectors:
                    try:
                        like_element = await tweet_element.query_selector(selector)
                        if like_element:
                            like_text = await like_element.get_attribute('aria-label') or ''
                            if like_text:
                                interaction_data['likes'] = self.extract_number(like_text)
                                break
                    except Exception:
                        continue
            except Exception as e:
                self.logger.debug(f"提取点赞数失败: {e}")
            
            # 评论数
            try:
                reply_selectors = [
                    '[data-testid="reply"]',
                    '[aria-label*="repl"]',
                    '[aria-label*="Reply"]'
                ]
                
                for selector in reply_selectors:
                    try:
                        reply_element = await tweet_element.query_selector(selector)
                        if reply_element:
                            reply_text = await reply_element.get_attribute('aria-label') or ''
                            if reply_text:
                                interaction_data['comments'] = self.extract_number(reply_text)
                                break
                    except Exception:
                        continue
            except Exception as e:
                self.logger.debug(f"提取评论数失败: {e}")
            
            # 转发数
            try:
                retweet_selectors = [
                    '[data-testid="retweet"]',
                    '[aria-label*="retweet"]',
                    '[aria-label*="Retweet"]'
                ]
                
                for selector in retweet_selectors:
                    try:
                        retweet_element = await tweet_element.query_selector(selector)
                        if retweet_element:
                            retweet_text = await retweet_element.get_attribute('aria-label') or ''
                            if retweet_text:
                                interaction_data['retweets'] = self.extract_number(retweet_text)
                                break
                    except Exception:
                        continue
            except Exception as e:
                self.logger.debug(f"提取转发数失败: {e}")
            
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
    
    async def scrape_tweets(self, max_tweets: int = 10, enable_enhanced: bool = False) -> List[Dict[str, Any]]:
        """
        抓取当前页面的推文数据
        
        Args:
            max_tweets: 最大抓取推文数量
            enable_enhanced: 是否启用增强抓取（包含详情页内容）
            
        Returns:
            推文数据列表
        """
        if enable_enhanced:
            return await self.enhanced_tweet_scraping(max_tweets)
            
        try:
            # 确保页面焦点
            await self.ensure_page_focus()
            
            # 滚动页面加载更多推文
            await self.scroll_and_load_tweets(max_tweets)
            
            # 获取所有推文元素
            tweet_elements = await self.page.query_selector_all('[data-testid="tweet"]')
            self.logger.info(f"找到 {len(tweet_elements)} 个推文元素")
            
            tweets_data = []
            
            for i, tweet_element in enumerate(tweet_elements[:max_tweets]):
                # 每隔几条推文检查页面焦点
                if i % 5 == 0:
                    await self.ensure_page_focus()
                
                # 模拟人工查看推文的行为
                if self.behavior_simulator and i % 3 == 0:  # 每3条推文模拟一次交互
                    await self.behavior_simulator.simulate_tweet_interaction(tweet_element)
                
                self.logger.debug(f"开始解析第 {i+1} 个推文元素")
                tweet_data = await self.parse_tweet_element(tweet_element)
                if tweet_data:
                    tweets_data.append(tweet_data)
                    self.logger.info(f"成功解析第 {i+1} 条推文: @{tweet_data['username']}")
                else:
                    self.logger.debug(f"第 {i+1} 个推文元素解析失败或返回None")
                
                # 模拟人工阅读间隔（极速模式）
                if self.behavior_simulator:
                    await asyncio.sleep(0.05)  # 极短等待时间
            
            self.logger.info(f"总共抓取到 {len(tweets_data)} 条推文")
            return tweets_data
            
        except Exception as e:
            self.logger.error(f"抓取推文失败: {e}")
            return []
    
    async def scrape_user_tweets(self, username: str, max_tweets: int = 10, enable_enhanced: bool = False) -> List[Dict[str, Any]]:
        """
        抓取指定用户的推文
        
        Args:
            username: Twitter 用户名
            max_tweets: 最大抓取推文数量
            enable_enhanced: 是否启用增强抓取（包含详情页内容）
            
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
            
            tweets = await self.scrape_tweets(max_tweets, enable_enhanced)
            
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
    
    async def scrape_keyword_tweets(self, keyword: str, max_tweets: int = 10, enable_enhanced: bool = False) -> List[Dict[str, Any]]:
        """
        抓取包含指定关键词的推文
        
        Args:
            keyword: 搜索关键词
            max_tweets: 最大抓取推文数量
            enable_enhanced: 是否启用增强抓取（包含详情页内容）
            
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
            
            tweets = await self.scrape_tweets(max_tweets, enable_enhanced)
            
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
            await asyncio.sleep(1)
            
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
        """优化的推文内容清理"""
        if not content:
            return ""
        
        # 缓存检查
        if content in self.content_cache:
            return self.content_cache[content]
        
        original_content = content
        
        # 去除多余的空白字符
        content = re.sub(r'\s+', ' ', content.strip())
        
        # 去除重复的用户名模式 (如: "Elon Musk Elon Musk @elonmusk")
        content = re.sub(r'(\w+\s+\w+)\s+\1', r'\1', content)
        
        # 去除重复的数字模式 (如: "4,8K 4,8K 4,8K")
        content = re.sub(r'(\d+[,.]?\d*[KMB]?)\s+\1(\s+\1)*', r'\1', content)
        
        # 去除重复的符号模式
        content = re.sub(r'(·\s*)+', '· ', content)
        
        # 去除末尾的统计数据模式
        content = re.sub(r'\s*·\s*[\d,KMB.\s]+$', '', content)
        
        # 去除开头的用户名重复
        content = re.sub(r'^(@?\w+\s+){2,}', '', content)
        
        # 去除多余的点和空格
        content = re.sub(r'\s*·\s*$', '', content)
        
        # 去除连续的重复词汇
        words = content.split()
        cleaned_words = []
        for i, word in enumerate(words):
            if i == 0 or word != words[i-1]:
                cleaned_words.append(word)
        
        cleaned_content = ' '.join(cleaned_words).strip()
        
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
        tweet_id = self.extract_tweet_id(tweet_link)
        if tweet_id:
            if tweet_id in self.seen_tweet_ids:
                return True
            self.seen_tweet_ids.add(tweet_id)
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
                await self.page.evaluate('window.focus()')
                
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
                
                # 检查新推文并更新seen_tweet_ids
                await self.update_seen_tweets()
                
            except Exception as e:
                self.logger.warning(f"滚动失败: {e}")
                await asyncio.sleep(1)
            
            # 如果连续多轮无新内容，考虑刷新
            if stagnant_rounds >= 8:
                self.logger.info("🔄 长时间无新内容，尝试刷新页面")
                try:
                    await self.page.reload(wait_until='domcontentloaded')
                    await asyncio.sleep(3)
                    stagnant_rounds = 0
                    # 重新收集已见过的推文ID
                    await self.rebuild_seen_tweets()
                except Exception as e:
                    self.logger.warning(f"页面刷新失败: {e}")
            
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
                return None
            
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
            
            # 验证数据有效性 - 放宽验证条件
            # 只要满足以下任一条件就认为是有效推文：
            # 1. 有有效用户名
            # 2. 有内容（即使是默认内容）
            # 3. 有链接
            # 4. 有媒体内容
            # 5. 有互动数据
            has_username = username and username != 'unknown'
            has_content = content and content != 'No content available'
            has_link = link and link.strip()
            has_media = media['images'] or media['videos']
            has_engagement = engagement['likes'] > 0 or engagement['comments'] > 0 or engagement['retweets'] > 0
            
            # 详细记录验证信息
            self.logger.info(f"🔧 推文验证详情:")
            self.logger.info(f"   - 用户名: '{username}' (有效: {has_username})")
            self.logger.info(f"   - 内容: '{content[:50] if content else 'None'}...' (有效: {has_content})")
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
                    self.logger.debug(f"找到用户名原始文本: '{username}' (选择器: {selector})")
                    # 清理用户名
                    username = re.sub(r'^@', '', username)
                    username = re.sub(r'\s.*', '', username)  # 只保留第一个词
                    if username and not re.match(r'^\d+[KMB]?$', username):
                        self.logger.debug(f"提取到有效用户名: '{username}'")
                        return username
            
            # 从链接中提取用户名
            link_element = await element.query_selector('a[href^="/"][role="link"]')
            if link_element:
                href = await link_element.get_attribute('href')
                if href:
                    self.logger.debug(f"找到链接: {href}")
                    match = re.match(r'^/([^/]+)', href)
                    if match:
                        username = match.group(1)
                        self.logger.debug(f"从链接提取用户名: '{username}'")
                        return username
            
            self.logger.debug("未找到有效用户名，返回 'unknown'")
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
                self.logger.debug(f"选择器 '{selector}' 找到 {len(content_elements)} 个内容元素")
                for content_element in content_elements:
                    text = await content_element.text_content()
                    text = text.strip()
                    if text and text not in content_parts:
                        self.logger.debug(f"找到内容片段: '{text[:50]}...'")
                        content_parts.append(text)
            
            # 合并内容
            raw_content = ' '.join(content_parts)
            self.logger.debug(f"合并后的原始内容: '{raw_content[:100]}...'")
            
            # 清理内容
            clean_content = self.clean_tweet_content(raw_content)
            self.logger.debug(f"清理后的内容: '{clean_content[:100]}...'")
            
            result = clean_content if clean_content else 'No content available'
            self.logger.debug(f"最终返回内容: '{result[:50]}...'")
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
        self.logger.info("✅ 优化功能已启用")
    
    def disable_optimizations(self):
        """禁用优化功能"""
        self.optimization_enabled = False
        self.logger.info("❌ 优化功能已禁用")
    
    def clear_optimization_cache(self):
        """清理优化缓存"""
        self.seen_tweet_ids.clear()
        self.content_cache.clear()
        self.logger.info("🧹 优化缓存已清理")

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