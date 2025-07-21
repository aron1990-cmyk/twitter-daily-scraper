#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断任务管理器状态
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import ADS_POWER_CONFIG
import requests
import json

def check_adspower_api():
    """检查AdsPower API连接"""
    api_url = ADS_POWER_CONFIG['local_api_url']
    print(f"检查AdsPower API: {api_url}")
    
    try:
        response = requests.get(f"{api_url}/api/v1/user/list", timeout=5)
        print(f"API响应状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"API响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"API响应错误: {response.text}")
            return False
    except Exception as e:
        print(f"API连接失败: {str(e)}")
        return False

def check_user_ids():
    """检查用户ID配置"""
    print("\n检查用户ID配置:")
    print(f"主用户ID: {ADS_POWER_CONFIG['user_id']}")
    print(f"多用户ID列表: {ADS_POWER_CONFIG['multi_user_ids']}")
    print(f"最大并发任务数: {ADS_POWER_CONFIG['max_concurrent_tasks']}")
    
    # 检查每个用户ID的状态
    api_url = ADS_POWER_CONFIG['local_api_url']
    for user_id in ADS_POWER_CONFIG['multi_user_ids']:
        try:
            response = requests.get(f"{api_url}/api/v1/user/list?user_id={user_id}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"用户ID {user_id}: {data.get('msg', '未知状态')}")
            else:
                print(f"用户ID {user_id}: API错误 - {response.status_code}")
        except Exception as e:
            print(f"用户ID {user_id}: 检查失败 - {str(e)}")

def check_task_manager_status():
    """检查任务管理器状态"""
    print("\n检查任务管理器状态:")
    try:
        response = requests.get("http://127.0.0.1:8086/api/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                parallel_status = data['data']['parallel_status']
                print(f"运行中任务数: {parallel_status['running_count']}")
                print(f"最大并发数: {parallel_status['max_concurrent']}")
                print(f"可用槽位: {parallel_status['available_slots']}")
                print(f"可用浏览器: {parallel_status['available_browsers']}")
                print(f"当前任务: {parallel_status['current_tasks']}")
                
                if parallel_status['available_browsers'] == 0:
                    print("\n❌ 问题发现: 没有可用的浏览器资源!")
                    print("这可能是因为:")
                    print("1. AdsPower用户ID配置错误")
                    print("2. AdsPower服务未运行")
                    print("3. 用户ID池被耗尽")
                else:
                    print("\n✅ 浏览器资源正常")
            else:
                print(f"API错误: {data.get('error')}")
        else:
            print(f"Web应用API错误: {response.status_code}")
    except Exception as e:
        print(f"检查任务管理器状态失败: {str(e)}")

def main():
    print("=== Twitter抓取系统诊断 ===")
    
    # 检查AdsPower API
    api_ok = check_adspower_api()
    
    # 检查用户ID配置
    check_user_ids()
    
    # 检查任务管理器状态
    check_task_manager_status()
    
    print("\n=== 诊断完成 ===")
    
    if not api_ok:
        print("\n建议解决方案:")
        print("1. 确保AdsPower应用正在运行")
        print("2. 检查AdsPower Local API是否启用")
        print("3. 验证API地址是否正确: http://local.adspower.net:50325")

if __name__ == '__main__':
    main()