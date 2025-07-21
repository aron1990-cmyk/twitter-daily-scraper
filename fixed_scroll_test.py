#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复版本的滚动测试脚本
基于调试发现的问题进行修复
"""

import asyncio
import logging
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ads_browser_launcher import AdsPowerLauncher
from twitter_parser import TwitterParser

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# AdsPower配置
ADS_POWER_CONFIG = {
    'user_id': 'k11p9ypc',
    'open_tabs': 1,
    'launch_args': [],
    'headless': False,
    'disable_password_filling': False,
    'clear_cache_after_closing': False,
    'enable_password_saving': False
}

async def test_fixed_scroll():
    """测试修复后的滚动功能"""
    launcher = None
    parser = None
    
    try:
        # 启动浏览器
        logger.info("🚀 启动浏览器...")
        launcher = AdsPowerLauncher(ADS_POWER_CONFIG)
        browser_info = launcher.start_browser()
        launcher.wait_for_browser_ready()
        debug_port = launcher.get_debug_port()
        logger.info(f"✅ 浏览器启动成功，调试端口: {debug_port}")
        
        # 初始化TwitterParser
        logger.info("🔧 初始化TwitterParser...")
        parser = TwitterParser(debug_port=debug_port)
        await parser.initialize()
        logger.info("✅ TwitterParser初始化完成")
        
        # 导航到Elon Musk的页面（调试脚本显示这个页面有推文）
        logger.info("🔄 导航到@elonmusk页面...")
        try:
            await parser.navigate_to_profile('elonmusk')
            logger.info("✅ 成功导航到用户页面")
        except Exception as nav_error:
            logger.warning(f"导航失败: {nav_error}，尝试直接访问")
            await parser.page.goto('https://x.com/elonmusk', wait_until='domcontentloaded')
            await asyncio.sleep(5)
        
        # 等待页面完全加载
        logger.info("⏳ 等待页面完全加载...")
        await asyncio.sleep(10)
        
        # 检查初始推文数量
        initial_tweets = await parser.page.query_selector_all('[data-testid="tweet"]')
        logger.info(f"📊 初始推文数量: {len(initial_tweets)}")
        
        if len(initial_tweets) == 0:
            logger.warning("⚠️ 未检测到初始推文，可能需要更长等待时间")
            await asyncio.sleep(10)
            initial_tweets = await parser.page.query_selector_all('[data-testid="tweet"]')
            logger.info(f"📊 重新检查推文数量: {len(initial_tweets)}")
        
        # 如果仍然没有推文，尝试滚动一下激活页面
        if len(initial_tweets) == 0:
            logger.info("🔄 尝试滚动激活页面...")
            await parser.page.evaluate('window.scrollBy(0, 500)')
            await asyncio.sleep(3)
            await parser.page.evaluate('window.scrollBy(0, -500)')
            await asyncio.sleep(3)
            initial_tweets = await parser.page.query_selector_all('[data-testid="tweet"]')
            logger.info(f"📊 滚动后推文数量: {len(initial_tweets)}")
        
        # 测试修复后的滚动功能
        target_tweets = 20
        logger.info(f"🎯 开始测试滚动加载，目标: {target_tweets} 条推文")
        
        # 使用修复后的滚动逻辑
        scroll_attempts = 0
        max_scroll_attempts = 10
        last_tweet_count = len(initial_tweets)
        stagnant_count = 0
        
        while scroll_attempts < max_scroll_attempts:
            # 获取当前推文数量
            current_tweets = await parser.page.query_selector_all('[data-testid="tweet"]')
            current_count = len(current_tweets)
            
            logger.info(f"📈 滚动尝试 {scroll_attempts + 1}/{max_scroll_attempts}，当前推文: {current_count}")
            
            # 检查是否达到目标
            if current_count >= target_tweets:
                logger.info(f"🎉 达到目标推文数量: {current_count}/{target_tweets}")
                break
            
            # 检查是否有新推文加载
            if current_count == last_tweet_count:
                stagnant_count += 1
                logger.info(f"⏸️ 推文数量未增加，停滞次数: {stagnant_count}")
            else:
                stagnant_count = 0
                logger.info(f"📈 新增推文: {current_count - last_tweet_count}")
            
            last_tweet_count = current_count
            
            # 如果连续停滞太多次，停止滚动
            if stagnant_count >= 5:
                logger.warning("⚠️ 连续多次无新推文，停止滚动")
                break
            
            # 执行滚动
            scroll_distance = 1000 if stagnant_count < 3 else 2000
            logger.info(f"📜 滚动距离: {scroll_distance}px")
            
            await parser.page.evaluate(f'window.scrollBy(0, {scroll_distance})')
            
            # 等待内容加载
            wait_time = 2 if stagnant_count < 3 else 4
            await asyncio.sleep(wait_time)
            
            scroll_attempts += 1
        
        # 最终统计
        final_tweets = await parser.page.query_selector_all('[data-testid="tweet"]')
        final_count = len(final_tweets)
        
        logger.info(f"\n📊 测试结果总结:")
        logger.info(f"  初始推文数量: {len(initial_tweets)}")
        logger.info(f"  最终推文数量: {final_count}")
        logger.info(f"  新增推文数量: {final_count - len(initial_tweets)}")
        logger.info(f"  滚动次数: {scroll_attempts}")
        logger.info(f"  目标完成度: {final_count}/{target_tweets} ({final_count/target_tweets*100:.1f}%)")
        
        # 测试推文内容提取
        if final_count > 0:
            logger.info(f"\n🔍 测试推文内容提取（前3条）:")
            for i, tweet_element in enumerate(final_tweets[:3]):
                try:
                    # 提取推文文本
                    text_element = await tweet_element.query_selector('[data-testid="tweetText"]')
                    if text_element:
                        text_content = await text_element.inner_text()
                        logger.info(f"  推文 {i+1}: {text_content[:100]}...")
                    else:
                        logger.info(f"  推文 {i+1}: 无法提取文本内容")
                except Exception as e:
                    logger.warning(f"  推文 {i+1}: 提取失败 - {e}")
        
        if final_count >= target_tweets * 0.8:
            logger.info("✅ 滚动测试成功！")
        else:
            logger.warning("⚠️ 滚动测试部分成功，但未达到预期目标")
            
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        
    finally:
        # 清理资源
        if parser:
            try:
                await parser.close()
                logger.info("✅ TwitterParser已关闭")
            except Exception as e:
                logger.warning(f"关闭TwitterParser时出错: {e}")
        
        if launcher:
            try:
                launcher.stop_browser()
                logger.info("✅ 浏览器已关闭")
            except Exception as e:
                logger.warning(f"关闭浏览器时出错: {e}")

if __name__ == "__main__":
    asyncio.run(test_fixed_scroll())