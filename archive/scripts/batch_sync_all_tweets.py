#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量同步所有未同步推文到飞书
分批处理，避免API限制
"""

import json
import time
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

def batch_sync_all_tweets():
    """批量同步所有未同步推文到飞书"""
    print("🚀 批量同步所有推文到飞书")
    print("=" * 60)
    
    with app.app_context():
        # 1. 检查飞书配置
        print("\n1. 检查飞书配置:")
        if not all([FEISHU_CONFIG.get('enabled'), FEISHU_CONFIG.get('app_id'), 
                   FEISHU_CONFIG.get('app_secret'), FEISHU_CONFIG.get('spreadsheet_token'),
                   FEISHU_CONFIG.get('table_id')]):
            print("❌ 飞书配置不完整，请先配置飞书信息")
            return
        print("   ✅ 飞书配置完整")
        
        # 2. 获取所有未同步推文
        print("\n2. 获取未同步推文:")
        unsynced_tweets = TweetData.query.filter_by(synced_to_feishu=False).all()
        total_tweets = TweetData.query.count()
        synced_tweets = TweetData.query.filter_by(synced_to_feishu=True).count()
        
        print(f"   - 总推文数: {total_tweets}")
        print(f"   - 已同步: {synced_tweets}")
        print(f"   - 未同步: {len(unsynced_tweets)}")
        
        if not unsynced_tweets:
            print("✅ 所有推文都已同步到飞书")
            return
        
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
        
        # 4. 分批同步
        print("\n4. 开始分批同步:")
        batch_size = 20  # 每批20条，避免API限制
        total_batches = (len(unsynced_tweets) + batch_size - 1) // batch_size
        success_count = 0
        failed_count = 0
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(unsynced_tweets))
            batch_tweets = unsynced_tweets[start_idx:end_idx]
            
            print(f"\n   📦 批次 {batch_num + 1}/{total_batches} (推文 {start_idx + 1}-{end_idx}):")
            
            # 准备批次数据
            batch_data = []
            for tweet in batch_tweets:
                # 使用用户设置的类型标签，如果为空则使用自动分类
                content_type = tweet.content_type or classify_content_type(tweet.content)
                
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
                
                tweet_data = {
                    '推文原文内容': tweet.content,
                    '发布时间': publish_time,
                    '作者（账号）': tweet.username,
                    '推文链接': tweet.link or '',
                    '话题标签（Hashtag）': ', '.join(json.loads(tweet.hashtags) if tweet.hashtags else []),
                    '类型标签': content_type,
                    '评论': 0,
                    '点赞': tweet.likes,
                    '转发': tweet.retweets,
                    '创建时间': int(tweet.scraped_at.timestamp() * 1000)
                }
                batch_data.append(tweet_data)
            
            # 执行批次同步
            try:
                print(f"      🔄 同步 {len(batch_data)} 条推文...")
                success = sync_manager.sync_to_feishu(
                    batch_data,
                    FEISHU_CONFIG['spreadsheet_token'],
                    FEISHU_CONFIG['table_id']
                )
                
                if success:
                    print(f"      ✅ 批次同步成功")
                    
                    # 更新数据库中的同步状态
                    for tweet in batch_tweets:
                        tweet.synced_to_feishu = True
                        tweet.content_type = classify_content_type(tweet.content)
                    
                    db.session.commit()
                    success_count += len(batch_tweets)
                    print(f"      ✅ 已更新 {len(batch_tweets)} 条推文的同步状态")
                    
                else:
                    print(f"      ❌ 批次同步失败")
                    failed_count += len(batch_tweets)
                    
            except Exception as e:
                print(f"      ❌ 批次同步异常: {e}")
                failed_count += len(batch_tweets)
            
            # 批次间延迟，避免API限制
            if batch_num < total_batches - 1:
                print(f"      ⏳ 等待 2 秒后处理下一批次...")
                time.sleep(2)
        
        # 5. 同步结果统计
        print("\n" + "=" * 60)
        print("📊 批量同步结果统计:")
        print(f"   - 成功同步: {success_count} 条")
        print(f"   - 同步失败: {failed_count} 条")
        print(f"   - 总计处理: {success_count + failed_count} 条")
        
        # 6. 最终验证
        print("\n6. 最终验证同步状态:")
        final_total = TweetData.query.count()
        final_synced = TweetData.query.filter_by(synced_to_feishu=True).count()
        final_unsynced = TweetData.query.filter_by(synced_to_feishu=False).count()
        
        print(f"   - 总推文数: {final_total}")
        print(f"   - 已同步: {final_synced}")
        print(f"   - 未同步: {final_unsynced}")
        
        if final_unsynced == 0:
            print("\n🎉 所有推文已成功同步到飞书！")
        else:
            print(f"\n⚠️ 还有 {final_unsynced} 条推文未同步")
            
        sync_rate = (final_synced / final_total) * 100 if final_total > 0 else 0
        print(f"   - 同步率: {sync_rate:.1f}%")

if __name__ == '__main__':
    batch_sync_all_tweets()