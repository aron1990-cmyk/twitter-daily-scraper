#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AdsPower 测试运行脚本
提供简单的命令行接口来运行各种 AdsPower 测试
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_command(cmd, description):
    """运行命令并显示结果"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    print(f"执行命令: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True, cwd=project_root)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ 命令执行失败: {e}")
        return False


def check_dependencies():
    """检查依赖项"""
    print("🔍 检查测试依赖项...")
    
    required_modules = [
        'requests',
        'unittest',
        'json',
        'time'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module} (缺失)")
            missing_modules.append(module)
            
    if missing_modules:
        print(f"\n⚠️ 缺少依赖模块: {', '.join(missing_modules)}")
        print("请运行: pip install -r requirements.txt")
        return False
        
    print("\n✅ 所有依赖项检查通过")
    return True


def check_test_files():
    """检查测试文件是否存在"""
    print("\n📁 检查测试文件...")
    
    test_dir = Path(__file__).parent
    required_files = [
        'test_adspower_config.py',
        'test_adspower_connection.py',
        'test_adspower_web_api.py',
        'test_adspower_all.py'
    ]
    
    missing_files = []
    
    for file_name in required_files:
        file_path = test_dir / file_name
        if file_path.exists():
            print(f"✅ {file_name}")
        else:
            print(f"❌ {file_name} (缺失)")
            missing_files.append(file_name)
            
    if missing_files:
        print(f"\n⚠️ 缺少测试文件: {', '.join(missing_files)}")
        return False
        
    print("\n✅ 所有测试文件检查通过")
    return True


def run_config_tests():
    """运行配置测试"""
    cmd = [sys.executable, 'test/test_adspower_config.py']
    return run_command(cmd, "AdsPower 配置测试")


def run_connection_tests():
    """运行连接测试"""
    cmd = [sys.executable, 'test/test_adspower_connection.py']
    return run_command(cmd, "AdsPower 连接测试")


def run_web_api_tests():
    """运行 Web API 测试"""
    cmd = [sys.executable, 'test/test_adspower_web_api.py']
    return run_command(cmd, "AdsPower Web API 测试")


def run_all_tests(skip_web_api=False, generate_report=False):
    """运行所有测试"""
    cmd = [sys.executable, 'test/test_adspower_all.py']
    
    if skip_web_api:
        cmd.append('--skip-web-api')
        
    if generate_report:
        cmd.extend(['--report', 'test/adspower_test_report.html'])
        
    return run_command(cmd, "AdsPower 综合测试")


def run_quick_check():
    """运行快速检查"""
    print("\n🚀 AdsPower 快速检查")
    print("="*60)
    
    # 检查配置
    try:
        from config.adspower_config import get_config, get_primary_user_id
        config = get_config()
        user_id = get_primary_user_id()
        
        print(f"✅ 配置加载成功")
        print(f"  API URL: {config.get('local_api_url', 'N/A')}")
        print(f"  主用户ID: {user_id or 'N/A'}")
        print(f"  无头模式: {config.get('headless', 'N/A')}")
        
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False
        
    # 检查连接
    try:
        from utils.adspower_manager import AdsPowerManager
        manager = AdsPowerManager()
        is_available, message = manager.is_adspower_available()
        
        if is_available:
            print(f"✅ AdsPower 连接正常: {message}")
        else:
            print(f"❌ AdsPower 连接失败: {message}")
            
    except Exception as e:
        print(f"❌ 连接检查异常: {e}")
        return False
        
    print("\n✅ 快速检查完成")
    return True


def show_help():
    """显示帮助信息"""
    help_text = """
🔧 AdsPower 测试工具使用说明

可用命令:
  config      - 运行配置测试
  connection  - 运行连接测试
  web-api     - 运行 Web API 测试
  all         - 运行所有测试
  quick       - 快速检查
  check       - 检查环境和依赖
  help        - 显示此帮助信息

选项:
  --skip-web-api  - 跳过 Web API 测试（仅适用于 all 命令）
  --report        - 生成 HTML 测试报告（仅适用于 all 命令）
  --quiet         - 静默模式

示例:
  python test/run_tests.py config
  python test/run_tests.py all --report
  python test/run_tests.py all --skip-web-api
  python test/run_tests.py quick

注意事项:
  1. 运行 Web API 测试前，请确保 Web 服务器已启动
  2. 运行连接测试前，请确保 AdsPower 已启动并开启本地 API
  3. 配置测试不需要 AdsPower 运行，可以独立执行
"""
    print(help_text)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='AdsPower 测试运行脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'command',
        choices=['config', 'connection', 'web-api', 'all', 'quick', 'check', 'help'],
        help='要执行的测试命令'
    )
    
    parser.add_argument(
        '--skip-web-api',
        action='store_true',
        help='跳过 Web API 测试（仅适用于 all 命令）'
    )
    
    parser.add_argument(
        '--report',
        action='store_true',
        help='生成 HTML 测试报告（仅适用于 all 命令）'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='静默模式'
    )
    
    args = parser.parse_args()
    
    # 显示标题
    if not args.quiet:
        print("\n" + "="*80)
        print("🧪 AdsPower 测试工具")
        print("="*80)
    
    success = False
    
    try:
        if args.command == 'help':
            show_help()
            success = True
            
        elif args.command == 'check':
            success = check_dependencies() and check_test_files()
            
        elif args.command == 'quick':
            success = run_quick_check()
            
        elif args.command == 'config':
            if check_dependencies() and check_test_files():
                success = run_config_tests()
                
        elif args.command == 'connection':
            if check_dependencies() and check_test_files():
                success = run_connection_tests()
                
        elif args.command == 'web-api':
            if check_dependencies() and check_test_files():
                success = run_web_api_tests()
                
        elif args.command == 'all':
            if check_dependencies() and check_test_files():
                success = run_all_tests(args.skip_web_api, args.report)
                
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被用户中断")
        success = False
    except Exception as e:
        print(f"\n\n❌ 执行异常: {e}")
        success = False
        
    # 显示最终结果
    if not args.quiet:
        print("\n" + "="*80)
        if success:
            print("🎉 测试执行完成")
        else:
            print("⚠️ 测试执行失败或异常")
        print("="*80)
        
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()