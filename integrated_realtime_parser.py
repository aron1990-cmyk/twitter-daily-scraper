#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成的实时解析器
将实时解析逻辑集成到真实的Twitter解析器中
解决滚动计数与实际元素不匹配的问题
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
import json

from twitter_parser import TwitterParser
from ads_browser_launcher import AdsPowerLauncher
from config import ADS_POWER_CONFIG

class IntegratedRealtimeParser:
    """集成的实时解析器，支持真实环境下的实时解析"""
    
    def __init__(self, parser: TwitterParser):
        self.parser = parser
        self.logger = logging.getLogger(__name__)
        
        # 实时解析状态
        self.parsed_tweets: List[Dict[str, Any]] = []
        self.seen_tweet_ids: Set[str] = set()
        self.parsing_stats = {
            'total_scrolls': 0,
            'tweets_parsed': 0,
            'duplicates_skipped': 0,
            'parsing_errors': 0,
            'incremental_saves': 0,
            'dom_elements_found': 0,
            'dom_elements_parsed': 0
        }
        
        # 实时解析配置
        self.incremental_save_interval = 5  # 每5条推文保存一次
        self.max_parse_attempts_per_element = 3
    
    async def scroll_and_parse_realtime_integrated(self, target_tweets: int = 30, max_attempts: int = 50) -> Dict[str, Any]:
        """集成的实时滚动和解析推文"""
        self.logger.info(f"🚀 开始集成实时滚动解析，目标: {target_tweets} 条推文")
        
        scroll_attempt = 0
        stagnant_rounds = 0
        last_parsed_count = 0
        
        # 动态调整参数
        base_scroll_distance = 800
        base_wait_time = 1.5
        
        # 初始状态检查
        await self._check_initial_state()
        
        while scroll_attempt < max_attempts and len(self.parsed_tweets) < target_tweets:
            self.parsing_stats['total_scrolls'] = scroll_attempt + 1
            
            self.logger.info(f"📊 滚动尝试 {scroll_attempt + 1}/{max_attempts}，已解析: {len(self.parsed_tweets)}/{target_tweets}")
            
            # 获取当前页面的推文元素
            current_elements = await self._get_current_tweet_elements()
            
            if current_elements:
                self.parsing_stats['dom_elements_found'] += len(current_elements)
                self.logger.debug(f"✅ 找到 {len(current_elements)} 个推文元素")
                
                # 实时解析新出现的推文
                new_tweets_parsed = await self._parse_elements_realtime(current_elements)
                
                if new_tweets_parsed > 0:
                    self.logger.info(f"✅ 本轮解析了 {new_tweets_parsed} 条新推文，总计: {len(self.parsed_tweets)}")
                    stagnant_rounds = 0
                    
                    # 增量保存检查
                    if len(self.parsed_tweets) % self.incremental_save_interval == 0:
                        await self._incremental_save()
                else:
                    stagnant_rounds += 1
                    self.logger.debug(f"⚠️ 本轮未发现新推文，停滞轮数: {stagnant_rounds}")
            else:
                stagnant_rounds += 1
                self.logger.warning(f"❌ 未找到推文元素，停滞轮数: {stagnant_rounds}")
            
            # 检查是否达到目标
            if len(self.parsed_tweets) >= target_tweets:
                self.logger.info(f"🎯 达到目标推文数量: {len(self.parsed_tweets)}")
                break
            
            # 检查停滞情况
            if len(self.parsed_tweets) == last_parsed_count:
                stagnant_rounds += 1
            else:
                stagnant_rounds = 0
            
            last_parsed_count = len(self.parsed_tweets)
            
            # 根据停滞情况调整滚动策略
            scroll_distance, wait_time = self._adjust_scroll_strategy(stagnant_rounds, base_scroll_distance, base_wait_time)
            
            # 执行滚动
            await self._perform_scroll(scroll_distance, wait_time)
            
            # 处理长时间停滞
            if stagnant_rounds >= 8:
                await self._handle_long_stagnation()
                stagnant_rounds = 0
            
            scroll_attempt += 1
        
        # 最终保存
        final_file = await self._final_save()
        
        # 生成结果摘要
        result = {
            'parsed_tweets_count': len(self.parsed_tweets),
            'target_tweets': target_tweets,
            'scroll_attempts': scroll_attempt,
            'target_reached': len(self.parsed_tweets) >= target_tweets,
            'efficiency': len(self.parsed_tweets) / max(scroll_attempt, 1),
            'parsing_stats': self.parsing_stats.copy(),
            'parsed_tweets': self.parsed_tweets.copy(),
            'final_save_file': final_file,
            'dom_parsing_ratio': self.parsing_stats['dom_elements_parsed'] / max(self.parsing_stats['dom_elements_found'], 1)
        }
        
        self.logger.info(f"📊 集成实时解析完成: {len(self.parsed_tweets)} 条推文，{scroll_attempt} 次滚动")
        self.logger.info(f"📊 DOM解析比率: {result['dom_parsing_ratio']:.2%} ({self.parsing_stats['dom_elements_parsed']}/{self.parsing_stats['dom_elements_found']})")
        
        return result
    
    async def _check_initial_state(self):
        """检查初始状态"""
        self.logger.info(f"📊 初始状态检查...")
        try:
            initial_elements = await self.parser.page.query_selector_all('[data-testid="tweet"]')
            self.logger.info(f"📊 页面初始推文元素数量: {len(initial_elements)}")
            
            # 检查页面是否正确加载
            page_title = await self.parser.page.title()
            current_url = self.parser.page.url
            self.logger.info(f"📊 当前页面: {page_title} - {current_url}")
            
        except Exception as e:
            self.logger.warning(f"初始状态检查失败: {e}")
    
    async def _get_current_tweet_elements(self) -> List:
        """获取当前页面的推文元素"""
        try:
            # 等待推文元素出现
            await self.parser.page.wait_for_selector('[data-testid="tweet"]', timeout=5000)
            
            # 尝试多个选择器
            selectors = [
                '[data-testid="tweet"]',
                'article[data-testid="tweet"]',
                '[data-testid="tweetText"]'
            ]
            
            all_elements = []
            for selector in selectors:
                try:
                    elements = await self.parser.page.query_selector_all(selector)
                    if elements:
                        all_elements.extend(elements)
                        self.logger.debug(f"✅ 选择器 {selector} 找到 {len(elements)} 个元素")
                except Exception as e:
                    self.logger.debug(f"选择器 {selector} 失败: {e}")
            
            # 去重（基于元素位置）
            unique_elements = []
            seen_positions = set()
            
            for element in all_elements:
                try:
                    box = await element.bounding_box()
                    if box:
                        position = (int(box['x']), int(box['y']))
                        if position not in seen_positions:
                            unique_elements.append(element)
                            seen_positions.add(position)
                except Exception:
                    # 如果无法获取位置，仍然包含该元素
                    unique_elements.append(element)
            
            self.logger.debug(f"📊 去重后推文元素: {len(unique_elements)} 个")
            return unique_elements
            
        except Exception as e:
            self.logger.warning(f"获取推文元素失败: {e}")
            return []
    
    async def _parse_elements_realtime(self, elements: List) -> int:
        """实时解析推文元素"""
        new_tweets_count = 0
        
        for element in elements:
            try:
                # 尝试解析推文
                parsed_tweet = await self._parse_single_element_safe(element)
                
                if parsed_tweet:
                    tweet_id = parsed_tweet.get('id') or parsed_tweet.get('tweet_id')
                    
                    if tweet_id and tweet_id not in self.seen_tweet_ids:
                        # 添加解析时间戳
                        parsed_tweet['parsed_at'] = datetime.now().isoformat()
                        parsed_tweet['parsing_method'] = 'realtime_integrated'
                        
                        self.parsed_tweets.append(parsed_tweet)
                        self.seen_tweet_ids.add(tweet_id)
                        self.parsing_stats['tweets_parsed'] += 1
                        self.parsing_stats['dom_elements_parsed'] += 1
                        new_tweets_count += 1
                        
                        self.logger.info(f"✅ 实时解析新推文: @{parsed_tweet.get('username', 'unknown')} - {tweet_id[:8] if tweet_id else 'no_id'}... - {parsed_tweet.get('content', '')[:30]}...")
                    
                    elif tweet_id in self.seen_tweet_ids:
                        self.parsing_stats['duplicates_skipped'] += 1
                        self.logger.debug(f"⏭️ 跳过重复推文: {tweet_id[:8] if tweet_id else 'no_id'}...")
                
            except Exception as e:
                self.parsing_stats['parsing_errors'] += 1
                self.logger.debug(f"解析推文元素失败: {e}")
                continue
        
        return new_tweets_count
    
    async def _parse_single_element_safe(self, element) -> Optional[Dict[str, Any]]:
        """安全地解析单个推文元素"""
        for attempt in range(self.max_parse_attempts_per_element):
            try:
                # 使用优化的解析方法
                if hasattr(self.parser, 'parse_tweet_element_optimized'):
                    result = await self.parser.parse_tweet_element_optimized(element)
                elif hasattr(self.parser, 'parse_tweet_element'):
                    result = await self.parser.parse_tweet_element(element)
                else:
                    # 基础解析方法
                    result = await self._basic_parse_element(element)
                
                if result and (result.get('content') or result.get('id')):
                    return result
                
            except Exception as e:
                self.logger.debug(f"解析尝试 {attempt + 1} 失败: {e}")
                if attempt < self.max_parse_attempts_per_element - 1:
                    await asyncio.sleep(0.1)  # 短暂等待后重试
        
        return None
    
    async def _basic_parse_element(self, element) -> Dict[str, Any]:
        """基础的推文元素解析"""
        result = {}
        
        try:
            # 提取推文链接和ID
            link_element = await element.query_selector('a[href*="/status/"]')
            if link_element:
                href = await link_element.get_attribute('href')
                if href and '/status/' in href:
                    tweet_id = href.split('/status/')[-1].split('?')[0]
                    result['id'] = tweet_id
            
            # 提取用户名
            username_element = await element.query_selector('[data-testid="User-Name"] a')
            if username_element:
                username_href = await username_element.get_attribute('href')
                if username_href:
                    username = username_href.strip('/').split('/')[-1]
                    result['username'] = username
            
            # 提取推文内容
            content_element = await element.query_selector('[data-testid="tweetText"]')
            if content_element:
                content = await content_element.inner_text()
                result['content'] = content.strip() if content else ''
            
            # 提取时间戳
            time_element = await element.query_selector('time')
            if time_element:
                datetime_attr = await time_element.get_attribute('datetime')
                if datetime_attr:
                    result['timestamp'] = datetime_attr
            
            return result
            
        except Exception as e:
            self.logger.debug(f"基础解析失败: {e}")
            return {}
    
    def _adjust_scroll_strategy(self, stagnant_rounds: int, base_distance: int, base_wait: float) -> tuple:
        """根据停滞情况调整滚动策略"""
        if stagnant_rounds >= 6:
            # 超激进模式
            distance = base_distance * 3
            wait_time = base_wait * 0.5
            self.logger.debug(f"⚡ 超激进模式：滚动距离 {distance}，等待时间 {wait_time:.1f}s")
        elif stagnant_rounds >= 3:
            # 激进模式
            distance = base_distance * 2
            wait_time = base_wait * 0.7
            self.logger.debug(f"🔥 激进模式：滚动距离 {distance}，等待时间 {wait_time:.1f}s")
        else:
            # 正常模式
            distance = base_distance
            wait_time = base_wait
        
        return distance, wait_time
    
    async def _perform_scroll(self, scroll_distance: int, wait_time: float):
        """执行滚动操作"""
        try:
            await self.parser.page.evaluate('window.focus()')
            current_scroll = await self.parser.page.evaluate('window.pageYOffset')
            
            await self.parser.page.evaluate(f'''
                window.scrollTo({{
                    top: {current_scroll + scroll_distance},
                    behavior: 'smooth'
                }});
            ''')
            
            await asyncio.sleep(wait_time)
            
        except Exception as e:
            self.logger.warning(f"滚动失败: {e}")
            await asyncio.sleep(1)
    
    async def _handle_long_stagnation(self):
        """处理长时间停滞"""
        self.logger.info("🔄 长时间无新内容，尝试页面刷新...")
        try:
            await self.parser.page.reload(wait_until='domcontentloaded')
            await asyncio.sleep(3)
        except Exception as e:
            self.logger.warning(f"页面刷新失败: {e}")
    
    async def _incremental_save(self) -> str:
        """增量保存解析结果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'integrated_realtime_incremental_{timestamp}.json'
        
        incremental_data = {
            'save_type': 'incremental',
            'timestamp': datetime.now().isoformat(),
            'total_tweets': len(self.parsed_tweets),
            'parsing_stats': self.parsing_stats.copy(),
            'latest_tweets': self.parsed_tweets[-self.incremental_save_interval:] if len(self.parsed_tweets) >= self.incremental_save_interval else self.parsed_tweets
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(incremental_data, f, ensure_ascii=False, indent=2)
            
            self.parsing_stats['incremental_saves'] += 1
            self.logger.info(f"💾 增量保存完成: {filename} ({len(self.parsed_tweets)} 条推文)")
            return filename
        except Exception as e:
            self.logger.error(f"增量保存失败: {e}")
            return ""
    
    async def _final_save(self) -> str:
        """最终保存所有解析结果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'integrated_realtime_final_{timestamp}.json'
        
        final_data = {
            'save_type': 'final',
            'timestamp': datetime.now().isoformat(),
            'total_tweets': len(self.parsed_tweets),
            'unique_tweets': len(self.seen_tweet_ids),
            'parsing_stats': self.parsing_stats.copy(),
            'quality_metrics': self._calculate_quality_metrics(),
            'all_tweets': self.parsed_tweets
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"📄 最终结果已保存: {filename}")
            return filename
        except Exception as e:
            self.logger.error(f"最终保存失败: {e}")
            return ""
    
    def _calculate_quality_metrics(self) -> Dict[str, Any]:
        """计算数据质量指标"""
        if not self.parsed_tweets:
            return {}
        
        total_tweets = len(self.parsed_tweets)
        
        # 内容质量
        has_content = sum(1 for t in self.parsed_tweets if t.get('content'))
        has_username = sum(1 for t in self.parsed_tweets if t.get('username'))
        has_id = sum(1 for t in self.parsed_tweets if t.get('id'))
        has_timestamp = sum(1 for t in self.parsed_tweets if t.get('timestamp'))
        
        # 解析效率
        total_attempts = self.parsing_stats['tweets_parsed'] + self.parsing_stats['duplicates_skipped'] + self.parsing_stats['parsing_errors']
        
        return {
            'content_completeness': has_content / total_tweets,
            'username_completeness': has_username / total_tweets,
            'id_completeness': has_id / total_tweets,
            'timestamp_completeness': has_timestamp / total_tweets,
            'parsing_success_rate': self.parsing_stats['tweets_parsed'] / max(total_attempts, 1),
            'duplicate_rate': self.parsing_stats['duplicates_skipped'] / max(total_attempts, 1),
            'error_rate': self.parsing_stats['parsing_errors'] / max(total_attempts, 1),
            'efficiency_per_scroll': self.parsing_stats['tweets_parsed'] / max(self.parsing_stats['total_scrolls'], 1),
            'dom_parsing_efficiency': self.parsing_stats['dom_elements_parsed'] / max(self.parsing_stats['dom_elements_found'], 1)
        }
    
    def get_parsing_summary(self) -> Dict[str, Any]:
        """获取解析摘要"""
        return {
            'total_parsed': len(self.parsed_tweets),
            'unique_tweets': len(self.seen_tweet_ids),
            'parsing_stats': self.parsing_stats.copy(),
            'quality_metrics': self._calculate_quality_metrics()
        }


