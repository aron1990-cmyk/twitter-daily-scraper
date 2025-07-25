#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试TaskManager功能的简单脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_app import app, ScrapingTask, db, init_task_manager
import time

def test_task_manager():
    """测试TaskManager的基本功能"""
    with app.app_context():
        print("=== TaskManager 测试开始 ===")
        
        # 导入并检查TaskManager
        from web_app import task_manager
        
        # 确保TaskManager已初始化
        if task_manager is None:
            print("TaskManager未初始化，正在初始化...")
            init_task_manager()
            from web_app import task_manager
        
        if task_manager is None:
            print("❌ TaskManager初始化失败")
            return
        
        # 检查TaskManager状态
        print(f"TaskManager状态:")
        print(f"  - 最大并发任务数: {task_manager.max_concurrent_tasks}")
        print(f"  - 当前运行任务数: {task_manager.get_running_task_count()}")
        print(f"  - 可用用户ID数量: {len(task_manager.user_id_pool)}")
        print(f"  - 用户ID池: {task_manager.user_id_pool}")
        print(f"  - 请求间隔: {task_manager.request_interval}s")
        
        # 检查任务4
        task_id = 4
        task = ScrapingTask.query.get(task_id)
        if not task:
            print(f"❌ 任务 {task_id} 不存在")
            return
        
        print(f"\n任务 {task_id} 信息:")
        print(f"  - 名称: {task.name}")
        print(f"  - 状态: {task.status}")
        print(f"  - 是否正在运行: {task_manager.is_task_running(task_id)}")
        
        # 检查是否可以启动任务
        can_start = task_manager.can_start_task()
        print(f"\n是否可以启动新任务: {can_start}")
        
        if not can_start:
            status = task_manager.get_task_status()
            print(f"无法启动的原因:")
            print(f"  - 运行任务数: {status['running_count']}/{status['max_concurrent']}")
            print(f"  - 可用浏览器: {status['available_browsers']}")
            return
        
        # 尝试启动任务
        print(f"\n🚀 尝试启动任务 {task_id}...")
        try:
            success, message = task_manager.start_task(task_id)
            if success:
                print(f"✅ 任务启动成功: {message}")
                
                # 等待一下，检查任务状态
                time.sleep(2)
                
                print(f"\n任务启动后状态:")
                print(f"  - 是否正在运行: {task_manager.is_task_running(task_id)}")
                print(f"  - 运行任务数: {task_manager.get_running_task_count()}")
                print(f"  - 后台进程: {list(task_manager.background_processes.keys())}")
                
            else:
                print(f"❌ 任务启动失败: {message}")
                
        except Exception as e:
            print(f"❌ 任务启动异常: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("\n=== TaskManager 测试结束 ===")

if __name__ == "__main__":
    test_task_manager()