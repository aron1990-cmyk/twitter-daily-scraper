#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务创建调试脚本
测试任务创建时的名称处理逻辑
"""

import requests
import json
import time

def test_task_creation():
    """测试任务创建"""
    api_base_url = "http://localhost:8091/api"
    
    # 测试数据
    task_name = f"测试任务_调试_{int(time.time())}"
    
    test_cases = [
        {
            "name": "单关键词任务",
            "data": {
                "name": task_name + "_单关键词",
                "target_keywords": ["测试关键词"],
                "target_accounts": [],
                "max_tweets": 5
            }
        },
        {
            "name": "单账号任务", 
            "data": {
                "name": task_name + "_单账号",
                "target_keywords": ["测试关键词"],
                "target_accounts": ["openai"],
                "max_tweets": 5
            }
        },
        {
            "name": "多账号任务",
            "data": {
                "name": task_name + "_多账号",
                "target_keywords": ["测试关键词"],
                "target_accounts": ["openai", "elonmusk"],
                "max_tweets": 5
            }
        }
    ]
    
    created_tasks = []
    
    for test_case in test_cases:
        print(f"\n🧪 测试: {test_case['name']}")
        print(f"📝 任务名称: {test_case['data']['name']}")
        print(f"🎯 目标账号: {test_case['data']['target_accounts']}")
        
        try:
            response = requests.post(f"{api_base_url}/tasks", json=test_case['data'])
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"✅ 任务创建成功")
                    print(f"   主任务ID: {result.get('task_id')}")
                    print(f"   任务类型: {result.get('task_type')}")
                    
                    if result.get('sub_task_ids'):
                        print(f"   子任务IDs: {result.get('sub_task_ids')}")
                        print(f"   消息: {result.get('message')}")
                    
                    created_tasks.append(result.get('task_id'))
                    
                    # 获取创建的任务详情
                    tasks_response = requests.get(f"{api_base_url}/tasks")
                    if tasks_response.status_code == 200:
                        tasks_data = tasks_response.json()
                        if tasks_data.get('success'):
                            tasks = tasks_data.get('tasks', [])
                            print(f"\n📋 最新创建的任务:")
                            for task in tasks[:3]:  # 显示最新的3个任务
                                if task['id'] in created_tasks or task['name'].startswith(test_case['data']['name']):
                                    print(f"   - ID: {task['id']}, 名称: '{task['name']}', 状态: {task['status']}")
                else:
                    print(f"❌ 任务创建失败: {result.get('error')}")
            else:
                print(f"❌ API请求失败: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")
        
        time.sleep(1)  # 避免请求过快
    
    print(f"\n🧹 清理创建的测试任务...")
    for task_id in created_tasks:
        try:
            delete_response = requests.delete(f"{api_base_url}/tasks/{task_id}")
            if delete_response.status_code == 200:
                print(f"✅ 任务 {task_id} 已删除")
            else:
                print(f"⚠️ 删除任务 {task_id} 失败: {delete_response.status_code}")
        except Exception as e:
            print(f"⚠️ 删除任务 {task_id} 异常: {e}")

if __name__ == "__main__":
    test_task_creation()