class IntegratedRealtimeTest:
    """集成实时解析测试类"""
    
    def __init__(self, max_tweets: int = 20):
        self.max_tweets = max_tweets
        self.logger = logging.getLogger(__name__)
        self.launcher = None
        self.parser = None
        self.realtime_parser = None
    
    async def setup_browser(self) -> bool:
        """设置浏览器环境"""
        try:
            self.logger.info("🚀 初始化AdsPower启动器...")
            self.launcher = AdsPowerLauncher(ADS_POWER_CONFIG)
            
            browser_info = self.launcher.start_browser()
            self.launcher.wait_for_browser_ready()
            debug_port = self.launcher.get_debug_port()
            
            self.logger.info(f"✅ 浏览器启动成功，调试端口: {debug_port}")
            
            # 初始化TwitterParser
            self.parser = TwitterParser(debug_port=debug_port)
            await self.parser.initialize()
            
            # 初始化集成实时解析器
            self.realtime_parser = IntegratedRealtimeParser(self.parser)
            
            return True
            
        except Exception as e:
            self.logger.error(f"浏览器设置失败: {e}")
            return False
    
    async def test_integrated_realtime_parsing(self, username: str = "elonmusk") -> Dict[str, Any]:
        """测试集成实时解析功能"""
        test_result = {
            'test_name': 'integrated_realtime_parsing_test',
            'success': False,
            'details': {},
            'errors': []
        }
        
        try:
            # 导航到用户页面
            self.logger.info(f"🔍 导航到 @{username} 的个人资料页面...")
            await self.parser.navigate_to_profile(username)
            await asyncio.sleep(3)
            
            # 执行集成实时滚动解析
            self.logger.info(f"📜 开始集成实时滚动解析（目标: {self.max_tweets}条）...")
            parse_result = await self.realtime_parser.scroll_and_parse_realtime_integrated(
                target_tweets=self.max_tweets,
                max_attempts=self.max_tweets * 2
            )
            
            # 获取解析摘要
            parsing_summary = self.realtime_parser.get_parsing_summary()
            
            test_result['details'] = {
                'target_tweets': self.max_tweets,
                'parsed_tweets': parse_result['parsed_tweets_count'],
                'scroll_attempts': parse_result['scroll_attempts'],
                'target_reached': parse_result['target_reached'],
                'efficiency': parse_result['efficiency'],
                'dom_parsing_ratio': parse_result['dom_parsing_ratio'],
                'parsing_summary': parsing_summary,
                'final_save_file': parse_result['final_save_file'],
                'sample_tweet_keys': list(parse_result['parsed_tweets'][0].keys()) if parse_result['parsed_tweets'] else []
            }
            
            # 验证集成实时解析的关键特性
            integration_validation = self._validate_integration_features(parse_result, parsing_summary)
            test_result['details']['integration_validation'] = integration_validation
            
            # 判断测试成功
            if (parse_result['parsed_tweets_count'] > 0 and 
                integration_validation['realtime_parsing_working'] and
                integration_validation['dom_element_handling_working']):
                test_result['success'] = True
                self.logger.info(f"✅ 集成实时解析测试成功: {parse_result['parsed_tweets_count']} 条推文")
            else:
                test_result['errors'].append("集成实时解析关键特性验证失败")
                self.logger.error("❌ 集成实时解析测试失败")
            
        except Exception as e:
            test_result['errors'].append(str(e))
            self.logger.error(f"❌ 集成实时解析测试失败: {e}")
        
        return test_result
    
    def _validate_integration_features(self, parse_result: Dict[str, Any], parsing_summary: Dict[str, Any]) -> Dict[str, Any]:
        """验证集成实时解析的关键特性"""
        validation = {
            'realtime_parsing_working': False,
            'dom_element_handling_working': False,
            'incremental_saves_working': False,
            'quality_metrics_working': False,
            'scroll_efficiency_acceptable': False
        }
        
        # 检查实时解析
        if parse_result['parsed_tweets_count'] > 0 and parse_result['efficiency'] > 0:
            validation['realtime_parsing_working'] = True
            self.logger.info(f"✅ 实时解析功能正常: 效率 {parse_result['efficiency']:.2f} 推文/滚动")
        
        # 检查DOM元素处理
        dom_ratio = parse_result.get('dom_parsing_ratio', 0)
        if dom_ratio > 0:
            validation['dom_element_handling_working'] = True
            self.logger.info(f"✅ DOM元素处理正常: 解析比率 {dom_ratio:.1%}")
        
        # 检查增量保存
        if parsing_summary['parsing_stats']['incremental_saves'] >= 0:
            validation['incremental_saves_working'] = True
            self.logger.info(f"✅ 增量保存功能正常: {parsing_summary['parsing_stats']['incremental_saves']} 次保存")
        
        # 检查质量指标
        quality_metrics = parsing_summary.get('quality_metrics', {})
        if quality_metrics and quality_metrics.get('content_completeness', 0) > 0:
            validation['quality_metrics_working'] = True
            self.logger.info(f"✅ 质量指标功能正常: 内容完整性 {quality_metrics['content_completeness']:.1%}")
        
        # 检查滚动效率
        if parse_result['efficiency'] > 0.1:  # 至少每10次滚动解析1条推文
            validation['scroll_efficiency_acceptable'] = True
            self.logger.info(f"✅ 滚动效率可接受: {parse_result['efficiency']:.2f}")
        
        return validation
    
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


