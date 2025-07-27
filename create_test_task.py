#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建测试任务来验证新建任务的同步逻辑
"""

import sqlite3
import requests
import json
from datetime import datetime

def create_test_task():
    """创建一个测试任务"""
    print("\n" + "="*60)
    print("🧪 创建测试任务验证同步逻辑")
    print("="*60)
    
    try:
        # 创建新任务
        print("\n📝 1. 创建新的抓取任务")
        
        task_data = {
            "name": "测试同步修复任务",
            "target_accounts": ["elonmusk"],
            "target_keywords": [],
            "max_tweets": 5,
            "min_likes": 0,
            "min_retweets": 0,
            "min_comments": 0
        }
        
        url = "http://localhost:8090/api/tasks"
        print(f"   调用API: {url}")
        print(f"   任务数据: {json.dumps(task_data, ensure_ascii=False, indent=2)}")
        
        response = requests.post(url, json=task_data, timeout=30)
        print(f"   响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            if result.get('success'):
                task_id = result.get('task_id')
                print(f"   ✅ 任务创建成功，任务ID: {task_id}")
                return task_id
            else:
                print(f"   ❌ 任务创建失败: {result.get('error')}")
                return None
        else:
            print(f"   ❌ API调用失败: {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ 创建任务失败: {e}")
        return None

def wait_for_task_completion(task_id, max_wait_time=300):
    """等待任务完成"""
    print(f"\n⏳ 2. 等待任务 {task_id} 完成")
    
    import time
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        try:
            # 检查任务状态
            conn = sqlite3.connect('instance/twitter_scraper.db')
            cursor = conn.cursor()
            cursor.execute("SELECT status, result_count FROM scraping_task WHERE id = ?", (task_id,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                status, result_count = result
                print(f"   任务状态: {status}, 结果数量: {result_count}")
                
                if status == 'completed':
                    print(f"   ✅ 任务完成，抓取到 {result_count} 条推文")
                    return True
                elif status == 'failed':
                    print(f"   ❌ 任务失败")
                    return False
            
            time.sleep(10)  # 等待10秒后再检查
            
        except Exception as e:
            print(f"   ❌ 检查任务状态失败: {e}")
            time.sleep(10)
    
    print(f"   ⏰ 等待超时")
    return False

def test_new_task_sync(task_id):
    """测试新任务的同步逻辑"""
    print(f"\n🔧 3. 测试新任务 {task_id} 的同步逻辑")
    
    try:
        # 检查任务的推文数据和同步状态
        conn = sqlite3.connect('instance/twitter_scraper.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_tweets,
                SUM(CASE WHEN synced_to_feishu = 1 THEN 1 ELSE 0 END) as synced_tweets,
                SUM(CASE WHEN synced_to_feishu = 0 THEN 1 ELSE 0 END) as unsynced_tweets
            FROM tweet_data 
            WHERE task_id = ?
        """, (task_id,))
        
        result = cursor.fetchone()
        total, synced, unsynced = result
        
        print(f"   任务 {task_id} 数据统计:")
        print(f"   - 总推文数: {total}")
        print(f"   - 已同步: {synced}")
        print(f"   - 未同步: {unsynced}")
        
        if total == 0:
            print(f"   ⚠️ 任务没有抓取到数据")
            conn.close()
            return False
        
        # 显示前几条推文的同步状态
        cursor.execute("""
            SELECT id, content, synced_to_feishu
            FROM tweet_data 
            WHERE task_id = ?
            ORDER BY id DESC 
            LIMIT 3
        """, (task_id,))
        
        tweets = cursor.fetchall()
        print(f"   推文同步状态:")
        for tweet_id, content, synced in tweets:
            status = "已同步" if synced else "未同步"
            print(f"   - 推文 {tweet_id}: {content[:50]}... [{status}]")
        
        conn.close()
        
        # 测试同步API
        if unsynced > 0:
            print(f"\n   🚀 测试同步API（应该同步 {unsynced} 条未同步数据）")
            
            url = f"http://localhost:8090/api/data/sync_feishu/{task_id}"
            response = requests.post(url, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                print(f"   API响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                if result.get('success'):
                    print(f"   ✅ 同步成功: {result.get('message')}")
                else:
                    print(f"   ❌ 同步失败: {result.get('error')}")
            else:
                print(f"   ❌ API调用失败: {response.text}")
                
            # 再次检查同步状态
            print(f"\n   📊 同步后状态检查")
            conn = sqlite3.connect('instance/twitter_scraper.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_tweets,
                    SUM(CASE WHEN synced_to_feishu = 1 THEN 1 ELSE 0 END) as synced_tweets,
                    SUM(CASE WHEN synced_to_feishu = 0 THEN 1 ELSE 0 END) as unsynced_tweets
                FROM tweet_data 
                WHERE task_id = ?
            """, (task_id,))
            
            result = cursor.fetchone()
            total, synced, unsynced = result
            
            print(f"   同步后统计:")
            print(f"   - 总推文数: {total}")
            print(f"   - 已同步: {synced}")
            print(f"   - 未同步: {unsynced}")
            
            conn.close()
            
        else:
            print(f"\n   ℹ️ 所有数据都已同步，测试重复同步API")
            
            url = f"http://localhost:8090/api/data/sync_feishu/{task_id}"
            response = requests.post(url, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                print(f"   API响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                if result.get('success'):
                    print(f"   ✅ 正确处理已同步数据: {result.get('message')}")
                else:
                    print(f"   ❌ 处理失败: {result.get('error')}")
            else:
                print(f"   ❌ API调用失败: {response.text}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    # 创建测试任务
    task_id = create_test_task()
    
    if task_id:
        # 等待任务完成
        if wait_for_task_completion(task_id):
            # 测试同步逻辑
            test_new_task_sync(task_id)
        else:
            print("❌ 任务未能完成，跳过同步测试")
    else:
        print("❌ 无法创建测试任务")
    
    print("\n✅ 测试完成")
    print("="*60)