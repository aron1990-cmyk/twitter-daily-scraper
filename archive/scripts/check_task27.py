#!/usr/bin/env python3
from web_app import app, db, TweetData, ScrapingTask

with app.app_context():
    # 查询任务27的基本信息
    task = ScrapingTask.query.get(27)
    if task:
        print(f"任务27信息:")
        print(f"  - 任务名称: {task.name}")
        print(f"  - 目标账号: {task.target_accounts}")
        print(f"  - 最大推文数: {task.max_tweets}")
        print(f"  - 状态: {task.status}")
        print(f"  - 开始时间: {task.started_at}")
        print(f"  - 完成时间: {task.completed_at}")
    else:
        print("任务27不存在")
    
    # 查询任务27的推文数量
    tweet_count = TweetData.query.filter_by(task_id=27).count()
    print(f"\n任务27的推文数量: {tweet_count}")
    
    # 如果有推文，显示前几条
    if tweet_count > 0:
        tweets = TweetData.query.filter_by(task_id=27).limit(5).all()
        print(f"\n前5条推文:")
        for i, tweet in enumerate(tweets, 1):
            print(f"  {i}. @{tweet.username}: {tweet.content[:50]}...")
    else:
        print("\n没有找到任何推文数据")