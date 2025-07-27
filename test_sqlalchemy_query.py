#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试SQLAlchemy查询synced_to_feishu字段
"""

import sys
sys.path.append('.')

from web_app import app, TweetData, db

def test_query():
    """测试不同的查询方式"""
    with app.app_context():
        print("🔍 测试SQLAlchemy查询synced_to_feishu字段")
        print("="*50)
        
        # 测试任务11的数据
        task_id = 11
        
        # 先检查数据库连接
        print(f"\n🔗 数据库连接信息:")
        print(f"   数据库引擎: {db.engine}")
        
        # 使用原生SQL检查数据
        from sqlalchemy import text
        print(f"\n📊 使用原生SQL查询任务 {task_id} 的所有数据:")
        raw_result = db.session.execute(
            text("SELECT id, task_id, content, synced_to_feishu FROM tweet_data WHERE task_id = :task_id"),
            {'task_id': task_id}
        ).fetchall()
        print(f"   原生SQL查询到 {len(raw_result)} 条数据")
        for row in raw_result:
            print(f"   - ID: {row[0]}, task_id: {row[1]}, synced_to_feishu: {row[3]} (type: {type(row[3])})")
        
        print(f"\n📊 使用SQLAlchemy查询任务 {task_id} 的所有数据:")
        all_tweets = TweetData.query.filter_by(task_id=task_id).all()
        print(f"   SQLAlchemy查询到 {len(all_tweets)} 条数据")
        for tweet in all_tweets:
            print(f"   - ID: {tweet.id}, synced_to_feishu: {tweet.synced_to_feishu} (type: {type(tweet.synced_to_feishu)})")
        
        if len(all_tweets) > 0:
            print(f"\n🔍 使用 synced_to_feishu=False 查询:")
            tweets_false = TweetData.query.filter_by(task_id=task_id, synced_to_feishu=False).all()
            print(f"   结果数量: {len(tweets_false)}")
            
            print(f"\n🔍 使用 synced_to_feishu=0 查询:")
            tweets_zero = TweetData.query.filter_by(task_id=task_id, synced_to_feishu=0).all()
            print(f"   结果数量: {len(tweets_zero)}")
            
            print(f"\n🔍 使用 synced_to_feishu=True 查询:")
            tweets_true = TweetData.query.filter_by(task_id=task_id, synced_to_feishu=True).all()
            print(f"   结果数量: {len(tweets_true)}")
            
            print(f"\n🔍 使用 synced_to_feishu=1 查询:")
            tweets_one = TweetData.query.filter_by(task_id=task_id, synced_to_feishu=1).all()
            print(f"   结果数量: {len(tweets_one)}")
        else:
            print(f"\n❌ SQLAlchemy无法查询到数据，可能存在数据库连接或模型定义问题")
        
        print(f"\n🔍 使用原生SQL查询:")
        from sqlalchemy import text
        result = db.session.execute(
            text("SELECT id, synced_to_feishu FROM tweet_data WHERE task_id = :task_id AND synced_to_feishu = 0"),
            {'task_id': task_id}
        ).fetchall()
        print(f"   原生SQL结果数量: {len(result)}")
        for row in result:
            print(f"   - ID: {row[0]}, synced_to_feishu: {row[1]}")

if __name__ == "__main__":
    test_query()