#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.twitter_parser import TwitterParser
from config.adspower_config import ADSPOWER_CONFIG
from utils.ads_browser_launcher import AdsPowerLauncher

async def test_scrape_0xluffy_eth():
    """测试抓取0xluffy_eth的推文"""
    try:
        print("=== 开始测试抓取0xluffy_eth ===\n")
        
        # 初始化浏览器启动器
        user_id = ADSPOWER_CONFIG['user_ids'][0]
        print(f"1. 启动AdsPower浏览器，用户ID: {user_id}")
        
        launcher = AdsPowerLauncher()
        browser_info = launcher.start_browser(user_id)
        
        if not launcher.wait_for_browser_ready():
            raise Exception("浏览器启动超时")
        
        debug_port = launcher.get_debug_port()
        if not debug_port:
            raise Exception("无法获取浏览器调试端口")
        
        print(f"2. 获取调试端口: {debug_port}")
        
        # 初始化解析器
        parser = TwitterParser()
        await parser.initialize(debug_port)
        print("✅ TwitterParser初始化成功\n")
        
        # 导航到用户页面
        username = '0xluffy_eth'
        print(f"3. 导航到用户页面: @{username}")
        await parser.navigate_to_profile(username)
        print("✅ 导航到用户页面成功\n")
        
        # 获取页面URL确认
        current_url = parser.page.url
        print(f"4. 当前页面URL: {current_url}")
        
        # 检查页面是否有推文元素
        tweet_elements = await parser.page.query_selector_all('[data-testid="tweet"]')
        print(f"5. 页面推文元素数量: {len(tweet_elements)}")
        
        if len(tweet_elements) == 0:
            print("⚠️ 页面没有找到推文元素，可能的原因:")
            print("   - 用户不存在或被封禁")
            print("   - 用户设置了隐私保护")
            print("   - 页面加载不完整")
            print("   - 需要登录才能查看")
            
            # 检查页面是否显示错误信息
            error_selectors = [
                '[data-testid="error-detail"]',
                '[data-testid="emptyState"]',
                'text="This account doesn\'t exist"',
                'text="Account suspended"',
                'text="Protected account"'
            ]
            
            for selector in error_selectors:
                try:
                    error_element = await parser.page.query_selector(selector)
                    if error_element:
                        error_text = await error_element.text_content()
                        print(f"   - 发现错误信息: {error_text}")
                        break
                except:
                    continue
        
        # 尝试抓取推文
        print(f"\n6. 开始抓取推文（目标: 5条）")
        tweets = await parser.scrape_tweets(max_tweets=5)
        print(f"✅ 抓取完成，获得推文数量: {len(tweets)}\n")
        
        # 显示抓取结果
        if tweets:
            print("7. 抓取到的推文详情:")
            for i, tweet in enumerate(tweets, 1):
                print(f"   推文{i}:")
                print(f"     用户: {tweet.get('username', 'unknown')}")
                print(f"     点赞: {tweet.get('likes', 0)}")
                print(f"     转发: {tweet.get('retweets', 0)}")
                print(f"     评论: {tweet.get('comments', 0)}")
                print(f"     内容: {tweet.get('content', '')[:100]}...")
                print(f"     链接: {tweet.get('link', 'N/A')}")
                print()
        else:
            print("7. ❌ 没有抓取到任何推文")
            print("   可能的原因:")
            print("   - 用户没有发布推文")
            print("   - 推文不满足筛选条件")
            print("   - 页面解析失败")
            print("   - 网络或浏览器问题")
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_scrape_0xluffy_eth())