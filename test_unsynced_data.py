#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建未同步的测试数据来验证修复逻辑
"""

import sqlite3
import requests
import json
from datetime import datetime

def create_unsynced_test_data():
    """创建一些未同步的测试数据"""
    print("\n" + "="*60)
    print("🧪 创建未同步测试数据验证修复逻辑")
    print("="*60)
    
    try:
        conn = sqlite3.connect('instance/twitter_scraper.db')
        cursor = conn.cursor()
        
        # 插入一些未同步的测试数据到任务4
        print("\n📝 1. 插入未同步的测试数据")
        
        test_tweets = [
            {
                'task_id': 4,
                'content': '这是一条测试推文1 - 未同步',
                'username': 'test_user1',
                'link': 'https://twitter.com/test1',
                'likes': 10,
                'retweets': 5,
                'comments': 2,
                'hashtags': json.dumps(['test', 'unsynced']),
                'synced_to_feishu': False,  # 关键：设置为未同步
                'scraped_at': datetime.now()
            },
            {
                'task_id': 4,
                'content': '这是一条测试推文2 - 未同步',
                'username': 'test_user2',
                'link': 'https://twitter.com/test2',
                'likes': 20,
                'retweets': 8,
                'comments': 3,
                'hashtags': json.dumps(['test', 'verification']),
                'synced_to_feishu': False,  # 关键：设置为未同步
                'scraped_at': datetime.now()
            },
            {
                'task_id': 4,
                'content': '这是一条测试推文3 - 未同步',
                'username': 'test_user3',
                'link': 'https://twitter.com/test3',
                'likes': 15,
                'retweets': 6,
                'comments': 1,
                'hashtags': json.dumps(['test', 'sync_fix']),
                'synced_to_feishu': False,  # 关键：设置为未同步
                'scraped_at': datetime.now()
            }
        ]
        
        for i, tweet in enumerate(test_tweets, 1):
            cursor.execute("""
                INSERT INTO tweet_data (
                    task_id, content, username, link, likes, retweets, comments, 
                    hashtags, synced_to_feishu, scraped_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tweet['task_id'], tweet['content'], tweet['username'], tweet['link'],
                tweet['likes'], tweet['retweets'], tweet['comments'], tweet['hashtags'],
                tweet['synced_to_feishu'], tweet['scraped_at']
            ))
            print(f"   ✅ 插入测试推文 {i}: {tweet['content'][:30]}...")
        
        conn.commit()
        conn.close()
        
        print(f"   ✅ 成功插入 {len(test_tweets)} 条未同步测试数据")
        
    except Exception as e:
        print(f"   ❌ 插入测试数据失败: {e}")
        return False
    
    return True

def test_sync_logic():
    """测试同步逻辑"""
    print("\n📊 2. 检查任务4的同步状态")
    
    try:
        conn = sqlite3.connect('instance/twitter_scraper.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_tweets,
                SUM(CASE WHEN synced_to_feishu = 1 THEN 1 ELSE 0 END) as synced_tweets,
                SUM(CASE WHEN synced_to_feishu = 0 THEN 1 ELSE 0 END) as unsynced_tweets,
                ROUND(SUM(CASE WHEN synced_to_feishu = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as sync_rate
            FROM tweet_data 
            WHERE task_id = 4
        """)
        
        result = cursor.fetchone()
        total, synced, unsynced, rate = result
        
        print(f"   任务4数据统计:")
        print(f"   - 总推文数: {total}")
        print(f"   - 已同步: {synced}")
        print(f"   - 未同步: {unsynced}")
        print(f"   - 同步率: {rate}%")
        
        # 显示未同步的推文
        cursor.execute("""
            SELECT id, content, synced_to_feishu
            FROM tweet_data 
            WHERE task_id = 4 AND synced_to_feishu = 0
            ORDER BY id DESC
        """)
        
        unsynced_tweets = cursor.fetchall()
        print(f"\n   未同步推文列表:")
        for tweet_id, content, synced in unsynced_tweets:
            print(f"   - 推文 {tweet_id}: {content[:50]}... [未同步]")
        
        conn.close()
        
        if unsynced > 0:
            print(f"\n🚀 3. 测试同步API（应该只同步 {unsynced} 条未同步数据）")
            
            url = f"http://localhost:8090/api/data/sync_feishu/4"
            print(f"   调用API: {url}")
            
            response = requests.post(url, timeout=30)
            print(f"   响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   API响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                if result.get('success'):
                    print(f"   ✅ 同步成功: {result.get('message')}")
                    
                    # 验证同步后的状态
                    print(f"\n📊 4. 验证同步后状态")
                    
                    conn = sqlite3.connect('instance/twitter_scraper.db')
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as total_tweets,
                            SUM(CASE WHEN synced_to_feishu = 1 THEN 1 ELSE 0 END) as synced_tweets,
                            SUM(CASE WHEN synced_to_feishu = 0 THEN 1 ELSE 0 END) as unsynced_tweets,
                            ROUND(SUM(CASE WHEN synced_to_feishu = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as sync_rate
                        FROM tweet_data 
                        WHERE task_id = 4
                    """)
                    
                    result = cursor.fetchone()
                    total, synced, unsynced, rate = result
                    
                    print(f"   同步后统计:")
                    print(f"   - 总推文数: {total}")
                    print(f"   - 已同步: {synced}")
                    print(f"   - 未同步: {unsynced}")
                    print(f"   - 同步率: {rate}%")
                    
                    if unsynced == 0:
                        print(f"   ✅ 修复验证成功：所有数据都已正确同步")
                    else:
                        print(f"   ❌ 修复验证失败：仍有 {unsynced} 条数据未同步")
                    
                    conn.close()
                    
                else:
                    print(f"   ❌ 同步失败: {result.get('error')}")
            else:
                print(f"   ❌ API调用失败: {response.text}")
                
            # 测试重复同步
            print(f"\n🔄 5. 测试重复同步（应该提示已同步）")
            
            response = requests.post(url, timeout=30)
            if response.status_code == 200:
                result = response.json()
                print(f"   重复同步API响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                if result.get('success') and '都已同步' in result.get('message', ''):
                    print(f"   ✅ 重复同步处理正确: {result.get('message')}")
                else:
                    print(f"   ⚠️ 重复同步处理异常: {result.get('message')}")
            else:
                print(f"   ❌ 重复同步API调用失败: {response.text}")
        
        else:
            print(f"\n   ℹ️ 没有未同步数据，无法测试同步逻辑")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    # 创建未同步测试数据
    if create_unsynced_test_data():
        # 测试同步逻辑
        test_sync_logic()
    else:
        print("❌ 无法创建测试数据")
    
    print("\n✅ 测试完成")
    print("="*60)