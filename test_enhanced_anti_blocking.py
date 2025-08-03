#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试增强的Twitter反封控机制
专门测试0xluffy_eth用户的推文抓取
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.twitter_parser import TwitterParser
from utils.ads_browser_launcher import AdsPowerLauncher
from config.adspower_config import ADSPOWER_CONFIG

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_anti_blocking.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

async def test_enhanced_anti_blocking():
    """
    测试增强的反封控机制
    """
    launcher = None
    parser = None
    
    try:
        logger.info("🚀 开始测试增强的反封控机制")
        
        # 1. 启动AdsPower浏览器
        logger.info("启动AdsPower浏览器...")
        launcher = AdsPowerLauncher()
        
        try:
            browser_info = await launcher.start_browser()
            if not browser_info:
                logger.error("AdsPower浏览器启动失败")
                return False
            
            debug_port = browser_info.get('debug_port')
            if not debug_port:
                logger.error("无法获取浏览器调试端口")
                return False
                
            logger.info(f"AdsPower浏览器启动成功，调试端口: {debug_port}")
            
        except Exception as e:
            logger.warning(f"AdsPower启动失败: {e}，尝试使用默认端口")
            debug_port = "ws://127.0.0.1:9222"
        
        # 2. 连接Twitter解析器
        logger.info("连接Twitter解析器...")
        parser = TwitterParser(debug_port)
        await parser.connect_browser()
        
        # 3. 启用优化功能（包含反封控机制）
        logger.info("启用优化功能和反封控机制...")
        parser.enable_optimizations()
        
        # 4. 导航到Twitter主页
        logger.info("导航到Twitter主页...")
        await parser.navigate_to_twitter()
        
        # 5. 导航到0xluffy_eth用户主页
        target_user = "0xluffy_eth"
        logger.info(f"导航到 @{target_user} 用户主页...")
        await parser.navigate_to_profile(target_user)
        
        # 6. 检查页面状态
        logger.info("检查页面状态...")
        current_url = parser.page.url
        logger.info(f"当前页面URL: {current_url}")
        
        # 检查是否有推文元素
        tweet_elements = await parser.page.query_selector_all('[data-testid="tweet"]')
        logger.info(f"页面推文元素数量: {len(tweet_elements)}")
        
        # 7. 如果没有推文元素，测试反封控机制
        if len(tweet_elements) == 0:
            logger.warning("页面无推文元素，测试反封控机制...")
            
            # 手动触发封控检测
            is_blocked = await parser.detect_twitter_blocking()
            logger.info(f"封控检测结果: {is_blocked}")
            
            # 执行反封控刷新
            logger.info("执行反封控刷新...")
            await parser.anti_blocking_refresh()
            
            # 重新检查推文元素
            await asyncio.sleep(3)
            tweet_elements = await parser.page.query_selector_all('[data-testid="tweet"]')
            logger.info(f"反封控刷新后推文元素数量: {len(tweet_elements)}")
        
        # 8. 尝试抓取推文
        logger.info("开始抓取推文...")
        max_tweets = 5
        
        try:
            tweets = await parser.scrape_tweets(
                max_tweets=max_tweets,
                enable_enhanced=False,
                filter_criteria=None
            )
            
            logger.info(f"✅ 成功抓取推文数量: {len(tweets)}")
            
            # 显示抓取到的推文信息
            for i, tweet in enumerate(tweets, 1):
                logger.info(f"推文 {i}:")
                logger.info(f"  用户: @{tweet.get('username', 'unknown')}")
                logger.info(f"  内容: {tweet.get('content', 'No content')[:100]}...")
                logger.info(f"  链接: {tweet.get('link', 'No link')}")
                logger.info(f"  点赞: {tweet.get('likes', 0)}")
                logger.info(f"  转发: {tweet.get('retweets', 0)}")
                logger.info(f"  评论: {tweet.get('comments', 0)}")
                logger.info("---")
            
            if len(tweets) > 0:
                logger.info("🎉 反封控机制测试成功！成功抓取到推文")
                return True
            else:
                logger.warning("⚠️ 抓取到的推文数量为0，可能仍存在问题")
                return False
                
        except Exception as scrape_error:
            logger.error(f"抓取推文失败: {scrape_error}")
            return False
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        return False
        
    finally:
        # 清理资源
        if parser:
            try:
                await parser.close()
                logger.info("Twitter解析器已关闭")
            except Exception as e:
                logger.error(f"关闭Twitter解析器失败: {e}")
        
        if launcher:
            try:
                await launcher.stop_browser()
                logger.info("AdsPower浏览器已关闭")
            except Exception as e:
                logger.error(f"关闭AdsPower浏览器失败: {e}")

async def main():
    """
    主函数
    """
    logger.info("=" * 60)
    logger.info("Twitter反封控机制增强测试")
    logger.info(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"目标用户: 0xluffy_eth")
    logger.info("=" * 60)
    
    success = await test_enhanced_anti_blocking()
    
    logger.info("=" * 60)
    if success:
        logger.info("✅ 测试结果: 成功")
        logger.info("反封控机制工作正常，可以正常抓取推文")
    else:
        logger.info("❌ 测试结果: 失败")
        logger.info("反封控机制可能需要进一步优化")
    logger.info("=" * 60)
    
    return success

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        logger.info("测试被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"测试执行失败: {e}")
        sys.exit(1)