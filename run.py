#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速启动脚本 - Twitter 日报采集系统

这个脚本提供了一个简化的命令行界面，让用户可以快速运行采集任务。
"""

import sys
import os
import argparse
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from main import main
from config import (
    ADS_POWER_CONFIG, TWITTER_TARGETS, FILTER_CONFIG, 
    OUTPUT_CONFIG, BROWSER_CONFIG, LOG_CONFIG
)

def print_banner():
    """打印启动横幅"""
    pass

def print_config_summary():
    """打印当前配置摘要"""
    pass

def check_adspower_status():
    """检查 AdsPower 状态"""
    try:
        import requests
        # 从完整URL中提取端口号
        api_url = ADS_POWER_CONFIG['local_api_url']
        url = f"{api_url}/api/v1/browser/list"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 0:
                browsers = data.get('data', {}).get('list', [])
                return True
        return False
    except Exception as e:
        return False

def run_with_options(args):
    """根据命令行参数运行采集任务"""
    print_banner()
    
    if args.check_config:
        print_config_summary()
        return
    
    if args.check_adspower:
        check_adspower_status()
        return
    
    # 显示配置摘要
    print_config_summary()
    
    # 检查 AdsPower 状态
    if not check_adspower_status():
        if not args.force:
            return
    
    # 运行主程序
    try:
        main()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        pass
        if args.debug:
            import traceback
            traceback.print_exc()

def main_cli():
    """命令行界面主函数"""
    parser = argparse.ArgumentParser(
        description="Twitter 日报采集系统 - 快速启动脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python3 run.py                    # 运行完整采集任务
  python3 run.py --check-config     # 查看当前配置
  python3 run.py --check-adspower   # 检查 AdsPower 连接
  python3 run.py --force            # 强制运行（忽略连接检查）
  python3 run.py --debug            # 调试模式（显示详细错误信息）

配置文件: config.py
输出目录: data/
日志目录: logs/
        """
    )
    
    parser.add_argument(
        '--check-config', 
        action='store_true',
        help='查看当前配置摘要'
    )
    
    parser.add_argument(
        '--check-adspower', 
        action='store_true',
        help='检查 AdsPower 连接状态'
    )
    
    parser.add_argument(
        '--force', 
        action='store_true',
        help='强制运行，忽略 AdsPower 连接检查'
    )
    
    parser.add_argument(
        '--debug', 
        action='store_true',
        help='启用调试模式，显示详细错误信息'
    )
    
    args = parser.parse_args()
    run_with_options(args)

if __name__ == "__main__":
    main_cli()