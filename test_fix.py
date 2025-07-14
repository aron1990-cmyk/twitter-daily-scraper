#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的TwitterParser
"""

import asyncio
import logging
from ads_browser_launcher import AdsPowerLauncher
from twitter_parser import TwitterParser

class TestFix:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    async def test_single_user_scraping(self):
        """
        测试单个用户抓取功能
        """
        browser_manager = None
        parser = None
        
        try:
            print("🧪 开始测试修复后的TwitterParser")
            print("📱 测试目标: @elonmusk")
            
            # 启动浏览器
            browser_manager = AdsPowerLauncher()
            user_id = "k11p9ypc"
            
            print(f"🚀 启动浏览器 (用户ID: {user_id})...")
            browser_info = browser_manager.start_browser(user_id)
            
            if not browser_info:
                print("❌ 浏览器启动失败")
                return False
                
            debug_port = browser_info.get('ws', {}).get('puppeteer')
            
            if not debug_port:
                print("❌ 浏览器启动失败")
                return False
                
            print(f"✅ 浏览器启动成功，调试端口: {debug_port}")
            
            # 连接解析器
            parser = TwitterParser(debug_port)
            await parser.connect_browser()
            print("🔗 解析器连接成功")
            
            # 导航到Twitter
            await parser.navigate_to_twitter()
            print("🐦 已导航到Twitter")
            
            # 抓取推文
            print("📱 开始抓取 @elonmusk 的推文...")
            tweets = await parser.scrape_user_tweets('elonmusk', max_tweets=3)
            
            print(f"\n📊 抓取结果:")
            print(f"✅ 成功抓取 {len(tweets)} 条推文")
            
            for i, tweet in enumerate(tweets, 1):
                print(f"\n📝 推文 {i}:")
                print(f"   👤 用户: @{tweet.get('username', 'unknown')}")
                print(f"   📄 内容: {tweet.get('content', '')[:100]}...")
                print(f"   👍 点赞: {tweet.get('likes', 0)}")
                print(f"   💬 评论: {tweet.get('comments', 0)}")
                print(f"   🔄 转发: {tweet.get('retweets', 0)}")
            
            return len(tweets) > 0
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            self.logger.error(f"测试失败: {e}", exc_info=True)
            return False
            
        finally:
            # 清理资源
            if parser:
                try:
                    await parser.close()
                    print("🔒 解析器已关闭")
                except Exception as e:
                    print(f"⚠️ 关闭解析器失败: {e}")
            
            if browser_manager:
                try:
                    browser_manager.stop_browser(user_id)
                    print("🛑 浏览器已停止")
                except Exception as e:
                    print(f"⚠️ 停止浏览器失败: {e}")

async def main():
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    test = TestFix()
    success = await test.test_single_user_scraping()
    
    if success:
        print("\n🎉 测试成功！修复生效")
    else:
        print("\n❌ 测试失败，需要进一步调试")

if __name__ == "__main__":
    asyncio.run(main())