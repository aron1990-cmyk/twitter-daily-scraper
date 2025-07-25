#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试任务创建和启动
"""

import requests
import json
import time

def test_task_creation():
    """测试任务创建和启动"""
    try:
        # 创建任务
        print('🔧 创建测试任务...')
        data = {
            'name': '测试任务_修复后',
            'target_accounts': 'yiguxia',
            'max_tweets': 10
        }
        
        response = requests.post('http://localhost:8088/create_task', data=data)
        print(f'创建任务响应状态: {response.status_code}')
        
        if response.status_code == 200:
            print('✅ 任务创建成功')
            
            # 获取最新任务ID
            tasks_response = requests.get('http://localhost:8088/api/tasks')
            if tasks_response.status_code == 200:
                tasks = tasks_response.json()
                if tasks:
                    latest_task = tasks[0]  # 最新的任务
                    task_id = latest_task['id']
                    print(f'最新任务ID: {task_id}')
                    
                    # 启动任务
                    print(f'🚀 启动任务 {task_id}...')
                    start_response = requests.post(f'http://localhost:8088/api/tasks/{task_id}/start')
                    print(f'启动任务响应状态: {start_response.status_code}')
                    
                    if start_response.status_code == 200:
                        result = start_response.json()
                        print(f'启动结果: {result}')
                        
                        if result.get('success'):
                            print('✅ 任务启动成功！')
                            print('请观察AdsPower浏览器是否正常打开')
                        else:
                            print(f'❌ 任务启动失败: {result.get("error", "未知错误")}')
                    else:
                        print(f'❌ 启动任务请求失败: {start_response.text}')
                else:
                    print('❌ 没有找到任务')
            else:
                print(f'❌ 获取任务列表失败: {tasks_response.text}')
        else:
            print(f'❌ 任务创建失败: {response.text}')
            
    except Exception as e:
        print(f'❌ 测试失败: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_task_creation()