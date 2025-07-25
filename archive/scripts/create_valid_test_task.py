#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建有效的测试任务
"""

import requests
import json

def create_valid_test_task():
    """创建一个使用有效Twitter用户名的测试任务"""
    base_url = "http://localhost:8088"
    
    print("🧪 创建有效的测试任务")
    
    # 创建新任务，使用有效的Twitter用户名
    task_data = {
        'name': '有效用户测试任务',
        'target_accounts': json.dumps(['elonmusk', 'OpenAI']),  # 使用有效的用户名
        'target_keywords': json.dumps(['AI', 'technology']),
        'max_tweets': 3,  # 减少数量以便快速测试
        'min_likes': 0,
        'min_comments': 0,
        'min_retweets': 0
    }
    
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(f"{base_url}/api/tasks", json=task_data, headers=headers, timeout=10)
        print(f"创建任务响应状态: {response.status_code}")
        print(f"创建任务响应内容: {response.text}")
        
        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            task_id = result.get('task_id')
            print(f"✅ 任务创建成功，任务ID: {task_id}")
            return task_id
        else:
            print(f"❌ 任务创建失败: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ 创建任务时发生错误: {e}")
        return None

def start_task(task_id):
    """启动任务"""
    base_url = "http://localhost:8088"
    
    print(f"\n🚀 启动任务 {task_id}")
    try:
        start_url = f"{base_url}/api/tasks/{task_id}/start"
        response = requests.post(start_url, timeout=30)
        print(f"启动任务响应状态: {response.status_code}")
        print(f"启动任务响应内容: {response.text}")
        
        if response.status_code == 200:
            print(f"✅ 任务启动成功")
            return True
        else:
            print(f"❌ 任务启动失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 启动任务时发生错误: {e}")
        return False

if __name__ == "__main__":
    # 创建任务
    task_id = create_valid_test_task()
    
    if task_id:
        # 启动任务
        success = start_task(task_id)
        if success:
            print(f"\n🎉 任务 {task_id} 已成功启动！")
            print("请查看Web界面或日志来监控任务进度。")
        else:
            print(f"\n❌ 任务 {task_id} 启动失败")
    else:
        print("\n❌ 无法创建任务")