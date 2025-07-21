from web_app import app, db, TweetData, ScrapingTask

with app.app_context():
    print('检查抓取任务:')
    tasks = ScrapingTask.query.all()
    for t in tasks:
        print(f'任务ID: {t.id}, 名称: {t.name}, 状态: {t.status}, 目标账户: {t.target_accounts}, 创建时间: {t.created_at}')
    
    print('\n检查推文数据:')
    tweets = TweetData.query.filter(TweetData.username == 'neilpatel').all()
    print(f'neilpatel 的推文数量: {len(tweets)}')
    
    for i, t in enumerate(tweets[:5]):
        print(f'推文{i+1}: ID={t.tweet_id}, 内容={t.content[:100]}...')
    
    print('\n检查所有推文数据:')
    all_tweets = TweetData.query.all()
    print(f'总推文数量: {len(all_tweets)}')