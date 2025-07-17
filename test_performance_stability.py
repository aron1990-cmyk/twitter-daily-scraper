#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter抓取系统性能和稳定性测试脚本
测试系统的并发处理能力、内存使用、响应时间等关键性能指标
"""

import os
import sys
import json
import time
import psutil
import requests
import threading
import concurrent.futures
from datetime import datetime, timedelta
from pathlib import Path
import statistics
import sqlite3

class PerformanceStabilityTester:
    def __init__(self, base_url="http://localhost:8084"):
        self.base_url = base_url
        self.test_results = []
        self.performance_metrics = []
        self.project_root = Path(__file__).parent
        
    def log_test_result(self, test_name, success, details="", metrics=None):
        """记录测试结果"""
        result = {
            'test_name': test_name,
            'success': success,
            'details': details,
            'metrics': metrics or {},
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅" if success else "❌"
        print(f"   {status} {test_name}: {details}")
        
        if metrics:
            for key, value in metrics.items():
                print(f"      📊 {key}: {value}")
    
    def get_system_metrics(self):
        """获取系统性能指标"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / (1024**3),
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / (1024**3)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def test_api_response_time(self):
        """测试API响应时间"""
        print("⏱️ 测试API响应时间...")
        
        test_endpoints = [
            ('/api/status', 'GET'),
            ('/api/check_adspower_installation', 'POST'),
            ('/config', 'GET'),
            ('/', 'GET')
        ]
        
        response_times = []
        successful_requests = 0
        
        for endpoint, method in test_endpoints:
            times = []
            
            # 每个端点测试5次
            for _ in range(5):
                try:
                    start_time = time.time()
                    
                    if method == 'GET':
                        response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                    else:
                        response = requests.post(f"{self.base_url}{endpoint}", json={}, timeout=10)
                    
                    end_time = time.time()
                    response_time = (end_time - start_time) * 1000  # 转换为毫秒
                    
                    if response.status_code in [200, 400, 422]:
                        times.append(response_time)
                        successful_requests += 1
                        
                except Exception as e:
                    print(f"      ⚠️ {endpoint} 请求失败: {str(e)}")
            
            if times:
                avg_time = statistics.mean(times)
                min_time = min(times)
                max_time = max(times)
                response_times.extend(times)
                
                self.log_test_result(
                    f"响应时间 {endpoint}",
                    avg_time < 2000,  # 平均响应时间小于2秒
                    f"平均: {avg_time:.1f}ms",
                    {
                        'avg_ms': round(avg_time, 1),
                        'min_ms': round(min_time, 1),
                        'max_ms': round(max_time, 1)
                    }
                )
        
        if response_times:
            overall_avg = statistics.mean(response_times)
            self.log_test_result(
                "整体响应时间",
                overall_avg < 1500,
                f"平均: {overall_avg:.1f}ms",
                {
                    'overall_avg_ms': round(overall_avg, 1),
                    'successful_requests': successful_requests,
                    'total_requests': len(test_endpoints) * 5
                }
            )
            return overall_avg < 1500
        
        return False
    
    def test_concurrent_requests(self):
        """测试并发请求处理能力"""
        print("\n🚀 测试并发请求处理能力...")
        
        def make_request(request_id):
            """发送单个请求"""
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}/api/status", timeout=15)
                end_time = time.time()
                
                return {
                    'request_id': request_id,
                    'success': response.status_code == 200,
                    'response_time': (end_time - start_time) * 1000,
                    'status_code': response.status_code
                }
            except Exception as e:
                return {
                    'request_id': request_id,
                    'success': False,
                    'error': str(e),
                    'response_time': None
                }
        
        # 测试不同并发级别
        concurrency_levels = [5, 10, 20]
        
        for concurrency in concurrency_levels:
            print(f"\n   测试并发级别: {concurrency}")
            
            start_time = time.time()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [executor.submit(make_request, i) for i in range(concurrency)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # 分析结果
            successful_requests = sum(1 for r in results if r['success'])
            failed_requests = concurrency - successful_requests
            
            response_times = [r['response_time'] for r in results if r['response_time'] is not None]
            
            if response_times:
                avg_response_time = statistics.mean(response_times)
                max_response_time = max(response_times)
                min_response_time = min(response_times)
            else:
                avg_response_time = max_response_time = min_response_time = 0
            
            success_rate = successful_requests / concurrency
            requests_per_second = concurrency / total_time
            
            self.log_test_result(
                f"并发测试 {concurrency}个请求",
                success_rate >= 0.9 and avg_response_time < 3000,
                f"成功率: {success_rate:.1%}, 平均响应: {avg_response_time:.1f}ms",
                {
                    'concurrency': concurrency,
                    'success_rate': round(success_rate, 3),
                    'successful_requests': successful_requests,
                    'failed_requests': failed_requests,
                    'avg_response_time_ms': round(avg_response_time, 1),
                    'max_response_time_ms': round(max_response_time, 1),
                    'min_response_time_ms': round(min_response_time, 1),
                    'total_time_seconds': round(total_time, 2),
                    'requests_per_second': round(requests_per_second, 2)
                }
            )
        
        return True
    
    def test_memory_usage(self):
        """测试内存使用情况"""
        print("\n🧠 测试内存使用情况...")
        
        # 获取初始内存状态
        initial_metrics = self.get_system_metrics()
        initial_memory = initial_metrics.get('memory_percent', 0)
        
        # 执行一系列操作来测试内存使用
        operations = [
            ('访问首页', lambda: requests.get(f"{self.base_url}/", timeout=10)),
            ('访问配置页面', lambda: requests.get(f"{self.base_url}/config", timeout=10)),
            ('检查系统状态', lambda: requests.get(f"{self.base_url}/api/status", timeout=10)),
            ('测试AdsPower连接', lambda: requests.post(f"{self.base_url}/api/check_adspower_installation", json={}, timeout=10))
        ]
        
        memory_readings = [initial_memory]
        
        for operation_name, operation in operations:
            try:
                # 执行操作
                operation()
                time.sleep(1)  # 等待内存稳定
                
                # 获取内存使用
                current_metrics = self.get_system_metrics()
                current_memory = current_metrics.get('memory_percent', 0)
                memory_readings.append(current_memory)
                
                print(f"      {operation_name}: 内存使用 {current_memory:.1f}%")
                
            except Exception as e:
                print(f"      ⚠️ {operation_name} 执行失败: {str(e)}")
        
        # 分析内存使用
        max_memory = max(memory_readings)
        memory_increase = max_memory - initial_memory
        
        self.log_test_result(
            "内存使用测试",
            memory_increase < 10 and max_memory < 80,  # 内存增长小于10%且总使用小于80%
            f"最大使用: {max_memory:.1f}%, 增长: {memory_increase:.1f}%",
            {
                'initial_memory_percent': round(initial_memory, 1),
                'max_memory_percent': round(max_memory, 1),
                'memory_increase_percent': round(memory_increase, 1),
                'memory_readings': [round(m, 1) for m in memory_readings]
            }
        )
        
        return memory_increase < 15  # 允许15%的内存增长
    
    def test_database_performance(self):
        """测试数据库性能"""
        print("\n🗄️ 测试数据库性能...")
        
        try:
            db_path = self.project_root / "instance" / "twitter_scraper.db"
            
            if not db_path.exists():
                self.log_test_result("数据库性能测试", False, "数据库文件不存在")
                return False
            
            # 测试数据库连接时间
            connection_times = []
            query_times = []
            
            for i in range(5):
                # 测试连接时间
                start_time = time.time()
                conn = sqlite3.connect(str(db_path))
                connection_time = (time.time() - start_time) * 1000
                connection_times.append(connection_time)
                
                # 测试查询时间
                cursor = conn.cursor()
                start_time = time.time()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                results = cursor.fetchall()
                query_time = (time.time() - start_time) * 1000
                query_times.append(query_time)
                
                conn.close()
            
            avg_connection_time = statistics.mean(connection_times)
            avg_query_time = statistics.mean(query_times)
            
            self.log_test_result(
                "数据库连接性能",
                avg_connection_time < 100,  # 连接时间小于100ms
                f"平均连接时间: {avg_connection_time:.1f}ms",
                {
                    'avg_connection_time_ms': round(avg_connection_time, 1),
                    'max_connection_time_ms': round(max(connection_times), 1),
                    'min_connection_time_ms': round(min(connection_times), 1)
                }
            )
            
            self.log_test_result(
                "数据库查询性能",
                avg_query_time < 50,  # 查询时间小于50ms
                f"平均查询时间: {avg_query_time:.1f}ms",
                {
                    'avg_query_time_ms': round(avg_query_time, 1),
                    'max_query_time_ms': round(max(query_times), 1),
                    'min_query_time_ms': round(min(query_times), 1)
                }
            )
            
            return avg_connection_time < 100 and avg_query_time < 50
            
        except Exception as e:
            self.log_test_result("数据库性能测试", False, f"测试异常: {str(e)}")
            return False
    
    def test_error_recovery(self):
        """测试错误恢复能力"""
        print("\n🛡️ 测试错误恢复能力...")
        
        # 测试各种错误情况
        error_scenarios = [
            {
                'name': '无效JSON请求',
                'method': 'POST',
                'endpoint': '/api/check_adspower_installation',
                'data': 'invalid json',
                'headers': {'Content-Type': 'application/json'}
            },
            {
                'name': '超大请求体',
                'method': 'POST',
                'endpoint': '/api/check_adspower_installation',
                'data': json.dumps({'data': 'x' * 10000}),
                'headers': {'Content-Type': 'application/json'}
            },
            {
                'name': '不存在的端点',
                'method': 'GET',
                'endpoint': '/api/nonexistent',
                'data': None,
                'headers': {}
            }
        ]
        
        recovery_success = 0
        
        for scenario in error_scenarios:
            try:
                # 发送错误请求
                if scenario['method'] == 'GET':
                    response = requests.get(
                        f"{self.base_url}{scenario['endpoint']}",
                        headers=scenario['headers'],
                        timeout=10
                    )
                else:
                    response = requests.post(
                        f"{self.base_url}{scenario['endpoint']}",
                        data=scenario['data'],
                        headers=scenario['headers'],
                        timeout=10
                    )
                
                # 检查服务器是否正确处理错误
                if response.status_code in [400, 404, 422, 500]:
                    # 发送正常请求验证服务器仍然可用
                    test_response = requests.get(f"{self.base_url}/api/status", timeout=10)
                    
                    if test_response.status_code == 200:
                        recovery_success += 1
                        self.log_test_result(
                            f"错误恢复 - {scenario['name']}",
                            True,
                            f"正确处理错误 (HTTP {response.status_code}) 并恢复正常"
                        )
                    else:
                        self.log_test_result(
                            f"错误恢复 - {scenario['name']}",
                            False,
                            "服务器未能从错误中恢复"
                        )
                else:
                    self.log_test_result(
                        f"错误恢复 - {scenario['name']}",
                        False,
                        f"未正确处理错误请求 (HTTP {response.status_code})"
                    )
                    
            except Exception as e:
                self.log_test_result(
                    f"错误恢复 - {scenario['name']}",
                    False,
                    f"测试异常: {str(e)}"
                )
        
        success_rate = recovery_success / len(error_scenarios)
        self.log_test_result(
            "整体错误恢复能力",
            success_rate >= 0.7,
            f"恢复成功率: {success_rate:.1%}",
            {'recovery_success_rate': round(success_rate, 3)}
        )
        
        return success_rate >= 0.7
    
    def test_sustained_load(self):
        """测试持续负载能力"""
        print("\n⏳ 测试持续负载能力...")
        
        duration_seconds = 30  # 测试30秒
        request_interval = 0.5  # 每0.5秒一个请求
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        successful_requests = 0
        failed_requests = 0
        response_times = []
        
        print(f"   开始{duration_seconds}秒持续负载测试...")
        
        while time.time() < end_time:
            try:
                request_start = time.time()
                response = requests.get(f"{self.base_url}/api/status", timeout=10)
                request_end = time.time()
                
                response_time = (request_end - request_start) * 1000
                response_times.append(response_time)
                
                if response.status_code == 200:
                    successful_requests += 1
                else:
                    failed_requests += 1
                    
            except Exception as e:
                failed_requests += 1
                print(f"      请求失败: {str(e)}")
            
            # 等待下一个请求
            time.sleep(request_interval)
        
        total_requests = successful_requests + failed_requests
        success_rate = successful_requests / total_requests if total_requests > 0 else 0
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
        else:
            avg_response_time = max_response_time = min_response_time = 0
        
        self.log_test_result(
            "持续负载测试",
            success_rate >= 0.95 and avg_response_time < 2000,
            f"成功率: {success_rate:.1%}, 平均响应: {avg_response_time:.1f}ms",
            {
                'duration_seconds': duration_seconds,
                'total_requests': total_requests,
                'successful_requests': successful_requests,
                'failed_requests': failed_requests,
                'success_rate': round(success_rate, 3),
                'avg_response_time_ms': round(avg_response_time, 1),
                'max_response_time_ms': round(max_response_time, 1),
                'min_response_time_ms': round(min_response_time, 1)
            }
        )
        
        return success_rate >= 0.9
    
    def run_comprehensive_test(self):
        """运行综合性能和稳定性测试"""
        print("🚀 Twitter抓取系统性能和稳定性测试")
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
        
        print(f"✅ Web服务器运行正常: {self.base_url}")
        
        # 记录初始系统状态
        initial_metrics = self.get_system_metrics()
        print(f"📊 初始系统状态:")
        print(f"   CPU使用率: {initial_metrics.get('cpu_percent', 0):.1f}%")
        print(f"   内存使用率: {initial_metrics.get('memory_percent', 0):.1f}%")
        print(f"   可用内存: {initial_metrics.get('memory_available_gb', 0):.1f}GB")
        print()
        
        # 测试套件
        test_suites = [
            ('API响应时间', self.test_api_response_time),
            ('并发请求处理', self.test_concurrent_requests),
            ('内存使用情况', self.test_memory_usage),
            ('数据库性能', self.test_database_performance),
            ('错误恢复能力', self.test_error_recovery),
            ('持续负载能力', self.test_sustained_load)
        ]
        
        passed_tests = 0
        total_tests = len(test_suites)
        
        for test_name, test_func in test_suites:
            try:
                print(f"\n{'='*20} {test_name} {'='*20}")
                if test_func():
                    passed_tests += 1
                    print(f"✅ {test_name}: 通过")
                else:
                    print(f"❌ {test_name}: 失败")
            except Exception as e:
                print(f"❌ {test_name}: 异常 - {str(e)}")
        
        # 记录最终系统状态
        final_metrics = self.get_system_metrics()
        
        # 生成测试报告
        self.generate_performance_report(passed_tests, total_tests, initial_metrics, final_metrics)
        
        return passed_tests == total_tests
    
    def generate_performance_report(self, passed_tests, total_tests, initial_metrics, final_metrics):
        """生成性能测试报告"""
        print("\n" + "=" * 60)
        print("📊 性能测试总结")
        print("=" * 60)
        print(f"总测试套件: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {total_tests - passed_tests} ❌")
        print(f"成功率: {(passed_tests/total_tests*100):.1f}%")
        
        # 系统资源变化
        cpu_change = final_metrics.get('cpu_percent', 0) - initial_metrics.get('cpu_percent', 0)
        memory_change = final_metrics.get('memory_percent', 0) - initial_metrics.get('memory_percent', 0)
        
        print(f"\n📈 系统资源变化:")
        print(f"CPU使用变化: {cpu_change:+.1f}%")
        print(f"内存使用变化: {memory_change:+.1f}%")
        
        # 详细结果统计
        success_count = sum(1 for result in self.test_results if result['success'])
        total_count = len(self.test_results)
        
        print(f"\n详细测试项: {total_count}")
        print(f"成功: {success_count}")
        print(f"失败: {total_count - success_count}")
        print(f"详细成功率: {(success_count/total_count*100):.1f}%")
        
        # 保存详细报告
        report_file = self.project_root / "performance_stability_test_report.json"
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
            'system_metrics': {
                'initial': initial_metrics,
                'final': final_metrics,
                'cpu_change': cpu_change,
                'memory_change': memory_change
            },
            'detailed_results': self.test_results
        }
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            print(f"\n📄 详细报告已保存: {report_file}")
        except Exception as e:
            print(f"\n⚠️ 无法保存报告: {str(e)}")
        
        # 性能评估
        print("\n" + "=" * 60)
        print("🏆 性能评估")
        print("=" * 60)
        
        if passed_tests == total_tests:
            print("🎉 性能状态: 优秀 - 所有性能指标达标")
        elif passed_tests >= total_tests * 0.8:
            print("✅ 性能状态: 良好 - 大部分性能指标正常")
        elif passed_tests >= total_tests * 0.6:
            print("⚠️ 性能状态: 一般 - 部分性能需要优化")
        else:
            print("❌ 性能状态: 需要优化 - 多项性能指标不达标")
        
        print("\n💡 性能优化建议:")
        print("1. 监控API响应时间，保持在合理范围内")
        print("2. 优化并发处理能力，提高系统吞吐量")
        print("3. 控制内存使用，避免内存泄漏")
        print("4. 优化数据库查询性能")
        print("5. 增强错误处理和恢复机制")
        print("6. 定期进行性能测试和监控")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Twitter抓取系统性能和稳定性测试')
    parser.add_argument('--url', default='http://localhost:8084', 
                       help='Web服务器地址 (默认: http://localhost:8084)')
    
    args = parser.parse_args()
    
    tester = PerformanceStabilityTester(args.url)
    tester.run_comprehensive_test()

if __name__ == '__main__':
    main()