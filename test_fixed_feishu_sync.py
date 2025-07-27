#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的飞书同步功能
验证推文原文内容字段能正确同步
"""

import os
import sys
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web_app import app, db, TweetData, ScrapingTask, FEISHU_CONFIG
from cloud_sync import CloudSyncManager

def test_fixed_feishu_sync():
    """测试修复后的飞书同步功能"""
    print("🧪 测试修复后的飞书同步功能")
    print("=" * 50)
    
    with app.app_context():
        # 1. 检查飞书配置
        print("\n1. 检查飞书配置:")
        if not FEISHU_CONFIG.get('enabled'):
            print("   ❌ 飞书同步未启用")
            return
        
        required_fields = ['app_id', 'app_secret', 'spreadsheet_token', 'table_id']
        missing_fields = [field for field in required_fields if not FEISHU_CONFIG.get(field)]
        if missing_fields:
            print(f"   ❌ 飞书配置不完整，缺少字段: {missing_fields}")
            return
        
        print("   ✅ 飞书配置完整")
        print(f"   📋 表格Token: {FEISHU_CONFIG['spreadsheet_token'][:10]}...")
        print(f"   📊 表格ID: {FEISHU_CONFIG['table_id'][:10]}...")
        
        # 2. 获取测试推文数据
        print("\n2. 获取测试推文数据:")
        test_tweet = TweetData.query.filter(
            TweetData.content.isnot(None),
            TweetData.content != ''
        ).first()
        
        if not test_tweet:
            print("   ❌ 没有找到有内容的推文数据")
            return
        
        print(f"   ✅ 找到测试推文: ID={test_tweet.id}")
        print(f"   📝 推文内容长度: {len(test_tweet.content)}")
        print(f"   📝 推文内容预览: {test_tweet.content[:100]}...")
        print(f"   👤 作者: {test_tweet.username}")
        print(f"   🔗 链接: {test_tweet.link}")
        
        # 3. 准备同步数据（模拟web_app.py的数据准备过程）
        print("\n3. 准备同步数据:")
        
        # 处理发布时间
        if isinstance(test_tweet.publish_time, str):
            try:
                publish_time_dt = datetime.fromisoformat(test_tweet.publish_time.replace('Z', '+00:00'))
                publish_time = int(publish_time_dt.timestamp())
            except:
                publish_time = int(datetime.now().timestamp())
        elif hasattr(test_tweet.publish_time, 'timestamp'):
            publish_time = int(test_tweet.publish_time.timestamp())
        else:
            publish_time = int(datetime.now().timestamp())
        
        # 修正1970年问题
        if publish_time < 946684800:  # 2000年1月1日
            publish_time = int(datetime.now().timestamp())
        
        # 处理创建时间（使用scraped_at字段）
        if hasattr(test_tweet, 'scraped_at') and test_tweet.scraped_at:
            if isinstance(test_tweet.scraped_at, str):
                try:
                    create_time_dt = datetime.fromisoformat(test_tweet.scraped_at.replace('Z', '+00:00'))
                    create_time = int(create_time_dt.timestamp())
                except:
                    create_time = int(datetime.now().timestamp())
            elif hasattr(test_tweet.scraped_at, 'timestamp'):
                create_time = int(test_tweet.scraped_at.timestamp())
            else:
                create_time = int(datetime.now().timestamp())
        else:
            create_time = int(datetime.now().timestamp())
        
        # 修正1970年问题
        if create_time < 946684800:  # 2000年1月1日
            create_time = int(datetime.now().timestamp())
        
        # 构建同步数据
        sync_data = [{
            '推文原文内容': test_tweet.content,
            '作者（账号）': test_tweet.username or '',
            '推文链接': test_tweet.link or '',
            '话题标签（Hashtag）': test_tweet.hashtags or '',
            '类型标签': test_tweet.content_type or '',
            '评论': test_tweet.comments or 0,
            '转发': test_tweet.retweets or 0,
            '点赞': test_tweet.likes or 0,
            '发布时间': publish_time,
            '创建时间': create_time
        }]
        
        print(f"   ✅ 同步数据准备完成")
        print(f"   📊 数据条数: {len(sync_data)}")
        print(f"   📝 推文原文内容: {sync_data[0]['推文原文内容'][:100]}...")
        print(f"   👤 作者: {sync_data[0]['作者（账号）']}")
        print(f"   🕐 发布时间: {sync_data[0]['发布时间']} ({datetime.fromtimestamp(sync_data[0]['发布时间'])})")
        
        # 4. 初始化云同步管理器
        print("\n4. 初始化云同步管理器:")
        sync_config = {
            'feishu': {
                'app_id': FEISHU_CONFIG['app_id'],
                'app_secret': FEISHU_CONFIG['app_secret'],
                'base_url': 'https://open.feishu.cn/open-apis'
            }
        }
        
        sync_manager = CloudSyncManager(sync_config)
        print("   ✅ 云同步管理器初始化成功")
        
        # 5. 执行飞书同步
        print("\n5. 执行飞书同步:")
        try:
            success = sync_manager.sync_to_feishu(
                sync_data,
                FEISHU_CONFIG['spreadsheet_token'],
                FEISHU_CONFIG['table_id']
            )
            
            if success:
                print("   ✅ 飞书同步成功！")
                print("   🎉 推文原文内容已成功同步到飞书")
            else:
                print("   ❌ 飞书同步失败")
                
        except Exception as e:
            print(f"   ❌ 飞书同步异常: {e}")
            import traceback
            print(f"   📋 异常详情: {traceback.format_exc()}")
        
        print("\n" + "=" * 50)
        print("🏁 测试完成")

if __name__ == '__main__':
    test_fixed_feishu_sync()