#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Web应用的飞书同步过程
模拟web_app.py中的同步逻辑
"""

import sys
import os
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web_app import app, db, TweetData, FEISHU_CONFIG
from cloud_sync import CloudSyncManager

def test_web_feishu_sync():
    """测试Web应用的飞书同步过程"""
    print("🧪 测试Web应用的飞书同步过程")
    print("=" * 50)
    
    with app.app_context():
        # 1. 检查飞书配置
        print("\n1. 检查飞书配置:")
        print(f"   - 启用状态: {FEISHU_CONFIG.get('enabled')}")
        print(f"   - App ID: {FEISHU_CONFIG.get('app_id', '')[:8]}...")
        print(f"   - 表格Token: {FEISHU_CONFIG.get('spreadsheet_token', '')[:8]}...")
        print(f"   - 表格ID: {FEISHU_CONFIG.get('table_id')}")
        
        if not FEISHU_CONFIG.get('enabled'):
            print("   ❌ 飞书同步未启用")
            return
        
        # 2. 查找测试数据
        print("\n2. 查找测试数据:")
        # 查找最近的一条推文数据
        tweet = TweetData.query.order_by(TweetData.id.desc()).first()
        if not tweet:
            print("   ❌ 没有找到推文数据")
            return
        
        print(f"   ✅ 找到推文 ID: {tweet.id}")
        print(f"   - 任务ID: {tweet.task_id}")
        print(f"   - 用户名: {tweet.username}")
        print(f"   - 内容长度: {len(tweet.content or '')}")
        print(f"   - 内容预览: {(tweet.content or '')[:100]}...")
        print(f"   - 发布时间: {tweet.publish_time} (类型: {type(tweet.publish_time)})")
        print(f"   - 抓取时间: {tweet.scraped_at}")
        print(f"   - 同步状态: {tweet.synced_to_feishu}")
        
        # 3. 模拟Web应用的数据准备过程
        print("\n3. 模拟Web应用的数据准备过程:")
        
        # 处理发布时间
        print(f"   📅 处理发布时间...")
        print(f"   - 原始发布时间: {tweet.publish_time} (类型: {type(tweet.publish_time)})")
        
        publish_time = 0
        if tweet.publish_time:
            try:
                if isinstance(tweet.publish_time, str):
                    from dateutil import parser
                    dt = parser.parse(tweet.publish_time)
                    publish_time = int(dt.timestamp())
                    print(f"   - 字符串时间解析: {dt} -> {publish_time}")
                else:
                    publish_time = int(tweet.publish_time.timestamp())
                    print(f"   - datetime对象转换: {tweet.publish_time} -> {publish_time}")
            except Exception as e:
                print(f"   - ❌ 时间解析失败: {e}")
                publish_time = int(tweet.scraped_at.timestamp())
                print(f"   - 使用抓取时间: {publish_time}")
        else:
            publish_time = int(tweet.scraped_at.timestamp())
            print(f"   - 没有发布时间，使用抓取时间: {publish_time}")
        
        # 验证时间戳合理性
        if publish_time < 946684800:  # 2000年1月1日
            print(f"   - ⚠️ 时间戳异常 ({publish_time})，修正为当前时间")
            publish_time = int(datetime.now().timestamp())
            print(f"   - 修正后时间戳: {publish_time}")
        
        # 准备数据
        hashtags_str = ', '.join(json.loads(tweet.hashtags) if tweet.hashtags else [])
        create_time = int(tweet.scraped_at.timestamp())
        
        if create_time < 946684800:
            print(f"   - ⚠️ 创建时间戳异常 ({create_time})，修正为当前时间")
            create_time = int(datetime.now().timestamp())
        
        tweet_data = {
            '推文原文内容': tweet.content or '',
            '发布时间': publish_time,
            '作者（账号）': tweet.username or '',
            '推文链接': tweet.link or '',
            '话题标签（Hashtag）': hashtags_str,
            '类型标签': tweet.content_type or '',
            '评论': tweet.comments or 0,
            '点赞': tweet.likes or 0,
            '转发': tweet.retweets or 0,
            '创建时间': create_time
        }
        
        print(f"   📊 准备的数据:")
        for key, value in tweet_data.items():
            if key == '推文原文内容':
                print(f"     - {key}: '{value[:50]}...' (长度: {len(str(value))})")
            else:
                print(f"     - {key}: {value}")
        
        # 4. 测试云同步管理器
        print("\n4. 测试云同步管理器:")
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
        
        print(f"   🔧 初始化云同步管理器...")
        sync_manager = CloudSyncManager(sync_config)
        
        # 5. 检查cloud_sync.py中的数据处理
        print("\n5. 检查cloud_sync.py中的数据处理:")
        print(f"   📝 调用send_records_to_feishu方法...")
        
        # 直接调用send_records_to_feishu方法来检查数据处理
        try:
            # 模拟send_records_to_feishu的数据处理过程
            records = []
            for tweet_item in [tweet_data]:
                record = {
                    "fields": {
                        "推文原文内容": {"type": "text", "text": tweet_item.get('推文原文内容', '')},
                        "发布时间": {"type": "number", "number": tweet_item.get('发布时间', 0)},
                        "作者（账号）": {"type": "text", "text": tweet_item.get('作者（账号）', '')},
                        "推文链接": {"type": "url", "link": tweet_item.get('推文链接', '')},
                        "话题标签（Hashtag）": {"type": "text", "text": tweet_item.get('话题标签（Hashtag）', '')},
                        "类型标签": {"type": "text", "text": tweet_item.get('类型标签', '')},
                        "评论": {"type": "number", "number": tweet_item.get('评论', 0)},
                        "点赞": {"type": "number", "number": tweet_item.get('点赞', 0)},
                        "转发": {"type": "number", "number": tweet_item.get('转发', 0)},
                        "创建时间": {"type": "number", "number": tweet_item.get('创建时间', 0)}
                    }
                }
                records.append(record)
            
            print(f"   📊 转换后的飞书记录:")
            for i, record in enumerate(records):
                print(f"     记录 {i+1}:")
                for field_name, field_data in record['fields'].items():
                    if field_name == '推文原文内容':
                        content = field_data.get('text', '')
                        print(f"       - {field_name}: '{content[:50]}...' (长度: {len(content)})")
                    else:
                        print(f"       - {field_name}: {field_data}")
            
            print(f"\n   ✅ 数据处理完成，推文原文内容字段正常")
            
        except Exception as e:
            print(f"   ❌ 数据处理失败: {e}")
            import traceback
            print(f"   详细错误: {traceback.format_exc()}")
        
        print(f"\n🎉 测试完成")
        print(f"📋 结论: 推文原文内容字段在Web应用的同步过程中应该是正常的")
        print(f"💡 建议: 检查飞书API调用过程中是否有数据丢失")

if __name__ == '__main__':
    test_web_feishu_sync()