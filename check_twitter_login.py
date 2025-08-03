#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.ads_browser_launcher import AdsPowerLauncher
from core.twitter_parser import TwitterParser
from config.adspower_config import ADSPOWER_CONFIG

async def check_twitter_login_status():
    """检查Twitter登录状态"""
    try:
        print("=== 检查Twitter登录状态 ===\n")
        
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
        
        # 导航到Twitter主页
        print(f"🌐 导航到Twitter主页...")
        await parser.navigate_to_twitter()
        print(f"✅ 成功导航到Twitter主页")
        print()
        
        # 检查当前页面URL
        current_url = parser.page.url
        print(f"📍 当前页面URL: {current_url}")
        
        # 等待页面加载
        await asyncio.sleep(3)
        
        # 检查登录状态
        print(f"🔍 检查登录状态...")
        
        # 方法1: 检查是否有登录按钮
        login_button = await parser.page.query_selector('a[href="/login"]')
        if login_button:
            print("❌ 未登录 - 发现登录按钮")
            login_status = False
        else:
            print("✅ 可能已登录 - 未发现登录按钮")
            login_status = True
        
        # 方法2: 检查是否有用户菜单
        user_menu = await parser.page.query_selector('[data-testid="SideNav_AccountSwitcher_Button"]')
        if user_menu:
            print("✅ 已登录 - 发现用户菜单")
            login_status = True
        else:
            print("❌ 未登录 - 未发现用户菜单")
            login_status = False
        
        # 方法3: 检查页面标题
        page_title = await parser.page.title()
        print(f"📄 页面标题: {page_title}")
        
        if 'login' in page_title.lower() or 'sign in' in page_title.lower():
            print("❌ 未登录 - 页面标题包含登录相关内容")
            login_status = False
        
        # 方法4: 检查页面内容
        page_text = await parser.page.text_content('body')
        if 'Sign in to X' in page_text or 'Log in to X' in page_text:
            print("❌ 未登录 - 页面包含登录提示")
            login_status = False
        elif 'Home' in page_text and 'Timeline' in page_text:
            print("✅ 已登录 - 页面包含主页内容")
            login_status = True
        
        print(f"\n📊 最终登录状态: {'已登录' if login_status else '未登录'}")
        
        if not login_status:
            print("\n💡 建议:")
            print("   1. 在AdsPower浏览器中手动登录Twitter")
            print("   2. 确保登录状态保持")
            print("   3. 重新运行抓取任务")
        else:
            print("\n🔄 测试访问受保护账号...")
            
            # 测试访问0xluffy_eth
            await parser.navigate_to_profile('0xluffy_eth')
            await asyncio.sleep(3)
            
            tweet_elements = await parser.page.query_selector_all('[data-testid="tweet"]')
            page_content = await parser.page.text_content('body')
            
            print(f"   - 推文元素数量: {len(tweet_elements)}")
            
            if 'protected' in page_content.lower():
                print("   - 账号仍然受保护，可能需要关注该用户")
            elif len(tweet_elements) > 0:
                print(f"   - ✅ 可以访问推文！找到 {len(tweet_elements)} 个推文元素")
            else:
                print("   - ❌ 仍然无法访问推文")
        
        print(f"\n=== 检查完成 ===")
        
    except Exception as e:
        print(f"❌ 检查过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_twitter_login_status())