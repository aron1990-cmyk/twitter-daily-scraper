#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终飞书同步功能验证测试
验证所有修复是否生效
"""

import requests
import json
import time
from datetime import datetime

def test_complete_feishu_functionality():
    """完整测试飞书同步功能"""
    print("🔍 最终飞书同步功能验证测试")
    print("=" * 60)
    
    base_url = "http://localhost:8090"
    
    # 1. 检查Web应用状态
    print("\n📊 步骤1: 检查Web应用状态")
    try:
        response = requests.get(f"{base_url}/api/status", timeout=10)
        if response.status_code == 200:
            status_data = response.json()
            print(f"   ✅ Web应用运行正常")
            print(f"   📈 总任务数: {status_data.get('total_tasks', 0)}")
            print(f"   📝 总推文数: {status_data.get('total_tweets', 0)}")
        else:
            print(f"   ❌ Web应用状态异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 无法连接Web应用: {e}")
        return False
    
    # 2. 获取最新任务
    print("\n📋 步骤2: 获取最新任务数据")
    try:
        response = requests.get(f"{base_url}/api/tasks", timeout=10)
        if response.status_code == 200:
            tasks = response.json()
            if not tasks:
                print("   ❌ 没有找到任务数据")
                return False
            
            # 找到最新的已完成任务
            completed_tasks = [t for t in tasks if t.get('status') == 'completed' and t.get('result_count', 0) > 0]
            if not completed_tasks:
                print("   ❌ 没有找到已完成的任务")
                return False
            
            latest_task = max(completed_tasks, key=lambda x: x.get('id', 0))
            task_id = latest_task['id']
            print(f"   ✅ 找到最新任务: ID={task_id}, 名称={latest_task.get('name', 'N/A')}")
            print(f"   📊 推文数量: {latest_task.get('result_count', 0)}")
        else:
            print(f"   ❌ 获取任务列表失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 获取任务数据异常: {e}")
        return False
    
    # 3. 检查任务推文数据
    print(f"\n📝 步骤3: 检查任务 {task_id} 的推文数据")
    try:
        response = requests.get(f"{base_url}/api/tasks/{task_id}/tweets", timeout=10)
        if response.status_code == 200:
            tweets_data = response.json()
            if tweets_data.get('success'):
                tweets = tweets_data.get('tweets', [])
                if not tweets:
                    print("   ❌ 任务没有推文数据")
                    return False
                
                print(f"   ✅ 找到 {len(tweets)} 条推文")
                
                # 检查数据完整性
                sample_tweet = tweets[0]
                print(f"   📊 示例推文数据:")
                print(f"      - 内容: {(sample_tweet.get('content', '') or '空')[:50]}...")
                print(f"      - 作者: {sample_tweet.get('username', '') or '空'}")
                print(f"      - 链接: {sample_tweet.get('link', '') or '空'}")
                print(f"      - 同步状态: {'已同步' if sample_tweet.get('synced_to_feishu') else '未同步'}")
                
                # 统计未同步数据
                unsynced_count = len([t for t in tweets if not t.get('synced_to_feishu')])
                print(f"   📊 未同步推文数量: {unsynced_count}")
            else:
                print(f"   ❌ API返回错误: {tweets_data.get('error', '未知错误')}")
                return False
        else:
            print(f"   ❌ 获取推文数据失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 获取推文数据异常: {e}")
        return False
    
    # 4. 测试飞书同步
    print(f"\n🚀 步骤4: 测试飞书同步功能")
    try:
        print(f"   🔄 开始同步任务 {task_id} 到飞书...")
        response = requests.post(f"{base_url}/api/data/sync_feishu/{task_id}", timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"   ✅ 飞书同步成功: {result.get('message', '')}")
            else:
                print(f"   ❌ 飞书同步失败: {result.get('error', '')}")
                return False
        else:
            print(f"   ❌ 飞书同步请求失败: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   📋 错误详情: {error_data.get('error', '')}")
            except:
                print(f"   📋 响应内容: {response.text[:200]}...")
            return False
    except Exception as e:
        print(f"   ❌ 飞书同步异常: {e}")
        return False
    
    # 5. 验证同步结果
    print(f"\n✅ 步骤5: 验证同步结果")
    try:
        # 等待一下让数据库更新
        time.sleep(2)
        
        response = requests.get(f"{base_url}/api/tasks/{task_id}/tweets", timeout=10)
        if response.status_code == 200:
            tweets_data = response.json()
            if tweets_data.get('success'):
                tweets = tweets_data.get('tweets', [])
                
                synced_count = len([t for t in tweets if t.get('synced_to_feishu')])
                total_count = len(tweets)
                
                print(f"   📊 同步统计:")
                print(f"      - 总推文数: {total_count}")
                print(f"      - 已同步数: {synced_count}")
                print(f"      - 同步率: {(synced_count/total_count*100):.1f}%")
                
                if synced_count == total_count:
                    print(f"   ✅ 所有数据已成功同步到飞书")
                    return True
                else:
                    print(f"   ⚠️ 部分数据未同步")
                    return False
            else:
                print(f"   ❌ API返回错误: {tweets_data.get('error', '未知错误')}")
                return False
        else:
            print(f"   ❌ 验证同步结果失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 验证同步结果异常: {e}")
        return False

def main():
    """主函数"""
    print(f"🧪 飞书同步功能最终验证")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    success = test_complete_feishu_functionality()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 飞书同步功能验证通过！所有功能正常工作。")
        print("✅ 可以确认现在飞书同步功能已完全修复。")
    else:
        print("❌ 飞书同步功能验证失败！仍存在问题需要修复。")
        print("🔧 请检查上述错误信息并进行相应修复。")
    
    return success

if __name__ == "__main__":
    main()