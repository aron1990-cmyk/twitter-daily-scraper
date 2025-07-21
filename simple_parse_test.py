#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的解析方法测试
"""

import asyncio
import logging
from playwright.async_api import async_playwright

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def simple_parse_test():
    """简单的解析测试"""
    async with async_playwright() as p:
        try:
            # 连接到现有的浏览器实例
            logger.info("🔍 尝试连接到现有浏览器...")
            
            # 尝试连接到AdsPower浏览器
            browser = await p.chromium.connect_over_cdp("ws://127.0.0.1:50671/devtools/browser/bb596ca1-9991-422f-b696-bc3edfadb4b6")
            logger.info("✅ 成功连接到浏览器")
            
            # 获取页面
            contexts = browser.contexts
            if not contexts:
                logger.error("❌ 没有找到浏览器上下文")
                return
            
            pages = contexts[0].pages
            if not pages:
                logger.error("❌ 没有找到页面")
                return
            
            page = pages[0]
            logger.info(f"✅ 使用页面: {page.url}")
            
            # 检查当前页面是否是Twitter页面
            current_url = page.url
            if 'x.com' not in current_url and 'twitter.com' not in current_url:
                logger.info("🔍 导航到Twitter页面...")
                await page.goto('https://x.com/elonmusk')
                await asyncio.sleep(3)
            
            # 查找推文元素
            logger.info("🔍 查找推文元素...")
            tweet_elements = await page.query_selector_all('[data-testid="tweet"]')
            logger.info(f"找到 {len(tweet_elements)} 个推文元素")
            
            if not tweet_elements:
                logger.error("❌ 未找到推文元素")
                return
            
            # 测试解析第一个推文元素
            logger.info("🔧 开始测试解析第一个推文元素...")
            first_element = tweet_elements[0]
            
            # 手动提取基本信息
            logger.info("🔧 手动提取推文信息...")
            
            # 提取用户名
            username = 'unknown'
            try:
                username_element = await first_element.query_selector('[data-testid="User-Name"] [dir="ltr"]')
                if username_element:
                    username_text = await username_element.text_content()
                    username = username_text.strip().split()[0] if username_text else 'unknown'
                    logger.info(f"✅ 用户名: {username}")
            except Exception as e:
                logger.error(f"❌ 提取用户名失败: {e}")
            
            # 提取内容
            content = 'No content available'
            try:
                content_element = await first_element.query_selector('[data-testid="tweetText"]')
                if content_element:
                    content_text = await content_element.text_content()
                    content = content_text.strip() if content_text else 'No content available'
                    logger.info(f"✅ 内容: {content[:100]}...")
            except Exception as e:
                logger.error(f"❌ 提取内容失败: {e}")
            
            # 提取链接
            link = ''
            try:
                link_element = await first_element.query_selector('a[href*="/status/"]')
                if link_element:
                    href = await link_element.get_attribute('href')
                    if href:
                        link = f'https://x.com{href}' if href.startswith('/') else href
                        logger.info(f"✅ 链接: {link}")
            except Exception as e:
                logger.error(f"❌ 提取链接失败: {e}")
            
            # 验证数据
            has_username = username and username != 'unknown'
            has_content = content and content != 'No content available'
            has_link = link and link.strip()
            
            logger.info(f"🔧 验证结果:")
            logger.info(f"   - 用户名有效: {has_username}")
            logger.info(f"   - 内容有效: {has_content}")
            logger.info(f"   - 链接有效: {has_link}")
            
            if has_username or has_content or has_link:
                logger.info("✅ 推文数据有效")
            else:
                logger.error("❌ 推文数据无效")
            
        except Exception as e:
            logger.error(f"测试过程中发生错误: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(simple_parse_test())