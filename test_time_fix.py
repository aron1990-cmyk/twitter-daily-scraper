#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import json
from datetime import datetime
from enhanced_tweet_scraper import EnhancedTwitterScraper

def test_time_field_fix():
    """测试时间字段修复"""
    print("🧪 测试时间字段修复...")
    
    # 创建测试推文数据（模拟抓取器返回的格式）
    test_tweets = [
        {
            'username': 'testuser1',
            'content': '这是一条测试推文1',
            'publish_time': '2024-01-01T12:00:00Z',  # 使用publish_time字段
            'link': 'https://x.com/testuser1/status/123',
            'likes': 10,
            'comments': 2,
            'retweets': 1,
            'hashtags': ['test'],
            'content_type': '纯文本'
        },
        {
            'username': 'testuser2', 
            'content': '这是一条测试推文2',
            'timestamp': '2024-01-02T12:00:00Z',  # 使用timestamp字段（旧格式）
            'link': 'https://x.com/testuser2/status/124',
            'likes': 20,
            'comments': 3,
            'retweets': 2,
            'hashtags': ['test2'],
            'content_type': '纯文本'
        }
    ]
    
    # 创建抓取器实例
    scraper = EnhancedTwitterScraper()
    
    # 保存测试数据
    saved_count = scraper.save_tweets_to_database(test_tweets)
    print(f"✅ 保存了 {saved_count} 条测试推文")
    
    # 检查数据库中的时间字段
    conn = sqlite3.connect('twitter_scraper.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT username, content, publish_time, scraped_at 
        FROM tweet_data 
        WHERE username IN ('testuser1', 'testuser2')
        ORDER BY id DESC
        LIMIT 2
    """)
    
    results = cursor.fetchall()
    
    print("\n📊 数据库中的时间字段检查:")
    for username, content, publish_time, scraped_at in results:
        print(f"用户: {username}")
        print(f"内容: {content[:30]}...")
        print(f"发布时间: {publish_time}")
        print(f"抓取时间: {scraped_at}")
        print("-" * 40)
    
    conn.close()
    
    # 验证修复效果
    if results:
        has_publish_time = any(row[2] for row in results)  # 检查是否有非空的publish_time
        if has_publish_time:
            print("✅ 时间字段修复成功！现在可以正确保存发布时间了")
        else:
            print("❌ 时间字段仍然为空，需要进一步检查")
    else:
        print("❌ 没有找到测试数据")

if __name__ == '__main__':
    test_time_field_fix()