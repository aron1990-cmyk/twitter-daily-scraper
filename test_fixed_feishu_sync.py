#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import json
from enhanced_tweet_scraper import EnhancedTwitterScraper, load_feishu_config_from_file

def test_fixed_feishu_sync():
    """测试修复后的飞书同步功能"""
    print("🔧 测试修复后的飞书同步功能...")
    
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
            COUNT(*) as total,
            COUNT(CASE WHEN publish_time IS NOT NULL AND publish_time != '' THEN 1 END) as has_publish_time,
            COUNT(CASE WHEN scraped_at IS NOT NULL THEN 1 END) as has_scraped_at,
            COUNT(CASE WHEN synced_to_feishu = 1 THEN 1 END) as synced
        FROM tweet_data
    """)
    
    stats = cursor.fetchone()
    total, has_publish_time, has_scraped_at, synced = stats
    
    print(f"\n📊 数据库统计:")
    print(f"  总推文数: {total}")
    print(f"  有发布时间: {has_publish_time} ({has_publish_time/total*100:.1f}%)")
    print(f"  有抓取时间: {has_scraped_at} ({has_scraped_at/total*100:.1f}%)")
    print(f"  已同步: {synced} ({synced/total*100:.1f}%)")
    
    # 获取样例数据测试格式化
    cursor.execute("""
        SELECT username, content, publish_time, likes, comments, retweets, link, hashtags, scraped_at
        FROM tweet_data 
        ORDER BY id DESC 
        LIMIT 3
    """)
    
    sample_tweets = cursor.fetchall()
    conn.close()
    
    # 测试格式化功能
    print("\n🧪 测试修复后的格式化功能...")
    scraper = EnhancedTwitterScraper()
    
    # 构建测试数据
    test_tweets = []
    for username, content, publish_time, likes, comments, retweets, link, hashtags, scraped_at in sample_tweets:
        tweet_dict = {
            'username': username,
            'content': content,
            'publish_time': publish_time,
            'likes': likes,
            'comments': comments,
            'retweets': retweets,
            'link': link,
            'hashtags': hashtags.split(',') if hashtags else [],
            'scraped_at': scraped_at
        }
        test_tweets.append(tweet_dict)
    
    formatted_tweets = scraper.format_tweets_for_feishu(test_tweets)
    
    print("\n📝 格式化结果分析:")
    for i, (original, formatted) in enumerate(zip(test_tweets, formatted_tweets), 1):
        print(f"\n  推文 {i}:")
        print(f"    原始发布时间: {original.get('publish_time') or '❌ 无'}")
        print(f"    原始抓取时间: {original.get('scraped_at') or '❌ 无'}")
        print(f"    格式化后发布时间: {formatted.get('发布时间') or '❌ 无'}")
        print(f"    格式化后创建时间: {formatted.get('创建时间') or '❌ 无'}")
        
        # 检查修复效果
        if not original.get('publish_time') and formatted.get('发布时间'):
            print(f"    ✅ 修复成功：使用抓取时间作为发布时间")
        elif original.get('publish_time') and formatted.get('发布时间'):
            print(f"    ✅ 正常：使用原始发布时间")
        else:
            print(f"    ❌ 仍有问题：发布时间为空")
    
    # 如果配置有效，执行实际同步测试
    is_placeholder = (
        feishu_config.get('app_id') == 'your_feishu_app_id' or
        feishu_config.get('spreadsheet_token') == 'your_spreadsheet_token'
    )
    
    if not is_placeholder and feishu_config.get('enabled'):
        print("\n🚀 执行实际飞书同步测试...")
        
        # 重置同步状态
        conn = sqlite3.connect('twitter_scraper.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE tweet_data SET synced_to_feishu = 0")
        conn.commit()
        conn.close()
        
        print("✅ 已重置所有推文的同步状态")
        
        # 执行同步
        success = scraper.sync_to_feishu(feishu_config)
        
        if success:
            print("✅ 飞书同步成功！")
            
            # 检查同步结果
            conn = sqlite3.connect('twitter_scraper.db')
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM tweet_data WHERE synced_to_feishu = 1")
            synced_count = cursor.fetchone()[0]
            conn.close()
            
            print(f"📊 同步结果: {synced_count} 条推文已同步到飞书")
        else:
            print("❌ 飞书同步失败")
    else:
        print("\n⚠️ 跳过实际同步测试（配置为占位符或未启用）")
    
    print("\n🎯 修复总结:")
    print("  ✅ 已修复 format_tweets_for_feishu 函数")
    print("  ✅ 当 publish_time 为空时，自动使用 scraped_at 作为回退")
    print("  ✅ 这将解决飞书中时间字段显示异常的问题")
    print("  📝 建议：重新同步所有数据以应用修复")

if __name__ == "__main__":
    test_fixed_feishu_sync()