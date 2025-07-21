#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修改后的滚动策略
"""

import asyncio
import logging
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from twitter_parser import TwitterParser
from ads_browser_launcher import AdsPowerLauncher
from config import ADS_POWER_CONFIG

# 设置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_scroll.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

async def test_scroll_strategy():
    """测试滚动策略"""
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
        parser = TwitterParser(debug_port=debug_port)
        await parser.initialize()
        logger.info("✅ TwitterParser初始化完成")
        
        # 测试抓取推文
        test_username = "elonmusk"  # 使用一个活跃的账户
        target_tweets = 50  # 降低目标数量以便快速测试
        
        logger.info(f"🎯 开始测试抓取 @{test_username} 的 {target_tweets} 条推文...")
        
        # 导航到用户页面
        try:
            await parser.navigate_to_profile(test_username)
            logger.info(f"✅ 成功导航到 @{test_username} 的页面")
        except Exception as e:
            logger.error(f"❌ 无法导航到 @{test_username} 的页面: {e}")
            return
        
        # 开始滚动加载推文
        logger.info(f"📜 开始滚动加载推文，目标: {target_tweets} 条")
        tweets = await parser.scroll_and_load_tweets(
            target_tweets=target_tweets,
            max_scroll_time=300  # 5分钟超时
        )
        
        logger.info(f"🎉 抓取完成！获得 {len(tweets)} 条推文")
        
        # 显示前几条推文的基本信息
        for i, tweet in enumerate(tweets[:5], 1):
            logger.info(f"推文 {i}: {tweet.get('text', '')[:100]}...")
            
        # 分析结果
        if len(tweets) >= target_tweets * 0.8:  # 达到目标的80%
            logger.info("✅ 滚动策略测试成功！")
        else:
            logger.warning(f"⚠️ 滚动策略可能需要进一步优化，只获得了 {len(tweets)}/{target_tweets} 条推文")
            
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
    finally:
        # 清理资源
        if parser:
            try:
                await parser.close()
                logger.info("✅ TwitterParser已关闭")
            except Exception as e:
                logger.error(f"关闭TwitterParser时出错: {e}")
                
        if launcher:
            try:
                launcher.stop_browser()
                logger.info("✅ 浏览器已关闭")
            except Exception as e:
                logger.error(f"关闭浏览器时出错: {e}")

if __name__ == "__main__":
    asyncio.run(test_scroll_strategy())