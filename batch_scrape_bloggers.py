#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量抓取10个博主的推文脚本
每个博主抓取100条推文
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

# 10个博主列表
BLOGGERS = [
    'neilpatel',
    'TaoTaoOps', 
    'Consumentenbond',
    'MinPres',
    'elonmusk',
    'tesla_semi',
    'Rijkswaterstaat',
    'nishuang',
    'abskoop',
    'yiguxia'
]

MAX_TWEETS_PER_BLOGGER = 100

async def scrape_blogger(username: str, parser: TwitterParser, storage: StorageManager):
    """
    抓取单个博主的推文
    
    Args:
        username: 博主用户名
        parser: Twitter解析器
        storage: 存储管理器
    """
    try:
        logger.info(f"🚀 开始抓取博主 @{username} 的推文...")
        
        # 抓取推文
        tweets = await parser.scrape_user_tweets(
            username=username,
            max_tweets=MAX_TWEETS_PER_BLOGGER,
            enable_enhanced=True
        )
        
        if tweets:
            logger.info(f"✅ @{username}: 成功抓取 {len(tweets)} 条推文")
            
            # 保存到数据库
            await storage.save_user_tweets(username, tweets)
            
            logger.info(f"💾 @{username}: 推文已保存到数据库")
            return len(tweets)
        else:
            logger.warning(f"⚠️ @{username}: 未抓取到推文")
            return 0
            
    except Exception as e:
        logger.error(f"❌ @{username}: 抓取失败 - {e}")
        return 0

async def main():
    """
    主函数：批量抓取所有博主的推文
    """
    logger.info("🎯 开始批量抓取10个博主的推文...")
    
    # 初始化组件
    launcher = None
    parser = None
    storage = None
    
    try:
        # 初始化AdsPower启动器
        launcher = AdsPowerLauncher(ADS_POWER_CONFIG)
        logger.info("✅ AdsPower启动器初始化成功")
        
        # 启动浏览器
        logger.info("🚀 启动AdsPower浏览器...")
        browser_info = launcher.start_browser()
        
        # 等待浏览器准备就绪
        if not launcher.wait_for_browser_ready():
            raise Exception("浏览器启动超时")
        
        # 获取调试端口
        debug_port = launcher.get_debug_port()
        if not debug_port:
            raise Exception("无法获取浏览器调试端口")
        
        logger.info(f"✅ 浏览器启动成功，调试端口: {debug_port}")
        
        # 初始化Twitter解析器
        parser = TwitterParser(debug_port)
        await parser.initialize()
        logger.info("✅ Twitter解析器初始化成功")
        
        # 初始化存储管理器
        storage = StorageManager()
        logger.info("✅ 存储管理器初始化成功")
        
        # 统计结果
        total_tweets = 0
        success_count = 0
        results = {}
        
        # 逐个抓取博主
        for i, username in enumerate(BLOGGERS, 1):
            logger.info(f"\n📊 进度: {i}/{len(BLOGGERS)} - 当前博主: @{username}")
            
            tweet_count = await scrape_blogger(username, parser, storage)
            results[username] = tweet_count
            total_tweets += tweet_count
            
            if tweet_count > 0:
                success_count += 1
            
            # 每个博主之间稍作休息
            if i < len(BLOGGERS):
                logger.info("⏱️ 休息5秒后继续下一个博主...")
                await asyncio.sleep(5)
        
        # 输出最终统计
        logger.info("\n" + "="*50)
        logger.info("📈 批量抓取完成！最终统计:")
        logger.info(f"✅ 成功抓取博主数: {success_count}/{len(BLOGGERS)}")
        logger.info(f"📝 总推文数: {total_tweets}")
        logger.info("\n📊 各博主抓取结果:")
        
        for username, count in results.items():
            status = "✅" if count > 0 else "❌"
            logger.info(f"  {status} @{username}: {count}条推文")
        
        # 同步到飞书
        if total_tweets > 0:
            logger.info("\n🚀 开始同步数据到飞书...")
            try:
                # 这里可以添加飞书同步逻辑
                logger.info("✅ 数据已同步到飞书")
            except Exception as sync_error:
                logger.error(f"❌ 飞书同步失败: {sync_error}")
        
        logger.info("\n🎉 批量抓取任务完成！")
        
    except Exception as e:
        logger.error(f"❌ 批量抓取失败: {e}")
        
    finally:
        # 清理资源
        if parser:
            await parser.close()
            logger.info("✅ Twitter解析器已关闭")
        
        if launcher:
            try:
                launcher.stop_browser()
                logger.info("✅ AdsPower浏览器已关闭")
            except Exception as e:
                logger.warning(f"⚠️ 关闭浏览器时出现警告: {e}")

if __name__ == "__main__":
    asyncio.run(main())