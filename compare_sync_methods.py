#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对比自动同步和手动同步的数据处理差异
"""

import sys
sys.path.append('.')

from web_app import app, TweetData, db, FEISHU_CONFIG
from cloud_sync import CloudSyncManager
import json
from datetime import datetime

def compare_sync_methods():
    """对比自动同步和手动同步的数据处理方法"""
    with app.app_context():
        print("🔍 对比自动同步和手动同步的数据处理差异")
        print("=" * 60)
        
        # 获取任务19的推文数据
        task_id = 19
        tweets = TweetData.query.filter_by(task_id=task_id).all()
        
        if not tweets:
            print("❌ 没有找到任务19的数据")
            return
            
        print(f"📊 找到 {len(tweets)} 条推文数据")
        tweet = tweets[0]  # 使用第一条数据进行对比
        
        print(f"\n📝 原始数据库数据:")
        print(f"   - ID: {tweet.id}")
        print(f"   - 内容: {tweet.content[:50]}...")
        print(f"   - 作者: {tweet.username}")
        print(f"   - 链接: {tweet.link[:50]}...")
        print(f"   - 话题标签: {tweet.hashtags}")
        print(f"   - 类型标签: {tweet.content_type}")
        print(f"   - 点赞数: {tweet.likes}")
        print(f"   - 转发数: {tweet.retweets}")
        print(f"   - 评论数: {tweet.comments}")
        print(f"   - 发布时间: {tweet.publish_time}")
        print(f"   - 抓取时间: {tweet.scraped_at}")
        
        print(f"\n🔄 方法1: 自动同步数据处理 (_check_auto_sync_feishu)")
        print("-" * 40)
        
        # 模拟自动同步的数据处理逻辑
        try:
            hashtags = json.loads(tweet.hashtags) if tweet.hashtags else []
        except:
            hashtags = []
        
        # 转换发布时间为毫秒时间戳
        publish_timestamp = ''
        if tweet.publish_time:
            try:
                if isinstance(tweet.publish_time, str):
                    dt = datetime.fromisoformat(tweet.publish_time.replace('Z', '+00:00'))
                else:
                    dt = tweet.publish_time
                publish_timestamp = str(int(dt.timestamp() * 1000))
            except:
                publish_timestamp = ''
        
        # 转换创建时间为毫秒时间戳
        created_timestamp = ''
        if tweet.scraped_at:
            try:
                created_timestamp = str(int(tweet.scraped_at.timestamp() * 1000))
            except:
                created_timestamp = ''
        
        auto_sync_data = {
            '推文原文内容': tweet.content or '',
            '发布时间': publish_timestamp,
            '作者（账号）': tweet.username or '',
            '推文链接': tweet.link or '',
            '话题标签（Hashtag）': ', '.join(hashtags),
            '类型标签': tweet.content_type or '',
            '评论': 0,  # Twitter API限制，暂时设为0
            '点赞': tweet.likes or 0,
            '转发': tweet.retweets or 0,
            '创建时间': created_timestamp
        }
        
        print("自动同步数据格式:")
        for key, value in auto_sync_data.items():
            if isinstance(value, str) and len(value) > 50:
                print(f"   - {key}: {value[:50]}...")
            else:
                print(f"   - {key}: {value}")
        
        print(f"\n🔄 方法2: 手动同步数据处理 (api_sync_feishu)")
        print("-" * 40)
        
        # 模拟手动同步的数据处理逻辑
        from web_app import classify_content_type
        content_type = tweet.content_type or classify_content_type(tweet.content)
        
        # 处理发布时间 - 手动同步中的逻辑
        publish_time = 0
        if tweet.publish_time:
            try:
                if isinstance(tweet.publish_time, str):
                    from dateutil import parser
                    dt = parser.parse(tweet.publish_time)
                    publish_time = int(dt.timestamp())
                else:
                    publish_time = int(tweet.publish_time.timestamp())
            except Exception as e:
                publish_time = int(tweet.scraped_at.timestamp())
        else:
            publish_time = int(tweet.scraped_at.timestamp())
        
        # 验证时间戳合理性
        if publish_time < 946684800:  # 2000年1月1日的时间戳
            publish_time = int(datetime.now().timestamp())
        
        # 转换为毫秒级时间戳
        if publish_time < 10000000000:  # 秒级时间戳
            publish_time_ms = publish_time * 1000
        else:  # 已经是毫秒级
            publish_time_ms = publish_time
        
        hashtags_str = ', '.join(json.loads(tweet.hashtags) if tweet.hashtags else [])
        
        manual_sync_data = {
            '推文原文内容': tweet.content or '',
            # 注意：移除发布时间字段，不同步时间戳
            '作者（账号）': tweet.username or '',
            '推文链接': tweet.link or '',
            '话题标签（Hashtag）': hashtags_str,
            '类型标签': content_type or '',
            '评论': tweet.comments or 0,
            '点赞': tweet.likes or 0,
            '转发': tweet.retweets or 0
            # 注意：移除创建时间字段，让飞书自动生成
        }
        
        print("手动同步数据格式:")
        for key, value in manual_sync_data.items():
            if isinstance(value, str) and len(value) > 50:
                print(f"   - {key}: {value[:50]}...")
            else:
                print(f"   - {key}: {value}")
        
        print(f"\n📊 差异分析:")
        print("-" * 40)
        
        # 对比字段差异
        auto_keys = set(auto_sync_data.keys())
        manual_keys = set(manual_sync_data.keys())
        
        only_in_auto = auto_keys - manual_keys
        only_in_manual = manual_keys - auto_keys
        common_keys = auto_keys & manual_keys
        
        if only_in_auto:
            print(f"❌ 仅在自动同步中的字段: {list(only_in_auto)}")
        
        if only_in_manual:
            print(f"❌ 仅在手动同步中的字段: {list(only_in_manual)}")
        
        print(f"✅ 共同字段: {len(common_keys)}个")
        
        # 对比共同字段的值差异
        value_differences = []
        for key in common_keys:
            auto_val = auto_sync_data[key]
            manual_val = manual_sync_data[key]
            if auto_val != manual_val:
                value_differences.append((key, auto_val, manual_val))
        
        if value_differences:
            print(f"\n⚠️ 值差异 ({len(value_differences)}个):")
            for key, auto_val, manual_val in value_differences:
                print(f"   - {key}:")
                print(f"     自动同步: {auto_val}")
                print(f"     手动同步: {manual_val}")
        else:
            print(f"✅ 共同字段的值完全一致")
        
        print(f"\n🎯 结论:")
        print("-" * 40)
        if only_in_auto:
            print(f"❌ 自动同步包含额外的时间字段，可能导致飞书API处理异常")
        if value_differences:
            print(f"❌ 字段值存在差异，可能影响同步结果")
        if not only_in_auto and not value_differences:
            print(f"✅ 数据处理逻辑基本一致")

if __name__ == "__main__":
    compare_sync_methods()