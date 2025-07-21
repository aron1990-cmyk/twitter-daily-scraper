#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进的滚动解析器
实现实时解析、增量保存和正确的测试逻辑
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
import json

from twitter_parser import TwitterParser
from ads_browser_launcher import AdsPowerLauncher
from config import ADS_POWER_CONFIG

class ImprovedScrollParser:
    """改进的滚动解析器，支持实时解析和增量保存"""
    
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
            'parsing_errors': 0
        }
    
    async def scroll_and_parse_realtime(self, target_tweets: int = 30, max_attempts: int = 50) -> Dict[str, Any]:
        """实时滚动和解析推文"""
        self.logger.info(f"🚀 开始实时滚动解析，目标: {target_tweets} 条推文")
        
        scroll_attempt = 0
        stagnant_rounds = 0
        last_parsed_count = 0
        
        # 动态调整参数
        base_scroll_distance = 800
        base_wait_time = 1.5
        
        # 添加调试信息
        self.logger.info(f"📊 初始状态检查...")
        try:
            initial_elements = await self.parser.page.query_selector_all('[data-testid="tweet"]')
            self.logger.info(f"📊 页面初始推文元素数量: {len(initial_elements)}")
        except Exception as e:
            self.logger.warning(f"初始元素检查失败: {e}")
        
        while scroll_attempt < max_attempts and len(self.parsed_tweets) < target_tweets:
            self.parsing_stats['total_scrolls'] = scroll_attempt + 1
            
            # 获取当前页面的推文元素
            try:
                await self.parser.page.wait_for_selector('[data-testid="tweet"]', timeout=5000)
                current_elements = await self.parser.page.query_selector_all('[data-testid="tweet"]')
                self.logger.debug(f"✅ 成功找到 {len(current_elements)} 个推文元素")
            except Exception as e:
                self.logger.warning(f"查找推文元素失败: {e}")
                current_elements = []
            
            self.logger.debug(f"📊 滚动尝试 {scroll_attempt + 1}/{max_attempts}，当前DOM元素: {len(current_elements)}，已解析: {len(self.parsed_tweets)}/{target_tweets}")
            
            # 实时解析新出现的推文
            new_tweets_parsed = await self._parse_new_tweets(current_elements)
            
            if new_tweets_parsed > 0:
                self.logger.info(f"✅ 本轮解析了 {new_tweets_parsed} 条新推文，总计: {len(self.parsed_tweets)}")
                stagnant_rounds = 0
            else:
                stagnant_rounds += 1
            
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
            if stagnant_rounds >= 3:
                scroll_distance = base_scroll_distance * 2
                wait_time = base_wait_time * 0.7
                self.logger.debug(f"🔥 激进模式：滚动距离 {scroll_distance}，等待时间 {wait_time:.1f}s")
            elif stagnant_rounds >= 6:
                scroll_distance = base_scroll_distance * 3
                wait_time = base_wait_time * 0.5
                self.logger.debug(f"⚡ 超激进模式：滚动距离 {scroll_distance}，等待时间 {wait_time:.1f}s")
            else:
                scroll_distance = base_scroll_distance
                wait_time = base_wait_time
            
            # 执行滚动
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
            
            # 如果长时间无新内容，尝试刷新
            if stagnant_rounds >= 8:
                self.logger.info("🔄 长时间无新内容，尝试刷新页面")
                try:
                    await self.parser.page.reload(wait_until='domcontentloaded')
                    await asyncio.sleep(3)
                    stagnant_rounds = 0
                except Exception as e:
                    self.logger.warning(f"页面刷新失败: {e}")
            
            scroll_attempt += 1
        
        # 生成结果摘要
        result = {
            'parsed_tweets_count': len(self.parsed_tweets),
            'target_tweets': target_tweets,
            'scroll_attempts': scroll_attempt,
            'target_reached': len(self.parsed_tweets) >= target_tweets,
            'efficiency': len(self.parsed_tweets) / max(scroll_attempt, 1),
            'parsing_stats': self.parsing_stats.copy(),
            'parsed_tweets': self.parsed_tweets.copy()
        }
        
        self.logger.info(f"📊 实时解析完成: {len(self.parsed_tweets)} 条推文，{scroll_attempt} 次滚动")
        return result
    
    async def _parse_new_tweets(self, elements: List) -> int:
        """解析新出现的推文元素"""
        new_tweets_count = 0
        
        for element in elements:
            try:
                # 提取推文链接以获取ID
                link_element = await element.query_selector('a[href*="/status/"]')
                if not link_element:
                    continue
                
                href = await link_element.get_attribute('href')
                if not href:
                    continue
                
                tweet_id = self.parser.extract_tweet_id(href)
                if not tweet_id or tweet_id in self.seen_tweet_ids:
                    if tweet_id in self.seen_tweet_ids:
                        self.parsing_stats['duplicates_skipped'] += 1
                    continue
                
                # 解析推文数据
                parsed_tweet = await self._parse_tweet_element_safe(element)
                if parsed_tweet:
                    self.parsed_tweets.append(parsed_tweet)
                    self.seen_tweet_ids.add(tweet_id)
                    self.parsing_stats['tweets_parsed'] += 1
                    new_tweets_count += 1
                    
                    self.logger.debug(f"✅ 解析新推文: {parsed_tweet.get('username', 'unknown')} - {tweet_id[:8]}...")
                
            except Exception as e:
                self.parsing_stats['parsing_errors'] += 1
                self.logger.debug(f"解析推文元素失败: {e}")
                continue
        
        return new_tweets_count
    
    async def _parse_tweet_element_safe(self, element) -> Optional[Dict[str, Any]]:
        """安全地解析推文元素"""
        try:
            # 使用优化的解析方法
            if hasattr(self.parser, 'parse_tweet_element_optimized'):
                return await self.parser.parse_tweet_element_optimized(element)
            else:
                return await self.parser.parse_tweet_element(element)
        except Exception as e:
            self.logger.debug(f"推文解析失败: {e}")
            return None
    
    def save_incremental_results(self, filename: str = None) -> str:
        """增量保存解析结果"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'realtime_parsed_tweets_{timestamp}.json'
        
        result_data = {
            'timestamp': datetime.now().isoformat(),
            'total_tweets': len(self.parsed_tweets),
            'parsing_stats': self.parsing_stats,
            'tweets': self.parsed_tweets
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"📄 增量结果已保存到: {filename}")
            return filename
        except Exception as e:
            self.logger.error(f"保存结果失败: {e}")
            return ""
    
    def get_parsing_summary(self) -> Dict[str, Any]:
        """获取解析摘要"""
        return {
            'total_parsed': len(self.parsed_tweets),
            'unique_tweets': len(self.seen_tweet_ids),
            'parsing_stats': self.parsing_stats.copy(),
            'efficiency_rate': self.parsing_stats['tweets_parsed'] / max(self.parsing_stats['total_scrolls'], 1),
            'duplicate_rate': self.parsing_stats['duplicates_skipped'] / max(self.parsing_stats['tweets_parsed'] + self.parsing_stats['duplicates_skipped'], 1),
            'error_rate': self.parsing_stats['parsing_errors'] / max(self.parsing_stats['total_scrolls'], 1)
        }


class ImprovedScrollTest:
    """改进的滚动测试类"""
    
    def __init__(self, max_tweets: int = 30):
        self.max_tweets = max_tweets
        self.logger = logging.getLogger(__name__)
        self.launcher = None
        self.parser = None
        self.scroll_parser = None
    
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
            
            # 初始化改进的滚动解析器
            self.scroll_parser = ImprovedScrollParser(self.parser)
            
            return True
            
        except Exception as e:
            self.logger.error(f"浏览器设置失败: {e}")
            return False
    
    async def test_realtime_parsing(self, username: str = "elonmusk") -> Dict[str, Any]:
        """测试实时解析功能"""
        test_result = {
            'test_name': 'realtime_parsing_test',
            'success': False,
            'details': {},
            'errors': []
        }
        
        try:
            # 导航到用户页面
            self.logger.info(f"🔍 导航到 @{username} 的个人资料页面...")
            await self.parser.navigate_to_profile(username)
            await asyncio.sleep(3)
            
            # 执行实时滚动解析
            self.logger.info(f"📜 开始实时滚动解析（目标: {self.max_tweets}条）...")
            parse_result = await self.scroll_parser.scroll_and_parse_realtime(
                target_tweets=self.max_tweets,
                max_attempts=self.max_tweets * 2
            )
            
            # 保存增量结果
            saved_file = self.scroll_parser.save_incremental_results()
            
            # 获取解析摘要
            parsing_summary = self.scroll_parser.get_parsing_summary()
            
            test_result['details'] = {
                'target_tweets': self.max_tweets,
                'parsed_tweets': parse_result['parsed_tweets_count'],
                'scroll_attempts': parse_result['scroll_attempts'],
                'target_reached': parse_result['target_reached'],
                'efficiency': parse_result['efficiency'],
                'parsing_summary': parsing_summary,
                'saved_file': saved_file,
                'sample_tweet_keys': list(parse_result['parsed_tweets'][0].keys()) if parse_result['parsed_tweets'] else []
            }
            
            # 验证结果质量
            valid_tweets = [t for t in parse_result['parsed_tweets'] if t.get('content') and t.get('username')]
            test_result['details']['quality'] = {
                'valid_tweets': len(valid_tweets),
                'quality_rate': len(valid_tweets) / len(parse_result['parsed_tweets']) if parse_result['parsed_tweets'] else 0,
                'has_content': sum(1 for t in parse_result['parsed_tweets'] if t.get('content')),
                'has_username': sum(1 for t in parse_result['parsed_tweets'] if t.get('username'))
            }
            
            # 判断测试成功
            if parse_result['parsed_tweets_count'] > 0:
                test_result['success'] = True
                self.logger.info(f"✅ 实时解析测试成功: {parse_result['parsed_tweets_count']} 条推文")
            else:
                test_result['errors'].append("未解析到任何推文")
                self.logger.error("❌ 实时解析测试失败: 未解析到任何推文")
            
        except Exception as e:
            test_result['errors'].append(str(e))
            self.logger.error(f"❌ 实时解析测试失败: {e}")
        
        return test_result
    
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
    test = ImprovedScrollTest(max_tweets=30)
    
    try:
        # 设置浏览器
        if not await test.setup_browser():
            logger.error("❌ 浏览器设置失败")
            return
        
        # 运行实时解析测试
        result = await test.test_realtime_parsing()
        
        # 输出测试结果
        logger.info("\n" + "="*50)
        logger.info("📊 改进滚动解析测试结果")
        logger.info("="*50)
        logger.info(f"测试状态: {'✅ 成功' if result['success'] else '❌ 失败'}")
        
        if result['success']:
            details = result['details']
            logger.info(f"目标推文数: {details['target_tweets']}")
            logger.info(f"实际解析数: {details['parsed_tweets']}")
            logger.info(f"滚动次数: {details['scroll_attempts']}")
            logger.info(f"解析效率: {details['efficiency']:.2f} 推文/滚动")
            logger.info(f"数据质量: {details['quality']['quality_rate']:.1%}")
            logger.info(f"结果文件: {details['saved_file']}")
        else:
            logger.error(f"错误信息: {result['errors']}")
        
    finally:
        await test.cleanup()


if __name__ == "__main__":
    asyncio.run(main())