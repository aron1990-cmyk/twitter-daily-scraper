#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速启动脚本 - Twitter 日报采集系统
默认启动优化版本的 Web 应用
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """启动优化版本的 Web 应用"""
    # 获取项目根目录
    project_root = Path(__file__).parent
    
    # 检查优化版本文件是否存在
    optimized_app = project_root / 'web_app_optimized.py'
    if not optimized_app.exists():
        print("❌ 错误: web_app_optimized.py 文件不存在")
        return 1
    
    print("🚀 启动优化版本的 Twitter 日报采集系统...")
    print("📍 访问地址: http://localhost:8090")
    print("📍 按 Ctrl+C 停止服务")
    print("\n" + "="*50)
    
    try:
        # 启动优化版本的 Web 应用
        os.chdir(project_root)
        subprocess.run([sys.executable, 'web_app_optimized.py'])
    except KeyboardInterrupt:
        print("\n🛑 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())