#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter Daily Scraper - Enhanced Setup Script
增强版Twitter日报采集器快速设置脚本

此脚本帮助用户快速配置和初始化所有增强功能，包括:
- 依赖包安装
- 配置文件生成
- 目录结构创建
- 权限设置
- 初始化检查

使用方法:
    python3 setup_enhanced.py [选项]
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

def print_banner():
    """打印欢迎横幅"""
    print("="*70)
    print("    Twitter Daily Scraper - Enhanced Setup")
    print("    增强版Twitter日报采集器快速设置")
    print("="*70)
    print()

def check_python_version():
    """检查Python版本"""
    print("🔍 检查Python版本...")
    
    if sys.version_info < (3, 8):
        print("❌ 错误: 需要Python 3.8或更高版本")
        print(f"   当前版本: {sys.version}")
        return False
    
    print(f"✅ Python版本检查通过: {sys.version.split()[0]}")
    return True

def install_dependencies():
    """安装依赖包"""
    print("\n📦 安装依赖包...")
    
    try:
        # 检查requirements.txt是否存在
        if not os.path.exists('requirements.txt'):
            print("❌ 错误: requirements.txt文件不存在")
            return False
        
        # 安装依赖
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ 依赖包安装完成")
            return True
        else:
            print(f"❌ 依赖包安装失败: {result.stderr}")
            return False
    
    except Exception as e:
        print(f"❌ 安装依赖包时发生错误: {e}")
        return False

def create_directory_structure():
    """创建目录结构"""
    print("\n📁 创建目录结构...")
    
    directories = [
        'configs',
        'config_backups',
        'logs',
        'data',
        'exports',
        'cache',
        'reports',
        'accounts',
        'credentials'
    ]
    
    try:
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
            print(f"   ✅ 创建目录: {directory}")
        
        print("✅ 目录结构创建完成")
        return True
    
    except Exception as e:
        print(f"❌ 创建目录时发生错误: {e}")
        return False

def generate_config_files():
    """生成配置文件"""
    print("\n⚙️  生成配置文件...")
    
    try:
        # 复制示例配置文件
        if os.path.exists('config_enhanced_example.py'):
            if not os.path.exists('config_enhanced.py'):
                shutil.copy('config_enhanced_example.py', 'config_enhanced.py')
                print("   ✅ 生成配置文件: config_enhanced.py")
            else:
                print("   ⚠️  配置文件已存在: config_enhanced.py")
        
        # 生成账户配置文件
        accounts_file = 'accounts/accounts.json'
        if not os.path.exists(accounts_file):
            default_accounts = {
                "accounts": [
                    {
                        "user_id": "your_ads_user_id_1",
                        "name": "主账户",
                        "priority": 1,
                        "daily_limit": 15,
                        "hourly_limit": 3,
                        "tags": ["primary", "high_quality"],
                        "enabled": True
                    },
                    {
                        "user_id": "your_ads_user_id_2",
                        "name": "备用账户",
                        "priority": 2,
                        "daily_limit": 10,
                        "hourly_limit": 2,
                        "tags": ["backup", "medium_quality"],
                        "enabled": True
                    }
                ],
                "created_at": datetime.now().isoformat(),
                "version": "1.0"
            }
            
            with open(accounts_file, 'w', encoding='utf-8') as f:
                json.dump(default_accounts, f, ensure_ascii=False, indent=2)
            
            print(f"   ✅ 生成账户配置文件: {accounts_file}")
        
        # 生成调度器配置文件
        scheduler_file = 'configs/scheduler.json'
        if not os.path.exists(scheduler_file):
            default_scheduler = {
                "timezone": "Asia/Shanghai",
                "max_workers": 3,
                "tasks": [
                    {
                        "id": "daily_scraping",
                        "name": "每日Twitter采集",
                        "function": "daily_twitter_scraping",
                        "trigger": "cron",
                        "hour": 9,
                        "minute": 0,
                        "enabled": False
                    }
                ]
            }
            
            with open(scheduler_file, 'w', encoding='utf-8') as f:
                json.dump(default_scheduler, f, ensure_ascii=False, indent=2)
            
            print(f"   ✅ 生成调度器配置文件: {scheduler_file}")
        
        # 生成AI分析器配置文件
        ai_config_file = 'configs/ai_analyzer.json'
        if not os.path.exists(ai_config_file):
            default_ai_config = {
                "quality_weights": {
                    "content_length": 0.15,
                    "structure_score": 0.20,
                    "richness_score": 0.25,
                    "language_quality": 0.20,
                    "professionalism": 0.20
                },
                "sentiment_keywords": {
                    "positive": ["好", "棒", "优秀", "成功", "创新", "great", "excellent", "amazing"],
                    "negative": ["差", "糟糕", "失败", "问题", "bad", "terrible", "failure"]
                },
                "trending_keywords": ["AI", "人工智能", "ChatGPT", "机器学习", "区块链"]
            }
            
            with open(ai_config_file, 'w', encoding='utf-8') as f:
                json.dump(default_ai_config, f, ensure_ascii=False, indent=2)
            
            print(f"   ✅ 生成AI分析器配置文件: {ai_config_file}")
        
        print("✅ 配置文件生成完成")
        return True
    
    except Exception as e:
        print(f"❌ 生成配置文件时发生错误: {e}")
        return False

