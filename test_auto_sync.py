#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from web_app import app, db, TweetData, FEISHU_CONFIG, load_config_from_database
from cloud_sync import CloudSyncManager
from datetime import datetime
import json

def test_auto_sync():
    """测试自动同步功能"""
    with app.app_context():
        # 重新加载配置
        load_config_from_database()
        
        print("=== 手动执行自动同步逻辑 ===")
        task_id = 3
        
        # 获取推文数据
        tweets = TweetData.query.filter_by(task_id=task_id).all()
        print(f"找到 {len(tweets)} 条推文")
        
        if not tweets:
            print("没有数据需要同步")
            return
        
        # 准备同步数据
        sync_data = []
        for tweet in tweets[:2]:  # 只测试前2条
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
            
            sync_data.append({
                '推文原文内容': tweet.content or '',
                '发布时间': publish_timestamp,
                '作者（账号）': tweet.username or '',
                '推文链接': tweet.link or '',
                '话题标签（Hashtag）': ', '.join(hashtags),
                '类型标签': tweet.content_type or '',
                '收藏数': tweet.likes or 0,
                '点赞数': tweet.likes or 0,
                '转发数': tweet.retweets or 0,
                '创建时间': created_timestamp
            })
        
        print(f"准备同步数据: {len(sync_data)} 条")
        print(f"第一条推文: {sync_data[0]['推文原文内容'][:50]}...")
        
        # 创建云同步管理器并同步
        sync_manager = CloudSyncManager()
        
        # 设置飞书配置
        print(f"飞书配置: app_id={FEISHU_CONFIG['app_id'][:10]}..., token={FEISHU_CONFIG['spreadsheet_token'][:10]}...")
        
        setup_result = sync_manager.setup_feishu(FEISHU_CONFIG['app_id'], FEISHU_CONFIG['app_secret'])
        print(f"飞书设置结果: {setup_result}")
        
        if setup_result:
            print("开始同步到飞书...")
            success = sync_manager.sync_to_feishu(
                sync_data,
                FEISHU_CONFIG['spreadsheet_token'],
                FEISHU_CONFIG['table_id']
            )
            
            if success:
                print(f"任务 {task_id} 同步到飞书成功")
            else:
                print(f"任务 {task_id} 同步到飞书失败")
        else:
            print(f"任务 {task_id} 同步失败：飞书配置设置失败")

if __name__ == '__main__':
    test_auto_sync()