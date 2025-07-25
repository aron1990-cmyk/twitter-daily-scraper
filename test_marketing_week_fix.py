#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试MarketingWeekEd推文抓取修复效果
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

async def test_marketing_week_scraping():
    """
    测试MarketingWeekEd的推文抓取
    """
    adspower_manager = None
    parser = None
    
    try:
        logger.info("开始测试MarketingWeekEd推文抓取修复效果")
        
        # 初始化AdsPower管理器
        adspower_manager = AdsPowerLauncher()
        
        # 启动浏览器
        user_id = "k11p9ypc"  # 使用配置的用户ID
        browser_info = adspower_manager.start_browser(user_id)
        
        if not browser_info:
            logger.error("无法启动浏览器")
            return False
            
        logger.info(f"浏览器启动成功: {browser_info}")
        
        # 初始化Twitter解析器
        parser = TwitterParser(browser_info['ws']['puppeteer'])
        
        await parser.initialize()
        logger.info("Twitter解析器初始化完成")
        
        # 测试抓取MarketingWeekEd的推文
        target_username = "MarketingWeekEd"
        target_count = 100
        
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
        
        # 显示前5条推文的摘要
        logger.info("\n前5条推文摘要:")
        for i, tweet in enumerate(tweets[:5], 1):
            content_preview = tweet.get('content', '')[:50] + '...' if len(tweet.get('content', '')) > 50 else tweet.get('content', '')
            logger.info(f"{i}. @{tweet.get('username', 'unknown')}: {content_preview}")
        
        # 检查是否达到目标
        if len(tweets) >= target_count * 0.9:  # 90%以上认为成功
            logger.info("✅ 测试成功！抓取数量达到预期")
            return True
        else:
            logger.warning(f"⚠️ 测试未完全成功，抓取数量不足。缺少 {target_count - len(tweets)} 条推文")
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
        
        if adspower_manager:
            try:
                adspower_manager.stop_browser(user_id)
                logger.info("浏览器已关闭")
            except Exception as e:
                logger.error(f"关闭浏览器失败: {e}")

async def main():
    """
    主函数
    """
    logger.info("=" * 60)
    logger.info("MarketingWeekEd推文抓取修复测试")
    logger.info("=" * 60)
    
    success = await test_marketing_week_scraping()
    
    logger.info("=" * 60)
    if success:
        logger.info("🎉 测试完成：修复成功！")
    else:
        logger.info("❌ 测试完成：仍需进一步优化")
    logger.info("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())