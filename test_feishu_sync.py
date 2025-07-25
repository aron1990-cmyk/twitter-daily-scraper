#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试飞书同步功能
验证字段映射修复是否有效
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_app import app, db, TweetData, FEISHU_CONFIG
from cloud_sync import CloudSyncManager
import json

def test_feishu_sync():
    """测试飞书同步功能"""
    print("🧪 测试飞书同步功能")
    print("=" * 50)
    
    with app.app_context():
        try:
            # 获取一些未同步的推文进行测试
            test_tweets = TweetData.query.filter_by(synced_to_feishu=False).limit(10).all()
            
            if not test_tweets:
                print("⚠️ 没有找到未同步的推文，请先重置同步状态")
                return
            
            print(f"📊 找到 {len(test_tweets)} 条未同步推文用于测试")
            
            for i, tweet in enumerate(test_tweets, 1):
                print(f"\n🔄 测试推文 {i}/{len(test_tweets)}")
                print(f"   - ID: {tweet.id}")
                print(f"   - 任务ID: {tweet.task_id}")
                print(f"   - 内容: {tweet.content[:50]}...")
                print(f"   - 作者: {tweet.username}")
                
                # 准备推文数据（模拟web_app.py中的数据准备逻辑）
                # 处理发布时间
                publish_time_str = ''
                if tweet.publish_time:
                    if hasattr(tweet.publish_time, 'strftime'):
                        publish_time_str = tweet.publish_time.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        publish_time_str = str(tweet.publish_time)
                
                # 处理创建时间
                scraped_at_str = ''
                if tweet.scraped_at:
                    if hasattr(tweet.scraped_at, 'strftime'):
                        scraped_at_str = tweet.scraped_at.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        scraped_at_str = str(tweet.scraped_at)
                
                tweet_data = {
                    '推文原文内容': tweet.content or '',
                    '发布时间': publish_time_str,
                    '作者（账号）': tweet.username or '',
                    '推文链接': tweet.link or '',
                    '话题标签（Hashtag）': tweet.hashtags or '',
                    '类型标签': tweet.content_type or '',
                    '评论': str(tweet.comments) if tweet.comments is not None else '0',
                    '点赞': str(tweet.likes) if tweet.likes is not None else '0',
                    '转发': str(tweet.retweets) if tweet.retweets is not None else '0',
                    '创建时间': scraped_at_str
                }
                
                print(f"   - 准备的数据字段: {list(tweet_data.keys())}")
                
                # 测试同步
                try:
                    # 创建CloudSyncManager实例
                    feishu_sync_config = {
                        'feishu': {
                            'app_id': FEISHU_CONFIG.get('app_id'),
                            'app_secret': FEISHU_CONFIG.get('app_secret'),
                            'base_url': 'https://open.feishu.cn/open-apis'
                        }
                    }
                    
                    cloud_sync = CloudSyncManager(feishu_sync_config)
                    
                    # 执行同步
                    success = cloud_sync.sync_to_feishu(
                        [tweet_data],
                        spreadsheet_token=FEISHU_CONFIG.get('spreadsheet_token'),
                        table_id=FEISHU_CONFIG.get('table_id')
                    )
                    
                    if success:
                        print(f"   ✅ 同步成功")
                        
                        # 更新数据库中的同步状态
                        tweet.synced_to_feishu = True
                        db.session.commit()
                        print(f"   ✅ 数据库状态已更新")
                        
                    else:
                        print(f"   ❌ 同步失败")
                        
                except Exception as e:
                    print(f"   ❌ 同步过程中发生异常: {e}")
                    import traceback
                    print(f"   📝 异常详情: {traceback.format_exc()}")
                
                print(f"   {'='*40}")
            
            # 显示测试结果统计
            print(f"\n📊 测试完成统计")
            synced_count = TweetData.query.filter_by(synced_to_feishu=True).count()
            total_count = TweetData.query.count()
            print(f"   - 总推文数: {total_count}")
            print(f"   - 已同步数: {synced_count}")
            print(f"   - 未同步数: {total_count - synced_count}")
            print(f"   - 同步率: {(synced_count/total_count*100):.1f}%")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")
            import traceback
            print(f"   - 错误详情: {traceback.format_exc()}")

if __name__ == '__main__':
    test_feishu_sync()