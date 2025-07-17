#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试框架验证脚本
验证测试文件的基本功能，不依赖pytest
"""

import sys
import os
import json
from pathlib import Path
import importlib.util
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestVerifier:
    """测试验证器"""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.passed_tests = 0
        self.failed_tests = 0
        self.errors = []
    
    def verify_test_files(self):
        """验证测试文件"""
        print("🔍 验证测试文件...")
        
        test_files = [
            "test_scraper.py",
            "test_export.py", 
            "test_deduplication.py",
            "test_value_analysis.py",
            "test_integration.py"
        ]
        
        for test_file in test_files:
            self._verify_file(test_file)
        
        self._print_summary()
    
    def _verify_file(self, filename):
        """验证单个测试文件"""
        print(f"\n📄 验证 {filename}...")
        
        file_path = self.test_dir / filename
        
        if not file_path.exists():
            self._record_error(filename, "文件不存在")
            return
        
        try:
            # 检查文件语法
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 编译检查
            compile(content, str(file_path), 'exec')
            
            # 检查基本结构
            self._check_file_structure(filename, content)
            
            print(f"  ✅ {filename} 验证通过")
            self.passed_tests += 1
            
        except Exception as e:
            self._record_error(filename, str(e))
    
    def _check_file_structure(self, filename, content):
        """检查文件结构"""
        required_imports = ['pytest', 'unittest.mock']
        required_patterns = ['def test_', 'class Test']
        
        # 检查导入
        for imp in required_imports:
            if imp not in content:
                raise ValueError(f"缺少必要导入: {imp}")
        
        # 检查测试函数或类
        has_test_pattern = any(pattern in content for pattern in required_patterns)
        if not has_test_pattern:
            raise ValueError("未找到测试函数或测试类")
        
        # 检查文档字符串
        if '"""' not in content:
            raise ValueError("缺少文档字符串")
    
    def _record_error(self, filename, error):
        """记录错误"""
        print(f"  ❌ {filename} 验证失败: {error}")
        self.failed_tests += 1
        self.errors.append(f"{filename}: {error}")
    
    def verify_fixtures(self):
        """验证测试固件"""
        print("\n🔧 验证测试固件...")
        
        fixtures_dir = self.test_dir / "fixtures"
        if not fixtures_dir.exists():
            print("  ❌ fixtures目录不存在")
            return
        
        sample_tweets_file = fixtures_dir / "sample_tweets.json"
        if not sample_tweets_file.exists():
            print("  ❌ sample_tweets.json不存在")
            return
        
        try:
            with open(sample_tweets_file, 'r', encoding='utf-8') as f:
                tweets = json.load(f)
            
            if not isinstance(tweets, list):
                print("  ❌ sample_tweets.json格式错误：应为数组")
                return
            
            if len(tweets) == 0:
                print("  ❌ sample_tweets.json为空")
                return
            
            # 验证推文结构
            required_fields = ['id', 'username', 'content', 'timestamp', 'url']
            for i, tweet in enumerate(tweets[:3]):  # 检查前3条
                for field in required_fields:
                    if field not in tweet:
                        print(f"  ❌ 推文{i}缺少字段: {field}")
                        return
            
            print(f"  ✅ 测试固件验证通过 ({len(tweets)}条推文)")
            
        except Exception as e:
            print(f"  ❌ 固件验证失败: {e}")
    
    def verify_config_files(self):
        """验证配置文件"""
        print("\n⚙️ 验证配置文件...")
        
        config_files = {
            "conftest.py": "pytest配置文件",
            "pytest.ini": "pytest配置",
            "requirements-test.txt": "测试依赖",
            "README.md": "测试文档"
        }
        
        for filename, description in config_files.items():
            file_path = self.test_dir / filename
            if file_path.exists():
                print(f"  ✅ {description} ({filename})")
            else:
                print(f"  ❌ {description}不存在 ({filename})")
    
    def verify_test_structure(self):
        """验证测试结构"""
        print("\n🏗️ 验证测试结构...")
        
        # 检查目录结构
        expected_dirs = ["fixtures", "reports"]
        for dirname in expected_dirs:
            dir_path = self.test_dir / dirname
            if dir_path.exists():
                print(f"  ✅ {dirname}/ 目录存在")
            else:
                print(f"  ⚠️ {dirname}/ 目录不存在（将在运行时创建）")
        
        # 检查测试覆盖范围
        test_modules = {
            "test_scraper.py": "推文抓取测试",
            "test_export.py": "数据导出测试",
            "test_deduplication.py": "去重处理测试",
            "test_value_analysis.py": "价值分析测试",
            "test_integration.py": "集成测试"
        }
        
        print("\n  测试模块覆盖:")
        for filename, description in test_modules.items():
            file_path = self.test_dir / filename
            if file_path.exists():
                print(f"    ✅ {description} ({filename})")
            else:
                print(f"    ❌ {description}缺失 ({filename})")
    
    def run_basic_imports(self):
        """运行基本导入测试"""
        print("\n📦 验证基本导入...")
        
        try:
            # 测试基本Python模块
            import json
            import pathlib
            import unittest.mock
            print("  ✅ 标准库导入正常")
            
            # 测试项目模块（如果存在）
            try:
                import config
                print("  ✅ config模块导入正常")
            except ImportError:
                print("  ⚠️ config模块不存在（可能正常）")
            
            try:
                import models
                print("  ✅ models模块导入正常")
            except ImportError:
                print("  ⚠️ models模块不存在（可能正常）")
            
        except Exception as e:
            print(f"  ❌ 导入测试失败: {e}")
    
    def generate_verification_report(self):
        """生成验证报告"""
        print("\n📊 生成验证报告...")
        
        report_content = f"""# 测试框架验证报告

**验证时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 验证结果

- ✅ 通过测试: {self.passed_tests}
- ❌ 失败测试: {self.failed_tests}
- 📊 总计: {self.passed_tests + self.failed_tests}

## 测试文件状态

| 文件 | 状态 | 描述 |
|------|------|------|
| test_scraper.py | {'✅' if (self.test_dir / 'test_scraper.py').exists() else '❌'} | 推文抓取测试 |
| test_export.py | {'✅' if (self.test_dir / 'test_export.py').exists() else '❌'} | 数据导出测试 |
| test_deduplication.py | {'✅' if (self.test_dir / 'test_deduplication.py').exists() else '❌'} | 去重处理测试 |
| test_value_analysis.py | {'✅' if (self.test_dir / 'test_value_analysis.py').exists() else '❌'} | 价值分析测试 |
| test_integration.py | {'✅' if (self.test_dir / 'test_integration.py').exists() else '❌'} | 集成测试 |

## 配置文件状态

| 文件 | 状态 | 描述 |
|------|------|------|
| conftest.py | {'✅' if (self.test_dir / 'conftest.py').exists() else '❌'} | pytest配置 |
| pytest.ini | {'✅' if (self.test_dir / 'pytest.ini').exists() else '❌'} | pytest设置 |
| requirements-test.txt | {'✅' if (self.test_dir / 'requirements-test.txt').exists() else '❌'} | 测试依赖 |
| README.md | {'✅' if (self.test_dir / 'README.md').exists() else '❌'} | 测试文档 |

## 错误详情

"""
        
        if self.errors:
            for error in self.errors:
                report_content += f"- {error}\n"
        else:
            report_content += "无错误\n"
        
        report_content += f"""

## 建议

1. **运行完整测试**: 安装pytest后运行 `python3 tests/run_tests.py --all`
2. **查看测试文档**: 阅读 `tests/README.md` 了解详细使用方法
3. **安装依赖**: 运行 `pip3 install -r tests/requirements-test.txt`
4. **生成报告**: 使用 `--html` 参数生成详细的HTML报告

## 测试命令示例

```bash
# 验证测试框架
python3 tests/verify_tests.py

# 运行快速测试
python3 tests/run_tests.py --quick

# 运行所有测试
python3 tests/run_tests.py --all

# 运行特定模块
python3 tests/run_tests.py --module scraper
```

---

**验证完成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # 确保reports目录存在
        reports_dir = self.test_dir / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        report_file = reports_dir / "verification_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"  ✅ 验证报告已生成: {report_file}")
    
    def _print_summary(self):
        """打印总结"""
        print("\n" + "="*50)
        print("📊 验证总结")
        print("="*50)
        print(f"✅ 通过: {self.passed_tests}")
        print(f"❌ 失败: {self.failed_tests}")
        print(f"📊 总计: {self.passed_tests + self.failed_tests}")
        
        if self.failed_tests == 0:
            print("\n🎉 所有测试文件验证通过！")
            print("💡 建议: 安装pytest依赖后运行完整测试套件")
        else:
            print("\n⚠️ 部分测试文件存在问题，请检查错误信息")
        
        print("="*50)

def main():
    """主函数"""
    print("🚀 Twitter采集系统测试框架验证")
    print("="*50)
    
    verifier = TestVerifier()
    
    # 执行各项验证
    verifier.verify_test_files()
    verifier.verify_fixtures()
    verifier.verify_config_files()
    verifier.verify_test_structure()
    verifier.run_basic_imports()
    
    # 生成报告
    verifier.generate_verification_report()
    
    print("\n🏁 验证完成！")
    print("📁 查看详细报告: tests/reports/verification_report.md")
    print("📖 阅读测试文档: tests/README.md")
    
    # 返回适当的退出码
    return 0 if verifier.failed_tests == 0 else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)