#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查最新任务状态和飞书同步情况
"""

import sqlite3
import json
from datetime import datetime
import os

def check_latest_tasks():
    """
    检查数据库中最新任务的状态和飞书同步情况
    """
    db_path = '/Users/aron/twitter-daily-scraper/instance/twitter_scraper.db'
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=" * 60)
        print("📊 检查数据库表结构")
        print("=" * 60)
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"数据库中的表: {[table[0] for table in tables]}")
        
        # 检查 ScrapingTask 表结构
        if ('scraping_task',) in tables:
            cursor.execute("PRAGMA table_info(scraping_task);")
            columns = cursor.fetchall()
            print(f"\nScrapingTask 表字段: {[col[1] for col in columns]}")
        
        # 检查 tweet_data 表结构
        if ('tweet_data',) in tables:
            cursor.execute("PRAGMA table_info(tweet_data);")
            columns = cursor.fetchall()
            print(f"tweet_data 表字段: {[col[1] for col in columns]}")
        
        print("\n" + "=" * 60)
        print("📋 最新5个任务详情")
        print("=" * 60)
        
        # 获取最新的5个任务
        cursor.execute("""
            SELECT id, name, status, created_at, started_at, 
                   result_count, error_message, notes
            FROM scraping_task 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        
        tasks = cursor.fetchall()
        
        if not tasks:
            print("❌ 没有找到任何任务")
            return
        
        for task in tasks:
            task_id, name, status, created_at, started_at, result_count, error_msg, notes = task
            
            print(f"\n📌 任务 #{task_id}: {name}")
            print(f"   状态: {status}")
            print(f"   创建时间: {created_at}")
            print(f"   开始时间: {started_at}")
            print(f"   结果数量: {result_count}")
            if error_msg:
                print(f"   错误信息: {error_msg}")
            if notes:
                print(f"   备注: {notes}")
            
            # 检查该任务的推文同步状态
            cursor.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN synced_to_feishu = 1 THEN 1 ELSE 0 END) as synced,
                       SUM(CASE WHEN synced_to_feishu = 0 OR synced_to_feishu IS NULL THEN 1 ELSE 0 END) as not_synced
                FROM tweet_data 
                WHERE task_id = ?
            """, (task_id,))
            
            sync_stats = cursor.fetchone()
            if sync_stats:
                total, synced, not_synced = sync_stats
                print(f"   推文同步状态:")
                print(f"     总推文数: {total}")
                print(f"     已同步: {synced}")
                print(f"     未同步: {not_synced}")
                if total > 0:
                    sync_rate = (synced / total) * 100
                    print(f"     同步率: {sync_rate:.1f}%")
            
            print("-" * 40)
        
        print("\n" + "=" * 60)
        print("🔧 飞书同步配置检查")
        print("=" * 60)
        
        # 检查飞书配置
        cursor.execute("""
            SELECT key, value FROM system_config 
            WHERE key LIKE '%feishu%' OR key LIKE '%sync%'
        """)
        
        configs = cursor.fetchall()
        if configs:
            print("飞书相关配置:")
            for key, value in configs:
                if 'secret' in key.lower() or 'token' in key.lower():
                    print(f"  {key}: {value[:10]}...")
                else:
                    print(f"  {key}: {value}")
        else:
            print("❌ 没有找到飞书相关配置")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 检查任务状态时出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_latest_tasks()