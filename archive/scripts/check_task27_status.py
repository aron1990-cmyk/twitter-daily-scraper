#!/usr/bin/env python3
from web_app import app, db, ScrapingTask
import json
import os

def check_task27_status():
    """检查任务27的当前状态"""
    
    with app.app_context():
        print("=== 任务27状态检查 ===")
        
        # 获取任务27
        task = ScrapingTask.query.get(27)
        if not task:
            print("❌ 任务27不存在")
            return
        
        print(f"\n任务基本信息:")
        print(f"  ID: {task.id}")
        print(f"  名称: {task.name}")
        print(f"  目标账号: {task.target_accounts}")
        print(f"  最大推文数: {task.max_tweets}")
        print(f"  状态: {task.status}")
        print(f"  创建时间: {task.created_at}")
        print(f"  开始时间: {task.started_at}")
        print(f"  完成时间: {task.completed_at}")
        print(f"  结果数量: {task.result_count}")
        print(f"  错误信息: {task.error_message or '无'}")
        
        # 检查任务错误文件
        error_file = f"task_error_{task.id}.json"
        if os.path.exists(error_file):
            print(f"\n错误文件存在: {error_file}")
            with open(error_file, 'r', encoding='utf-8') as f:
                error_data = json.load(f)
                print(f"  错误信息: {error_data.get('error', 'N/A')}")
                print(f"  时间戳: {error_data.get('timestamp', 'N/A')}")
        else:
            print(f"\n无错误文件")
        
        # 检查任务结果文件
        result_file = f"task_result_{task.id}.json"
        if os.path.exists(result_file):
            print(f"\n结果文件存在: {result_file}")
            with open(result_file, 'r', encoding='utf-8') as f:
                result_data = json.load(f)
                print(f"  任务ID: {result_data.get('task_id', 'N/A')}")
                print(f"  状态: {result_data.get('status', 'N/A')}")
                print(f"  推文数量: {result_data.get('tweets_count', 'N/A')}")
        else:
            print(f"\n无结果文件")
        
        # 检查日志文件
        log_files = [f for f in os.listdir('.') if f.startswith('task_') and f.endswith('.log')]
        if log_files:
            print(f"\n日志文件: {log_files}")
        else:
            print(f"\n无日志文件")

if __name__ == "__main__":
    check_task27_status()