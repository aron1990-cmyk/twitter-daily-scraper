#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import json
import subprocess
import sys
import os
from datetime import datetime

def start_task_3():
    """手动启动任务ID为3的抓取任务"""
    
    # 连接数据库
    conn = sqlite3.connect('instance/twitter_scraper.db')
    cursor = conn.cursor()
    
    try:
        # 获取任务3的详细信息
        cursor.execute("SELECT * FROM scraping_task WHERE id = 3")
        task = cursor.fetchone()
        
        if not task:
            print("❌ 任务ID为3的任务不存在")
            return False
            
        task_id, name, target_accounts, keywords, tweet_count, min_likes, min_retweets, max_pages, status, created_at, started_at, completed_at, error_count, error_message = task
        
        print(f"📋 任务信息:")
        print(f"   ID: {task_id}")
        print(f"   名称: {name}")
        print(f"   目标账号: {target_accounts}")
        print(f"   推文数量: {tweet_count}")
        print(f"   最小点赞数: {min_likes}")
        print(f"   最小转发数: {min_retweets}")
        print(f"   当前状态: {status}")
        
        if status != 'pending':
            print(f"⚠️ 任务状态不是pending，当前状态: {status}")
            return False
            
        # 更新任务状态为running
        cursor.execute("""
            UPDATE scraping_task 
            SET status = 'running', started_at = ?
            WHERE id = 3
        """, (datetime.now().isoformat(),))
        conn.commit()
        
        print("✅ 任务状态已更新为running")
        
        # 创建临时配置文件
        temp_config = {
            'task_id': task_id,
            'target_accounts': json.loads(target_accounts),
            'keywords': json.loads(keywords),
            'tweet_count': tweet_count,
            'min_likes': min_likes,
            'min_retweets': min_retweets,
            'max_pages': max_pages
        }
        
        config_file = f'temp_config_{task_id}.json'
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(temp_config, f, ensure_ascii=False, indent=2)
            
        print(f"📄 临时配置文件已创建: {config_file}")
        
        # 启动后台任务
        cmd = [sys.executable, 'background_task_runner.py', config_file]
        print(f"🚀 启动命令: {' '.join(cmd)}")
        
        # 使用subprocess启动后台进程
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.getcwd()
        )
        
        print(f"✅ 后台任务已启动，进程ID: {process.pid}")
        
        # 等待一小段时间检查进程是否正常启动
        import time
        time.sleep(2)
        
        if process.poll() is None:
            print("✅ 后台进程正在运行")
            return True
        else:
            stdout, stderr = process.communicate()
            print(f"❌ 后台进程启动失败")
            print(f"stdout: {stdout}")
            print(f"stderr: {stderr}")
            
            # 恢复任务状态
            cursor.execute("""
                UPDATE scraping_task 
                SET status = 'pending', started_at = NULL
                WHERE id = 3
            """)
            conn.commit()
            return False
            
    except Exception as e:
        print(f"❌ 启动任务时发生错误: {e}")
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    print("🔄 开始启动任务ID为3的抓取任务...")
    success = start_task_3()
    if success:
        print("✅