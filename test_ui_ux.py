#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter抓取系统用户界面和用户体验测试脚本
测试前端界面的可用性、响应性、交互性和用户体验
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class UIUXTester:
    def __init__(self, base_url="http://localhost:8084"):
        self.base_url = base_url
        self.test_results = []
        self.project_root = Path(__file__).parent
        self.driver = None
        
    def setup_driver(self):
        """设置Selenium WebDriver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # 无头模式
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            return True
        except Exception as e:
            print(f"⚠️ 无法启动Chrome WebDriver: {str(e)}")
            print("   将使用requests进行基础测试")
            return False
    
    def teardown_driver(self):
        """关闭WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def log_test_result(self, test_name, success, details="", priority="NORMAL"):
        """记录测试结果"""
        result = {
            'test_name': test_name,
            'success': success,
            'details': details,
            'priority': priority,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        priority_emoji = {"LOW": "🟢", "NORMAL": "🔵", "HIGH": "🟡", "CRITICAL": "🔴"}.get(priority, "🔵")
        print(f"   {status} {priority_emoji} {test_name}: {details}")
    
    def test_page_accessibility(self):
        """测试页面可访问性"""
        print("🌐 测试页面可访问性...")
        
        # 主要页面列表
        pages = [
            ('/', '主页'),
            ('/config', '配置页面'),
            ('/data', '数据页面'),
            ('/tasks', '任务页面'),
            ('/api/status', 'API状态')
        ]
        
        accessible_pages = 0
        
        for path, name in pages:
            try:
                response = requests.get(urljoin(self.base_url, path), timeout=10)
                
                if response.status_code == 200:
                    accessible_pages += 1
                    self.log_test_result(
                        f"页面访问 - {name}",
                        True,
                        f"HTTP {response.status_code}"
                    )
                else:
                    self.log_test_result(
                        f"页面访问 - {name}",
                        False,
                        f"HTTP {response.status_code}",
                        "HIGH"
                    )
                    
            except Exception as e:
                self.log_test_result(
                    f"页面访问 - {name}",
                    False,
                    f"访问异常: {str(e)}",
                    "HIGH"
                )
        
        success_rate = accessible_pages / len(pages)
        
        self.log_test_result(
            "页面可访问性总体",
            success_rate >= 0.8,
            f"可访问率: {success_rate:.1%} ({accessible_pages}/{len(pages)})",
            "CRITICAL" if success_rate < 0.5 else "HIGH" if success_rate < 0.8 else "NORMAL"
        )
        
        return success_rate >= 0.8
    
    def test_page_load_performance(self):
        """测试页面加载性能"""
        print("\n⚡ 测试页面加载性能...")
        
        pages = [
            ('/', '主页'),
            ('/config', '配置页面'),
            ('/data', '数据页面')
        ]
        
        fast_pages = 0
        
        for path, name in pages:
            try:
                start_time = time.time()
                response = requests.get(urljoin(self.base_url, path), timeout=10)
                load_time = time.time() - start_time
                
                if response.status_code == 200:
                    if load_time < 2.0:  # 2秒内加载
                        fast_pages += 1
                        self.log_test_result(
                            f"页面加载速度 - {name}",
                            True,
                            f"加载时间: {load_time:.2f}秒"
                        )
                    else:
                        self.log_test_result(
                            f"页面加载速度 - {name}",
                            False,
                            f"加载时间过长: {load_time:.2f}秒",
                            "HIGH"
                        )
                else:
                    self.log_test_result(
                        f"页面加载 - {name}",
                        False,
                        f"HTTP {response.status_code}",
                        "HIGH"
                    )
                    
            except Exception as e:
                self.log_test_result(
                    f"页面加载 - {name}",
                    False,
                    f"加载异常: {str(e)}",
                    "HIGH"
                )
        
        performance_rate = fast_pages / len(pages)
        
        self.log_test_result(
            "页面加载性能总体",
            performance_rate >= 0.7,
            f"快速加载率: {performance_rate:.1%} ({fast_pages}/{len(pages)})",
            "HIGH" if performance_rate < 0.5 else "NORMAL"
        )
        
        return performance_rate >= 0.7
    
    def test_html_validity(self):
        """测试HTML有效性"""
        print("\n📝 测试HTML有效性...")
        
        pages = [
            ('/', '主页'),
            ('/config', '配置页面'),
            ('/data', '数据页面')
        ]
        
        valid_pages = 0
        
        for path, name in pages:
            try:
                response = requests.get(urljoin(self.base_url, path), timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 检查基本HTML结构
                    has_doctype = response.text.strip().startswith('<!DOCTYPE')
                    has_html_tag = soup.find('html') is not None
                    has_head_tag = soup.find('head') is not None
                    has_body_tag = soup.find('body') is not None
                    has_title_tag = soup.find('title') is not None
                    
                    structure_score = sum([
                        has_doctype, has_html_tag, has_head_tag, 
                        has_body_tag, has_title_tag
                    ])
                    
                    if structure_score >= 4:  # 至少4个基本元素
                        valid_pages += 1
                        self.log_test_result(
                            f"HTML结构 - {name}",
                            True,
                            f"结构完整性: {structure_score}/5"
                        )
                    else:
                        self.log_test_result(
                            f"HTML结构 - {name}",
                            False,
                            f"结构不完整: {structure_score}/5",
                            "HIGH"
                        )
                    
                    # 检查常见错误
                    errors = []
                    
                    # 检查是否有未闭合的标签（简单检查）
                    if response.text.count('<div') != response.text.count('</div>'):
                        errors.append("可能存在未闭合的div标签")
                    
                    # 检查是否有重复的ID
                    ids = [elem.get('id') for elem in soup.find_all(attrs={'id': True})]
                    duplicate_ids = [id for id in set(ids) if ids.count(id) > 1]
                    if duplicate_ids:
                        errors.append(f"重复ID: {duplicate_ids}")
                    
                    if errors:
                        self.log_test_result(
                            f"HTML错误检查 - {name}",
                            False,
                            f"发现错误: {'; '.join(errors)}",
                            "NORMAL"
                        )
                    else:
                        self.log_test_result(
                            f"HTML错误检查 - {name}",
                            True,
                            "未发现明显错误"
                        )
                        
            except Exception as e:
                self.log_test_result(
                    f"HTML验证 - {name}",
                    False,
                    f"验证异常: {str(e)}",
                    "HIGH"
                )
        
        validity_rate = valid_pages / len(pages)
        
        self.log_test_result(
            "HTML有效性总体",
            validity_rate >= 0.8,
            f"有效性通过率: {validity_rate:.1%} ({valid_pages}/{len(pages)})",
            "HIGH" if validity_rate < 0.6 else "NORMAL"
        )
        
        return validity_rate >= 0.8
    
    def test_responsive_design(self):
        """测试响应式设计"""
        print("\n📱 测试响应式设计...")
        
        if not self.driver:
            self.log_test_result(
                "响应式设计测试",
                False,
                "需要WebDriver支持",
                "HIGH"
            )
            return False
        
        # 不同屏幕尺寸
        screen_sizes = [
            (1920, 1080, '桌面'),
            (1024, 768, '平板'),
            (375, 667, '手机')
        ]
        
        responsive_pages = 0
        total_tests = 0
        
        for width, height, device in screen_sizes:
            try:
                self.driver.set_window_size(width, height)
                self.driver.get(self.base_url)
                
                time.sleep(2)  # 等待页面加载
                
                # 检查页面是否正确显示
                body = self.driver.find_element(By.TAG_NAME, 'body')
                
                if body.is_displayed():
                    total_tests += 1
                    
                    # 检查是否有水平滚动条（响应式设计应该避免）
                    page_width = self.driver.execute_script("return document.body.scrollWidth")
                    viewport_width = self.driver.execute_script("return window.innerWidth")
                    
                    if page_width <= viewport_width + 20:  # 允许小误差
                        responsive_pages += 1
                        self.log_test_result(
                            f"响应式设计 - {device}",
                            True,
                            f"页面宽度适配良好 ({page_width}px <= {viewport_width}px)"
                        )
                    else:
                        self.log_test_result(
                            f"响应式设计 - {device}",
                            False,
                            f"页面宽度超出视口 ({page_width}px > {viewport_width}px)",
                            "HIGH"
                        )
                        
            except Exception as e:
                total_tests += 1
                self.log_test_result(
                    f"响应式测试 - {device}",
                    False,
                    f"测试异常: {str(e)}",
                    "HIGH"
                )
        
        responsive_rate = responsive_pages / total_tests if total_tests > 0 else 0
        
        self.log_test_result(
            "响应式设计总体",
            responsive_rate >= 0.8,
            f"响应式适配率: {responsive_rate:.1%} ({responsive_pages}/{total_tests})",
            "HIGH" if responsive_rate < 0.6 else "NORMAL"
        )
        
        return responsive_rate >= 0.8
    
    def test_interactive_elements(self):
        """测试交互元素"""
        print("\n🖱️ 测试交互元素...")
        
        if not self.driver:
            self.log_test_result(
                "交互元素测试",
                False,
                "需要WebDriver支持",
                "HIGH"
            )
            return False
        
        try:
            # 测试配置页面的交互元素
            self.driver.get(urljoin(self.base_url, '/config'))
            time.sleep(3)
            
            interactive_elements = 0
            total_elements = 0
            
            # 测试按钮
            buttons = self.driver.find_elements(By.TAG_NAME, 'button')
            for button in buttons[:5]:  # 限制测试数量
                total_elements += 1
                try:
                    if button.is_enabled() and button.is_displayed():
                        interactive_elements += 1
                        self.log_test_result(
                            f"按钮交互 - {button.text[:20] if button.text else 'unnamed'}",
                            True,
                            "按钮可点击"
                        )
                    else:
                        self.log_test_result(
                            f"按钮状态 - {button.text[:20] if button.text else 'unnamed'}",
                            False,
                            "按钮不可用或不可见",
                            "NORMAL"
                        )
                except Exception as e:
                    self.log_test_result(
                        f"按钮测试异常",
                        False,
                        f"异常: {str(e)}",
                        "NORMAL"
                    )
            
            # 测试输入框
            inputs = self.driver.find_elements(By.TAG_NAME, 'input')
            for input_elem in inputs[:5]:  # 限制测试数量
                total_elements += 1
                try:
                    if input_elem.is_enabled() and input_elem.is_displayed():
                        # 尝试输入测试文本
                        input_elem.clear()
                        input_elem.send_keys("test")
                        
                        if input_elem.get_attribute('value') == 'test':
                            interactive_elements += 1
                            self.log_test_result(
                                f"输入框交互 - {input_elem.get_attribute('placeholder') or 'unnamed'}",
                                True,
                                "输入框可正常输入"
                            )
                        else:
                            self.log_test_result(
                                f"输入框功能 - {input_elem.get_attribute('placeholder') or 'unnamed'}",
                                False,
                                "输入框无法正常输入",
                                "HIGH"
                            )
                        
                        input_elem.clear()  # 清理测试数据
                    else:
                        self.log_test_result(
                            f"输入框状态 - {input_elem.get_attribute('placeholder') or 'unnamed'}",
                            False,
                            "输入框不可用或不可见",
                            "NORMAL"
                        )
                except Exception as e:
                    self.log_test_result(
                        f"输入框测试异常",
                        False,
                        f"异常: {str(e)}",
                        "NORMAL"
                    )
            
            # 测试链接
            links = self.driver.find_elements(By.TAG_NAME, 'a')
            for link in links[:3]:  # 限制测试数量
                total_elements += 1
                try:
                    href = link.get_attribute('href')
                    if href and link.is_displayed():
                        interactive_elements += 1
                        self.log_test_result(
                            f"链接 - {link.text[:20] if link.text else 'unnamed'}",
                            True,
                            f"链接有效: {href[:50]}..."
                        )
                    else:
                        self.log_test_result(
                            f"链接状态 - {link.text[:20] if link.text else 'unnamed'}",
                            False,
                            "链接无效或不可见",
                            "NORMAL"
                        )
                except Exception as e:
                    self.log_test_result(
                        f"链接测试异常",
                        False,
                        f"异常: {str(e)}",
                        "NORMAL"
                    )
            
            interaction_rate = interactive_elements / total_elements if total_elements > 0 else 0
            
            self.log_test_result(
                "交互元素总体",
                interaction_rate >= 0.7,
                f"交互可用率: {interaction_rate:.1%} ({interactive_elements}/{total_elements})",
                "HIGH" if interaction_rate < 0.5 else "NORMAL"
            )
            
            return interaction_rate >= 0.7
            
        except Exception as e:
            self.log_test_result(
                "交互元素测试",
                False,
                f"测试异常: {str(e)}",
                "HIGH"
            )
            return False
    
    def test_javascript_functionality(self):
        """测试JavaScript功能"""
        print("\n⚡ 测试JavaScript功能...")
        
        if not self.driver:
            self.log_test_result(
                "JavaScript功能测试",
                False,
                "需要WebDriver支持",
                "HIGH"
            )
            return False
        
        try:
            self.driver.get(urljoin(self.base_url, '/config'))
            time.sleep(3)
            
            js_tests = 0
            js_passed = 0
            
            # 测试基本JavaScript功能
            try:
                result = self.driver.execute_script("return typeof jQuery !== 'undefined'")
                js_tests += 1
                if result:
                    js_passed += 1
                    self.log_test_result(
                        "jQuery库加载",
                        True,
                        "jQuery已正确加载"
                    )
                else:
                    self.log_test_result(
                        "jQuery库加载",
                        False,
                        "jQuery未加载或不可用",
                        "NORMAL"
                    )
            except Exception as e:
                js_tests += 1
                self.log_test_result(
                    "jQuery测试",
                    False,
                    f"测试异常: {str(e)}",
                    "NORMAL"
                )
            
            # 测试DOM操作
            try:
                result = self.driver.execute_script("""
                    var testDiv = document.createElement('div');
                    testDiv.id = 'test-element';
                    testDiv.innerHTML = 'Test';
                    document.body.appendChild(testDiv);
                    var found = document.getElementById('test-element');
                    if (found) {
                        document.body.removeChild(found);
                        return true;
                    }
                    return false;
                """)
                
                js_tests += 1
                if result:
                    js_passed += 1
                    self.log_test_result(
                        "DOM操作",
                        True,
                        "DOM操作正常"
                    )
                else:
                    self.log_test_result(
                        "DOM操作",
                        False,
                        "DOM操作异常",
                        "HIGH"
                    )
            except Exception as e:
                js_tests += 1
                self.log_test_result(
                    "DOM操作测试",
                    False,
                    f"测试异常: {str(e)}",
                    "HIGH"
                )
            
            # 测试AJAX功能
            try:
                result = self.driver.execute_script("""
                    return typeof XMLHttpRequest !== 'undefined' || typeof fetch !== 'undefined';
                """)
                
                js_tests += 1
                if result:
                    js_passed += 1
                    self.log_test_result(
                        "AJAX支持",
                        True,
                        "AJAX功能可用"
                    )
                else:
                    self.log_test_result(
                        "AJAX支持",
                        False,
                        "AJAX功能不可用",
                        "HIGH"
                    )
            except Exception as e:
                js_tests += 1
                self.log_test_result(
                    "AJAX测试",
                    False,
                    f"测试异常: {str(e)}",
                    "HIGH"
                )
            
            # 检查JavaScript错误
            try:
                logs = self.driver.get_log('browser')
                js_errors = [log for log in logs if log['level'] == 'SEVERE']
                
                if not js_errors:
                    self.log_test_result(
                        "JavaScript错误检查",
                        True,
                        "未发现严重JavaScript错误"
                    )
                else:
                    self.log_test_result(
                        "JavaScript错误检查",
                        False,
                        f"发现 {len(js_errors)} 个严重错误",
                        "HIGH"
                    )
            except Exception as e:
                self.log_test_result(
                    "JavaScript错误检查",
                    False,
                    f"无法检查错误: {str(e)}",
                    "NORMAL"
                )
            
            js_success_rate = js_passed / js_tests if js_tests > 0 else 0
            
            self.log_test_result(
                "JavaScript功能总体",
                js_success_rate >= 0.7,
                f"功能可用率: {js_success_rate:.1%} ({js_passed}/{js_tests})",
                "HIGH" if js_success_rate < 0.5 else "NORMAL"
            )
            
            return js_success_rate >= 0.7
            
        except Exception as e:
            self.log_test_result(
                "JavaScript功能测试",
                False,
                f"测试异常: {str(e)}",
                "HIGH"
            )
            return False
    
    def test_accessibility_features(self):
        """测试可访问性特性"""
        print("\n♿ 测试可访问性特性...")
        
        pages = [
            ('/', '主页'),
            ('/config', '配置页面')
        ]
        
        accessible_features = 0
        total_checks = 0
        
        for path, name in pages:
            try:
                response = requests.get(urljoin(self.base_url, path), timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 检查alt属性
                    images = soup.find_all('img')
                    total_checks += 1
                    
                    if not images or all(img.get('alt') is not None for img in images):
                        accessible_features += 1
                        self.log_test_result(
                            f"图片alt属性 - {name}",
                            True,
                            f"所有图片都有alt属性 ({len(images)}个图片)"
                        )
                    else:
                        missing_alt = sum(1 for img in images if not img.get('alt'))
                        self.log_test_result(
                            f"图片alt属性 - {name}",
                            False,
                            f"{missing_alt}个图片缺少alt属性",
                            "NORMAL"
                        )
                    
                    # 检查表单标签
                    inputs = soup.find_all('input')
                    total_checks += 1
                    
                    if not inputs:
                        accessible_features += 1
                        self.log_test_result(
                            f"表单标签 - {name}",
                            True,
                            "页面无表单元素"
                        )
                    else:
                        labeled_inputs = 0
                        for input_elem in inputs:
                            input_id = input_elem.get('id')
                            if input_id:
                                label = soup.find('label', {'for': input_id})
                                if label:
                                    labeled_inputs += 1
                            elif input_elem.get('placeholder') or input_elem.get('aria-label'):
                                labeled_inputs += 1
                        
                        if labeled_inputs == len(inputs):
                            accessible_features += 1
                            self.log_test_result(
                                f"表单标签 - {name}",
                                True,
                                f"所有输入框都有标签 ({len(inputs)}个)"
                            )
                        else:
                            self.log_test_result(
                                f"表单标签 - {name}",
                                False,
                                f"{len(inputs) - labeled_inputs}个输入框缺少标签",
                                "NORMAL"
                            )
                    
                    # 检查标题结构
                    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                    total_checks += 1
                    
                    if headings:
                        accessible_features += 1
                        self.log_test_result(
                            f"标题结构 - {name}",
                            True,
                            f"页面有标题结构 ({len(headings)}个标题)"
                        )
                    else:
                        self.log_test_result(
                            f"标题结构 - {name}",
                            False,
                            "页面缺少标题结构",
                            "NORMAL"
                        )
                        
            except Exception as e:
                total_checks += 3  # 每个页面检查3项
                self.log_test_result(
                    f"可访问性检查 - {name}",
                    False,
                    f"检查异常: {str(e)}",
                    "HIGH"
                )
        
        accessibility_rate = accessible_features / total_checks if total_checks > 0 else 0
        
        self.log_test_result(
            "可访问性特性总体",
            accessibility_rate >= 0.7,
            f"可访问性通过率: {accessibility_rate:.1%} ({accessible_features}/{total_checks})",
            "HIGH" if accessibility_rate < 0.5 else "NORMAL"
        )
        
        return accessibility_rate >= 0.7
    
    def run_comprehensive_test(self):
        """运行综合UI/UX测试"""
        print("🎨 Twitter抓取系统UI/UX测试")
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
        
        # 设置WebDriver（可选）
        has_webdriver = self.setup_driver()
        if has_webdriver:
            print("✅ WebDriver已启动，将进行完整测试\n")
        else:
            print("⚠️ WebDriver不可用，将进行基础测试\n")
        
        # UI/UX测试套件
        test_suites = [
            ('页面可访问性', self.test_page_accessibility),
            ('页面加载性能', self.test_page_load_performance),
            ('HTML有效性', self.test_html_validity),
            ('响应式设计', self.test_responsive_design),
            ('交互元素', self.test_interactive_elements),
            ('JavaScript功能', self.test_javascript_functionality),
            ('可访问性特性', self.test_accessibility_features)
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
        
        # 清理WebDriver
        self.teardown_driver()
        
        # 生成UI/UX报告
        self.generate_ui_ux_report(passed_tests, total_tests)
        
        return passed_tests == total_tests
    
    def generate_ui_ux_report(self, passed_tests, total_tests):
        """生成UI/UX测试报告"""
        print("=" * 60)
        print("🎨 UI/UX测试总结")
        print("=" * 60)
        print(f"总测试套件: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {total_tests - passed_tests} ❌")
        print(f"成功率: {(passed_tests/total_tests*100):.1f}%")
        
        # 优先级评估
        critical_count = sum(1 for result in self.test_results if result.get('priority') == 'CRITICAL' and not result['success'])
        high_count = sum(1 for result in self.test_results if result.get('priority') == 'HIGH' and not result['success'])
        normal_count = sum(1 for result in self.test_results if result.get('priority') == 'NORMAL' and not result['success'])
        low_count = sum(1 for result in self.test_results if result.get('priority') == 'LOW' and not result['success'])
        
        print(f"\n🚨 问题优先级分析:")
        print(f"关键问题: {critical_count} 🔴")
        print(f"高优先级: {high_count} 🟡")
        print(f"普通问题: {normal_count} 🔵")
        print(f"低优先级: {low_count} 🟢")
        
        # 详细结果统计
        success_count = sum(1 for result in self.test_results if result['success'])
        total_count = len(self.test_results)
        
        print(f"\n详细测试项: {total_count}")
        print(f"成功: {success_count}")
        print(f"失败: {total_count - success_count}")
        print(f"详细成功率: {(success_count/total_count*100):.1f}%")
        
        # 保存详细报告
        report_file = self.project_root / "ui_ux_test_report.json"
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
            'priority_analysis': {
                'critical_issues': critical_count,
                'high_priority_issues': high_count,
                'normal_issues': normal_count,
                'low_priority_issues': low_count
            },
            'detailed_results': self.test_results
        }
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            print(f"\n📄 详细报告已保存: {report_file}")
        except Exception as e:
            print(f"\n⚠️ 无法保存报告: {str(e)}")
        
        # UI/UX评估
        print("\n" + "=" * 60)
        print("🎨 用户体验评估")
        print("=" * 60)
        
        if critical_count == 0 and high_count <= 1:
            print("🎉 用户体验: 优秀 - 界面友好，交互流畅")
        elif critical_count == 0 and high_count <= 3:
            print("✅ 用户体验: 良好 - 基本功能正常，有改进空间")
        elif critical_count <= 1:
            print("⚠️ 用户体验: 一般 - 存在影响使用的问题")
        else:
            print("❌ 用户体验: 需要改进 - 存在严重可用性问题")
        
        print("\n🎨 UI/UX改进建议:")
        print("1. 优化页面加载速度")
        print("2. 改善响应式设计")
        print("3. 增强交互反馈")
        print("4. 提升可访问性")
        print("5. 优化JavaScript性能")
        print("6. 改进错误处理和用户提示")
        print("7. 统一设计风格和交互模式")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Twitter抓取系统UI/UX测试')
    parser.add_argument('--url', default='http://localhost:8084', 
                       help='Web服务器地址 (默认: http://localhost:8084)')
    
    args = parser.parse_args()
    
    tester = UIUXTester(args.url)
    tester.run_comprehensive_test()

if __name__ == '__main__':
    main()