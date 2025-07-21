#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import json
import logging
from enhanced_tweet_scraper import EnhancedTwitterScraper, load_feishu_config_from_file

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def resync_all_to_feishu():
    """重新同步所有推文到飞书"""
    print("🔄 开始重新同步所有推文到飞书...")
    
    # 加载飞书配置
    feishu_config = load_feishu_config_from_file()
    if not feishu_config:
        print("❌ 无法加载飞书配置")
        return
    
    if not feishu_config.get('enabled'):
        print("❌ 飞书同步未启用，请先在配置中启用")
        return
    
    # 检查是否为占位符配置
    is_placeholder = (
        feishu_config.get('app_id') == 'your_feishu_app_id' or
        feishu_config.get('spreadsheet_token') == 'your_spreadsheet_token'
    )
    
    if is_placeholder:
        print("❌ 检测到占位符配置，请先配置有效的飞书参数")
        return
    
    print(f"✅ 飞书配置加载成功，启用状态: {feishu_config.get('enabled')}")
    
    # 统计数据库状态
    conn = sqlite3.connect('twitter_scraper.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM tweet_data")
    total_count = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT 
            COUNT(CASE WHEN publish_time IS NOT NULL AND publish_time != '' THEN 1 END) as has_publish_time,
            COUNT(CASE WHEN scraped_at IS NOT NULL THEN 1 END) as has_scraped_at
        FROM tweet_data
    """)
    
    stats = cursor.fetchone()
    has_publish_time, has_scraped_at = stats
    
    print(f"\n📊 数据库统计:")
    print(f"  总推文数: {total_count}")
    print(f"  有发布时间: {has_publish_time} ({has_publish_time/total_count*100:.1f}%)")
    print(f"  有抓取时间: {has_scraped_at} ({has_scraped_at/total_count*100:.1f}%)")
    
    # 重置所有推文的同步状态
    cursor.execute("UPDATE tweet_data SET synced_to_feishu = 0")
    conn.commit()
    conn.close()
    
    print("✅ 已重置所有推文的同步状态")
    
    # 初始化抓取器并执行同步
    scraper = EnhancedTwitterScraper()
    
    print("\n🚀 开始同步到飞书...")
    success = scraper.sync_to_feishu(feishu_config)
    
    if success:
        # 检查同步结果
        conn = sqlite3.connect('twitter_scraper.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tweet_data WHERE synced_to_feishu = 1")
        synced_count = cursor.fetchone()[0]
        conn.close()
        
        print(f"\n✅ 同步成功! {synced_count}/{total_count} 条推文已同步到飞书")
        print(f"  - 其中 {has_publish_time} 条使用原始发布时间")
        print(f"  - {total_count - has_publish_time} 条使用抓取时间作为发布时间")
        
        print("\n🎯 修复效果:")
        print("  ✅ 所有推文现在在飞书中都有有效的时间字段")
        print("  ✅ 飞书表格中的时间显示应该已恢复正常")
    else:
        print("\n❌ 同步失败，请检查飞书配置和网络连接")

if __name__ == "__main__":
    resync_all_to_feishu()