#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试飞书字段映射问题
检查web_app.py传递的数据格式与cloud_sync.py期望的格式是否匹配
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_app import app, TweetData, db, FEISHU_CONFIG
from cloud_sync import CloudSyncManager
import json

def debug_field_mapping():
    """调试字段映射问题"""
    print("🔍 调试飞书字段映射问题")
    print("=" * 60)
    
    with app.app_context():
        # 1. 获取最新的joshwoodward任务数据
        print("\n1. 获取数据库中的推文数据:")
        tweets = TweetData.query.filter_by(task_id=20).limit(2).all()
        
        if not tweets:
            print("   ❌ 没有找到推文数据")
            return
        
        print(f"   ✅ 找到 {len(tweets)} 条推文数据")
        
        # 2. 检查web_app.py中的数据准备逻辑
        print("\n2. 模拟web_app.py的数据准备逻辑:")
        web_app_data = []
        for tweet in tweets:
            # 这是web_app.py中api_sync_feishu方法的数据格式
            tweet_data = {
                '推文原文内容': tweet.content or '',
                '作者（账号）': tweet.username or '',
                '推文链接': tweet.link or '',
                '话题标签（Hashtag）': ', '.join(json.loads(tweet.hashtags) if tweet.hashtags else []),
                '类型标签': tweet.content_type or '',
                '评论': tweet.comments or 0,
                '点赞': tweet.likes or 0,
                '转发': tweet.retweets or 0
            }
            web_app_data.append(tweet_data)
            print(f"   推文 {tweet.id}:")
            print(f"     - 推文原文内容: '{tweet_data['推文原文内容'][:30]}...'")
            print(f"     - 作者（账号）: '{tweet_data['作者（账号）']}'")
            print(f"     - 推文链接: '{tweet_data['推文链接']}'")
        
        # 3. 检查cloud_sync.py中的数据处理逻辑
        print("\n3. 模拟cloud_sync.py的数据处理逻辑:")
        
        # 模拟cloud_sync.py中的字段获取逻辑
        for idx, tweet in enumerate(web_app_data):
            print(f"\n   处理第 {idx + 1} 条推文:")
            print(f"     - tweet.get('推文原文内容', ''): '{tweet.get('推文原文内容', '')[:30]}...'")
            print(f"     - tweet.get('作者（账号）', ''): '{tweet.get('作者（账号）', '')}'")
            print(f"     - tweet.get('推文链接', ''): '{tweet.get('推文链接', '')}'")
            
            # 检查字段是否存在
            missing_fields = []
            for field_name in ['推文原文内容', '作者（账号）', '推文链接']:
                if not tweet.get(field_name):
                    missing_fields.append(field_name)
            
            if missing_fields:
                print(f"     ❌ 缺失字段: {missing_fields}")
            else:
                print(f"     ✅ 所有关键字段都存在")
        
        # 4. 测试实际的飞书同步
        print("\n4. 测试实际的飞书同步:")
        sync_config = {
            'feishu': {
                'enabled': True,
                'app_id': FEISHU_CONFIG['app_id'],
                'app_secret': FEISHU_CONFIG['app_secret'],
                'base_url': 'https://open.feishu.cn/open-apis'
            }
        }
        
        sync_manager = CloudSyncManager(sync_config)
        
        # 只测试第一条数据
        test_data = [web_app_data[0]]
        print(f"   测试数据: {test_data}")
        
        try:
            success = sync_manager.sync_to_feishu(
                test_data,
                FEISHU_CONFIG['spreadsheet_token'],
                FEISHU_CONFIG['table_id']
            )
            print(f"   同步结果: {'成功' if success else '失败'}")
        except Exception as e:
            print(f"   同步异常: {e}")
            import traceback
            print(f"   详细错误: {traceback.format_exc()}")

if __name__ == "__main__":
    debug_field_mapping()