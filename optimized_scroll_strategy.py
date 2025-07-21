#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化的滚动策略
解决推文加载效率低和重复内容问题
"""

import asyncio
import logging
import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Set, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ads_browser_launcher import AdsPowerLauncher
from twitter_parser import TwitterParser
from data_extractor import DataExtractor
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

class OptimizedScrollStrategy:
    """优化的滚动策略类"""
    
    def __init__(self, parser: TwitterParser):
        self.parser = parser
        self.logger = logging.getLogger(__name__)
        self.seen_tweet_ids: Set[str] = set()
        self.scroll_metrics = {
            'total_scrolls': 0,
            'successful_loads': 0,
            'duplicate_detections': 0,
            'efficiency_score': 0.0
        }
    
    def extract_tweet_id(self, tweet_link: str) -> str:
        """从推文链接中提取ID"""
        try:
            if '/status/' in tweet_link:
                return tweet_link.split('/status/')[-1].split('?')[0]
            return ''
        except Exception:
            return ''
    
    async def get_current_tweet_elements(self):
        """获取当前页面的推文元素"""
        try:
            # 等待推文元素加载
            await self.parser.page.wait_for_selector('[data-testid="tweet"]', timeout=5000)
            return await self.parser.page.query_selector_all('[data-testid="tweet"]')
        except Exception as e:
            self.logger.warning(f"获取推文元素失败: {e}")
            return []
    
    async def check_for_new_tweets(self, previous_count: int) -> Dict[str, Any]:
        """检查是否有新推文加载"""
        current_elements = await self.get_current_tweet_elements()
        current_count = len(current_elements)
        
        new_tweets_count = max(0, current_count - previous_count)
        
        # 检查重复推文
        duplicate_count = 0
        if current_elements:
            for element in current_elements[-new_tweets_count:] if new_tweets_count > 0 else current_elements:
                try:
                    # 尝试获取推文链接来检测重复
                    link_element = await element.query_selector('a[href*="/status/"]')
                    if link_element:
                        href = await link_element.get_attribute('href')
                        if href:
                            tweet_id = self.extract_tweet_id(href)
                            if tweet_id:
                                if tweet_id in self.seen_tweet_ids:
                                    duplicate_count += 1
                                else:
                                    self.seen_tweet_ids.add(tweet_id)
                except Exception:
                    continue
        
        return {
            'current_count': current_count,
            'new_tweets': new_tweets_count,
            'duplicates': duplicate_count,
            'unique_new': max(0, new_tweets_count - duplicate_count)
        }
    
    async def smart_scroll(self, distance: int = 1000, wait_time: float = 2.0):
        """智能滚动，包含焦点检查和平滑滚动"""
        try:
            # 确保页面焦点
            await self.parser.ensure_page_focus()
            
            # 获取当前滚动位置
            current_scroll = await self.parser.page.evaluate('window.pageYOffset')
            
            # 平滑滚动
            await self.parser.page.evaluate(f'''
                window.scrollTo({{
                    top: {current_scroll + distance},
                    behavior: 'smooth'
                }});
            ''')
            
            # 等待滚动完成和内容加载
            await asyncio.sleep(wait_time)
            
            # 检查是否到达页面底部
            scroll_info = await self.parser.page.evaluate('''
                ({
                    scrollTop: window.pageYOffset,
                    scrollHeight: document.documentElement.scrollHeight,
                    clientHeight: window.innerHeight
                })
            ''')
            
            is_at_bottom = (scroll_info['scrollTop'] + scroll_info['clientHeight'] >= 
                          scroll_info['scrollHeight'] - 100)
            
            return {
                'scrolled': True,
                'at_bottom': is_at_bottom,
                'scroll_position': scroll_info['scrollTop']
            }
            
        except Exception as e:
            self.logger.warning(f"滚动失败: {e}")
            return {'scrolled': False, 'at_bottom': False, 'scroll_position': 0}
    
    async def adaptive_scroll_strategy(self, target_tweets: int = 15, max_attempts: int = 20):
        """自适应滚动策略"""
        self.logger.info(f"🚀 开始自适应滚动策略，目标: {target_tweets} 条推文")
        
        scroll_attempt = 0
        stagnant_rounds = 0
        last_unique_count = 0
        
        # 动态调整参数
        base_scroll_distance = 800
        base_wait_time = 1.5
        
        while scroll_attempt < max_attempts:
            # 获取滚动前的推文状态
            pre_scroll_info = await self.check_for_new_tweets(0)
            current_unique_tweets = len(self.seen_tweet_ids)
            
            self.logger.info(f"📊 滚动尝试 {scroll_attempt + 1}/{max_attempts}，当前唯一推文: {current_unique_tweets}/{target_tweets}")
            
            # 检查是否达到目标
            if current_unique_tweets >= target_tweets:
                self.logger.info(f"🎯 达到目标推文数量: {current_unique_tweets}")
                break
            
            # 检查停滞情况
            if current_unique_tweets == last_unique_count:
                stagnant_rounds += 1
            else:
                stagnant_rounds = 0
            
            last_unique_count = current_unique_tweets
            
            # 根据停滞情况调整策略
            if stagnant_rounds >= 3:
                # 激进模式：增加滚动距离，减少等待时间
                scroll_distance = base_scroll_distance * 2
                wait_time = base_wait_time * 0.7
                self.logger.debug(f"🔥 激进模式：滚动距离 {scroll_distance}，等待时间 {wait_time:.1f}s")
            elif stagnant_rounds >= 6:
                # 超激进模式：大幅滚动
                scroll_distance = base_scroll_distance * 3
                wait_time = base_wait_time * 0.5
                self.logger.debug(f"⚡ 超激进模式：滚动距离 {scroll_distance}，等待时间 {wait_time:.1f}s")
            else:
                # 正常模式
                scroll_distance = base_scroll_distance
                wait_time = base_wait_time
            
            # 执行滚动
            scroll_result = await self.smart_scroll(scroll_distance, wait_time)
            
            if not scroll_result['scrolled']:
                self.logger.warning("滚动失败，尝试继续")
                await asyncio.sleep(1)
            
            # 检查滚动后的效果
            post_scroll_info = await self.check_for_new_tweets(pre_scroll_info['current_count'])
            
            # 更新指标
            self.scroll_metrics['total_scrolls'] += 1
            if post_scroll_info['unique_new'] > 0:
                self.scroll_metrics['successful_loads'] += 1
            
            self.scroll_metrics['duplicate_detections'] += post_scroll_info['duplicates']
            
            self.logger.debug(f"📈 本轮效果: +{post_scroll_info['unique_new']} 唯一推文, +{post_scroll_info['duplicates']} 重复")
            
            # 如果到达页面底部且连续多轮无新内容，考虑刷新
            if scroll_result['at_bottom'] and stagnant_rounds >= 5:
                self.logger.info("🔄 到达页面底部且长时间无新内容，尝试刷新页面")
                try:
                    await self.parser.page.reload(wait_until='domcontentloaded')
                    await asyncio.sleep(3)
                    stagnant_rounds = 0
                    # 重新收集已见过的推文ID
                    await self.rebuild_seen_tweets()
                except Exception as e:
                    self.logger.warning(f"页面刷新失败: {e}")
            
            scroll_attempt += 1
        
        # 计算效率分数
        if self.scroll_metrics['total_scrolls'] > 0:
            self.scroll_metrics['efficiency_score'] = (
                self.scroll_metrics['successful_loads'] / self.scroll_metrics['total_scrolls']
            )
        
        final_unique_tweets = len(self.seen_tweet_ids)
        self.logger.info(f"📊 滚动策略完成: {final_unique_tweets} 条唯一推文，{scroll_attempt} 次滚动")
        self.logger.info(f"📈 效率指标: {self.scroll_metrics}")
        
        return {
            'final_tweet_count': final_unique_tweets,
            'scroll_attempts': scroll_attempt,
            'metrics': self.scroll_metrics
        }
    
    async def rebuild_seen_tweets(self):
        """重新构建已见推文ID集合"""
        try:
            self.seen_tweet_ids.clear()
            current_elements = await self.get_current_tweet_elements()
            
            for element in current_elements:
                try:
                    link_element = await element.query_selector('a[href*="/status/"]')
                    if link_element:
                        href = await link_element.get_attribute('href')
                        if href:
                            tweet_id = self.extract_tweet_id(href)
                            if tweet_id:
                                self.seen_tweet_ids.add(tweet_id)
                except Exception:
                    continue
            
            self.logger.debug(f"重建已见推文ID集合: {len(self.seen_tweet_ids)} 条")
        except Exception as e:
            self.logger.warning(f"重建已见推文ID失败: {e}")

async def test_optimized_scroll_strategy():
    """测试优化的滚动策略"""
    launcher = None
    parser = None
    
    try:
        # 启动浏览器
        logger.info("🚀 启动浏览器...")
        launcher = AdsPowerLauncher(ADS_POWER_CONFIG)
        browser_info = launcher.start_browser()
        launcher.wait_for_browser_ready()
        debug_port = launcher.get_debug_port()
        logger.info(f"✅ 浏览器启动成功，调试端口: {debug_port}")
        
        # 初始化TwitterParser
        logger.info("🔧 初始化TwitterParser...")
        parser = TwitterParser(debug_port=debug_port)
        await parser.initialize()
        logger.info("✅ TwitterParser初始化完成")
        
        # 导航到测试页面
        logger.info("🔄 导航到@elonmusk页面...")
        try:
            await parser.navigate_to_profile('elonmusk')
        except Exception:
            await parser.page.goto('https://x.com/elonmusk', wait_until='domcontentloaded')
        
        await asyncio.sleep(5)
        
        # 创建优化滚动策略实例
        scroll_strategy = OptimizedScrollStrategy(parser)
        
        # 执行优化滚动
        target_tweets = 20
        result = await scroll_strategy.adaptive_scroll_strategy(target_tweets, max_attempts=15)
        
        # 获取最终推文并解析
        logger.info("🔍 开始解析推文数据...")
        final_elements = await scroll_strategy.get_current_tweet_elements()
        
        parsed_tweets = []
        for i, element in enumerate(final_elements[:target_tweets]):
            try:
                tweet_data = await parser.parse_tweet_element(element)
                if tweet_data and (tweet_data.get('content') or tweet_data.get('username') != 'unknown'):
                    parsed_tweets.append(tweet_data)
                    logger.info(f"  ✅ 推文 {i+1}: @{tweet_data.get('username', 'unknown')} - {tweet_data.get('content', 'No content')[:50]}...")
            except Exception as e:
                logger.warning(f"  ❌ 推文 {i+1}: 解析失败 - {e}")
        
        # 应用过滤器
        tweet_filter = TweetFilter()
        filtered_tweets = []
        for tweet in parsed_tweets:
            try:
                if tweet_filter.should_include_tweet(tweet):
                    filtered_tweets.append(tweet)
            except Exception as e:
                logger.warning(f"过滤推文时出错: {e}")
        
        # 生成测试报告
        test_report = {
            'timestamp': datetime.now().isoformat(),
            'test_type': 'optimized_scroll_strategy',
            'target_tweets': target_tweets,
            'scroll_result': result,
            'final_elements_count': len(final_elements),
            'parsed_tweets_count': len(parsed_tweets),
            'filtered_tweets_count': len(filtered_tweets),
            'parse_success_rate': len(parsed_tweets) / max(len(final_elements), 1) * 100,
            'filter_pass_rate': len(filtered_tweets) / max(len(parsed_tweets), 1) * 100,
            'overall_efficiency': len(filtered_tweets) / max(result['scroll_attempts'], 1),
            'sample_tweets': filtered_tweets[:3]
        }
        
        # 保存测试报告
        report_file = f"optimized_scroll_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(test_report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 测试报告已保存到: {report_file}")
        
        # 输出测试结果
        logger.info("\n📊 优化滚动策略测试结果:")
        logger.info(f"  🎯 目标推文数量: {target_tweets}")
        logger.info(f"  📈 最终元素数量: {len(final_elements)}")
        logger.info(f"  ✅ 成功解析推文: {len(parsed_tweets)}")
        logger.info(f"  🎛️ 过滤后推文: {len(filtered_tweets)}")
        logger.info(f"  🔄 滚动次数: {result['scroll_attempts']}")
        logger.info(f"  📊 解析成功率: {test_report['parse_success_rate']:.1f}%")
        logger.info(f"  🎯 过滤通过率: {test_report['filter_pass_rate']:.1f}%")
        logger.info(f"  ⚡ 整体效率: {test_report['overall_efficiency']:.2f} 推文/滚动")
        
        # 与之前的结果比较
        improvement_score = test_report['overall_efficiency']
        if improvement_score >= 1.0:
            logger.info(f"🎉 优化成功！效率提升明显 (效率分数: {improvement_score:.2f})")
            return True
        elif improvement_score >= 0.6:
            logger.info(f"✅ 优化有效，系统性能良好 (效率分数: {improvement_score:.2f})")
            return True
        else:
            logger.warning(f"⚠️ 优化效果有限，需要进一步调整 (效率分数: {improvement_score:.2f})")
            return False
            
    except Exception as e:
        logger.error(f"❌ 优化滚动策略测试失败: {e}")
        return False
        
    finally:
        # 清理资源
        if parser:
            try:
                await parser.close()
                logger.info("✅ TwitterParser已关闭")
            except Exception as e:
                logger.warning(f"关闭TwitterParser时出错: {e}")
        
        if launcher:
            try:
                launcher.stop_browser()
                logger.info("✅ 浏览器已关闭")
            except Exception as e:
                logger.warning(f"关闭浏览器时出错: {e}")

if __name__ == "__main__":
    success = asyncio.run(test_optimized_scroll_strategy())
    if success:
        logger.info("\n🎊 优化滚动策略测试成功！")
    else:
        logger.error("\n💥 优化滚动策略测试失败")
        sys.exit(1)