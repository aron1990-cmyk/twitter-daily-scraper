#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动同步任务13的数据到飞书
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_app import app, db, TweetData, FEISHU_CONFIG
from cloud_sync import CloudSyncManager

with app.app_context():
    print('开始手动同步任务13的数据到飞书...')
    
    # 查询任务13的推文数据
    tweets = db.session.query(TweetData).filter_by(task_id=13).all()
    print(f'找到{len(tweets)}条推文')
    
    if not tweets:
        print('没有找到推文数据')
        sys.exit(1)
    
    # 检查飞书配置
    print(f'飞书配置:')
    print(f'  enabled: {FEISHU_CONFIG.get("enabled")}')
    print(f'  app_id: {FEISHU_CONFIG.get("app_id")}')
    print(f'  spreadsheet_token: {FEISHU_CONFIG.get("spreadsheet_token")}')
    print(f'  table_id: {FEISHU_CONFIG.get("table_id")}')
    
    if not FEISHU_CONFIG.get('enabled'):
        print('飞书同步未启用')
        sys.exit(1)
    
    # 构建CloudSyncManager需要的配置格式
    sync_config = {
        'feishu': {
            'app_id': FEISHU_CONFIG.get('app_id'),
            'app_secret': FEISHU_CONFIG.get('app_secret'),
            'base_url': 'https://open.feishu.cn/open-apis'
        }
    }
    
    # 转换推文数据为字典格式
    tweet_dicts = []
    for tweet in tweets:
        tweet_dict = {
            '推文原文内容': tweet.content or '',
            '发布时间': tweet.publish_time or '',
            '作者（账号）': tweet.username or '',
            '推文链接': tweet.link or '',
            '话题标签（Hashtag）': tweet.hashtags or '',
            '类型标签': tweet.content_type or '',
            '收藏数': tweet.likes or 0,
            '点赞数': tweet.likes or 0,
            '转发数': tweet.retweets or 0,
            '创建时间': tweet.scraped_at.strftime('%Y-%m-%d %H:%M:%S') if tweet.scraped_at else ''
        }
        tweet_dicts.append(tweet_dict)
    
    print(f'准备同步{len(tweet_dicts)}条推文到飞书...')
    
    # 创建CloudSyncManager并同步
    cloud_sync = CloudSyncManager(sync_config)
    sync_result = cloud_sync.sync_to_feishu(
        tweet_dicts,
        spreadsheet_token=FEISHU_CONFIG.get('spreadsheet_token'),
        table_id=FEISHU_CONFIG.get('table_id'),
        max_retries=3,
        continue_on_failure=True
    )
    
    print(f'同步结果: {sync_result}')
    
    if sync_result:
        print('开始更新数据库中的同步状态...')
        try:
            for tweet in tweets:
                tweet.synced_to_feishu = True
            db.session.commit()
            print(f'✅ 数据库同步状态更新完成，共更新 {len(tweets)} 条记录')
        except Exception as e:
            print(f'❌ 更新数据库同步状态失败: {e}')
    else:
        print('❌ 飞书同步失败')