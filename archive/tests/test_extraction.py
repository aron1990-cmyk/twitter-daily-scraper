#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试改进后的统计数据提取功能
"""

import asyncio
import json
from twitter_parser import TwitterParser
from ads_browser_launcher import AdsPowerLauncher

async def test_extraction():
    """测试统计数据提取"""
    launcher = None
    parser = None
    try:
        print("🔧 启动浏览器...")
        launcher = AdsPowerLauncher()
        browser_info = launcher.start_browser('k11p9ypc')
        
        # 获取调试端口
        debug_port = browser_info.get('ws', {}).get('puppeteer')
        if not debug_port:
            raise Exception("无法获取浏览器调试端口")
        
        print(f"🔧 获取到调试端口: {debug_port}")
        
        print("🔧 创建解析器...")
        parser = TwitterParser()
        await parser.initialize(debug_port)
        
        print("🔧 访问Twitter页面...")
        await parser.navigate_to_profile('elonmusk')
        await asyncio.sleep(5)
        
        print("🔧 查找推文元素...")
        tweets = await parser.page.query_selector_all('[data-testid="tweet"]')
        print(f"找到 {len(tweets)} 个推文元素")
        
        if tweets:
            print("🔧 解析第一个推文...")
            result = await parser.parse_tweet_element(tweets[0])
            
            if result:
                print("\n✅ 解析结果:")
                print(json.dumps(result, ensure_ascii=False, indent=2))
                
                # 检查统计数据
                likes = result.get('likes', 0)
                comments = result.get('comments', 0)
                retweets = result.get('retweets', 0)
                
                print(f"\n📊 统计数据:")
                print(f"  点赞数: {likes}")
                print(f"  评论数: {comments}")
                print(f"  转发数: {retweets}")
                
                if likes > 0 or comments > 0 or retweets > 0:
                    print("\n🎉 统计数据提取成功！")
                else:
                    print("\n⚠️ 统计数据仍为零，可能需要进一步调试")
            else:
                print("❌ 解析失败")
        else:
            print("❌ 未找到推文元素")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if parser and parser.browser:
            print("🔧 关闭解析器...")
            await parser.browser.close()
        if launcher:
            print("🔧 关闭浏览器...")
            launcher.stop_browser()

if __name__ == '__main__':
    asyncio.run(test_extraction())