#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AdsPower 综合测试脚本
整合所有 AdsPower 相关测试功能
"""

import sys
import os
import unittest
import argparse
import time
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入各个测试模块
try:
    from test_adspower_config import TestAdsPowerConfig, TestAdsPowerConfigClass, TestAdsPowerManager
    from test_adspower_connection import TestAdsPowerConnection, TestAdsPowerLauncher
    from test_adspower_web_api import TestAdsPowerWebAPI, TestAdsPowerWebAPIOptimized
except ImportError as e:
    print(f"警告: 无法导入测试模块: {e}")
    print("请确保所有测试文件都在同一目录下")


class AdsPowerTestSuite:
    """AdsPower 测试套件管理器"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = None
        self.end_time = None
        
    def run_config_tests(self, verbose=True):
        """运行配置测试"""
        print("\n" + "="*50)
        print("🔧 AdsPower 配置测试")
        print("="*50)
        
        suite = unittest.TestSuite()
        suite.addTest(unittest.makeSuite(TestAdsPowerConfig))
        suite.addTest(unittest.makeSuite(TestAdsPowerConfigClass))
        suite.addTest(unittest.makeSuite(TestAdsPowerManager))
        
        runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
        result = runner.run(suite)
        
        self.test_results['config'] = {
            'total': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success': result.testsRun - len(result.failures) - len(result.errors)
        }
        
        return len(result.failures) == 0 and len(result.errors) == 0
        
    def run_connection_tests(self, verbose=True):
        """运行连接测试"""
        print("\n" + "="*50)
        print("🔗 AdsPower 连接测试")
        print("="*50)
        
        suite = unittest.TestSuite()
        suite.addTest(unittest.makeSuite(TestAdsPowerConnection))
        suite.addTest(unittest.makeSuite(TestAdsPowerLauncher))
        
        runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
        result = runner.run(suite)
        
        self.test_results['connection'] = {
            'total': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success': result.testsRun - len(result.failures) - len(result.errors)
        }
        
        return len(result.failures) == 0 and len(result.errors) == 0
        
    def run_web_api_tests(self, verbose=True):
        """运行 Web API 测试"""
        print("\n" + "="*50)
        print("🌐 AdsPower Web API 测试")
        print("="*50)
        
        suite = unittest.TestSuite()
        suite.addTest(unittest.makeSuite(TestAdsPowerWebAPI))
        suite.addTest(unittest.makeSuite(TestAdsPowerWebAPIOptimized))
        
        runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
        result = runner.run(suite)
        
        self.test_results['web_api'] = {
            'total': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success': result.testsRun - len(result.failures) - len(result.errors)
        }
        
        return len(result.failures) == 0 and len(result.errors) == 0
        
    def run_all_tests(self, verbose=True, skip_web_api=False):
        """运行所有测试"""
        self.start_time = datetime.now()
        
        print("\n" + "="*80)
        print("🚀 AdsPower 综合测试开始")
        print(f"开始时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        results = []
        
        # 运行配置测试
        try:
            config_success = self.run_config_tests(verbose)
            results.append(('配置测试', config_success))
        except Exception as e:
            print(f"❌ 配置测试异常: {e}")
            results.append(('配置测试', False))
            
        # 运行连接测试
        try:
            connection_success = self.run_connection_tests(verbose)
            results.append(('连接测试', connection_success))
        except Exception as e:
            print(f"❌ 连接测试异常: {e}")
            results.append(('连接测试', False))
            
        # 运行 Web API 测试（可选）
        if not skip_web_api:
            try:
                web_api_success = self.run_web_api_tests(verbose)
                results.append(('Web API测试', web_api_success))
            except Exception as e:
                print(f"❌ Web API测试异常: {e}")
                results.append(('Web API测试', False))
        else:
            print("\n⏭️ 跳过 Web API 测试")
            
        self.end_time = datetime.now()
        
        # 输出测试结果汇总
        self.print_summary(results)
        
        # 返回是否所有测试都通过
        return all(success for _, success in results)
        
    def print_summary(self, results):
        """打印测试结果汇总"""
        duration = self.end_time - self.start_time
        
        print("\n" + "="*80)
        print("📊 AdsPower 测试结果汇总")
        print("="*80)
        print(f"测试时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')} - {self.end_time.strftime('%H:%M:%S')}")
        print(f"总耗时: {duration.total_seconds():.2f} 秒")
        print()
        
        # 测试模块结果
        print("测试模块结果:")
        for test_name, success in results:
            status = "✅ 通过" if success else "❌ 失败"
            print(f"  {test_name}: {status}")
            
        print()
        
        # 详细统计
        if self.test_results:
            print("详细统计:")
            total_tests = 0
            total_success = 0
            total_failures = 0
            total_errors = 0
            
            for category, stats in self.test_results.items():
                total_tests += stats['total']
                total_success += stats['success']
                total_failures += stats['failures']
                total_errors += stats['errors']
                
                print(f"  {category}:")
                print(f"    总计: {stats['total']}")
                print(f"    成功: {stats['success']}")
                print(f"    失败: {stats['failures']}")
                print(f"    错误: {stats['errors']}")
                
            print(f"\n总计:")
            print(f"  测试用例: {total_tests}")
            print(f"  成功: {total_success}")
            print(f"  失败: {total_failures}")
            print(f"  错误: {total_errors}")
            print(f"  成功率: {(total_success/total_tests*100):.1f}%" if total_tests > 0 else "  成功率: N/A")
            
        # 总体结果
        all_passed = all(success for _, success in results)
        print("\n" + "="*80)
        if all_passed:
            print("🎉 所有测试通过！AdsPower 功能正常")
        else:
            print("⚠️ 部分测试失败，请检查 AdsPower 配置和连接")
            print("\n建议检查:")
            print("1. AdsPower 是否已启动并登录")
            print("2. 本地 API 服务是否已开启")
            print("3. API 配置是否正确")
            print("4. 网络连接是否正常")
            print("5. Web 服务器是否运行")
        print("="*80)
        
    def generate_report(self, output_file="adspower_test_report.html"):
        """生成 HTML 测试报告"""
        if not self.test_results:
            print("⚠️ 没有测试结果，无法生成报告")
            return
            
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AdsPower 测试报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; }}
        .summary {{ margin: 20px 0; }}
        .test-category {{ margin: 15px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .success {{ color: #28a745; }}
        .failure {{ color: #dc3545; }}
        .error {{ color: #fd7e14; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f8f9fa; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>AdsPower 测试报告</h1>
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>测试时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')} - {self.end_time.strftime('%H:%M:%S')}</p>
        <p>总耗时: {(self.end_time - self.start_time).total_seconds():.2f} 秒</p>
    </div>
    
    <div class="summary">
        <h2>测试汇总</h2>
        <table>
            <tr><th>测试类别</th><th>总计</th><th>成功</th><th>失败</th><th>错误</th><th>成功率</th></tr>
"""
        
        for category, stats in self.test_results.items():
            success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
            html_content += f"""
            <tr>
                <td>{category}</td>
                <td>{stats['total']}</td>
                <td class="success">{stats['success']}</td>
                <td class="failure">{stats['failures']}</td>
                <td class="error">{stats['errors']}</td>
                <td>{success_rate:.1f}%</td>
            </tr>
"""
            
        html_content += """
        </table>
    </div>
    
    <div class="test-details">
        <h2>测试详情</h2>
"""
        
        for category, stats in self.test_results.items():
            html_content += f"""
        <div class="test-category">
            <h3>{category} 测试</h3>
            <p>总计: {stats['total']}, 成功: <span class="success">{stats['success']}</span>, 
               失败: <span class="failure">{stats['failures']}</span>, 
               错误: <span class="error">{stats['errors']}</span></p>
        </div>
"""
            
        html_content += """
    </div>
</body>
</html>
"""
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"✅ 测试报告已生成: {output_file}")
        except Exception as e:
            print(f"❌ 生成测试报告失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='AdsPower 综合测试脚本')
    parser.add_argument('--config', action='store_true', help='只运行配置测试')
    parser.add_argument('--connection', action='store_true', help='只运行连接测试')
    parser.add_argument('--web-api', action='store_true', help='只运行 Web API 测试')
    parser.add_argument('--skip-web-api', action='store_true', help='跳过 Web API 测试')
    parser.add_argument('--quiet', '-q', action='store_true', help='静默模式')
    parser.add_argument('--report', '-r', help='生成 HTML 报告文件路径')
    
    args = parser.parse_args()
    
    test_suite = AdsPowerTestSuite()
    verbose = not args.quiet
    
    success = False
    
    try:
        if args.config:
            success = test_suite.run_config_tests(verbose)
        elif args.connection:
            success = test_suite.run_connection_tests(verbose)
        elif args.web_api:
            success = test_suite.run_web_api_tests(verbose)
        else:
            success = test_suite.run_all_tests(verbose, args.skip_web_api)
            
        # 生成报告
        if args.report:
            test_suite.generate_report(args.report)
            
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被用户中断")
        success = False
    except Exception as e:
        print(f"\n\n❌ 测试执行异常: {e}")
        success = False
        
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()