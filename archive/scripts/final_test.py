#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终验证测试 - MarketingWeekEd 100条推文
"""

import asyncio
import logging
import time
from twitter_parser import TwitterParser
from ads_browser_launcher import AdsPowerLauncher

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def final_test():
    """
    最终验证测试
    """
    start_time = time.time()
    adspower_manager = None
    parser = None
    
    try:
        print("\n" + "="*60)
        print("🚀 MarketingWeekEd 抓取修复最终验证")
        print("="*60)
        
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
        
        # 抓取100条推文
        target_username = "MarketingWeekEd"
        target_count = 100
        
        print(f"\n🎯 目标: 抓取 @{target_username} 的 {target_count} 条推文")
        print("-" * 40)
        
        tweets = await parser.scrape_user_tweets(
            username=target_username,
            max_tweets=target_count,
            enable_enhanced=False
        )
        
        # 计算结果
        actual_count = len(tweets)
        success_rate = actual_count / target_count * 100
        elapsed_time = time.time() - start_time
        
        print("\n" + "="*60)
        print("📊 抓取结果统计")
        print("="*60)
        print(f"🎯 目标数量: {target_count} 条")
        print(f"✅ 实际抓取: {actual_count} 条")
        print(f"📈 完成率: {success_rate:.1f}%")
        print(f"⏱️  耗时: {elapsed_time:.1f} 秒")
        
        # 质量分析
        valid_tweets = sum(1 for tweet in tweets if tweet.get('content') and len(tweet.get('content', '').strip()) > 10)
        quality_rate = valid_tweets / actual_count * 100 if actual_count > 0 else 0
        
        print(f"🔍 有效推文: {valid_tweets}/{actual_count} ({quality_rate:.1f}%)")
        
        # 显示样本
        print("\n📝 推文样本 (前3条):")
        print("-" * 40)
        for i, tweet in enumerate(tweets[:3], 1):
            username = tweet.get('username', 'unknown')
            content = tweet.get('content', '')[:80] + '...' if len(tweet.get('content', '')) > 80 else tweet.get('content', '')
            print(f"{i}. @{username}: {content}")
        
        # 判断成功标准
        print("\n" + "="*60)
        if success_rate >= 95:
            print("🎉 测试完全成功！修复效果优秀！")
            result = "完全成功"
        elif success_rate >= 90:
            print("✅ 测试基本成功！修复效果良好！")
            result = "基本成功"
        elif success_rate >= 80:
            print("⚠️ 测试部分成功，还有改进空间")
            result = "部分成功"
        else:
            print("❌ 测试失败，需要进一步优化")
            result = "失败"
        
        print(f"📋 测试结论: {result}")
        print("="*60)
        
        return success_rate >= 90
            
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # 清理资源
        if parser:
            try:
                await parser.close()
                print("🧹 解析器已关闭")
            except Exception:
                pass
        
        if adspower_manager:
            try:
                adspower_manager.stop_browser(user_id)
                print("🧹 浏览器已停止")
            except Exception:
                pass

if __name__ == "__main__":
    asyncio.run(final_test())