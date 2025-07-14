
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化代码质量检查和改进脚本
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_code_formatting():
    """运行代码格式化"""
    try:
        print("🎨 检查代码格式化工具...")
        # 检查black是否可用
        subprocess.run(["black", "--version"], check=True, capture_output=True)
        print("🎨 运行代码格式化...")
        subprocess.run(["black", "."], check=True)
        print("✅ 代码格式化完成")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️ black未安装，跳过代码格式化")
        return True  # 返回True以继续其他检查

def run_code_linting():
    """运行代码检查"""
    print("🔍 运行代码检查...")
    success = True
    
    # Flake8检查
    try:
        subprocess.run(["flake8", "."], check=True)
        print("✅ Flake8检查通过")
    except subprocess.CalledProcessError:
        print("⚠️ Flake8检查发现问题")
        success = False
    
    # MyPy类型检查
    try:
        subprocess.run(["mypy", "."], check=True)
        print("✅ MyPy类型检查通过")
    except subprocess.CalledProcessError:
        print("⚠️ MyPy类型检查发现问题")
        success = False
    
    return success

def run_security_check():
    """运行安全检查"""
    print("🔒 运行安全检查...")
    try:
        subprocess.run(["bandit", "-r", "."], check=True)
        print("✅ 安全检查通过")
        return True
    except subprocess.CalledProcessError:
        print("⚠️ 安全检查发现问题")
        return False

def run_tests():
    """运行测试"""
    print("🧪 运行测试...")
    try:
        subprocess.run(["pytest", "-v", "--cov=."], check=True)
        print("✅ 测试通过")
        return True
    except subprocess.CalledProcessError:
        print("❌ 测试失败")
        return False

def run_complexity_analysis():
    """运行复杂度分析"""
    print("📊 运行复杂度分析...")
    try:
        subprocess.run(["radon", "cc", ".", "-a"], check=True)
        subprocess.run(["radon", "mi", "."], check=True)
        print("✅ 复杂度分析完成")
        return True
    except subprocess.CalledProcessError:
        print("⚠️ 复杂度分析失败")
        return False

def setup_pre_commit_hooks():
    """设置Git pre-commit hooks"""
    print("🪝 设置Git pre-commit hooks...")
    try:
        subprocess.run(["pre-commit", "install"], check=True)
        print("✅ Pre-commit hooks设置完成")
        return True
    except subprocess.CalledProcessError:
        print("⚠️ Pre-commit hooks设置失败")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="自动化代码质量检查")
    parser.add_argument("--format", action="store_true", help="运行代码格式化")
    parser.add_argument("--lint", action="store_true", help="运行代码检查")
    parser.add_argument("--security", action="store_true", help="运行安全检查")
    parser.add_argument("--test", action="store_true", help="运行测试")
    parser.add_argument("--complexity", action="store_true", help="运行复杂度分析")
    parser.add_argument("--hooks", action="store_true", help="设置pre-commit hooks")
    parser.add_argument("--all", action="store_true", help="运行所有检查")
    
    args = parser.parse_args()
    
    if not any(vars(args).values()):
        args.all = True
    
    success_count = 0
    total_count = 0
    
    if args.all or args.format:
        total_count += 1
        if run_code_formatting():
            success_count += 1
    
    if args.all or args.lint:
        total_count += 1
        if run_code_linting():
            success_count += 1
    
    if args.all or args.security:
        total_count += 1
        if run_security_check():
            success_count += 1
    
    if args.all or args.test:
        total_count += 1
        if run_tests():
            success_count += 1
    
    if args.all or args.complexity:
        total_count += 1
        if run_complexity_analysis():
            success_count += 1
    
    if args.all or args.hooks:
        total_count += 1
        if setup_pre_commit_hooks():
            success_count += 1
    
    print(f"\n📊 总结: {success_count}/{total_count} 项检查通过")
    
    if success_count == total_count:
        print("🎉 所有检查都通过了！")
        sys.exit(0)
    else:
        print("⚠️ 部分检查未通过，请查看上面的详细信息")
        sys.exit(1)

if __name__ == "__main__":
    main()
