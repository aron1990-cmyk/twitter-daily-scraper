#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Twitter导航功能
诊断导航超时问题
"""

import asyncio
import logging
from playwright.async_api import async_playwright
from ads_browser_launcher import AdsPowerLauncher

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_twitter_navigation():
    """
    测试Twitter导航功能
    """
    browser_launcher = None
    browser = None
    page = None
    
    try:
        # 1. 启动AdsPower浏览器
        logger.info("=== 步骤1: 启动AdsPower浏览器 ===")
        browser_launcher = AdsPowerLauncher()
        browser_info = browser_launcher.start_browser()
        debug_port = browser_launcher.get_debug_port()
        logger.info(f"浏览器调试端口: {debug_port}")
        
        # 2. 连接到浏览器
        logger.info("=== 步骤2: 连接到浏览器 ===")
        playwright = await async_playwright().start()
        browser = await playwright.chromium.connect_over_cdp(debug_port)
        
        # 获取现有页面或创建新页面
        contexts = browser.contexts
        if contexts and contexts[0].pages:
            page = contexts[0].pages[0]
            logger.info(f"使用现有页面，当前URL: {page.url}")
        else:
            context = await browser.new_context()
            page = await context.new_page()
            logger.info("创建新页面")
        
        # 3. 测试基本导航
        logger.info("=== 步骤3: 测试基本导航 ===")
        
        # 设置较长的超时时间
        page.set_default_timeout(120000)  # 120秒
        
        # 先访问Twitter主页
        logger.info("导航到Twitter主页...")
        try:
            await page.goto('https://x.com', timeout=120000)
            await page.wait_for_load_state('networkidle', timeout=30000)
            logger.info("✅ 成功访问Twitter主页")
        except Exception as e:
            logger.error(f"❌ 访问Twitter主页失败: {e}")
            return
        
        # 等待页面完全加载
        await asyncio.sleep(5)
        
        # 4. 测试用户页面导航
        logger.info("=== 步骤4: 测试用户页面导航 ===")
        
        test_users = ['elonmusk', 'OpenAI', 'sama']
        
        for username in test_users:
            logger.info(f"\n--- 测试用户: @{username} ---")
            
            try:
                profile_url = f'https://x.com/{username}'
                logger.info(f"导航到: {profile_url}")
                
                # 使用更长的超时时间
                await page.goto(profile_url, timeout=120000)
                logger.info("页面导航完成，等待加载...")
                
                # 等待网络空闲
                await page.wait_for_load_state('networkidle', timeout=60000)
                logger.info("网络空闲状态达到")
                
                # 额外等待时间
                await asyncio.sleep(3)
                
                # 检查页面内容
                current_url = page.url
                logger.info(f"当前URL: {current_url}")
                
                # 检查是否有推文元素
                tweet_elements = await page.query_selector_all('[data-testid="tweet"]')
                logger.info(f"找到 {len(tweet_elements)} 个推文元素")
                
                # 检查页面标题
                title = await page.title()
                logger.info(f"页面标题: {title}")
                
                # 检查是否需要登录
                login_elements = await page.query_selector_all('text="登录"')
                if login_elements:
                    logger.warning("⚠️ 页面显示需要登录")
                
                # 检查是否被限制访问
                restricted_elements = await page.query_selector_all('text="Something went wrong"')
                if restricted_elements:
                    logger.warning("⚠️ 页面显示访问受限")
                
                logger.info(f"✅ 成功访问 @{username} 的页面")
                
            except Exception as e:
                logger.error(f"❌ 访问 @{username} 失败: {e}")
                
                # 尝试截图诊断
                try:
                    screenshot_path = f"./debug_screenshot_{username}.png"
                    await page.screenshot(path=screenshot_path)
                    logger.info(f"已保存诊断截图: {screenshot_path}")
                except:
                    pass
            
            # 每个用户之间等待一段时间
            await asyncio.sleep(2)
        
        # 5. 测试页面交互
        logger.info("=== 步骤5: 测试页面交互 ===")
        
        try:
            # 测试滚动
            logger.info("测试页面滚动...")
            await page.evaluate('window.scrollBy(0, 500)')
            await asyncio.sleep(1)
            await page.evaluate('window.scrollBy(0, 500)')
            await asyncio.sleep(1)
            await page.evaluate('window.scrollTo(0, 0)')
            logger.info("✅ 页面滚动测试成功")
            
        except Exception as e:
            logger.error(f"❌ 页面交互测试失败: {e}")
        
        logger.info("=== 测试完成 ===")
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        
    finally:
        # 清理资源
        try:
            if page:
                await page.close()
            if browser:
                await browser.close()
            if browser_launcher:
                browser_launcher.stop_browser()
        except Exception as e:
            logger.error(f"清理资源时发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_twitter_navigation())