#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import json
from enhanced_tweet_scraper import EnhancedTwitterScraper, load_feishu_config_from_file

def test_feishu_no_publish_time():
    """测试移除发布时间字段后的飞书同步功能"""
    print("🔧 测试移除发布时间字段后的飞书同步功能...")
    
    # 加载飞书配置
    feishu_config = load_feishu_config_from_file()
    if not feishu_config:
        print("❌ 无法加载飞书配置")
        return
    
    print(f"✅ 飞书配置加载成功，启用状态: {feishu_config.get('enabled')}")
    
    # 检查数据库状态
    conn = sqlite3.connect('twitter_scraper.db')
    cursor = conn.cursor()
    
    # 统计推文数据
    cursor.execute("""
        SELECT 
            COUNT(*) as total_tweets,
            COUNT(CASE WHEN publish_time IS NOT NULL AND publish_time != '' THEN 1 END) as has_publish_time,
            COUNT(CASE WHEN scraped_at IS NOT NULL THEN 1 END) as has_scraped_at,
            COUNT(CASE WHEN synced_to_feishu = 1 THEN 1 END) as synced_count
        FROM tweet_data
    """)
    
    stats = cursor.fetchone()
    print(f"\n📊 数据库统计:")
    print(f"   总推文数: {stats[0]}")
    print(f"   有发布时间的推文: {stats[1]}")
    print(f"   有抓取时间的推文: {stats[2]}")
    print(f"   已同步到飞书的推文: {stats[3]}")
    
    # 获取一些示例推文进行测试
    cursor.execute("""
        SELECT id, username, content, publish_time, scraped_at, synced_to_feishu
        FROM tweet_data 
        LIMIT 5
    """)
    
    sample_tweets = cursor.fetchall()
    conn.close()
    
    if not sample_tweets:
        print("❌ 数据库中没有推文数据")
        return
    
    # 转换为字典格式
    tweets_data = []
    for tweet in sample_tweets:
        tweet_dict = {
            'id': tweet[0],
            'username': tweet[1],
            'content': tweet[2],
            'publish_time': tweet[3],
            'scraped_at': tweet[4],
            'synced_to_feishu': tweet[5],
            'hashtags': [],
            'content_type': '普通推文',
            'comments': 0,
            'retweets': 0,
            'likes': 0,
            'link': f'https://twitter.com/{tweet[1]}/status/{tweet[0]}'
        }
        tweets_data.append(tweet_dict)
    
    # 测试格式化函数
    scraper = EnhancedTwitterScraper()
    formatted_tweets = scraper.format_tweets_for_feishu(tweets_data)
    
    print(f"\n🧪 测试格式化结果:")
    print(f"   原始推文数: {len(tweets_data)}")
    print(f"   格式化后推文数: {len(formatted_tweets)}")
    
    # 检查格式化后的字段
    if formatted_tweets:
        first_tweet = formatted_tweets[0]
        print(f"\n📋 格式化后的字段:")
        for key in first_tweet.keys():
            print(f"   - {key}")
        
        # 验证是否移除了发布时间字段
        if '发布时间' in first_tweet:
            print("\n❌ 错误：发布时间字段仍然存在！")
            print(f"   发布时间值: {first_tweet['发布时间']}")
        else:
            print("\n✅ 成功：发布时间字段已被移除")
        
        # 显示示例数据
        print(f"\n📝 示例格式化数据:")
        print(json.dumps(first_tweet, ensure_ascii=False, indent=2))
    
    # 检查配置状态
    if feishu_config.get('enabled') and all([
        feishu_config.get('app_id'),
        feishu_config.get('app_secret'),
        feishu_config.get('spreadsheet_token'),
        feishu_config.get('table_id')
    ]):
        print("\n🚀 飞书配置完整，可以进行实际同步测试")
    else:
        print("\n⚠️  检测到占位符配置，无法进行实际同步")
        print("   请在 feishu_config.json 中配置有效的飞书参数")
    
    print("\n✅ 测试完成")

if __name__ == "__main__":
    test_feishu_no_publish_time()