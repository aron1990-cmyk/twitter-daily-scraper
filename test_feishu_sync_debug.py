#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试飞书同步功能并观察详细日志
"""

import requests
import json
import time
from datetime import datetime

def test_feishu_sync():
    """
    测试飞书同步功能
    """
    base_url = "http://localhost:8090"
    
    print("🚀 开始测试飞书同步功能")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # 1. 首先获取所有任务列表
    print("\n📋 步骤1: 获取任务列表")
    try:
        response = requests.get(f"{base_url}/api/tasks", timeout=10)
        if response.status_code == 200:
            tasks = response.json()
            print(f"✅ 成功获取任务列表，共 {len(tasks)} 个任务")
            
            # 显示任务信息
            for task in tasks:
                task_id = task.get('id')
                task_name = task.get('name', 'N/A')
                status = task.get('status', 'N/A')
                print(f"   - 任务 #{task_id}: {task_name} (状态: {status})")
                
            # 选择一个已完成的任务进行测试
            completed_tasks = [t for t in tasks if t.get('status') == 'completed']
            if completed_tasks:
                test_task = completed_tasks[0]
                task_id = test_task['id']
                print(f"\n🎯 选择任务 #{task_id} 进行飞书同步测试")
            else:
                print("❌ 没有找到已完成的任务")
                return
        else:
            print(f"❌ 获取任务列表失败: HTTP {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 获取任务列表异常: {e}")
        return
    
    # 2. 测试飞书同步
    print(f"\n🔄 步骤2: 测试任务 #{task_id} 的飞书同步")
    try:
        sync_url = f"{base_url}/api/data/sync_feishu/{task_id}"
        print(f"📡 发送同步请求到: {sync_url}")
        
        response = requests.post(sync_url, timeout=30)
        print(f"📊 同步响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 飞书同步响应成功")
            print(f"📋 响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 检查同步结果
            if result.get('success'):
                print(f"🎉 飞书同步成功!")
                print(f"📊 同步统计: {result.get('message', 'N/A')}")
            else:
                print(f"❌ 飞书同步失败: {result.get('message', 'N/A')}")
        else:
            print(f"❌ 飞书同步请求失败: HTTP {response.status_code}")
            print(f"📋 错误响应: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ 飞书同步异常: {e}")
        import traceback
        print(f"📋 异常详情: {traceback.format_exc()}")
    
    # 3. 等待一下，让日志输出完整
    print("\n⏳ 等待3秒，让服务器日志输出完整...")
    time.sleep(3)
    
    print("\n" + "="*60)
    print("🏁 飞书同步测试完成")
    print("💡 请查看Web应用的控制台日志以获取详细的同步过程信息")

if __name__ == "__main__":
    test_feishu_sync()