#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
人工行为模拟器简单测试脚本
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

async def test_human_behavior():
    """
    测试人工行为模拟器功能
    """
    try:
        # 启动新浏览器
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            # 初始化人工行为模拟器
            behavior_simulator = HumanBehaviorSimulator(page)
            logger.info("人工行为模拟器初始化完成")
            
            # 导航到一个简单的测试页面
            test_url = "https://example.com"
            logger.info(f"导航到测试页面: {test_url}")
            await page.goto(test_url, wait_until='networkidle')
            
            # 测试各种人工行为模拟功能
            logger.info("开始测试人工行为模拟功能...")
            
            # 1. 测试随机暂停
            logger.info("测试随机暂停功能")
            await behavior_simulator.random_pause(1.0, 2.0)
            
            # 2. 测试鼠标移动
            logger.info("测试随机鼠标移动")
            await behavior_simulator.simulate_mouse_movement()
            
            # 3. 测试阅读行为
            logger.info("测试阅读行为模拟")
            await behavior_simulator.simulate_reading_behavior()
            
            # 4. 测试页面探索
            logger.info("测试页面探索行为")
            await behavior_simulator.simulate_page_exploration()
            
            # 5. 测试人工滚动
            logger.info("测试人工滚动行为")
            await behavior_simulator.human_like_scroll(direction='down', distance=300)
            
            logger.info("所有人工行为模拟测试完成！")
            
            # 保持页面打开一段时间以便观察
            logger.info("测试完成，保持页面打开3秒钟...")
            await asyncio.sleep(3)
            
            await browser.close()
            
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_human_behavior())