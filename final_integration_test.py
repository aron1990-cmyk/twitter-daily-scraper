#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终集成测试脚本
测试完整的Twitter抓取流程
"""

import asyncio
import logging
import sys
import os
import json
from datetime import datetime

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

async def test_complete_scraping_workflow():
    """测试完整的抓取工作流程"""
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
        
        # 初始化数据提取器和过滤器
        data_extractor = DataExtractor()
        tweet_filter = TweetFilter()
        logger.info("✅ 数据提取器和过滤器初始化完成")
        
        # 测试场景1: 用户推文抓取
        logger.info("\n📋 测试场景1: 用户推文抓取")
        logger.info("🔄 导航到@elonmusk页面...")
        
        try:
            await parser.navigate_to_profile('elonmusk')
            logger.info("✅ 成功导航到用户页面")
        except Exception as nav_error:
            logger.warning(f"导航失败: {nav_error}，尝试直接访问")
            await parser.page.goto('https://x.com/elonmusk', wait_until='domcontentloaded')
            await asyncio.sleep(5)
        
        # 等待页面加载
        logger.info("⏳ 等待页面加载...")
        await asyncio.sleep(10)
        
        # 检查初始推文数量
        initial_tweets = await parser.page.query_selector_all('[data-testid="tweet"]')
        logger.info(f"📊 初始推文数量: {len(initial_tweets)}")
        
        # 执行滚动加载
        target_tweets = 15
        logger.info(f"🎯 开始滚动加载，目标: {target_tweets} 条推文")
        
        scroll_attempts = 0
        max_scroll_attempts = 8
        last_tweet_count = len(initial_tweets)
        stagnant_count = 0
        
        while scroll_attempts < max_scroll_attempts:
            # 获取当前推文数量
            current_tweets = await parser.page.query_selector_all('[data-testid="tweet"]')
            current_count = len(current_tweets)
            
            logger.info(f"📈 滚动尝试 {scroll_attempts + 1}/{max_scroll_attempts}，当前推文: {current_count}")
            
            # 检查是否达到目标
            if current_count >= target_tweets:
                logger.info(f"🎉 达到目标推文数量: {current_count}/{target_tweets}")
                break
            
            # 检查是否有新推文加载
            if current_count == last_tweet_count:
                stagnant_count += 1
            else:
                stagnant_count = 0
            
            last_tweet_count = current_count
            
            # 如果连续停滞太多次，停止滚动
            if stagnant_count >= 4:
                logger.warning("⚠️ 连续多次无新推文，停止滚动")
                break
            
            # 执行滚动
            scroll_distance = 1000 if stagnant_count < 2 else 2000
            await parser.page.evaluate(f'window.scrollBy(0, {scroll_distance})')
            await asyncio.sleep(3)
            
            scroll_attempts += 1
        
        # 获取最终推文列表
        final_tweets = await parser.page.query_selector_all('[data-testid="tweet"]')
        final_count = len(final_tweets)
        logger.info(f"📊 最终推文数量: {final_count}")
        
        # 解析推文数据
        logger.info("🔍 开始解析推文数据...")
        parsed_tweets = []
        successful_parses = 0
        failed_parses = 0
        
        for i, tweet_element in enumerate(final_tweets[:target_tweets]):
            try:
                tweet_data = await parser.parse_tweet_element(tweet_element)
                if tweet_data:
                    # 验证必要字段
                    if tweet_data.get('content') or tweet_data.get('username') != 'unknown':
                        parsed_tweets.append(tweet_data)
                        successful_parses += 1
                        logger.info(f"  ✅ 推文 {i+1}: {tweet_data.get('username', 'unknown')} - {tweet_data.get('content', 'No content')[:50]}...")
                    else:
                        failed_parses += 1
                        logger.warning(f"  ⚠️ 推文 {i+1}: 数据不完整")
                else:
                    failed_parses += 1
                    logger.warning(f"  ❌ 推文 {i+1}: 解析失败")
            except Exception as e:
                failed_parses += 1
                logger.warning(f"  ❌ 推文 {i+1}: 解析异常 - {e}")
        
        logger.info(f"📊 解析结果: 成功 {successful_parses}，失败 {failed_parses}")
        
        # 应用过滤器
        logger.info("🔍 应用推文过滤器...")
        filtered_tweets = []
        for tweet in parsed_tweets:
            try:
                if tweet_filter.should_include_tweet(tweet):
                    filtered_tweets.append(tweet)
            except Exception as e:
                logger.warning(f"过滤推文时出错: {e}")
        
        logger.info(f"📊 过滤结果: {len(filtered_tweets)}/{len(parsed_tweets)} 条推文通过过滤")
        
        # 保存测试结果
        test_results = {
            'timestamp': datetime.now().isoformat(),
            'test_scenario': 'user_profile_scraping',
            'target_user': 'elonmusk',
            'target_tweets': target_tweets,
            'final_tweet_count': final_count,
            'parsed_tweets': successful_parses,
            'failed_parses': failed_parses,
            'filtered_tweets': len(filtered_tweets),
            'scroll_attempts': scroll_attempts,
            'success_rate': successful_parses / max(final_count, 1) * 100,
            'sample_tweets': filtered_tweets[:3]  # 保存前3条作为样本
        }
        
        # 保存到文件
        output_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(test_results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 测试结果已保存到: {output_file}")
        
        # 测试场景2: 搜索功能测试（可选）
        if successful_parses >= target_tweets * 0.6:  # 如果用户抓取成功率超过60%
            logger.info("\n📋 测试场景2: 搜索功能测试")
            try:
                search_keyword = "AI"
                logger.info(f"🔍 搜索关键词: {search_keyword}")
                
                await parser.search_tweets(search_keyword)
                await asyncio.sleep(5)
                
                # 获取搜索结果
                search_tweets = await parser.page.query_selector_all('[data-testid="tweet"]')
                logger.info(f"📊 搜索结果: {len(search_tweets)} 条推文")
                
                if len(search_tweets) > 0:
                    logger.info("✅ 搜索功能正常")
                    test_results['search_test'] = {
                        'keyword': search_keyword,
                        'results_count': len(search_tweets),
                        'status': 'success'
                    }
                else:
                    logger.warning("⚠️ 搜索功能可能有问题")
                    test_results['search_test'] = {
                        'keyword': search_keyword,
                        'results_count': 0,
                        'status': 'no_results'
                    }
                    
            except Exception as search_error:
                logger.warning(f"❌ 搜索功能测试失败: {search_error}")
                test_results['search_test'] = {
                    'keyword': search_keyword,
                    'status': 'failed',
                    'error': str(search_error)
                }
        
        # 更新测试结果文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(test_results, f, ensure_ascii=False, indent=2)
        
        # 生成测试报告
        logger.info("\n📊 测试报告:")
        logger.info(f"  目标推文数量: {target_tweets}")
        logger.info(f"  实际获取推文: {final_count}")
        logger.info(f"  成功解析推文: {successful_parses}")
        logger.info(f"  解析成功率: {successful_parses / max(final_count, 1) * 100:.1f}%")
        logger.info(f"  过滤后推文: {len(filtered_tweets)}")
        logger.info(f"  滚动次数: {scroll_attempts}")
        
        # 判断测试结果
        if successful_parses >= target_tweets * 0.7:
            logger.info("🎉 集成测试成功！抓取系统工作正常")
            return True
        elif successful_parses >= target_tweets * 0.4:
            logger.warning("⚠️ 集成测试部分成功，系统基本可用但需要优化")
            return True
        else:
            logger.error("❌ 集成测试失败，系统存在严重问题")
            return False
            
    except Exception as e:
        logger.error(f"❌ 集成测试失败: {e}")
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
    success = asyncio.run(test_complete_scraping_workflow())
    if success:
        logger.info("\n🎊 所有测试完成，系统状态良好！")
    else:
        logger.error("\n💥 测试失败，需要进一步调试")
        sys.exit(1)