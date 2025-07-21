#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的批量抓取脚本
专注于完成剩余博主的抓取任务
"""

import asyncio
import logging
from datetime import datetime
from twitter_parser import TwitterParser
from storage_manager import StorageManager
from ads_browser_launcher import AdsPowerLauncher
from config import ADS_POWER_CONFIG

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 博主列表（排除已完成的neilpatel）
BLOGGERS = [
    "TaoTaoOps",
    "Consumentenbond", 
    "MinPres",
    "elonmusk",
    "tesla_semi",
    "Rijkswaterstaat",
    "nishuang",
    "abskoop",
    "yiguxia"
]

MAX_TWEETS_PER_BLOGGER = 100

async def scrape_blogger_simple(username: str, parser: TwitterParser, storage: StorageManager):
    """
    简化的博主抓取函数
    """
    try:
        logger.info(f"🚀 开始抓取博主 @{username} 的推文...")
        
        # 抓取推文
        tweets = await parser.scrape_user_tweets(
            username=username,
            max_tweets=MAX_TWEETS_PER_BLOGGER,
            enable_enhanced=False  # 关闭增强模式以提高稳定性
        )
        
        if tweets:
            # 保存推文数据
            await storage.save_user_tweets(username, tweets)
            logger.info(f"✅ @{username}: 成功抓取并保存 {len(tweets)} 条推文")
            return len(tweets)
        else:
            logger.warning(f"⚠️ @{username}: 未抓取到推文")
            return 0
            
    except Exception as e:
        logger.error(f"❌ @{username}: 抓取失败 - {e}")
        return 0

async def main():
    """
    主函数
    """
    logger.info(f"🎯 开始批量抓取{len(BLOGGERS)}个博主的推文...")
    
    twitter_parser = None
    storage = None
    
    try:
        # 启动AdsPower浏览器
        logger.info("🚀 启动AdsPower浏览器...")
        ads_config = {
            'local_api_url': ADS_POWER_CONFIG['api_url'],
            'user_id': ADS_POWER_CONFIG['user_ids'][0] if ADS_POWER_CONFIG['user_ids'] else '',
            'group_id': ''
        }
        
        ads_launcher = AdsPowerLauncher(ads_config)
        browser_info = ads_launcher.start_browser()
        
        if not browser_info:
            raise Exception("AdsPower浏览器启动失败")
            
        debug_port = browser_info.get('debug_port')
        if not debug_port:
            raise Exception("无法获取浏览器调试端口")
            
        logger.info(f"✅ AdsPower浏览器启动成功，调试端口: {debug_port}")
        
        # 初始化Twitter解析器
        twitter_parser = TwitterParser()
        await twitter_parser.initialize(debug_port=f"http://localhost:{debug_port}")
        logger.info("✅ Twitter解析器初始化成功")
        
        # 初始化存储管理器
        storage = StorageManager()
        logger.info("✅ 存储管理器初始化成功")
        
        # 统计信息
        total_tweets = 0
        successful_count = 0
        
        # 逐个抓取博主
        for i, username in enumerate(BLOGGERS, 1):
            logger.info(f"\n📊 进度: {i}/{len(BLOGGERS)} - 当前博主: @{username}")
            
            tweet_count = await scrape_blogger_simple(username, twitter_parser, storage)
            
            if tweet_count > 0:
                successful_count += 1
                total_tweets += tweet_count
            
            # 休息一下再继续
            if i < len(BLOGGERS):
                logger.info("⏱️ 休息5秒后继续下一个博主...")
                await asyncio.sleep(5)
        
        # 输出最终统计
        logger.info(f"\n🎉 批量抓取完成!")
        logger.info(f"📈 成功抓取: {successful_count}/{len(BLOGGERS)} 个博主")
        logger.info(f"📝 总推文数: {total_tweets} 条")
        logger.info(f"📊 平均每个博主: {total_tweets/successful_count:.1f} 条推文" if successful_count > 0 else "📊 平均每个博主: 0 条推文")
        
    except Exception as e:
        logger.error(f"❌ 批量抓取失败: {e}")
        
    finally:
        # 清理资源
        if twitter_parser:
            await twitter_parser.close()
            logger.info("✅ Twitter解析器已关闭")
            
        # 停止AdsPower浏览器
        try:
            if 'ads_launcher' in locals():
                ads_launcher.stop_browser()
                logger.info("✅ AdsPower浏览器已停止")
        except Exception as e:
            logger.warning(f"⚠️ 停止AdsPower浏览器时出错: {e}")

if __name__ == "__main__":
    asyncio.run(main())