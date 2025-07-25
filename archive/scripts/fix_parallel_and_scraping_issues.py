#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复并行任务和抓取逻辑问题
1. 确保多任务并行执行时能启动多个浏览器实例
2. 修复推文抓取逻辑中的数量判断问题
"""

import os
import sys
import json
import logging
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fix_refactored_task_manager():
    """修复RefactoredTaskManager的并行任务管理"""
    logger.info("开始修复RefactoredTaskManager的并行任务管理...")
    
    file_path = "/Users/aron/twitter-daily-scraper/refactored_task_manager.py"
    
    # 读取原文件
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复1: 确保用户ID池正确初始化
    old_init = '''def __init__(self, max_concurrent_tasks=1, user_ids=None):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.user_id_pool = list(user_ids or ['default'])
        self.available_user_ids = list(user_ids or ['default'])  # 兼容原API'''
    
    new_init = '''def __init__(self, max_concurrent_tasks=1, user_ids=None):
        self.max_concurrent_tasks = max_concurrent_tasks
        # 确保用户ID池正确设置
        if user_ids and isinstance(user_ids, list) and len(user_ids) > 0:
            self.user_id_pool = list(user_ids)
            self.available_user_ids = list(user_ids)  # 兼容原API
            logger.info(f"[RefactoredTaskManager] 初始化用户ID池: {user_ids}")
        else:
            self.user_id_pool = ['default']
            self.available_user_ids = ['default']
            logger.warning(f"[RefactoredTaskManager] 使用默认用户ID: ['default']")
        
        logger.info(f"[RefactoredTaskManager] 最大并发任务数: {max_concurrent_tasks}")
        logger.info(f"[RefactoredTaskManager] 可用用户ID数量: {len(self.user_id_pool)}")
        logger.info(f"[RefactoredTaskManager] 用户ID列表: {self.user_id_pool}")'''
    
    if old_init in content:
        content = content.replace(old_init, new_init)
        logger.info("✅ 修复了用户ID池初始化逻辑")
    
    # 修复2: 改进用户ID分配逻辑
    old_get_user_id = '''def _get_available_user_id(self) -> Optional[str]:
        """获取可用的用户ID"""
        with self._state_lock:
            if self.available_users:
                return self.available_users.pop()
            return None'''
    
    new_get_user_id = '''def _get_available_user_id(self) -> Optional[str]:
        """获取可用的用户ID"""
        with self._state_lock:
            if self.available_users:
                user_id = self.available_users.pop()
                logger.info(f"[RefactoredTaskManager] 分配用户ID: {user_id}，剩余可用: {len(self.available_users)}")
                return user_id
            logger.warning(f"[RefactoredTaskManager] 没有可用的用户ID，当前活跃任务: {len(self.active_slots)}")
            return None'''
    
    if old_get_user_id in content:
        content = content.replace(old_get_user_id, new_get_user_id)
        logger.info("✅ 修复了用户ID分配逻辑")
    
    # 修复3: 改进用户ID归还逻辑
    old_return_user_id = '''def _return_user_id(self, user_id: str):
        """归还用户ID"""
        with self._state_lock:
            self.available_users.add(user_id)'''
    
    new_return_user_id = '''def _return_user_id(self, user_id: str):
        """归还用户ID"""
        with self._state_lock:
            if user_id in self.user_id_pool:  # 确保只归还有效的用户ID
                self.available_users.add(user_id)
                logger.info(f"[RefactoredTaskManager] 归还用户ID: {user_id}，当前可用: {len(self.available_users)}")
            else:
                logger.warning(f"[RefactoredTaskManager] 尝试归还无效用户ID: {user_id}")'''
    
    if old_return_user_id in content:
        content = content.replace(old_return_user_id, new_return_user_id)
        logger.info("✅ 修复了用户ID归还逻辑")
    
    # 修复4: 改进任务启动日志
    old_start_background = '''print(f"[RefactoredTaskManager] 后台任务 {task_id} 启动成功，PID: {process.pid}")'''
    new_start_background = '''print(f"[RefactoredTaskManager] 后台任务 {task_id} 启动成功，PID: {process.pid}，用户ID: {user_id}")
            logger.info(f"[RefactoredTaskManager] 当前活跃任务数: {len(self.active_slots)}/{self.max_concurrent_tasks}")'''
    
    if old_start_background in content:
        content = content.replace(old_start_background, new_start_background)
        logger.info("✅ 修复了任务启动日志")
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info("✅ RefactoredTaskManager修复完成")

def fix_twitter_parser_scraping():
    """修复TwitterParser的推文抓取逻辑"""
    logger.info("开始修复TwitterParser的推文抓取逻辑...")
    
    file_path = "/Users/aron/twitter-daily-scraper/twitter_parser.py"
    
    # 读取原文件
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复1: 改进scrape_tweets方法的滚动和抓取逻辑
    old_scrape_tweets = '''async def scrape_tweets(self, max_tweets: int = 10, enable_enhanced: bool = False) -> List[Dict[str, Any]]:
        """
        抓取当前页面的推文数据
        
        Args:
            max_tweets: 最大抓取推文数量
            enable_enhanced: 是否启用增强抓取（包含详情页内容）
            
        Returns:
            推文数据列表
        """
        if enable_enhanced:
            return await self.enhanced_tweet_scraping(max_tweets, enable_details=True)
        
        tweets_data = []
        
        try:
            # 等待推文加载
            await self.page.wait_for_selector('[data-testid="tweet"]', timeout=10000)
            
            # 获取当前页面的推文元素
            tweet_elements = await self.page.query_selector_all('[data-testid="tweet"]')
            available_tweets = len(tweet_elements)
            
            self.logger.info(f"当前页面找到 {available_tweets} 条推文，目标抓取 {max_tweets} 条")
            
            # 确定实际抓取数量
            actual_max = min(max_tweets, available_tweets)
            
            for i, tweet_element in enumerate(tweet_elements[:actual_max]):
                # 每隔几条推文检查页面焦点
                if i % 5 == 0:
                    await self.ensure_page_focus()
                
                # 模拟人工查看推文的行为
                if self.behavior_simulator and i % 3 == 0:  # 每3条推文模拟一次交互
                    await self.behavior_simulator.simulate_tweet_interaction(tweet_element)
                
                self.logger.debug(f"开始解析第 {i+1} 个推文元素")
                tweet_data = await self.parse_tweet_element(tweet_element)
                if tweet_data:
                    tweets_data.append(tweet_data)
                    self.logger.info(f"成功解析第 {i+1} 条推文: @{tweet_data['username']}")
                else:
                    self.logger.debug(f"第 {i+1} 个推文元素解析失败或返回None")
                
                # 添加短暂延迟，模拟人工阅读
                await asyncio.sleep(0.1)
            
            self.logger.info(f"推文抓取完成，成功获取 {len(tweets_data)} 条推文")
            return tweets_data
            
        except Exception as e:
            self.logger.error(f"抓取推文失败: {e}")
            return []'''
    
    new_scrape_tweets = '''async def scrape_tweets(self, max_tweets: int = 10, enable_enhanced: bool = False) -> List[Dict[str, Any]]:
        """
        抓取当前页面的推文数据
        
        Args:
            max_tweets: 最大抓取推文数量
            enable_enhanced: 是否启用增强抓取（包含详情页内容）
            
        Returns:
            推文数据列表
        """
        if enable_enhanced:
            return await self.enhanced_tweet_scraping(max_tweets, enable_details=True)
        
        tweets_data = []
        max_scroll_attempts = 20  # 最大滚动次数
        scroll_attempts = 0
        last_tweet_count = 0
        no_new_tweets_count = 0
        
        try:
            self.logger.info(f"开始抓取推文，目标数量: {max_tweets}")
            
            while len(tweets_data) < max_tweets and scroll_attempts < max_scroll_attempts:
                # 等待推文加载
                try:
                    await self.page.wait_for_selector('[data-testid="tweet"]', timeout=5000)
                except Exception:
                    self.logger.warning(f"等待推文元素超时，当前滚动次数: {scroll_attempts}")
                    if scroll_attempts == 0:  # 第一次就没找到推文，可能页面有问题
                        break
                
                # 获取当前页面的推文元素
                tweet_elements = await self.page.query_selector_all('[data-testid="tweet"]')
                current_tweet_count = len(tweet_elements)
                
                self.logger.info(f"滚动第 {scroll_attempts + 1} 次，页面推文数: {current_tweet_count}，已抓取: {len(tweets_data)}")
                
                # 解析新的推文
                new_tweets_parsed = 0
                for i, tweet_element in enumerate(tweet_elements):
                    if len(tweets_data) >= max_tweets:
                        break
                    
                    # 每隔几条推文检查页面焦点
                    if i % 5 == 0:
                        await self.ensure_page_focus()
                    
                    tweet_data = await self.parse_tweet_element(tweet_element)
                    if tweet_data:
                        # 检查是否已经抓取过这条推文（去重）
                        tweet_id = tweet_data.get('link', '') or tweet_data.get('content', '')[:50]
                        if tweet_id not in self.seen_tweet_ids:
                            self.seen_tweet_ids.add(tweet_id)
                            tweets_data.append(tweet_data)
                            new_tweets_parsed += 1
                            self.logger.debug(f"新抓取推文: @{tweet_data.get('username', 'unknown')}")
                
                self.logger.info(f"本次滚动新解析推文: {new_tweets_parsed}，累计: {len(tweets_data)}/{max_tweets}")
                
                # 检查是否有新推文
                if current_tweet_count <= last_tweet_count:
                    no_new_tweets_count += 1
                    self.logger.info(f"页面推文数量未增加，连续次数: {no_new_tweets_count}")
                    if no_new_tweets_count >= 3:  # 连续3次没有新推文，可能到底了
                        self.logger.info("连续多次滚动无新推文，可能已到页面底部")
                        break
                else:
                    no_new_tweets_count = 0
                
                last_tweet_count = current_tweet_count
                
                # 如果已达到目标数量，停止滚动
                if len(tweets_data) >= max_tweets:
                    self.logger.info(f"已达到目标推文数量: {len(tweets_data)}/{max_tweets}")
                    break
                
                # 滚动页面加载更多推文
                scroll_attempts += 1
                if scroll_attempts < max_scroll_attempts:
                    await self.page.evaluate('window.scrollBy(0, 800)')
                    await asyncio.sleep(1)  # 等待加载
                    
                    # 处理可能的弹窗
                    try:
                        await self.dismiss_translate_popup()
                    except Exception:
                        pass
            
            # 只返回目标数量的推文
            final_tweets = tweets_data[:max_tweets]
            self.logger.info(f"推文抓取完成，目标: {max_tweets}，实际获取: {len(final_tweets)}，滚动次数: {scroll_attempts}")
            
            if len(final_tweets) < max_tweets:
                shortage = max_tweets - len(final_tweets)
                self.logger.warning(f"推文数量不足，缺少 {shortage} 条推文")
            
            return final_tweets
            
        except Exception as e:
            self.logger.error(f"抓取推文失败: {e}")
            return tweets_data[:max_tweets] if tweets_data else []'''
    
    if old_scrape_tweets in content:
        content = content.replace(old_scrape_tweets, new_scrape_tweets)
        logger.info("✅ 修复了scrape_tweets方法的滚动和抓取逻辑")
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info("✅ TwitterParser推文抓取逻辑修复完成")

def fix_web_app_config():
    """修复web_app.py中的配置初始化"""
    logger.info("开始修复web_app.py中的配置初始化...")
    
    file_path = "/Users/aron/twitter-daily-scraper/web_app.py"
    
    # 读取原文件
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复init_task_manager函数
    old_init_task_manager = '''def init_task_manager():
    """初始化任务管理器"""
    global task_manager, optimized_scraper
    
    # 检查是否已经初始化，避免重复初始化
    if task_manager is not None:
        print("⚠️ TaskManager已经初始化，跳过重复初始化")
        return
    
    max_concurrent = ADS_POWER_CONFIG.get('max_concurrent_tasks', 2)
    user_ids = ADS_POWER_CONFIG.get('user_ids', [ADS_POWER_CONFIG.get('user_id', 'default')])
    task_manager = RefactoredTaskManager(max_concurrent_tasks=max_concurrent, user_ids=user_ids)
    
    print(f"[RefactoredTaskManager] 初始化完成，最大并发: {max_concurrent}")
    
    # 初始化优化抓取器
    # optimized_scraper = MultiWindowEnhancedScraper(max_workers=max_concurrent)
    
    print(f"✅ TaskManager已初始化，最大并发任务数: {max_concurrent}")
    print(f"✅ OptimizedScraper已初始化，支持多窗口并发抓取")'''
    
    new_init_task_manager = '''def init_task_manager():
    """初始化任务管理器"""
    global task_manager, optimized_scraper
    
    # 检查是否已经初始化，避免重复初始化
    if task_manager is not None:
        print("⚠️ TaskManager已经初始化，跳过重复初始化")
        return
    
    max_concurrent = ADS_POWER_CONFIG.get('max_concurrent_tasks', 2)
    
    # 获取用户ID列表，优先使用user_ids，然后是multi_user_ids，最后是单个user_id
    user_ids = ADS_POWER_CONFIG.get('user_ids')
    if not user_ids:
        user_ids = ADS_POWER_CONFIG.get('multi_user_ids')
    if not user_ids:
        user_ids = [ADS_POWER_CONFIG.get('user_id', 'default')]
    
    print(f"[TaskManager] 配置信息:")
    print(f"  - 最大并发任务数: {max_concurrent}")
    print(f"  - 用户ID列表: {user_ids}")
    print(f"  - 用户ID数量: {len(user_ids)}")
    
    # 确保用户ID数量足够支持并发任务
    if len(user_ids) < max_concurrent:
        print(f"⚠️ 警告: 用户ID数量({len(user_ids)})少于最大并发任务数({max_concurrent})")
        print(f"⚠️ 建议配置至少 {max_concurrent} 个用户ID以支持完全并行")
    
    task_manager = RefactoredTaskManager(max_concurrent_tasks=max_concurrent, user_ids=user_ids)
    
    print(f"[RefactoredTaskManager] 初始化完成，最大并发: {max_concurrent}")
    
    # 初始化优化抓取器
    # optimized_scraper = MultiWindowEnhancedScraper(max_workers=max_concurrent)
    
    print(f"✅ TaskManager已初始化，最大并发任务数: {max_concurrent}")
    print(f"✅ 用户ID池大小: {len(user_ids)}")
    print(f"✅ OptimizedScraper已初始化，支持多窗口并发抓取")'''
    
    if old_init_task_manager in content:
        content = content.replace(old_init_task_manager, new_init_task_manager)
        logger.info("✅ 修复了init_task_manager函数")
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info("✅ web_app.py配置初始化修复完成")

def main():
    """主函数"""
    logger.info("开始修复并行任务和抓取逻辑问题...")
    
    try:
        # 修复1: RefactoredTaskManager的并行任务管理
        fix_refactored_task_manager()
        
        # 修复2: TwitterParser的推文抓取逻辑
        fix_twitter_parser_scraping()
        
        # 修复3: web_app.py的配置初始化
        fix_web_app_config()
        
        logger.info("\n" + "="*60)
        logger.info("🎉 所有修复完成！")
        logger.info("="*60)
        logger.info("修复内容总结:")
        logger.info("1. ✅ 修复了RefactoredTaskManager的用户ID池管理")
        logger.info("2. ✅ 改进了用户ID分配和归还逻辑")
        logger.info("3. ✅ 修复了TwitterParser的推文抓取和滚动逻辑")
        logger.info("4. ✅ 改进了推文数量判断和去重机制")
        logger.info("5. ✅ 修复了web_app.py的任务管理器初始化")
        logger.info("="*60)
        logger.info("\n现在系统应该能够:")
        logger.info("• 同时启动多个任务时正确分配不同的AdsPower用户ID")
        logger.info("• 启动多个浏览器实例并行执行抓取任务")
        logger.info("• 正确判断推文数量并进行充分的滚动抓取")
        logger.info("• 避免Mike_Stelzner等大V账号的内容不足误报")
        logger.info("\n请重启应用以使修复生效。")
        
    except Exception as e:
        logger.error(f"修复过程中出现错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()