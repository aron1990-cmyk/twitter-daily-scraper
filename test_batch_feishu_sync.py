#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量测试飞书同步功能
将所有未同步的推文数据同步到飞书
"""

import requests
import json
from web_app import app, db, TweetData, ScrapingTask, FEISHU_CONFIG

def test_batch_feishu_sync():
    """批量测试飞书同步功能"""
    print("🚀 开始批量飞书同步测试")
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
        
        # 2. 获取所有未同步的推文
        print("\n2. 获取未同步推文数据:")
        unsynced_tweets = TweetData.query.filter_by(synced_to_feishu=False).all()
        total_tweets = TweetData.query.count()
        synced_tweets = TweetData.query.filter_by(synced_to_feishu=True).count()
        
        print(f"   - 总推文数: {total_tweets}")
        print(f"   - 已同步: {synced_tweets}")
        print(f"   - 未同步: {len(unsynced_tweets)}")
        
        if not unsynced_tweets:
            print("✅ 所有推文都已同步到飞书")
            return
        
        # 3. 按任务分组同步
        print("\n3. 按任务分组同步:")
        task_groups = {}
        for tweet in unsynced_tweets:
            if tweet.task_id not in task_groups:
                task_groups[tweet.task_id] = []
            task_groups[tweet.task_id].append(tweet)
        
        print(f"   - 涉及任务数: {len(task_groups)}")
        
        # 4. 逐个任务同步
        success_count = 0
        failed_count = 0
        
        for task_id, tweets in task_groups.items():
            task = ScrapingTask.query.get(task_id)
            task_name = task.name if task else f"任务{task_id}"
            
            print(f"\n   📋 同步任务: {task_name} (ID: {task_id})")
            print(f"      - 推文数量: {len(tweets)}")
            
            try:
                # 调用web API进行同步
                response = requests.post(
                    f'http://localhost:5000/api/data/sync_feishu/{task_id}',
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        print(f"      ✅ 同步成功: {result.get('message')}")
                        success_count += len(tweets)
                    else:
                        print(f"      ❌ 同步失败: {result.get('error')}")
                        failed_count += len(tweets)
                else:
                    print(f"      ❌ HTTP错误: {response.status_code}")
                    failed_count += len(tweets)
                    
            except Exception as e:
                print(f"      ❌ 同步异常: {e}")
                failed_count += len(tweets)
        
        # 5. 同步结果统计
        print("\n" + "=" * 60)
        print("📊 同步结果统计:")
        print(f"   - 成功同步: {success_count} 条")
        print(f"   - 同步失败: {failed_count} 条")
        print(f"   - 总计处理: {success_count + failed_count} 条")
        
        # 6. 验证同步状态
        print("\n6. 验证同步状态:")
        final_unsynced = TweetData.query.filter_by(synced_to_feishu=False).count()
        final_synced = TweetData.query.filter_by(synced_to_feishu=True).count()
        
        print(f"   - 最终已同步: {final_synced}")
        print(f"   - 最终未同步: {final_unsynced}")
        
        if final_unsynced == 0:
            print("\n🎉 所有推文已成功同步到飞书！")
        else:
            print(f"\n⚠️ 还有 {final_unsynced} 条推文未同步")

if __name__ == '__main__':
    test_batch_feishu_sync()