#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试用户轮询机制
"""

import requests
import time
import json

def test_user_rotation():
    """测试用户轮询机制"""
    print("=== 测试用户轮询机制 ===")
    
    # 检查系统状态
    print("\n1. 检查系统状态:")
    try:
        response = requests.get("http://127.0.0.1:8086/api/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                parallel_status = data['data']['parallel_status']
                print(f"✅ 系统状态正常")
                print(f"   - 可用浏览器: {parallel_status['available_browsers']}")
                print(f"   - 可用槽位: {parallel_status['available_slots']}")
                print(f"   - 最大并发: {parallel_status['max_concurrent']}")
                print(f"   - 运行中任务: {parallel_status['running_count']}")
            else:
                print("❌ 系统状态异常")
                return
        else:
            print(f"❌ API响应错误: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return
    
    # 测试AdsPower用户ID可用性
    print("\n2. 测试AdsPower用户ID:")
    from config import ADS_POWER_CONFIG
    
    api_url = ADS_POWER_CONFIG['local_api_url']
    user_ids = ADS_POWER_CONFIG['multi_user_ids']
    
    print(f"配置的用户ID: {user_ids}")
    
    for user_id in user_ids:
        try:
            # 测试用户ID状态
            response = requests.get(f"{api_url}/api/v1/user/list?user_id={user_id}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0 and data.get('data', {}).get('list'):
                    print(f"✅ 用户ID {user_id}: 可用")
                else:
                    print(f"❌ 用户ID {user_id}: 不存在或不可用")
            else:
                print(f"❌ 用户ID {user_id}: API错误 {response.status_code}")
                
            # 添加请求间隔
            time.sleep(ADS_POWER_CONFIG.get('request_interval', 2.0))
            
        except Exception as e:
            print(f"❌ 用户ID {user_id}: 请求失败 - {e}")
    
    # 测试任务创建（模拟）
    print("\n3. 测试任务管理器轮询机制:")
    print("模拟创建多个任务以测试用户ID轮询...")
    
    # 创建测试任务数据
    test_tasks = [
        {
            'task_name': f'测试任务_{i+1}',
            'keywords': 'AI,人工智能',
            'target_accounts': '',
            'max_tweets': 10
        }
        for i in range(3)  # 创建3个测试任务
    ]
    
    created_tasks = []
    
    for i, task_data in enumerate(test_tasks):
        try:
            print(f"\n创建任务 {i+1}: {task_data['task_name']}")
            
            # 发送POST请求创建任务
            response = requests.post(
                "http://127.0.0.1:8086/create_task",
                data=task_data,
                timeout=10
            )
            
            if response.status_code == 200 or response.status_code == 302:  # 302是重定向
                print(f"✅ 任务 {i+1} 创建成功")
                created_tasks.append(i+1)
            else:
                print(f"❌ 任务 {i+1} 创建失败: {response.status_code}")
                print(f"响应内容: {response.text[:200]}...")
            
            # 检查系统状态变化
            time.sleep(1)
            status_response = requests.get("http://127.0.0.1:8086/api/status", timeout=5)
            if status_response.status_code == 200:
                status_data = status_response.json()
                if status_data.get('success'):
                    parallel_status = status_data['data']['parallel_status']
                    print(f"   当前运行任务数: {parallel_status['running_count']}")
                    print(f"   可用浏览器: {parallel_status['available_browsers']}")
            
            # 添加间隔避免频率限制
            time.sleep(3)
            
        except Exception as e:
            print(f"❌ 创建任务 {i+1} 时出错: {e}")
    
    print(f"\n=== 测试完成 ===")
    print(f"成功创建任务数: {len(created_tasks)}")
    print("\n轮询机制特性:")
    print(f"- 请求间隔: {ADS_POWER_CONFIG.get('request_interval', 2.0)}秒")
    print(f"- 用户轮询: {ADS_POWER_CONFIG.get('user_rotation_enabled', True)}")
    print(f"- 用户切换间隔: {ADS_POWER_CONFIG.get('user_switch_interval', 30)}秒")
    print(f"- API重试延迟: {ADS_POWER_CONFIG.get('api_retry_delay', 5.0)}秒")

if __name__ == "__main__":
    test_user_rotation()