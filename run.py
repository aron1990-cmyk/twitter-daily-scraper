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
    print("\n" + "="*60)
    print("🐦 Twitter 日报采集系统 - 快速启动")
    print("="*60)
    print("📊 自动化采集 Twitter 数据，生成日报矩阵")
    print("🚀 基于 AdsPower 虚拟浏览器技术")
    print("="*60 + "\n")

def print_config_summary():
    """打印当前配置摘要"""
    print("📋 当前配置摘要:")
    print(f"   🌐 AdsPower API: {ADS_POWER_CONFIG['local_api_url']}")
    print(f"   🎯 目标账号: {', '.join(TWITTER_TARGETS['accounts'])}")
    print(f"   🔍 关键词: {', '.join(TWITTER_TARGETS['keywords'])}")
    print(f"   📊 最大采集数: {FILTER_CONFIG['max_tweets_per_target']}")
    print(f"   💾 输出目录: {OUTPUT_CONFIG['data_dir']}")
    print()

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
                print(f"✅ AdsPower 连接正常，发现 {len(browsers)} 个浏览器配置")
                return True
        print("⚠️  AdsPower API 响应异常")
        return False
    except Exception as e:
        print(f"❌ 无法连接到 AdsPower: {e}")
        print("   请确保 AdsPower 客户端已启动")
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
            print("\n❌ AdsPower 连接失败，使用 --force 参数强制运行")
            return
        else:
            print("\n⚠️  强制运行模式，忽略 AdsPower 连接检查")
    
    # 运行主程序
    print("\n🚀 开始执行采集任务...\n")
    try:
        main()
        print("\n✅ 采集任务完成！")
        print(f"📁 请查看输出目录: {OUTPUT_CONFIG['data_dir']}")
    except KeyboardInterrupt:
        print("\n⏹️  用户中断操作")
    except Exception as e:
        print(f"\n❌ 采集过程中出现错误: {e}")
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