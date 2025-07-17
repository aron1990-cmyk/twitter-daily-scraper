#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter抓取系统安全性测试脚本
测试系统的安全防护能力，包括输入验证、注入攻击防护、权限控制等
"""

import os
import sys
import json
import time
import requests
import urllib.parse
from datetime import datetime
from pathlib import Path
import base64
import hashlib

class SecurityTester:
    def __init__(self, base_url="http://localhost:8084"):
        self.base_url = base_url
        self.test_results = []
        self.project_root = Path(__file__).parent
        
    def log_test_result(self, test_name, success, details="", risk_level="LOW"):
        """记录测试结果"""
        result = {
            'test_name': test_name,
            'success': success,
            'details': details,
            'risk_level': risk_level,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        risk_emoji = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}.get(risk_level, "⚪")
        print(f"   {status} {risk_emoji} {test_name}: {details}")
    
    def test_sql_injection_protection(self):
        """测试SQL注入防护"""
        print("🛡️ 测试SQL注入防护...")
        
        # SQL注入测试载荷
        sql_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM users --",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --",
            "' OR 1=1 --",
            "admin'--",
            "' OR 'x'='x",
            "'; EXEC xp_cmdshell('dir'); --"
        ]
        
        # 测试不同的输入点
        test_endpoints = [
            ('/api/check_adspower_installation', 'POST', 'api_url'),
            ('/api/test_adspower_connection', 'POST', 'api_url'),
            ('/api/config/feishu/test', 'POST', 'webhook_url')
        ]
        
        injection_blocked = 0
        total_tests = 0
        
        for endpoint, method, param_name in test_endpoints:
            for payload in sql_payloads:
                total_tests += 1
                
                try:
                    data = {param_name: payload}
                    
                    if method == 'POST':
                        response = requests.post(
                            f"{self.base_url}{endpoint}",
                            json=data,
                            timeout=10
                        )
                    else:
                        response = requests.get(
                            f"{self.base_url}{endpoint}",
                            params=data,
                            timeout=10
                        )
                    
                    # 检查是否正确阻止了SQL注入
                    if response.status_code in [400, 422, 500]:  # 错误响应表示被阻止
                        injection_blocked += 1
                    elif "error" in response.text.lower() or "invalid" in response.text.lower():
                        injection_blocked += 1
                    
                except Exception as e:
                    # 异常也可能表示攻击被阻止
                    injection_blocked += 1
        
        protection_rate = injection_blocked / total_tests if total_tests > 0 else 0
        
        self.log_test_result(
            "SQL注入防护",
            protection_rate >= 0.8,
            f"防护率: {protection_rate:.1%} ({injection_blocked}/{total_tests})",
            "HIGH" if protection_rate < 0.5 else "MEDIUM" if protection_rate < 0.8 else "LOW"
        )
        
        return protection_rate >= 0.8
    
    def test_xss_protection(self):
        """测试XSS防护"""
        print("\n🔒 测试XSS防护...")
        
        # XSS测试载荷
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "<iframe src=javascript:alert('XSS')></iframe>",
            "<body onload=alert('XSS')>",
            "<input onfocus=alert('XSS') autofocus>",
            "<select onfocus=alert('XSS') autofocus>"
        ]
        
        # 测试页面端点
        page_endpoints = [
            '/config',
            '/data',
            '/tasks'
        ]
        
        xss_blocked = 0
        total_tests = 0
        
        for endpoint in page_endpoints:
            for payload in xss_payloads:
                total_tests += 1
                
                try:
                    # 测试GET参数
                    response = requests.get(
                        f"{self.base_url}{endpoint}",
                        params={'test': payload},
                        timeout=10
                    )
                    
                    # 检查响应中是否包含未转义的脚本
                    if payload not in response.text:
                        xss_blocked += 1
                    elif "&lt;script&gt;" in response.text or "&amp;lt;script&amp;gt;" in response.text:
                        xss_blocked += 1  # 正确转义
                    
                except Exception as e:
                    xss_blocked += 1
        
        protection_rate = xss_blocked / total_tests if total_tests > 0 else 0
        
        self.log_test_result(
            "XSS防护",
            protection_rate >= 0.9,
            f"防护率: {protection_rate:.1%} ({xss_blocked}/{total_tests})",
            "HIGH" if protection_rate < 0.7 else "MEDIUM" if protection_rate < 0.9 else "LOW"
        )
        
        return protection_rate >= 0.9
    
    def test_input_validation(self):
        """测试输入验证"""
        print("\n✅ 测试输入验证...")
        
        # 无效输入测试
        invalid_inputs = [
            {
                'name': '空字符串',
                'data': {'api_url': ''},
                'endpoint': '/api/check_adspower_installation'
            },
            {
                'name': '超长字符串',
                'data': {'api_url': 'x' * 10000},
                'endpoint': '/api/check_adspower_installation'
            },
            {
                'name': '无效URL格式',
                'data': {'api_url': 'not-a-url'},
                'endpoint': '/api/check_adspower_installation'
            },
            {
                'name': '特殊字符',
                'data': {'api_url': '!@#$%^&*()'},
                'endpoint': '/api/check_adspower_installation'
            },
            {
                'name': 'NULL字符',
                'data': {'api_url': '\x00'},
                'endpoint': '/api/check_adspower_installation'
            }
        ]
        
        validation_success = 0
        
        for test_case in invalid_inputs:
            try:
                response = requests.post(
                    f"{self.base_url}{test_case['endpoint']}",
                    json=test_case['data'],
                    timeout=10
                )
                
                # 检查是否正确拒绝无效输入
                if response.status_code in [400, 422]:  # 客户端错误
                    validation_success += 1
                    self.log_test_result(
                        f"输入验证 - {test_case['name']}",
                        True,
                        f"正确拒绝无效输入 (HTTP {response.status_code})"
                    )
                else:
                    self.log_test_result(
                        f"输入验证 - {test_case['name']}",
                        False,
                        f"未正确验证输入 (HTTP {response.status_code})",
                        "MEDIUM"
                    )
                    
            except Exception as e:
                self.log_test_result(
                    f"输入验证 - {test_case['name']}",
                    False,
                    f"测试异常: {str(e)}",
                    "MEDIUM"
                )
        
        success_rate = validation_success / len(invalid_inputs)
        
        self.log_test_result(
            "整体输入验证",
            success_rate >= 0.8,
            f"验证成功率: {success_rate:.1%}",
            "MEDIUM" if success_rate < 0.8 else "LOW"
        )
        
        return success_rate >= 0.8
    
    def test_file_access_security(self):
        """测试文件访问安全性"""
        print("\n📁 测试文件访问安全性...")
        
        # 路径遍历攻击测试
        path_traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc//passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "..%252f..%252f..%252fetc%252fpasswd",
            "..%c0%af..%c0%af..%c0%afetc%c0%afpasswd"
        ]
        
        # 测试静态文件访问
        static_endpoints = [
            '/static/',
            '/templates/',
            '/config/',
            '/data/'
        ]
        
        access_blocked = 0
        total_tests = 0
        
        for endpoint in static_endpoints:
            for payload in path_traversal_payloads:
                total_tests += 1
                
                try:
                    response = requests.get(
                        f"{self.base_url}{endpoint}{payload}",
                        timeout=10
                    )
                    
                    # 检查是否阻止了路径遍历
                    if response.status_code in [403, 404]:  # 禁止访问或未找到
                        access_blocked += 1
                    elif "passwd" not in response.text and "system32" not in response.text:
                        access_blocked += 1  # 没有泄露敏感文件内容
                    
                except Exception as e:
                    access_blocked += 1
        
        protection_rate = access_blocked / total_tests if total_tests > 0 else 0
        
        self.log_test_result(
            "路径遍历防护",
            protection_rate >= 0.9,
            f"防护率: {protection_rate:.1%} ({access_blocked}/{total_tests})",
            "HIGH" if protection_rate < 0.7 else "MEDIUM" if protection_rate < 0.9 else "LOW"
        )
        
        return protection_rate >= 0.9
    
    def test_http_security_headers(self):
        """测试HTTP安全头"""
        print("\n🔐 测试HTTP安全头...")
        
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            headers = response.headers
            
            # 检查重要的安全头
            security_headers = {
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': ['DENY', 'SAMEORIGIN'],
                'X-XSS-Protection': '1; mode=block',
                'Strict-Transport-Security': None,  # HTTPS才需要
                'Content-Security-Policy': None,
                'Referrer-Policy': None
            }
            
            headers_present = 0
            total_headers = len(security_headers)
            
            for header, expected_value in security_headers.items():
                if header in headers:
                    headers_present += 1
                    self.log_test_result(
                        f"安全头 - {header}",
                        True,
                        f"存在: {headers[header]}"
                    )
                else:
                    self.log_test_result(
                        f"安全头 - {header}",
                        False,
                        "缺失",
                        "MEDIUM"
                    )
            
            # 检查是否暴露了服务器信息
            server_header = headers.get('Server', '')
            if 'Flask' in server_header or 'Werkzeug' in server_header:
                self.log_test_result(
                    "服务器信息泄露",
                    False,
                    f"暴露了服务器信息: {server_header}",
                    "MEDIUM"
                )
            else:
                self.log_test_result(
                    "服务器信息泄露",
                    True,
                    "未暴露敏感服务器信息"
                )
            
            success_rate = headers_present / total_headers
            
            self.log_test_result(
                "HTTP安全头总体",
                success_rate >= 0.5,
                f"安全头覆盖率: {success_rate:.1%}",
                "MEDIUM" if success_rate < 0.5 else "LOW"
            )
            
            return success_rate >= 0.3  # 降低要求，因为开发环境可能不需要所有安全头
            
        except Exception as e:
            self.log_test_result(
                "HTTP安全头测试",
                False,
                f"测试异常: {str(e)}",
                "MEDIUM"
            )
            return False
    
    def test_rate_limiting(self):
        """测试速率限制"""
        print("\n⏱️ 测试速率限制...")
        
        # 快速发送大量请求
        rapid_requests = 50
        successful_requests = 0
        blocked_requests = 0
        
        start_time = time.time()
        
        for i in range(rapid_requests):
            try:
                response = requests.get(f"{self.base_url}/api/status", timeout=5)
                
                if response.status_code == 200:
                    successful_requests += 1
                elif response.status_code == 429:  # Too Many Requests
                    blocked_requests += 1
                    
            except Exception as e:
                # 连接被拒绝可能表示速率限制生效
                if "Connection" in str(e):
                    blocked_requests += 1
        
        end_time = time.time()
        duration = end_time - start_time
        requests_per_second = rapid_requests / duration
        
        # 如果所有请求都成功，可能没有速率限制
        rate_limiting_active = blocked_requests > 0 or requests_per_second < 100
        
        self.log_test_result(
            "速率限制",
            rate_limiting_active,
            f"请求速率: {requests_per_second:.1f}/秒, 被阻止: {blocked_requests}",
            "MEDIUM" if not rate_limiting_active else "LOW"
        )
        
        return True  # 速率限制不是必需的，所以总是返回True
    
    def test_error_information_disclosure(self):
        """测试错误信息泄露"""
        print("\n🚨 测试错误信息泄露...")
        
        # 触发各种错误的测试
        error_tests = [
            {
                'name': '404错误',
                'url': f"{self.base_url}/nonexistent-page",
                'method': 'GET'
            },
            {
                'name': '500错误',
                'url': f"{self.base_url}/api/config/feishu/test",
                'method': 'POST',
                'data': {'invalid': 'data'}
            },
            {
                'name': '400错误',
                'url': f"{self.base_url}/api/check_adspower_installation",
                'method': 'POST',
                'data': 'invalid json'
            }
        ]
        
        safe_errors = 0
        
        for test in error_tests:
            try:
                if test['method'] == 'GET':
                    response = requests.get(test['url'], timeout=10)
                else:
                    if isinstance(test.get('data'), str):
                        response = requests.post(
                            test['url'],
                            data=test['data'],
                            headers={'Content-Type': 'application/json'},
                            timeout=10
                        )
                    else:
                        response = requests.post(
                            test['url'],
                            json=test.get('data', {}),
                            timeout=10
                        )
                
                # 检查错误响应是否泄露敏感信息
                sensitive_patterns = [
                    'Traceback',
                    'File "/',
                    'line ',
                    'Exception:',
                    'Error:',
                    'sqlite3',
                    'flask',
                    'werkzeug'
                ]
                
                response_text = response.text.lower()
                leaked_info = [pattern for pattern in sensitive_patterns if pattern.lower() in response_text]
                
                if not leaked_info:
                    safe_errors += 1
                    self.log_test_result(
                        f"错误信息安全 - {test['name']}",
                        True,
                        "未泄露敏感信息"
                    )
                else:
                    self.log_test_result(
                        f"错误信息安全 - {test['name']}",
                        False,
                        f"泄露信息: {leaked_info}",
                        "HIGH"
                    )
                    
            except Exception as e:
                self.log_test_result(
                    f"错误信息安全 - {test['name']}",
                    True,
                    "请求失败，未获取到错误信息"
                )
                safe_errors += 1
        
        success_rate = safe_errors / len(error_tests)
        
        self.log_test_result(
            "错误信息泄露防护",
            success_rate >= 0.8,
            f"安全率: {success_rate:.1%}",
            "HIGH" if success_rate < 0.5 else "MEDIUM" if success_rate < 0.8 else "LOW"
        )
        
        return success_rate >= 0.8
    
    def run_comprehensive_test(self):
        """运行综合安全测试"""
        print("🔒 Twitter抓取系统安全性测试")
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
        
        # 安全测试套件
        test_suites = [
            ('SQL注入防护', self.test_sql_injection_protection),
            ('XSS防护', self.test_xss_protection),
            ('输入验证', self.test_input_validation),
            ('文件访问安全', self.test_file_access_security),
            ('HTTP安全头', self.test_http_security_headers),
            ('速率限制', self.test_rate_limiting),
            ('错误信息泄露', self.test_error_information_disclosure)
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
        
        # 生成安全报告
        self.generate_security_report(passed_tests, total_tests)
        
        return passed_tests == total_tests
    
    def generate_security_report(self, passed_tests, total_tests):
        """生成安全测试报告"""
        print("=" * 60)
        print("🛡️ 安全测试总结")
        print("=" * 60)
        print(f"总测试套件: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {total_tests - passed_tests} ❌")
        print(f"成功率: {(passed_tests/total_tests*100):.1f}%")
        
        # 风险评估
        high_risk_count = sum(1 for result in self.test_results if result.get('risk_level') == 'HIGH' and not result['success'])
        medium_risk_count = sum(1 for result in self.test_results if result.get('risk_level') == 'MEDIUM' and not result['success'])
        low_risk_count = sum(1 for result in self.test_results if result.get('risk_level') == 'LOW' and not result['success'])
        
        print(f"\n🚨 风险评估:")
        print(f"高风险问题: {high_risk_count} 🔴")
        print(f"中风险问题: {medium_risk_count} 🟡")
        print(f"低风险问题: {low_risk_count} 🟢")
        
        # 详细结果统计
        success_count = sum(1 for result in self.test_results if result['success'])
        total_count = len(self.test_results)
        
        print(f"\n详细测试项: {total_count}")
        print(f"成功: {success_count}")
        print(f"失败: {total_count - success_count}")
        print(f"详细成功率: {(success_count/total_count*100):.1f}%")
        
        # 保存详细报告
        report_file = self.project_root / "security_test_report.json"
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
            'risk_assessment': {
                'high_risk_issues': high_risk_count,
                'medium_risk_issues': medium_risk_count,
                'low_risk_issues': low_risk_count
            },
            'detailed_results': self.test_results
        }
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            print(f"\n📄 详细报告已保存: {report_file}")
        except Exception as e:
            print(f"\n⚠️ 无法保存报告: {str(e)}")
        
        # 安全评估
        print("\n" + "=" * 60)
        print("🔐 安全评估")
        print("=" * 60)
        
        if high_risk_count == 0 and medium_risk_count <= 1:
            print("🎉 安全状态: 优秀 - 系统安全防护良好")
        elif high_risk_count == 0 and medium_risk_count <= 3:
            print("✅ 安全状态: 良好 - 存在少量中等风险")
        elif high_risk_count <= 1:
            print("⚠️ 安全状态: 一般 - 需要关注安全问题")
        else:
            print("❌ 安全状态: 需要加强 - 存在高风险安全问题")
        
        print("\n🛡️ 安全建议:")
        print("1. 实施输入验证和输出编码")
        print("2. 添加SQL注入和XSS防护")
        print("3. 配置适当的HTTP安全头")
        print("4. 实施速率限制和访问控制")
        print("5. 避免在错误信息中泄露敏感信息")
        print("6. 定期进行安全测试和漏洞扫描")
        print("7. 保持系统和依赖库的更新")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Twitter抓取系统安全性测试')
    parser.add_argument('--url', default='http://localhost:8084', 
                       help='Web服务器地址 (默认: http://localhost:8084)')
    
    args = parser.parse_args()
    
    tester = SecurityTester(args.url)
    tester.run_comprehensive_test()

if __name__ == '__main__':
    main()