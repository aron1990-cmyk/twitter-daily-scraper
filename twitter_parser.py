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

class TwitterParser:
    def __init__(self, debug_port: str):
        self.debug_port = debug_port
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.logger = logging.getLogger(__name__)
        
    async def connect_browser(self):
        """
        连接到 AdsPower 浏览器
        """
        try:
            playwright = await async_playwright().start()
            
            # 连接到现有的浏览器实例
            self.browser = await playwright.chromium.connect_over_cdp(self.debug_port)
            
            # 获取现有页面或创建新页面
            contexts = self.browser.contexts
            if contexts:
                pages = contexts[0].pages
                if pages:
                    self.page = pages[0]
                else:
                    self.page = await contexts[0].new_page()
            else:
                context = await self.browser.new_context()
                self.page = await context.new_page()
            
            self.logger.info("成功连接到浏览器")
            
        except Exception as e:
            self.logger.error(f"连接浏览器失败: {e}")
            raise
    
    async def navigate_to_twitter(self):
        """
        导航到 Twitter 主页
        """
        try:
            await self.page.goto('https://twitter.com', timeout=BROWSER_CONFIG['timeout'])
            await self.page.wait_for_load_state('networkidle')
            self.logger.info("成功导航到 Twitter")
            
        except Exception as e:
            self.logger.error(f"导航到 Twitter 失败: {e}")
            raise
    
    async def navigate_to_profile(self, username: str):
        """
        导航到指定用户的个人资料页面
        
        Args:
            username: Twitter 用户名（不包含@符号）
        """
        try:
            profile_url = f'https://twitter.com/{username}'
            await self.page.goto(profile_url, timeout=BROWSER_CONFIG['timeout'])
            await self.page.wait_for_load_state('networkidle')
            
            # 等待推文加载
            await asyncio.sleep(BROWSER_CONFIG['wait_time'])
            
            self.logger.info(f"成功导航到 @{username} 的个人资料页面")
            
        except Exception as e:
            self.logger.error(f"导航到 @{username} 个人资料页面失败: {e}")
            raise
    
    async def search_tweets(self, keyword: str):
        """
        搜索包含指定关键词的推文
        
        Args:
            keyword: 搜索关键词
        """
        try:
            search_url = f'https://twitter.com/search?q={keyword}&src=typed_query&f=live'
            await self.page.goto(search_url, timeout=BROWSER_CONFIG['timeout'])
            await self.page.wait_for_load_state('networkidle')
            
            # 等待搜索结果加载
            await asyncio.sleep(BROWSER_CONFIG['wait_time'])
            
            self.logger.info(f"成功搜索关键词: {keyword}")
            
        except Exception as e:
            self.logger.error(f"搜索关键词 '{keyword}' 失败: {e}")
            raise
    
    async def scroll_and_load_tweets(self, max_tweets: int = 10):
        """
        滚动页面并加载更多推文
        
        Args:
            max_tweets: 最大加载推文数量
        """
        try:
            # 滚动页面以加载更多推文
            for i in range(max_tweets // 5 + 1):  # 每次滚动大约加载5条推文
                await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await asyncio.sleep(BROWSER_CONFIG['scroll_pause_time'])
                
                # 检查是否已经加载足够的推文
                tweets = await self.page.query_selector_all('[data-testid="tweet"]')
                if len(tweets) >= max_tweets:
                    break
            
            self.logger.info(f"页面滚动完成，当前可见推文数量: {len(tweets)}")
            
        except Exception as e:
            self.logger.error(f"滚动页面失败: {e}")
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
            
            # 提取用户名
            username_element = await tweet_element.query_selector('[data-testid="User-Name"] a')
            if username_element:
                username_href = await username_element.get_attribute('href')
                if username_href:
                    tweet_data['username'] = username_href.split('/')[-1]
            
            # 提取推文内容
            content_element = await tweet_element.query_selector('[data-testid="tweetText"]')
            if content_element:
                tweet_data['content'] = await content_element.inner_text()
            
            # 提取发布时间
            time_element = await tweet_element.query_selector('time')
            if time_element:
                datetime_attr = await time_element.get_attribute('datetime')
                if datetime_attr:
                    tweet_data['publish_time'] = datetime_attr
            
            # 提取推文链接
            link_elements = await tweet_element.query_selector_all('a[href*="/status/"]')
            if link_elements:
                href = await link_elements[0].get_attribute('href')
                if href:
                    tweet_data['link'] = f"https://twitter.com{href}"
            
            # 提取互动数据（点赞、评论、转发）
            # 点赞数
            like_element = await tweet_element.query_selector('[data-testid="like"]')
            if like_element:
                like_text = await like_element.get_attribute('aria-label') or ''
                tweet_data['likes'] = self.extract_number(like_text)
            
            # 评论数
            reply_element = await tweet_element.query_selector('[data-testid="reply"]')
            if reply_element:
                reply_text = await reply_element.get_attribute('aria-label') or ''
                tweet_data['comments'] = self.extract_number(reply_text)
            
            # 转发数
            retweet_element = await tweet_element.query_selector('[data-testid="retweet"]')
            if retweet_element:
                retweet_text = await retweet_element.get_attribute('aria-label') or ''
                tweet_data['retweets'] = self.extract_number(retweet_text)
            
            # 设置默认值
            tweet_data.setdefault('username', 'unknown')
            tweet_data.setdefault('content', '')
            tweet_data.setdefault('publish_time', datetime.now().isoformat())
            tweet_data.setdefault('link', '')
            tweet_data.setdefault('likes', 0)
            tweet_data.setdefault('comments', 0)
            tweet_data.setdefault('retweets', 0)
            
            return tweet_data
            
        except Exception as e:
            self.logger.error(f"解析推文元素失败: {e}")
            return None
    
    async def scrape_tweets(self, max_tweets: int = 10) -> List[Dict[str, Any]]:
        """
        抓取当前页面的推文数据
        
        Args:
            max_tweets: 最大抓取推文数量
            
        Returns:
            推文数据列表
        """
        try:
            # 滚动页面加载更多推文
            await self.scroll_and_load_tweets(max_tweets)
            
            # 获取所有推文元素
            tweet_elements = await self.page.query_selector_all('[data-testid="tweet"]')
            
            tweets_data = []
            
            for i, tweet_element in enumerate(tweet_elements[:max_tweets]):
                tweet_data = await self.parse_tweet_element(tweet_element)
                if tweet_data:
                    tweets_data.append(tweet_data)
                    self.logger.info(f"成功解析第 {i+1} 条推文: @{tweet_data['username']}")
            
            self.logger.info(f"总共抓取到 {len(tweets_data)} 条推文")
            return tweets_data
            
        except Exception as e:
            self.logger.error(f"抓取推文失败: {e}")
            return []
    
    async def scrape_user_tweets(self, username: str, max_tweets: int = 10) -> List[Dict[str, Any]]:
        """
        抓取指定用户的推文
        
        Args:
            username: Twitter 用户名
            max_tweets: 最大抓取推文数量
            
        Returns:
            推文数据列表
        """
        try:
            await self.navigate_to_profile(username)
            tweets = await self.scrape_tweets(max_tweets)
            
            # 为每条推文添加来源信息
            for tweet in tweets:
                tweet['source'] = f'@{username}'
                tweet['source_type'] = 'user_profile'
            
            return tweets
            
        except Exception as e:
            self.logger.error(f"抓取用户 @{username} 的推文失败: {e}")
            return []
    
    async def scrape_keyword_tweets(self, keyword: str, max_tweets: int = 10) -> List[Dict[str, Any]]:
        """
        抓取包含指定关键词的推文
        
        Args:
            keyword: 搜索关键词
            max_tweets: 最大抓取推文数量
            
        Returns:
            推文数据列表
        """
        try:
            await self.search_tweets(keyword)
            tweets = await self.scrape_tweets(max_tweets)
            
            # 为每条推文添加来源信息
            for tweet in tweets:
                tweet['source'] = keyword
                tweet['source_type'] = 'keyword_search'
            
            return tweets
            
        except Exception as e:
            self.logger.error(f"抓取关键词 '{keyword}' 的推文失败: {e}")
            return []
    
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