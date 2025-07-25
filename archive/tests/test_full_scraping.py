#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试完整的抓取流程
"""

import asyncio
import json
from refactored_task_manager import RefactoredTaskManager

async def test_full_scraping():
    """测试完整抓取流程"""
    try:
        print("🔧 执行抓取任务...")
        # 直接调用抓取引擎
        from twitter_scraping_engine import TwitterScrapingEngine
        from models import ScrapingConfig
        
        config = ScrapingConfig(
            target_accounts=['elonmusk'],
            target_keywords=[],
            max_tweets_per_target=3,
            max_total_tweets=3,
            min_likes=0,
            min_retweets=0,
            min_comments=0
        )
        
        engine = TwitterScrapingEngine()
        result = await engine.batch_scrape_first_time(config.target_accounts)
        
        print(f"\n✅ 抓取结果: {result}")
        
        # 检查数据库中的最新数据
        print("\n🔧 检查数据库中的最新推文...")
        import sqlite3
        
        # 直接使用sqlite3查询数据库
        conn = sqlite3.connect('twitter_scraper.db')
        cursor = conn.cursor()
        
        # 获取最新的3条推文
        cursor.execute("""
            SELECT username, content, likes, comments, retweets, publish_time, created_at
            FROM tweets 
            ORDER BY created_at DESC 
            LIMIT 3
        """)
        latest_tweets = cursor.fetchall()
        
        print(f"\n📊 数据库中最新的 {len(latest_tweets)} 条推文:")
        for i, tweet in enumerate(latest_tweets, 1):
            username, content, likes, comments, retweets, publish_time, created_at = tweet
            print(f"\n推文 {i}:")
            print(f"  用户名: {username}")
            print(f"  内容: {content[:100]}...")
            print(f"  点赞数: {likes}")
            print(f"  评论数: {comments}")
            print(f"  转发数: {retweets}")
            print(f"  发布时间: {publish_time}")
        
        conn.close()
        
        # 检查是否有统计数据
        has_stats = any(tweet[2] > 0 or tweet[3] > 0 or tweet[4] > 0 for tweet in latest_tweets)
        
        if has_stats:
            print("\n🎉 统计数据提取和存储成功！")
        else:
            print("\n⚠️ 统计数据仍为零，需要进一步调试")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_full_scraping())