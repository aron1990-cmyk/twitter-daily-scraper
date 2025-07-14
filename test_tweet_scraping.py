#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试推文抓取功能
验证能否成功抓取真实推文并输出到控制台
"""

import asyncio
import logging
import json
from twitter_parser import TwitterParser
from ads_browser_launcher import AdsPowerLauncher

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_tweet_scraping():
    """
    测试推文抓取功能
    """
    browser_launcher = None
    parser = None
    
    try:
        # 1. 启动AdsPower浏览器
        logger.info("=== 启动AdsPower浏览器 ===")
        browser_launcher = AdsPowerLauncher()
        browser_info = browser_launcher.start_browser()
        debug_port = browser_launcher.get_debug_port()
        logger.info(f"浏览器调试端口: {debug_port}")
        
        # 2. 初始化Twitter解析器
        logger.info("=== 初始化Twitter解析器 ===")
        parser = TwitterParser(debug_port)
        await parser.connect_browser()
        
        # 3. 导航到Twitter
        logger.info("=== 导航到Twitter ===")
        await parser.navigate_to_twitter()
        
        # 4. 测试用户推文抓取
        test_users = ['OpenAI', 'sama']  # 从相对容易访问的用户开始
        
        for username in test_users:
            logger.info(f"\n=== 测试抓取 @{username} 的推文 ===")
            
            try:
                # 抓取推文
                tweets = await parser.scrape_user_tweets(username, max_tweets=5)
                
                if tweets:
                    logger.info(f"✅ 成功抓取到 {len(tweets)} 条推文")
                    
                    # 输出推文内容到控制台
                    print(f"\n{'='*60}")
                    print(f"用户 @{username} 的推文:")
                    print(f"{'='*60}")
                    
                    for i, tweet in enumerate(tweets, 1):
                        print(f"\n--- 推文 {i} ---")
                        print(f"用户: @{tweet.get('username', 'unknown')}")
                        print(f"内容: {tweet.get('content', '无内容')[:200]}{'...' if len(tweet.get('content', '')) > 200 else ''}")
                        print(f"发布时间: {tweet.get('publish_time', '未知')}")
                        print(f"点赞: {tweet.get('likes', 0)} | 评论: {tweet.get('comments', 0)} | 转发: {tweet.get('retweets', 0)}")
                        if tweet.get('link'):
                            print(f"链接: {tweet.get('link')}")
                        print("-" * 40)
                    
                    # 保存到JSON文件用于进一步分析
                    filename = f"tweets_{username}.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(tweets, f, ensure_ascii=False, indent=2)
                    logger.info(f"推文数据已保存到 {filename}")
                    
                else:
                    logger.warning(f"❌ 未能抓取到 @{username} 的推文")
                    
            except Exception as e:
                logger.error(f"❌ 抓取 @{username} 推文失败: {e}")
            
            # 用户之间等待一段时间
            await asyncio.sleep(3)
        
        # 5. 测试关键词搜索
        logger.info(f"\n=== 测试关键词搜索 ===")
        
        try:
            keyword = "AI"
            logger.info(f"搜索关键词: {keyword}")
            
            tweets = await parser.scrape_keyword_tweets(keyword, max_tweets=3)
            
            if tweets:
                logger.info(f"✅ 成功搜索到 {len(tweets)} 条相关推文")
                
                print(f"\n{'='*60}")
                print(f"关键词 '{keyword}' 的搜索结果:")
                print(f"{'='*60}")
                
                for i, tweet in enumerate(tweets, 1):
                    print(f"\n--- 搜索结果 {i} ---")
                    print(f"用户: @{tweet.get('username', 'unknown')}")
                    print(f"内容: {tweet.get('content', '无内容')[:200]}{'...' if len(tweet.get('content', '')) > 200 else ''}")
                    print(f"发布时间: {tweet.get('publish_time', '未知')}")
                    print(f"点赞: {tweet.get('likes', 0)} | 评论: {tweet.get('comments', 0)} | 转发: {tweet.get('retweets', 0)}")
                    print("-" * 40)
                
                # 保存搜索结果
                filename = f"search_{keyword}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(tweets, f, ensure_ascii=False, indent=2)
                logger.info(f"搜索结果已保存到 {filename}")
                
            else:
                logger.warning(f"❌ 未能搜索到关键词 '{keyword}' 的相关推文")
                
        except Exception as e:
            logger.error(f"❌ 关键词搜索失败: {e}")
        
        logger.info("\n=== 测试完成 ===")
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        
    finally:
        # 清理资源
        try:
            if parser:
                await parser.close()
            if browser_launcher:
                browser_launcher.stop_browser()
        except Exception as e:
            logger.error(f"清理资源时发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_tweet_scraping())