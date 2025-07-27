#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查推文内容字段
分析为什么同步到飞书时推文原文内容为空
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_app import app, db, TweetData, ScrapingTask
from datetime import datetime

def check_tweet_content():
    """检查推文内容字段"""
    print("🔍 检查推文内容字段")
    print("=" * 60)
    
    with app.app_context():
        # 1. 获取最近的任务
        print("\n1. 获取最近的任务:")
        recent_tasks = ScrapingTask.query.order_by(ScrapingTask.id.desc()).limit(5).all()
        
        for task in recent_tasks:
            print(f"   - 任务 {task.id}: {task.name} (状态: {task.status})")
            
            # 获取该任务的推文数据
            tweets = TweetData.query.filter_by(task_id=task.id).limit(3).all()
            print(f"     推文数量: {len(tweets)}")
            
            for i, tweet in enumerate(tweets):
                print(f"     推文 {i+1} (ID: {tweet.id}):")
                print(f"       - content字段: '{tweet.content}'")
                print(f"       - content长度: {len(tweet.content) if tweet.content else 0}")
                print(f"       - content类型: {type(tweet.content)}")
                print(f"       - username: '{tweet.username}'")
                print(f"       - link: '{tweet.link}'")
                print(f"       - hashtags: '{tweet.hashtags}'")
                print(f"       - scraped_at: {tweet.scraped_at}")
                print(f"       - publish_time: {tweet.publish_time}")
                print("")
        
        # 2. 统计空内容的推文
        print("\n2. 统计空内容的推文:")
        total_tweets = TweetData.query.count()
        empty_content_tweets = TweetData.query.filter(
            (TweetData.content == None) | (TweetData.content == '')
        ).count()
        
        print(f"   - 总推文数: {total_tweets}")
        print(f"   - 空内容推文数: {empty_content_tweets}")
        print(f"   - 空内容比例: {empty_content_tweets/total_tweets*100:.1f}%" if total_tweets > 0 else "   - 空内容比例: 0%")
        
        # 3. 检查最近同步到飞书的推文
        print("\n3. 检查最近同步到飞书的推文:")
        synced_tweets = TweetData.query.filter_by(synced_to_feishu=1).order_by(TweetData.id.desc()).limit(5).all()
        
        if synced_tweets:
            print(f"   - 已同步推文数: {len(synced_tweets)}")
            for i, tweet in enumerate(synced_tweets):
                print(f"   推文 {i+1} (ID: {tweet.id}):")
                print(f"     - content: '{tweet.content[:100] if tweet.content else 'None'}{'...' if tweet.content and len(tweet.content) > 100 else ''}")
                print(f"     - content长度: {len(tweet.content) if tweet.content else 0}")
                print(f"     - username: '{tweet.username}'")
                print(f"     - task_id: {tweet.task_id}")
        else:
            print("   - 没有找到已同步的推文")
        
        # 4. 检查数据库字段定义
        print("\n4. 检查数据库字段定义:")
        try:
            # 获取表结构信息
            with db.engine.connect() as conn:
                result = conn.execute(db.text("PRAGMA table_info(tweet_data)"))
                columns = result.fetchall()
                
                print("   TweetData表字段:")
                for col in columns:
                    print(f"     - {col[1]}: {col[2]} (NOT NULL: {col[3]}, DEFAULT: {col[4]})")
        except Exception as e:
            print(f"   获取表结构失败: {e}")
        
        # 5. 模拟飞书同步数据准备
        print("\n5. 模拟飞书同步数据准备:")
        if synced_tweets:
            tweet = synced_tweets[0]
            print(f"   使用推文 {tweet.id} 进行模拟:")
            
            # 模拟web_app.py中的数据准备逻辑
            # 处理发布时间
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
                    print(f"     时间解析错误: {e}")
                    publish_time = 0
            
            tweet_data = {
                '推文原文内容': tweet.content or '',
                '发布时间': publish_time,
                '作者（账号）': tweet.username or '',
                '推文链接': tweet.link or '',
                '话题标签（Hashtag）': tweet.hashtags or '',
                '类型标签': tweet.content_type or '',
                '评论': tweet.comments or 0,
                '点赞': tweet.likes or 0,
                '转发': tweet.retweets or 0,
                '创建时间': int(tweet.scraped_at.timestamp()) if tweet.scraped_at else 0
            }
            
            print(f"   准备的数据:")
            for key, value in tweet_data.items():
                if key == '推文原文内容':
                    print(f"     - {key}: '{value}' (长度: {len(str(value))})")
                else:
                    print(f"     - {key}: {value}")
        
        print("\n✅ 检查完成")

if __name__ == '__main__':
    check_tweet_content()