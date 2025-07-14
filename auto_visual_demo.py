#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动可视化演示脚本 - 在AdsPower浏览器中显示操作过程
无需用户交互，自动执行所有步骤
"""

import asyncio
import logging
import time
from ads_browser_launcher import AdsPowerLauncher
from twitter_parser import TwitterParser

class AutoVisualDemo:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    async def run_demo(self):
        """
        自动可视化抓取演示 - 在浏览器中显示操作过程
        """
        browser_manager = None
        parser = None
        
        try:
            print("🎬 自动可视化Twitter抓取演示")
            print("👀 请观察AdsPower浏览器窗口中的操作过程")
            print("📱 演示目标: @elonmusk")
            print("⚡ 完全自动化，无需用户交互")
            
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
            for i in range(5, 0, -1):
                print(f"⏰ {i} 秒后开始连接...")
                await asyncio.sleep(1)
            
            # 连接解析器
            print("\n🔗 连接到浏览器...")
            parser = TwitterParser(debug_port)
            await parser.connect_browser()
            print("✅ 解析器连接成功")
            
            # 导航到Twitter
            print("\n🐦 导航到Twitter主页...")
            await parser.navigate_to_twitter()
            print("✅ 已到达Twitter主页")
            
            # 等待用户观察
            print("\n⏳ 等待3秒，观察页面加载...")
            await asyncio.sleep(3)
            
            # 显示当前页面信息
            current_url = parser.page.url
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
            
            # 滚动回顶部
            print("\n⬆️ 滚动回顶部...")
            await parser.page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(2)
            
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
            
            # 演示其他操作
            print("\n🎯 演示其他浏览器操作...")
            
            # 模拟点击操作
            print("🖱️ 模拟鼠标移动...")
            await parser.page.mouse.move(400, 300)
            await asyncio.sleep(1)
            
            # 模拟滚动到不同位置
            print("📜 模拟页面浏览...")
            for scroll_pos in [500, 1000, 1500, 0]:
                await parser.page.evaluate(f"window.scrollTo(0, {scroll_pos})")
                await asyncio.sleep(1.5)
            
            # 演示结束提示
            print("\n🎉 演示完成！")
            print("📊 演示统计:")
            print(f"   🔢 抓取推文数: {len(tweets)}")
            print(f"   ⏱️ 演示时长: 约60秒")
            print(f"   🎯 演示操作: 导航、滚动、抓取、解析")
            
            print("\n🔄 浏览器将保持打开状态")
            print("💡 您可以继续在AdsPower浏览器中进行操作")
            print("🛑 如需关闭，请手动停止脚本 (Ctrl+C)")
            
            # 保持脚本运行，不自动关闭浏览器
            print("\n⏳ 脚本将保持运行状态，按 Ctrl+C 停止...")
            try:
                while True:
                    await asyncio.sleep(10)
                    print("💤 脚本运行中... (浏览器保持打开)")
            except KeyboardInterrupt:
                print("\n🛑 收到停止信号，开始清理资源...")
            
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
                    print("\n❓ 是否关闭AdsPower浏览器？")
                    print("💡 浏览器将保持打开状态，您可以继续使用")
                    print("🔧 如需关闭浏览器，请手动在AdsPower中操作")
                    # 不自动关闭浏览器，让用户手动控制
                    # browser_manager.stop_browser(user_id)
                    print("✅ 脚本已完成，浏览器保持运行")
                except Exception as e:
                    print(f"⚠️ 处理浏览器状态失败: {e}")

async def main():
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🎬 自动可视化Twitter抓取演示")
    print("=" * 50)
    print("🚀 即将开始自动演示")
    print("👀 请准备观察AdsPower浏览器窗口")
    print("⚡ 演示将完全自动化进行")
    
    # 倒计时
    print("\n⏳ 3秒后开始演示...")
    for i in range(3, 0, -1):
        print(f"🕐 倒计时: {i} 秒")
        await asyncio.sleep(1)
    
    demo = AutoVisualDemo()
    success = await demo.run_demo()
    
    if success:
        print("\n🎉 演示成功完成！")
        print("💡 您已经看到了完整的Twitter抓取过程")
    else:
        print("\n❌ 演示失败")

if __name__ == "__main__":
    asyncio.run(main())