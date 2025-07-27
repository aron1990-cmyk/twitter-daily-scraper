#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整测试飞书同步流程
验证推文原文内容在哪个环节丢失
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_app import app, db, TweetData, ScrapingTask, FEISHU_CONFIG
from cloud_sync import CloudSyncManager
from datetime import datetime
import json

def test_complete_feishu_sync():
    """完整测试飞书同步流程"""
    print("🔍 完整测试飞书同步流程")
    print("=" * 60)
    
    with app.app_context():
        # 1. 获取一条有内容的推文
        print("\n1. 获取测试推文数据:")
        tweet = TweetData.query.filter(
            TweetData.content.isnot(None),
            TweetData.content != ''
        ).first()
        
        if not tweet:
            print("❌ 没有找到有内容的推文")
            return
        
        print(f"   - 推文ID: {tweet.id}")
        print(f"   - 原始content: '{tweet.content[:100]}...'")
        print(f"   - content长度: {len(tweet.content)}")
        print(f"   - username: {tweet.username}")
        print(f"   - link: {tweet.link}")
        
        # 2. 模拟web_app.py中的数据准备逻辑
        print("\n2. 模拟数据准备逻辑:")
        
        # 处理发布时间
        publish_time = 0
        if tweet.publish_time:
            try:
                if isinstance(tweet.publish_time, str):
                    from dateutil import parser
                    dt = parser.parse(tweet.publish_time)
                    publish_time = int(dt.timestamp())
                else:
                    publish_time = int(tweet.publish_time.timestamp())
            except Exception as e:
                print(f"     时间解析错误: {e}")
                publish_time = 0
        
        # 准备同步数据
        sync_data = [{
            '推文原文内容': tweet.content or '',
            '发布时间': publish_time,
            '作者（账号）': tweet.username or '',
            '推文链接': tweet.link or '',
            '话题标签（Hashtag）': tweet.hashtags or '',
            '类型标签': tweet.content_type or '',
            '评论': tweet.comments or 0,
            '点赞': tweet.likes or 0,
            '转发': tweet.retweets or 0,
            '创建时间': int(tweet.scraped_at.timestamp()) if tweet.scraped_at else 0
        }]
        
        print(f"   准备的同步数据:")
        for key, value in sync_data[0].items():
            if key == '推文原文内容':
                print(f"     - {key}: '{value[:100]}...' (长度: {len(str(value))})")
            else:
                print(f"     - {key}: {value}")
        
        # 3. 初始化CloudSyncManager
        print("\n3. 初始化CloudSyncManager:")
        try:
            # 从web_app.py获取飞书配置
            feishu_config = {
                'feishu': {
                    'app_id': FEISHU_CONFIG.get('app_id'),
                    'app_secret': FEISHU_CONFIG.get('app_secret'),
                    'spreadsheet_token': FEISHU_CONFIG.get('spreadsheet_token'),
                    'table_id': FEISHU_CONFIG.get('table_id'),
                    'base_url': 'https://open.feishu.cn/open-apis'
                }
            }
            cloud_sync = CloudSyncManager(feishu_config)
            print("   ✅ CloudSyncManager初始化成功")
        except Exception as e:
            print(f"   ❌ CloudSyncManager初始化失败: {e}")
            return
        
        # 4. 检查飞书配置
        print("\n4. 检查飞书配置:")
        feishu_config = cloud_sync.feishu_config
        if feishu_config:
            print("   ✅ 飞书配置已加载")
            print(f"   - app_id: {feishu_config.get('app_id', 'N/A')[:10]}...")
            print(f"   - spreadsheet_token: {feishu_config.get('spreadsheet_token', 'N/A')[:10]}...")
        else:
            print("   ❌ 飞书配置未找到")
            return
        
        # 5. 获取访问令牌
        print("\n5. 获取飞书访问令牌:")
        try:
            access_token = cloud_sync.get_feishu_access_token()
            if access_token:
                print(f"   ✅ 访问令牌获取成功: {access_token[:20]}...")
            else:
                print("   ❌ 访问令牌获取失败")
                return
        except Exception as e:
            print(f"   ❌ 访问令牌获取异常: {e}")
            return
        
        # 6. 测试完整的飞书同步流程
        print("\n6. 测试完整的飞书同步流程:")
        try:
            # 调用sync_to_feishu方法进行完整同步
            result = cloud_sync.sync_to_feishu(
                sync_data, 
                feishu_config['spreadsheet_token'], 
                feishu_config.get('table_id')
            )
            
            if result:
                print("   ✅ 飞书同步成功")
                print("   - 推文原文内容已成功同步到飞书")
            else:
                print("   ❌ 飞书同步失败")
                
        except Exception as e:
            print(f"   ❌ 飞书同步异常: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n✅ 完整测试完成")

if __name__ == '__main__':
    test_complete_feishu_sync()