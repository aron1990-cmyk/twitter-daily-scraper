
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迁移到重构的TaskManager
"""

import os
import shutil
from datetime import datetime

# 导入Flask应用和数据库
from web_app_integrated import app, db, ScrapingTask

def migrate_to_refactored_manager():
    """迁移到重构的TaskManager"""
    print("开始迁移到重构的TaskManager...")
    
    # 停止现有的web应用
    print("请先停止现有的web应用")
    
    # 使用已导入的app上下文
    with app.app_context():
        
        # 重置所有运行中的任务状态
        running_tasks = ScrapingTask.query.filter_by(status='running').all()
        for task in running_tasks:
            task.status = 'pending'
            print(f"重置任务 {task.id} 状态为 pending")
        
        db.session.commit()
        print(f"已重置 {len(running_tasks)} 个运行中的任务")
    
    # 替换web_app.py
    if os.path.exists("web_app_integrated.py"):
        # 备份原文件
        if os.path.exists("web_app.py"):
            os.rename("web_app.py", "web_app_original.py")
        
        # 使用新文件
        os.rename("web_app_integrated.py", "web_app.py")
        print("已替换web_app.py为重构版本")
    
    print("迁移完成！现在可以重新启动web应用")

if __name__ == "__main__":
    migrate_to_refactored_manager()
