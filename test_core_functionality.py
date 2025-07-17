#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter抓取系统核心功能测试脚本
测试主要模块的功能完整性和稳定性
"""

import os
import sys
import json
import time
import sqlite3
import requests
import threading
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class CoreFunctionalityTester:
    def __init__(self, base_url="http://localhost:8084"):
        self.base_url = base_url
        self.test_results = []
        self.project_root = Path(__file__).parent
        
    def log_test_result(self, test_name, success, details=""):
        """记录测试结果"""
        result = {
            'test_name': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅" if success else "❌"
        print(f"   {status} {test_name}: {details}")
        
    def test_database_connectivity(self):
        """测试数据库连接和基本操作"""
        print("🗄️ 测试数据库连接...")
        
        try:
            db_path = self.project_root / "instance" / "twitter_scraper.db"
            
            # 检查数据库文件是否存在
            if not db_path.exists():
                self.log_test_result("数据库文件存在性", False, "数据库文件不存在")
                return False
                
            # 测试数据库连接
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # 检查主要表是否存在
            tables = ['tweets', 'users', 'scraping_tasks', 'accounts']
            existing_tables = []
            
            for table in tables:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
                if cursor.fetchone():
                    existing_tables.append(table)
                    
            conn.close()
            
            self.log_test_result("数据库连接", True, f"成功连接，发现表: {existing_tables}")
            self.log_test_result("数据库表结构", len(existing_tables) >= 2, f"找到{len(existing_tables)}个表")
            
            return True
            
        except Exception as e:
            self.log_test_result("数据库连接", False, f"连接失败: {str(e)}")
            return False
    
    def test_config_management(self):
        """测试配置管理功能"""
        print("\n⚙️ 测试配置管理...")
        
        try:
            # 测试配置文件导入
            import config
            
            # 检查关键配置项
            required_configs = [
                'ADSPOWER_API_URL', 'ADSPOWER_USER_ID', 'MAX_TWEETS_PER_USER',
                'MIN_LIKES', 'MIN_RETWEETS', 'EXCEL_OUTPUT_PATH'
            ]
            
            missing_configs = []
            for config_name in required_configs:
                if not hasattr(config, config_name):
                    missing_configs.append(config_name)
                    
            if missing_configs:
                self.log_test_result("配置完整性", False, f"缺少配置: {missing_configs}")
            else:
                self.log_test_result("配置完整性", True, "所有必需配置项存在")
                
            # 测试配置值有效性
            if hasattr(config, 'ADSPOWER_API_URL') and config.ADSPOWER_API_URL:
                self.log_test_result("AdsPower配置", True, "AdsPower API URL已配置")
            else:
                self.log_test_result("AdsPower配置", False, "AdsPower API URL未配置")
                
            return len(missing_configs) == 0
            
        except ImportError as e:
            self.log_test_result("配置模块导入", False, f"无法导入配置: {str(e)}")
            return False
        except Exception as e:
            self.log_test_result("配置管理测试", False, f"测试异常: {str(e)}")
            return False
    
    def test_twitter_parser_module(self):
        """测试Twitter解析器模块"""
        print("\n🐦 测试Twitter解析器模块...")
        
        try:
            # 导入Twitter解析器
            import twitter_parser
            
            # 检查关键类和方法
            if hasattr(twitter_parser, 'TwitterParser'):
                parser_class = getattr(twitter_parser, 'TwitterParser')
                
                # 检查关键方法
                required_methods = ['parse_tweets', 'parse_user_profile', 'extract_tweet_data']
                missing_methods = []
                
                for method in required_methods:
                    if not hasattr(parser_class, method):
                        missing_methods.append(method)
                        
                if missing_methods:
                    self.log_test_result("解析器方法完整性", False, f"缺少方法: {missing_methods}")
                else:
                    self.log_test_result("解析器方法完整性", True, "所有必需方法存在")
                    
                self.log_test_result("Twitter解析器模块", True, "模块导入成功")
                return len(missing_methods) == 0
            else:
                self.log_test_result("Twitter解析器模块", False, "TwitterParser类不存在")
                return False
                
        except ImportError as e:
            self.log_test_result("Twitter解析器导入", False, f"无法导入模块: {str(e)}")
            return False
        except Exception as e:
            self.log_test_result("Twitter解析器测试", False, f"测试异常: {str(e)}")
            return False
    
    def test_account_manager(self):
        """测试账户管理器"""
        print("\n👥 测试账户管理器...")
        
        try:
            import account_manager
            
            # 检查AccountManager类
            if hasattr(account_manager, 'AccountManager'):
                manager_class = getattr(account_manager, 'AccountManager')
                
                # 检查关键方法
                required_methods = ['get_available_account', 'mark_account_used', 'release_account']
                missing_methods = []
                
                for method in required_methods:
                    if not hasattr(manager_class, method):
                        missing_methods.append(method)
                        
                if missing_methods:
                    self.log_test_result("账户管理器方法", False, f"缺少方法: {missing_methods}")
                else:
                    self.log_test_result("账户管理器方法", True, "所有必需方法存在")
                    
                # 测试账户文件
                accounts_file = self.project_root / "accounts" / "accounts.json"
                if accounts_file.exists():
                    try:
                        with open(accounts_file, 'r', encoding='utf-8') as f:
                            accounts_data = json.load(f)
                        self.log_test_result("账户配置文件", True, f"找到{len(accounts_data)}个账户配置")
                    except Exception as e:
                        self.log_test_result("账户配置文件", False, f"读取失败: {str(e)}")
                else:
                    self.log_test_result("账户配置文件", False, "accounts.json不存在")
                    
                self.log_test_result("账户管理器模块", True, "模块导入成功")
                return len(missing_methods) == 0
            else:
                self.log_test_result("账户管理器模块", False, "AccountManager类不存在")
                return False
                
        except ImportError as e:
            self.log_test_result("账户管理器导入", False, f"无法导入模块: {str(e)}")
            return False
        except Exception as e:
            self.log_test_result("账户管理器测试", False, f"测试异常: {str(e)}")
            return False
    
    def test_ai_analyzer(self):
        """测试AI分析器"""
        print("\n🤖 测试AI分析器...")
        
        try:
            import ai_analyzer
            
            # 检查AIAnalyzer类
            if hasattr(ai_analyzer, 'AIAnalyzer'):
                analyzer_class = getattr(ai_analyzer, 'AIAnalyzer')
                
                # 检查关键方法
                required_methods = ['analyze_tweet_quality', 'analyze_sentiment', 'generate_insights']
                missing_methods = []
                
                for method in required_methods:
                    if not hasattr(analyzer_class, method):
                        missing_methods.append(method)
                        
                if missing_methods:
                    self.log_test_result("AI分析器方法", False, f"缺少方法: {missing_methods}")
                else:
                    self.log_test_result("AI分析器方法", True, "所有必需方法存在")
                    
                self.log_test_result("AI分析器模块", True, "模块导入成功")
                return len(missing_methods) == 0
            else:
                self.log_test_result("AI分析器模块", False, "AIAnalyzer类不存在")
                return False
                
        except ImportError as e:
            self.log_test_result("AI分析器导入", False, f"无法导入模块: {str(e)}")
            return False
        except Exception as e:
            self.log_test_result("AI分析器测试", False, f"测试异常: {str(e)}")
            return False
    
    def test_batch_scraper(self):
        """测试批量抓取器"""
        print("\n📦 测试批量抓取器...")
        
        try:
            import batch_scraper
            
            # 检查BatchScraper类
            if hasattr(batch_scraper, 'BatchScraper'):
                scraper_class = getattr(batch_scraper, 'BatchScraper')
                
                # 检查关键方法
                required_methods = ['start_batch_scraping', 'get_progress', 'stop_scraping']
                missing_methods = []
                
                for method in required_methods:
                    if not hasattr(scraper_class, method):
                        missing_methods.append(method)
                        
                if missing_methods:
                    self.log_test_result("批量抓取器方法", False, f"缺少方法: {missing_methods}")
                else:
                    self.log_test_result("批量抓取器方法", True, "所有必需方法存在")
                    
                self.log_test_result("批量抓取器模块", True, "模块导入成功")
                return len(missing_methods) == 0
            else:
                self.log_test_result("批量抓取器模块", False, "BatchScraper类不存在")
                return False
                
        except ImportError as e:
            self.log_test_result("批量抓取器导入", False, f"无法导入模块: {str(e)}")
            return False
        except Exception as e:
            self.log_test_result("批量抓取器测试", False, f"测试异常: {str(e)}")
            return False
    
    def test_web_api_endpoints(self):
        """测试Web API端点"""
        print("\n🌐 测试Web API端点...")
        
        # 关键API端点
        api_endpoints = [
            ('/api/status', 'GET', '系统状态'),
            ('/api/config/feishu/test', 'POST', '飞书连接测试'),
            ('/api/test_adspower_connection', 'POST', 'AdsPower连接测试'),
            ('/api/check_adspower_installation', 'POST', 'AdsPower安装检测'),
            ('/api/start-intelligent-scraping', 'POST', '智能抓取'),
            ('/api/analyze-page-structure', 'POST', '页面结构分析')
        ]
        
        successful_endpoints = 0
        
        for endpoint, method, description in api_endpoints:
            try:
                if method == 'GET':
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                else:
                    response = requests.post(f"{self.base_url}{endpoint}", json={}, timeout=10)
                
                # 检查响应状态
                if response.status_code in [200, 400, 422]:  # 400和422表示端点存在但参数错误
                    self.log_test_result(f"API端点 {endpoint}", True, f"{description} - HTTP {response.status_code}")
                    successful_endpoints += 1
                else:
                    self.log_test_result(f"API端点 {endpoint}", False, f"{description} - HTTP {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                self.log_test_result(f"API端点 {endpoint}", False, f"{description} - 请求失败: {str(e)}")
            except Exception as e:
                self.log_test_result(f"API端点 {endpoint}", False, f"{description} - 异常: {str(e)}")
        
        success_rate = successful_endpoints / len(api_endpoints)
        self.log_test_result("API端点总体可用性", success_rate >= 0.7, f"{successful_endpoints}/{len(api_endpoints)} 可用")
        
        return success_rate >= 0.7
    
    def test_file_structure(self):
        """测试文件结构完整性"""
        print("\n📁 测试文件结构完整性...")
        
        # 核心文件列表
        core_files = [
            'main.py', 'config.py', 'twitter_parser.py', 'tweet_filter.py',
            'excel_writer.py', 'ads_browser_launcher.py', 'web_app.py'
        ]
        
        # 增强功能文件
        enhanced_files = [
            'ai_analyzer.py', 'account_manager.py', 'scheduler.py',
            'system_monitor.py', 'management_console.py', 'batch_scraper.py'
        ]
        
        # 配置和数据目录
        directories = [
            'templates', 'static', 'data', 'logs', 'accounts', 'instance'
        ]
        
        missing_core = []
        missing_enhanced = []
        missing_dirs = []
        
        # 检查核心文件
        for file in core_files:
            if not (self.project_root / file).exists():
                missing_core.append(file)
                
        # 检查增强功能文件
        for file in enhanced_files:
            if not (self.project_root / file).exists():
                missing_enhanced.append(file)
                
        # 检查目录
        for directory in directories:
            if not (self.project_root / directory).exists():
                missing_dirs.append(directory)
        
        # 记录结果
        self.log_test_result("核心文件完整性", len(missing_core) == 0, 
                           f"缺少文件: {missing_core}" if missing_core else "所有核心文件存在")
        self.log_test_result("增强功能文件", len(missing_enhanced) <= 2, 
                           f"缺少文件: {missing_enhanced}" if missing_enhanced else "所有增强功能文件存在")
        self.log_test_result("目录结构", len(missing_dirs) <= 1, 
                           f"缺少目录: {missing_dirs}" if missing_dirs else "所有必需目录存在")
        
        return len(missing_core) == 0 and len(missing_enhanced) <= 2
    
    def test_system_dependencies(self):
        """测试系统依赖"""
        print("\n📦 测试系统依赖...")
        
        # 关键Python包
        required_packages = [
            'selenium', 'requests', 'pandas', 'openpyxl', 'flask',
            'sqlite3', 'json', 'datetime', 'threading', 'asyncio'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                if package == 'sqlite3':
                    import sqlite3
                elif package == 'json':
                    import json
                elif package == 'datetime':
                    import datetime
                elif package == 'threading':
                    import threading
                elif package == 'asyncio':
                    import asyncio
                else:
                    __import__(package)
                    
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            self.log_test_result("Python依赖", False, f"缺少包: {missing_packages}")
        else:
            self.log_test_result("Python依赖", True, "所有必需包已安装")
            
        # 检查requirements.txt
        requirements_file = self.project_root / "requirements.txt"
        if requirements_file.exists():
            self.log_test_result("依赖配置文件", True, "requirements.txt存在")
        else:
            self.log_test_result("依赖配置文件", False, "requirements.txt不存在")
            
        return len(missing_packages) == 0
    
    def run_comprehensive_test(self):
        """运行综合测试"""
        print("🧪 Twitter抓取系统核心功能综合测试")
        print("=" * 60)
        
        # 检查Web服务器
        try:
            response = requests.get(self.base_url, timeout=5)
            if response.status_code != 200:
                print(f"❌ Web服务器无法访问: {self.base_url}")
                return
        except:
            print(f"❌ 无法连接到Web服务器: {self.base_url}")
            return
        
        print(f"✅ Web服务器运行正常: {self.base_url}\n")
        
        # 测试套件
        test_suites = [
            ('文件结构完整性', self.test_file_structure),
            ('系统依赖检查', self.test_system_dependencies),
            ('数据库连接', self.test_database_connectivity),
            ('配置管理', self.test_config_management),
            ('Twitter解析器', self.test_twitter_parser_module),
            ('账户管理器', self.test_account_manager),
            ('AI分析器', self.test_ai_analyzer),
            ('批量抓取器', self.test_batch_scraper),
            ('Web API端点', self.test_web_api_endpoints)
        ]
        
        passed_tests = 0
        total_tests = len(test_suites)
        
        for test_name, test_func in test_suites:
            try:
                if test_func():
                    passed_tests += 1
                    print(f"✅ {test_name}: 通过\n")
                else:
                    print(f"❌ {test_name}: 失败\n")
            except Exception as e:
                print(f"❌ {test_name}: 异常 - {str(e)}\n")
        
        # 生成测试报告
        self.generate_test_report(passed_tests, total_tests)
        
        return passed_tests == total_tests
    
    def generate_test_report(self, passed_tests, total_tests):
        """生成测试报告"""
        print("=" * 60)
        print("📊 测试总结")
        print("=" * 60)
        print(f"总测试套件: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {total_tests - passed_tests} ❌")
        print(f"成功率: {(passed_tests/total_tests*100):.1f}%")
        
        # 详细结果统计
        success_count = sum(1 for result in self.test_results if result['success'])
        total_count = len(self.test_results)
        
        print(f"\n详细测试项: {total_count}")
        print(f"成功: {success_count}")
        print(f"失败: {total_count - success_count}")
        print(f"详细成功率: {(success_count/total_count*100):.1f}%")
        
        # 保存详细报告
        report_file = self.project_root / "core_functionality_test_report.json"
        report_data = {
            'test_summary': {
                'total_suites': total_tests,
                'passed_suites': passed_tests,
                'suite_success_rate': passed_tests/total_tests,
                'total_tests': total_count,
                'passed_tests': success_count,
                'test_success_rate': success_count/total_count,
                'timestamp': datetime.now().isoformat()
            },
            'detailed_results': self.test_results
        }
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            print(f"\n📄 详细报告已保存: {report_file}")
        except Exception as e:
            print(f"\n⚠️ 无法保存报告: {str(e)}")
        
        # 系统健康评估
        print("\n" + "=" * 60)
        print("🏥 系统健康评估")
        print("=" * 60)
        
        if passed_tests == total_tests:
            print("🎉 系统状态: 优秀 - 所有核心功能正常")
        elif passed_tests >= total_tests * 0.8:
            print("✅ 系统状态: 良好 - 大部分功能正常")
        elif passed_tests >= total_tests * 0.6:
            print("⚠️ 系统状态: 一般 - 部分功能需要关注")
        else:
            print("❌ 系统状态: 需要修复 - 多个核心功能异常")
        
        print("\n💡 建议:")
        print("1. 定期运行此测试脚本监控系统健康")
        print("2. 关注失败的测试项并及时修复")
        print("3. 在部署前确保所有核心功能测试通过")
        print("4. 监控系统性能和资源使用情况")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Twitter抓取系统核心功能测试')
    parser.add_argument('--url', default='http://localhost:8084', 
                       help='Web服务器地址 (默认: http://localhost:8084)')
    
    args = parser.parse_args()
    
    tester = CoreFunctionalityTester(args.url)
    tester.run_comprehensive_test()

if __name__ == '__main__':
    main()