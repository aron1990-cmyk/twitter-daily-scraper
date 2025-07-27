#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细对比任务完成后自动同步和API手动同步的差异
分析为什么会出现不同的结果
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_app import app, FEISHU_CONFIG, ScrapingTask, TweetData, db
from cloud_sync import CloudSyncManager
from datetime import datetime
import json

def analyze_sync_methods():
    """分析两种同步方式的差异"""
    print("🔍 分析任务完成后自动同步 vs API手动同步的差异")
    print("=" * 60)
    
    with app.app_context():
        # 获取任务28的数据作为测试
        task_id = 28
        tweets = TweetData.query.filter_by(task_id=task_id).all()
        
        if not tweets:
            print(f"❌ 任务 {task_id} 没有数据")
            return
        
        print(f"📊 任务 {task_id} 共有 {len(tweets)} 条推文数据")
        
        # 模拟自动同步的数据处理方式
        print("\n🤖 模拟自动同步数据处理方式:")
        print("-" * 40)
        
        auto_sync_data = []
        for i, tweet in enumerate(tweets[:3]):  # 只处理前3条作为示例
            # 解析hashtags
            try:
                hashtags = json.loads(tweet.hashtags) if tweet.hashtags else []
            except:
                hashtags = []
            
            data_item = {
                '推文原文内容': tweet.content or '',
                '作者（账号）': tweet.username or '',
                '推文链接': tweet.link or '',
                '话题标签（Hashtag）': ', '.join(hashtags),
                '类型标签': tweet.content_type or '',
                '评论': tweet.comments or 0,
                '点赞': tweet.likes or 0,
                '转发': tweet.retweets or 0
            }
            
            auto_sync_data.append(data_item)
            
            print(f"推文 {i+1} (ID: {tweet.id}):")
            print(f"  - 内容: {(tweet.content or '')[:50]}...")
            print(f"  - 作者: {tweet.username or ''}")
            print(f"  - 点赞: {tweet.likes or 0}")
            print(f"  - 转发: {tweet.retweets or 0}")
            print(f"  - 评论: {tweet.comments or 0}")
            print(f"  - 类型标签: {tweet.content_type or ''}")
            print(f"  - 话题标签: {', '.join(hashtags)}")
            print()
        
        # 模拟API同步的数据处理方式
        print("\n🌐 模拟API同步数据处理方式:")
        print("-" * 40)
        
        api_sync_data = []
        for i, tweet in enumerate(tweets[:3]):  # 只处理前3条作为示例
            # 使用用户设置的类型标签，如果为空则使用自动分类
            from web_app import classify_content_type
            content_type = tweet.content_type or classify_content_type(tweet.content)
            
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
                    publish_time = int(tweet.scraped_at.timestamp())
            else:
                publish_time = int(tweet.scraped_at.timestamp())
            
            # 验证时间戳合理性
            if publish_time < 946684800:  # 2000年1月1日的时间戳
                publish_time = int(datetime.now().timestamp())
            
            hashtags_str = ', '.join(json.loads(tweet.hashtags) if tweet.hashtags else [])
            
            # 转换为毫秒级时间戳
            if publish_time < 10000000000:  # 秒级时间戳
                publish_time_ms = publish_time * 1000
            else:  # 已经是毫秒级
                publish_time_ms = publish_time
            
            data_item = {
                '推文原文内容': tweet.content or '',
                '作者（账号）': tweet.username or '',
                '推文链接': tweet.link or '',
                '话题标签（Hashtag）': hashtags_str,
                '类型标签': content_type or '',
                '评论': tweet.comments or 0,
                '点赞': tweet.likes or 0,
                '转发': tweet.retweets or 0
            }
            
            api_sync_data.append(data_item)
            
            print(f"推文 {i+1} (ID: {tweet.id}):")
            print(f"  - 内容: {(tweet.content or '')[:50]}...")
            print(f"  - 作者: {tweet.username or ''}")
            print(f"  - 点赞: {tweet.likes or 0}")
            print(f"  - 转发: {tweet.retweets or 0}")
            print(f"  - 评论: {tweet.comments or 0}")
            print(f"  - 类型标签: {content_type or ''}")
            print(f"  - 话题标签: {hashtags_str}")
            print(f"  - 发布时间戳: {publish_time} -> {publish_time_ms} (毫秒级)")
            print()
        
        # 对比两种方式的差异
        print("\n🔍 对比两种同步方式的差异:")
        print("=" * 40)
        
        differences_found = False
        
        for i in range(min(len(auto_sync_data), len(api_sync_data))):
            auto_item = auto_sync_data[i]
            api_item = api_sync_data[i]
            
            print(f"\n推文 {i+1} 对比:")
            
            for key in auto_item.keys():
                auto_value = auto_item[key]
                api_value = api_item[key]
                
                if auto_value != api_value:
                    differences_found = True
                    print(f"  ❌ {key}:")
                    print(f"     自动同步: {auto_value}")
                    print(f"     API同步:  {api_value}")
                else:
                    print(f"  ✅ {key}: {auto_value}")
        
        # 检查CloudSyncManager的初始化方式差异
        print("\n🔧 CloudSyncManager初始化方式对比:")
        print("-" * 40)
        
        print("自动同步初始化方式:")
        auto_sync_config = {
            'feishu': {
                'enabled': True,
                'app_id': FEISHU_CONFIG['app_id'],
                'app_secret': FEISHU_CONFIG['app_secret'],
                'base_url': 'https://open.feishu.cn/open-apis'
            }
        }
        print(f"  配置: {auto_sync_config}")
        print(f"  初始化: CloudSyncManager(sync_config)")
        print(f"  设置飞书: sync_manager.setup_feishu(app_id, app_secret)")
        
        print("\nAPI同步初始化方式:")
        api_sync_config = {
            'feishu': {
                'enabled': True,
                'app_id': FEISHU_CONFIG['app_id'],
                'app_secret': FEISHU_CONFIG['app_secret'],
                'spreadsheet_token': FEISHU_CONFIG['spreadsheet_token'],
                'table_id': FEISHU_CONFIG['table_id'],
                'base_url': 'https://open.feishu.cn/open-apis'
            }
        }
        print(f"  配置: {api_sync_config}")
        print(f"  初始化: CloudSyncManager(sync_config)")
        print(f"  无需额外设置")
        
        # 关键差异分析
        print("\n🎯 关键差异分析:")
        print("=" * 40)
        
        print("1. 初始化方式差异:")
        print("   - 自动同步: 先创建CloudSyncManager，再调用setup_feishu()")
        print("   - API同步: 直接在配置中包含所有参数")
        
        print("\n2. 数据处理差异:")
        if differences_found:
            print("   - 发现数据处理差异，详见上方对比")
        else:
            print("   - 数据处理方式基本一致")
        
        print("\n3. 可能的问题原因:")
        print("   - setup_feishu()方法可能影响后续的同步行为")
        print("   - 两种初始化方式可能导致不同的内部状态")
        print("   - 需要检查CloudSyncManager的setup_feishu()实现")
        
        return differences_found

