#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试飞书同步功能
绕过HTTP请求，直接在应用上下文中调用同步功能
"""

import json
from datetime import datetime
from web_app import app, db, TweetData, ScrapingTask, FEISHU_CONFIG
from cloud_sync import CloudSyncManager

def classify_content_type(content):
    """简单的内容分类函数"""
    content_lower = content.lower()
    if any(word in content_lower for word in ['money', 'earn', 'profit', 'income', '赚钱', '收入']):
        return '搞钱'
    elif any(word in content_lower for word in ['ad', 'marketing', 'campaign', '广告', '营销']):
        return '投放'
    elif any(word in content_lower for word in ['tip', 'guide', 'how to', '干货', '教程']):
        return '副业干货'
    else:
        return '其他'

def direct_feishu_sync_test():
    """直接测试飞书同步功能"""
    print("🚀 直接飞书同步测试")
    print("=" * 60)
    
    with app.app_context():
        # 1. 检查飞书配置
        print("\n1. 检查飞书配置:")
        print(f"   - 启用状态: {FEISHU_CONFIG.get('enabled')}")
        print(f"   - App ID: {'已配置' if FEISHU_CONFIG.get('app_id') else '未配置'}")
        print(f"   - App Secret: {'已配置' if FEISHU_CONFIG.get('app_secret') else '未配置'}")
        print(f"   - 表格Token: {'已配置' if FEISHU_CONFIG.get('spreadsheet_token') else '未配置'}")
        print(f"   - 表格ID: {'已配置' if FEISHU_CONFIG.get('table_id') else '未配置'}")
        
        if not all([FEISHU_CONFIG.get('enabled'), FEISHU_CONFIG.get('app_id'), 
                   FEISHU_CONFIG.get('app_secret'), FEISHU_CONFIG.get('spreadsheet_token'),
                   FEISHU_CONFIG.get('table_id')]):
            print("❌ 飞书配置不完整，请先配置飞书信息")
            return
        
        # 2. 获取一个任务的未同步推文进行测试
        print("\n2. 获取测试数据:")
        unsynced_tweets = TweetData.query.filter_by(synced_to_feishu=False).limit(5).all()
        
        if not unsynced_tweets:
            print("❌ 没有未同步的推文数据")
            return
        
        print(f"   - 选择 {len(unsynced_tweets)} 条推文进行测试")
        
        # 3. 初始化云同步管理器
        print("\n3. 初始化飞书同步管理器:")
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
        
        try:
            sync_manager = CloudSyncManager(sync_config)
            print("   ✅ 同步管理器初始化成功")
        except Exception as e:
            print(f"   ❌ 同步管理器初始化失败: {e}")
            return
        
        # 4. 准备数据
        print("\n4. 准备同步数据:")
        data = []
        for i, tweet in enumerate(unsynced_tweets, 1):
            print(f"   📝 处理推文 {i}: {tweet.username} - {tweet.content[:30]}...")
            
            # 使用用户设置的类型标签，如果为空则使用自动分类
            content_type = tweet.content_type or classify_content_type(tweet.content)
            
            # 处理发布时间
            publish_time = ''
            if tweet.publish_time:
                try:
                    if isinstance(tweet.publish_time, str):
                        # 如果是字符串，尝试解析为datetime
                        from dateutil import parser
                        dt = parser.parse(tweet.publish_time)
                        publish_time = int(dt.timestamp() * 1000)
                    else:
                        # 如果已经是datetime对象
                        publish_time = int(tweet.publish_time.timestamp() * 1000)
                except Exception as e:
                    print(f"      ⚠️ 时间解析失败: {e}")
                    publish_time = ''
            
            tweet_data = {
                '推文原文内容': tweet.content,
                '发布时间': publish_time,
                '作者（账号）': tweet.username,
                '推文链接': tweet.link or '',
                '话题标签（Hashtag）': ', '.join(json.loads(tweet.hashtags) if tweet.hashtags else []),
                '类型标签': content_type,
                '评论': 0,  # Twitter API限制，暂时设为0
                '点赞': tweet.likes,
                '转发': tweet.retweets,
                '创建时间': int(tweet.scraped_at.timestamp() * 1000)
            }
            data.append(tweet_data)
        
        print(f"   ✅ 准备了 {len(data)} 条数据")
        
        # 5. 执行同步
        print("\n5. 执行飞书同步:")
        try:
            success = sync_manager.sync_to_feishu(
                data,
                FEISHU_CONFIG['spreadsheet_token'],
                FEISHU_CONFIG['table_id']
            )
            
            if success:
                print("   ✅ 飞书同步成功")
                
                # 更新数据库中的同步状态
                print("\n6. 更新数据库同步状态:")
                for tweet in unsynced_tweets:
                    tweet.synced_to_feishu = True
                    tweet.content_type = classify_content_type(tweet.content)
                
                db.session.commit()
                print(f"   ✅ 已更新 {len(unsynced_tweets)} 条推文的同步状态")
                
                # 验证结果
                print("\n7. 验证同步结果:")
                total_tweets = TweetData.query.count()
                synced_tweets = TweetData.query.filter_by(synced_to_feishu=True).count()
                unsynced_count = TweetData.query.filter_by(synced_to_feishu=False).count()
                
                print(f"   - 总推文数: {total_tweets}")
                print(f"   - 已同步: {synced_tweets}")
                print(f"   - 未同步: {unsynced_count}")
                
                print("\n🎉 飞书同步测试成功！")
                
            else:
                print("   ❌ 飞书同步失败")
                
        except Exception as e:
            print(f"   ❌ 飞书同步异常: {e}")
            import traceback
            print(f"   详细错误: {traceback.format_exc()}")

if __name__ == '__main__':
    direct_feishu_sync_test()