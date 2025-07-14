#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可视化演示脚本 - 在AdsPower浏览器中显示操作过程
"""

import asyncio
import logging
import time
from ads_browser_launcher import AdsPowerLauncher
from twitter_parser import TwitterParser

class VisualDemo:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    async def visual_scraping_demo(self):
        """
        可视化抓取演示 - 在浏览器中显示操作过程
        """
        browser_manager = None
        parser = None
        
        try:
            print("🎬 开始可视化Twitter抓取演示")
            print("👀 请观察AdsPower浏览器窗口中的操作过程")
            print("📱 演示目标: @elonmusk")
            
            # 启动浏览器
            browser_manager = AdsPowerLauncher()
            user_id = "k11p9ypc"
            
            print(f"\n🚀 启动浏览器 (用户ID: {user_id})...")
            browser_info = browser_manager.start_browser(user_id)
            
            if not browser_info:
                print("❌ 浏览器启动失败")
                return False
                
            debug_port = browser_info.get('ws', {}).get('puppeteer')
            print(f"✅ 浏览器启动成功")
            print(f"🔗 调试端口: {debug_port}")
            
            # 等待用户观察浏览器窗口
            print("\n⏳ 等待5秒，请观察AdsPower浏览器窗口...")
            await asyncio.sleep(5)
            
            # 连接解析器
            parser = TwitterParser(debug_port)
            await parser.connect_browser()
            print("🔗 解析器连接成功")
            
            # 导航到Twitter
            print("\n🐦 导航到Twitter主页...")
            await parser.navigate_to_twitter()
            print("✅ 已到达Twitter主页")
            
            # 等待用户观察
            print("\n⏳ 等待3秒，观察页面加载...")
            await asyncio.sleep(3)
            
            # 显示当前页面信息
            current_url = await parser.page.url()
            print(f"📍 当前页面: {current_url}")
            
            # 导航到用户页面
            print(f"\n👤 导航到 @elonmusk 的个人页面...")
            await parser.navigate_to_profile('elonmusk')
            print("✅ 已到达用户个人页面")
            
            # 等待用户观察
            print("\n⏳ 等待5秒，观察个人页面...")
            await asyncio.sleep(5)
            
            # 显示页面滚动过程
            print("\n📜 开始滚动页面加载更多推文...")
            print("👀 请观察浏览器中的滚动操作")
            
            # 执行可见的滚动操作
            for i in range(3):
                print(f"⬇️ 执行第 {i+1} 次滚动...")
                await parser.page.evaluate("window.scrollBy(0, 800)")
                await asyncio.sleep(2)  # 让用户看到滚动效果
                
            print("✅ 滚动完成")
            
            # 抓取推文
            print("\n📱 开始抓取推文...")
            print("👀 请观察浏览器中的推文解析过程")
            
            tweets = await parser.scrape_tweets(max_tweets=3)
            
            print(f"\n📊 抓取结果展示:")
            print(f"✅ 成功抓取 {len(tweets)} 条推文")
            
            for i, tweet in enumerate(tweets, 1):
                print(f"\n📝 推文 {i}:")
                print(f"   👤 用户: @{tweet.get('username', 'unknown')}")
                print(f"   📄 内容: {tweet.get('content', '')[:100]}...")
                print(f"   👍 点赞: {tweet.get('likes', 0)}")
                print(f"   💬 评论: {tweet.get('comments', 0)}")
                print(f"   🔄 转发: {tweet.get('retweets', 0)}")
            
            # 演示结束提示
            print("\n🎉 演示完成！")
            print("⏳ 浏览器窗口将在10秒后关闭...")
            await asyncio.sleep(10)
            
            return len(tweets) > 0
            
        except Exception as e:
            print(f"❌ 演示失败: {e}")
            self.logger.error(f"演示失败: {e}", exc_info=True)
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

    async def interactive_demo(self):
        """
        交互式演示 - 需要用户确认每个步骤
        """
        browser_manager = None
        parser = None
        
        try:
            print("🎬 交互式Twitter抓取演示")
            print("👀 每个步骤都需要您的确认")
            print("📱 演示目标: @elonmusk")
            
            input("\n按回车键开始演示...")
            
            # 启动浏览器
            browser_manager = AdsPowerLauncher()
            user_id = "k11p9ypc"
            
            print(f"\n🚀 启动浏览器 (用户ID: {user_id})...")
            browser_info = browser_manager.start_browser(user_id)
            
            if not browser_info:
                print("❌ 浏览器启动失败")
                return False
                
            debug_port = browser_info.get('ws', {}).get('puppeteer')
            print(f"✅ 浏览器启动成功")
            
            input("\n请观察AdsPower浏览器窗口，然后按回车继续...")
            
            # 连接解析器
            parser = TwitterParser(debug_port)
            await parser.connect_browser()
            print("🔗 解析器连接成功")
            
            input("\n按回车开始导航到Twitter...")
            
            # 导航到Twitter
            await parser.navigate_to_twitter()
            print("✅ 已到达Twitter主页")
            
            input("\n观察Twitter主页，然后按回车继续...")
            
            # 导航到用户页面
            print(f"\n👤 导航到 @elonmusk 的个人页面...")
            await parser.navigate_to_profile('elonmusk')
            print("✅ 已到达用户个人页面")
            
            input("\n观察用户个人页面，然后按回车开始抓取...")
            
            # 抓取推文
            print("\n📱 开始抓取推文...")
            tweets = await parser.scrape_tweets(max_tweets=3)
            
            print(f"\n📊 抓取结果:")
            print(f"✅ 成功抓取 {len(tweets)} 条推文")
            
            for i, tweet in enumerate(tweets, 1):
                print(f"\n📝 推文 {i}:")
                print(f"   👤 用户: @{tweet.get('username', 'unknown')}")
                print(f"   📄 内容: {tweet.get('content', '')[:100]}...")
                print(f"   👍 点赞: {tweet.get('likes', 0)}")
                print(f"   💬 评论: {tweet.get('comments', 0)}")
                print(f"   🔄 转发: {tweet.get('retweets', 0)}")
            
            input("\n演示完成！按回车关闭浏览器...")
            
            return len(tweets) > 0
            
        except Exception as e:
            print(f"❌ 演示失败: {e}")
            self.logger.error(f"演示失败: {e}", exc_info=True)
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
    
    demo = VisualDemo()
    
    print("🎬 Twitter抓取可视化演示")
    print("=" * 50)
    print("1. 自动演示 (自动执行所有步骤)")
    print("2. 交互式演示 (需要确认每个步骤)")
    
    choice = input("\n请选择演示模式 (1/2): ").strip()
    
    if choice == "1":
        success = await demo.visual_scraping_demo()
    elif choice == "2":
        success = await demo.interactive_demo()
    else:
        print("❌ 无效选择")
        return
    
    if success:
        print("\n🎉 演示成功完成！")
    else:
        print("\n❌ 演示失败")

if __name__ == "__main__":
    asyncio.run(main())