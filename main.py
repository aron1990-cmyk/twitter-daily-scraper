#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter 日报采集系统 - 主程序入口
基于 AdsPower 虚拟浏览器的自动化 Twitter 信息采集系统
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from typing import List, Dict, Any
import threading
import signal

# 添加当前目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import (
    ADS_POWER_CONFIG, TWITTER_TARGETS, FILTER_CONFIG, 
    OUTPUT_CONFIG, BROWSER_CONFIG, LOG_CONFIG, CLOUD_SYNC_CONFIG
)
from ads_browser_launcher import AdsPowerLauncher
from twitter_parser import TwitterParser
from tweet_filter import TweetFilter
from excel_writer import ExcelWriter
from cloud_sync import CloudSyncManager
from ai_analyzer import AIContentAnalyzer as AIAnalyzer
from account_manager import AccountManager
from system_monitor import SystemMonitor
from performance_optimizer import HighSpeedCollector, EnhancedSearchOptimizer
from exception_handler import ExceptionHandler, resilient_task_execution
import json
import time

class TwitterDailyScraper:
    def __init__(self):
        # 从数据库加载AdsPower配置
        adspower_config = self._load_adspower_config_from_db()
        self.launcher = AdsPowerLauncher(adspower_config)
        self.parser = None
        self.filter_engine = TweetFilter()
        self.excel_writer = ExcelWriter()
        self.cloud_sync = CloudSyncManager(CLOUD_SYNC_CONFIG)
        self.ai_analyzer = AIAnalyzer()
        
        # 性能优化组件
        self.high_speed_collector = HighSpeedCollector()
        self.search_optimizer = EnhancedSearchOptimizer()
        
        # 加载账号配置
        accounts_config = self._load_accounts_config()
        self.account_manager = AccountManager(accounts_config)
        
        self.system_monitor = SystemMonitor()
        self.logger = self.setup_logging()
        
        # 异常处理器
        self.exception_handler = ExceptionHandler()
        
        # 运行状态
        self.is_running = False
        self.should_stop = False
        self._background_thread = None
        self._task_lock = threading.Lock()
        
        # 启动系统监控
        self.system_monitor.start_monitoring()
        
        # 注册信号处理器
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("TwitterDailyScraper 初始化完成")
    
    def _load_adspower_config_from_db(self) -> Dict[str, Any]:
        """
        从数据库加载AdsPower配置
        
        Returns:
            AdsPower配置字典
        """
        try:
            import sqlite3
            conn = sqlite3.connect('instance/twitter_scraper.db')
            cursor = conn.cursor()
            
            # 查询AdsPower相关配置
            cursor.execute("SELECT key, value FROM system_config WHERE key LIKE '%adspower%'")
            configs = cursor.fetchall()
            
            config_dict = {}
            api_host = None
            api_port = None
            
            for key, value in configs:
                if key == 'adspower_api_host':
                    api_host = value
                elif key == 'adspower_api_port':
                    api_port = value
                elif key == 'adspower_user_id':
                    config_dict['user_id'] = value
                elif key == 'adspower_group_id':
                    config_dict['group_id'] = value
                elif key == 'adspower_api_status':
                    config_dict['api_status'] = value
                elif key == 'adspower_api_key':
                    config_dict['api_key'] = value
            
            # 构建完整的API URL
            if api_host and api_port:
                config_dict['local_api_url'] = f"http://{api_host}:{api_port}"
            else:
                config_dict['local_api_url'] = 'http://local.adspower.net:50325'
            
            conn.close()
            
            # 如果没有用户ID，使用默认值
            if 'user_id' not in config_dict or not config_dict['user_id']:
                config_dict['user_id'] = 'k11p9ypc'
            
            self.logger.info(f"从数据库加载AdsPower配置: {config_dict}")
            return config_dict
            
        except Exception as e:
            self.logger.warning(f"从数据库加载AdsPower配置失败: {e}，使用默认配置")
            return {
                'local_api_url': 'http://local.adspower.net:50325',
                'user_id': 'k11p9ypc',
                'group_id': ''
            }
    
    def _load_accounts_config(self) -> List[Dict[str, Any]]:
        """
        加载账号配置文件
        
        Returns:
            账号配置列表
        """
        try:
            accounts_file = os.path.join(os.path.dirname(__file__), 'accounts', 'accounts.json')
            with open(accounts_file, 'r', encoding='utf-8') as f:
                accounts_config = json.load(f)
            return accounts_config
        except Exception as e:
            print(f"加载账号配置失败: {e}")
            # 返回默认配置
            return [{
                "user_id": "k11p9ypc",
                "name": "Default_Account",
                "priority": 1,
                "daily_limit": 50
            }]
        
    def setup_logging(self) -> logging.Logger:
        """
        设置日志配置
        
        Returns:
            配置好的日志记录器
        """
        # 创建日志记录器
        logger = logging.getLogger('TwitterScraper')
        logger.setLevel(getattr(logging, LOG_CONFIG['level']))
        
        # 避免重复添加处理器
        if logger.handlers:
            return logger
        
        # 创建格式化器
        formatter = logging.Formatter(LOG_CONFIG['format'])
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 文件处理器
        try:
            file_handler = logging.FileHandler(LOG_CONFIG['filename'], encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"无法创建日志文件: {e}")
        
        return logger
    
    async def initialize_browser(self, user_id: str = None) -> bool:
        """
        初始化浏览器环境
        
        Args:
            user_id: AdsPower 用户ID
            
        Returns:
            是否初始化成功
        """
        try:
            self.logger.info("开始初始化 AdsPower 浏览器...")
            
            # 启动 AdsPower 浏览器
            browser_info = self.launcher.start_browser(user_id)
            
            # 等待浏览器准备就绪
            if not self.launcher.wait_for_browser_ready():
                raise Exception("浏览器启动超时")
            
            # 获取调试端口
            debug_port = self.launcher.get_debug_port()
            if not debug_port:
                raise Exception("无法获取浏览器调试端口")
            
            self.logger.info(f"浏览器调试端口: {debug_port}")
            
            # 创建 Twitter 解析器并连接浏览器
            self.parser = TwitterParser(debug_port)
            await self.parser.connect_browser()
            
            # 导航到 Twitter
            await self.parser.navigate_to_twitter()
            
            self.logger.info("浏览器初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"浏览器初始化失败: {e}")
            return False
    
    async def scrape_user_tweets(self, usernames: List[str], max_tweets_per_user: int = 10) -> List[Dict[str, Any]]:
        """
        抓取指定用户的推文
        
        Args:
            usernames: 用户名列表
            max_tweets_per_user: 每个用户最大抓取推文数
            
        Returns:
            推文数据列表
        """
        all_tweets = []
        
        for username in usernames:
            try:
                self.logger.info(f"开始抓取用户 @{username} 的推文...")
                
                tweets = await self.parser.scrape_user_tweets(username, max_tweets_per_user, enable_enhanced=True)
                all_tweets.extend(tweets)
                
                self.logger.info(f"用户 @{username} 抓取完成，获得 {len(tweets)} 条推文")
                
                # 添加延迟避免被限制
                await asyncio.sleep(BROWSER_CONFIG['wait_time'])
                
            except Exception as e:
                self.logger.error(f"抓取用户 @{username} 失败: {e}")
                continue
        
        return all_tweets
    
    async def scrape_keyword_tweets(self, keywords: List[str], max_tweets_per_keyword: int = 10) -> List[Dict[str, Any]]:
        """
        抓取包含指定关键词的推文 - 增强版本
        
        Args:
            keywords: 关键词列表
            max_tweets_per_keyword: 每个关键词最大抓取推文数
            
        Returns:
            推文数据列表
        """
        all_tweets = []
        
        for keyword in keywords:
            try:
                self.logger.info(f"开始搜索关键词 '{keyword}' 的推文...")
                
                # 使用增强搜索查询
                enhanced_queries = self.search_optimizer.get_enhanced_search_queries(keyword)
                self.logger.info(f"为关键词 '{keyword}' 生成了 {len(enhanced_queries)} 个增强查询")
                
                keyword_tweets = []
                for query in enhanced_queries[:3]:  # 限制查询数量避免过度请求
                    try:
                        tweets = await self.parser.scrape_keyword_tweets(query, max_tweets_per_keyword // len(enhanced_queries[:3]), enable_enhanced=True)
                        keyword_tweets.extend(tweets)
                        
                        # 短暂延迟
                        await asyncio.sleep(0.5)
                    except Exception as e:
                        self.logger.warning(f"查询 '{query}' 失败: {e}")
                        continue
                
                # 如果增强查询没有足够结果，使用原始关键词
                if len(keyword_tweets) < max_tweets_per_keyword // 2:
                    original_tweets = await self.parser.scrape_keyword_tweets(keyword, max_tweets_per_keyword, enable_enhanced=True)
                    keyword_tweets.extend(original_tweets)
                
                all_tweets.extend(keyword_tweets)
                self.logger.info(f"关键词 '{keyword}' 搜索完成，获得 {len(keyword_tweets)} 条推文")
                
                # 添加延迟避免被限制
                await asyncio.sleep(BROWSER_CONFIG['wait_time'])
                
            except Exception as e:
                self.logger.error(f"搜索关键词 '{keyword}' 失败: {e}")
                continue
        
        return all_tweets
    
    def remove_duplicates(self, tweets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        去除重复的推文 - 使用高级去重算法
        
        Args:
            tweets: 推文数据列表
            
        Returns:
            去重后的推文列表
        """
        # 使用高级去重器
        unique_tweets = []
        for tweet in tweets:
            if not self.high_speed_collector.deduplicator.is_duplicate(tweet):
                unique_tweets.append(tweet)
        
        dedup_stats = self.high_speed_collector.deduplicator.stats
        self.logger.info(f"高级去重完成：处理 {dedup_stats['total_processed']} 条，去除 {dedup_stats['duplicates_removed']} 条重复")
        
        return unique_tweets
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        self.logger.info(f"接收到信号 {signum}，准备停止任务...")
        self.should_stop = True
    
    @resilient_task_execution()
    async def run_scraping_task(self, user_id: str = None) -> str:
        """
        执行完整的抓取任务（支持断点续传和弹性执行）
        
        Args:
            user_id: AdsPower 用户ID
            
        Returns:
            生成的 Excel 文件路径
        """
        try:
            with self._task_lock:
                self.is_running = True
            
            self.logger.info("="*50)
            self.logger.info("Twitter 日报采集任务开始")
            self.logger.info(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.logger.info("="*50)
            
            # 检查是否有断点数据
            checkpoint = self.exception_handler.checkpoint_manager.load_checkpoint("scraping_task")
            start_step = checkpoint.get('current_step', 'initialize') if checkpoint else 'initialize'
            
            # 初始化浏览器
            if start_step == 'initialize':
                if not await self.initialize_browser(user_id):
                    raise Exception("浏览器初始化失败")
                self.exception_handler.checkpoint_manager.save_checkpoint("scraping_task", {
                    'current_step': 'scrape',
                    'user_id': user_id
                })
                start_step = 'scrape'
            
            all_tweets = []
            
            # 抓取推文
            if start_step == 'scrape':
                # 抓取用户推文
                if TWITTER_TARGETS['accounts']:
                    self.logger.info(f"开始抓取 {len(TWITTER_TARGETS['accounts'])} 个用户的推文...")
                    user_tweets = await self.scrape_user_tweets(
                        TWITTER_TARGETS['accounts'], 
                        FILTER_CONFIG['max_tweets_per_target']
                    )
                    all_tweets.extend(user_tweets)
                    self.logger.info(f"用户推文抓取完成，共获得 {len(user_tweets)} 条推文")
                
                # 抓取关键词推文
                if TWITTER_TARGETS['keywords']:
                    self.logger.info(f"开始搜索 {len(TWITTER_TARGETS['keywords'])} 个关键词的推文...")
                    keyword_tweets = await self.scrape_keyword_tweets(
                        TWITTER_TARGETS['keywords'], 
                        FILTER_CONFIG['max_tweets_per_target']
                    )
                    all_tweets.extend(keyword_tweets)
                    self.logger.info(f"关键词推文搜索完成，共获得 {len(keyword_tweets)} 条推文")
                
                if not all_tweets:
                    self.logger.warning("没有抓取到任何推文数据")
                    return ''
                
                self.exception_handler.checkpoint_manager.save_checkpoint("scraping_task", {
                    'current_step': 'process',
                    'all_tweets': all_tweets
                })
                start_step = 'process'
            else:
                all_tweets = checkpoint.get('all_tweets', [])
            
            # 处理推文
            if start_step == 'process':
                # 使用高速采集器进行批量处理：去重、价值筛选、优化
                self.logger.info("开始高级处理推文：去重、价值分析、优化...")
                start_time = time.time()
                
                # 批量处理推文
                processed_tweets = self.high_speed_collector.process_tweets_batch(
                    all_tweets, 
                    enable_dedup=True, 
                    enable_value_filter=True
                )
                
                processing_time = time.time() - start_time
                self.logger.info(f"高级处理完成，耗时 {processing_time:.2f}秒")
                self.logger.info(f"处理结果：{len(processed_tweets)}/{len(all_tweets)} 条推文通过处理")
                
                # 获取性能报告
                performance_report = self.high_speed_collector.get_performance_report()
                self.logger.info(f"采集效率：{performance_report['efficiency_metrics']['collection_rate_per_minute']:.1f} 推文/分钟")
                self.logger.info(f"目标达成率：{performance_report['efficiency_metrics']['rate_achievement']:.1f}%")
                self.logger.info(f"高价值推文比例：{performance_report['efficiency_metrics']['high_value_rate']:.2%}")
                
                # 传统筛选作为补充
                self.logger.info("开始传统筛选作为补充...")
                filtered_tweets = self.filter_engine.filter_tweets(processed_tweets)
                passed_tweets = self.filter_engine.get_passed_tweets(filtered_tweets)
                
                self.logger.info(f"最终筛选完成，{len(passed_tweets)}/{len(processed_tweets)} 条推文通过所有筛选")
                
                if not passed_tweets:
                    self.logger.warning("没有推文通过筛选条件")
                    # 仍然生成文件，但只包含统计信息
                    passed_tweets = []
                
                # 生成统计信息
                statistics = self.filter_engine.get_filter_statistics(filtered_tweets)
                
                self.exception_handler.checkpoint_manager.save_checkpoint("scraping_task", {
                    'current_step': 'ai_analyze',
                    'passed_tweets': passed_tweets,
                    'statistics': statistics
                })
                start_step = 'ai_analyze'
            else:
                passed_tweets = checkpoint.get('passed_tweets', [])
                statistics = checkpoint.get('statistics', {})
            
            # AI分析
            if start_step == 'ai_analyze':
                try:
                    self.logger.info("开始AI分析...")
                    ai_insights = await self.ai_analyzer.analyze_tweets_batch(passed_tweets)
                    
                    # 添加AI分析结果到推文数据
                    for i, tweet in enumerate(passed_tweets):
                        if i < len(ai_insights):
                            tweet.update({
                                'ai_quality_score': ai_insights[i].get('quality_score', 0),
                                'ai_sentiment': ai_insights[i].get('sentiment', 'neutral'),
                                'ai_engagement_prediction': ai_insights[i].get('engagement_score', 0),
                                'ai_trend_relevance': ai_insights[i].get('trend_relevance', 0)
                            })
                    
                    self.logger.info(f"AI分析完成，处理了 {len(ai_insights)} 条推文")
                
                except Exception as e:
                    self.logger.error(f"AI分析过程中发生错误: {e}")
                
                self.exception_handler.checkpoint_manager.save_checkpoint("scraping_task", {
                    'current_step': 'export',
                    'passed_tweets': passed_tweets,
                    'statistics': statistics
                })
                start_step = 'export'
            
            # 导出到 Excel
            if start_step == 'export':
                self.logger.info("开始导出数据到 Excel...")
                output_file = self.excel_writer.write_tweets_with_summary(passed_tweets, statistics)
                
                self.exception_handler.checkpoint_manager.save_checkpoint("scraping_task", {
                    'current_step': 'sync',
                    'passed_tweets': passed_tweets,
                    'statistics': statistics,
                    'output_file': output_file
                })
                start_step = 'sync'
            else:
                output_file = checkpoint.get('output_file', '')
            
            # 云端同步
            sync_results = {}
            if start_step == 'sync':
                if any(config.get('enabled', False) for config in CLOUD_SYNC_CONFIG.values()):
                    self.logger.info("开始同步数据到云端平台...")
                    try:
                        sync_results = await self._sync_to_cloud_with_retry(passed_tweets, CLOUD_SYNC_CONFIG)
                        for platform, success in sync_results.items():
                            if success:
                                self.logger.info(f"✅ {platform} 同步成功")
                            else:
                                self.logger.warning(f"❌ {platform} 同步失败")
                    except Exception as e:
                        self.logger.error(f"云端同步过程中出现异常: {e}")
                
                self.exception_handler.checkpoint_manager.save_checkpoint("scraping_task", {
                    'current_step': 'insights',
                    'passed_tweets': passed_tweets,
                    'statistics': statistics,
                    'output_file': output_file,
                    'sync_results': sync_results
                })
                start_step = 'insights'
            else:
                sync_results = checkpoint.get('sync_results', {})
            
            # 生成AI洞察报告
            if start_step == 'insights':
                try:
                    ai_report = await self.ai_analyzer.generate_insights_report(passed_tweets)
                    report_file = f"ai_insights_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    
                    import json
                    with open(report_file, 'w', encoding='utf-8') as f:
                        json.dump(ai_report, f, ensure_ascii=False, indent=2)
                    
                    self.logger.info(f"AI洞察报告已生成: {report_file}")
                
                except Exception as e:
                    self.logger.error(f"生成AI洞察报告时发生错误: {e}")
                
                # 清除断点数据
                self.exception_handler.checkpoint_manager.delete_checkpoint("scraping_task")
            
            self.logger.info("="*50)
            self.logger.info("Twitter 日报采集任务完成")
            self.logger.info(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.logger.info(f"输出文件: {output_file}")
            self.logger.info(f"总推文数: {statistics.get('total_tweets', 0)}")
            self.logger.info(f"通过筛选: {statistics.get('passed_tweets', 0)}")
            self.logger.info(f"通过率: {statistics.get('pass_rate', 0):.2%}")
            if sync_results:
                self.logger.info(f"云端同步结果: {sync_results}")
            self.logger.info("="*50)
            
            return output_file
            
        except Exception as e:
            self.logger.error(f"抓取任务执行失败: {e}")
            await self.exception_handler.handle_exception(e, "scraping_task")
            raise e  # 让装饰器处理重试逻辑
        finally:
            with self._task_lock:
                self.is_running = False
            await self.cleanup()
    
    async def _sync_to_cloud_with_retry(self, tweets: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, bool]:
        """带重试机制的云端同步"""
        sync_results = {}
        
        try:
            sync_results = await self.cloud_sync.sync_all_platforms(tweets, config)
        except Exception as e:
            self.logger.error(f"云端同步失败，尝试重试: {e}")
            await asyncio.sleep(5)  # 等待5秒后重试
            try:
                sync_results = await self.cloud_sync.sync_all_platforms(tweets, config)
            except Exception as retry_e:
                self.logger.error(f"云端同步重试失败: {retry_e}")
                # 返回失败状态但不中断程序
                sync_results = {platform: False for platform in config.keys()}
        
        return sync_results
    
    async def cleanup(self):
        """
        清理资源
        """
        try:
            # 关闭浏览器解析器
            if self.parser:
                await self.parser.close()
            
            # 停止 AdsPower 浏览器
            self.launcher.stop_browser()
            
            # 停止系统监控
            if self.system_monitor:
                self.system_monitor.stop_monitoring()
                self.logger.info("系统监控已停止")
            
            # 保存账户管理器状态
            if self.account_manager:
                self.account_manager.save_accounts()
                self.logger.info("账户状态已保存")
            
            self.logger.info("资源清理完成")
            
        except Exception as e:
            self.logger.error(f"资源清理失败: {e}")
    
    def validate_config(self) -> bool:
        """
        验证配置文件
        
        Returns:
            配置是否有效
        """
        errors = []
        
        # 检查 AdsPower 配置
        if not ADS_POWER_CONFIG.get('user_id'):
            errors.append("AdsPower 用户ID未配置")
        
        # 检查目标配置
        if not TWITTER_TARGETS['accounts'] and not TWITTER_TARGETS['keywords']:
            errors.append("未配置任何抓取目标（用户或关键词）")
        
        # 检查筛选配置
        if (FILTER_CONFIG['min_likes'] <= 0 and 
            FILTER_CONFIG['min_comments'] <= 0 and 
            FILTER_CONFIG['min_retweets'] <= 0 and 
            not FILTER_CONFIG['keywords_filter']):
            errors.append("筛选条件配置无效")
        
        if errors:
            for error in errors:
                self.logger.error(f"配置错误: {error}")
            return False
        
        return True

async def main():
    """
    主函数
    """
    scraper = TwitterDailyScraper()
    
    try:
        # 验证配置
        if not scraper.validate_config():
            return
        
        # 执行抓取任务
        output_file = await scraper.run_scraping_task()
            
    except KeyboardInterrupt:
        scraper.logger.info("任务被用户中断")
    except Exception as e:
        scraper.logger.error(f"任务执行失败: {e}")
    finally:
        await scraper.cleanup()

if __name__ == "__main__":
    # 检查 Python 版本
    if sys.version_info < (3, 7):
        sys.exit(1)
    
    # 运行主程序
    try:
        asyncio.run(main())
    except Exception as e:
        sys.exit(1)