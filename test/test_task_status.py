#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务状态测试脚本
专门测试任务状态更新功能
"""

import sys
import os
import time
import requests
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TaskStatusTest:
    def __init__(self):
        self.api_base_url = 'http://localhost:8091/api'
        
    def create_test_task(self):
        """创建测试任务"""
        task_data = {
            'name': f'状态测试任务_{int(time.time())}',
            'target_keywords': ['测试状态'],
            'max_tweets': 5
        }
        
        response = requests.post(f'{self.api_base_url}/tasks', json=task_data)
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                return result.get('task_id')
        return None
    
    def get_task_status(self, task_id):
        """获取任务状态"""
        response = requests.get(f'{self.api_base_url}/tasks')
        if response.status_code == 200:
            data = response.json()
            tasks = data.get('tasks', [])
            for task in tasks:
                if task['id'] == task_id:
                    return task.get('status')
        return None
    
    def start_task(self, task_id):
        """启动任务"""
        response = requests.post(f'{self.api_base_url}/tasks/{task_id}/start')
        return response.status_code == 200, response.json() if response.status_code == 200 else response.text
    
    def stop_task(self, task_id):
        """停止任务"""
        response = requests.post(f'{self.api_base_url}/tasks/{task_id}/stop')
        return response.status_code == 200, response.json() if response.status_code == 200 else response.text
    
    def delete_task(self, task_id):
        """删除任务"""
        response = requests.delete(f'{self.api_base_url}/tasks/{task_id}')
        return response.status_code == 200, response.json() if response.status_code == 200 else response.text
    
    def test_task_lifecycle(self):
        """测试任务生命周期"""
        print("\n=== 任务状态测试开始 ===")
        
        # 1. 创建任务
        print("\n1. 创建任务...")
        task_id = self.create_test_task()
        if not task_id:
            print("❌ 创建任务失败")
            return False
        print(f"✅ 任务创建成功，ID: {task_id}")
        
        # 2. 检查初始状态
        print("\n2. 检查初始状态...")
        initial_status = self.get_task_status(task_id)
        print(f"初始状态: {initial_status}")
        if initial_status != 'pending':
            print(f"❌ 初始状态异常，期望: pending，实际: {initial_status}")
        else:
            print("✅ 初始状态正确")
        
        # 3. 启动任务
        print("\n3. 启动任务...")
        success, result = self.start_task(task_id)
        print(f"启动结果: {success}, 响应: {result}")
        
        # 4. 等待状态更新
        print("\n4. 等待状态更新...")
        for i in range(10):  # 等待最多10秒
            time.sleep(1)
            status = self.get_task_status(task_id)
            print(f"第{i+1}秒状态: {status}")
            if status in ['running', 'queued']:
                print(f"✅ 状态更新成功: {status}")
                break
        else:
            print(f"❌ 状态未更新为running或queued，当前状态: {status}")
        
        # 5. 停止任务
        print("\n5. 停止任务...")
        success, result = self.stop_task(task_id)
        print(f"停止结果: {success}, 响应: {result}")
        
        # 6. 检查停止后状态
        print("\n6. 检查停止后状态...")
        time.sleep(2)
        final_status = self.get_task_status(task_id)
        print(f"停止后状态: {final_status}")
        
        # 7. 删除任务
        print("\n7. 删除任务...")
        success, result = self.delete_task(task_id)
        print(f"删除结果: {success}, 响应: {result}")
        
        # 8. 验证删除
        print("\n8. 验证删除...")
        time.sleep(1)
        deleted_status = self.get_task_status(task_id)
        if deleted_status is None:
            print("✅ 任务删除成功")
        else:
            print(f"❌ 任务删除失败，仍存在状态: {deleted_status}")
        
        print("\n=== 任务状态测试完成 ===")
        return True

if __name__ == '__main__':
    tester = TaskStatusTest()
    tester.test_task_lifecycle()