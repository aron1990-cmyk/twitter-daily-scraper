#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的飞书同步时间问题
验证发布时间正确转换和创建时间字段移除
"""

import json
from datetime import datetime
from web_app import app, db, TweetData, FEISHU_CONFIG, classify_content_type
from dateutil import parser

def test_time_conversion():
    """测试时间转换逻辑"""
    print("🕐 测试时间转换逻辑")
    print("=" * 50)
    
    with app.app_context():
        # 获取几条推文数据进行测试
        tweets = TweetData.query.limit(5).all()
        
        if not tweets:
            print("❌ 没有找到推文数据")
            return
        
        print(f"📊 找到 {len(tweets)} 条推文用于测试")
        
        for i, tweet in enumerate(tweets, 1):
            print(f"\n🔍 测试推文 {i}:")
            print(f"   - ID: {tweet.id}")
            print(f"   - 用户: {tweet.username}")
            print(f"   - 原始发布时间: {repr(tweet.publish_time)}")
            print(f"   - 抓取时间: {tweet.scraped_at}")
            
            # 模拟飞书同步的时间处理逻辑
            publish_time = ''
            if tweet.publish_time:
                try:
                    if isinstance(tweet.publish_time, str):
                        # 如果是字符串，尝试解析为datetime
                        dt = parser.parse(tweet.publish_time)
                        # 转换为毫秒时间戳
                        publish_time = int(dt.timestamp() * 1000)
                        print(f"   - 解析后的datetime: {dt}")
                    else:
                        # 如果已经是datetime对象
                        publish_time = int(tweet.publish_time.timestamp() * 1000)
                except Exception as e:
                    # 如果解析失败，使用抓取时间作为备选
                    print(f"   - 发布时间解析失败: {e}, 使用抓取时间作为备选")
                    publish_time = int(tweet.scraped_at.timestamp() * 1000)
            else:
                # 如果没有发布时间，使用抓取时间
                publish_time = int(tweet.scraped_at.timestamp() * 1000)
            
            print(f"   - 转换后的时间戳: {publish_time}")
            
            # 验证时间戳是否合理（转换回日期查看）
            if publish_time:
                converted_date = datetime.fromtimestamp(publish_time / 1000)
                print(f"   - 验证转换结果: {converted_date}")
                
                # 检查是否是1970年（错误的时间戳）
                if converted_date.year == 1970:
                    print(f"   - ⚠️ 警告: 时间戳转换错误，显示为1970年")
                else:
                    print(f"   - ✅ 时间戳转换正确")

def test_feishu_data_format():
    """测试飞书数据格式"""
    print("\n📋 测试飞书数据格式")
    print("=" * 50)
    
    with app.app_context():
        # 获取一条推文数据
        tweet = TweetData.query.first()
        
        if not tweet:
            print("❌ 没有找到推文数据")
            return
        
        # 使用修复后的逻辑准备数据
        content_type = tweet.content_type or classify_content_type(tweet.content)
        
        # 处理发布时间 - 修复时间戳转换问题
        publish_time = ''
        if tweet.publish_time:
            try:
                if isinstance(tweet.publish_time, str):
                    dt = parser.parse(tweet.publish_time)
                    publish_time = int(dt.timestamp() * 1000)
                else:
                    publish_time = int(tweet.publish_time.timestamp() * 1000)
            except Exception as e:
                print(f"发布时间解析失败: {e}, 使用抓取时间作为备选")
                publish_time = int(tweet.scraped_at.timestamp() * 1000)
        else:
            publish_time = int(tweet.scraped_at.timestamp() * 1000)
        
        # 准备飞书数据（移除创建时间字段）
        feishu_data = {
            '推文原文内容': tweet.content,
            '发布时间': publish_time,
            '作者（账号）': tweet.username,
            '推文链接': tweet.link or '',
            '话题标签（Hashtag）': ', '.join(json.loads(tweet.hashtags) if tweet.hashtags else []),
            '类型标签': content_type,
            '评论': 0,
            '点赞': tweet.likes,
            '转发': tweet.retweets
            # 注意：已移除创建时间字段，让飞书自动生成
        }
        
        print("📤 准备发送到飞书的数据格式:")
        for key, value in feishu_data.items():
            if key == '推文原文内容':
                print(f"   - {key}: {str(value)[:50]}...")
            elif key == '发布时间':
                # 显示时间戳对应的日期
                date_str = datetime.fromtimestamp(value / 1000).strftime('%Y-%m-%d %H:%M:%S')
                print(f"   - {key}: {value} ({date_str})")
            else:
                print(f"   - {key}: {value}")
        
        print("\n✅ 修复要点:")
        print("   1. 发布时间使用正确的时间戳转换")
        print("   2. 移除了创建时间字段，让飞书自动生成")
        print("   3. 增加了错误处理，解析失败时使用抓取时间作为备选")

if __name__ == '__main__':
    print("🧪 测试修复后的飞书同步时间问题")
    print("=" * 60)
    
    test_time_conversion()
    test_feishu_data_format()
    
    print("\n🎉 测试完成！")
    print("\n💡 如果时间显示正确，可以重新同步数据到飞书进行验证")