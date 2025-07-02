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

# 添加当前目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import (
    ADS_POWER_CONFIG, TWITTER_TARGETS, FILTER_CONFIG, 
    OUTPUT_CONFIG, BROWSER_CONFIG, LOG_CONFIG
)
from ads_browser_launcher import AdsPowerLauncher
from twitter_parser import TwitterParser
from tweet_filter import TweetFilter
from excel_writer import ExcelWriter

class TwitterDailyScraper:
    def __init__(self):
        self.launcher = AdsPowerLauncher()
        self.parser = None
        self.filter_engine = TweetFilter()
        self.excel_writer = ExcelWriter()
        self.logger = self.setup_logging()
        
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
                
                tweets = await self.parser.scrape_user_tweets(username, max_tweets_per_user)
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
        抓取包含指定关键词的推文
        
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
                
                tweets = await self.parser.scrape_keyword_tweets(keyword, max_tweets_per_keyword)
                all_tweets.extend(tweets)
                
                self.logger.info(f"关键词 '{keyword}' 搜索完成，获得 {len(tweets)} 条推文")
                
                # 添加延迟避免被限制
                await asyncio.sleep(BROWSER_CONFIG['wait_time'])
                
            except Exception as e:
                self.logger.error(f"搜索关键词 '{keyword}' 失败: {e}")
                continue
        
        return all_tweets
    
    def remove_duplicates(self, tweets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        去除重复的推文
        
        Args:
            tweets: 推文数据列表
            
        Returns:
            去重后的推文列表
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
            self.logger.info(f"去除了 {removed_count} 条重复推文")
        
        return unique_tweets
    
    async def run_scraping_task(self, user_id: str = None) -> str:
        """
        执行完整的抓取任务
        
        Args:
            user_id: AdsPower 用户ID
            
        Returns:
            生成的 Excel 文件路径
        """
        try:
            self.logger.info("="*50)
            self.logger.info("Twitter 日报采集任务开始")
            self.logger.info(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.logger.info("="*50)
            
            # 初始化浏览器
            if not await self.initialize_browser(user_id):
                raise Exception("浏览器初始化失败")
            
            all_tweets = []
            
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
            
            # 去除重复推文
            unique_tweets = self.remove_duplicates(all_tweets)
            self.logger.info(f"去重后共有 {len(unique_tweets)} 条推文")
            
            # 筛选推文
            self.logger.info("开始筛选推文...")
            filtered_tweets = self.filter_engine.filter_tweets(unique_tweets)
            passed_tweets = self.filter_engine.get_passed_tweets(filtered_tweets)
            
            self.logger.info(f"筛选完成，{len(passed_tweets)}/{len(unique_tweets)} 条推文通过筛选")
            
            if not passed_tweets:
                self.logger.warning("没有推文通过筛选条件")
                # 仍然生成文件，但只包含统计信息
                passed_tweets = []
            
            # 生成统计信息
            statistics = self.filter_engine.get_filter_statistics(filtered_tweets)
            
            # 导出到 Excel
            self.logger.info("开始导出数据到 Excel...")
            output_file = self.excel_writer.write_tweets_with_summary(passed_tweets, statistics)
            
            self.logger.info("="*50)
            self.logger.info("Twitter 日报采集任务完成")
            self.logger.info(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.logger.info(f"输出文件: {output_file}")
            self.logger.info(f"总推文数: {statistics['total_tweets']}")
            self.logger.info(f"通过筛选: {statistics['passed_tweets']}")
            self.logger.info(f"通过率: {statistics['pass_rate']:.2%}")
            self.logger.info("="*50)
            
            return output_file
            
        except Exception as e:
            self.logger.error(f"抓取任务执行失败: {e}")
            raise
        finally:
            await self.cleanup()
    
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
            print("配置验证失败，请检查 config.py 文件")
            return
        
        # 执行抓取任务
        output_file = await scraper.run_scraping_task()
        
        if output_file:
            print(f"\n✅ 任务完成！")
            print(f"📊 Excel 报表已生成: {output_file}")
            print(f"📁 数据目录: {OUTPUT_CONFIG['data_dir']}")
        else:
            print("\n❌ 任务失败，请查看日志了解详情")
            
    except KeyboardInterrupt:
        print("\n⏹️  任务被用户中断")
        scraper.logger.info("任务被用户中断")
    except Exception as e:
        print(f"\n❌ 任务执行失败: {e}")
        scraper.logger.error(f"任务执行失败: {e}")
    finally:
        await scraper.cleanup()

if __name__ == "__main__":
    # 检查 Python 版本
    if sys.version_info < (3, 7):
        print("错误: 需要 Python 3.7 或更高版本")
        sys.exit(1)
    
    # 运行主程序
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"程序启动失败: {e}")
        sys.exit(1)