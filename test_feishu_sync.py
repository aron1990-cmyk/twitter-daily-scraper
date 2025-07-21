#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from enhanced_tweet_scraper import EnhancedTwitterScraper, load_feishu_config_from_database, load_feishu_config_from_file
from cloud_sync import CloudSyncManager
import sqlite3

def load_feishu_config():
    """加载飞书配置（优先从数据库，回退到文件）"""
    try:
        # 首先尝试从数据库加载
        config = load_feishu_config_from_database()
        if config and config.get('enabled'):
            print("✅ 从数据库加载飞书配置成功")
            return config
    except Exception as e:
        print(f"从数据库加载配置失败: {e}")
    
    try:
        # 回退到文件加载
        config = load_feishu_config_from_file()
        if config and config.get('enabled'):
            print("✅ 从文件加载飞书配置成功")
            return config
        elif config:
            print("⚠️ 飞书配置已加载但未启用")
            return config
    except Exception as e:
        print(f"从文件加载配置失败: {e}")
    
    print("❌ 无法加载飞书配置")
    return None

def test_feishu_sync():
    """测试飞书同步功能"""
    print("🧪 测试飞书同步功能...")
    
    # 加载飞书配置
    feishu_config = load_feishu_config()
    if not feishu_config:
        print("❌ 无法加载飞书配置")
        return
    
    if not feishu_config.get('enabled'):
        print("❌ 飞书同步未启用")
        print("💡 提示：请在feishu_config.json中设置正确的配置并启用同步")
        return
        
    print(f"✅ 飞书配置加载成功，表格ID: {feishu_config.get('spreadsheet_token', '')[:10]}...")
    
    # 创建抓取器实例
    scraper = EnhancedTwitterScraper()
    
    # 检查数据库中的推文状态
    conn = sqlite3.connect('twitter_scraper.db')
    cursor = conn.cursor()
    
    # 统计推文数据
    cursor.execute("SELECT COUNT(*) FROM tweet_data")
    total_tweets = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM tweet_data WHERE synced_to_feishu = 1")
    synced_tweets = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM tweet_data WHERE publish_time IS NOT NULL AND publish_time != ''")
    tweets_with_time = cursor.fetchone()[0]
    
    print(f"\n📊 数据库状态:")
    print(f"总推文数: {total_tweets}")
    print(f"已同步推文: {synced_tweets}")
    print(f"有时间的推文: {tweets_with_time}")
    print(f"未同步推文: {total_tweets - synced_tweets}")
    
    # 重置同步状态，重新同步所有推文
    print("\n🔄 重置同步状态，准备重新同步...")
    cursor.execute("UPDATE tweet_data SET synced_to_feishu = 0")
    conn.commit()
    conn.close()
    
    # 执行同步
    print("\n🚀 开始同步到飞书...")
    success = scraper.sync_to_feishu(feishu_config)
    
    if success:
        print("✅ 飞书同步成功！")
        
        # 再次检查同步状态
        conn = sqlite3.connect('twitter_scraper.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tweet_data WHERE synced_to_feishu = 1")
        new_synced_count = cursor.fetchone()[0]
        conn.close()
        
        print(f"📈 同步后状态: {new_synced_count}/{total_tweets} 条推文已同步")
        
        # 显示一些样例数据
        print("\n📝 同步的推文样例:")
        unsync_tweets = scraper.get_unsync_tweets()
        if not unsync_tweets:  # 如果没有未同步的，说明都同步了
            conn = sqlite3.connect('twitter_scraper.db')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT username, content, publish_time, likes
                FROM tweet_data 
                ORDER BY id DESC 
                LIMIT 3
            """)
            results = cursor.fetchall()
            conn.close()
            
            for i, (username, content, publish_time, likes) in enumerate(results, 1):
                print(f"  {i}. {username}: {content[:50]}...")
                print(f"     时间: {publish_time or '无'}, 点赞: {likes}")
        
    else:
        print("❌ 飞书同步失败")

if __name__ == '__main__':
    test_feishu_sync()