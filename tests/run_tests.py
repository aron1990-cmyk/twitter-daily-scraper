#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter采集系统测试运行脚本
提供便捷的测试执行和报告生成功能
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
import shutil
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestRunner:
    """测试运行器"""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.reports_dir = self.test_dir / "reports"
        self.coverage_dir = self.test_dir / "htmlcov"
        
        # 确保报告目录存在
        self.reports_dir.mkdir(exist_ok=True)
        self.coverage_dir.mkdir(exist_ok=True)
    
    def clean_reports(self):
        """清理旧的测试报告"""
        print("🧹 清理旧的测试报告...")
        
        if self.reports_dir.exists():
            shutil.rmtree(self.reports_dir)
        if self.coverage_dir.exists():
            shutil.rmtree(self.coverage_dir)
        
        self.reports_dir.mkdir(exist_ok=True)
        self.coverage_dir.mkdir(exist_ok=True)
        
        print("✅ 报告目录已清理")
    
    def run_unit_tests(self, verbose=True):
        """运行单元测试"""
        print("\n🔬 运行单元测试...")
        
        # 检查pytest是否可用
        try:
            check_cmd = ["python3", "-c", "import pytest"]
            check_result = subprocess.run(check_cmd, capture_output=True, text=True)
            
            if check_result.returncode != 0:
                raise ImportError("pytest not available")
            
            cmd = [
                "python3", "-m", "pytest",
                "-m", "unit",
                "--tb=short",
                "--durations=10"
            ]
            
            if verbose:
                cmd.append("-v")
            
            return self._run_command(cmd)
            
        except (ImportError, Exception):
            # 回退到直接运行测试文件
            print("pytest不可用，直接运行Python测试文件...")
            return self._run_fallback_tests()
    
    def run_integration_tests(self, verbose=True):
        """运行集成测试"""
        print("\n🔗 运行集成测试...")
        
        # 检查pytest是否可用
        try:
            check_cmd = ["python3", "-c", "import pytest"]
            check_result = subprocess.run(check_cmd, capture_output=True, text=True)
            
            if check_result.returncode != 0:
                raise ImportError("pytest not available")
            
            cmd = [
                "python3", "-m", "pytest",
                "-m", "integration",
                "--tb=short",
                "--durations=10"
            ]
            
            if verbose:
                cmd.append("-v")
            
            return self._run_command(cmd)
            
        except (ImportError, Exception):
            # 回退到直接运行测试文件
            print("pytest不可用，直接运行Python测试文件...")
            return self._run_fallback_tests()
    
    def run_performance_tests(self, verbose=True):
        """运行性能测试"""
        print("\n⚡ 运行性能测试...")
        
        # 检查pytest是否可用
        try:
            check_cmd = ["python3", "-c", "import pytest"]
            check_result = subprocess.run(check_cmd, capture_output=True, text=True)
            
            if check_result.returncode != 0:
                raise ImportError("pytest not available")
            
            cmd = [
                "python3", "-m", "pytest",
                "-m", "performance",
                "--tb=short",
                "--durations=10"
            ]
            
            if verbose:
                cmd.append("-v")
            
            return self._run_command(cmd)
            
        except (ImportError, Exception):
            # 回退到直接运行测试文件
            print("pytest不可用，直接运行Python测试文件...")
            return self._run_fallback_tests()
    
    def run_all_tests(self, with_coverage=True, generate_html=True):
        """运行所有测试"""
        print("\n🚀 运行完整测试套件...")
        
        # 检查pytest是否可用
        try:
            check_cmd = ["python3", "-c", "import pytest"]
            check_result = subprocess.run(check_cmd, capture_output=True, text=True)
            
            if check_result.returncode != 0:
                raise ImportError("pytest not available")
            
            cmd = [
                "python3", "-m", "pytest",
                "--tb=short",
                "--durations=10",
                "-v"
            ]
            
            if with_coverage:
                cmd.extend([
                    "--cov=.",
                    "--cov-report=term-missing",
                    f"--cov-report=html:{self.coverage_dir}",
                    f"--cov-report=xml:{self.reports_dir}/coverage.xml"
                ])
            
            if generate_html:
                cmd.extend([
                    f"--html={self.reports_dir}/report.html",
                    "--self-contained-html",
                    f"--junitxml={self.reports_dir}/junit.xml"
                ])
            
            return self._run_command(cmd)
            
        except (ImportError, Exception):
            # 回退到直接运行所有测试文件
            print("pytest不可用，直接运行所有Python测试文件...")
            success = True
            test_files = list(self.test_dir.glob("test_*.py"))
            
            for test_file in test_files:
                print(f"\n运行测试文件: {test_file.name}")
                cmd = ["python3", str(test_file)]
                if not self._run_command(cmd):
                    success = False
            
            return success
    
    def run_specific_module(self, module_name, verbose=True):
        """运行特定模块的测试"""
        print(f"\n🎯 运行 {module_name} 模块测试...")
        
        # 支持的测试模块映射
        module_mapping = {
            'scraper': 'test_scraper.py',
            'export': 'test_export.py',
            'deduplication': 'test_deduplication.py',
            'value_analysis': 'test_value_analysis.py',
            'integration': 'test_integration.py',
            'fixes': 'test_fixes.py'
        }
        
        if module_name in module_mapping:
            test_file = self.test_dir / module_mapping[module_name]
        else:
            test_file = self.test_dir / f"test_{module_name}.py"
            
        if not test_file.exists():
            print(f"❌ 测试文件不存在: {test_file}")
            return False
        
        # 优先使用pytest，如果不可用则直接运行Python文件
        try:
            cmd = [
                "python3", "-m", "pytest",
                str(test_file),
                "--tb=short",
                "--durations=10"
            ]
            
            if verbose:
                cmd.append("-v")
            
            # 检查pytest是否可用
            check_cmd = ["python3", "-c", "import pytest"]
            check_result = subprocess.run(check_cmd, capture_output=True, text=True)
            
            if check_result.returncode != 0:
                raise ImportError("pytest not available")
                
            return self._run_command(cmd)
            
        except (ImportError, Exception):
            # 回退到直接运行Python文件
            print("pytest不可用，直接运行Python测试文件...")
            cmd = ["python3", str(test_file)]
            return self._run_command(cmd)
    
    def run_quick_tests(self):
        """运行快速测试（排除慢速测试）"""
        print("\n⚡ 运行快速测试...")
        
        # 检查pytest是否可用
        try:
            check_cmd = ["python3", "-c", "import pytest"]
            check_result = subprocess.run(check_cmd, capture_output=True, text=True)
            
            if check_result.returncode != 0:
                raise ImportError("pytest not available")
            
            cmd = [
                "python3", "-m", "pytest",
                "-m", "not slow",
                "--tb=short",
                "-v"
            ]
            
            return self._run_command(cmd)
            
        except (ImportError, Exception):
            # 回退到直接运行测试文件
            print("pytest不可用，直接运行Python测试文件...")
            return self._run_fallback_tests()
    
    def run_failed_tests(self):
        """重新运行失败的测试"""
        print("\n🔄 重新运行失败的测试...")
        
        # 检查pytest是否可用
        try:
            check_cmd = ["python3", "-c", "import pytest"]
            check_result = subprocess.run(check_cmd, capture_output=True, text=True)
            
            if check_result.returncode != 0:
                raise ImportError("pytest not available")
            
            cmd = [
                "python3", "-m", "pytest",
                "--lf",  # last failed
                "--tb=short",
                "-v"
            ]
            
            return self._run_command(cmd)
            
        except (ImportError, Exception):
            # 回退到直接运行测试文件
            print("pytest不可用，直接运行Python测试文件...")
            return self._run_fallback_tests()
    
    def _run_command(self, cmd):
        """执行命令"""
        try:
            print(f"执行命令: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                cwd=self.test_dir,
                capture_output=False,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            print(f"❌ 命令执行失败: {e}")
            return False
    
    def _run_fallback_tests(self):
        """回退方案：直接运行Python测试文件"""
        success = True
        test_files = list(self.test_dir.glob("test_*.py"))
        
        if not test_files:
            print("❌ 未找到测试文件")
            return False
        
        for test_file in test_files:
            print(f"\n运行测试文件: {test_file.name}")
            cmd = ["python3", str(test_file)]
            if not self._run_command(cmd):
                success = False
        
        return success
    
    def generate_test_summary(self):
        """生成测试总结报告"""
        print("\n📊 生成测试总结报告...")
        
        summary_file = self.reports_dir / "test_summary.md"
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"# Twitter采集系统测试报告\n\n")
            f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## 测试模块\n\n")
            f.write("| 模块 | 文件 | 描述 |\n")
            f.write("|------|------|------|\n")
            f.write("| 推文抓取 | test_scraper.py | 测试Twitter抓取功能 |\n")
            f.write("| 数据导出 | test_export.py | 测试数据保存和导出 |\n")
            f.write("| 去重处理 | test_deduplication.py | 测试去重算法 |\n")
            f.write("| 价值分析 | test_value_analysis.py | 测试推文价值评估 |\n")
            f.write("| 集成测试 | test_integration.py | 测试完整工作流程 |\n")
            f.write("| 修复测试 | test_fixes.py | 测试系统修复和改进 |\n\n")
            
            f.write("## 测试报告文件\n\n")
            f.write("- **HTML报告**: `reports/report.html`\n")
            f.write("- **覆盖率报告**: `htmlcov/index.html`\n")
            f.write("- **JUnit XML**: `reports/junit.xml`\n")
            f.write("- **覆盖率XML**: `reports/coverage.xml`\n\n")
            
            f.write("## 测试标记\n\n")
            f.write("- `unit`: 单元测试\n")
            f.write("- `integration`: 集成测试\n")
            f.write("- `performance`: 性能测试\n")
            f.write("- `slow`: 慢速测试\n")
            f.write("- `network`: 需要网络的测试\n")
            f.write("- `browser`: 需要浏览器的测试\n\n")
            
            f.write("## 运行命令示例\n\n")
            f.write("```bash\n")
            f.write("# 运行所有测试\n")
            f.write("python3 tests/run_tests.py --all\n\n")
            f.write("# 运行单元测试\n")
            f.write("python3 tests/run_tests.py --unit\n\n")
            f.write("# 运行特定模块\n")
            f.write("python3 tests/run_tests.py --module scraper\n\n")
            f.write("# 快速测试（排除慢速）\n")
            f.write("python3 tests/run_tests.py --quick\n")
            f.write("```\n")
        
        print(f"✅ 测试总结报告已生成: {summary_file}")
    
    def install_dependencies(self):
        """安装测试依赖"""
        print("📦 安装测试依赖...")
        
        dependencies = [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-html>=3.1.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "pytest-xdist>=3.0.0",  # 并行测试
            "coverage>=7.0.0"
        ]
        
        for dep in dependencies:
            cmd = ["pip3", "install", dep]
            print(f"安装: {dep}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ 安装失败: {dep}")
                print(result.stderr)
                print("⚠️  注意：即使依赖安装失败，测试运行器仍可直接运行Python测试文件")
                # 不返回False，允许继续
        
        print("✅ 测试依赖安装完成（或可使用回退方案）")
        return True

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Twitter采集系统测试运行器")
    
    # 测试类型选项
    parser.add_argument("--all", action="store_true", help="运行所有测试")
    parser.add_argument("--unit", action="store_true", help="运行单元测试")
    parser.add_argument("--integration", action="store_true", help="运行集成测试")
    parser.add_argument("--performance", action="store_true", help="运行性能测试")
    parser.add_argument("--quick", action="store_true", help="运行快速测试")
    parser.add_argument("--failed", action="store_true", help="重新运行失败的测试")
    
    # 特定模块
    parser.add_argument("--module", type=str, help="运行特定模块测试 (scraper, export, deduplication, value_analysis, integration, fixes)")
    
    # 选项
    parser.add_argument("--no-coverage", action="store_true", help="不生成覆盖率报告")
    parser.add_argument("--no-html", action="store_true", help="不生成HTML报告")
    parser.add_argument("--clean", action="store_true", help="清理旧报告")
    parser.add_argument("--install-deps", action="store_true", help="安装测试依赖")
    parser.add_argument("--summary", action="store_true", help="生成测试总结")
    parser.add_argument("--quiet", action="store_true", help="静默模式")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    # 安装依赖
    if args.install_deps:
        if not runner.install_dependencies():
            sys.exit(1)
        return
    
    # 清理报告
    if args.clean:
        runner.clean_reports()
        return
    
    # 生成总结
    if args.summary:
        runner.generate_test_summary()
        return
    
    verbose = not args.quiet
    success = True
    
    # 执行测试
    if args.all:
        success = runner.run_all_tests(
            with_coverage=not args.no_coverage,
            generate_html=not args.no_html
        )
    elif args.unit:
        success = runner.run_unit_tests(verbose)
    elif args.integration:
        success = runner.run_integration_tests(verbose)
    elif args.performance:
        success = runner.run_performance_tests(verbose)
    elif args.quick:
        success = runner.run_quick_tests()
    elif args.failed:
        success = runner.run_failed_tests()
    elif args.module:
        success = runner.run_specific_module(args.module, verbose)
    else:
        # 默认运行快速测试
        print("🚀 默认运行快速测试（使用 --help 查看更多选项）")
        success = runner.run_quick_tests()
    
    # 生成总结报告
    if success and not args.quiet:
        runner.generate_test_summary()
        
        print("\n📊 测试完成！")
        print(f"📁 报告目录: {runner.reports_dir}")
        print(f"📈 覆盖率报告: {runner.coverage_dir}/index.html")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()