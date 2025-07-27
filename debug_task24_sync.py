#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试任务24的飞书同步问题
检查数据传递和字段映射
"""

import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_app import app, TweetData, db, FEISHU_CONFIG
from cloud_sync import CloudSyncManager

def debug_task24_sync():
    """调试任务24的飞书同步"""
    print("🔍 开始调试任务24的飞书同步问题")
    print("="*60)
    
    with app.app_context():
        # 1. 检查任务24的数据
        print("\n📊 步骤1: 检查任务24的推特数据")
        tweets = TweetData.query.filter_by(task_id=24).limit(5).all()
        print(f"   - 找到 {len(tweets)} 条推特数据")
        
        if not tweets:
            print("❌ 没有找到任务24的数据")
            return
        
        # 显示原始数据
        for i, tweet in enumerate(tweets[:3]):
            print(f"   - 推特{i+1}: id={tweet.id}")
            print(f"     - content: {repr(tweet.content[:100])}")
            print(f"     - username: {tweet.username}")
            print(f"     - content长度: {len(tweet.content) if tweet.content else 0}")
        
        # 2. 模拟web_app.py中的数据准备过程
        print("\n🔄 步骤2: 模拟数据准备过程")
        sync_data = []
        for tweet in tweets:
            # 解析hashtags
            try:
                hashtags = json.loads(tweet.hashtags) if tweet.hashtags else []
            except:
                hashtags = []
            
            tweet_data = {
                '推文原文内容': tweet.content or '',
                '作者（账号）': tweet.username or '',
                '推文链接': tweet.link or '',
                '话题标签（Hashtag）': ', '.join(hashtags),
                '类型标签': tweet.content_type or '',
                '评论': tweet.comments or 0,
                '点赞': tweet.likes or 0,
                '转发': tweet.retweets or 0
            }
            sync_data.append(tweet_data)
        
        print(f"   - 准备了 {len(sync_data)} 条同步数据")
        
        # 显示准备的数据
        for i, data in enumerate(sync_data[:3]):
            print(f"   - 数据{i+1}:")
            for key, value in data.items():
                if key == '推文原文内容':
                    print(f"     - {key}: {repr(str(value)[:100])}")
                else:
                    print(f"     - {key}: {repr(value)}")
        
        # 3. 检查飞书配置
        print("\n⚙️ 步骤3: 检查飞书配置")
        print(f"   - enabled: {FEISHU_CONFIG.get('enabled')}")
        print(f"   - app_id: {FEISHU_CONFIG.get('app_id', '')[:10]}...")
        print(f"   - spreadsheet_token: {FEISHU_CONFIG.get('spreadsheet_token', '')[:10]}...")
        print(f"   - table_id: {FEISHU_CONFIG.get('table_id')}")
        
        # 4. 创建同步管理器并测试
        print("\n🚀 步骤4: 创建同步管理器并测试")
        sync_config = {
            'feishu': {
                'enabled': True,
                'app_id': FEISHU_CONFIG['app_id'],
                'app_secret': FEISHU_CONFIG['app_secret'],
                'base_url': 'https://open.feishu.cn/open-apis'
            }
        }
        
        sync_manager = CloudSyncManager(sync_config)
        
        # 设置飞书配置
        if sync_manager.setup_feishu(FEISHU_CONFIG['app_id'], FEISHU_CONFIG['app_secret']):
            print("✅ 飞书配置设置成功")
            
            # 只测试第一条数据
            test_data = sync_data[:1]
            print(f"\n🧪 步骤5: 测试同步第一条数据")
            print(f"   - 测试数据: {test_data}")
            
            try:
                success = sync_manager.sync_to_feishu(
                    test_data,
                    FEISHU_CONFIG['spreadsheet_token'],
                    FEISHU_CONFIG['table_id']
                )
                
                if success:
                    print("✅ 同步测试成功")
                else:
                    print("❌ 同步测试失败")
                    
            except Exception as e:
                print(f"❌ 同步过程中发生异常: {e}")
                import traceback
                print(f"   - 详细错误: {traceback.format_exc()}")
        else:
            print("❌ 飞书配置设置失败")

if __name__ == "__main__":
    debug_task24_sync()