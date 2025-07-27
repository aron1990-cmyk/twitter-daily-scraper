#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整同步任务27的数据到飞书
"""

import os
import sys
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web_app import app, db, TweetData, FEISHU_CONFIG
from cloud_sync import CloudSyncManager

def sync_task27_complete():
    """完整同步任务27的数据到飞书"""
    print("="*80)
    print("🚀 完整同步任务27的数据到飞书")
    print("="*80)
    
    with app.app_context():
        # 1. 获取任务27的所有数据
        print("\n1. 获取任务27的数据:")
        tweets = TweetData.query.filter_by(task_id=27).all()
        print(f"   - 获取到 {len(tweets)} 条数据")
        
        if not tweets:
            print("   - 没有找到数据")
            return
        
        # 2. 准备同步数据
        print("\n2. 准备同步数据:")
        data = []
        for i, tweet in enumerate(tweets):
            hashtags_str = ', '.join(json.loads(tweet.hashtags) if tweet.hashtags else [])
            
            tweet_data = {
                '推文原文内容': tweet.content or '',
                '作者（账号）': tweet.username or '',
                '推文链接': tweet.link or '',
                '话题标签（Hashtag）': hashtags_str,
                '类型标签': tweet.content_type or '',
                '评论': tweet.comments or 0,
                '点赞': tweet.likes or 0,
                '转发': tweet.retweets or 0
            }
            
            data.append(tweet_data)
            
            if i < 3:  # 只打印前3条的详细信息
                print(f"\n   推文 {i+1}:")
                print(f"     - 内容: {tweet.content[:50]}...")
                print(f"     - 点赞: {tweet.likes}")
                print(f"     - 评论: {tweet.comments}")
                print(f"     - 转发: {tweet.retweets}")
        
        print(f"\n   - 准备了 {len(data)} 条同步数据")
        
        # 3. 初始化CloudSyncManager
        print("\n3. 初始化CloudSyncManager:")
        sync_config = {
            'feishu': {
                'enabled': True,
                'app_id': FEISHU_CONFIG['app_id'],
                'app_secret': FEISHU_CONFIG['app_secret'],
                'spreadsheet_token': FEISHU_CONFIG['spreadsheet_token'],
                'table_id': FEISHU_CONFIG['table_id'],
                'base_url': 'https://open.feishu.cn/open-apis'
            }
        }
        
        sync_manager = CloudSyncManager(sync_config)
        print("   - CloudSyncManager初始化完成")
        
        # 4. 执行同步
        print("\n4. 执行飞书同步:")
        try:
            success = sync_manager.sync_to_feishu(
                data,
                FEISHU_CONFIG['spreadsheet_token'],
                FEISHU_CONFIG['table_id']
            )
            
            if success:
                print("\n   - ✅ 飞书同步成功！")
                print(f"   - 🎉 {len(data)} 条数据已成功同步到飞书多维表格")
                print("   - 📊 所有字段（包括点赞、评论、转发）都已同步")
                
                # 5. 更新数据库同步状态
                print("\n5. 更新数据库同步状态:")
                for tweet in tweets:
                    tweet.synced_to_feishu = 1
                db.session.commit()
                print(f"   - ✅ 已更新 {len(tweets)} 条记录的同步状态")
                
            else:
                print("   - ❌ 飞书同步失败")
                
        except Exception as e:
            print(f"   - ❌ 飞书同步异常: {e}")
            import traceback
            print(f"   - 📋 异常详情: {traceback.format_exc()}")
        
        print("\n" + "="*80)
        print("🏁 同步完成")
        print("请检查飞书表格中是否显示了完整的数据")
        print("="*80)

if __name__ == '__main__':
    sync_task27_complete()