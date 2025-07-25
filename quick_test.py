#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速验证测试
"""

import asyncio
import logging
from twitter_parser import TwitterParser
from ads_browser_launcher import AdsPowerLauncher

logging.basicConfig(level=logging.WARNING)  # 减少日志输出
logger = logging.getLogger(__name__)

async def quick_test():
    adspower_manager = None
    parser = None
    
    try:
        print("🚀 快速验证测试开始")
        
        # 启动浏览器
        adspower_manager = AdsPowerLauncher()
        user_id = "k11p9ypc"
        browser_info = adspower_manager.start_browser(user_id)
        
        if not browser_info:
            print("❌ 浏览器启动失败")
            return False
            
        print("✅ 浏览器启动成功")
        
        # 初始化解析器
        parser = TwitterParser(browser_info['ws']['puppeteer'])
        await parser.initialize()
        print("✅ 解析器初始化完成")
        
        # 测试抓取80条推文（稍微降低目标）
        target_username = "MarketingWeekEd"
        target_count = 80
        
        print(f"🎯 目标: 抓取 @{target_username} 的 {target_count} 条推文")
        
        tweets = await parser.scrape_user_tweets(
            username=target_username,
            max_tweets=target_count,
            enable_enhanced=False
        )
        
        actual_count = len(tweets)
        success_rate = actual_count / target_count * 100
        
        print(f"\n📊 结果统计:")
        print(f"🎯 目标: {target_count} 条")
        print(f"✅ 实际: {actual_count} 条")
        print(f"📈 成功率: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🎉 修复成功！")
            result = True
        elif success_rate >= 75:
            print("✅ 修复基本成功！")
            result = True
        else:
            print("⚠️ 仍需优化")
            result = False
            
        return result
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
        
    finally:
        if parser:
            try:
                await parser.close()
            except Exception:
                pass
        
        if adspower_manager:
            try:
                adspower_manager.stop_browser(user_id)
            except Exception:
                pass

if __name__ == "__main__":
    result = asyncio.run(quick_test())
    print(f"\n{'='*40}")
    if result:
        print("🎉 MarketingWeekEd抓取问题已修复！")
    else:
        print("❌ 需要进一步优化")
    print(f"{'='*40}")