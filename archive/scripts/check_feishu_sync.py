#!/usr/bin/env python3
from web_app import app, TweetData, db

with app.app_context():
    # 检查所有推文的飞书同步状态
    tweets = TweetData.query.all()
    synced_count = sum(1 for t in tweets if t.synced_to_feishu)
    
    print(f'数据库中总推文数: {len(tweets)}')
    print(f'已同步到飞书的推文数: {synced_count}')
    print(f'未同步到飞书的推文数: {len(tweets) - synced_count}')
    
    if tweets:
        print('\n最新几条推文的同步状态:')
        for tweet in tweets[-5:]:
            print(f'- 推文ID: {tweet.id}')
            print(f'  任务ID: {tweet.task_id}')
            print(f'  用户: {tweet.username}')
            print(f'  内容: {tweet.content[:50]}...')
            print(f'  已同步到飞书: {tweet.synced_to_feishu}')
            print(f'  抓取时间: {tweet.scraped_at}')
            print('---')
    
    # 检查飞书配置
    from web_app import FEISHU_CONFIG
    print(f'\n飞书配置状态:')
    print(f'- 启用状态: {FEISHU_CONFIG.get("enabled", False)}')
    print(f'- App ID: {"已配置" if FEISHU_CONFIG.get("app_id") else "未配置"}')
    print(f'- App Secret: {"已配置" if FEISHU_CONFIG.get("app_secret") else "未配置"}')
    print(f'- 表格Token: {"已配置" if FEISHU_CONFIG.get("spreadsheet_token") else "未配置"}')
    print(f'- 表格ID: {"已配置" if FEISHU_CONFIG.get("table_id") else "未配置"}')