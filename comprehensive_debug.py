#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面的推文元素调试脚本
检查页面结构、等待加载、尝试滚动
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

async def comprehensive_debug():
    """全面调试推文元素"""
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
            logger.info(f"📍 当前页面: {current_url}")
            
            # 如果不在Twitter页面，导航到Twitter首页
            if 'x.com' not in current_url and 'twitter.com' not in current_url:
                logger.info("🔄 导航到Twitter首页...")
                await page.goto('https://x.com', wait_until='domcontentloaded')
                await asyncio.sleep(5)
                logger.info("✅ 已导航到Twitter首页")
            
            # 等待页面完全加载
            logger.info("⏳ 等待页面完全加载...")
            await asyncio.sleep(10)
            
            # 检查页面的基本结构
            logger.info("🔍 检查页面基本结构...")
            
            # 检查主要容器
            main_containers = [
                'main[role="main"]',
                '[data-testid="primaryColumn"]',
                '[data-testid="AppTabBar"]',
                'div[data-testid="sidebarColumn"]',
                'section[aria-labelledby]',
                'div[aria-label*="Timeline"]',
                'div[aria-label*="时间线"]'
            ]
            
            for container in main_containers:
                try:
                    elements = await page.query_selector_all(container)
                    logger.info(f"容器 '{container}': 找到 {len(elements)} 个")
                except Exception as e:
                    logger.debug(f"检查容器 '{container}' 失败: {e}")
            
            # 检查所有可能的推文相关元素
            logger.info("\n🐦 检查推文相关元素...")
            
            tweet_selectors = [
                # 标准推文选择器
                'article[data-testid="tweet"]',
                '[data-testid="tweet"]',
                'article[role="article"]',
                'article',
                
                # 推文内容选择器
                '[data-testid="tweetText"]',
                'div[data-testid="tweetText"]',
                'span[data-testid="tweetText"]',
                
                # 推文容器选择器
                '[data-testid="cellInnerDiv"]',
                'div[data-testid="cellInnerDiv"]',
                '[data-testid="primaryColumn"] > div > div',
                
                # 时间线相关选择器
                'section[aria-labelledby] > div > div',
                'div[aria-label*="Timeline"] > div',
                'div[aria-label*="时间线"] > div',
                
                # 其他可能的选择器
                '[role="article"]',
                'div[dir="auto"]',
                'div[lang]',
                'span[dir="auto"]',
                'div[data-testid="User-Name"]',
                'time[datetime]'
            ]
            
            found_elements = {}
            
            for selector in tweet_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    count = len(elements)
                    logger.info(f"选择器 '{selector}': 找到 {count} 个元素")
                    
                    if count > 0:
                        found_elements[selector] = count
                        
                        # 检查前几个元素的内容
                        for i, element in enumerate(elements[:3]):
                            try:
                                text_content = await element.inner_text()
                                if text_content and len(text_content.strip()) > 5:
                                    logger.info(f"  元素 {i+1} 内容: {text_content[:80]}...")
                            except Exception as e:
                                logger.debug(f"  检查元素 {i+1} 内容失败: {e}")
                                
                except Exception as e:
                    logger.debug(f"选择器 '{selector}' 测试失败: {e}")
            
            # 尝试滚动页面
            logger.info("\n📜 尝试滚动页面加载更多内容...")
            
            for scroll_attempt in range(3):
                logger.info(f"滚动尝试 {scroll_attempt + 1}/3")
                await page.evaluate('window.scrollBy(0, 1000)')
                await asyncio.sleep(3)
                
                # 重新检查最有希望的选择器
                best_selectors = ['article[data-testid="tweet"]', '[data-testid="tweet"]', 'article']
                for selector in best_selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        logger.info(f"  滚动后选择器 '{selector}': 找到 {len(elements)} 个元素")
                    except Exception as e:
                        logger.debug(f"  滚动后检查选择器 '{selector}' 失败: {e}")
            
            # 检查页面是否有特殊状态
            logger.info("\n🔍 检查页面特殊状态...")
            
            # 检查是否需要登录
            login_selectors = [
                '[data-testid="loginButton"]',
                '[href="/login"]',
                '[href="/i/flow/login"]',
                'a[href*="login"]',
                'button[data-testid="loginButton"]'
            ]
            
            login_required = False
            for login_selector in login_selectors:
                try:
                    login_elements = await page.query_selector_all(login_selector)
                    if login_elements:
                        logger.warning(f"发现登录元素: {login_selector} ({len(login_elements)} 个)")
                        login_required = True
                except Exception as e:
                    logger.debug(f"检查登录选择器 '{login_selector}' 失败: {e}")
            
            if not login_required:
                logger.info("✅ 页面不需要登录")
            
            # 检查是否有错误或空状态
            error_selectors = [
                '[data-testid="error"]',
                '[role="alert"]',
                '.error',
                '[data-testid="emptyState"]',
                '[data-testid="empty"]',
                'div[data-testid="emptyState"]'
            ]
            
            for error_selector in error_selectors:
                try:
                    error_elements = await page.query_selector_all(error_selector)
                    if error_elements:
                        for error_element in error_elements:
                            error_text = await error_element.inner_text()
                            if error_text:
                                logger.warning(f"发现错误/空状态消息: {error_text}")
                except Exception as e:
                    logger.debug(f"检查错误选择器 '{error_selector}' 失败: {e}")
            
            # 获取页面的完整HTML结构（部分）
            logger.info("\n📄 获取页面结构信息...")
            try:
                # 获取主要内容区域的HTML
                main_content = await page.query_selector('main[role="main"]')
                if main_content:
                    main_html = await main_content.inner_html()
                    logger.info(f"主内容区域HTML长度: {len(main_html)} 字符")
                    
                    # 检查是否包含推文相关的关键词
                    keywords = ['tweet', 'data-testid', 'article', 'timeline', 'cellInnerDiv']
                    for keyword in keywords:
                        if keyword.lower() in main_html.lower():
                            count = main_html.lower().count(keyword.lower())
                            logger.info(f"  关键词 '{keyword}' 出现 {count} 次")
                else:
                    logger.warning("未找到主内容区域")
            except Exception as e:
                logger.warning(f"获取页面结构失败: {e}")
            
            # 总结发现的元素
            logger.info("\n📊 调试总结:")
            if found_elements:
                logger.info("找到的元素:")
                for selector, count in found_elements.items():
                    logger.info(f"  {selector}: {count} 个")
            else:
                logger.warning("❌ 未找到任何推文相关元素！")
                logger.info("可能的原因:")
                logger.info("  1. 页面还在加载中")
                logger.info("  2. 需要登录")
                logger.info("  3. Twitter页面结构发生了变化")
                logger.info("  4. 页面显示错误或空状态")
                logger.info("  5. 需要更长的等待时间")
            
            # 获取页面标题和URL
            try:
                title = await page.title()
                url = page.url
                logger.info(f"\n页面信息:")
                logger.info(f"  标题: {title}")
                logger.info(f"  URL: {url}")
            except Exception as e:
                logger.debug(f"获取页面信息失败: {e}")
            
            logger.info("\n✅ 全面调试完成")
            
    except Exception as e:
        logger.error(f"❌ 调试失败: {e}")
        
    finally:
        # 清理资源
        if launcher:
            try:
                launcher.stop_browser()
                logger.info("✅ 浏览器已关闭")
            except Exception as e:
                logger.warning(f"关闭浏览器时出错: {e}")

if __name__ == "__main__":
    asyncio.run(comprehensive_debug())