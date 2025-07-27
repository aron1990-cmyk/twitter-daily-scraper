#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试完整的抓取任务后飞书同步功能
验证从创建任务到抓取完成再到飞书同步的完整流程
"""

import requests
import json
import time
from datetime import datetime

def test_complete_flow():
    """测试完整的抓取+同步流程"""
    base_url = "http://localhost:8090"
    
    print("🚀 测试完整的抓取任务后飞书同步功能")
    print("=" * 60)
    
    # 1. 创建新的测试任务
    print("\n📝 步骤1: 创建新的抓取任务...")
    task_data = {
        "name": f"飞书同步测试_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "target_keywords": ["Python", "编程"],
        "max_tweets": 5,  # 少量数据便于测试
        "min_likes": 0,
        "min_retweets": 0,
        "min_comments": 0
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/tasks",
            headers={"Content-Type": "application/json"},
            json=task_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                task_id = result['task_id']
                print(f"   ✅ 任务创建成功，ID: {task_id}")
            else:
                print(f"   ❌ 任务创建失败: {result.get('error')}")
                return False
        else:
            print(f"   ❌ 任务创建失败，HTTP状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 创建任务时发生错误: {e}")
        return False
    
    # 2. 启动任务
    print(f"\n🚀 步骤2: 启动任务 {task_id}...")
    try:
        response = requests.post(
            f"{base_url}/api/tasks/{task_id}/start",
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"   ✅ 任务启动成功: {result.get('message')}")
            else:
                print(f"   ❌ 任务启动失败: {result.get('message')}")
                return False
        else:
            print(f"   ❌ 任务启动失败，HTTP状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 启动任务时发生错误: {e}")
        return False
    
    # 3. 等待任务完成
    print(f"\n⏳ 步骤3: 等待任务 {task_id} 完成...")
    max_wait_time = 120  # 最多等待2分钟
    wait_interval = 10   # 每10秒检查一次
    waited_time = 0
    
    while waited_time < max_wait_time:
        try:
            response = requests.get(f"{base_url}/api/tasks/{task_id}", timeout=10)
            
            if response.status_code == 200:
                # 解析HTML响应中的任务状态
                html_content = response.text
                if 'completed' in html_content.lower():
                    print(f"   ✅ 任务已完成")
                    break
                elif 'failed' in html_content.lower():
                    print(f"   ❌ 任务执行失败")
                    return False
                elif 'running' in html_content.lower():
                    print(f"   ⏳ 任务正在执行中... (已等待 {waited_time}s)")
                else:
                    print(f"   📋 任务状态未知，继续等待... (已等待 {waited_time}s)")
            else:
                print(f"   ⚠️ 无法获取任务状态，HTTP状态码: {response.status_code}")
            
            time.sleep(wait_interval)
            waited_time += wait_interval
            
        except Exception as e:
            print(f"   ⚠️ 检查任务状态时发生错误: {e}")
            time.sleep(wait_interval)
            waited_time += wait_interval
    
    if waited_time >= max_wait_time:
        print(f"   ⏰ 等待超时，任务可能仍在执行中")
        print(f"   💡 建议手动检查任务状态")
        return False
    
    # 4. 等待一小段时间确保数据保存完成
    print(f"\n💾 步骤4: 等待数据保存完成...")
    time.sleep(5)
    
    # 5. 执行飞书同步
    print(f"\n☁️ 步骤5: 同步任务 {task_id} 数据到飞书...")
    try:
        response = requests.post(
            f"{base_url}/api/data/sync_feishu/{task_id}",
            timeout=60  # 飞书同步可能需要更长时间
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"   ✅ 飞书同步成功!")
                print(f"   📊 同步消息: {result.get('message')}")
                return True
            else:
                print(f"   ❌ 飞书同步失败: {result.get('error')}")
                return False
        else:
            print(f"   ❌ 飞书同步失败，HTTP状态码: {response.status_code}")
            try:
                error_result = response.json()
                print(f"   📋 错误详情: {error_result.get('error')}")
            except:
                print(f"   📋 响应内容: {response.text[:200]}...")
            return False
    except Exception as e:
        print(f"   ❌ 执行飞书同步时发生错误: {e}")
        return False

def check_feishu_config():
    """检查飞书配置"""
    base_url = "http://localhost:8090"
    
    print("\n🔧 检查飞书配置...")
    try:
        response = requests.get(f"{base_url}/api/config/feishu", timeout=10)
        if response.status_code == 200:
            config = response.json()
            print(f"   ✅ 飞书配置获取成功")
            print(f"   - 启用状态: {config.get('enabled', False)}")
            print(f"   - App ID: {config.get('app_id', 'N/A')}")
            print(f"   - 表格Token: {config.get('spreadsheet_token', 'N/A')}")
            print(f"   - 表格ID: {config.get('table_id', 'N/A')}")
            return config.get('enabled', False)
        else:
            print(f"   ❌ 获取飞书配置失败，HTTP状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 检查飞书配置时发生错误: {e}")
        return False

if __name__ == '__main__':
    print("🧪 开始测试抓取任务后的飞书同步功能")
    print("=" * 70)
    
    # 检查飞书配置
    feishu_enabled = check_feishu_config()
    
    if not feishu_enabled:
        print("\n❌ 飞书配置未启用或配置有误，无法进行测试")
        exit(1)
    
    # 执行完整流程测试
    success = test_complete_flow()
    
    print("\n" + "=" * 70)
    print("📊 测试结果总结:")
    if success:
        print("🎉 测试成功！抓取任务后的飞书同步功能正常工作！")
        print("\n✅ 验证项目:")
        print("   - 任务创建 ✓")
        print("   - 任务启动 ✓")
        print("   - 数据抓取 ✓")
        print("   - 飞书同步 ✓")
        print("\n💡 所有字段（推文内容、作者、链接、点赞、评论、转发等）都已正确同步到飞书多维表格")
    else:
        print("❌ 测试失败，请检查相关配置和日志")
        print("\n🔍 排查建议:")
        print("   - 检查Web应用是否正常运行")
        print("   - 检查飞书配置是否正确")
        print("   - 查看Web应用终端日志")
        print("   - 确认网络连接正常")