def create_startup_scripts():
    """创建启动脚本"""
    print("\n🚀 创建启动脚本...")
    
    try:
        # 创建快速启动脚本
        quick_start_content = '''#!/bin/bash
# Twitter Daily Scraper - Quick Start Script

echo "启动Twitter日报采集器..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到python3命令"
    exit 1
fi

# 运行采集任务
python3 run_enhanced.py --mode scrape --ai-analysis

echo "采集任务完成"
'''
        
        with open('quick_start.sh', 'w') as f:
            f.write(quick_start_content)
        
        # 设置执行权限
        os.chmod('quick_start.sh', 0o755)
        print("   ✅ 创建快速启动脚本: quick_start.sh")
        
        # 创建调度器启动脚本
        scheduler_start_content = '''#!/bin/bash
# Twitter Daily Scraper - Scheduler Start Script

echo "启动任务调度器..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到python3命令"
    exit 1
fi

# 运行调度器
python3 run_enhanced.py --mode schedule

echo "调度器已停止"
'''
        
        with open('start_scheduler.sh', 'w') as f:
            f.write(scheduler_start_content)
        
        os.chmod('start_scheduler.sh', 0o755)
        print("   ✅ 创建调度器启动脚本: start_scheduler.sh")
        
        # 创建管理控制台启动脚本
        console_start_content = '''#!/bin/bash
# Twitter Daily Scraper - Management Console Start Script

echo "启动管理控制台..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到python3命令"
    exit 1
fi

# 运行管理控制台
python3 run_enhanced.py --mode console

echo "管理控制台已退出"
'''
        
        with open('start_console.sh', 'w') as f:
            f.write(console_start_content)
        
        os.chmod('start_console.sh', 0o755)
        print("   ✅ 创建管理控制台启动脚本: start_console.sh")
        
        print("✅ 启动脚本创建完成")
        return True
    
    except Exception as e:
        print(f"❌ 创建启动脚本时发生错误: {e}")
        return False

def run_initial_tests():
    """运行初始测试"""
    print("\n🧪 运行初始测试...")
    
    try:
        # 测试配置文件加载
        print("   🔍 测试配置文件加载...")
        
        test_script = '''
import sys
sys.path.insert(0, ".")

try:
    from config_manager import ConfigManager
    config_manager = ConfigManager()
    print("✅ 配置管理器加载成功")
except Exception as e:
    print(f"❌ 配置管理器加载失败: {e}")
    sys.exit(1)

try:
    from ai_analyzer import AIAnalyzer
    ai_analyzer = AIAnalyzer()
    print("✅ AI分析器加载成功")
except Exception as e:
    print(f"❌ AI分析器加载失败: {e}")
    sys.exit(1)

try:
    from account_manager import AccountManager
    account_manager = AccountManager()
    print("✅ 账户管理器加载成功")
except Exception as e:
    print(f"❌ 账户管理器加载失败: {e}")
    sys.exit(1)

try:
    from system_monitor import SystemMonitor
    system_monitor = SystemMonitor()
    print("✅ 系统监控器加载成功")
except Exception as e:
    print(f"❌ 系统监控器加载失败: {e}")
    sys.exit(1)

print("\n🎉 所有模块加载测试通过！")
'''
        
        result = subprocess.run(
            [sys.executable, '-c', test_script],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(result.stdout)
            print("✅ 初始测试通过")
            return True
        else:
            print(f"❌ 初始测试失败: {result.stderr}")
            return False
    
    except Exception as e:
        print(f"❌ 运行初始测试时发生错误: {e}")
        return False

def print_next_steps():
    """打印后续步骤"""
    print("\n" + "="*70)
    print("🎉 设置完成！后续步骤:")
    print("="*70)
    print()
    print("1. 配置AdsPower连接:")
    print("   编辑 config_enhanced.py 中的 ADS_POWER_CONFIG")
    print()
    print("2. 配置Twitter目标:")
    print("   编辑 config_enhanced.py 中的 TWITTER_TARGETS")
    print()
    print("3. 配置账户信息:")
    print("   编辑 accounts/accounts.json 中的账户列表")
    print()
    print("4. 配置云同步 (可选):")
    print("   编辑 config_enhanced.py 中的 CLOUD_SYNC_CONFIG")
    print()
    print("5. 运行测试:")
    print("   python3 run_enhanced.py --mode scrape --dry-run")
    print()
    print("6. 开始采集:")
    print("   ./quick_start.sh")
    print("   或 python3 run_enhanced.py --mode scrape --ai-analysis")
    print()
    print("7. 启动管理控制台:")
    print("   ./start_console.sh")
    print("   或 python3 run_enhanced.py --mode console")
    print()
    print("8. 启动任务调度器:")
    print("   ./start_scheduler.sh")
    print("   或 python3 run_enhanced.py --mode schedule")
    print()
    print("📚 更多信息请查看:")
    print("   - README.md")
    print("   - CLOUD_SYNC_SETUP.md")
    print("   - config_enhanced_example.py")
    print()
    print("="*70)

def main():
    """主函数"""
    print_banner()
    
    # 检查步骤
    steps = [
        ("检查Python版本", check_python_version),
        ("安装依赖包", install_dependencies),
        ("创建目录结构", create_directory_structure),
        ("生成配置文件", generate_config_files),
        ("创建启动脚本", create_startup_scripts),
        ("运行初始测试", run_initial_tests)
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        try:
            if not step_func():
                failed_steps.append(step_name)
        except Exception as e:
            print(f"❌ {step_name}执行失败: {e}")
            failed_steps.append(step_name)
    
    # 检查结果
    if failed_steps:
        print(f"\n❌ 设置过程中有 {len(failed_steps)} 个步骤失败:")
        for step in failed_steps:
            print(f"   - {step}")
        print("\n请检查错误信息并重新运行设置脚本")
        return 1
    else:
        print_next_steps()
        return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  设置被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 设置过程中发生未预期的错误: {e}")
        sys.exit(1)