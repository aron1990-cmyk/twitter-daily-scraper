#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的数据提取功能
"""

import asyncio
import logging
from datetime import datetime, timezone
from data_extractor import DataExtractor
from browser_manager import BrowserManager
from config import BROWSER_CONFIG, FILTER_CONFIG

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_data_extraction():
    """测试数据提取功能"""
    try:
        logger.info("开始测试数据提取功能")
        
        # 创建配置对象
        class TestConfig:
            def __init__(self):
                self.max_tweets = 5
                self.headless = False
                self.wait_time = 2
                self.timeout = BROWSER_CONFIG['timeout']
                self.scroll_pause_time = BROWSER_CONFIG['scroll_pause_time']
                self.min_likes = FILTER_CONFIG['min_likes']
                self.min_comments = FILTER_CONFIG['min_comments']
                self.min_retweets = FILTER_CONFIG['min_retweets']
        
        config = TestConfig()
        
        # 初始化浏览器管理器
        browser_manager = BrowserManager(max_instances=1, headless=config.headless)
        await browser_manager.initialize()
        
        # 获取浏览器实例
        browser_instance = await browser_manager.get_available_instance()
        if not browser_instance:
            raise Exception("无法获取浏览器实例")
        
        # 创建数据提取器
        data_extractor = DataExtractor()
        
        # 测试账号
        test_username = "elonmusk"
        
        logger.info(f"开始测试账号: @{test_username}")
        
        # 导航到用户页面
        page = browser_instance.page
        
        # 设置更短的超时时间并使用更宽松的等待条件
        try:
            await page.goto(f"https://twitter.com/{test_username}", 
                          wait_until="domcontentloaded", 
                          timeout=30000)  # 30秒超时
            logger.info(f"成功导航到 @{test_username} 页面")
            await asyncio.sleep(5)  # 等待页面完全加载
        except Exception as e:
            logger.warning(f"导航到Twitter页面失败: {e}")
            # 尝试使用x.com域名
            try:
                await page.goto(f"https://x.com/{test_username}", 
                              wait_until="domcontentloaded", 
                              timeout=30000)
                logger.info(f"成功导航到 @{test_username} 页面 (使用x.com)")
                await asyncio.sleep(5)
            except Exception as e2:
                logger.error(f"导航失败，跳过测试: {e2}")
                return
        
        # 提取推文数据
        logger.info("开始提取推文数据...")
        tweets = await data_extractor.extract_tweets_from_page(browser_instance, max_tweets=3)
        
        # 显示结果
        logger.info(f"成功提取 {len(tweets)} 条推文")
        
        for i, tweet in enumerate(tweets, 1):
            logger.info(f"\n=== 推文 {i} ===")
            logger.info(f"用户名: {tweet.username}")
            logger.info(f"内容: {tweet.content[:100]}...")
            logger.info(f"发布时间: {tweet.created_at}")
            logger.info(f"点赞数: {tweet.likes_count}")
            logger.info(f"转发数: {tweet.retweets_count}")
            logger.info(f"回复数: {tweet.replies_count}")
            logger.info(f"引用数: {tweet.quotes_count}")
            logger.info(f"浏览数: {tweet.views_count}")
            logger.info(f"图片数量: {len(tweet.media_urls)}")
            logger.info(f"视频数量: {len([url for url, media_type in zip(tweet.media_urls, tweet.media_types) if 'video' in media_type])}")
            
            if tweet.media_urls:
                logger.info(f"媒体URL: {tweet.media_urls[:2]}...")  # 只显示前2个
            if tweet.urls:
                logger.info(f"链接URL: {tweet.urls[:2]}...")  # 只显示前2个
        
        # 测试用户资料提取
        logger.info("\n=== 测试用户资料提取 ===")
        user_profile = await data_extractor.extract_user_profile(browser_instance)
        if user_profile:
            logger.info(f"用户名: {user_profile.username}")
            logger.info(f"显示名: {user_profile.display_name}")
            logger.info(f"简介: {user_profile.bio[:100]}...")
            logger.info(f"关注数: {user_profile.following_count}")
            logger.info(f"粉丝数: {user_profile.followers_count}")
            logger.info(f"推文数: {user_profile.tweets_count}")
        
        logger.info("\n测试完成！")
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理资源
        if 'browser_manager' in locals():
            await browser_manager.close_all()

if __name__ == "__main__":
    asyncio.run(test_data_extraction())