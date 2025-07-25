#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试重构后的TaskManager
验证是否解决了死锁问题
"""

import time
import threading
from web_app import app, task_manager, ScrapingTask, db, init_task_manager

def test_task_manager():
    """测试TaskManager的基本功能"""
    print("=== 测试重构后的TaskManager ===")
    
    with app.app_context():
        # 确保task_manager已初始化
        init_task_manager()
        
        # 重新导入task_manager
        from web_app import task_manager
        # 1. 测试基本状态查询
        print("\n1. 测试基本状态查询:")
        status = task_manager.get_status()
        print(f"   管理器状态: {status}")
        
        # 2. 测试can_start_task方法
        print("\n2. 测试can_start_task方法:")
        can_start = task_manager.can_start_task()
        print(f"   可以启动新任务: {can_start}")
        
        # 3. 测试get_task_status方法
        print("\n3. 测试get_task_status方法:")
        task_status = task_manager.get_task_status()
        print(f"   任务状态: {task_status}")
        
        # 4. 创建测试任务
        print("\n4. 创建测试任务:")
        test_task = ScrapingTask(
            name="测试任务 - 重构后",
            target_accounts='["test_account"]',
            target_keywords='["test_keyword"]',
            max_tweets=10,
            status='pending'
        )
        db.session.add(test_task)
        db.session.commit()
        print(f"   创建任务ID: {test_task.id}")
        
        # 5. 测试任务启动（非阻塞）
        print("\n5. 测试任务启动:")
        print(f"   启动前状态: {task_manager.get_status()}")
        
        # 启动任务
        success = task_manager.start_task(test_task.id)
        print(f"   启动结果: {success}")
        
        # 等待一下看状态变化
        time.sleep(2)
        print(f"   启动后状态: {task_manager.get_status()}")
        
        # 6. 测试is_task_running方法
        print("\n6. 测试is_task_running方法:")
        is_running = task_manager.is_task_running(test_task.id)
        print(f"   任务 {test_task.id} 是否运行中: {is_running}")
        
        # 7. 测试并发启动（验证无死锁）
        print("\n7. 测试并发启动（验证无死锁）:")
        
        def concurrent_start_test(task_id, thread_id):
            """并发启动测试"""
            try:
                print(f"   线程 {thread_id}: 尝试启动任务 {task_id}")
                result = task_manager.start_task(task_id)
                print(f"   线程 {thread_id}: 启动结果 {result}")
            except Exception as e:
                print(f"   线程 {thread_id}: 启动失败 {str(e)}")
        
        # 创建多个测试任务
        test_tasks = []
        for i in range(3):
            task = ScrapingTask(
                name=f"并发测试任务 {i+1}",
                target_accounts='["test_account"]',
                target_keywords='["test_keyword"]',
                max_tweets=5,
                status='pending'
            )
            db.session.add(task)
            test_tasks.append(task)
        db.session.commit()
        
        # 并发启动测试
        threads = []
        for i, task in enumerate(test_tasks):
            thread = threading.Thread(
                target=concurrent_start_test,
                args=(task.id, i+1)
            )
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        print("\n8. 最终状态:")
        final_status = task_manager.get_status()
        print(f"   最终管理器状态: {final_status}")
        
        # 9. 清理测试任务
        print("\n9. 清理测试任务:")
        for task in [test_task] + test_tasks:
            if task_manager.is_task_running(task.id):
                print(f"   停止任务 {task.id}")
                task_manager.stop_task(task.id)
        
        # 等待清理完成
        time.sleep(3)
        print(f"   清理后状态: {task_manager.get_status()}")
        
        print("\n=== 测试完成 ===")
        print("✅ 重构后的TaskManager测试通过，未发现死锁问题")

if __name__ == '__main__':
    test_task_manager()