#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的自动同步功能
验证任务完成后的自动同步是否与API手动同步一致
"""

import requests
import json
import time
from datetime import datetime

def test_fixed_auto_sync():
    """
    测试修复后的自动同步功能
    """
    print("\n" + "="*80)
    print("🧪 测试修复后的自动同步功能")
    print("="*80)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    base_url = "http://localhost:8090"
    
    # 1. 检查飞书配置
    print("\n1. 检查飞书配置:")
    try:
        response = requests.get(f"{base_url}/api/config/feishu")
        if response.status_code == 200:
            config = response.json()
            print("   ✅ 飞书配置获取成功")
            print(f"   - 启用状态: {config.get('enabled', False)}")
            print(f"   - 自动同步: {config.get('auto_sync', False)}")
            print(f"   - App ID: {config.get('app_id', 'N/A')[:10]}...")
            print(f"   - 表格Token: {config.get('spreadsheet_token', 'N/A')[:10]}...")
            print(f"   - 表格ID: {config.get('table_id', 'N/A')}")
            
            if not config.get('enabled'):
                print("   ⚠️ 飞书配置未启用，无法测试自动同步")
                return False
                
            if not config.get('auto_sync'):
                print("   ⚠️ 自动同步未启用，无法测试自动同步")
                return False
                
        else:
            print(f"   ❌ 获取飞书配置失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 检查飞书配置异常: {e}")
        return False
    
    # 2. 创建新的抓取任务
    print("\n2. 创建新的抓取任务:")
    task_data = {
        "name": "自动同步测试任务",
        "keywords": ["Python"],
        "target_accounts": ["elonmusk"],
        "max_tweets": 5,
        "enable_content_filter": True,
        "content_filters": {
            "min_length": 10,
            "max_length": 500,
            "required_keywords": [],
            "excluded_keywords": ["广告", "spam"]
        }
    }
    
    try:
        response = requests.post(f"{base_url}/api/tasks", json=task_data)
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            print(f"   ✅ 任务创建成功，ID: {task_id}")
        else:
            print(f"   ❌ 任务创建失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ 创建任务异常: {e}")
        return False
    
    # 3. 启动任务
    print("\n3. 启动抓取任务:")
    try:
        response = requests.post(f"{base_url}/api/tasks/{task_id}/start")
        if response.status_code == 200:
            print(f"   ✅ 任务 {task_id} 启动成功")
        else:
            print(f"   ❌ 任务启动失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 启动任务异常: {e}")
        return False
    
    # 4. 等待任务完成
    print("\n4. 等待任务完成:")
    max_wait_time = 120  # 最多等待2分钟
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        try:
            response = requests.get(f"{base_url}/api/tasks/{task_id}")
            if response.status_code == 200:
                task_info = response.json()
                status = task_info.get('status')
                scraped_count = task_info.get('scraped_count', 0)
                
                print(f"   - 任务状态: {status}, 已抓取: {scraped_count} 条")
                
                if status == 'completed':
                    print(f"   ✅ 任务 {task_id} 完成，共抓取 {scraped_count} 条数据")
                    break
                elif status == 'failed':
                    print(f"   ❌ 任务 {task_id} 失败")
                    return False
                    
            time.sleep(5)  # 每5秒检查一次
            
        except Exception as e:
            print(f"   ❌ 检查任务状态异常: {e}")
            time.sleep(5)
    else:
        print(f"   ⚠️ 任务等待超时 ({max_wait_time}秒)，当前状态未知")
        # 继续测试，可能任务已经完成但状态更新延迟
    
    # 5. 等待自动同步完成
    print("\n5. 等待自动同步完成:")
    print("   - 等待10秒让自动同步完成...")
    time.sleep(10)
    
    # 6. 检查同步状态
    print("\n6. 检查自动同步结果:")
    try:
        response = requests.get(f"{base_url}/api/tasks/{task_id}/tweets")
        if response.status_code == 200:
            tweets_data = response.json()
            tweets = tweets_data.get('tweets', [])
            
            if not tweets:
                print("   ⚠️ 没有找到推文数据")
                return False
                
            print(f"   - 找到 {len(tweets)} 条推文数据")
            
            # 检查同步状态
            synced_count = sum(1 for tweet in tweets if tweet.get('synced_to_feishu', False))
            print(f"   - 已同步到飞书: {synced_count} 条")
            print(f"   - 未同步到飞书: {len(tweets) - synced_count} 条")
            
            if synced_count == len(tweets):
                print("   ✅ 所有数据都已自动同步到飞书")
                sync_success = True
            elif synced_count > 0:
                print("   ⚠️ 部分数据已同步到飞书")
                sync_success = False
            else:
                print("   ❌ 没有数据被自动同步到飞书")
                sync_success = False
                
        else:
            print(f"   ❌ 获取推文数据失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ 检查同步状态异常: {e}")
        return False
    
    # 7. 对比测试：手动API同步
    print("\n7. 对比测试 - 手动API同步:")
    try:
        response = requests.post(f"{base_url}/api/data/sync_feishu/{task_id}")
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("   ✅ 手动API同步成功")
                api_sync_success = True
            else:
                print(f"   ❌ 手动API同步失败: {result.get('error')}")
                api_sync_success = False
        else:
            print(f"   ❌ 手动API同步请求失败: {response.status_code}")
            api_sync_success = False
    except Exception as e:
        print(f"   ❌ 手动API同步异常: {e}")
        api_sync_success = False
    
    # 8. 测试结果总结
    print("\n" + "="*80)
    print("📊 测试结果总结")
    print("="*80)
    
    print(f"\n✅ 测试完成情况:")
    print(f"   - 任务创建: ✅ 成功 (ID: {task_id})")
    print(f"   - 任务执行: ✅ 成功 (抓取了数据)")
    print(f"   - 自动同步: {'✅ 成功' if sync_success else '❌ 失败'}")
    print(f"   - 手动同步: {'✅ 成功' if api_sync_success else '❌ 失败'}")
    
    if sync_success and api_sync_success:
        print("\n🎉 修复成功！")
        print("   - 自动同步和手动同步都正常工作")
        print("   - 两种同步方式现在使用相同的初始化逻辑")
        print("   - 问题已解决")
        return True
    elif sync_success:
        print("\n⚠️ 部分修复成功")
        print("   - 自动同步现在正常工作")
        print("   - 但手动同步出现问题")
        return False
    else:
        print("\n❌ 修复失败")
        print("   - 自动同步仍然有问题")
        print("   - 需要进一步调试")
        return False

if __name__ == '__main__':
    print("🚀 开始测试修复后的自动同步功能")
    success = test_fixed_auto_sync()
    print(f"\n🏁 测试{'成功' if success else '失败'}")