#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的MarketingWeekEd推文抓取测试
"""

import asyncio
import logging
from twitter_parser import TwitterParser
from ads_browser_launcher import AdsPowerLauncher

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_simple_scraping():
    """
    简化的推文抓取测试
    """
    adspower_manager = None
    parser = None
    
    try:
        logger.info("开始简化测试")
        
        # 启动浏览器
        adspower_manager = AdsPowerLauncher()
        user_id = "k11p9ypc"
        browser_info = adspower_manager.start_browser(user_id)
        
        if not browser_info:
            logger.error("无法启动浏览器")
            return False
            
        logger.info("浏览器启动成功")
        
        # 初始化解析器
        parser = TwitterParser(browser_info['ws']['puppeteer'])
        await parser.initialize()
        logger.info("解析器初始化完成")
        
        # 测试抓取50条推文（较小数量便于测试）
        target_username = "MarketingWeekEd"
        target_count = 50
        
        logger.info(f"开始抓取 @{target_username} 的 {target_count} 条推文")
        
        tweets = await parser.scrape_user_tweets(
            username=target_username,
            max_tweets=target_count,
            enable_enhanced=False
        )
        
        logger.info(f"抓取完成！")
        logger.info(f"目标数量: {target_count}")
        logger.info(f"实际抓取: {len(tweets)}")
        logger.info(f"完成率: {len(tweets)/target_count*100:.1f}%")
        
        # 显示前3条推文
        logger.info("\n前3条推文:")
        for i, tweet in enumerate(tweets[:3], 1):
            content = tweet.get('content', '')[:80] + '...' if len(tweet.get('content', '')) > 80 else tweet.get('content', '')
            logger.info(f"{i}. @{tweet.get('username', 'unknown')}: {content}")
        
        # 检查成功率
        success_rate = len(tweets) / target_count
        if success_rate >= 0.8:  # 80%以上认为成功
            logger.info("✅ 测试成功！")
            return True
        else:
            logger.warning(f"⚠️ 测试部分成功，成功率: {success_rate*100:.1f}%")
            return False
            
    except Exception as e:
        logger.error(f"测试失败: {e}")
        return False
        
    finally:
        # 清理
        if parser:
            try:
                await parser.close()
            except Exception:
                pass
        
        if adspower_manager:
            try:
                adspower_manager.stop_browser(user_id)
            except Exception:
                pass

async def main():
    logger.info("=" * 50)
    logger.info("MarketingWeekEd抓取修复测试")
    logger.info("=" * 50)
    
    success = await test_simple_scraping()
    
    logger.info("=" * 50)
    if success:
        logger.info("🎉 修复成功！")
    else:
        logger.info("❌ 需要进一步优化")
    logger.info("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())