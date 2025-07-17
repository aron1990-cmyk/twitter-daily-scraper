#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter抓取系统综合测试脚本
整合所有测试模块，提供完整的系统测试报告
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path
import requests

class ComprehensiveTester:
    def __init__(self, base_url="http://localhost:8084"):
        self.base_url = base_url
        self.project_root = Path(__file__).parent
        self.test_results = {}
        self.overall_results = []
        
    def log_result(self, test_name, success, details="", score=0):
        """记录测试结果"""
        result = {
            'test_name': test_name,
            'success': success,
            'details': details,
            'score': score,
            'timestamp': datetime.now().isoformat()
        }
        self.overall_results.append(result)
        
        status = "✅" if success else "❌"
        print(f"   {status} {test_name}: {details}")
    
    def run_test_script(self, script_name, test_category):
        """运行测试脚本"""
        script_path = self.project_root / script_name
        
        if not script_path.exists():
            self.log_result(
                f"{test_category}测试",
                False,
                f"测试脚本不存在: {script_name}"
            )
            return False, {}
        
        try:
            print(f"\n🔄 运行{test_category}测试...")
            
            # 运行测试脚本
            result = subprocess.run(
                [sys.executable, str(script_path), '--url', self.base_url],
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            # 检查是否有对应的报告文件
            report_files = {
                'AdsPower检测': 'adspower_detection_test_report.json',
                '核心功能': 'core_functionality_test_report.json',
                '性能稳定性': 'performance_stability_test_report.json',
                '安全性': 'security_test_report.json',
                '数据完整性': 'data_integrity_test_report.json',
                'UI/UX': 'ui_ux_test_report.json'
            }
            
            report_file = self.project_root / report_files.get(test_category, '')
            test_data = {}
            
            if report_file.exists():
                try:
                    with open(report_file, 'r', encoding='utf-8') as f:
                        test_data = json.load(f)
                except Exception as e:
                    print(f"   ⚠️ 无法读取报告文件: {str(e)}")
            
            # 分析测试结果
            if result.returncode == 0:
                # 从报告文件中提取成功率
                success_rate = 0
                if test_data and 'test_summary' in test_data:
                    summary = test_data['test_summary']
                    if 'suite_success_rate' in summary:
                        success_rate = summary['suite_success_rate']
                    elif 'test_success_rate' in summary:
                        success_rate = summary['test_success_rate']
                
                self.log_result(
                    f"{test_category}测试",
                    success_rate >= 0.7,
                    f"成功率: {success_rate:.1%}",
                    int(success_rate * 100)
                )
                
                return success_rate >= 0.7, test_data
            else:
                self.log_result(
                    f"{test_category}测试",
                    False,
                    f"测试脚本执行失败: {result.stderr[:100]}..."
                )
                return False, {}
                
        except subprocess.TimeoutExpired:
            self.log_result(
                f"{test_category}测试",
                False,
                "测试超时（5分钟）"
            )
            return False, {}
        except Exception as e:
            self.log_result(
                f"{test_category}测试",
                False,
                f"测试异常: {str(e)}"
            )
            return False, {}
    
    def check_system_prerequisites(self):
        """检查系统先决条件"""
        print("🔍 检查系统先决条件...")
        
        prerequisites_passed = 0
        total_prerequisites = 0
        
        # 检查Web服务器
        total_prerequisites += 1
        try:
            response = requests.get(self.base_url, timeout=10)
            if response.status_code == 200:
                prerequisites_passed += 1
                self.log_result(
                    "Web服务器状态",
                    True,
                    f"服务器运行正常 (HTTP {response.status_code})"
                )
            else:
                self.log_result(
                    "Web服务器状态",
                    False,
                    f"服务器响应异常 (HTTP {response.status_code})"
                )
        except Exception as e:
            self.log_result(
                "Web服务器状态",
                False,
                f"无法连接服务器: {str(e)}"
            )
        
        # 检查Python依赖
        total_prerequisites += 1
        required_packages = {
            'requests': 'requests',
            'pandas': 'pandas', 
            'beautifulsoup4': 'bs4'
        }
        missing_packages = []
        
        for package_name, import_name in required_packages.items():
            try:
                __import__(import_name)
            except ImportError:
                missing_packages.append(package_name)
        
        if not missing_packages:
            prerequisites_passed += 1
            self.log_result(
                "Python依赖",
                True,
                "所有必需的包都已安装"
            )
        else:
            self.log_result(
                "Python依赖",
                False,
                f"缺少包: {', '.join(missing_packages)}"
            )
        
        # 检查项目文件结构
        total_prerequisites += 1
        required_files = ['web_app.py', 'config.py', 'main.py']
        missing_files = []
        
        for file_name in required_files:
            if not (self.project_root / file_name).exists():
                missing_files.append(file_name)
        
        if not missing_files:
            prerequisites_passed += 1
            self.log_result(
                "项目文件结构",
                True,
                "核心文件都存在"
            )
        else:
            self.log_result(
                "项目文件结构",
                False,
                f"缺少文件: {', '.join(missing_files)}"
            )
        
        # 检查数据目录
        total_prerequisites += 1
        data_dir = self.project_root / "data"
        if data_dir.exists():
            prerequisites_passed += 1
            self.log_result(
                "数据目录",
                True,
                "数据目录存在"
            )
        else:
            self.log_result(
                "数据目录",
                False,
                "数据目录不存在"
            )
        
        success_rate = prerequisites_passed / total_prerequisites
        
        self.log_result(
            "系统先决条件总体",
            success_rate >= 0.8,
            f"通过率: {success_rate:.1%} ({prerequisites_passed}/{total_prerequisites})",
            int(success_rate * 100)
        )
        
        return success_rate >= 0.8
    
    def run_comprehensive_tests(self):
        """运行综合测试"""
        print("🧪 Twitter抓取系统综合测试")
        print("=" * 80)
        
        # 检查先决条件
        if not self.check_system_prerequisites():
            print("\n❌ 系统先决条件检查失败，无法继续测试")
            return False
        
        print("\n✅ 系统先决条件检查通过，开始综合测试\n")
        
        # 测试套件配置
        test_suites = [
            ('test_adspower_detection_simple.py', 'AdsPower检测'),
            ('test_core_functionality.py', '核心功能'),
            ('test_performance_stability.py', '性能稳定性'),
            ('test_security.py', '安全性'),
            ('test_data_integrity.py', '数据完整性'),
            ('test_ui_ux.py', 'UI/UX')
        ]
        
        passed_suites = 0
        total_suites = len(test_suites)
        
        # 运行各个测试套件
        for script_name, test_category in test_suites:
            try:
                success, test_data = self.run_test_script(script_name, test_category)
                self.test_results[test_category] = test_data
                
                if success:
                    passed_suites += 1
                    print(f"✅ {test_category}测试: 通过\n")
                else:
                    print(f"❌ {test_category}测试: 失败\n")
                    
            except Exception as e:
                print(f"❌ {test_category}测试: 异常 - {str(e)}\n")
                self.test_results[test_category] = {}
        
        # 生成综合报告
        self.generate_comprehensive_report(passed_suites, total_suites)
        
        return passed_suites == total_suites
    
    def calculate_overall_score(self):
        """计算总体评分"""
        if not self.overall_results:
            return 0
        
        # 权重配置
        weights = {
            'AdsPower检测': 0.10,
            '核心功能': 0.25,
            '性能稳定性': 0.20,
            '安全性': 0.20,
            '数据完整性': 0.15,
            'UI/UX': 0.10
        }
        
        total_score = 0
        total_weight = 0
        
        for result in self.overall_results:
            test_name = result['test_name']
            score = result['score']
            
            # 查找对应的权重
            weight = 0
            for category, w in weights.items():
                if category in test_name:
                    weight = w
                    break
            
            if weight > 0:
                total_score += score * weight
                total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0
    
    def generate_comprehensive_report(self, passed_suites, total_suites):
        """生成综合测试报告"""
        print("=" * 80)
        print("📊 综合测试报告")
        print("=" * 80)
        
        # 基本统计
        print(f"测试套件总数: {total_suites}")
        print(f"通过套件: {passed_suites} ✅")
        print(f"失败套件: {total_suites - passed_suites} ❌")
        print(f"套件成功率: {(passed_suites/total_suites*100):.1f}%")
        
        # 计算总体评分
        overall_score = self.calculate_overall_score()
        print(f"\n🎯 系统总体评分: {overall_score:.1f}/100")
        
        # 详细分析
        print("\n📈 详细分析:")
        
        category_scores = {}
        for result in self.overall_results:
            test_name = result['test_name']
            score = result['score']
            success = result['success']
            
            # 提取类别
            category = "其他"
            for cat in ['AdsPower检测', '核心功能', '性能稳定性', '安全性', '数据完整性', 'UI/UX']:
                if cat in test_name:
                    category = cat
                    break
            
            if category not in category_scores:
                category_scores[category] = []
            category_scores[category].append((score, success))
        
        for category, scores in category_scores.items():
            if scores:
                avg_score = sum(s[0] for s in scores) / len(scores)
                success_count = sum(1 for s in scores if s[1])
                total_count = len(scores)
                
                status_emoji = "✅" if success_count == total_count else "⚠️" if success_count > 0 else "❌"
                print(f"   {status_emoji} {category}: {avg_score:.1f}分 ({success_count}/{total_count}通过)")
        
        # 问题汇总
        failed_tests = [r for r in self.overall_results if not r['success']]
        if failed_tests:
            print(f"\n🚨 发现的问题 ({len(failed_tests)}个):")
            for i, test in enumerate(failed_tests[:10], 1):  # 最多显示10个
                print(f"   {i}. {test['test_name']}: {test['details']}")
            
            if len(failed_tests) > 10:
                print(f"   ... 还有 {len(failed_tests) - 10} 个问题")
        
        # 系统健康评估
        print("\n" + "=" * 80)
        print("🏥 系统健康评估")
        print("=" * 80)
        
        if overall_score >= 90:
            health_status = "🎉 优秀"
            health_desc = "系统运行状态优秀，各项功能正常"
        elif overall_score >= 80:
            health_status = "✅ 良好"
            health_desc = "系统运行状态良好，存在少量改进空间"
        elif overall_score >= 70:
            health_status = "⚠️ 一般"
            health_desc = "系统基本可用，但存在一些需要关注的问题"
        elif overall_score >= 60:
            health_status = "🔧 需要改进"
            health_desc = "系统存在较多问题，需要及时修复"
        else:
            health_status = "❌ 严重问题"
            health_desc = "系统存在严重问题，需要立即处理"
        
        print(f"系统状态: {health_status}")
        print(f"评估说明: {health_desc}")
        
        # 改进建议
        print("\n💡 改进建议:")
        
        suggestions = []
        
        if any('核心功能' in r['test_name'] and not r['success'] for r in self.overall_results):
            suggestions.append("1. 修复核心功能模块的缺失方法和类")
        
        if any('安全性' in r['test_name'] and not r['success'] for r in self.overall_results):
            suggestions.append("2. 加强系统安全防护，添加输入验证和安全头")
        
        if any('性能' in r['test_name'] and not r['success'] for r in self.overall_results):
            suggestions.append("3. 优化系统性能，改善响应时间和并发处理能力")
        
        if any('UI/UX' in r['test_name'] and not r['success'] for r in self.overall_results):
            suggestions.append("4. 改善用户界面和用户体验")
        
        if any('数据完整性' in r['test_name'] and not r['success'] for r in self.overall_results):
            suggestions.append("5. 完善数据管理和备份机制")
        
        if not suggestions:
            suggestions = [
                "1. 继续保持系统的良好状态",
                "2. 定期进行系统测试和维护",
                "3. 关注新功能的开发和优化"
            ]
        
        for suggestion in suggestions:
            print(f"   {suggestion}")
        
        # 保存综合报告
        report_data = {
            'test_summary': {
                'total_suites': total_suites,
                'passed_suites': passed_suites,
                'suite_success_rate': passed_suites / total_suites,
                'overall_score': overall_score,
                'health_status': health_status,
                'health_description': health_desc,
                'timestamp': datetime.now().isoformat()
            },
            'category_scores': category_scores,
            'detailed_results': self.overall_results,
            'individual_test_results': self.test_results,
            'improvement_suggestions': suggestions
        }
        
        report_file = self.project_root / "comprehensive_test_report.json"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            print(f"\n📄 综合测试报告已保存: {report_file}")
        except Exception as e:
            print(f"\n⚠️ 无法保存综合报告: {str(e)}")
        
        # 测试完成提示
        print("\n" + "=" * 80)
        print("🎯 测试完成")
        print("=" * 80)
        print(f"总体评分: {overall_score:.1f}/100")
        print(f"系统状态: {health_status}")
        print("\n感谢使用Twitter抓取系统综合测试工具！")
        print("如有问题，请查看详细报告文件。")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Twitter抓取系统综合测试')
    parser.add_argument('--url', default='http://localhost:8084', 
                       help='Web服务器地址 (默认: http://localhost:8084)')
    
    args = parser.parse_args()
    
    tester = ComprehensiveTester(args.url)
    tester.run_comprehensive_tests()

if __name__ == '__main__':
    main()