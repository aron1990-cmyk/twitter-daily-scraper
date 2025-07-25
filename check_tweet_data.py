#!/usr/bin/env python3
from web_app import app, TweetData, db

with app.app_context():
    # 检查任务5的推文数据
    tweets = TweetData.query.filter_by(task_id=5).all()
    print(f'任务5抓取的推文数量: {len(tweets)}')
    
    if tweets:
        print('\n最新的几条推文:')
        for tweet in tweets[:5]:
            print(f'- ID: {tweet.id}')
            print(f'  用户: {tweet.username}')
            print(f'  内容: {tweet.content[:100]}...')
            print(f'  时间: {tweet.created_at}')
            print(f'  点赞数: {tweet.likes}')
            print(f'  转发数: {tweet.retweets}')
            print(f'  评论数: {tweet.comments}')
            print('---')
    
    # 检查所有推文数据
    all_tweets = TweetData.query.all()
    print(f'\n数据库中总推文数量: {len(all_tweets)}')
    
    # 按任务ID分组统计
    from collections import defaultdict
    task_counts = defaultdict(int)
    for tweet in all_tweets:
        task_counts[tweet.task_id] += 1
    
    print('\n各任务的推文数量:')
    for task_id, count in sorted(task_counts.items()):
        print(f'任务{task_id}: {count}条推文')