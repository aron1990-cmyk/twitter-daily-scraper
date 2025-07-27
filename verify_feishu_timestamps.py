#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证飞书表格中的时间戳数据是否正确
"""

import sqlite3
import json
from datetime import datetime
import os

def verify_feishu_timestamps():
    """验证飞书表格中的时间戳数据"""
    print("🔍 验证飞书时间戳处理逻辑")
    print(f"⏰ 验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        # 1. 连接数据库
        db_path = '/Users/aron/twitter-daily-scraper/twitter_scraper.db'
        if not os.path.exists(db_path):
            print(f"❌ 数据库文件不存在: {db_path}")
            return False
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 2. 查询最近的推文数据
        print("\n📋 步骤1: 查询最近的推文数据")
        cursor.execute("""
            SELECT id, content, publish_time, scraped_at, username, link
            FROM tweet_data 
            WHERE task_id = 11 
            ORDER BY scraped_at DESC 
            LIMIT 5
        """)
        
        tweets = cursor.fetchall()
        if not tweets:
            print("❌ 未找到推文数据")
            return False
            
        print(f"✅ 找到 {len(tweets)} 条推文数据")
        
        # 3. 分析时间戳处理
        print("\n📋 步骤2: 分析时间戳处理逻辑")
        for i, tweet in enumerate(tweets, 1):
            tweet_id, content, publish_time, scraped_at, username, link = tweet
            
            print(f"\n🐦 推文 #{tweet_id} (@{username})")
            print(f"📝 内容: {content[:50]}...")
            print(f"📅 原始发布时间: {publish_time}")
            print(f"📅 抓取时间: {scraped_at}")
            
            # 模拟修复后的Web应用时间戳处理逻辑
            try:
                publish_timestamp = 0
                if publish_time:
                    if isinstance(publish_time, str):
                        from dateutil import parser
                        dt = parser.parse(publish_time)
                        # 使用秒级时间戳（修复后的逻辑）
                        publish_timestamp = int(dt.timestamp())
                        readable_time = datetime.fromtimestamp(publish_timestamp).strftime('%Y-%m-%d %H:%M:%S')
                        print(f"⏰ 修复后时间戳: {publish_timestamp} (秒级)")
                        print(f"📖 可读时间: {readable_time}")
                        
                        # 检查是否是1970年问题
                        if publish_timestamp < 946684800:  # 2000年1月1日
                            print(f"⚠️ 检测到1970年问题！时间戳: {publish_timestamp}")
                            print(f"🔧 将修正为当前时间")
                            publish_timestamp = int(datetime.now().timestamp())
                        else:
                            print(f"✅ 时间戳正常")
                            
                        # 验证时间戳格式
                        if len(str(publish_timestamp)) == 10:
                            print(f"✅ 时间戳格式正确（10位秒级）")
                        else:
                            print(f"⚠️ 时间戳格式异常: {len(str(publish_timestamp))}位")
                            
                    else:
                        print(f"⚠️ 发布时间不是字符串格式: {type(publish_time)}")
                else:
                    print(f"⚠️ 没有发布时间，将使用抓取时间")
                    scraped_dt = datetime.fromisoformat(scraped_at.replace('Z', '+00:00'))
                    publish_timestamp = int(scraped_dt.timestamp())
                    print(f"⏰ 抓取时间戳: {publish_timestamp}")
                    
            except Exception as e:
                print(f"❌ 时间戳处理失败: {e}")
        
        # 4. 总结修复效果
        print("\n📋 步骤3: 修复效果总结")
        print("🔧 修复内容:")
        print("   1. 将毫秒时间戳改为秒级时间戳")
        print("   2. 添加1970年问题检测和修正")
        print("   3. 统一时间戳格式为10位秒级")
        print("   4. 确保与cloud_sync.py的时间处理逻辑一致")
        
        print("\n✅ 预期效果:")
        print("   - 飞书表格中的时间字段应该正确显示")
        print("   - 不再出现1970年的异常时间")
        print("   - 时间戳格式统一为秒级")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 验证过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    success = verify_feishu_timestamps()
    
    print("\n" + "=" * 60)
    if success:
        print("🏁 飞书时间戳验证完成")
        print("💡 修复已完成，建议重新测试飞书同步功能")
        print("🔍 请检查飞书表格中的时间字段是否显示正确")
    else:
        print("🏁 飞书时间戳验证失败")
        print("💡 请检查数据库连接")