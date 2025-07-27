#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断飞书同步问题
分析Web应用和独立脚本的差异
"""

import os
import sys
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def diagnose_database_connection():
    """诊断数据库连接问题"""
    print("\n🔍 诊断1: 数据库连接")
    print("=" * 40)
    
    # 检查数据库文件
    db_paths = [
        '/Users/aron/twitter-daily-scraper/instance/twitter_scraper.db',
        '/Users/aron/twitter-daily-scraper/twitter_scraper.db',
        './instance/twitter_scraper.db',
        './twitter_scraper.db'
    ]
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"✅ 找到数据库文件: {db_path}")
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # 检查表结构
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                print(f"   - 表数量: {len(tables)}")
                print(f"   - 表名: {[t[0] for t in tables]}")
                
                # 检查TweetData表
                if ('tweet_data',) in tables:
                    cursor.execute("PRAGMA table_info(tweet_data);")
                    columns = cursor.fetchall()
                    print(f"   - TweetData表字段数: {len(columns)}")
                    
                    # 检查synced_to_feishu字段
                    synced_column = [c for c in columns if c[1] == 'synced_to_feishu']
                    if synced_column:
                        print(f"   - synced_to_feishu字段类型: {synced_column[0][2]}")
                    
                    # 检查数据量
                    cursor.execute("SELECT COUNT(*) FROM tweet_data;")
                    total_count = cursor.fetchone()[0]
                    print(f"   - 总推文数: {total_count}")
                    
                    # 检查同步状态分布
                    cursor.execute("SELECT synced_to_feishu, COUNT(*) FROM tweet_data GROUP BY synced_to_feishu;")
                    sync_stats = cursor.fetchall()
                    print(f"   - 同步状态分布: {dict(sync_stats)}")
                    
                    # 检查最近的任务
                    cursor.execute("""
                        SELECT task_id, COUNT(*) as count, 
                               SUM(CASE WHEN synced_to_feishu = 1 THEN 1 ELSE 0 END) as synced_count
                        FROM tweet_data 
                        GROUP BY task_id 
                        ORDER BY task_id DESC 
                        LIMIT 5
                    """)
                    recent_tasks = cursor.fetchall()
                    print(f"   - 最近5个任务的同步情况:")
                    for task_id, count, synced in recent_tasks:
                        print(f"     * 任务{task_id}: {synced}/{count} 已同步")
                
                conn.close()
                
            except Exception as e:
                print(f"   ❌ 数据库连接错误: {e}")
        else:
            print(f"❌ 数据库文件不存在: {db_path}")

def diagnose_config_loading():
    """诊断配置加载问题"""
    print("\n🔍 诊断2: 配置加载")
    print("=" * 40)
    
    try:
        # 模拟Web应用的配置加载
        from web_app import FEISHU_CONFIG, ADS_POWER_CONFIG
        print("✅ 成功导入Web应用配置")
        print(f"   - 飞书配置启用: {FEISHU_CONFIG.get('enabled')}")
        print(f"   - 飞书App ID: {FEISHU_CONFIG.get('app_id', '')[:8]}...")
        print(f"   - 飞书表格Token: {FEISHU_CONFIG.get('spreadsheet_token', '')[:8]}...")
        print(f"   - 飞书表格ID: {FEISHU_CONFIG.get('table_id')}")
        
    except Exception as e:
        print(f"❌ Web应用配置加载失败: {e}")
    
    # 检查配置文件
    config_files = [
        './config/feishu_config.json',
        '/Users/aron/twitter-daily-scraper/config/feishu_config.json'
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"✅ 找到配置文件: {config_file}")
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"   - 配置内容: {list(config.keys())}")
            except Exception as e:
                print(f"   ❌ 配置文件读取错误: {e}")
        else:
            print(f"❌ 配置文件不存在: {config_file}")

def diagnose_time_handling():
    """诊断时间处理问题"""
    print("\n🔍 诊断3: 时间处理")
    print("=" * 40)
    
    # 测试不同时间格式的处理
    test_times = [
        datetime.now(),
        datetime.now().isoformat(),
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        int(datetime.now().timestamp()),
        int(datetime.now().timestamp() * 1000),
        '1970-01-01 00:00:01',
        0,
        1,
        None,
        ''
    ]
    
    print("测试时间格式处理:")
    for i, test_time in enumerate(test_times):
        print(f"\n   测试 {i+1}: {test_time} (类型: {type(test_time)})")
        
        try:
            # 模拟Web应用的时间处理逻辑
            if test_time:
                if isinstance(test_time, str):
                    from dateutil import parser
                    dt = parser.parse(test_time)
                    timestamp = int(dt.timestamp() * 1000)
                    print(f"     - 字符串解析结果: {timestamp} ({datetime.fromtimestamp(timestamp/1000)})")
                elif hasattr(test_time, 'timestamp'):
                    timestamp = int(test_time.timestamp() * 1000)
                    print(f"     - datetime对象结果: {timestamp} ({datetime.fromtimestamp(timestamp/1000)})")
                elif isinstance(test_time, (int, float)):
                    if test_time > 10000000000:  # 毫秒时间戳
                        timestamp = test_time
                    else:  # 秒时间戳
                        timestamp = test_time * 1000
                    print(f"     - 数字处理结果: {timestamp} ({datetime.fromtimestamp(timestamp/1000)})")
                else:
                    timestamp = int(datetime.now().timestamp() * 1000)
                    print(f"     - 默认当前时间: {timestamp} ({datetime.fromtimestamp(timestamp/1000)})")
                    
                # 检查是否是1970年问题
                if timestamp < 946684800000:  # 2000年1月1日的毫秒时间戳
                    print(f"     - ⚠️ 检测到1970年问题!")
                    
            else:
                timestamp = int(datetime.now().timestamp() * 1000)
                print(f"     - 空值处理结果: {timestamp} ({datetime.fromtimestamp(timestamp/1000)})")
                
        except Exception as e:
            print(f"     - ❌ 处理异常: {e}")

def diagnose_web_vs_script_differences():
    """诊断Web应用和独立脚本的差异"""
    print("\n🔍 诊断4: Web应用 vs 独立脚本差异")
    print("=" * 40)
    
    print("主要差异分析:")
    print("1. 数据库连接方式:")
    print("   - Web应用: 使用Flask-SQLAlchemy ORM")
    print("   - 独立脚本: 直接使用sqlite3连接")
    
    print("\n2. 配置加载方式:")
    print("   - Web应用: 从数据库SystemConfig表加载配置")
    print("   - 独立脚本: 直接使用硬编码或文件配置")
    
    print("\n3. 时间处理差异:")
    print("   - Web应用: 在路由中处理时间，转换为毫秒时间戳")
    print("   - 独立脚本: 在cloud_sync.py中处理时间，转换为秒时间戳")
    
    print("\n4. 数据查询差异:")
    print("   - Web应用: 使用SQLAlchemy查询 synced_to_feishu=0")
    print("   - 独立脚本: 可能使用不同的查询条件")
    
    print("\n5. 事务处理差异:")
    print("   - Web应用: 使用Flask-SQLAlchemy的事务管理")
    print("   - 独立脚本: 手动管理数据库事务")

def suggest_solutions():
    """提供解决方案建议"""
    print("\n💡 解决方案建议")
    print("=" * 40)
    
    solutions = [
        {
            "问题": "时间戳格式不一致",
            "解决方案": [
                "统一使用秒级时间戳（而非毫秒）",
                "在Web应用中修改时间处理逻辑，与cloud_sync.py保持一致",
                "添加时间戳验证，确保不会出现1970年问题"
            ]
        },
        {
            "问题": "数据库查询条件不一致",
            "解决方案": [
                "确保Web应用和独立脚本使用相同的查询条件",
                "统一使用整数0/1而非布尔值True/False",
                "添加调试日志确认查询结果"
            ]
        },
        {
            "问题": "配置加载差异",
            "解决方案": [
                "确保Web应用正确加载数据库中的飞书配置",
                "添加配置验证逻辑",
                "统一配置加载方式"
            ]
        },
        {
            "问题": "事务处理差异",
            "解决方案": [
                "确保Web应用正确提交数据库事务",
                "添加异常处理和回滚逻辑",
                "使用相同的数据库连接方式"
            ]
        }
    ]
    
    for i, solution in enumerate(solutions, 1):
        print(f"\n{i}. {solution['问题']}:")
        for j, step in enumerate(solution['解决方案'], 1):
            print(f"   {j}) {step}")

def main():
    """主函数"""
    print("🔧 飞书同步问题诊断工具")
    print("=" * 50)
    print(f"诊断时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 执行各项诊断
    diagnose_database_connection()
    diagnose_config_loading()
    diagnose_time_handling()
    diagnose_web_vs_script_differences()
    suggest_solutions()
    
    print("\n" + "=" * 50)
    print("🏁 诊断完成")
    print("💡 请根据诊断结果和建议进行相应的修复")

if __name__ == "__main__":
    main()