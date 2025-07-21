#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试数据抓取问题的脚本
用于诊断为什么互动数据（点赞、转发、评论）都是0
"""

import asyncio
import logging
from playwright.async_api import async_playwright
from datetime import datetime
import json
import re

# 设置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug_scraping.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TwitterDebugger:
    """Twitter数据抓取调试器"""
    
    def __init__(self):
        self.logger = logger
        
    def extract_number(self, text: str) -> int:
        """从文本中提取数字（处理K、M等单位）"""
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
    
    async def debug_tweet_elements(self, page):
        """调试推文元素结构"""
        try:
            # 等待推文加载
            await page.wait_for_selector('article[data-testid="tweet"]', timeout=10000)
            
            # 获取所有推文元素
            tweet_elements = await page.query_selector_all('article[data-testid="tweet"]')
            self.logger.info(f"找到 {len(tweet_elements)} 个推文元素")
            
            for i, tweet_element in enumerate(tweet_elements[:3]):  # 只调试前3个
                self.logger.info(f"\n=== 调试推文 {i+1} ===")
                await self.debug_single_tweet(tweet_element, i+1)
                
        except Exception as e:
            self.logger.error(f"调试推文元素失败: {e}")
    
    async def debug_single_tweet(self, tweet_element, index):
        """调试单个推文元素"""
        try:
            # 1. 检查推文内容
            content_selectors = [
                '[data-testid="tweetText"]',
                '[lang] span',
                'div[dir="auto"] span'
            ]
            
            content_found = False
            for selector in content_selectors:
                try:
                    content_element = await tweet_element.query_selector(selector)
                    if content_element:
                        content_text = await content_element.inner_text()
                        if content_text and content_text.strip():
                            self.logger.info(f"推文内容: {content_text[:100]}...")
                            content_found = True
                            break
                except Exception as e:
                    self.logger.debug(f"选择器 {selector} 失败: {e}")
            
            if not content_found:
                self.logger.warning("未找到推文内容")
            
            # 2. 调试互动数据
            await self.debug_interactions(tweet_element)
            
            # 3. 检查用户名
            await self.debug_username(tweet_element)
            
            # 4. 检查时间
            await self.debug_timestamp(tweet_element)
            
        except Exception as e:
            self.logger.error(f"调试单个推文失败: {e}")
    
    async def debug_interactions(self, tweet_element):
        """调试互动数据提取"""
        self.logger.info("--- 调试互动数据 ---")
        
        # 点赞数调试
        await self.debug_interaction_type(tweet_element, "点赞", [
            '[data-testid="like"]',
            '[aria-label*="like"]',
            '[aria-label*="Like"]',
            'button[aria-label*="like"]',
            'div[aria-label*="like"]'
        ])
        
        # 转发数调试
        await self.debug_interaction_type(tweet_element, "转发", [
            '[data-testid="retweet"]',
            '[aria-label*="retweet"]',
            '[aria-label*="Retweet"]',
            'button[aria-label*="retweet"]',
            'div[aria-label*="retweet"]'
        ])
        
        # 评论数调试
        await self.debug_interaction_type(tweet_element, "评论", [
            '[data-testid="reply"]',
            '[aria-label*="repl"]',
            '[aria-label*="Reply"]',
            'button[aria-label*="repl"]',
            'div[aria-label*="repl"]'
        ])
    
    async def debug_interaction_type(self, tweet_element, interaction_name, selectors):
        """调试特定类型的互动数据"""
        self.logger.info(f"调试{interaction_name}数据:")
        
        found_elements = []
        for selector in selectors:
            try:
                elements = await tweet_element.query_selector_all(selector)
                if elements:
                    for element in elements:
                        aria_label = await element.get_attribute('aria-label')
                        inner_text = await element.inner_text()
                        
                        found_elements.append({
                            'selector': selector,
                            'aria_label': aria_label,
                            'inner_text': inner_text,
                            'extracted_number': self.extract_number(aria_label or '')
                        })
                        
                        self.logger.info(f"  选择器: {selector}")
                        self.logger.info(f"  aria-label: {aria_label}")
                        self.logger.info(f"  inner_text: {inner_text}")
                        self.logger.info(f"  提取的数字: {self.extract_number(aria_label or '')}")
                        
            except Exception as e:
                self.logger.debug(f"选择器 {selector} 失败: {e}")
        
        if not found_elements:
            self.logger.warning(f"未找到{interaction_name}元素")
            
            # 尝试查找所有可能的互动按钮
            try:
                all_buttons = await tweet_element.query_selector_all('button')
                self.logger.info(f"找到 {len(all_buttons)} 个按钮元素")
                
                for i, button in enumerate(all_buttons[:10]):  # 只检查前10个
                    aria_label = await button.get_attribute('aria-label')
                    if aria_label:
                        self.logger.info(f"  按钮 {i+1} aria-label: {aria_label}")
                        
            except Exception as e:
                self.logger.debug(f"查找按钮元素失败: {e}")
    
    async def debug_username(self, tweet_element):
        """调试用户名提取"""
        self.logger.info("--- 调试用户名 ---")
        
        username_selectors = [
            '[data-testid="User-Name"] a',
            '[data-testid="User-Names"] a',
            'a[href^="/"][role="link"]',
            'a[href*="/"]'
        ]
        
        for selector in username_selectors:
            try:
                username_element = await tweet_element.query_selector(selector)
                if username_element:
                    username_href = await username_element.get_attribute('href')
                    username_text = await username_element.inner_text()
                    
                    self.logger.info(f"选择器: {selector}")
                    self.logger.info(f"href: {username_href}")
                    self.logger.info(f"text: {username_text}")
                    
                    if username_href and '/' in username_href:
                        username = username_href.split('/')[-1]
                        self.logger.info(f"提取的用户名: {username}")
                        break
                        
            except Exception as e:
                self.logger.debug(f"选择器 {selector} 失败: {e}")
    
    async def debug_timestamp(self, tweet_element):
        """调试时间戳提取"""
        self.logger.info("--- 调试时间戳 ---")
        
        try:
            time_element = await tweet_element.query_selector('time')
            if time_element:
                datetime_attr = await time_element.get_attribute('datetime')
                time_text = await time_element.inner_text()
                
                self.logger.info(f"datetime属性: {datetime_attr}")
                self.logger.info(f"时间文本: {time_text}")
            else:
                self.logger.warning("未找到time元素")
                
        except Exception as e:
            self.logger.error(f"调试时间戳失败: {e}")
    
    async def run_debug(self, url: str = "https://x.com/elonmusk"):
        """运行调试"""
        async with async_playwright() as p:
            # 启动浏览器
            browser = await p.chromium.launch(
                headless=False,  # 显示浏览器窗口以便观察
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            try:
                # 创建页面
                page = await browser.new_page()
                
                # 设置用户代理
                await page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                })
                
                # 访问页面
                self.logger.info(f"访问页面: {url}")
                try:
                    await page.goto(url, wait_until='domcontentloaded', timeout=15000)
                except Exception as e:
                    self.logger.warning(f"页面加载超时，尝试继续: {e}")
                    # 如果超时，尝试直接访问
                    await page.goto(url, timeout=10000)
                
                # 等待页面加载
                await asyncio.sleep(8)
                
                # 开始调试
                await self.debug_tweet_elements(page)
                
                # 保持浏览器打开一段时间以便观察
                self.logger.info("调试完成，浏览器将在30秒后关闭...")
                await asyncio.sleep(30)
                
            finally:
                await browser.close()

async def main():
    """主函数"""
    debugger = TwitterDebugger()
    
    # 可以修改URL来调试不同的页面
    urls_to_debug = [
        "https://x.com/elonmusk",
        # "https://x.com/OpenAI",
        # "https://x.com/home"
    ]
    
    for url in urls_to_debug:
        logger.info(f"\n{'='*50}")
        logger.info(f"开始调试: {url}")
        logger.info(f"{'='*50}")
        
        try:
            await debugger.run_debug(url)
        except Exception as e:
            logger.error(f"调试失败: {e}")
        
        # 在调试不同URL之间等待
        await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())