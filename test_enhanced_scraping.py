
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的推文抓取功能
"""

import asyncio
import logging
from twitter_parser import TwitterParser

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_enhanced_scraping():
    """测试增强的推文抓取"""
    parser = None
    try:
        logger.info("开始测试增强推文抓取...")
        
        # 创建解析器
        parser = TwitterParser()
        await parser.initialize(debug_port="ws://localhost:9222")
        
        # 测试用户推文抓取
        test_username = "socialmedia2day"
        target_tweets = 50
        
        logger.info(f"测试抓取用户 @{test_username} 的 {target_tweets} 条推文")
        
        tweets = await parser.scrape_user_tweets(test_username, target_tweets)
        
        logger.info(f"抓取结果: 目标 {target_tweets} 条，实际获得 {len(tweets)} 条")
        
        if len(tweets) < target_tweets:
            shortage = target_tweets - len(tweets)
            logger.warning(f"仍然存在数量不足问题，缺少 {shortage} 条推文")
        else:
            logger.info("抓取数量达到目标！")
        
        # 分析推文质量
        if hasattr(parser, 'detect_tweet_quality'):
            quality_stats = {'high': 0, 'medium': 0, 'low': 0, 'unknown': 0}
            for tweet in tweets:
                tweet = parser.detect_tweet_quality(tweet)
                quality_level = tweet.get('quality_level', 'unknown')
                quality_stats[quality_level] += 1
            
            logger.info(f"推文质量分布: {quality_stats}")
        
        # 显示前5条推文的详细信息
        logger.info("前5条推文详情:")
        for i, tweet in enumerate(tweets[:5], 1):
            logger.info(f"推文 {i}:")
            logger.info(f"  用户: @{tweet.get('username', 'unknown')}")
            logger.info(f"  内容: {tweet.get('content', 'No content')[:100]}...")
            logger.info(f"  链接: {tweet.get('link', 'No link')}")
            logger.info(f"  互动: 👍{tweet.get('likes', 0)} 💬{tweet.get('comments', 0)} 🔄{tweet.get('retweets', 0)}")
            if 'quality_score' in tweet:
                logger.info(f"  质量: {tweet['quality_level']} ({tweet['quality_score']}/100)")
            logger.info("")
        
        return len(tweets)
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        return 0
    finally:
        if parser:
            await parser.close()

if __name__ == "__main__":
    result = asyncio.run(test_enhanced_scraping())
    print(f"\n测试完成，共抓取 {result} 条推文")
