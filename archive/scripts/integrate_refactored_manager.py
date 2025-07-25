#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成重构的TaskManager到web_app.py
这个脚本将:
1. 备份原有的TaskManager
2. 替换为新的无锁TaskManager
3. 更新相关的路由和接口
"""

import os
import shutil
from datetime import datetime

def backup_original_web_app():
    """备份原有的web_app.py"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"web_app_backup_{timestamp}.py"
    
    shutil.copy2("web_app.py", backup_file)
    print(f"原有web_app.py已备份为: {backup_file}")
    return backup_file

def create_integrated_web_app():
    """创建集成了重构TaskManager的新web_app.py"""
    
    # 读取原有的web_app.py内容
    with open("web_app.py", "r", encoding="utf-8") as f:
        original_content = f.read()
    
    # 读取重构的TaskManager
    with open("refactored_task_manager.py", "r", encoding="utf-8") as f:
        refactored_content = f.read()
    
    # 找到原有ParallelTaskManager类的开始和结束位置
    start_marker = "# 并行任务管理器\nclass ParallelTaskManager:"
    end_marker = "# 单个任务执行器（修改为支持指定用户ID）"
    
    start_pos = original_content.find(start_marker)
    end_pos = original_content.find(end_marker)
    
    if start_pos == -1 or end_pos == -1:
        print("错误: 无法找到TaskManager类的边界")
        return False
    
    # 提取重构的TaskManager相关代码
    refactored_imports = """
# 重构TaskManager的导入
import queue
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple
"""
    
    # 从重构文件中提取类定义
    refactored_classes = refactored_content[refactored_content.find("class TaskState"):]
    
    # 构建新的web_app.py内容
    new_content = (
        original_content[:start_pos] +  # 原有内容的前半部分
        refactored_imports + "\n" +     # 新的导入
        refactored_classes + "\n" +    # 重构的类
        original_content[end_pos:]      # 原有内容的后半部分
    )
    
    # 更新TaskManager初始化代码
    old_init = "task_manager = ParallelTaskManager("
    new_init = "task_manager = RefactoredTaskManager("
    new_content = new_content.replace(old_init, new_init)
    
    # 同时替换类型别名
    new_content = new_content.replace("ParallelTaskManager", "RefactoredTaskManager")
    
    # 写入新的web_app.py
    with open("web_app_integrated.py", "w", encoding="utf-8") as f:
        f.write(new_content)
    
    print("集成的web_app.py已创建为: web_app_integrated.py")
    return True

def create_migration_script():
    """创建迁移脚本"""
    migration_script = '''
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迁移到重构的TaskManager
"""

import os
import sys
from flask import Flask
from models import db, ScrapingTask
from refactored_task_manager import RefactoredTaskManager

def migrate_to_refactored_manager():
    """迁移到重构的TaskManager"""
    print("开始迁移到重构的TaskManager...")
    
    # 停止现有的web应用
    print("请先停止现有的web应用")
    
    # 备份数据库中的运行状态
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/twitter_scraper.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    with app.app_context():
        db.init_app(app)
        
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
'''
    
    with open("migrate_task_manager.py", "w", encoding="utf-8") as f:
        f.write(migration_script)
    
    print("迁移脚本已创建: migrate_task_manager.py")

def main():
    """主函数"""
    print("开始集成重构的TaskManager...")
    
    # 1. 备份原文件
    backup_file = backup_original_web_app()
    
    # 2. 创建集成版本
    if create_integrated_web_app():
        print("集成成功！")
        
        # 3. 创建迁移脚本
        create_migration_script()
        
        print("\n下一步操作:")
        print("1. 检查 web_app_integrated.py 确认集成正确")
        print("2. 运行 python3 migrate_task_manager.py 进行迁移")
        print("3. 重新启动web应用测试")
        
    else:
        print("集成失败！")
        return False
    
    return True

if __name__ == "__main__":
    main()