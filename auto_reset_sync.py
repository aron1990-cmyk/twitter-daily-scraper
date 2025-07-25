#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动重置飞书同步状态
用于重新测试同步功能（无需用户确认）
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_app import app, db, TweetData

def auto_reset_sync_status():
    """自动重置飞书同步状态"""
    print("🔄 自动重置飞书同步状态")
    print("=" * 50)
    
    with app.app_context():
        try:
            # 获取所有推文
            tweets = TweetData.query.all()
            print(f"📊 找到推文总数: {len(tweets)}")
            
            if not tweets:
                print("⚠️ 没有找到推文数据")
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
            
            # 自动执行重置
            print(f"\n🔄 开始重置 {synced_count} 条已同步推文的状态...")
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
            
            # 验证重置结果
            remaining_synced = TweetData.query.filter_by(synced_to_feishu=True).count()
            total_tweets = TweetData.query.count()
            
            print(f"\n📊 重置后状态:")
            print(f"   - 已同步: {remaining_synced}")
            print(f"   - 未同步: {total_tweets - remaining_synced}")
            print(f"   - 重置成功: {'✅' if remaining_synced == 0 else '❌'}")
            
        except Exception as e:
            print(f"❌ 重置过程中发生错误: {e}")
            db.session.rollback()
            import traceback
            print(f"   - 错误详情: {traceback.format_exc()}")

if __name__ == '__main__':
    auto_reset_sync_status()