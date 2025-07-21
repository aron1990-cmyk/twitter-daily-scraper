#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试解析方法测试
"""

import asyncio
import logging
from ads_browser_launcher import AdsPowerLauncher
from twitter_parser import TwitterParser
from config import ADS_POWER_CONFIG

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def debug_parse_test():
    """调试解析方法"""
    launcher = None
    parser = None
    
    try:
        # 启动浏览器
        logger.info("🚀 启动浏览器...")
        launcher = AdsPowerLauncher(ADS_POWER_CONFIG)
        browser_info = launcher.start_browser()
        launcher.wait_for_browser_ready()
        debug_port = launcher.get_debug_port()
        logger.info(f"✅ 浏览器启动成功，调试端口: {debug_port}")
        
        # 初始化TwitterParser
        logger.info("🔧 初始化TwitterParser...")
        parser = TwitterParser(debug_port=debug_port)
        await parser.initialize()
        parser.enable_optimizations()  # 启用优化功能
        logger.info("✅ TwitterParser初始化完成")
        
        # 导航到页面
        logger.info("🔍 导航到测试页面...")
        try:
            await parser.navigate_to_profile("elonmusk")
            logger.info("✅ 导航成功")
        except Exception as e:
            logger.error(f"❌ 导航失败: {e}")
            return
        
        # 等待页面加载
        await asyncio.sleep(3)
        
        # 获取推文元素
        logger.info("🔍 查找推文元素...")
        tweet_elements = await parser.page.query_selector_all('[data-testid="tweet"]')
        logger.info(f"找到 {len(tweet_elements)} 个推文元素")
        
        if not tweet_elements:
            logger.error("❌ 未找到推文元素")
            return
        
        # 测试解析第一个推文元素
        logger.info("🔧 开始测试解析第一个推文元素...")
        first_element = tweet_elements[0]
        
        # 调用优化版本的解析方法
        result = await parser.parse_tweet_element_optimized(first_element)
        
        logger.info(f"🔧 解析结果: {result}")
        
        if result:
            logger.info("✅ 解析成功")
        else:
            logger.error("❌ 解析失败")
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理资源
        if parser:
            await parser.close()
        if launcher:
            launcher.stop_browser()
        logger.info("🧹 资源清理完成")

if __name__ == "__main__":
    asyncio.run(debug_parse_test())