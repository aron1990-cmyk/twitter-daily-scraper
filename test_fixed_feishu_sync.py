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

from cloud_sync import CloudSyncManager
from web_app import app, db, TweetData, ScrapingTask, SystemConfig, FEISHU_CONFIG, load_config_from_database

def test_fixed_feishu_sync():
    """测试修复后的飞书同步功能"""
    print("🔧 测试修复后的飞书同步功能")
    print("=" * 60)
    
    with app.app_context():
        # 加载数据库配置
        load_config_from_database()
        
        # 1. 获取Campaign任务的推文数据
        print("\n1. 获取Campaign任务的推文数据:")
        campaign_task = ScrapingTask.query.filter(
            ScrapingTask.name.like('%Campaign%')
        ).order_by(ScrapingTask.id.desc()).first()
        
        if not campaign_task:
            print("   ❌ 未找到Campaign相关任务")
            return
            
        tweets = TweetData.query.filter_by(task_id=campaign_task.id).limit(2).all()
        print(f"   - 任务ID: {campaign_task.id}")
        print(f"   - 推文数量: {len(tweets)}")
        
        if not tweets:
            print("   ❌ 该任务没有推文数据")
            return
        
        # 2. 使用修复后的字段映射准备数据
        print("\n2. 使用修复后的字段映射准备数据:")
        data = []
        
        for tweet in tweets:
            # 处理发布时间
            publish_time = ''
            if tweet.publish_time:
                try:
                    if isinstance(tweet.publish_time, str):
                        from dateutil import parser
                        dt = parser.parse(tweet.publish_time)
                        publish_time = int(dt.timestamp() * 1000)
                    else:
                        publish_time = int(tweet.publish_time.timestamp() * 1000)
                except:
                    publish_time = ''
            
            # 使用修复后的字段映射（与web_app.py中的一致）
            tweet_data = {
                '推文原文内容': tweet.content,
                '发布时间': publish_time,
                '作者（账号）': tweet.username,
                '推文链接': tweet.link or '',
                '话题标签（Hashtag）': ', '.join(json.loads(tweet.hashtags) if tweet.hashtags else []),
                '类型标签': tweet.content_type or 'general',
                '评论': 0,  # Twitter API限制，暂时设为0
                '点赞': tweet.likes,
                '转发': tweet.retweets,
                '创建时间': int(tweet.scraped_at.timestamp() * 1000)
            }
            
            data.append(tweet_data)
            
            print(f"   - 推文 {tweet.id} 数据:")
            for key, value in tweet_data.items():
                if key == '推文原文内容':
                    print(f"     {key}: '{str(value)[:50]}...'")
                else:
                    print(f"     {key}: {repr(value)}")
            print()
        
        # 3. 初始化CloudSyncManager并测试同步
        print("\n3. 测试飞书同步:")
        try:
            # 使用正确的飞书配置初始化CloudSyncManager
            feishu_config = {
                'feishu': {
                    'app_id': FEISHU_CONFIG['app_id'],
                    'app_secret': FEISHU_CONFIG['app_secret'],
                    'base_url': 'https://open.feishu.cn/open-apis'
                }
            }
            sync_manager = CloudSyncManager(feishu_config)
            print("   ✅ CloudSyncManager 初始化成功")
            
            # 获取访问令牌
            access_token = sync_manager.get_feishu_access_token()
            if not access_token:
                print("   ❌ 获取访问令牌失败")
                return
            print(f"   ✅ 成功获取访问令牌: {access_token[:10]}...")
            
            # 获取飞书表格字段信息
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
                    print(f"   ✅ 飞书表格字段: {available_fields}")
                    
                    # 检查字段匹配情况
                    data_fields = list(data[0].keys()) if data else []
                    print(f"   - 数据字段: {data_fields}")
                    
                    matched_fields = []
                    unmatched_fields = []
                    
                    for field in data_fields:
                        if field in available_fields:
                            matched_fields.append(field)
                        else:
                            unmatched_fields.append(field)
                    
                    print(f"   ✅ 匹配字段: {matched_fields}")
                    if unmatched_fields:
                        print(f"   ⚠️ 不匹配字段: {unmatched_fields}")
                    else:
                        print("   ✅ 所有字段都匹配！")
                    
                    # 执行实际同步测试
                    print("\n4. 执行飞书同步测试:")
                    success = sync_manager.sync_to_feishu(
                        data,
                        FEISHU_CONFIG['spreadsheet_token'],
                        FEISHU_CONFIG['table_id']
                    )
                    
                    if success:
                        print("   ✅ 飞书同步测试成功！")
                        print(f"   - 成功同步 {len(data)} 条数据")
                    else:
                        print("   ❌ 飞书同步测试失败")
                    
                else:
                    print(f"   ❌ 获取字段信息失败: {fields_result.get('msg')}")
            else:
                print(f"   ❌ 请求字段信息失败: HTTP {fields_response.status_code}")
            
        except Exception as e:
            print(f"   ❌ 飞书同步测试失败: {e}")
            import traceback
            print(f"   - 错误详情: {traceback.format_exc()}")
        
        print("\n" + "=" * 60)
        print("🔧 修复后的飞书同步功能测试完成")

if __name__ == '__main__':
    test_fixed_feishu_sync()