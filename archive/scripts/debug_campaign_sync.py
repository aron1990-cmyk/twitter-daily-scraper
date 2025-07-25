#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试Campaign任务的飞书同步问题
检查数据库中的推文数据和同步状态
"""

import json
from web_app import app, db, TweetData, ScrapingTask

def debug_campaign_sync():
    """调试Campaign任务的飞书同步问题"""
    with app.app_context():
        print("🔍 开始调试Campaign任务的飞书同步问题")
        print("=" * 60)
        
        # 1. 查找包含Campaign的推文
        print("\n1. 查找包含Campaign的推文数据:")
        campaign_tweets = TweetData.query.filter(
            TweetData.content.like('%Campaign%')
        ).all()
        
        print(f"   - 找到 {len(campaign_tweets)} 条包含Campaign的推文")
        
        if campaign_tweets:
            print("\n   最新的5条Campaign推文:")
            for i, tweet in enumerate(campaign_tweets[-5:], 1):
                print(f"   [{i}] 任务ID: {tweet.task_id}")
                print(f"       用户名: {tweet.username}")
                print(f"       内容: {tweet.content[:100]}...")
                print(f"       点赞数: {tweet.likes}")
                print(f"       转发数: {tweet.retweets}")
                print(f"       链接: {tweet.link}")
                print(f"       话题标签: {tweet.hashtags}")
                print(f"       飞书同步状态: {tweet.synced_to_feishu}")
                print(f"       抓取时间: {tweet.scraped_at}")
                print()
        
        # 2. 查找Campaign相关的任务
        print("\n2. 查找Campaign相关的抓取任务:")
        campaign_tasks = ScrapingTask.query.filter(
            ScrapingTask.name.like('%Campaign%')
        ).all()
        
        print(f"   - 找到 {len(campaign_tasks)} 个Campaign相关任务")
        
        if campaign_tasks:
            print("\n   Campaign任务详情:")
            for i, task in enumerate(campaign_tasks, 1):
                print(f"   [{i}] 任务ID: {task.id}")
                print(f"       任务名称: {task.name}")
                print(f"       状态: {task.status}")
                print(f"       目标账号: {task.target_accounts}")
                print(f"       目标关键词: {task.target_keywords}")
                print(f"       结果数量: {task.result_count}")
                print(f"       创建时间: {task.created_at}")
                print(f"       完成时间: {task.completed_at}")
                
                # 查看该任务的推文数据
                task_tweets = TweetData.query.filter_by(task_id=task.id).all()
                print(f"       推文数量: {len(task_tweets)}")
                
                if task_tweets:
                    synced_count = sum(1 for t in task_tweets if t.synced_to_feishu)
                    print(f"       已同步到飞书: {synced_count}/{len(task_tweets)}")
                    
                    # 显示前3条推文的详细信息
                    print(f"       前3条推文详情:")
                    for j, tweet in enumerate(task_tweets[:3], 1):
                        print(f"         [{j}] 内容: {tweet.content[:50]}...")
                        print(f"             用户名: {tweet.username}")
                        print(f"             点赞: {tweet.likes}, 转发: {tweet.retweets}")
                        print(f"             链接: {tweet.link}")
                        print(f"             话题标签: {tweet.hashtags}")
                        print(f"             飞书同步: {tweet.synced_to_feishu}")
                print()
        
        # 3. 检查最近的所有任务
        print("\n3. 检查最近的所有抓取任务:")
        recent_tasks = ScrapingTask.query.order_by(ScrapingTask.created_at.desc()).limit(10).all()
        
        print(f"   - 最近10个任务:")
        for i, task in enumerate(recent_tasks, 1):
            task_tweets = TweetData.query.filter_by(task_id=task.id).all()
            synced_count = sum(1 for t in task_tweets if t.synced_to_feishu)
            
            print(f"   [{i}] ID:{task.id} | {task.name[:30]}... | 状态:{task.status} | 推文:{len(task_tweets)} | 已同步:{synced_count}")
        
        # 4. 分析数据格式问题
        print("\n4. 分析推文数据格式:")
        if campaign_tweets:
            sample_tweet = campaign_tweets[0]
            print(f"   样本推文数据结构:")
            print(f"   - ID: {sample_tweet.id}")
            print(f"   - 任务ID: {sample_tweet.task_id}")
            print(f"   - 用户名: '{sample_tweet.username}'")
            print(f"   - 内容长度: {len(sample_tweet.content) if sample_tweet.content else 0}")
            print(f"   - 内容类型: {type(sample_tweet.content)}")
            print(f"   - 点赞数: {sample_tweet.likes} (类型: {type(sample_tweet.likes)})")
            print(f"   - 转发数: {sample_tweet.retweets} (类型: {type(sample_tweet.retweets)})")
            print(f"   - 链接: '{sample_tweet.link}'")
            print(f"   - 话题标签: '{sample_tweet.hashtags}' (类型: {type(sample_tweet.hashtags)})")
            print(f"   - 发布时间: {sample_tweet.publish_time} (类型: {type(sample_tweet.publish_time)})")
            print(f"   - 抓取时间: {sample_tweet.scraped_at} (类型: {type(sample_tweet.scraped_at)})")
            
            # 尝试解析话题标签
            if sample_tweet.hashtags:
                try:
                    hashtags = json.loads(sample_tweet.hashtags)
                    print(f"   - 解析后的话题标签: {hashtags} (类型: {type(hashtags)})")
                except Exception as e:
                    print(f"   - 话题标签解析失败: {e}")
        
        print("\n=" * 60)
        print("🔍 调试完成")

if __name__ == '__main__':
    debug_campaign_sync()