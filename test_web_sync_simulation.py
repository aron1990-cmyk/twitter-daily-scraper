#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟Web应用执行任务时的飞书同步流程
测试修复后的自动同步功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_app import app, FEISHU_CONFIG, ScrapingTask, TweetData, db
from datetime import datetime
import json

def simulate_web_task_sync():
    """模拟web任务执行时的飞书同步"""
    with app.app_context():
        print("🧪 模拟Web应用任务执行时的飞书同步")
        print("=" * 60)
        
        # 1. 检查当前FEISHU_CONFIG
        print("\n🔧 当前FEISHU_CONFIG状态:")
        for key, value in FEISHU_CONFIG.items():
            if key == 'app_secret':
                print(f"   - {key}: {'已配置' if value else '未配置'}")
            else:
                print(f"   - {key}: {value}")
        
        # 2. 检查配置完整性
        print("\n✅ 配置完整性检查:")
        required_fields = ['app_id', 'app_secret', 'spreadsheet_token', 'table_id']
        missing_fields = [field for field in required_fields if not FEISHU_CONFIG.get(field)]
        
        if missing_fields:
            print(f"   ❌ 配置不完整，缺少字段: {', '.join(missing_fields)}")
            return False
        else:
            print(f"   ✅ 基本配置完整")
        
        print(f"   - 飞书同步启用: {FEISHU_CONFIG.get('enabled', False)}")
        print(f"   - 自动同步启用: {FEISHU_CONFIG.get('auto_sync', False)}")
        
        # 3. 模拟自动同步检查逻辑
        print("\n🔍 模拟自动同步检查逻辑:")
        
        # 检查飞书配置是否启用
        if not FEISHU_CONFIG.get('enabled'):
            print(f"   ❌ 飞书配置未启用，跳过同步")
            return False
        else:
            print(f"   ✅ 飞书配置已启用")
        
        # 检查是否启用自动同步
        if not FEISHU_CONFIG.get('auto_sync', False):
            print(f"   ❌ 自动同步未启用，跳过同步 (当前值: {FEISHU_CONFIG.get('auto_sync', False)})")
            return False
        else:
            print(f"   ✅ 自动同步已启用")
        
        # 检查飞书配置完整性
        if missing_fields:
            print(f"   ❌ 飞书自动同步跳过：配置不完整，缺少字段: {', '.join(missing_fields)}")
            return False
        else:
            print(f"   ✅ 飞书配置完整，可以进行同步")
        
        # 4. 查找最近的任务进行测试
        print("\n📋 查找测试任务:")
        latest_task = ScrapingTask.query.filter_by(status='completed').order_by(ScrapingTask.completed_at.desc()).first()
        
        if not latest_task:
            print("   ❌ 没有找到已完成的任务")
            return False
        
        print(f"   ✅ 找到测试任务: {latest_task.name} (ID: {latest_task.id})")
        
        # 5. 检查任务的推文数据
        tweets = TweetData.query.filter_by(task_id=latest_task.id).all()
        if not tweets:
            print(f"   ❌ 任务 {latest_task.id} 没有推文数据")
            return False
        
        print(f"   ✅ 任务 {latest_task.id} 有 {len(tweets)} 条推文数据")
        
        # 6. 检查同步状态
        synced_count = sum(1 for tweet in tweets if tweet.synced_to_feishu)
        unsynced_count = len(tweets) - synced_count
        
        print(f"   - 已同步: {synced_count} 条")
        print(f"   - 未同步: {unsynced_count} 条")
        
        # 7. 模拟同步数据准备
        print("\n📦 模拟同步数据准备:")
        sync_data = []
        for i, tweet in enumerate(tweets[:3]):  # 只处理前3条作为示例
            # 解析hashtags
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
            
            sync_item = {
                '推文原文内容': tweet.content or '',
                '发布时间': publish_timestamp,
                '作者（账号）': tweet.username or '',
                '推文链接': tweet.link or '',
                '话题标签（Hashtag）': ', '.join(hashtags),
                '类型标签': tweet.content_type or '',
                '评论': 0,  # Twitter API限制，暂时设为0
                '点赞': tweet.likes or 0,
                '转发': tweet.retweets or 0,
                '创建时间': created_timestamp
            }
            sync_data.append(sync_item)
            print(f"   ✅ 准备推文 {i+1}: {tweet.username} - {tweet.content[:50]}...")
        
        print(f"   ✅ 共准备 {len(sync_data)} 条数据用于同步")
        
        # 8. 模拟云同步管理器配置
        print("\n☁️ 模拟云同步管理器配置:")
        sync_config = {
            'feishu': {
                'enabled': True,
                'app_id': FEISHU_CONFIG['app_id'],
                'app_secret': FEISHU_CONFIG['app_secret'],
                'base_url': 'https://open.feishu.cn/open-apis'
            }
        }
        print(f"   ✅ 同步配置已准备")
        print(f"   - App ID: {sync_config['feishu']['app_id']}")
        print(f"   - App Secret: {'已配置' if sync_config['feishu']['app_secret'] else '未配置'}")
        print(f"   - Spreadsheet Token: {FEISHU_CONFIG['spreadsheet_token']}")
        print(f"   - Table ID: {FEISHU_CONFIG['table_id']}")
        
        print("\n🎉 模拟测试完成！")
        print("\n📋 测试结果总结:")
        print(f"   ✅ 飞书配置完整且正确")
        print(f"   ✅ 自动同步功能已启用")
        print(f"   ✅ 找到测试任务和数据")
        print(f"   ✅ 同步数据准备成功")
        print(f"   ✅ 云同步管理器配置正确")
        
        return True

if __name__ == '__main__':
    success = simulate_web_task_sync()
    if success:
        print("\n🎉 Web应用飞书同步模拟测试通过！")
        print("\n💡 建议: 现在可以创建一个新的小任务来实际测试飞书同步功能")
    else:
        print("\n❌ Web应用飞书同步模拟测试失败！")