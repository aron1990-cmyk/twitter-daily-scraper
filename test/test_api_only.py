#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的API测试脚本
只测试API功能，不涉及UI自动化
"""

import unittest
import requests
import time
import json

class APIOnlyTest(unittest.TestCase):
    """API功能测试"""
    
    def setUp(self):
        """测试前准备"""
        self.api_base_url = 'http://localhost:8091/api'
        self.test_tasks = []
    
    def tearDown(self):
        """测试后清理"""
        # 清理测试任务
        for task_id in self.test_tasks:
            try:
                requests.delete(f'{self.api_base_url}/tasks/{task_id}')
            except:
                pass
    
    def _create_test_task_via_api(self, name, keywords=None, target_accounts=None, max_tweets=50):
        """通过API创建测试任务"""
        task_data = {
            'name': name,
            'target_keywords': keywords or [],
            'target_accounts': target_accounts or [],
            'max_tweets': max_tweets
        }
        
        response = requests.post(f'{self.api_base_url}/tasks', json=task_data)
        self.assertEqual(response.status_code, 200, f"创建任务失败: {response.text}")
        
        data = response.json()
        self.assertTrue(data.get('success'), f"创建任务失败: {data.get('error')}")
        
        task_id = data.get('task_id')
        self.assertIsNotNone(task_id, "任务ID为空")
        
        self.test_tasks.append(task_id)
        return task_id
    
    def _get_task_status(self, task_id):
        """获取任务状态"""
        response = requests.get(f'{self.api_base_url}/tasks')
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('tasks'):
                tasks = data['tasks']
                for task in tasks:
                    if task['id'] == task_id:
                        return task['status']
        return None
    
    def _start_task_via_api(self, task_id):
        """通过API启动任务"""
        response = requests.post(f'{self.api_base_url}/tasks/{task_id}/start')
        return response.status_code == 200, response.json() if response.status_code == 200 else response.text
    
    def _stop_task_via_api(self, task_id):
        """通过API停止任务"""
        response = requests.post(f'{self.api_base_url}/tasks/{task_id}/stop')
        return response.status_code == 200, response.json() if response.status_code == 200 else response.text
    
    def _restart_task_via_api(self, task_id):
        """通过API重启任务"""
        response = requests.post(f'{self.api_base_url}/tasks/{task_id}/restart')
        return response.status_code == 200, response.json() if response.status_code == 200 else response.text
    
    def test_01_create_single_task(self):
        """测试创建单个任务"""
        print("\n🧪 测试创建单个任务")
        
        task_name = f"测试任务_单个_{int(time.time())}"
        keywords = ["人工智能", "机器学习"]
        
        task_id = self._create_test_task_via_api(task_name, keywords=keywords)
        self.assertIsNotNone(task_id, "任务创建失败")
        
        # 验证任务状态
        status = self._get_task_status(task_id)
        self.assertEqual(status, 'pending', f"任务状态异常: {status}")
        
        print(f"✅ 单个任务创建成功，ID: {task_id}, 状态: {status}")
    
    def test_02_create_multiple_tasks(self):
        """测试创建多个任务"""
        print("\n🧪 测试创建多个任务")
        
        task_configs = [
            {"name": f"测试任务_多任务1_{int(time.time())}", "keywords": ["深度学习"]},
            {"name": f"测试任务_多任务2_{int(time.time())}", "keywords": ["神经网络"]},
            {"name": f"测试任务_多任务3_{int(time.time())}", "target_accounts": ["openai"]}
        ]
        
        created_tasks = []
        for config in task_configs:
            task_id = self._create_test_task_via_api(
                config["name"], 
                keywords=config.get("keywords"),
                target_accounts=config.get("target_accounts")
            )
            created_tasks.append(task_id)
            time.sleep(0.5)  # 避免创建过快
        
        self.assertEqual(len(created_tasks), 3, "多任务创建数量不正确")
        
        # 验证所有任务状态
        for task_id in created_tasks:
            status = self._get_task_status(task_id)
            self.assertEqual(status, 'pending', f"任务 {task_id} 状态异常: {status}")
        
        print(f"✅ 多任务创建成功，创建了 {len(created_tasks)} 个任务")
    
    def test_03_start_task(self):
        """测试启动任务"""
        print("\n🧪 测试启动任务")
        
        # 创建一个任务
        task_name = f"测试任务_启动_{int(time.time())}"
        task_id = self._create_test_task_via_api(task_name, keywords=["测试启动"])
        
        # 验证初始状态
        initial_status = self._get_task_status(task_id)
        self.assertEqual(initial_status, 'pending', f"任务初始状态异常: {initial_status}")
        
        # 启动任务
        success, result = self._start_task_via_api(task_id)
        self.assertTrue(success, f"启动任务失败: {result}")
        
        # 等待状态变化
        time.sleep(3)
        
        # 验证状态变化
        new_status = self._get_task_status(task_id)
        self.assertIn(new_status, ['running', 'queued'], f"任务启动后状态异常: {new_status}")
        
        print(f"✅ 任务启动成功，状态从 {initial_status} 变为 {new_status}")
    
    def test_04_stop_task(self):
        """测试停止任务"""
        print("\n🧪 测试停止任务")
        
        # 创建并启动任务
        task_name = f"测试任务_停止_{int(time.time())}"
        task_id = self._create_test_task_via_api(task_name, keywords=["测试停止"])
        
        # 启动任务
        success, result = self._start_task_via_api(task_id)
        self.assertTrue(success, f"启动任务失败: {result}")
        
        time.sleep(2)  # 等待任务开始运行
        
        # 停止任务
        success, result = self._stop_task_via_api(task_id)
        self.assertTrue(success, f"停止任务失败: {result}")
        
        # 等待状态变化
        time.sleep(2)
        
        # 验证状态变化
        final_status = self._get_task_status(task_id)
        self.assertIn(final_status, ['stopped', 'failed', 'completed'], f"任务停止后状态异常: {final_status}")
        
        print(f"✅ 任务停止成功，最终状态: {final_status}")
    
    def test_05_restart_task(self):
        """测试重启任务"""
        print("\n🧪 测试重启任务")
        
        # 创建任务
        task_name = f"测试任务_重启_{int(time.time())}"
        task_id = self._create_test_task_via_api(task_name, keywords=["测试重启"])
        
        # 启动任务
        success, result = self._start_task_via_api(task_id)
        self.assertTrue(success, f"启动任务失败: {result}")
        
        time.sleep(2)  # 等待任务开始运行
        
        # 重启任务
        success, result = self._restart_task_via_api(task_id)
        self.assertTrue(success, f"重启任务失败: {result}")
        
        # 等待状态变化
        time.sleep(3)
        
        # 验证状态变化
        final_status = self._get_task_status(task_id)
        self.assertIn(final_status, ['running', 'queued', 'pending'], f"任务重启后状态异常: {final_status}")
        
        print(f"✅ 任务重启成功，最终状态: {final_status}")
    
    def test_06_delete_task(self):
        """测试删除任务"""
        print("\n🧪 测试删除任务")
        
        # 创建任务
        task_name = f"测试任务_删除_{int(time.time())}"
        task_id = self._create_test_task_via_api(task_name, keywords=["测试删除"])
        
        # 验证任务存在
        status = self._get_task_status(task_id)
        self.assertIsNotNone(status, "任务不存在")
        
        # 删除任务
        response = requests.delete(f'{self.api_base_url}/tasks/{task_id}')
        self.assertEqual(response.status_code, 200, f"删除任务失败: {response.text}")
        
        # 验证任务已删除
        status = self._get_task_status(task_id)
        self.assertIsNone(status, "任务删除后仍然存在")
        
        # 从测试任务列表中移除（避免重复删除）
        if task_id in self.test_tasks:
            self.test_tasks.remove(task_id)
        
        print(f"✅ 任务删除成功，ID: {task_id}")

if __name__ == '__main__':
    print("🚀 开始API功能测试...")
    print("="*60)
    
    # 运行测试
    unittest.main(verbosity=2)