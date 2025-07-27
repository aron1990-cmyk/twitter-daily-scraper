#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的飞书同步功能
"""

import os
import sys
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web_app import app, db, TweetData, FEISHU_CONFIG
from cloud_sync import CloudSyncManager

def test_fixed_sync():
    """测试修复后的飞书同步功能"""
    print("="*80)
    print("🧪 测试修复后的飞书同步功能")
    print("="*80)
    
    with app.app_context():
        # 1. 获取一条测试数据
        print("\n1. 获取测试数据:")
        tweet = TweetData.query.filter_by(task_id=27).first()
        if not tweet:
            print("   - 没有找到测试数据")
            return
        
        print(f"   - 推文ID: {tweet.id}")
        print(f"   - 内容: {tweet.content[:50]}...")
        print(f"   - 点赞: {tweet.likes}")
        print(f"   - 评论: {tweet.comments}")
        print(f"   - 转发: {tweet.retweets}")
        print(f"   - 作者: {tweet.username}")
        
        # 2. 准备同步数据
        print("\n2. 准备同步数据:")
        hashtags_str = ', '.join(json.loads(tweet.hashtags) if tweet.hashtags else [])
        
        sync_data = [{
            '推文原文内容': tweet.content or '',
            '作者（账号）': tweet.username or '',
            '推文链接': tweet.link or '',
            '话题标签（Hashtag）': hashtags_str,
            '类型标签': tweet.content_type or '',
            '评论': tweet.comments or 0,
            '点赞': tweet.likes or 0,
            '转发': tweet.retweets or 0
        }]
        
        print(f"   - 同步数据: {json.dumps(sync_data[0], indent=4, ensure_ascii=False)}")
        
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
                sync_data,
                FEISHU_CONFIG['spreadsheet_token'],
                FEISHU_CONFIG['table_id']
            )
            
            if success:
                print("   - ✅ 飞书同步成功！")
                print("   - 🎉 所有字段（包括点赞、评论、转发）应该已成功同步到飞书")
            else:
                print("   - ❌ 飞书同步失败")
                
        except Exception as e:
            print(f"   - ❌ 飞书同步异常: {e}")
            import traceback
            print(f"   - 📋 异常详情: {traceback.format_exc()}")
        
        print("\n" + "="*80)
        print("🏁 测试完成")
        print("请检查飞书表格中是否显示了完整的数据（包括点赞、评论、转发等字段）")
        print("="*80)

if __name__ == '__main__':
    test_fixed_sync()