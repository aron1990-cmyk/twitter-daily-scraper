#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建新任务并测试飞书同步功能
用于排查飞书同步问题
"""

import requests
import json
import time
from datetime import datetime

def create_and_test_sync():
    """
    创建新任务并测试飞书同步
    """
    print("🚀 开始创建新任务并测试飞书同步")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Web应用地址
    base_url = "http://localhost:8090"
    
    try:
        # 1. 创建新任务
        print("📝 创建新的测试任务...")
        task_name = f"飞书同步测试任务_{int(time.time())}"
        task_data = {
            "name": task_name,
            "target_keywords": ["AI", "人工智能"],
            "target_accounts": ["elonmusk", "OpenAI"]
        }
        
        print(f"   - 任务名称: {task_name}")
        print(f"   - 目标关键词: {task_data['target_keywords']}")
        print(f"   - 目标账号: {task_data['target_accounts']}")
        
        create_response = requests.post(
            f"{base_url}/api/tasks",
            json=task_data,
            timeout=30
        )
        
        if create_response.status_code == 200:
            create_result = create_response.json()
            print(f"📋 创建任务API响应: {json.dumps(create_result, ensure_ascii=False, indent=2)}")
            
            if create_result.get('success'):
                # 尝试不同的字段名
                new_task_id = create_result.get('new_task_id') or create_result.get('task_id') or create_result.get('id')
                print(f"✅ 任务创建成功，任务ID: {new_task_id}")
                
                if not new_task_id:
                    print(f"❌ 无法获取任务ID，响应中没有找到task_id字段")
                    return
            else:
                print(f"❌ 任务创建失败: {create_result.get('error')}")
                return
        else:
            print(f"❌ 任务创建请求失败: {create_response.status_code}")
            print(f"📋 错误响应: {create_response.text[:500]}...")
            return
        
        # 2. 手动添加一些测试数据到数据库
        print(f"\n📊 为任务 {new_task_id} 添加测试数据...")
        
        # 使用直接的数据库操作添加测试数据
        test_tweets = [
            {
                "content": "测试推文1：AI技术的发展真是令人惊叹！#AI #技术",
                "username": "test_user1",
                "link": "https://twitter.com/test_user1/status/1",
                "publish_time": "2025-01-27 10:00:00",
                "likes": 100,
                "retweets": 50,
                "comments": 25,
                "hashtags": '["AI", "技术"]'
            },
            {
                "content": "测试推文2：人工智能将改变世界！这是一个激动人心的时代。",
                "username": "test_user2", 
                "link": "https://twitter.com/test_user2/status/2",
                "publish_time": "2025-01-27 11:00:00",
                "likes": 200,
                "retweets": 80,
                "comments": 40,
                "hashtags": '["人工智能", "未来"]'
            },
            {
                "content": "测试推文3：OpenAI的最新模型性能提升显著，期待更多突破！",
                "username": "test_user3",
                "link": "https://twitter.com/test_user3/status/3", 
                "publish_time": "2025-01-27 12:00:00",
                "likes": 150,
                "retweets": 60,
                "comments": 30,
                "hashtags": '["OpenAI", "模型"]'
            }
        ]
        
        # 通过API添加测试数据（如果有相应的API）
        # 或者直接操作数据库
        import sqlite3
        from datetime import datetime as dt
        
        conn = sqlite3.connect('instance/twitter_scraper.db')
        cursor = conn.cursor()
        
        for tweet in test_tweets:
            cursor.execute("""
                INSERT INTO tweet_data (
                    task_id, content, username, link, publish_time, 
                    likes, retweets, comments, hashtags, scraped_at, synced_to_feishu
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                new_task_id,
                tweet['content'],
                tweet['username'],
                tweet['link'],
                tweet['publish_time'],
                tweet['likes'],
                tweet['retweets'],
                tweet['comments'],
                tweet['hashtags'],
                dt.now().strftime('%Y-%m-%d %H:%M:%S'),
                False  # 未同步到飞书
            ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ 成功添加 {len(test_tweets)} 条测试数据")
        
        # 3. 等待一下，然后触发飞书同步
        print(f"\n🔄 开始测试飞书同步...")
        time.sleep(2)
        
        sync_url = f"{base_url}/api/data/sync_feishu/{new_task_id}"
        print(f"   - 同步URL: {sync_url}")
        
        print("\n📤 发送同步请求...")
        sync_response = requests.post(sync_url, timeout=60)
        
        print(f"📊 同步响应状态码: {sync_response.status_code}")
        
        if sync_response.status_code == 200:
            try:
                result = sync_response.json()
                print("✅ 同步请求成功")
                print(f"📋 响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
            except json.JSONDecodeError:
                print("⚠️ 响应不是有效的JSON格式")
                print(f"📋 原始响应: {sync_response.text[:500]}...")
        else:
            print(f"❌ 同步请求失败: {sync_response.status_code}")
            print(f"📋 错误响应: {sync_response.text[:500]}...")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求异常: {e}")
    except Exception as e:
        print(f"❌ 测试过程中发生异常: {e}")
        import traceback
        print(f"📋 异常详情: {traceback.format_exc()}")
    
    print("\n" + "="*60)
    print("🏁 飞书同步测试完成")
    print(f"⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    create_and_test_sync()