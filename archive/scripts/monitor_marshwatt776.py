#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import time
import json
import os
from datetime import datetime

def monitor_task_4():
    """监控任务ID为4的MarshWatt776任务"""
    
    print("🔍 开始监控MarshWatt776任务 (ID: 4)")
    print("=" * 50)
    
    last_status = None
    last_error_count = 0
    
    while True:
        try:
            # 连接数据库
            conn = sqlite3.connect('instance/twitter_scraper.db')
            cursor = conn.cursor()
            
            # 查询任务状态
            cursor.execute("SELECT * FROM scraping_task WHERE id = 4")
            task = cursor.fetchone()
            
            if not task:
                print("❌ 任务ID为4的任务不存在")
                break
                
            task_id, name, target_accounts, keywords, tweet_count, min_likes, min_retweets, max_pages, status, created_at, started_at, completed_at, error_count, error_message = task
            
            # 检查状态是否发生变化
            if status != last_status or error_count != last_error_count:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n[{current_time}] 任务状态更新:")
                print(f"  📋 任务名称: {name}")
                print(f"  🎯 目标账号: {json.loads(target_accounts)}")
                print(f"  📊 推文数量: {tweet_count}")
                print(f"  ❤️ 最小点赞数: {min_likes}")
                print(f"  🔄 最小转发数: {min_retweets}")
                print(f"  📈 状态: {status}")
                
                if started_at:
                    print(f"  🚀 开始时间: {started_at}")
                if completed_at:
                    print(f"  ✅ 完成时间: {completed_at}")
                if error_count > 0:
                    print(f"  ⚠️ 错误次数: {error_count}")
                if error_message:
                    print(f"  ❌ 错误信息: {error_message}")
                    
                # 检查结果文件
                if status == 'completed':
                    result_file = f'task_result_{task_id}.json'
                    if os.path.exists(result_file):
                        with open(result_file, 'r', encoding='utf-8') as f:
                            result = json.load(f)
                        print(f"  📄 结果文件: {result_file}")
                        if 'output_file' in result:
                            print(f"  📊 输出文件: {result['output_file']}")
                        if 'total_tweets' in result:
                            print(f"  📝 抓取推文数: {result['total_tweets']}")
                            
                # 检查错误文件
                if status == 'failed':
                    error_file = f'task_error_{task_id}.json'
                    if os.path.exists(error_file):
                        with open(error_file, 'r', encoding='utf-8') as f:
                            error_info = json.load(f)
                        print(f"  📄 错误文件: {error_file}")
                        if 'error' in error_info:
                            print(f"  ❌ 详细错误: {error_info['error']}")
                
                last_status = status
                last_error_count = error_count
                
                # 如果任务完成或失败，停止监控
                if status in ['completed', 'failed']:
                    print(f"\n🏁 任务已{status}，监控结束")
                    break
                    
            conn.close()
            
            # 等待5秒后再次检查
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("\n⏹️ 用户中断监控")
            break
        except Exception as e:
            print(f"\n❌ 监控过程中发生错误: {e}")
            time.sleep(10)  # 出错时等待更长时间

def check_task_files():
    """检查任务相关文件"""
    task_id = 4
    files_to_check = [
        f'task_result_{task_id}.json',
        f'task_error_{task_id}.json',
        f'temp_config_{task_id}.json',
        'background_task.log'
    ]
    
    print("\n📁 检查任务相关文件:")
    for file_path in files_to_check:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            mod_time = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d %H:%M:%S")
            print(f"  ✅ {file_path} (大小: {file_size} bytes, 修改时间: {mod_time})")
        else:
            print(f"  ❌ {file_path} (不存在)")

if __name__ == '__main__':
    print("🎯 MarshWatt776任务监控器")
    print("任务配置:")
    print("  - 目标账号: MarshWatt776")
    print("  - 推文数量: 100")
    print("  - 最小点赞数: 0 (无过滤)")
    print("  - 最小转发数: 0 (无过滤)")
    print("\n按 Ctrl+C 停止监控\n")
    
    # 先检查文件状态
    check_task_files()
    
    # 开始监控
    monitor_task_4()