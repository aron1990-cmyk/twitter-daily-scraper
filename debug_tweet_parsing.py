#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试推文解析过程
"""

import asyncio
import json
from playwright.async_api import async_playwright

async def debug_tweet_parsing():
    """调试推文解析过程"""
    
    async with async_playwright() as p:
        try:
            # 连接到现有浏览器实例
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            
            # 获取第一个页面
            pages = await browser.contexts[0].pages
            if not pages:
                print("❌ 没有找到打开的页面")
                return
                
            page = pages[0]
            current_url = page.url
            print(f"📍 当前页面: {current_url}")
            
            # 检查页面标题
            title = await page.title()
            print(f"📄 页面标题: {title}")
            
            # 查找推文元素
            print("\n🔍 查找推文元素...")
            tweet_elements = await page.query_selector_all('article[role="article"]')
            print(f"找到 {len(tweet_elements)} 个推文元素")
            
            if not tweet_elements:
                print("❌ 没有找到推文元素")
                return
            
            # 详细分析前3个推文元素
            for i, tweet_element in enumerate(tweet_elements[:3]):
                print(f"\n📝 分析第 {i+1} 个推文元素:")
                
                try:
                    # 检查元素是否可见
                    is_visible = await tweet_element.is_visible()
                    print(f"  可见性: {is_visible}")
                    
                    # 获取元素的HTML内容（截取前500字符）
                    html_content = await tweet_element.inner_html()
                    print(f"  HTML长度: {len(html_content)} 字符")
                    print(f"  HTML预览: {html_content[:200]}...")
                    
                    # 尝试提取用户名
                    username_selectors = [
                        '[data-testid="User-Name"] a',
                        '[data-testid="User-Names"] a', 
                        'a[href^="/"][role="link"]'
                    ]
                    
                    username = None
                    for selector in username_selectors:
                        try:
                            username_element = await tweet_element.query_selector(selector)
                            if username_element:
                                username_href = await username_element.get_attribute('href')
                                if username_href and '/' in username_href:
                                    username = username_href.split('/')[-1]
                                    print(f"  用户名: @{username} (使用选择器: {selector})")
                                    break
                        except Exception as e:
                            print(f"  用户名选择器 {selector} 失败: {e}")
                    
                    if not username:
                        print("  ❌ 未找到用户名")
                    
                    # 尝试提取推文内容
                    content_selectors = [
                        '[data-testid="tweetText"]',
                        '[lang] span',
                        'div[dir="auto"] span'
                    ]
                    
                    content = None
                    for selector in content_selectors:
                        try:
                            content_element = await tweet_element.query_selector(selector)
                            if content_element:
                                content_text = await content_element.inner_text()
                                if content_text and content_text.strip():
                                    content = content_text.strip()
                                    print(f"  内容: {content[:100]}... (使用选择器: {selector})")
                                    break
                        except Exception as e:
                            print(f"  内容选择器 {selector} 失败: {e}")
                    
                    if not content:
                        print("  ❌ 未找到推文内容")
                    
                    # 尝试提取时间
                    try:
                        time_element = await tweet_element.query_selector('time')
                        if time_element:
                            datetime_attr = await time_element.get_attribute('datetime')
                            print(f"  时间: {datetime_attr}")
                        else:
                            print("  ❌ 未找到时间元素")
                    except Exception as e:
                        print(f"  时间提取失败: {e}")
                    
                    # 尝试提取链接
                    try:
                        link_elements = await tweet_element.query_selector_all('a[href*="/status/"]')
                        if link_elements:
                            href = await link_elements[0].get_attribute('href')
                            if href:
                                if href.startswith('/'):
                                    link = f"https://x.com{href}"
                                else:
                                    link = href
                                print(f"  链接: {link}")
                        else:
                            print("  ❌ 未找到推文链接")
                    except Exception as e:
                        print(f"  链接提取失败: {e}")
                    
                    # 检查验证逻辑
                    if not content and (not username or username == 'unknown'):
                        print(f"  ⚠️  验证失败: 内容为空且用户名无效 (用户名: {username})")
                    else:
                        print(f"  ✅ 验证通过: 内容={bool(content)}, 用户名={username}")
                        
                except Exception as e:
                    print(f"  ❌ 分析第 {i+1} 个推文元素失败: {e}")
            
            print("\n🔍 检查页面是否需要登录...")
            login_indicators = [
                'text="Log in"',
                'text="Sign up"', 
                '[data-testid="loginButton"]',
                '[data-testid="signupButton"]'
            ]
            
            needs_login = False
            for indicator in login_indicators:
                try:
                    element = await page.query_selector(indicator)
                    if element:
                        needs_login = True
                        print(f"  发现登录指示器: {indicator}")
                        break
                except:
                    continue
            
            if not needs_login:
                print("  ✅ 页面不需要登录")
            else:
                print("  ❌ 页面需要登录")
                
        except Exception as e:
            print(f"❌ 调试失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_tweet_parsing())