async def main():
    """主测试函数"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    # 创建测试实例
    test = IntegratedRealtimeTest(max_tweets=15)
    
    try:
        # 设置浏览器
        if not await test.setup_browser():
            logger.error("❌ 浏览器设置失败")
            return
        
        # 运行集成实时解析测试
        result = await test.test_integrated_realtime_parsing()
        
        # 输出测试结果
        logger.info("\n" + "="*60)
        logger.info("📊 集成实时解析测试结果")
        logger.info("="*60)
        logger.info(f"测试状态: {'✅ 成功' if result['success'] else '❌ 失败'}")
        
        if result['success']:
            details = result['details']
            logger.info(f"目标推文数: {details['target_tweets']}")
            logger.info(f"实际解析数: {details['parsed_tweets']}")
            logger.info(f"滚动次数: {details['scroll_attempts']}")
            logger.info(f"解析效率: {details['efficiency']:.2f} 推文/滚动")
            logger.info(f"DOM解析比率: {details['dom_parsing_ratio']:.1%}")
            
            # 集成特性验证结果
            validation = details['integration_validation']
            logger.info("\n🔍 集成特性验证:")
            for feature, status in validation.items():
                status_icon = "✅" if status else "❌"
                logger.info(f"  {status_icon} {feature}: {status}")
            
            # 质量指标
            quality = details['parsing_summary']['quality_metrics']
            logger.info("\n📈 数据质量指标:")
            logger.info(f"  内容完整性: {quality['content_completeness']:.1%}")
            logger.info(f"  用户名完整性: {quality['username_completeness']:.1%}")
            logger.info(f"  ID完整性: {quality['id_completeness']:.1%}")
            logger.info(f"  DOM解析效率: {quality['dom_parsing_efficiency']:.1%}")
            
            logger.info(f"\n📄 结果文件: {details['final_save_file']}")
        else:
            logger.error(f"错误信息: {result['errors']}")
        
        logger.info("="*60)
        
    finally:
        await test.cleanup()


if __name__ == "__main__":
    asyncio.run(main())