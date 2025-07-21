#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的推文解析逻辑
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from twitter_parser import TwitterParser
from config import BROWSER_CONFIG

async def test_parsing_fix():
    """测试修复后的推文解析逻辑"""
    
    parser = None
    try:
        print("🔧 开始测试修复后的推文解析逻辑...")
        
        # 初始化 TwitterParser，使用正确的debug_port URL格式
        parser = TwitterParser(debug_port="http://localhost:9222")
        await parser.initialize()
        print("✅ TwitterParser 初始化成功")
        
        # 导航到 neilpatel 的个人资料页面
        print("📍 导航到 @neilpatel 的个人资料页面...")
        await parser.navigate_to_profile('neilpatel')
        print("✅ 导航成功")
        
        # 等待页面加载
        await asyncio.sleep(3)
        
        # 查找推文元素
        print("🔍 查找推文元素...")
        tweet_elements = await parser.page.query_selector_all('article[role="article"]')
        print(f"找到 {len(tweet_elements)} 个推文元素")
        
        if not tweet_elements:
            print("❌ 没有找到推文元素")
            return
        
        # 测试解析前3个推文
        successful_parses = 0
        for i, tweet_element in enumerate(tweet_elements[:3]):
            print(f"\n📝 解析第 {i+1} 个推文元素...")
            
            try:
                tweet_data = await parser.parse_tweet_element(tweet_element)
                
                if tweet_data:
                    successful_parses += 1
                    print(f"✅ 解析成功:")
                    print(f"   用户名: @{tweet_data.get('username', 'unknown')}")
                    print(f"   内容长度: {len(tweet_data.get('content', ''))} 字符")
                    print(f"   内容预览: {tweet_data.get('content', '')[:100]}...")
                    print(f"   链接: {tweet_data.get('link', 'None')}")
                    print(f"   点赞数: {tweet_data.get('likes', 0)}")
                    print(f"   评论数: {tweet_data.get('comments', 0)}")
                    print(f"   转发数: {tweet_data.get('retweets', 0)}")
                else:
                    print(f"❌ 解析失败: 返回 None")
                    
            except Exception as e:
                print(f"❌ 解析第 {i+1} 个推文元素时出错: {e}")
        
        print(f"\n📊 测试结果: 成功解析 {successful_parses}/3 个推文")
        
        if successful_parses > 0:
            print("🎉 推文解析修复成功！")
        else:
            print("⚠️  推文解析仍有问题，需要进一步调试")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if parser:
            try:
                await parser.close()
                print("✅ TwitterParser 已关闭")
            except Exception as e:
                print(f"⚠️  关闭 TwitterParser 时出错: {e}")

if __name__ == "__main__":
    asyncio.run(test_parsing_fix())