def test_cloud_sync_manager_behavior():
    """测试CloudSyncManager的不同初始化方式"""
    print("\n🧪 测试CloudSyncManager的不同初始化方式")
    print("=" * 60)
    
    # 方式1: 自动同步的方式
    print("\n🤖 测试自动同步的初始化方式:")
    sync_config1 = {
        'feishu': {
            'enabled': True,
            'app_id': FEISHU_CONFIG['app_id'],
            'app_secret': FEISHU_CONFIG['app_secret'],
            'base_url': 'https://open.feishu.cn/open-apis'
        }
    }
    
    try:
        sync_manager1 = CloudSyncManager(sync_config1)
        setup_result = sync_manager1.setup_feishu(FEISHU_CONFIG['app_id'], FEISHU_CONFIG['app_secret'])
        print(f"  - CloudSyncManager创建: 成功")
        print(f"  - setup_feishu结果: {setup_result}")
        print(f"  - 内部状态检查...")
        
        # 检查内部状态
        if hasattr(sync_manager1, 'feishu_config'):
            print(f"  - feishu_config: {sync_manager1.feishu_config}")
        if hasattr(sync_manager1, 'access_token'):
            print(f"  - access_token: {'已设置' if sync_manager1.access_token else '未设置'}")
            
    except Exception as e:
        print(f"  - 错误: {e}")
    
    # 方式2: API同步的方式
    print("\n🌐 测试API同步的初始化方式:")
    sync_config2 = {
        'feishu': {
            'enabled': True,
            'app_id': FEISHU_CONFIG['app_id'],
            'app_secret': FEISHU_CONFIG['app_secret'],
            'spreadsheet_token': FEISHU_CONFIG['spreadsheet_token'],
            'table_id': FEISHU_CONFIG['table_id'],
            'base_url': 'https://open.feishu.cn/open-apis'
        }
    }
    
    try:
        sync_manager2 = CloudSyncManager(sync_config2)
        print(f"  - CloudSyncManager创建: 成功")
        print(f"  - 无需setup_feishu")
        print(f"  - 内部状态检查...")
        
        # 检查内部状态
        if hasattr(sync_manager2, 'feishu_config'):
            print(f"  - feishu_config: {sync_manager2.feishu_config}")
        if hasattr(sync_manager2, 'access_token'):
            print(f"  - access_token: {'已设置' if sync_manager2.access_token else '未设置'}")
            
    except Exception as e:
        print(f"  - 错误: {e}")

if __name__ == '__main__':
    print("🔍 开始分析飞书同步方式差异")
    print("=" * 60)
    
    # 分析同步方法差异
    differences_found = analyze_sync_methods()
    
    # 测试CloudSyncManager行为
    test_cloud_sync_manager_behavior()
    
    print("\n📋 总结:")
    print("=" * 60)
    if differences_found:
        print("❌ 发现两种同步方式存在差异")
        print("💡 建议统一两种同步方式的实现")
    else:
        print("✅ 两种同步方式的数据处理基本一致")
        print("🔍 问题可能在CloudSyncManager的初始化或内部逻辑")
    
    print("\n🎯 下一步建议:")
    print("1. 检查CloudSyncManager的setup_feishu()方法实现")
    print("2. 统一两种同步方式的初始化逻辑")
    print("3. 确保数据处理的一致性")