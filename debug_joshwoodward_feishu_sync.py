#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import sys
from datetime import datetime

def debug_joshwoodward_feishu_sync():
    """Debug joshwoodward任务的飞书同步问题"""
    base_url = "http://localhost:8090"
    
    print("=" * 80)
    print("开始Debug joshwoodward任务的飞书同步问题")
    print("=" * 80)
    
    # 步骤1: 根据任务名称joshwoodward查找数据库
    print("\n步骤1: 查找joshwoodward相关任务")
    print("-" * 50)
    
    try:
        # 获取所有任务
        response = requests.get(f"{base_url}/api/tasks")
        if response.status_code != 200:
            print(f"❌ 获取任务列表失败: {response.status_code}")
            return
        
        tasks = response.json()
        print(f"✅ 成功获取 {len(tasks)} 个任务")
        
        # 查找joshwoodward相关任务
        joshwoodward_tasks = []
        for task in tasks:
            target_accounts = task.get('target_accounts', [])
            if isinstance(target_accounts, str):
                target_accounts = [target_accounts]
            
            if 'joshwoodward' in str(target_accounts).lower() or 'joshwoodward' in task.get('name', '').lower():
                joshwoodward_tasks.append(task)
        
        if not joshwoodward_tasks:
            print("❌ 没有找到joshwoodward相关任务")
            print("\n所有任务列表:")
            for task in tasks:
                print(f"  任务ID: {task['id']}, 名称: {task['name']}, 账号: {task.get('target_accounts', [])}")
            return
        
        print(f"✅ 找到 {len(joshwoodward_tasks)} 个joshwoodward相关任务:")
        for task in joshwoodward_tasks:
            print(f"  任务ID: {task['id']}, 名称: {task['name']}, 状态: {task['status']}, 结果数: {task.get('result_count', 0)}")
        
        # 选择最新的已完成任务
        completed_tasks = [t for t in joshwoodward_tasks if t['status'] == 'completed' and t.get('result_count', 0) > 0]
        if not completed_tasks:
            print("❌ 没有找到已完成且有数据的joshwoodward任务")
            return
        
        # 按创建时间排序，选择最新的
        latest_task = max(completed_tasks, key=lambda x: x['created_at'])
        task_id = latest_task['id']
        
        print(f"\n选择最新任务: ID={task_id}, 名称={latest_task['name']}, 结果数={latest_task.get('result_count', 0)}")
        
    except Exception as e:
        print(f"❌ 查找任务时出错: {e}")
        return
    
    # 步骤2: 查找joshwoodward相关的推文数据
    print(f"\n步骤2: 查找任务{task_id}的推文数据")
    print("-" * 50)
    
    try:
        # 获取任务的推文数据 - 使用正确的API路径
        response = requests.get(f"{base_url}/api/data/export/{task_id}")
        if response.status_code != 200:
            print(f"❌ 获取推文数据失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return
        
        tweets_data = response.json()
        tweets = tweets_data.get('data', [])  # 导出API返回的是data字段
        
        if not tweets:
            print("❌ 任务没有推文数据")
            return
        
        print(f"✅ 找到 {len(tweets)} 条推文数据")
        
        # 显示前3条推文的详细信息
        print("\n前3条推文详细信息:")
        for i, tweet in enumerate(tweets[:3], 1):
            print(f"\n推文 {i}:")
            print(f"  ID: {tweet.get('id')}")
            print(f"  内容: {tweet.get('content', '')[:100]}{'...' if len(tweet.get('content', '')) > 100 else ''}")
            print(f"  作者: {tweet.get('username', '')}")
            print(f"  链接: {tweet.get('link', '')}")
            print(f"  话题标签: {tweet.get('hashtags', '')}")
            print(f"  点赞数: {tweet.get('likes', 0)}")
            print(f"  转发数: {tweet.get('retweets', 0)}")
            print(f"  评论数: {tweet.get('comments', 0)}")
            print(f"  发布时间: {tweet.get('publish_time', '')}")
        
    except Exception as e:
        print(f"❌ 获取推文数据时出错: {e}")
        return
    
    # 步骤3: 通过web API同步到飞书
    print(f"\n步骤3: 通过web API同步任务{task_id}到飞书")
    print("-" * 50)
    
    try:
        # 调用飞书同步API
        sync_data = {
            "task_id": task_id
        }
        
        print(f"发送同步请求: {sync_data}")
        response = requests.post(f"{base_url}/api/data/sync_feishu/{task_id}")
        
        print(f"同步响应状态码: {response.status_code}")
        print(f"同步响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 同步请求发送成功")
            print(f"同步结果: {result}")
        else:
            print(f"❌ 同步请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return
        
    except Exception as e:
        print(f"❌ 同步到飞书时出错: {e}")
        return
    
    # 步骤4: Debug同步过程中的数据传递
    print(f"\n步骤4: Debug同步过程中的数据传递")
    print("-" * 50)
    
    print("\n检查要点:")
    print("1. 推文数据是否完整（内容、作者、链接等字段）")
    print("2. 字段映射是否正确")
    print("3. 数据格式化是否正确")
    print("4. 飞书API调用是否成功")
    
    # 检查推文数据完整性
    print("\n检查推文数据完整性:")
    empty_fields = {
        'content': 0,
        'username': 0,
        'link': 0,
        'hashtags': 0,
        'likes': 0,
        'retweets': 0,
        'comments': 0
    }
    
    for tweet in tweets:
        for field in empty_fields:
            value = tweet.get(field)
            if value is None or value == '' or value == 0:
                empty_fields[field] += 1
    
    print("空字段统计:")
    for field, count in empty_fields.items():
        percentage = (count / len(tweets)) * 100 if tweets else 0
        status = "⚠️" if percentage > 50 else "✅"
        print(f"  {status} {field}: {count}/{len(tweets)} ({percentage:.1f}%) 为空")
    
    print("\n=" * 80)
    print("Debug完成")
    print("=" * 80)

if __name__ == "__main__":
    debug_joshwoodward_feishu_sync()