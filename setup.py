#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安装和设置脚本
Twitter 日报采集系统快速设置工具
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_python_version():
    """检查 Python 版本"""
    if sys.version_info < (3, 7):
        print("❌ 错误: 需要 Python 3.7 或更高版本")
        print(f"当前版本: {sys.version}")
        return False
    print(f"✅ Python 版本检查通过: {sys.version.split()[0]}")
    return True

def install_dependencies():
    """安装依赖包"""
    print("\n📦 安装依赖包...")
    try:
        # 安装依赖包（使用可信主机解决SSL问题）
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', 
            '--trusted-host', 'pypi.org',
            '--trusted-host', 'pypi.python.org', 
            '--trusted-host', 'files.pythonhosted.org',
            '-r', 'requirements.txt'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ 依赖包安装失败: {result.stderr}")
            print("\n🔧 尝试手动安装:")
            print(f"   pip3 install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt")
            return False
        
        print("✅ 依赖包安装完成")
        return True
    except Exception as e:
        print(f"❌ 依赖包安装失败: {e}")
        return False

def install_playwright():
    """安装 Playwright 浏览器"""
    print("\n🌐 安装 Playwright 浏览器...")
    try:
        # 安装 Playwright 浏览器
        result = subprocess.run([
            sys.executable, '-m', 'playwright', 'install'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Playwright 安装失败: {result.stderr}")
            print("\n🔧 尝试手动安装:")
            print(f"   python3 -m playwright install")
            return False
        
        print("✅ Playwright 浏览器安装完成")
        return True
    except Exception as e:
        print(f"❌ Playwright 浏览器安装失败: {e}")
        return False

def create_directories():
    """创建必要的目录"""
    print("\n📁 创建目录结构...")
    directories = ['data', 'logs']
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ 创建目录: {directory}/")
    
    return True

def setup_config():
    """设置配置文件"""
    print("\n⚙️  配置设置...")
    
    config_file = 'config.py'
    if not os.path.exists(config_file):
        print(f"❌ 配置文件 {config_file} 不存在")
        return False
    
    print("\n请按照以下步骤配置系统:")
    print("\n1. AdsPower 配置:")
    print("   - 启动 AdsPower 客户端")
    print("   - 创建或选择一个浏览器配置文件")
    print("   - 记录配置文件的用户ID")
    print("   - 在 config.py 中设置 ADS_POWER_CONFIG['user_id']")
    
    print("\n2. 采集目标配置:")
    print("   - 在 config.py 中设置 TWITTER_TARGETS['accounts']（目标用户）")
    print("   - 在 config.py 中设置 TWITTER_TARGETS['keywords']（搜索关键词）")
    
    print("\n3. 筛选条件配置:")
    print("   - 根据需要调整 FILTER_CONFIG 中的阈值")
    
    return True

def test_installation():
    """测试安装"""
    print("\n🧪 测试安装...")
    
    try:
        # 测试导入主要模块
        import requests
        import playwright
        import openpyxl
        print("✅ 核心依赖包导入成功")
        
        # 测试项目模块
        from config import ADS_POWER_CONFIG, TWITTER_TARGETS, FILTER_CONFIG
        print("✅ 项目配置文件加载成功")
        
        return True
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def show_next_steps():
    """显示后续步骤"""
    print("\n" + "="*50)
    print("🎉 安装完成！")
    print("="*50)
    
    print("\n📋 后续步骤:")
    print("\n1. 配置 AdsPower:")
    print("   编辑 config.py 文件，设置你的 AdsPower 用户ID")
    
    print("\n2. 设置采集目标:")
    print("   在 config.py 中配置要采集的 Twitter 账号和关键词")
    
    print("\n3. 运行系统:")
    print("   python main.py")
    
    print("\n4. 查看结果:")
    print("   生成的 Excel 文件将保存在 data/ 目录中")
    
    print("\n📚 更多信息请查看 README.md 文件")
    
    print("\n⚠️  重要提醒:")
    print("   - 请确保 AdsPower 客户端正在运行")
    print("   - 请遵守 Twitter 使用条款")
    print("   - 建议先进行小规模测试")

def main():
    """主函数"""
    print("🚀 Twitter 日报采集系统 - 安装向导")
    print("="*50)
    
    # 检查 Python 版本
    if not check_python_version():
        return False
    
    # 创建目录
    if not create_directories():
        return False
    
    # 安装依赖
    if not install_dependencies():
        return False
    
    # 安装 Playwright
    if not install_playwright():
        return False
    
    # 测试安装
    if not test_installation():
        return False
    
    # 设置配置
    setup_config()
    
    # 显示后续步骤
    show_next_steps()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ 安装成功完成！")
        else:
            print("\n❌ 安装过程中出现错误")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  安装被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 安装失败: {e}")
        sys.exit(1)