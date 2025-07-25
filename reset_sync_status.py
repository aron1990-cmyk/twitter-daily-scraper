#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重置飞书同步状态
用于重新测试同步功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_app import app, db, TweetData
from sqlalchemy import text

def reset_sync_status(task_id=None):
    """重置飞书同步状态"""
    print("🔄 重置飞书同步状态")
    print("=" * 50)
    
    with app.app_context():
        try:
            if task_id:
                # 重置指定任务的同步状态
                tweets = TweetData.query.filter_by(task_id=task_id).all()
                print(f"📊 找到任务 {task_id} 的推文数量: {len(tweets)}")
            else:
                # 重置所有推文的同步状态
                tweets = TweetData.query.all()
                print(f"📊 找到所有推文数量: {len(tweets)}")
            
            if not tweets:
                print("⚠️ 没有找到需要重置的推文")
                return
            
            # 统计当前同步状态
            synced_count = sum(1 for tweet in tweets if tweet.synced_to_feishu)
            unsynced_count = len(tweets) - synced_count
            
            print(f"📈 当前同步状态:")
            print(f"   - 已同步: {synced_count}")
            print(f"   - 未同步: {unsynced_count}")
            
            if synced_count == 0:
                print("ℹ️ 所有推文都未同步，无需重置")
                return
        
            # 确认重置操作
            if task_id:
                confirm = input(f"\n❓ 确认重置任务 {task_id} 的 {synced_count} 条已同步推文状态？(y/N): ")
            else:
                confirm = input(f"\n❓ 确认重置所有 {synced_count} 条已同步推文状态？(y/N): ")
            
            if confirm.lower() != 'y':
                print("❌ 操作已取消")
                return
            
            # 执行重置
            print("\n🔄 开始重置同步状态...")
            reset_count = 0
            
            for tweet in tweets:
                if tweet.synced_to_feishu:
                    tweet.synced_to_feishu = False
                    reset_count += 1
            
            # 提交更改
            db.session.commit()
            
            print(f"✅ 重置完成!")
            print(f"   - 重置数量: {reset_count}")
            print(f"   - 现在所有推文都可以重新同步到飞书")
            
            # 显示重置后的状态
            if task_id:
                remaining_synced = TweetData.query.filter_by(task_id=task_id, synced_to_feishu=True).count()
                total_tweets = TweetData.query.filter_by(task_id=task_id).count()
            else:
                remaining_synced = TweetData.query.filter_by(synced_to_feishu=True).count()
                total_tweets = TweetData.query.count()
            
            print(f"\n📊 重置后状态:")
            print(f"   - 已同步: {remaining_synced}")
            print(f"   - 未同步: {total_tweets - remaining_synced}")
        
        except Exception as e:
            print(f"❌ 重置过程中发生错误: {e}")
            db.session.rollback()
            import traceback
            print(f"   - 错误详情: {traceback.format_exc()}")

def show_sync_status(task_id=None):
    """显示同步状态"""
    print("📊 当前同步状态")
    print("=" * 30)
    
    with app.app_context():
        try:
            if task_id:
                total_tweets = TweetData.query.filter_by(task_id=task_id).count()
                synced_tweets = TweetData.query.filter_by(task_id=task_id, synced_to_feishu=True).count()
                print(f"任务 {task_id}:")
            else:
                total_tweets = TweetData.query.count()
                synced_tweets = TweetData.query.filter_by(synced_to_feishu=True).count()
                print("所有任务:")
        
            unsynced_tweets = total_tweets - synced_tweets
            sync_rate = (synced_tweets / total_tweets * 100) if total_tweets > 0 else 0
            
            print(f"   - 总推文数: {total_tweets}")
            print(f"   - 已同步: {synced_tweets}")
            print(f"   - 未同步: {unsynced_tweets}")
            print(f"   - 同步率: {sync_rate:.1f}%")
            
            # 显示各任务的同步状态
            if not task_id:
                print("\n📋 各任务同步状态:")
                tasks = db.session.execute(text("""
                    SELECT task_id, 
                           COUNT(*) as total,
                           SUM(CASE WHEN synced_to_feishu THEN 1 ELSE 0 END) as synced
                    FROM tweet_data 
                    GROUP BY task_id 
                    ORDER BY task_id
                """)).fetchall()
                
                for task in tasks:
                    task_id, total, synced = task
                    unsynced = total - synced
                    rate = (synced / total * 100) if total > 0 else 0
                    print(f"   任务 {task_id}: {synced}/{total} ({rate:.1f}%)")
            
        except Exception as e:
            print(f"❌ 查询同步状态时发生错误: {e}")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='重置飞书同步状态')
    parser.add_argument('--task-id', type=int, help='指定任务ID（不指定则重置所有任务）')
    parser.add_argument('--status-only', action='store_true', help='仅显示同步状态，不执行重置')
    
    args = parser.parse_args()
    
    if args.status_only:
        show_sync_status(args.task_id)
    else:
        show_sync_status(args.task_id)
        print()
        reset_sync_status(args.task_id)