# -*- coding: utf-8 -*-
"""
Twitter 解析器
使用 Playwright 控制浏览器并抓取推文数据
"""

import asyncio
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from playwright.async_api import async_playwright, Browser, Page
from config import BROWSER_CONFIG, TWITTER_TARGETS, FILTER_CONFIG
from human_behavior_simulator import HumanBehaviorSimulator

class TwitterParser:
    def __init__(self, debug_port: str):
        self.debug_port = debug_port
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.behavior_simulator = None
        self.logger = logging.getLogger(__name__)
        
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
            self.page.set_default_timeout(BROWSER_CONFIG['timeout'])
            self.logger.info(f"设置页面超时时间: {BROWSER_CONFIG['timeout']}ms")
            
            # 设置页面导航超时时间
            self.page.set_default_navigation_timeout(BROWSER_CONFIG['navigation_timeout'])
            self.logger.info(f"设置导航超时时间: {BROWSER_CONFIG['navigation_timeout']}ms")
            
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
                current_url = self.page.url
                self.logger.info(f"当前页面URL: {current_url}")
                
                # 检查是否已经在 x.com
                if 'x.com' not in current_url:
                    self.logger.info(f"页面不在 x.com，开始导航... (第{attempt + 1}次尝试)")
                    
                    # 使用更长的超时时间
                    await self.page.goto('https://x.com', timeout=BROWSER_CONFIG['navigation_timeout'])
                    
                    # 分步等待加载
                    try:
                        await self.page.wait_for_load_state('domcontentloaded', timeout=30000)
                        await self.page.wait_for_load_state('networkidle', timeout=BROWSER_CONFIG['load_state_timeout'])
                    except Exception as load_error:
                        self.logger.warning(f"等待加载状态失败: {load_error}，继续尝试")
                    
                    self.logger.info("成功导航到 X (Twitter)")
                else:
                    self.logger.info("页面已经在 X (Twitter)，跳过导航")
                
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
                self.logger.info(f"尝试导航到 @{username} 的个人资料页面 (第{attempt + 1}次)")
                
                # 使用更长的超时时间进行导航
                await self.page.goto(profile_url, timeout=BROWSER_CONFIG['navigation_timeout'])
                
                # 分步等待加载状态
                try:
                    await self.page.wait_for_load_state('domcontentloaded', timeout=30000)
                    self.logger.info("DOM内容加载完成")
                    
                    await self.page.wait_for_load_state('networkidle', timeout=BROWSER_CONFIG['load_state_timeout'])
                    self.logger.info("网络空闲状态达到")
                except Exception as load_error:
                    self.logger.warning(f"等待加载状态失败: {load_error}，继续尝试")
                
                # 额外等待时间确保页面完全加载
                await asyncio.sleep(BROWSER_CONFIG['wait_time'])
                
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
                    # 等待后重试
                    wait_time = (attempt + 1) * 5  # 递增等待时间
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
                self.logger.info(f"开始搜索关键词 '{keyword}' (第{attempt + 1}次尝试)")
                
                # 构建搜索URL，使用URL编码
                import urllib.parse
                encoded_keyword = urllib.parse.quote(keyword)
                search_url = f'https://x.com/search?q={encoded_keyword}&src=typed_query&f=live'
                self.logger.info(f"搜索URL: {search_url}")
                
                # 导航到搜索页面
                self.logger.info("正在导航到搜索页面...")
                await self.page.goto(search_url, timeout=BROWSER_CONFIG['timeout'])
                self.logger.info("导航完成，等待页面加载...")
                
                # 简化等待策略
                try:
                    await self.page.wait_for_load_state('domcontentloaded', timeout=10000)
                    self.logger.info("DOM内容加载完成")
                except Exception as load_error:
                    self.logger.warning(f"DOM加载超时: {load_error}")
                
                # 等待搜索结果加载
                self.logger.info("等待搜索结果加载...")
                await asyncio.sleep(5)  # 使用固定等待时间
                
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
                    wait_time = (attempt + 1) * 3
                    self.logger.info(f"等待{wait_time}秒后重试...")
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error(f"搜索关键词 '{keyword}' 失败，已尝试{max_retries + 1}次")
                    raise Exception(f"搜索关键词 '{keyword}' 失败: {e}")
    
    async def scroll_and_load_tweets(self, max_tweets: int = 10):
        """
        使用人工行为模拟器滚动页面并加载更多推文
        
        Args:
            max_tweets: 最大加载推文数量
        """
        try:
            if not self.behavior_simulator:
                self.logger.warning("人工行为模拟器未初始化，使用基础滚动")
                # 回退到基础滚动
                for i in range(max_tweets // 5 + 1):
                    await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    await asyncio.sleep(BROWSER_CONFIG['scroll_pause_time'])
                    tweets = await self.page.query_selector_all('[data-testid="tweet"]')
                    if len(tweets) >= max_tweets:
                        break
                return
            
            self.logger.info(f"开始使用人工行为模拟器加载推文，目标: {max_tweets} 条")
            
            # 使用人工行为模拟器进行智能滚动
            collected_data = await self.behavior_simulator.smart_scroll_and_collect(
                max_tweets=max_tweets,
                target_selector='[data-testid="tweet"]'
            )
            
            # 获取最终的推文数量
            final_tweets = await self.page.query_selector_all('[data-testid="tweet"]')
            self.logger.info(f"人工行为模拟完成，当前可见推文数量: {len(final_tweets)}")
            
        except Exception as e:
            self.logger.error(f"人工行为滚动失败: {e}")
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
                    '[lang] span',
                    'div[dir="auto"] span'
                ]
                
                content_element = None
                for selector in content_selectors:
                    try:
                        content_element = await tweet_element.query_selector(selector)
                        if content_element:
                            content_text = await content_element.inner_text()
                            if content_text and content_text.strip():
                                tweet_data['content'] = content_text.strip()
                                break
                    except Exception:
                        continue
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
            
            # 设置默认值
            tweet_data.setdefault('username', 'unknown')
            tweet_data.setdefault('content', '')
            tweet_data.setdefault('publish_time', datetime.now().isoformat())
            tweet_data.setdefault('link', '')
            tweet_data.setdefault('likes', 0)
            tweet_data.setdefault('comments', 0)
            tweet_data.setdefault('retweets', 0)
            
            # 验证推文数据的有效性
            if not tweet_data.get('content') and not tweet_data.get('username', '').replace('unknown', ''):
                self.logger.debug("推文数据无效，跳过")
                return None
            
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
            # 滚动页面加载更多推文
            await self.scroll_and_load_tweets(max_tweets)
            
            # 获取所有推文元素
            tweet_elements = await self.page.query_selector_all('[data-testid="tweet"]')
            
            tweets_data = []
            
            for i, tweet_element in enumerate(tweet_elements[:max_tweets]):
                # 模拟人工查看推文的行为
                if self.behavior_simulator and i % 3 == 0:  # 每3条推文模拟一次交互
                    await self.behavior_simulator.simulate_tweet_interaction(tweet_element)
                
                tweet_data = await self.parse_tweet_element(tweet_element)
                if tweet_data:
                    tweets_data.append(tweet_data)
                    self.logger.info(f"成功解析第 {i+1} 条推文: @{tweet_data['username']}")
                
                # 模拟人工阅读间隔
                if self.behavior_simulator:
                    await self.behavior_simulator.random_pause(0.5, 2.0)
            
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
            await self.navigate_to_profile(username)
            
            # 使用人工行为模拟器进行页面探索
            if self.behavior_simulator:
                self.logger.info(f"开始模拟用户浏览 @{username} 的页面")
                await self.behavior_simulator.simulate_page_exploration()
                
                # 模拟阅读行为
                await self.behavior_simulator.simulate_reading_behavior()
            else:
                await asyncio.sleep(3)  # 回退到基础等待
            
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
            await self.search_tweets(keyword)
            
            # 使用人工行为模拟器进行搜索页面探索
            if self.behavior_simulator:
                self.logger.info(f"开始模拟用户浏览关键词 '{keyword}' 的搜索结果")
                await self.behavior_simulator.simulate_page_exploration()
                
                # 模拟阅读搜索结果
                await self.behavior_simulator.simulate_reading_behavior()
            else:
                await asyncio.sleep(3)  # 回退到基础等待
            
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
            
            # 等待内容加载
            await asyncio.sleep(3)
            
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
    
    async def extract_media_content(self) -> List[Dict[str, Any]]:
        """
        提取推文中的图片、视频等多媒体内容
        
        Returns:
            多媒体内容列表
        """
        media_items = []
        
        try:
            # 抓取图片
            image_selectors = [
                '[data-testid="tweetPhoto"] img',
                'img[src*="pbs.twimg.com"]',
                'div[data-testid="tweetPhoto"] img'
            ]
            
            for selector in image_selectors:
                try:
                    images = await self.page.query_selector_all(selector)
                    for img in images:
                        src = await img.get_attribute('src')
                        alt = await img.get_attribute('alt') or ''
                        if src and 'pbs.twimg.com' in src:
                            media_items.append({
                                'type': 'image',
                                'url': src,
                                'description': alt,
                                'original_url': src.replace(':small', ':orig').replace(':medium', ':orig')
                            })
                    if images:
                        break
                except Exception:
                    continue
            
            # 抓取视频
            video_selectors = [
                'video',
                '[data-testid="videoPlayer"] video',
                'div[data-testid="videoComponent"] video'
            ]
            
            for selector in video_selectors:
                try:
                    videos = await self.page.query_selector_all(selector)
                    for video in videos:
                        poster = await video.get_attribute('poster')
                        src = await video.get_attribute('src')
                        media_items.append({
                            'type': 'video',
                            'poster': poster,
                            'url': src,
                            'description': '视频内容'
                        })
                    if videos:
                        break
                except Exception:
                    continue
            
            # 抓取GIF
            gif_selectors = [
                'img[src*="video.twimg.com"]',
                '[data-testid="tweetPhoto"] img[src*=".gif"]'
            ]
            
            for selector in gif_selectors:
                try:
                    gifs = await self.page.query_selector_all(selector)
                    for gif in gifs:
                        src = await gif.get_attribute('src')
                        alt = await gif.get_attribute('alt') or ''
                        if src:
                            media_items.append({
                                'type': 'gif',
                                'url': src,
                                'description': alt
                            })
                    if gifs:
                        break
                except Exception:
                    continue
            
            self.logger.info(f"提取到 {len(media_items)} 个多媒体内容")
            return media_items
            
        except Exception as e:
            self.logger.error(f"提取多媒体内容失败: {e}")
            return []
    
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
            
            for tweet in tweets:
                print(f"用户: @{tweet['username']}")
                print(f"内容: {tweet['content'][:100]}...")
                print(f"点赞: {tweet['likes']}, 评论: {tweet['comments']}, 转发: {tweet['retweets']}")
                print(f"链接: {tweet['link']}")
                print("-" * 50)
                
        except Exception as e:
            print(f"错误: {e}")
        finally:
            await parser.close()
    
    asyncio.run(main())