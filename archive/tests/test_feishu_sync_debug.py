#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试飞书同步调试脚本
用于调试Campaign任务飞书同步内容为空的问题
"""

import os
import sys
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cloud_sync import CloudSyncManager
from web_app import app, db, TweetData, ScrapingTask, SystemConfig, FEISHU_CONFIG, load_config_from_database

def test_feishu_sync_debug():
    """测试飞书同步调试"""
    print("🔍 开始飞书同步调试测试")
    print("=" * 60)
    
    with app.app_context():
        # 加载数据库配置
        load_config_from_database()
        
        # 1. 检查飞书配置
        print("\n1. 检查飞书配置:")
        print(f"   - App ID: {FEISHU_CONFIG.get('app_id', 'N/A')[:10]}...")
        print(f"   - 表格Token: {FEISHU_CONFIG.get('spreadsheet_token', 'N/A')[:10]}...")
        print(f"   - 表格ID: {FEISHU_CONFIG.get('table_id', 'N/A')}")
        print(f"   - 启用状态: {FEISHU_CONFIG.get('enabled', False)}")
        
        # 2. 获取Campaign任务的推文数据
        print("\n2. 获取Campaign任务的推文数据:")
        campaign_task = ScrapingTask.query.filter(
            ScrapingTask.name.like('%Campaign%')
        ).order_by(ScrapingTask.id.desc()).first()
        
        if not campaign_task:
            print("   ❌ 未找到Campaign相关任务")
            return
            
        print(f"   - 任务ID: {campaign_task.id}")
        print(f"   - 任务名称: {campaign_task.name}")
        print(f"   - 任务状态: {campaign_task.status}")
        
        # 获取该任务的推文
        tweets = TweetData.query.filter_by(task_id=campaign_task.id).all()
        print(f"   - 推文数量: {len(tweets)}")
        
        if not tweets:
            print("   ❌ 该任务没有推文数据")
            return
            
        # 3. 分析推文数据结构
        print("\n3. 分析推文数据结构:")
        sample_tweet = tweets[0]
        print(f"   - 样本推文ID: {sample_tweet.id}")
        print(f"   - 用户名: '{sample_tweet.username}'")
        print(f"   - 内容长度: {len(sample_tweet.content or '')}")
        print(f"   - 内容预览: '{(sample_tweet.content or '')[:100]}...'")
        print(f"   - 链接: '{sample_tweet.link}'")
        print(f"   - 点赞数: {sample_tweet.likes}")
        print(f"   - 转发数: {sample_tweet.retweets}")
        print(f"   - 话题标签: {sample_tweet.hashtags}")
        print(f"   - 发布时间: {sample_tweet.publish_time}")
        print(f"   - 抓取时间: {sample_tweet.scraped_at}")
        
        # 4. 模拟数据准备过程（与web_app.py中的逻辑一致）
        print("\n4. 模拟数据准备过程:")
        data = []
        
        for tweet in tweets[:2]:  # 只处理前2条作为测试
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
            
            # 准备数据（与web_app.py中的格式一致）
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
                print(f"     {key}: {repr(value)}")
            print()
        
        # 5. 测试飞书同步管理器
        print("\n5. 测试飞书同步管理器:")
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
            
            # 检查飞书配置
            if not all([FEISHU_CONFIG.get('app_id'), FEISHU_CONFIG.get('app_secret'), 
                       FEISHU_CONFIG.get('spreadsheet_token'), FEISHU_CONFIG.get('table_id')]):
                print("   ❌ 飞书配置不完整，无法进行实际同步测试")
                print("   - 建议检查飞书配置是否正确设置")
                return
            
            # 获取访问令牌测试
            print("   - 测试获取飞书访问令牌...")
            access_token = sync_manager.get_feishu_access_token()
            if access_token:
                print(f"   ✅ 成功获取访问令牌: {access_token[:10]}...")
            else:
                print("   ❌ 获取访问令牌失败")
                return
            
            # 获取表格字段信息
            print("   - 获取飞书表格字段信息...")
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
                    print(f"   ✅ 获取到飞书表格字段: {available_fields}")
                    
                    # 检查字段匹配情况
                    print("\n6. 检查字段匹配情况:")
                    data_fields = list(data[0].keys()) if data else []
                    print(f"   - 数据字段: {data_fields}")
                    print(f"   - 飞书字段: {available_fields}")
                    
                    matched_fields = []
                    unmatched_fields = []
                    
                    for field in data_fields:
                        if field in available_fields:
                            matched_fields.append(field)
                        else:
                            unmatched_fields.append(field)
                    
                    print(f"   - 匹配字段: {matched_fields}")
                    print(f"   - 不匹配字段: {unmatched_fields}")
                    
                    if unmatched_fields:
                        print("   ⚠️ 发现不匹配字段，这可能导致数据同步问题")
                        print("   - 建议检查飞书表格的字段名称是否与代码中的字段名称一致")
                    
                else:
                    print(f"   ❌ 获取字段信息失败: {fields_result.get('msg')}")
            else:
                print(f"   ❌ 请求字段信息失败: HTTP {fields_response.status_code}")
                print(f"   - 响应内容: {fields_response.text[:200]}...")
            
        except Exception as e:
            print(f"   ❌ 飞书同步管理器测试失败: {e}")
            import traceback
            print(f"   - 错误详情: {traceback.format_exc()}")
        
        print("\n" + "=" * 60)
        print("🔍 飞书同步调试测试完成")

if __name__ == '__main__':
    test_feishu_sync_debug()