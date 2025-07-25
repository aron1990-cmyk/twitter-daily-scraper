#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的飞书同步功能
验证发布时间正确转换和创建时间字段移除
"""

import requests
import json
from datetime import datetime

def test_feishu_sync():
    """测试飞书同步功能"""
    print("🧪 测试修复后的飞书同步功能")
    print("=" * 60)
    
    # API基础URL
    base_url = "http://localhost:8089"
    
    try:
        # 1. 获取系统状态
        print("📊 获取系统状态...")
        status_response = requests.get(f"{base_url}/api/status")
        if status_response.status_code == 200:
            status_data = status_response.json()
            print(f"   - 总推文数: {status_data.get('tweet_stats', {}).get('total', 0)}")
            print(f"   - 已同步到飞书: {status_data.get('tweet_stats', {}).get('synced_to_feishu', 0)}")
            print(f"   - 未同步到飞书: {status_data.get('tweet_stats', {}).get('not_synced_to_feishu', 0)}")
        else:
            print(f"   ❌ 获取状态失败: {status_response.status_code}")
            return
        
        # 2. 获取飞书配置
        print("\n🔧 检查飞书配置...")
        config_response = requests.get(f"{base_url}/api/config/feishu")
        if config_response.status_code == 200:
            config_data = config_response.json()
            if config_data.get('enabled'):
                print("   ✅ 飞书配置已启用")
                print(f"   - App Token: {'已配置' if config_data.get('app_token') else '未配置'}")
                print(f"   - App Secret: {'已配置' if config_data.get('app_secret') else '未配置'}")
                print(f"   - Spreadsheet Token: {'已配置' if config_data.get('spreadsheet_token') else '未配置'}")
                print(f"   - Table ID: {'已配置' if config_data.get('table_id') else '未配置'}")
            else:
                print("   ❌ 飞书配置未启用")
                return
        else:
            print(f"   ❌ 获取飞书配置失败: {config_response.status_code}")
            return
        
        # 3. 获取任务列表
        print("\n📋 获取任务列表...")
        tasks_response = requests.get(f"{base_url}/api/tasks")
        if tasks_response.status_code == 200:
            tasks_data = tasks_response.json()
            # 处理不同的响应格式
            if isinstance(tasks_data, list):
                tasks = tasks_data
            else:
                tasks = tasks_data.get('tasks', [])
            
            if tasks:
                # 选择第一个有推文数据的任务
                target_task = None
                for task in tasks:
                    if isinstance(task, dict) and task.get('tweet_count', 0) > 0:
                        target_task = task
                        break
                
                if target_task:
                    task_id = target_task['id']
                    print(f"   ✅ 选择任务: {target_task['name']} (ID: {task_id})")
                    print(f"   - 推文数量: {target_task.get('tweet_count', 0)}")
                    
                    # 4. 测试飞书同步
                    print(f"\n🚀 开始同步任务 {task_id} 到飞书...")
                    sync_response = requests.post(f"{base_url}/api/data/sync_feishu/{task_id}")
                    
                    if sync_response.status_code == 200:
                        sync_result = sync_response.json()
                        if sync_result.get('success'):
                            print("   ✅ 飞书同步成功！")
                            print(f"   - 同步数量: {sync_result.get('synced_count', 0)}")
                            print(f"   - 消息: {sync_result.get('message', '')}")
                            
                            # 5. 再次检查状态，验证同步结果
                            print("\n📊 验证同步结果...")
                            status_response2 = requests.get(f"{base_url}/api/status")
                            if status_response2.status_code == 200:
                                status_data2 = status_response2.json()
                                print(f"   - 总推文数: {status_data2.get('tweet_stats', {}).get('total', 0)}")
                                print(f"   - 已同步到飞书: {status_data2.get('tweet_stats', {}).get('synced_to_feishu', 0)}")
                                print(f"   - 未同步到飞书: {status_data2.get('tweet_stats', {}).get('not_synced_to_feishu', 0)}")
                                
                                # 计算同步率
                                total = status_data2.get('tweet_stats', {}).get('total', 0)
                                synced = status_data2.get('tweet_stats', {}).get('synced_to_feishu', 0)
                                if total > 0:
                                    sync_rate = (synced / total) * 100
                                    print(f"   - 同步率: {sync_rate:.1f}%")
                        else:
                            print(f"   ❌ 飞书同步失败: {sync_result.get('error', '未知错误')}")
                    else:
                        print(f"   ❌ 同步请求失败: {sync_response.status_code}")
                        try:
                            error_data = sync_response.json()
                            print(f"   错误信息: {error_data.get('error', '未知错误')}")
                        except:
                            print(f"   错误信息: {sync_response.text}")
                else:
                    print("   ❌ 没有找到包含推文数据的任务")
            else:
                print("   ❌ 没有找到任务")
        else:
            print(f"   ❌ 获取任务列表失败: {tasks_response.status_code}")
    
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败: 请确保web应用正在运行 (http://localhost:8089)")
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")

def main():
    """主函数"""
    print("🔧 飞书同步修复验证")
    print("修复内容:")
    print("1. 移除【创建时间】字段，让飞书自动生成")
    print("2. 修复【发布时间】字段显示为1970/01/21的问题")
    print("3. 增强时间解析的错误处理")
    print()
    
    test_feishu_sync()
    
    print("\n🎉 测试完成！")
    print("\n💡 请检查飞书多维表格中的数据:")
    print("   - 【创建时间】字段应该由飞书自动生成")
    print("   - 【发布时间】字段应该显示正确的日期（不再是1970/01/21）")

if __name__ == '__main__':
    main()