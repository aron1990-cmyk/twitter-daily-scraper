# -*- coding: utf-8 -*-
"""
多窗口并行抓取器
实现多个AdsPower浏览器窗口同时运行，实时显示操作过程
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import threading

from ads_browser_launcher import AdsPowerLauncher
from twitter_parser import TwitterParser
from config import (
    ADS_POWER_CONFIG, TWITTER_TARGETS, FILTER_CONFIG, 
    BROWSER_CONFIG, OUTPUT_CONFIG
)
from tweet_filter import TweetFilter
from excel_writer import ExcelWriter

class WindowManager:
    """
    单个窗口管理器
    """
    def __init__(self, window_id: int, user_id: str, target_accounts: List[str], target_keywords: List[str]):
        self.window_id = window_id
        self.user_id = user_id
        self.target_accounts = target_accounts
        self.target_keywords = target_keywords
        self.launcher = AdsPowerLauncher()
        self.parser = None
        self.logger = logging.getLogger(f"Window-{window_id}")
        self.status = "初始化"
        self.collected_tweets = []
        self.current_task = ""
        
    async def initialize(self) -> bool:
        """
        初始化窗口和浏览器
        """
        try:
            self.status = "启动浏览器"
            self.logger.info(f"🚀 窗口 {self.window_id} 开始启动浏览器...")
            
            # 启动AdsPower浏览器
            browser_info = self.launcher.start_browser(self.user_id)
            if not browser_info:
                raise Exception("浏览器启动失败")
            
            # 获取调试端口
            debug_port = browser_info.get('ws', {}).get('puppeteer', '')
            if not debug_port:
                raise Exception("无法获取浏览器调试端口")
            
            self.status = "连接解析器"
            self.logger.info(f"🔗 窗口 {self.window_id} 连接到调试端口: {debug_port}")
            
            # 初始化Twitter解析器
            self.parser = TwitterParser(debug_port)
            await self.parser.connect_browser()
            
            self.status = "就绪"
            self.logger.info(f"✅ 窗口 {self.window_id} 初始化完成")
            return True
            
        except Exception as e:
            self.status = f"错误: {e}"
            self.logger.error(f"❌ 窗口 {self.window_id} 初始化失败: {e}")
            return False
    
    async def scrape_accounts(self) -> List[Dict[str, Any]]:
        """
        抓取指定账号的推文
        """
        tweets = []
        
        for account in self.target_accounts:
            try:
                self.current_task = f"抓取 @{account}"
                self.status = f"抓取 @{account}"
                self.logger.info(f"📱 窗口 {self.window_id} 开始抓取 @{account}")
                
                # 抓取用户推文
                user_tweets = await self.parser.scrape_user_tweets(
                    account, 
                    FILTER_CONFIG['max_tweets_per_target'],
                    enable_enhanced=True
                )
                
                tweets.extend(user_tweets)
                self.collected_tweets.extend(user_tweets)
                
                self.logger.info(f"📊 窗口 {self.window_id} 从 @{account} 获得 {len(user_tweets)} 条推文")
                
                # 添加延迟
                await asyncio.sleep(BROWSER_CONFIG['wait_time'])
                
            except Exception as e:
                self.logger.error(f"❌ 窗口 {self.window_id} 抓取 @{account} 失败: {e}")
                continue
        
        return tweets
    
    async def scrape_keywords(self) -> List[Dict[str, Any]]:
        """
        抓取关键词推文
        """
        tweets = []
        
        for keyword in self.target_keywords:
            try:
                self.current_task = f"搜索 '{keyword}'"
                self.status = f"搜索 '{keyword}'"
                self.logger.info(f"🔍 窗口 {self.window_id} 开始搜索关键词 '{keyword}'")
                
                # 搜索关键词推文
                keyword_tweets = await self.parser.scrape_keyword_tweets(
                    keyword, 
                    FILTER_CONFIG['max_tweets_per_target'],
                    enable_enhanced=True
                )
                
                tweets.extend(keyword_tweets)
                self.collected_tweets.extend(keyword_tweets)
                
                self.logger.info(f"📊 窗口 {self.window_id} 关键词 '{keyword}' 获得 {len(keyword_tweets)} 条推文")
                
                # 添加延迟
                await asyncio.sleep(BROWSER_CONFIG['wait_time'])
                
            except Exception as e:
                self.logger.error(f"❌ 窗口 {self.window_id} 搜索 '{keyword}' 失败: {e}")
                continue
        
        return tweets
    
    async def run_scraping_task(self) -> List[Dict[str, Any]]:
        """
        执行完整的抓取任务
        """
        all_tweets = []
        
        try:
            # 抓取账号推文
            if self.target_accounts:
                account_tweets = await self.scrape_accounts()
                all_tweets.extend(account_tweets)
            
            # 抓取关键词推文
            if self.target_keywords:
                keyword_tweets = await self.scrape_keywords()
                all_tweets.extend(keyword_tweets)
            
            self.status = "完成"
            self.current_task = "任务完成"
            self.logger.info(f"🎉 窗口 {self.window_id} 抓取任务完成，共获得 {len(all_tweets)} 条推文")
            
        except Exception as e:
            self.status = f"错误: {e}"
            self.logger.error(f"❌ 窗口 {self.window_id} 抓取任务失败: {e}")
        
        return all_tweets
    
    async def cleanup(self):
        """
        清理资源
        """
        try:
            if self.parser:
                await self.parser.close()
            self.launcher.stop_browser(self.user_id)
            self.logger.info(f"🧹 窗口 {self.window_id} 资源清理完成")
        except Exception as e:
            self.logger.error(f"❌ 窗口 {self.window_id} 清理失败: {e}")

class MultiWindowScraper:
    """
    多窗口并行抓取器
    """
    def __init__(self, num_windows: int = 4):
        self.num_windows = num_windows
        self.windows: List[WindowManager] = []
        self.logger = logging.getLogger(__name__)
        self.filter_engine = TweetFilter()
        self.excel_writer = ExcelWriter()
        self.status_monitor_running = False
        
    def distribute_targets(self) -> List[Dict[str, Any]]:
        """
        将抓取目标分配给各个窗口
        """
        accounts = TWITTER_TARGETS['accounts']
        keywords = TWITTER_TARGETS['keywords']
        multi_user_ids = ADS_POWER_CONFIG.get('multi_user_ids', [ADS_POWER_CONFIG['user_id']])
        
        # 确保窗口数量不超过可用的用户ID数量
        actual_windows = min(self.num_windows, len(multi_user_ids))
        
        # 计算每个窗口的分配
        accounts_per_window = len(accounts) // actual_windows
        keywords_per_window = len(keywords) // actual_windows
        
        window_configs = []
        
        for i in range(actual_windows):
            # 分配账号
            start_acc = i * accounts_per_window
            end_acc = start_acc + accounts_per_window if i < actual_windows - 1 else len(accounts)
            window_accounts = accounts[start_acc:end_acc]
            
            # 分配关键词
            start_kw = i * keywords_per_window
            end_kw = start_kw + keywords_per_window if i < actual_windows - 1 else len(keywords)
            window_keywords = keywords[start_kw:end_kw]
            
            window_configs.append({
                'window_id': i + 1,
                'user_id': multi_user_ids[i],  # 使用不同的用户ID
                'accounts': window_accounts,
                'keywords': window_keywords
            })
        
        self.logger.info(f"🎯 目标分配完成: {actual_windows} 个窗口")
        for i, config in enumerate(window_configs):
            self.logger.info(f"   窗口 {i+1}: {len(config['accounts'])} 个账号, {len(config['keywords'])} 个关键词")
        
        return window_configs
    
    def start_status_monitor(self):
        """
        启动状态监控器，实时显示各窗口状态
        """
        def monitor_loop():
            while self.status_monitor_running:
                try:
                    # 清屏并显示状态
                    print("\033[2J\033[H")  # 清屏
                    print("="*80)
                    print(f"🚀 多窗口Twitter抓取器 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    print("="*80)
                    
                    for window in self.windows:
                        status_icon = {
                            "初始化": "🔄",
                            "启动浏览器": "🚀",
                            "连接解析器": "🔗",
                            "就绪": "✅",
                            "完成": "🎉"
                        }.get(window.status.split(":")[0], "📱")
                        
                        print(f"{status_icon} 窗口 {window.window_id:2d} | {window.status:20s} | {window.current_task:30s} | 推文: {len(window.collected_tweets):3d}")
                    
                    print("="*80)
                    print(f"💡 提示: 您可以看到各个浏览器窗口正在同步执行抓取任务")
                    print(f"📊 总计: {sum(len(w.collected_tweets) for w in self.windows)} 条推文")
                    
                    time.sleep(2)  # 每2秒更新一次
                    
                except Exception as e:
                    self.logger.error(f"状态监控错误: {e}")
                    time.sleep(5)
        
        self.status_monitor_running = True
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
    
    def stop_status_monitor(self):
        """
        停止状态监控器
        """
        self.status_monitor_running = False
    
    async def run_parallel_scraping(self) -> str:
        """
        执行并行抓取任务
        """
        try:
            self.logger.info("="*50)
            self.logger.info("🚀 多窗口并行Twitter抓取任务开始")
            self.logger.info(f"📅 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.logger.info(f"🪟 窗口数量: {self.num_windows}")
            self.logger.info("="*50)
            
            # 分配抓取目标
            window_configs = self.distribute_targets()
            
            # 创建窗口管理器
            self.windows = []
            for config in window_configs:
                window = WindowManager(
                    config['window_id'],
                    config['user_id'],
                    config['accounts'],
                    config['keywords']
                )
                self.windows.append(window)
            
            # 启动状态监控
            self.start_status_monitor()
            
            # 并行初始化所有窗口
            self.logger.info("🔄 开始并行初始化所有窗口...")
            init_tasks = [window.initialize() for window in self.windows]
            init_results = await asyncio.gather(*init_tasks, return_exceptions=True)
            
            # 检查初始化结果
            successful_windows = []
            for i, result in enumerate(init_results):
                if isinstance(result, Exception):
                    self.logger.error(f"❌ 窗口 {i+1} 初始化失败: {result}")
                elif result:
                    successful_windows.append(self.windows[i])
                    self.logger.info(f"✅ 窗口 {i+1} 初始化成功")
            
            if not successful_windows:
                raise Exception("所有窗口初始化失败")
            
            self.logger.info(f"🎯 {len(successful_windows)}/{self.num_windows} 个窗口初始化成功")
            
            # 并行执行抓取任务
            self.logger.info("📱 开始并行抓取任务...")
            scraping_tasks = [window.run_scraping_task() for window in successful_windows]
            scraping_results = await asyncio.gather(*scraping_tasks, return_exceptions=True)
            
            # 收集所有推文
            all_tweets = []
            for i, result in enumerate(scraping_results):
                if isinstance(result, Exception):
                    self.logger.error(f"❌ 窗口 {i+1} 抓取失败: {result}")
                elif isinstance(result, list):
                    all_tweets.extend(result)
                    self.logger.info(f"📊 窗口 {i+1} 贡献 {len(result)} 条推文")
            
            # 停止状态监控
            self.stop_status_monitor()
            
            if not all_tweets:
                self.logger.warning("⚠️ 没有抓取到任何推文数据")
                return ''
            
            # 去除重复推文
            unique_tweets = self.remove_duplicates(all_tweets)
            self.logger.info(f"🔄 去重后共有 {len(unique_tweets)} 条推文")
            
            # 筛选推文
            self.logger.info("🔍 开始筛选推文...")
            filtered_tweets = self.filter_engine.filter_tweets(unique_tweets)
            passed_tweets = self.filter_engine.get_passed_tweets(filtered_tweets)
            
            self.logger.info(f"✅ 筛选完成，{len(passed_tweets)}/{len(unique_tweets)} 条推文通过筛选")
            
            # 生成统计信息
            statistics = self.filter_engine.get_filter_statistics(filtered_tweets)
            
            # 导出到 Excel
            self.logger.info("📊 开始导出数据到 Excel...")
            output_file = self.excel_writer.write_tweets_with_summary(passed_tweets, statistics)
            
            self.logger.info("="*50)
            self.logger.info("🎉 多窗口并行抓取任务完成")
            self.logger.info(f"📅 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.logger.info(f"📄 输出文件: {output_file}")
            self.logger.info(f"📊 总推文数: {statistics['total_tweets']}")
            self.logger.info(f"✅ 通过筛选: {statistics['passed_tweets']}")
            self.logger.info(f"📈 通过率: {statistics['pass_rate']:.2%}")
            self.logger.info("="*50)
            
            return output_file
            
        except Exception as e:
            self.logger.error(f"❌ 多窗口抓取任务失败: {e}")
            raise
        finally:
            await self.cleanup_all_windows()
    
    def remove_duplicates(self, tweets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        去除重复的推文
        """
        seen_links = set()
        unique_tweets = []
        
        for tweet in tweets:
            link = tweet.get('link', '')
            content = tweet.get('content', '')
            
            # 使用链接或内容作为去重标识
            identifier = link if link else content
            
            if identifier and identifier not in seen_links:
                seen_links.add(identifier)
                unique_tweets.append(tweet)
        
        removed_count = len(tweets) - len(unique_tweets)
        if removed_count > 0:
            self.logger.info(f"🔄 去除了 {removed_count} 条重复推文")
        
        return unique_tweets
    
    async def cleanup_all_windows(self):
        """
        清理所有窗口资源
        """
        self.stop_status_monitor()
        
        if self.windows:
            self.logger.info("🧹 开始清理所有窗口资源...")
            cleanup_tasks = [window.cleanup() for window in self.windows]
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
            self.logger.info("✅ 所有窗口资源清理完成")

async def main():
    """
    主函数 - 多窗口并行抓取
    """
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建多窗口抓取器
    scraper = MultiWindowScraper(num_windows=4)  # 可以调整窗口数量
    
    try:
        print("🚀 启动多窗口并行Twitter抓取器")
        print("💡 您将看到多个浏览器窗口同时打开并执行抓取任务")
        print("📱 每个窗口都会实时显示其操作过程")
        print("⏳ 请稍等，正在初始化...\n")
        
        # 执行并行抓取
        output_file = await scraper.run_parallel_scraping()
        
        if output_file:
            print(f"\n🎉 多窗口抓取任务完成！")
            print(f"📊 Excel 报表已生成: {output_file}")
            print(f"📁 数据目录: {OUTPUT_CONFIG['data_dir']}")
        else:
            print("\n❌ 抓取任务失败，请查看日志了解详情")
            
    except KeyboardInterrupt:
        print("\n⏹️ 任务被用户中断")
    except Exception as e:
        print(f"\n❌ 任务执行失败: {e}")
    finally:
        await scraper.cleanup_all_windows()

if __name__ == "__main__":
    asyncio.run(main())