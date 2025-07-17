#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter抓取系统测试结果总结脚本
快速查看所有测试报告的汇总信息
"""

import json
import os
from pathlib import Path
from datetime import datetime

class TestSummary:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.report_files = {
            'AdsPower检测': 'adspower_detection_test_report.json',
            '核心功能': 'core_functionality_test_report.json', 
            '性能稳定性': 'performance_stability_test_report.json',
            '安全性': 'security_test_report.json',
            '数据完整性': 'data_integrity_test_report.json',
            'UI/UX': 'ui_ux_test_report.json',
            '综合测试': 'comprehensive_test_report.json'
        }
    
    def load_report(self, report_file):
        """加载测试报告"""
        report_path = self.project_root / report_file
        
        if not report_path.exists():
            return None
        
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 无法读取报告文件 {report_file}: {str(e)}")
            return None
    
    def format_percentage(self, value):
        """格式化百分比"""
        if isinstance(value, (int, float)):
            return f"{value * 100:.1f}%" if value <= 1 else f"{value:.1f}%"
        return "N/A"
    
    def get_status_emoji(self, success_rate):
        """根据成功率获取状态表情"""
        if success_rate >= 0.9:
            return "🎉"
        elif success_rate >= 0.8:
            return "✅"
        elif success_rate >= 0.7:
            return "⚠️"
        elif success_rate >= 0.5:
            return "🔧"
        else:
            return "❌"
    
    def display_summary(self):
        """显示测试总结"""
        print("📋 Twitter抓取系统测试结果总结")
        print("=" * 80)
        print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 检查报告文件
        available_reports = []
        missing_reports = []
        
        for test_name, report_file in self.report_files.items():
            if (self.project_root / report_file).exists():
                available_reports.append((test_name, report_file))
            else:
                missing_reports.append((test_name, report_file))
        
        print(f"📊 可用报告: {len(available_reports)}/{len(self.report_files)}")
        
        if missing_reports:
            print(f"⚠️ 缺失报告: {', '.join([name for name, _ in missing_reports])}")
        
        print()
        
        # 显示各个测试模块的结果
        print("📈 各模块测试结果:")
        print("-" * 80)
        
        total_score = 0
        total_weight = 0
        
        # 权重配置
        weights = {
            'AdsPower检测': 0.10,
            '核心功能': 0.25,
            '性能稳定性': 0.20,
            '安全性': 0.20,
            '数据完整性': 0.15,
            'UI/UX': 0.10
        }
        
        for test_name, report_file in available_reports:
            if test_name == '综合测试':
                continue  # 跳过综合测试，单独处理
                
            report_data = self.load_report(report_file)
            
            if not report_data:
                print(f"❌ {test_name:<15}: 无法读取报告")
                continue
            
            # 提取关键信息
            summary = report_data.get('test_summary', {})
            
            # 尝试获取成功率
            success_rate = None
            score = 0
            
            if 'suite_success_rate' in summary:
                success_rate = summary['suite_success_rate']
                score = success_rate * 100
            elif 'test_success_rate' in summary:
                success_rate = summary['test_success_rate']
                score = success_rate * 100
            elif 'overall_score' in summary:
                score = summary['overall_score']
                success_rate = score / 100
            
            # 获取详细统计
            passed = summary.get('passed_tests', summary.get('passed_suites', 0))
            total = summary.get('total_tests', summary.get('total_suites', 0))
            
            # 获取状态描述
            status = summary.get('status', summary.get('health_status', '未知'))
            
            # 显示结果
            if success_rate is not None:
                emoji = self.get_status_emoji(success_rate)
                print(f"{emoji} {test_name:<15}: {self.format_percentage(success_rate):<8} ({passed}/{total}) - {status}")
                
                # 计算加权分数
                weight = weights.get(test_name, 0)
                if weight > 0:
                    total_score += score * weight
                    total_weight += weight
            else:
                print(f"❓ {test_name:<15}: 无法获取成功率 - {status}")
        
        # 显示综合测试结果
        print()
        print("🎯 综合测试结果:")
        print("-" * 80)
        
        comprehensive_report = self.load_report('comprehensive_test_report.json')
        if comprehensive_report:
            summary = comprehensive_report.get('test_summary', {})
            overall_score = summary.get('overall_score', 0)
            health_status = summary.get('health_status', '未知')
            suite_success_rate = summary.get('suite_success_rate', 0)
            passed_suites = summary.get('passed_suites', 0)
            total_suites = summary.get('total_suites', 0)
            
            emoji = self.get_status_emoji(overall_score / 100)
            print(f"{emoji} 系统总体评分: {overall_score:.1f}/100")
            print(f"📊 套件成功率: {self.format_percentage(suite_success_rate)} ({passed_suites}/{total_suites})")
            print(f"🏥 系统状态: {health_status}")
        else:
            print("❌ 综合测试报告不存在")
        
        # 显示关键问题
        print()
        print("🚨 关键问题汇总:")
        print("-" * 80)
        
        all_issues = []
        
        for test_name, report_file in available_reports:
            if test_name == '综合测试':
                continue
                
            report_data = self.load_report(report_file)
            if not report_data:
                continue
            
            # 提取失败的测试
            failed_tests = report_data.get('failed_tests', [])
            detailed_results = report_data.get('detailed_results', [])
            
            # 从详细结果中提取失败项
            if detailed_results and isinstance(detailed_results, list):
                for result in detailed_results:
                    if isinstance(result, dict) and not result.get('success', True):
                        all_issues.append({
                            'category': test_name,
                            'test_name': result.get('test_name', '未知测试'),
                            'details': result.get('details', '无详细信息')
                        })
            
            # 从失败测试中提取
            if failed_tests and isinstance(failed_tests, list):
                for test in failed_tests:
                    if isinstance(test, dict):
                        all_issues.append({
                            'category': test_name,
                            'test_name': test.get('test_name', '未知测试'),
                            'details': test.get('error', test.get('details', '无详细信息'))
                        })
        
        if all_issues:
            # 按类别分组显示
            issues_by_category = {}
            for issue in all_issues:
                category = issue['category']
                if category not in issues_by_category:
                    issues_by_category[category] = []
                issues_by_category[category].append(issue)
            
            for category, issues in issues_by_category.items():
                print(f"\n📍 {category} ({len(issues)}个问题):")
                for i, issue in enumerate(issues[:5], 1):  # 最多显示5个
                    print(f"   {i}. {issue['test_name']}: {issue['details'][:100]}...")
                
                if len(issues) > 5:
                    print(f"   ... 还有 {len(issues) - 5} 个问题")
        else:
            print("✅ 未发现关键问题")
        
        # 显示改进建议
        print()
        print("💡 改进建议:")
        print("-" * 80)
        
        suggestions = set()
        
        # 从综合报告中获取建议
        if comprehensive_report:
            comp_suggestions = comprehensive_report.get('improvement_suggestions', [])
            for suggestion in comp_suggestions:
                suggestions.add(suggestion)
        
        # 从各个报告中获取建议
        for test_name, report_file in available_reports:
            if test_name == '综合测试':
                continue
                
            report_data = self.load_report(report_file)
            if not report_data:
                continue
            
            report_suggestions = report_data.get('suggestions', report_data.get('improvement_suggestions', []))
            for suggestion in report_suggestions:
                if isinstance(suggestion, str):
                    suggestions.add(suggestion)
                elif isinstance(suggestion, dict) and 'suggestion' in suggestion:
                    suggestions.add(suggestion['suggestion'])
        
        if suggestions:
            for i, suggestion in enumerate(sorted(suggestions)[:10], 1):
                print(f"   {i}. {suggestion}")
        else:
            print("   暂无改进建议")
        
        # 显示测试文件状态
        print()
        print("📁 测试文件状态:")
        print("-" * 80)
        
        test_files = [
            'test_adspower_detection_simple.py',
            'test_core_functionality.py',
            'test_performance_stability.py', 
            'test_security.py',
            'test_data_integrity.py',
            'test_ui_ux.py',
            'test_comprehensive.py'
        ]
        
        for test_file in test_files:
            file_path = self.project_root / test_file
            if file_path.exists():
                size = file_path.stat().st_size
                print(f"✅ {test_file:<35}: {size:,} bytes")
            else:
                print(f"❌ {test_file:<35}: 文件不存在")
        
        print()
        print("=" * 80)
        print("📋 总结完成")
        print("=" * 80)
        
        if comprehensive_report:
            summary = comprehensive_report.get('test_summary', {})
            overall_score = summary.get('overall_score', 0)
            
            if overall_score >= 80:
                print("🎉 系统整体状态良好，继续保持！")
            elif overall_score >= 60:
                print("⚠️ 系统存在一些问题，建议及时修复")
            else:
                print("🚨 系统存在严重问题，需要立即处理")
        
        print("\n如需查看详细信息，请查看对应的测试报告文件。")

def main():
    """主函数"""
    summary = TestSummary()
    summary.display_summary()

if __name__ == '__main__':
    main()