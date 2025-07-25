#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的任务启动功能
"""

import requests
import json
import time

def test_task_creation_and_start():
    """测试任务创建和启动"""
    base_url = "http://localhost:8088"
    
    print("🧪 开始测试修复后的任务功能")
    
    # 1. 创建新任务
    print("\n📝 步骤1: 创建新任务")
    task_data = {
        'name': '测试任务_修复后_v2',
        'target_accounts': json.dumps(['elonmusk']),
        'target_keywords': json.dumps(['AI', 'Tesla']),
        'max_tweets': 5,
        'min_likes': 0,
        'min_comments': 0,
        'min_retweets': 0
    }
    
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(f"{base_url}/api/tasks", json=task_data, headers=headers, timeout=10)
        print(f"创建任务响应状态: {response.status_code}")
        print(f"创建任务响应内容: {response.text[:200]}...")
        
        if response.status_code == 200 or response.status_code == 201:
            print("✅ 任务创建成功")
        else:
            print(f"❌ 任务创建失败: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ 创建任务时发生错误: {e}")
        return
    
    # 2. 获取最新任务ID
    print("\n🔍 步骤2: 获取最新任务ID")
    try:
        response = requests.get(f"{base_url}/api/tasks", timeout=10)
        if response.status_code == 200:
            tasks = response.json()
            if tasks:
                latest_task_id = max([task['id'] for task in tasks])
                print(f"✅ 最新任务ID: {latest_task_id}")
            else:
                print("❌ 没有找到任务")
                return
        else:
            print(f"❌ 获取任务列表失败: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 获取任务列表时发生错误: {e}")
        return
    
    # 3. 启动任务
    print(f"\n🚀 步骤3: 启动任务 {latest_task_id}")
    try:
        start_url = f"{base_url}/api/tasks/{latest_task_id}/start"
        print(f"启动URL: {start_url}")
        
        response = requests.post(start_url, timeout=30)
        print(f"启动任务响应状态: {response.status_code}")
        print(f"启动任务响应内容: {response.text[:500]}...")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 任务启动成功")
            print(f"任务状态: {result.get('status', 'unknown')}")
            print(f"消息: {result.get('message', 'no message')}")
        else:
            print(f"❌ 任务启动失败: {response.status_code}")
            print(f"错误详情: {response.text}")
            
    except Exception as e:
        print(f"❌ 启动任务时发生错误: {e}")
        return
    
    # 4. 监控任务状态
    print(f"\n👀 步骤4: 监控任务状态")
    for i in range(10):  # 监控10次
        try:
            time.sleep(2)  # 等待2秒
            response = requests.get(f"{base_url}/api/tasks/{latest_task_id}", timeout=10)
            if response.status_code == 200:
                task_info = response.json()
                status = task_info.get('status', 'unknown')
                result_count = task_info.get('result_count', 0)
                print(f"监控第{i+1}次 - 状态: {status}, 结果数: {result_count}")
                
                if status in ['completed', 'failed']:
                    print(f"🏁 任务已结束，最终状态: {status}")
                    if status == 'completed':
                        print(f"✅ 任务成功完成，抓取了 {result_count} 条推文")
                    else:
                        error_msg = task_info.get('error_message', '未知错误')
                        print(f"❌ 任务失败: {error_msg}")
                    break
            else:
                print(f"获取任务状态失败: {response.status_code}")
        except Exception as e:
            print(f"监控任务状态时发生错误: {e}")
    
    print("\n🎉 测试完成")

if __name__ == "__main__":
    test_task_creation_and_start()