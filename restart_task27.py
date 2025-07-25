#!/usr/bin/env python3
from web_app import app, db, ScrapingTask
import requests
import time

def restart_task27():
    """重新启动任务27"""
    
    with app.app_context():
        print("=== 重新启动任务27 ===")
        
        # 获取任务27
        task = ScrapingTask.query.get(27)
        if not task:
            print("❌ 任务27不存在")
            return
        
        print(f"\n任务信息:")
        print(f"  ID: {task.id}")
        print(f"  名称: {task.name}")
        print(f"  目标账号: {task.target_accounts}")
        print(f"  最大推文数: {task.max_tweets}")
        print(f"  当前状态: {task.status}")
        
        # 重置任务状态
        task.status = 'pending'
        task.started_at = None
        task.completed_at = None
        task.result_count = 0
        task.error_message = None
        db.session.commit()
        
        print(f"\n✅ 任务状态已重置为pending")
        
        # 通过API启动任务
        try:
            print(f"\n🚀 正在启动任务...")
            response = requests.post('http://127.0.0.1:5000/api/tasks/27/start')
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"✅ 任务启动成功: {result.get('message', '')}")
                    
                    # 等待一段时间后检查状态
                    print(f"\n⏳ 等待10秒后检查任务状态...")
                    time.sleep(10)
                    
                    # 检查任务状态
                    updated_task = ScrapingTask.query.get(27)
                    print(f"\n任务状态更新:")
                    print(f"  状态: {updated_task.status}")
                    print(f"  开始时间: {updated_task.started_at}")
                    print(f"  错误信息: {updated_task.error_message or '无'}")
                    
                else:
                    print(f"❌ 任务启动失败: {result.get('error', 'Unknown error')}")
            else:
                print(f"❌ API请求失败: {response.status_code}")
                print(f"响应内容: {response.text}")
                
        except Exception as e:
            print(f"❌ 启动任务时发生错误: {e}")

if __name__ == "__main__":
    restart_task27()