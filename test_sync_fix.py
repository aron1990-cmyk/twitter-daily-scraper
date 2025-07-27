#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试飞书同步修复
验证新建任务的同步状态是否正确显示
"""

import sqlite3
import requests
import json
from datetime import datetime

def test_sync_status():
    """测试同步状态"""
    print("\n" + "="*60)
    print("🧪 测试飞书同步修复")
    print("="*60)
    
    # 1. 检查数据库中的同步状态
    print("\n📊 1. 检查数据库同步状态")
    try:
        conn = sqlite3.connect('instance/twitter_scraper.db')
        cursor = conn.cursor()
        
        # 查询各任务的同步状态
        cursor.execute("""
            SELECT 
                task_id,
                COUNT(*) as total_tweets,
                SUM(CASE WHEN synced_to_feishu = 1 THEN 1 ELSE 0 END) as synced_tweets,
                SUM(CASE WHEN synced_to_feishu = 0 THEN 1 ELSE 0 END) as unsynced_tweets,
                ROUND(SUM(CASE WHEN synced_to_feishu = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as sync_rate
            FROM tweet_data 
            GROUP BY task_id 
            ORDER BY task_id DESC
        """)
        
        results = cursor.fetchall()
        print(f"   任务同步状态统计:")
        for row in results:
            task_id, total, synced, unsynced, rate = row
            print(f"   - 任务 {task_id}: 总计 {total} 条，已同步 {synced} 条，未同步 {unsynced} 条，同步率 {rate}%")
        
        # 查询最新任务的详细信息
        cursor.execute("""
            SELECT id, task_id, content, synced_to_feishu, scraped_at
            FROM tweet_data 
            WHERE task_id = (SELECT MAX(id) FROM scraping_task)
            ORDER BY id DESC 
            LIMIT 5
        """)
        
        latest_tweets = cursor.fetchall()
        print(f"\n   最新任务的推文详情:")
        for tweet in latest_tweets:
            tweet_id, task_id, content, synced, scraped_at = tweet
            status = "已同步" if synced else "未同步"
            print(f"   - 推文 {tweet_id}: {content[:50]}... [{status}]")
        
        conn.close()
        
    except Exception as e:
        print(f"   ❌ 数据库查询失败: {e}")
        return False
    
    # 2. 测试API同步接口
    print(f"\n🔧 2. 测试API同步接口")
    try:
        # 获取最新任务ID
        conn = sqlite3.connect('instance/twitter_scraper.db')
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(id) FROM scraping_task")
        latest_task_id = cursor.fetchone()[0]
        conn.close()
        
        if not latest_task_id:
            print("   ❌ 没有找到任务")
            return False
        
        print(f"   测试任务ID: {latest_task_id}")
        
        # 调用同步API
        url = f"http://localhost:8090/api/data/sync_feishu/{latest_task_id}"
        print(f"   调用API: {url}")
        
        response = requests.post(url, timeout=30)
        print(f"   响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            if result.get('success'):
                print(f"   ✅ API调用成功: {result.get('message')}")
            else:
                print(f"   ⚠️ API返回失败: {result.get('error')}")
        else:
            print(f"   ❌ API调用失败: {response.text}")
            
    except Exception as e:
        print(f"   ❌ API测试失败: {e}")
        return False
    
    # 3. 再次检查同步状态
    print(f"\n📊 3. 同步后状态检查")
    try:
        conn = sqlite3.connect('instance/twitter_scraper.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                task_id,
                COUNT(*) as total_tweets,
                SUM(CASE WHEN synced_to_feishu = 1 THEN 1 ELSE 0 END) as synced_tweets,
                SUM(CASE WHEN synced_to_feishu = 0 THEN 1 ELSE 0 END) as unsynced_tweets,
                ROUND(SUM(CASE WHEN synced_to_feishu = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as sync_rate
            FROM tweet_data 
            GROUP BY task_id 
            ORDER BY task_id DESC
        """)
        
        results = cursor.fetchall()
        print(f"   同步后状态统计:")
        for row in results:
            task_id, total, synced, unsynced, rate = row
            print(f"   - 任务 {task_id}: 总计 {total} 条，已同步 {synced} 条，未同步 {unsynced} 条，同步率 {rate}%")
        
        conn.close()
        
    except Exception as e:
        print(f"   ❌ 状态检查失败: {e}")
        return False
    
    print(f"\n✅ 测试完成")
    print("="*60)
    return True

if __name__ == "__main__":
    test_sync_status()