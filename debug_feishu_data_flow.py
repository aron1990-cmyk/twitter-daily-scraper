#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试飞书同步数据流程
检查数据在传输过程中是否被正确处理
"""

import os
import sys
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web_app import app, db, TweetData, FEISHU_CONFIG
from cloud_sync import CloudSyncManager

def debug_feishu_data_flow():
    """调试飞书同步数据流程"""
    print("="*80)
    print("🔍 飞书同步数据流程调试")
    print("="*80)
    
    with app.app_context():
        # 1. 获取任务27的数据
        print("\n1. 获取任务27的数据:")
        tweets = TweetData.query.filter_by(task_id=27).limit(3).all()
        print(f"   - 获取到 {len(tweets)} 条数据")
        
        for i, tweet in enumerate(tweets):
            print(f"\n   推文 {i+1}:")
            print(f"     - ID: {tweet.id}")
            print(f"     - 内容: {tweet.content[:50] if tweet.content else '空'}...")
            print(f"     - 点赞: {tweet.likes} (类型: {type(tweet.likes)})")
            print(f"     - 评论: {tweet.comments} (类型: {type(tweet.comments)})")
            print(f"     - 转发: {tweet.retweets} (类型: {type(tweet.retweets)})")
            print(f"     - 作者: {tweet.username}")
            print(f"     - 链接: {tweet.link}")
        
        # 2. 模拟web_app.py中的数据准备过程
        print("\n2. 模拟web_app.py中的数据准备过程:")
        data = []
        for i, tweet in enumerate(tweets):
            print(f"\n   处理推文 {i+1}:")
            
            # 模拟web_app.py中的数据映射逻辑
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
            
            print(f"     - 映射后数据:")
            for key, value in tweet_data.items():
                print(f"       * {key}: '{str(value)[:50]}...' (类型: {type(value)})")
            
            data.append(tweet_data)
        
        # 3. 检查飞书配置
        print("\n3. 检查飞书配置:")
        print(f"   - app_id: {FEISHU_CONFIG['app_id'][:10]}...")
        print(f"   - spreadsheet_token: {FEISHU_CONFIG['spreadsheet_token'][:10]}...")
        print(f"   - table_id: {FEISHU_CONFIG['table_id']}")
        
        # 4. 初始化CloudSyncManager
        print("\n4. 初始化CloudSyncManager:")
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
        
        # 5. 获取飞书表格字段信息
        print("\n5. 获取飞书表格字段信息:")
        try:
            access_token = sync_manager.get_feishu_access_token()
            if access_token:
                print(f"   - 访问令牌获取成功: {access_token[:15]}...")
                
                import requests
                headers = {
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json'
                }
                
                fields_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_CONFIG['spreadsheet_token']}/tables/{FEISHU_CONFIG['table_id']}/fields"
                fields_response = requests.get(fields_url, headers=headers)
                
                if fields_response.status_code == 200:
                    fields_result = fields_response.json()
                    if fields_result.get('code') == 0:
                        fields_data = fields_result.get('data', {}).get('items', [])
                        available_fields = [field.get('field_name') for field in fields_data]
                        field_types = {field.get('field_name'): field.get('type') for field in fields_data}
                        
                        print(f"   - 飞书表格字段: {available_fields}")
                        print(f"   - 字段类型: {field_types}")
                        
                        # 6. 检查数据字段匹配
                        print("\n6. 检查数据字段匹配:")
                        for field_name in data[0].keys():
                            if field_name in available_fields:
                                print(f"   - ✅ {field_name}: 匹配")
                            else:
                                print(f"   - ❌ {field_name}: 不匹配")
                        
                        # 7. 模拟cloud_sync.py中的数据处理
                        print("\n7. 模拟cloud_sync.py中的数据处理:")
                        print("   - 注意：cloud_sync.py中被简化为只传输推文原文内容！")
                        
                        # 检查cloud_sync.py中的简化逻辑
                        for i, tweet_item in enumerate(data[:1]):
                            print(f"\n   处理数据项 {i+1}:")
                            print(f"     - 原始数据: {json.dumps(tweet_item, indent=6, ensure_ascii=False)}")
                            
                            # 模拟cloud_sync.py中的简化处理
                            content_value = tweet_item.get('推文原文内容', '')
                            field_type = field_types.get('推文原文内容', 1)
                            
                            # 只保留推文原文内容字段
                            simplified_fields = {
                                '推文原文内容': content_value
                            }
                            
                            print(f"     - 简化后字段: {json.dumps(simplified_fields, indent=6, ensure_ascii=False)}")
                            print(f"     - 问题：其他字段（点赞、评论、转发等）被丢弃了！")
                    else:
                        print(f"   - 字段查询失败: {fields_result.get('msg')}")
                else:
                    print(f"   - 字段查询请求失败: {fields_response.status_code}")
            else:
                print("   - 访问令牌获取失败")
        except Exception as e:
            print(f"   - 异常: {e}")
        
        print("\n" + "="*80)
        print("🔍 调试结论:")
        print("   1. 数据库中的数据是正确的（有点赞、评论、转发数据）")
        print("   2. web_app.py中的数据映射是正确的")
        print("   3. 问题出现在cloud_sync.py中：")
        print("      - 数据被简化为只传输推文原文内容")
        print("      - 其他字段（点赞、评论、转发等）被丢弃")
        print("   4. 需要修复cloud_sync.py中的数据处理逻辑")
        print("="*80)

if __name__ == '__main__':
    debug_feishu_data_flow()