#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
人工行为模拟器演示脚本
展示如何在Twitter抓取中使用人工行为模拟
"""

import asyncio
import logging
from playwright.async_api import async_playwright
from human_behavior_simulator import HumanBehaviorSimulator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def demo_twitter_like_behavior():
    """
    演示类似Twitter抓取的人工行为模拟
    """
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            # 初始化人工行为模拟器
            behavior_simulator = HumanBehaviorSimulator(page)
            logger.info("人工行为模拟器初始化完成")
            
            # 模拟访问一个有内容的页面（使用GitHub作为示例）
            demo_url = "https://github.com/trending"
            logger.info(f"导航到演示页面: {demo_url}")
            await page.goto(demo_url, wait_until='networkidle')
            
            # 模拟用户刚到达页面的行为
            logger.info("模拟用户刚到达页面的探索行为")
            await behavior_simulator.simulate_page_exploration()
            
            # 模拟查看页面内容
            logger.info("模拟阅读页面内容")
            await behavior_simulator.simulate_reading_behavior()
            
            # 模拟滚动查看更多内容
            logger.info("模拟滚动查看更多内容")
            for i in range(3):
                logger.info(f"第 {i+1} 次滚动")
                await behavior_simulator.human_like_scroll('down', distance=400)
                
                # 模拟查看新出现的内容
                await behavior_simulator.simulate_reading_behavior()
                
                # 随机停顿
                await behavior_simulator.random_pause(1, 3)
            
            # 模拟智能滚动和收集（使用GitHub的仓库卡片作为示例）
            logger.info("演示智能滚动和收集功能")
            collected_items = await behavior_simulator.smart_scroll_and_collect(
                max_tweets=5,  # 收集5个项目
                target_selector='article'  # GitHub trending页面的文章元素
            )
            
            logger.info(f"智能收集完成，收集到 {len(collected_items)} 个项目")
            
            # 模拟用户会话结束前的行为
            logger.info("模拟会话结束行为")
            await behavior_simulator.simulate_page_exploration()
            
            logger.info("演示完成，保持页面打开5秒钟以便观察...")
            await asyncio.sleep(5)
            
            await browser.close()
            
    except Exception as e:
        logger.error(f"演示过程中发生错误: {e}")
        raise

async def demo_multi_window_simulation():
    """
    演示多窗口并行人工行为模拟
    """
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            
            # 创建多个页面模拟多窗口
            pages = []
            simulators = []
            
            urls = [
                "https://example.com",
                "https://httpbin.org/html",
                "https://github.com"
            ]
            
            # 初始化多个窗口
            for i, url in enumerate(urls):
                page = await browser.new_page()
                simulator = HumanBehaviorSimulator(page)
                
                pages.append(page)
                simulators.append(simulator)
                
                logger.info(f"窗口 {i+1} 初始化完成")
            
            # 并行执行多窗口行为模拟
            async def simulate_window(page, simulator, url, window_id):
                try:
                    logger.info(f"窗口 {window_id} 开始导航到: {url}")
                    await page.goto(url, wait_until='networkidle')
                    
                    # 模拟用户行为
                    await simulator.simulate_page_exploration()
                    await simulator.simulate_reading_behavior()
                    await simulator.human_like_scroll('down')
                    await simulator.random_pause(2, 4)
                    
                    logger.info(f"窗口 {window_id} 行为模拟完成")
                    
                except Exception as e:
                    logger.error(f"窗口 {window_id} 模拟失败: {e}")
            
            # 并行执行所有窗口的模拟
            tasks = []
            for i, (page, simulator, url) in enumerate(zip(pages, simulators, urls)):
                task = simulate_window(page, simulator, url, i+1)
                tasks.append(task)
            
            logger.info("开始并行执行多窗口人工行为模拟...")
            await asyncio.gather(*tasks)
            
            logger.info("多窗口演示完成，保持页面打开5秒钟...")
            await asyncio.sleep(5)
            
            await browser.close()
            
    except Exception as e:
        logger.error(f"多窗口演示过程中发生错误: {e}")
        raise

if __name__ == "__main__":
    print("选择演示模式:")
    print("1. 单窗口Twitter类似行为演示")
    print("2. 多窗口并行行为演示")
    
    choice = input("请输入选择 (1 或 2): ").strip()
    
    if choice == "1":
        asyncio.run(demo_twitter_like_behavior())
    elif choice == "2":
        asyncio.run(demo_multi_window_simulation())
    else:
        print("无效选择，运行默认演示")
        asyncio.run(demo_twitter_like_behavior())