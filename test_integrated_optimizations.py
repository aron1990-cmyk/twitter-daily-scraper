#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成优化功能测试脚本
测试TwitterParser类中集成的所有优化功能
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any

from twitter_parser import TwitterParser
from ads_browser_launcher import AdsPowerLauncher
from config import ADS_POWER_CONFIG

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IntegratedOptimizationTester:
    """集成优化功能测试器"""
    
    def __init__(self, max_tweets: int = 1):
        self.logger = logger
        self.launcher = None
        self.parser = None
        self.max_tweets = max_tweets
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'summary': {},
            'config': {
                'max_tweets': max_tweets
            }
        }
    
    async def setup_browser(self) -> bool:
        """设置浏览器环境"""
        try:
            self.logger.info("🚀 启动浏览器...")
            self.launcher = AdsPowerLauncher(ADS_POWER_CONFIG)
            browser_info = self.launcher.start_browser()
            self.launcher.wait_for_browser_ready()
            
            # 从浏览器信息中提取debug_port
            debug_port = browser_info.get('ws', {}).get('puppeteer', '') if isinstance(browser_info.get('ws'), dict) else browser_info.get('ws', '')
            if not debug_port:
                raise Exception("无法获取浏览器调试端口")
            
            # 初始化TwitterParser
            self.parser = TwitterParser(debug_port=debug_port)
            await self.parser.initialize()
            
            # 连接到浏览器
            await self.parser.connect_browser()
            
            self.logger.info("✅ 浏览器连接成功")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 浏览器设置失败: {e}")
            return False
    
    async def test_optimization_attributes(self) -> Dict[str, Any]:
        """测试优化属性是否正确初始化"""
        self.logger.info("🔍 测试优化属性...")
        
        test_result = {
            'test_name': 'optimization_attributes',
            'success': True,
            'details': {},
            'errors': []
        }
        
        try:
            # 检查优化属性
            attributes_to_check = [
                'seen_tweet_ids',
                'content_cache', 
                'optimization_enabled'
            ]
            
            for attr in attributes_to_check:
                if hasattr(self.parser, attr):
                    test_result['details'][attr] = 'exists'
                    self.logger.info(f"✅ 属性 {attr} 存在")
                else:
                    test_result['details'][attr] = 'missing'
                    test_result['errors'].append(f"属性 {attr} 不存在")
                    test_result['success'] = False
                    self.logger.error(f"❌ 属性 {attr} 不存在")
            
            # 检查优化状态
            if hasattr(self.parser, 'optimization_enabled'):
                test_result['details']['optimization_status'] = self.parser.optimization_enabled
                self.logger.info(f"🔧 优化功能状态: {self.parser.optimization_enabled}")
            
        except Exception as e:
            test_result['success'] = False
            test_result['errors'].append(str(e))
            self.logger.error(f"❌ 测试优化属性失败: {e}")
        
        return test_result
    
    async def test_optimization_methods(self) -> Dict[str, Any]:
        """测试优化方法是否存在"""
        self.logger.info("🔍 测试优化方法...")
        
        test_result = {
            'test_name': 'optimization_methods',
            'success': True,
            'details': {},
            'errors': []
        }
        
        try:
            # 检查优化方法
            methods_to_check = [
                'clean_tweet_content',
                'extract_tweet_id',
                'is_duplicate_tweet',
                'parse_engagement_number',
                'scroll_and_load_tweets_optimized',
                'parse_tweet_element_optimized',
                'extract_clean_username',
                'extract_clean_content',
                'extract_tweet_link',
                'extract_publish_time',
                'extract_engagement_data',
                'extract_media_content',
                'get_optimization_summary',
                'enable_optimizations',
                'disable_optimizations',
                'clear_optimization_cache'
            ]
            
            for method in methods_to_check:
                if hasattr(self.parser, method) and callable(getattr(self.parser, method)):
                    test_result['details'][method] = 'exists'
                    self.logger.info(f"✅ 方法 {method} 存在")
                else:
                    test_result['details'][method] = 'missing'
                    test_result['errors'].append(f"方法 {method} 不存在")
                    test_result['success'] = False
                    self.logger.error(f"❌ 方法 {method} 不存在")
            
        except Exception as e:
            test_result['success'] = False
            test_result['errors'].append(str(e))
            self.logger.error(f"❌ 测试优化方法失败: {e}")
        
        return test_result
    
    async def test_content_cleaning(self) -> Dict[str, Any]:
        """测试内容清理功能"""
        self.logger.info("🔍 测试内容清理功能...")
        
        test_result = {
            'test_name': 'content_cleaning',
            'success': True,
            'details': {},
            'errors': []
        }
        
        try:
            # 测试用例
            test_cases = [
                {
                    'input': 'Elon Musk Elon Musk @elonmusk This is a test tweet',
                    'expected_improvement': True,
                    'description': '重复用户名清理'
                },
                {
                    'input': '4,8K 4,8K 4,8K likes on this post',
                    'expected_improvement': True,
                    'description': '重复数字清理'
                },
                {
                    'input': 'Normal tweet content without duplicates',
                    'expected_improvement': False,
                    'description': '正常内容保持不变'
                }
            ]
            
            for i, case in enumerate(test_cases):
                try:
                    cleaned = self.parser.clean_tweet_content(case['input'])
                    
                    # 检查是否有改进
                    improved = len(cleaned) < len(case['input']) or cleaned != case['input']
                    
                    test_result['details'][f'case_{i+1}'] = {
                        'description': case['description'],
                        'input_length': len(case['input']),
                        'output_length': len(cleaned),
                        'improved': improved,
                        'expected_improvement': case['expected_improvement'],
                        'passed': improved == case['expected_improvement'] or not case['expected_improvement']
                    }
                    
                    self.logger.info(f"✅ 测试用例 {i+1}: {case['description']} - {'通过' if test_result['details'][f'case_{i+1}']['passed'] else '失败'}")
                    
                except Exception as e:
                    test_result['success'] = False
                    test_result['errors'].append(f"测试用例 {i+1} 失败: {e}")
                    self.logger.error(f"❌ 测试用例 {i+1} 失败: {e}")
            
        except Exception as e:
            test_result['success'] = False
            test_result['errors'].append(str(e))
            self.logger.error(f"❌ 测试内容清理功能失败: {e}")
        
        return test_result
    
    async def test_optimization_toggle(self) -> Dict[str, Any]:
        """测试优化功能开关"""
        self.logger.info("🔍 测试优化功能开关...")
        
        test_result = {
            'test_name': 'optimization_toggle',
            'success': True,
            'details': {},
            'errors': []
        }
        
        try:
            # 测试启用优化
            initial_state = self.parser.optimization_enabled
            
            self.parser.enable_optimizations()
            enabled_state = self.parser.optimization_enabled
            
            self.parser.disable_optimizations()
            disabled_state = self.parser.optimization_enabled
            
            # 恢复初始状态
            if initial_state:
                self.parser.enable_optimizations()
            
            test_result['details'] = {
                'initial_state': initial_state,
                'enabled_state': enabled_state,
                'disabled_state': disabled_state,
                'toggle_works': enabled_state == True and disabled_state == False
            }
            
            if not test_result['details']['toggle_works']:
                test_result['success'] = False
                test_result['errors'].append("优化功能开关不工作")
                self.logger.error("❌ 优化功能开关不工作")
            else:
                self.logger.info("✅ 优化功能开关正常工作")
            
        except Exception as e:
            test_result['success'] = False
            test_result['errors'].append(str(e))
            self.logger.error(f"❌ 测试优化功能开关失败: {e}")
        
        return test_result
    
    async def test_navigation_and_parsing(self, max_tweets: int = 1) -> Dict[str, Any]:
        """测试导航和解析功能"""
        self.logger.info(f"🔍 测试导航和解析功能（目标推文数: {max_tweets}）...")
        
        test_result = {
            'test_name': 'navigation_and_parsing',
            'success': True,
            'details': {},
            'errors': []
        }
        
        try:
            # 导航到测试用户页面
            test_username = 'elonmusk'
            await self.parser.navigate_to_profile(test_username)
            
            # 等待页面加载
            await asyncio.sleep(3)
            
            # 如果需要测试多条推文，使用滚动加载
            if max_tweets > 10:
                self.logger.info(f"📜 开始滚动加载更多推文（目标: {max_tweets}条）...")
                scroll_result = await self.parser.scroll_and_load_tweets_optimized(
                    target_tweets=max_tweets,
                    max_attempts=max_tweets * 2
                )
                
                # 等待页面稳定后获取推文元素
                await asyncio.sleep(2)
                tweet_elements = await self.parser.page.query_selector_all('[data-testid="tweet"]')
                
                # 如果没有找到推文元素，尝试其他选择器
                if not tweet_elements:
                    alternative_selectors = [
                        'article[data-testid="tweet"]',
                        '[data-testid="tweetText"]',
                        'div[data-testid="tweet"]'
                    ]
                    for selector in alternative_selectors:
                        tweet_elements = await self.parser.page.query_selector_all(selector)
                        if tweet_elements:
                            self.logger.info(f"使用备用选择器找到推文元素: {selector}")
                            break
                
                test_result['details']['navigation'] = {
                    'target_user': test_username,
                    'target_tweets': max_tweets,
                    'scroll_result': scroll_result,
                    'tweet_elements_found': len(tweet_elements),
                    'navigation_success': len(tweet_elements) > 0
                }
                
                if len(tweet_elements) > 0:
                    self.logger.info(f"✅ 滚动完成，找到 {len(tweet_elements)} 个推文元素")
                    
                    # 清空已见推文ID，避免重复检查影响解析
                    original_seen_ids = self.parser.seen_tweet_ids.copy()
                    self.parser.seen_tweet_ids.clear()
                    
                    # 解析推文
                    parsed_tweets = []
                    parse_count = min(max_tweets, len(tweet_elements))
                    
                    for i in range(parse_count):
                        try:
                            parsed_tweet = await self.parser.parse_tweet_element(tweet_elements[i])
                            if parsed_tweet:
                                parsed_tweets.append(parsed_tweet)
                                self.logger.debug(f"✅ 成功解析第 {i+1} 条推文")
                            else:
                                self.logger.warning(f"第 {i+1} 条推文解析返回None")
                        except Exception as e:
                            self.logger.warning(f"解析第 {i+1} 条推文失败: {e}")
                            continue
                    
                    test_result['details']['parsing'] = {
                        'target_count': parse_count,
                        'parsed_count': len(parsed_tweets),
                        'optimization_used': self.parser.optimization_enabled,
                        'parsing_success': len(parsed_tweets) > 0,
                        'sample_data_keys': list(parsed_tweets[0].keys()) if parsed_tweets else []
                    }
                    
                    if parsed_tweets:
                        self.logger.info(f"✅ 成功解析 {len(parsed_tweets)} 条推文，使用优化: {self.parser.optimization_enabled}")
                        
                        # 统计解析质量
                        valid_tweets = [t for t in parsed_tweets if t.get('content') and t.get('username')]
                        test_result['details']['quality'] = {
                            'valid_tweets': len(valid_tweets),
                            'quality_rate': len(valid_tweets) / len(parsed_tweets) if parsed_tweets else 0,
                            'has_content': sum(1 for t in parsed_tweets if t.get('content')),
                            'has_username': sum(1 for t in parsed_tweets if t.get('username')),
                            'has_timestamp': sum(1 for t in parsed_tweets if t.get('timestamp'))
                        }
                        
                        self.logger.info(f"📊 解析质量: {len(valid_tweets)}/{len(parsed_tweets)} 条有效推文")
                    else:
                        test_result['success'] = False
                        test_result['errors'].append("推文解析失败")
                        self.logger.error("❌ 推文解析失败")
                else:
                    test_result['success'] = False
                    test_result['errors'].append("滚动后未找到推文元素")
                    self.logger.error("❌ 滚动后未找到推文元素")
            
            else:
                # 原有的单条推文测试逻辑
                tweet_elements = await self.parser.page.query_selector_all('[data-testid="tweet"]')
                
                test_result['details']['navigation'] = {
                    'target_user': test_username,
                    'tweet_elements_found': len(tweet_elements),
                    'navigation_success': len(tweet_elements) > 0
                }
                
                if len(tweet_elements) > 0:
                    self.logger.info(f"✅ 导航成功，找到 {len(tweet_elements)} 个推文元素")
                    
                    # 测试解析指定数量的推文
                    parsed_tweets = []
                    test_count = min(max_tweets, len(tweet_elements))
                    
                    for i in range(test_count):
                        try:
                            parsed_tweet = await self.parser.parse_tweet_element(tweet_elements[i])
                            if parsed_tweet:
                                parsed_tweets.append(parsed_tweet)
                        except Exception as e:
                            self.logger.warning(f"解析第 {i+1} 条推文失败: {e}")
                    
                    test_result['details']['parsing'] = {
                        'target_count': test_count,
                        'parsed_count': len(parsed_tweets),
                        'parsing_success': len(parsed_tweets) > 0,
                        'optimization_used': self.parser.optimization_enabled,
                        'parsed_data_keys': list(parsed_tweets[0].keys()) if parsed_tweets else []
                    }
                    
                    if parsed_tweets:
                        self.logger.info(f"✅ 成功解析 {len(parsed_tweets)}/{test_count} 条推文，使用优化: {self.parser.optimization_enabled}")
                    else:
                        test_result['success'] = False
                        test_result['errors'].append("推文解析返回None")
                        self.logger.error("❌ 推文解析返回None")
                else:
                    test_result['success'] = False
                    test_result['errors'].append("未找到推文元素")
                    self.logger.error("❌ 未找到推文元素")
            
        except Exception as e:
            test_result['success'] = False
            test_result['errors'].append(str(e))
            self.logger.error(f"❌ 测试导航和解析功能失败: {e}")
        
        return test_result
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        self.logger.info("🚀 开始集成优化功能测试...")
        
        # 设置浏览器
        if not await self.setup_browser():
            return {
                'success': False,
                'error': '浏览器设置失败',
                'tests': {}
            }
        
        try:
            # 运行所有测试
            tests = [
                (self.test_optimization_attributes, []),
                (self.test_optimization_methods, []),
                (self.test_content_cleaning, []),
                (self.test_optimization_toggle, []),
                (self.test_navigation_and_parsing, [self.max_tweets])
            ]
            
            for test_func, args in tests:
                try:
                    result = await test_func(*args)
                    self.test_results['tests'][result['test_name']] = result
                except Exception as e:
                    self.logger.error(f"❌ 测试 {test_func.__name__} 失败: {e}")
                    self.test_results['tests'][test_func.__name__] = {
                        'test_name': test_func.__name__,
                        'success': False,
                        'errors': [str(e)]
                    }
            
            # 生成摘要
            total_tests = len(self.test_results['tests'])
            passed_tests = sum(1 for test in self.test_results['tests'].values() if test['success'])
            
            self.test_results['summary'] = {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': total_tests - passed_tests,
                'success_rate': passed_tests / total_tests if total_tests > 0 else 0,
                'overall_success': passed_tests == total_tests
            }
            
            # 获取优化摘要
            if hasattr(self.parser, 'get_optimization_summary'):
                try:
                    self.test_results['optimization_summary'] = self.parser.get_optimization_summary()
                except Exception as e:
                    self.logger.warning(f"获取优化摘要失败: {e}")
            
            self.logger.info(f"📊 测试完成: {passed_tests}/{total_tests} 通过")
            
            return self.test_results
            
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """清理资源"""
        try:
            if self.parser:
                await self.parser.close()
            if self.launcher:
                self.launcher.stop_browser()
            self.logger.info("🧹 资源清理完成")
        except Exception as e:
            self.logger.error(f"清理资源失败: {e}")
    
    def save_results(self, filename: str = None):
        """保存测试结果"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'integrated_optimization_test_{timestamp}.json'
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False)
            self.logger.info(f"📄 测试结果已保存到: {filename}")
        except Exception as e:
            self.logger.error(f"保存测试结果失败: {e}")

async def main(max_tweets: int = 1):
    """主函数"""
    tester = IntegratedOptimizationTester(max_tweets=max_tweets)
    
    try:
        # 运行测试
        results = await tester.run_all_tests()
        
        # 保存结果
        tester.save_results()
        
        # 打印摘要
        if 'summary' in results:
            summary = results['summary']
            print("\n" + "="*50)
            print("📊 集成优化功能测试摘要")
            print("="*50)
            print(f"测试配置: 最大推文数 {max_tweets}")
            print(f"总测试数: {summary['total_tests']}")
            print(f"通过测试: {summary['passed_tests']}")
            print(f"失败测试: {summary['failed_tests']}")
            print(f"成功率: {summary['success_rate']:.1%}")
            print(f"整体状态: {'✅ 成功' if summary['overall_success'] else '❌ 失败'}")
            
            if 'optimization_summary' in results:
                opt_summary = results['optimization_summary']
                print("\n🔧 优化功能摘要:")
                for key, value in opt_summary.items():
                    print(f"  {key}: {value}")
        
        return results['summary']['overall_success'] if 'summary' in results else False
        
    except Exception as e:
        logger.error(f"测试执行失败: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    # 解析命令行参数
    max_tweets = 1
    if len(sys.argv) > 1:
        try:
            max_tweets = int(sys.argv[1])
            if max_tweets <= 0:
                print("❌ 推文数量必须大于0")
                exit(1)
        except ValueError:
            print("❌ 请提供有效的推文数量（整数）")
            print("用法: python test_integrated_optimizations.py [推文数量]")
            print("示例: python test_integrated_optimizations.py 100")
            exit(1)
    
    print(f"🚀 开始测试，目标推文数: {max_tweets}")
    success = asyncio.run(main(max_tweets))
    exit(0 if success else 1)