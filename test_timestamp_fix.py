#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试时间戳修复后的飞书同步功能
"""

import requests
import json
from datetime import datetime
import time

def test_feishu_sync_with_timestamp_fix():
    """测试修复后的飞书同步功能"""
    base_url = "http://localhost:8090"
    
    print("🚀 测试时间戳修复后的飞书同步功能")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        # 1. 获取任务列表
        print("\n📋 步骤1: 获取任务列表")
        response = requests.get(f"{base_url}/api/tasks")
        
        if response.status_code != 200:
            print(f"❌ 获取任务列表失败: {response.status_code}")
            return False
            
        tasks = response.json()
        print(f"✅ 成功获取任务列表，共 {len(tasks)} 个任务")
        
        # 找到一个已完成的任务
        completed_tasks = [task for task in tasks if task.get('status') == 'completed']
        if not completed_tasks:
            print("❌ 没有找到已完成的任务")
            return False
            
        # 选择第一个已完成的任务
        test_task = completed_tasks[0]
        task_id = test_task['id']
        task_name = test_task['name']
        
        print(f"🎯 选择任务 #{task_id}: {task_name} 进行测试")
        
        # 2. 测试飞书同步
        print(f"\n🔄 步骤2: 测试任务 #{task_id} 的飞书同步（关注时间戳处理）")
        sync_url = f"{base_url}/api/data/sync_feishu/{task_id}"
        print(f"📡 发送同步请求到: {sync_url}")
        
        # 发送同步请求
        sync_response = requests.post(sync_url)
        print(f"📊 同步响应状态码: {sync_response.status_code}")
        
        if sync_response.status_code == 200:
            print("✅ 飞书同步响应成功")
            try:
                sync_result = sync_response.json()
                print(f"📋 响应内容: {json.dumps(sync_result, indent=2, ensure_ascii=False)}")
                
                if sync_result.get('success'):
                    print("🎉 飞书同步成功!")
                    print(f"📊 同步统计: {sync_result.get('message', '无详细信息')}")
                    
                    # 等待一下让日志输出完整
                    print("\n⏳ 等待5秒，让服务器日志输出完整...")
                    time.sleep(5)
                    
                    return True
                else:
                    print(f"❌ 飞书同步失败: {sync_result.get('message', '未知错误')}")
                    return False
                    
            except json.JSONDecodeError:
                print(f"❌ 响应内容不是有效的JSON: {sync_response.text}")
                return False
        else:
            print(f"❌ 飞书同步请求失败: {sync_response.status_code}")
            print(f"错误内容: {sync_response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到Web应用，请确保应用正在运行")
        return False
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    success = test_feishu_sync_with_timestamp_fix()
    
    print("\n" + "=" * 60)
    if success:
        print("🏁 时间戳修复测试完成 - 成功")
        print("💡 请查看Web应用的控制台日志，确认时间戳处理是否正确")
        print("🔍 特别关注日志中的时间戳格式（应该是秒级而非毫秒级）")
    else:
        print("🏁 时间戳修复测试完成 - 失败")
        print("💡 请检查Web应用状态和错误日志")