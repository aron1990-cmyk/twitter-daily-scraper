#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目清理脚本
用于定期清理临时文件、日志文件和过期的导出文件
"""

import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path

def cleanup_logs(days_to_keep=30):
    """清理超过指定天数的日志文件"""
    logs_dir = Path('logs')
    if not logs_dir.exists():
        return
    
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    cleaned_files = []
    
    for log_file in logs_dir.glob('*.log'):
        if log_file.stat().st_mtime < cutoff_date.timestamp():
            log_file.unlink()
            cleaned_files.append(str(log_file))
    
    print(f"清理了 {len(cleaned_files)} 个过期日志文件")
    return cleaned_files

def cleanup_exports(days_to_keep=90):
    """清理超过指定天数的导出文件"""
    exports_dir = Path('exports')
    if not exports_dir.exists():
        return
    
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    cleaned_files = []
    
    for export_file in exports_dir.glob('*.xlsx'):
        if export_file.stat().st_mtime < cutoff_date.timestamp():
            export_file.unlink()
            cleaned_files.append(str(export_file))
    
    print(f"清理了 {len(cleaned_files)} 个过期导出文件")
    return cleaned_files

def cleanup_task_results(days_to_keep=60):
    """清理超过指定天数的任务结果文件"""
    task_results_dir = Path('task_results')
    if not task_results_dir.exists():
        return
    
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    cleaned_files = []
    
    for result_file in task_results_dir.glob('*.json'):
        if result_file.stat().st_mtime < cutoff_date.timestamp():
            result_file.unlink()
            cleaned_files.append(str(result_file))
    
    print(f"清理了 {len(cleaned_files)} 个过期任务结果文件")
    return cleaned_files

def cleanup_temp_files():
    """清理临时文件"""
    temp_patterns = ['*.tmp', '*.temp', '*.bak', '*.backup']
    cleaned_files = []
    
    for pattern in temp_patterns:
        for temp_file in Path('.').glob(pattern):
            temp_file.unlink()
            cleaned_files.append(str(temp_file))
    
    print(f"清理了 {len(cleaned_files)} 个临时文件")
    return cleaned_files

def cleanup_pycache():
    """清理Python缓存文件"""
    cleaned_dirs = []
    
    for pycache_dir in Path('.').rglob('__pycache__'):
        shutil.rmtree(pycache_dir)
        cleaned_dirs.append(str(pycache_dir))
    
    print(f"清理了 {len(cleaned_dirs)} 个__pycache__目录")
    return cleaned_dirs

def main():
    """主清理函数"""
    print("开始项目清理...")
    print(f"清理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    # 清理各类文件
    cleanup_logs()
    cleanup_exports()
    cleanup_task_results()
    cleanup_temp_files()
    cleanup_pycache()
    
    print("-" * 50)
    print("项目清理完成!")

if __name__ == '__main__':
    main()