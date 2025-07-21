#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
稳定的优化测试脚本
包含错误处理和重连机制
"""

import asyncio
import logging
import sys
import os
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ads_browser_launcher import AdsPowerLauncher
from twitter_parser import TwitterParser
from tweet_filter import TweetFilter

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# AdsPower配置
ADS_POWER_CONFIG = {
    'user_id': 'k11p9ypc',
    'open_tabs': 1,
    'launch_args': [],
    'headless': False,
    'disable_password_filling': False,
    'clear_cache_after_closing': False,
    'enable_password_saving': False
}

class StableOptimizationTester:
    """稳定的优化测试器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.launcher = None
        self.parser = None
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'optimization_tests': [],
            'performance_metrics': {},
            'recommendations': []
        }
    
    async def initialize_browser(self, max_retries: int = 3) -> bool:
        """初始化浏览器，包含重试机制"""
        for attempt in range(max_retries):
            try:
                self.logger.info(f"🚀 启动浏览器 (尝试 {attempt + 1}/{max_retries})...")
                
                # 启动浏览器
                self.launcher = AdsPowerLauncher(ADS_POWER_CONFIG)
                browser_info = self.launcher.start_browser()
                self.launcher.wait_for_browser_ready()
                debug_port = self.launcher.get_debug_port()
                
                self.logger.info(f"✅ 浏览器启动成功，调试端口: {debug_port}")
                
                # 初始化TwitterParser
                self.parser = TwitterParser(debug_port=debug_port)
                await self.parser.initialize()
                
                self.logger.info("✅ TwitterParser初始化完成")
                return True
                
            except Exception as e:
                self.logger.warning(f"❌ 浏览器初始化失败 (尝试 {attempt + 1}): {e}")
                await self.cleanup_resources()
                if attempt < max_retries - 1:
                    await asyncio.sleep(5)  # 等待5秒后重试
                
        return False
    
    async def cleanup_resources(self):
        """清理资源"""
        if self.parser:
            try:
                await self.parser.close()
                self.parser = None
            except Exception as e:
                self.logger.debug(f"关闭parser时出错: {e}")
        
        if self.launcher:
            try:
                self.launcher.stop_browser()
                self.launcher = None
            except Exception as e:
                self.logger.debug(f"关闭浏览器时出错: {e}")
    
    def clean_tweet_content(self, content: str) -> str:
        """清理推文内容"""
        if not content:
            return ""
        
        # 去除多余的空白字符
        content = re.sub(r'\s+', ' ', content.strip())
        
        # 去除重复的用户名模式
        content = re.sub(r'(\w+\s+\w+)\s+\1', r'\1', content)
        
        # 去除重复的数字模式
        content = re.sub(r'(\d+[,.]?\d*[KMB]?)\s+\1(\s+\1)*', r'\1', content)
        
        # 去除重复的符号模式
        content = re.sub(r'(·\s*)+', '· ', content)
        
        # 去除末尾的统计数据模式
        content = re.sub(r'\s*·\s*[\d,KMB.\s]+$', '', content)
        
        # 去除开头的用户名重复
        content = re.sub(r'^(@?\w+\s+){2,}', '', content)
        
        # 去除多余的点和空格
        content = re.sub(r'\s*·\s*$', '', content)
        
        return content.strip()
    
    async def test_scroll_optimization(self) -> Dict[str, Any]:
        """测试滚动优化"""
        try:
            self.logger.info("🔄 开始滚动优化测试...")
            
            # 导航到测试页面
            try:
                await self.parser.navigate_to_profile('elonmusk')
            except Exception:
                await self.parser.page.goto('https://x.com/elonmusk', wait_until='domcontentloaded')
            
            await asyncio.sleep(3)
            
            # 获取初始推文数量
            initial_tweets = await self.get_tweet_count()
            
            # 执行优化滚动
            scroll_results = await self.optimized_scroll_test(target_tweets=15)
            
            # 获取最终推文数量
            final_tweets = await self.get_tweet_count()
            
            return {
                'test_name': 'scroll_optimization',
                'initial_tweets': initial_tweets,
                'final_tweets': final_tweets,
                'scroll_attempts': scroll_results.get('attempts', 0),
                'efficiency': final_tweets / max(scroll_results.get('attempts', 1), 1),
                'success': final_tweets >= 10,
                'details': scroll_results
            }
            
        except Exception as e:
            self.logger.error(f"滚动优化测试失败: {e}")
            return {
                'test_name': 'scroll_optimization',
                'success': False,
                'error': str(e)
            }
    
    async def test_content_extraction_optimization(self) -> Dict[str, Any]:
        """测试内容提取优化"""
        try:
            self.logger.info("🔍 开始内容提取优化测试...")
            
            # 获取推文元素
            tweet_elements = await self.get_tweet_elements()
            
            if not tweet_elements:
                return {
                    'test_name': 'content_extraction_optimization',
                    'success': False,
                    'error': '未找到推文元素'
                }
            
            # 测试前5条推文
            test_tweets = tweet_elements[:5]
            original_results = []
            optimized_results = []
            
            for i, element in enumerate(test_tweets):
                self.logger.info(f"测试推文 {i+1}/{len(test_tweets)}")
                
                # 原始解析
                try:
                    original_tweet = await self.parser.parse_tweet_element(element)
                    original_results.append(original_tweet)
                except Exception as e:
                    self.logger.debug(f"原始解析失败: {e}")
                    original_results.append(None)
                
                # 优化解析
                try:
                    optimized_tweet = await self.optimized_parse_tweet(element)
                    optimized_results.append(optimized_tweet)
                except Exception as e:
                    self.logger.debug(f"优化解析失败: {e}")
                    optimized_results.append(None)
            
            # 分析结果
            original_success = len([r for r in original_results if r])
            optimized_success = len([r for r in optimized_results if r])
            
            # 内容质量分析
            content_improvements = 0
            for orig, opt in zip(original_results, optimized_results):
                if orig and opt:
                    orig_content = orig.get('content', '')
                    opt_content = opt.get('content', '')
                    if len(opt_content) > 0 and opt_content != orig_content:
                        content_improvements += 1
            
            return {
                'test_name': 'content_extraction_optimization',
                'total_tested': len(test_tweets),
                'original_success': original_success,
                'optimized_success': optimized_success,
                'content_improvements': content_improvements,
                'improvement_rate': content_improvements / max(len(test_tweets), 1),
                'success': optimized_success >= original_success,
                'sample_results': {
                    'original': original_results[:2],
                    'optimized': optimized_results[:2]
                }
            }
            
        except Exception as e:
            self.logger.error(f"内容提取优化测试失败: {e}")
            return {
                'test_name': 'content_extraction_optimization',
                'success': False,
                'error': str(e)
            }
    
    async def get_tweet_count(self) -> int:
        """获取当前页面推文数量"""
        try:
            await self.parser.page.wait_for_selector('[data-testid="tweet"]', timeout=5000)
            elements = await self.parser.page.query_selector_all('[data-testid="tweet"]')
            return len(elements)
        except Exception:
            return 0
    
    async def get_tweet_elements(self):
        """获取推文元素"""
        try:
            await self.parser.page.wait_for_selector('[data-testid="tweet"]', timeout=10000)
            return await self.parser.page.query_selector_all('[data-testid="tweet"]')
        except Exception:
            return []
    
    async def optimized_scroll_test(self, target_tweets: int = 15) -> Dict[str, Any]:
        """优化的滚动测试"""
        attempts = 0
        max_attempts = 10
        last_count = 0
        stagnant_rounds = 0
        
        while attempts < max_attempts:
            current_count = await self.get_tweet_count()
            
            if current_count >= target_tweets:
                break
            
            if current_count == last_count:
                stagnant_rounds += 1
            else:
                stagnant_rounds = 0
            
            last_count = current_count
            
            # 执行滚动
            try:
                scroll_distance = 1000 if stagnant_rounds < 3 else 2000
                await self.parser.page.evaluate(f'window.scrollBy(0, {scroll_distance})')
                await asyncio.sleep(2)
                attempts += 1
            except Exception as e:
                self.logger.debug(f"滚动失败: {e}")
                break
            
            # 如果连续多轮无变化，尝试刷新
            if stagnant_rounds >= 5:
                try:
                    await self.parser.page.reload(wait_until='domcontentloaded')
                    await asyncio.sleep(3)
                    stagnant_rounds = 0
                except Exception:
                    break
        
        final_count = await self.get_tweet_count()
        
        return {
            'attempts': attempts,
            'final_count': final_count,
            'target_reached': final_count >= target_tweets,
            'efficiency': final_count / max(attempts, 1)
        }
    
    async def optimized_parse_tweet(self, element) -> Optional[Dict[str, Any]]:
        """优化的推文解析"""
        try:
            # 提取用户名
            username = 'unknown'
            try:
                username_element = await element.query_selector('[data-testid="User-Name"] [dir="ltr"]')
                if username_element:
                    username_text = await username_element.text_content()
                    username = re.sub(r'^@', '', username_text.strip().split()[0])
            except Exception:
                pass
            
            # 提取内容
            content = 'No content available'
            try:
                content_element = await element.query_selector('[data-testid="tweetText"]')
                if content_element:
                    raw_content = await content_element.text_content()
                    content = self.clean_tweet_content(raw_content)
            except Exception:
                pass
            
            # 提取链接
            link = ''
            try:
                link_element = await element.query_selector('a[href*="/status/"]')
                if link_element:
                    href = await link_element.get_attribute('href')
                    if href:
                        link = f'https://x.com{href}' if href.startswith('/') else href
            except Exception:
                pass
            
            # 提取时间
            publish_time = ''
            try:
                time_element = await element.query_selector('time')
                if time_element:
                    datetime_attr = await time_element.get_attribute('datetime')
                    if datetime_attr:
                        publish_time = datetime_attr
            except Exception:
                pass
            
            # 构建推文数据
            tweet_data = {
                'username': username,
                'content': content,
                'publish_time': publish_time,
                'link': link,
                'likes': 0,
                'comments': 0,
                'retweets': 0
            }
            
            # 验证数据有效性
            if username != 'unknown' and content != 'No content available':
                return tweet_data
            
            return None
            
        except Exception as e:
            self.logger.debug(f"优化解析失败: {e}")
            return None
    
    async def run_comprehensive_test(self) -> bool:
        """运行综合优化测试"""
        try:
            # 初始化浏览器
            if not await self.initialize_browser():
                self.logger.error("❌ 浏览器初始化失败")
                return False
            
            # 运行滚动优化测试
            scroll_test = await self.test_scroll_optimization()
            self.test_results['optimization_tests'].append(scroll_test)
            
            # 运行内容提取优化测试
            content_test = await self.test_content_extraction_optimization()
            self.test_results['optimization_tests'].append(content_test)
            
            # 计算性能指标
            self.calculate_performance_metrics()
            
            # 生成建议
            self.generate_recommendations()
            
            # 保存测试报告
            report_file = f"optimization_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"💾 优化测试报告已保存到: {report_file}")
            
            # 输出测试结果
            self.print_test_summary()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 综合优化测试失败: {e}")
            return False
        
        finally:
            await self.cleanup_resources()
    
    def calculate_performance_metrics(self):
        """计算性能指标"""
        tests = self.test_results['optimization_tests']
        
        # 滚动效率
        scroll_test = next((t for t in tests if t['test_name'] == 'scroll_optimization'), {})
        scroll_efficiency = scroll_test.get('efficiency', 0)
        
        # 内容提取改进率
        content_test = next((t for t in tests if t['test_name'] == 'content_extraction_optimization'), {})
        improvement_rate = content_test.get('improvement_rate', 0)
        
        # 总体成功率
        successful_tests = len([t for t in tests if t.get('success', False)])
        overall_success_rate = successful_tests / max(len(tests), 1)
        
        self.test_results['performance_metrics'] = {
            'scroll_efficiency': scroll_efficiency,
            'content_improvement_rate': improvement_rate,
            'overall_success_rate': overall_success_rate,
            'optimization_score': (scroll_efficiency + improvement_rate + overall_success_rate) / 3
        }
    
    def generate_recommendations(self):
        """生成优化建议"""
        metrics = self.test_results['performance_metrics']
        recommendations = []
        
        if metrics.get('scroll_efficiency', 0) < 0.8:
            recommendations.append("建议优化滚动策略，增加智能停滞检测和自适应滚动距离")
        
        if metrics.get('content_improvement_rate', 0) < 0.5:
            recommendations.append("建议改进内容提取算法，增强文本清理和去重功能")
        
        if metrics.get('overall_success_rate', 0) < 0.8:
            recommendations.append("建议增强错误处理机制，提高系统稳定性")
        
        if metrics.get('optimization_score', 0) >= 0.8:
            recommendations.append("系统优化效果良好，可考虑部署到生产环境")
        
        self.test_results['recommendations'] = recommendations
    
    def print_test_summary(self):
        """打印测试摘要"""
        self.logger.info("\n📊 优化测试结果摘要:")
        
        for test in self.test_results['optimization_tests']:
            test_name = test.get('test_name', 'Unknown')
            success = test.get('success', False)
            status = "✅ 成功" if success else "❌ 失败"
            self.logger.info(f"  {test_name}: {status}")
        
        metrics = self.test_results['performance_metrics']
        self.logger.info(f"\n📈 性能指标:")
        self.logger.info(f"  滚动效率: {metrics.get('scroll_efficiency', 0):.2f}")
        self.logger.info(f"  内容改进率: {metrics.get('content_improvement_rate', 0):.1%}")
        self.logger.info(f"  总体成功率: {metrics.get('overall_success_rate', 0):.1%}")
        self.logger.info(f"  优化分数: {metrics.get('optimization_score', 0):.2f}")
        
        self.logger.info(f"\n💡 优化建议:")
        for rec in self.test_results['recommendations']:
            self.logger.info(f"  • {rec}")

async def main():
    """主函数"""
    tester = StableOptimizationTester()
    success = await tester.run_comprehensive_test()
    
    if success:
        logger.info("\n🎊 优化测试完成！")
        return True
    else:
        logger.error("\n💥 优化测试失败")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)