#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter抓取管理系统 - Web应用启动脚本

这个脚本用于启动Flask Web应用，提供用户友好的界面来管理Twitter抓取任务。

功能特性：
- Web界面管理抓取任务
- 关键词配置和任务调度
- 数据查看和导出
- 飞书文档同步
- 系统配置管理

使用方法：
    python3 run_web.py
    
    可选参数：
    --host: 指定主机地址 (默认: 127.0.0.1)
    --port: 指定端口号 (默认: 5000)
    --debug: 启用调试模式 (默认: False)
    
示例：
    python3 run_web.py --host 0.0.0.0 --port 8080 --debug
"""

import os
import sys
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from web_app import app, init_database
except ImportError as e:
    sys.exit(1)

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='Twitter抓取管理系统 - Web应用',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python3 run_web.py                    # 使用默认设置启动
python3 run_web.py --port 8080        # 在端口8080启动
python3 run_web.py --host 0.0.0.0     # 允许外部访问
python3 run_web.py --debug            # 启用调试模式
        """
    )
    
    parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='服务器主机地址 (默认: 127.0.0.1)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='服务器端口号 (默认: 5000)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='启用调试模式'
    )
    
    parser.add_argument(
        '--no-browser',
        action='store_true',
        help='启动后不自动打开浏览器'
    )
    
    return parser.parse_args()

def check_dependencies():
    """检查必要的依赖是否已安装"""
    required_packages = [
        'flask',
        'flask_sqlalchemy',
        'requests',
        'playwright',
        'openpyxl',
        'pydantic'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        return False
    
    return True

def open_browser(host, port):
    """自动打开浏览器"""
    import webbrowser
    import time
    import threading
    
    def delayed_open():
        time.sleep(1.5)  # 等待服务器启动
        url = f"http://{host}:{port}"
        webbrowser.open(url)
    
    thread = threading.Thread(target=delayed_open)
    thread.daemon = True
    thread.start()

def print_startup_info(host, port, debug):
    """打印启动信息"""
    print(f"🐦 Twitter抓取管理系统启动成功")
    print(f"📍 访问地址: http://{host}:{port}")
    if debug:
        print(f"🔧 调试模式: 启用")
    print("💡 按 Ctrl+C 停止服务器\n")

def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 初始化数据库
    try:
        init_database()
    except Exception as e:
        sys.exit(1)
    
    # 打印启动信息
    print_startup_info(args.host, args.port, args.debug)
    
    # 自动打开浏览器（如果不是调试模式且未禁用）
    if not args.debug and not args.no_browser:
        open_browser(args.host, args.port)
    
    try:
        # 启动Flask应用
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug,
            threaded=True
        )
    except KeyboardInterrupt:
        pass
    except Exception as e:
        sys.exit(1)

if __name__ == '__main__':
    main()