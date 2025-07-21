#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试推文选择器脚本
用于检查页面上实际存在的推文元素
"""

import asyncio
import logging
import sys
import os
from playwright.async_api import async_playwright

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ads_browser_launcher import AdsPowerLauncher

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# AdsPower配置
ADS_POWER_CONFIG = {
    'user_id': 'k11p9ypc',
    'open_tabs': 1,
    'launch_args': [],
    'headless': False,
    'disable_password_filling': False,
    'clear_cache_after_closing': False,
    'enable_password_saving': False
}

async def debug_tweet_selectors():
    """调试推文选择器"""
    launcher = None
    
    try:
        # 启动浏览器
        logger.info("🚀 启动浏览器...")
        launcher = AdsPowerLauncher(ADS_POWER_CONFIG)
        browser_info = launcher.start_browser()
        launcher.wait_for_browser_ready()
        debug_port = launcher.get_debug_port()
        logger.info(f"✅ 浏览器启动成功，调试端口: {debug_port}")
        
        async with async_playwright() as p:
            logger.info(f"连接到浏览器: {debug_port}")
            browser = await p.chromium.connect_over_cdp(debug_port)
            
            # 获取现有上下文和页面
            contexts = browser.contexts
            if not contexts:
                logger.error("没有找到浏览器上下文")
                return
            
            context = contexts[0]
            pages = context.pages
            if not pages:
                logger.error("没有找到页面")
                return
            
            page = pages[0]
            current_url = page.url
            logger.info(f"当前页面URL: {current_url}")
            
            # 等待页面加载
            await asyncio.sleep(3)
            
            # 测试各种推文选择器
            selectors_to_test = [
                'article[data-testid="tweet"]',
                '[data-testid="tweet"]',
                'article',
                '[data-testid="cellInnerDiv"]',
                '[data-testid="primaryColumn"] article',
                'div[data-testid="cellInnerDiv"] > div',
                '[role="article"]',
                'div[data-testid="tweetText"]',
                'article[role="article"]',
                'div[aria-label*="Timeline"] article',
                'section[aria-labelledby] article'
            ]
            
            logger.info("开始测试推文选择器...")
            
            for selector in selectors_to_test:
                try:
                    elements = await page.query_selector_all(selector)
                    logger.info(f"选择器 '{selector}': 找到 {len(elements)} 个元素")
                    
                    # 如果找到元素，检查前几个的内容
                    if elements:
                        for i, element in enumerate(elements[:3]):
                            try:
                                # 检查是否包含推文文本
                                text_element = await element.query_selector('[data-testid="tweetText"]')
                                if text_element:
                                    text_content = await text_element.inner_text()
                                    logger.info(f"  元素 {i+1} 包含推文文本: {text_content[:50]}...")
                                else:
                                    # 检查是否有其他文本内容
                                    inner_text = await element.inner_text()
                                    if inner_text and len(inner_text.strip()) > 10:
                                        logger.info(f"  元素 {i+1} 内容: {inner_text[:50]}...")
                            except Exception as e:
                                logger.debug(f"  检查元素 {i+1} 失败: {e}")
                                
                except Exception as e:
                    logger.warning(f"选择器 '{selector}' 测试失败: {e}")
            
            # 检查页面是否需要登录
            try:
                login_elements = await page.query_selector_all('[data-testid="loginButton"], [href="/login"], [href="/i/flow/login"]')
                if login_elements:
                    logger.warning("页面可能需要登录！")
                else:
                    logger.info("页面不需要登录")
            except Exception as e:
                logger.debug(f"检查登录状态失败: {e}")
            
            # 检查是否有错误消息
            try:
                error_selectors = [
                    '[data-testid="error"]',
                    '[role="alert"]',
                    '.error',
                    '[data-testid="emptyState"]'
                ]
                
                for error_selector in error_selectors:
                    error_elements = await page.query_selector_all(error_selector)
                    if error_elements:
                        for error_element in error_elements:
                            error_text = await error_element.inner_text()
                            if error_text:
                                logger.warning(f"发现错误消息: {error_text}")
            except Exception as e:
                logger.debug(f"检查错误消息失败: {e}")
            
            # 获取页面标题
            try:
                title = await page.title()
                logger.info(f"页面标题: {title}")
            except Exception as e:
                logger.debug(f"获取页面标题失败: {e}")
            
            logger.info("推文选择器调试完成")
            
    except Exception as e:
        logger.error(f"调试失败: {e}")
        
    finally:
        # 清理资源
        if launcher:
            try:
                launcher.stop_browser()
                logger.info("✅ 浏览器已关闭")
            except Exception as e:
                logger.warning(f"关闭浏览器时出错: {e}")

if __name__ == "__main__":
    asyncio.run(debug_tweet_selectors())