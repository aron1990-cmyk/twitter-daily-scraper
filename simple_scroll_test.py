#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单滚动策略测试脚本
直接在当前页面测试滚动功能，无需导航
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ads_browser_launcher import AdsPowerLauncher
from twitter_parser import TwitterParser

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('simple_scroll_test.log')
    ]
)
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

async def simple_scroll_test():
    """简单滚动测试"""
    launcher = None
    parser = None
    
    try:
        # 初始化AdsPower启动器
        logger.info("🚀 初始化AdsPower启动器...")
        launcher = AdsPowerLauncher(ADS_POWER_CONFIG)
        
        # 启动浏览器
        logger.info("🌐 启动浏览器...")
        browser_info = launcher.start_browser()
        
        # 等待浏览器就绪
        launcher.wait_for_browser_ready()
        debug_port = launcher.get_debug_port()
        logger.info(f"✅ 浏览器启动成功，调试端口: {debug_port}")
        
        # 初始化TwitterParser
        logger.info("🔧 初始化TwitterParser...")
        parser = TwitterParser(debug_port)
        await parser.initialize(debug_port)
        logger.info("✅ TwitterParser初始化完成")
        
        # 检查当前页面
        current_url = parser.page.url
        logger.info(f"📍 当前页面: {current_url}")
        
        # 如果不在Twitter页面，导航到Twitter首页
        if 'x.com' not in current_url and 'twitter.com' not in current_url:
            logger.info("🔄 导航到Twitter首页...")
            await parser.page.goto('https://x.com', wait_until='domcontentloaded')
            await asyncio.sleep(3)
            logger.info("✅ 已导航到Twitter首页")
        
        # 获取初始推文数量
        initial_tweets = await parser.page.query_selector_all('[data-testid="tweet"]')
        logger.info(f"📊 初始推文数量: {len(initial_tweets)}")
        
        # 测试滚动策略
        logger.info("🎯 开始测试滚动策略...")
        start_time = datetime.now()
        
        try:
            await parser.scroll_and_load_tweets(max_tweets=30)
        except Exception as e:
            logger.error(f"滚动过程中出错: {e}")
        
        # 获取最终推文数量
        final_tweets = await parser.page.query_selector_all('[data-testid="tweet"]')
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"📈 测试结果:")
        logger.info(f"   初始推文数量: {len(initial_tweets)}")
        logger.info(f"   最终推文数量: {len(final_tweets)}")
        logger.info(f"   新增推文数量: {len(final_tweets) - len(initial_tweets)}")
        logger.info(f"   测试耗时: {duration:.2f} 秒")
        
        if len(final_tweets) > len(initial_tweets):
            logger.info("✅ 滚动策略测试成功！成功加载了更多推文")
        else:
            logger.warning("⚠️ 滚动策略可能需要优化，未能加载更多推文")
            
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        
    finally:
        # 清理资源
        if parser:
            try:
                await parser.close()
                logger.info("✅ TwitterParser已关闭")
            except Exception as e:
                logger.warning(f"关闭TwitterParser时出错: {e}")
        
        if launcher:
            try:
                launcher.stop_browser()
                logger.info("✅ 浏览器已关闭")
            except Exception as e:
                logger.warning(f"关闭浏览器时出错: {e}")

if __name__ == "__main__":
    asyncio.run(simple_scroll_test())