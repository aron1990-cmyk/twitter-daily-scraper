#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.ads_browser_launcher import AdsPowerLauncher
from core.twitter_parser import TwitterParser
from config.adspower_config import ADSPOWER_CONFIG
from utils.models import ScrapingTask, db, app

async def debug_0xluffy_eth_scraping():
    """调试0xluffy_eth推文抓取问题"""
    try:
        print("=== 开始调试0xluffy_eth推文抓取 ===\n")
        
        # 获取任务信息
        with app.app_context():
            task = ScrapingTask.query.filter_by(id=1579).first()
            if not task:
                print("❌ 任务1579不存在")
                return
            
            print(f"📋 任务信息:")
            print(f"   - ID: {task.id}")
            print(f"   - 名称: {task.name}")
            print(f"   - 目标账号: {task.target_accounts}")
            print(f"   - 最大推文数: {task.max_tweets}")
            print(f"   - 最小点赞数: {task.min_likes}")
            print(f"   - 最小转发数: {task.min_retweets}")
            print(f"   - 最小评论数: {task.min_comments}")
            print(f"   - 状态: {task.status}")
            print()
        
        # 启动AdsPower浏览器
        user_id = ADSPOWER_CONFIG['user_ids'][0]
        print(f"🚀 启动AdsPower浏览器，用户ID: {user_id}")
        
        launcher = AdsPowerLauncher(ADSPOWER_CONFIG)
        browser_info = launcher.start_browser(user_id)
        
        if not browser_info:
            print("❌ AdsPower浏览器启动失败")
            return
        
        debug_port = browser_info.get('ws', {}).get('puppeteer')
        print(f"✅ 浏览器启动成功，调试端口: {debug_port}")
        print()
        
        # 连接Twitter解析器
        print(f"🔗 连接Twitter解析器...")
        parser = TwitterParser(debug_port)
        await parser.connect_browser()
        print(f"✅ Twitter解析器连接成功")
        print()
        
        # 导航到0xluffy_eth用户主页
        username = '0xluffy_eth'
        print(f"🌐 导航到 @{username} 用户主页...")
        await parser.navigate_to_profile(username)
        print(f"✅ 成功导航到 @{username} 用户主页")
        print()
        
        # 检查页面状态
        current_url = parser.page.url
        print(f"📍 当前页面URL: {current_url}")
        
        # 等待页面加载
        print(f"⏳ 等待页面完全加载...")
        await asyncio.sleep(3)
        
        # 检查是否有推文元素
        tweet_elements = await parser.page.query_selector_all('[data-testid="tweet"]')
        print(f"📊 页面推文元素数量: {len(tweet_elements)}")
        
        if len(tweet_elements) == 0:
            print("⚠️ 页面没有找到推文元素，可能的原因:")
            print("   - 用户不存在或被封禁")
            print("   - 用户设置了隐私保护")
            print("   - 页面加载不完整")
            print("   - 需要登录才能查看")
            
            # 检查页面内容
            page_text = await parser.page.text_content('body')
            if 'This account doesn\'t exist' in page_text:
                print("❌ 用户不存在")
            elif 'protected' in page_text.lower():
                print("🔒 用户账号受保护")
            elif 'suspended' in page_text.lower():
                print("🚫 用户账号被暂停")
            else:
                print(f"📄 页面内容片段: {page_text[:200]}...")
            
            return
        
        print(f"✅ 找到 {len(tweet_elements)} 个推文元素")
        print()
        
        # 尝试抓取推文
        print(f"📱 开始抓取推文（目标: 5条用于测试）...")
        
        # 构建筛选条件
        filter_criteria = {
            'min_likes': 0,
            'min_comments': 0,
            'min_retweets': 0
        }
        
        tweets = await parser.scrape_tweets(
            max_tweets=5,
            enable_enhanced=False,
            filter_criteria=filter_criteria
        )
        
        print(f"📊 抓取结果: {len(tweets)} 条推文")
        print()
        
        if tweets:
            print(f"📝 推文详情:")
            for i, tweet in enumerate(tweets, 1):
                print(f"   推文 {i}:")
                print(f"     - 用户: {tweet.get('username', 'N/A')}")
                print(f"     - 内容: {tweet.get('content', 'N/A')[:100]}...")
                print(f"     - 点赞: {tweet.get('likes', 0)}")
                print(f"     - 转发: {tweet.get('retweets', 0)}")
                print(f"     - 评论: {tweet.get('comments', 0)}")
                print(f"     - 链接: {tweet.get('link', 'N/A')}")
                print()
        else:
            print(f"❌ 没有抓取到任何推文")
            print(f"   可能的原因:")
            print(f"   1. 推文解析逻辑有问题")
            print(f"   2. 页面结构发生变化")
            print(f"   3. 推文内容被过滤掉")
            print(f"   4. 网络或加载问题")
        
        # 测试更宽松的筛选条件
        if len(tweets) == 0:
            print(f"\n🔄 尝试更宽松的抓取策略...")
            
            # 直接解析当前页面的推文元素
            manual_tweets = []
            for i, element in enumerate(tweet_elements[:3]):  # 只测试前3个
                try:
                    tweet_data = await parser.parse_tweet_element(element)
                    if tweet_data:
                        manual_tweets.append(tweet_data)
                        print(f"   手动解析推文 {i+1}: @{tweet_data.get('username', 'N/A')} - {tweet_data.get('content', 'N/A')[:50]}...")
                except Exception as e:
                    print(f"   手动解析推文 {i+1} 失败: {e}")
            
            print(f"\n📊 手动解析结果: {len(manual_tweets)} 条推文")
        
        print(f"\n=== 调试完成 ===")
        
    except Exception as e:
        print(f"❌ 调试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_0xluffy_eth_scraping())