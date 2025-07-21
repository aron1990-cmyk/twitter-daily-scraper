#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
元素结构调试测试
专门用于检查推文元素的HTML结构和选择器有效性
"""

import asyncio
import logging
from playwright.async_api import async_playwright
import json
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('element_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def debug_tweet_elements():
    """调试推文元素结构"""
    try:
        async with async_playwright() as p:
            # 连接到现有的浏览器实例
            browser = await p.chromium.connect_over_cdp("ws://127.0.0.1:50671")
            
            # 获取现有页面
            contexts = browser.contexts
            if not contexts:
                logger.error("没有找到浏览器上下文")
                return
            
            pages = contexts[0].pages
            if not pages:
                logger.error("没有找到页面")
                return
            
            page = pages[0]
            logger.info(f"当前页面URL: {page.url}")
            
            # 等待页面加载
            await page.wait_for_load_state('networkidle', timeout=10000)
            
            # 查找推文元素
            tweet_elements = await page.query_selector_all('[data-testid="tweet"]')
            logger.info(f"找到 {len(tweet_elements)} 个推文元素")
            
            if not tweet_elements:
                logger.warning("没有找到推文元素，尝试其他选择器")
                # 尝试其他可能的选择器
                alternative_selectors = [
                    'article[data-testid="tweet"]',
                    '[data-testid="cellInnerDiv"]',
                    'div[data-testid="tweet"]'
                ]
                
                for selector in alternative_selectors:
                    elements = await page.query_selector_all(selector)
                    logger.info(f"选择器 '{selector}' 找到 {len(elements)} 个元素")
                    if elements:
                        tweet_elements = elements[:3]  # 只取前3个
                        break
            
            # 分析前3个推文元素的结构
            for i, element in enumerate(tweet_elements[:3]):
                logger.info(f"\n=== 分析第 {i+1} 个推文元素 ===")
                
                # 获取元素的HTML结构
                try:
                    html = await element.inner_html()
                    logger.info(f"元素HTML长度: {len(html)} 字符")
                    
                    # 检查各种选择器
                    selectors_to_check = {
                        '用户名': [
                            '[data-testid="User-Name"] [dir="ltr"]',
                            '[data-testid="User-Name"] span',
                            'a[href^="/"][role="link"] span',
                            '[dir="ltr"] span'
                        ],
                        '内容': [
                            '[data-testid="tweetText"]',
                            '[lang] span',
                            'div[dir="auto"] span'
                        ],
                        '链接': [
                            'a[href*="/status/"]'
                        ],
                        '时间': [
                            'time'
                        ],
                        '互动': [
                            '[data-testid="like"]',
                            '[data-testid="reply"]',
                            '[data-testid="retweet"]'
                        ],
                        '媒体': [
                            'img[src*="pbs.twimg.com"]',
                            'video',
                            '[data-testid="videoPlayer"]'
                        ]
                    }
                    
                    for category, selectors in selectors_to_check.items():
                        logger.info(f"\n--- {category} ---")
                        for selector in selectors:
                            try:
                                elements = await element.query_selector_all(selector)
                                logger.info(f"  选择器 '{selector}': {len(elements)} 个元素")
                                
                                if elements:
                                    # 获取第一个元素的文本或属性
                                    first_element = elements[0]
                                    text = await first_element.text_content()
                                    if text:
                                        logger.info(f"    文本: '{text[:100]}...'")
                                    
                                    # 对于链接和时间，也检查属性
                                    if 'href' in selector:
                                        href = await first_element.get_attribute('href')
                                        if href:
                                            logger.info(f"    href: '{href}'")
                                    
                                    if selector == 'time':
                                        datetime_attr = await first_element.get_attribute('datetime')
                                        if datetime_attr:
                                            logger.info(f"    datetime: '{datetime_attr}'")
                                        
                            except Exception as e:
                                logger.debug(f"  选择器 '{selector}' 检查失败: {e}")
                    
                    # 保存HTML到文件以便进一步分析
                    with open(f'tweet_element_{i+1}.html', 'w', encoding='utf-8') as f:
                        f.write(html)
                    logger.info(f"HTML已保存到 tweet_element_{i+1}.html")
                    
                except Exception as e:
                    logger.error(f"分析第 {i+1} 个元素失败: {e}")
            
            logger.info("\n=== 元素结构调试完成 ===")
            
    except Exception as e:
        logger.error(f"调试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(debug_tweet_elements())