#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Web应用的飞书同步API
实际调用API来验证修复效果
"""

import requests
import json
import time

def test_web_api_sync():
    """测试web应用的飞书同步API"""
    base_url = "http://127.0.0.1:8080"
    
    print("🧪 测试Web应用飞书同步API")
    print("=" * 50)
    
    # 1. 检查web应用是否运行
    print("\n🔍 检查Web应用状态...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("   ✅ Web应用正在运行")
        else:
            print(f"   ❌ Web应用响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 无法连接到Web应用: {e}")
        return False
    
    # 2. 获取任务列表
    print("\n📋 获取任务列表...")
    try:
        response = requests.get(f"{base_url}/api/tasks", timeout=10)
        if response.status_code == 200:
            tasks = response.json()
            print(f"   ✅ 获取到 {len(tasks)} 个任务")
            
            # 找到已完成的任务
            completed_tasks = [task for task in tasks if task['status'] == 'completed']
            if not completed_tasks:
                print("   ❌ 没有已完成的任务可供测试")
                return False
            
            test_task = completed_tasks[0]
            print(f"   ✅ 选择测试任务: {test_task['name']} (ID: {test_task['id']})")
        else:
            print(f"   ❌ 获取任务列表失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 获取任务列表时发生错误: {e}")
        return False
    
    # 3. 测试飞书同步API
    print(f"\n☁️ 测试任务 {test_task['id']} 的飞书同步...")
    try:
        sync_url = f"{base_url}/api/data/sync_feishu/{test_task['id']}"
        print(f"   调用API: {sync_url}")
        
        response = requests.post(sync_url, timeout=30)
        print(f"   响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 同步成功!")
            print(f"   - 成功: {result.get('success', False)}")
            if 'message' in result:
                print(f"   - 消息: {result['message']}")
            if 'synced_count' in result:
                print(f"   - 同步数量: {result['synced_count']}")
            return True
        else:
            try:
                error_result = response.json()
                print(f"   ❌ 同步失败: {error_result.get('error', '未知错误')}")
            except:
                print(f"   ❌ 同步失败: HTTP {response.status_code}")
                print(f"   响应内容: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"   ❌ 调用同步API时发生错误: {e}")
        return False
    
    # 4. 检查飞书配置API
    print("\n🔧 检查飞书配置API...")
    try:
        response = requests.get(f"{base_url}/api/config/feishu", timeout=10)
        if response.status_code == 200:
            config = response.json()
            print(f"   ✅ 飞书配置API正常")
            print(f"   - 启用状态: {config.get('enabled', False)}")
            print(f"   - 自动同步: {config.get('auto_sync', False)}")
        else:
            print(f"   ⚠️ 飞书配置API响应异常: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️ 检查飞书配置API时发生错误: {e}")

def test_feishu_config_api():
    """测试飞书配置API"""
    base_url = "http://127.0.0.1:8080"
    
    print("\n🔧 测试飞书配置API")
    print("=" * 30)
    
    try:
        response = requests.get(f"{base_url}/api/config/feishu", timeout=10)
        if response.status_code == 200:
            config = response.json()
            print(f"   ✅ 获取飞书配置成功")
            print(f"   - App ID: {config.get('app_id', 'N/A')}")
            print(f"   - App Secret: {'已配置' if config.get('app_secret') else '未配置'}")
            print(f"   - Spreadsheet Token: {config.get('spreadsheet_token', 'N/A')}")
            print(f"   - Table ID: {config.get('table_id', 'N/A')}")
            print(f"   - 启用状态: {config.get('enabled', False)}")
            print(f"   - 自动同步: {config.get('auto_sync', False)}")
            return True
        else:
            print(f"   ❌ 获取飞书配置失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 测试飞书配置API时发生错误: {e}")
        return False

if __name__ == '__main__':
    print("🚀 开始Web应用飞书同步API测试")
    print("=" * 60)
    
    # 测试飞书配置API
    config_success = test_feishu_config_api()
    
    # 测试同步API
    sync_success = test_web_api_sync()
    
    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    print(f"   - 飞书配置API: {'✅ 通过' if config_success else '❌ 失败'}")
    print(f"   - 飞书同步API: {'✅ 通过' if sync_success else '❌ 失败'}")
    
    if config_success and sync_success:
        print("\n🎉 所有测试通过！Web应用飞书同步功能正常！")
    else:
        print("\n❌ 部分测试失败，需要进一步检查")