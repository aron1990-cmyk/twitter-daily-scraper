#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试推文内容提取问题
分析为什么某些推文无法提取文本内容
"""

import asyncio
import logging
import sys
import os
from playwright.async_api import async_playwright

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ads_browser_launcher import AdsPowerLauncher

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

async def debug_tweet_content_extraction():
    """调试推文内容提取"""
    launcher = None
    
    try:
        # 启动浏览器
        logger.info("🚀 启动浏览器...")
        launcher = AdsPowerLauncher(ADS_POWER_CONFIG)
        browser_info = launcher.start_browser()
        launcher.wait_for_browser_ready()
        debug_port = launcher.get_debug_port()
        logger.info(f"✅ 浏览器启动成功，调试端口: {debug_port}")
        
        async with async_playwright() as p:
            logger.info(f"连接到浏览器: {debug_port}")
            browser = await p.chromium.connect_over_cdp(debug_port)
            
            # 获取现有上下文和页面
            contexts = browser.contexts
            if not contexts:
                logger.error("没有找到浏览器上下文")
                return
            
            context = contexts[0]
            pages = context.pages
            if not pages:
                logger.error("没有找到页面")
                return
            
            page = pages[0]
            current_url = page.url
            logger.info(f"📍 当前页面: {current_url}")
            
            # 如果不在Twitter页面，导航到Elon Musk页面
            if 'elonmusk' not in current_url:
                logger.info("🔄 导航到@elonmusk页面...")
                await page.goto('https://x.com/elonmusk', wait_until='domcontentloaded')
                await asyncio.sleep(10)
                logger.info("✅ 已导航到@elonmusk页面")
            
            # 等待页面完全加载
            logger.info("⏳ 等待页面完全加载...")
            await asyncio.sleep(5)
            
            # 获取所有推文元素
            tweet_elements = await page.query_selector_all('[data-testid="tweet"]')
            logger.info(f"📊 找到 {len(tweet_elements)} 个推文元素")
            
            if len(tweet_elements) == 0:
                logger.warning("❌ 未找到推文元素")
                return
            
            # 分析每个推文元素
            for i, tweet_element in enumerate(tweet_elements[:5]):  # 只分析前5个
                logger.info(f"\n🔍 分析推文 {i+1}:")
                
                try:
                    # 检查元素是否可见
                    is_visible = await tweet_element.is_visible()
                    logger.info(f"  元素可见性: {is_visible}")
                    
                    # 获取元素的HTML结构
                    element_html = await tweet_element.inner_html()
                    logger.info(f"  HTML长度: {len(element_html)} 字符")
                    
                    # 测试各种内容选择器
                    content_selectors = [
                        '[data-testid="tweetText"]',
                        '[data-testid="tweetText"] span',
                        'div[lang] span',
                        'div[dir="auto"] span',
                        'div[dir="ltr"] span',
                        'div[dir="rtl"] span',
                        '[lang] span',
                        'span[dir="auto"]',
                        'div[data-testid="tweetText"] > span',
                        'article div[lang] span',
                        'article span[dir]',
                        # 新增更多选择器
                        'div[data-testid="tweetText"] div',
                        'div[data-testid="tweetText"] *',
                        '[data-testid="tweetText"] div[dir]',
                        '[data-testid="tweetText"] span[dir]',
                        'span[lang]',
                        'div[lang]'
                    ]
                    
                    found_content = False
                    
                    for j, selector in enumerate(content_selectors):
                        try:
                            content_elements = await tweet_element.query_selector_all(selector)
                            if content_elements:
                                # 收集所有文本内容
                                text_parts = []
                                for elem in content_elements:
                                    text = await elem.inner_text()
                                    if text and text.strip():
                                        text_parts.append(text.strip())
                                
                                if text_parts:
                                    content_text = ' '.join(text_parts)
                                    logger.info(f"  ✅ 选择器 {j+1} '{selector}': 找到内容")
                                    logger.info(f"     内容: {content_text[:100]}...")
                                    found_content = True
                                    break
                                else:
                                    logger.debug(f"  ⚪ 选择器 {j+1} '{selector}': 找到元素但无文本")
                            else:
                                logger.debug(f"  ❌ 选择器 {j+1} '{selector}': 未找到元素")
                        except Exception as e:
                            logger.debug(f"  ⚠️ 选择器 {j+1} '{selector}': 测试失败 - {e}")
                    
                    # 如果所有选择器都失败，尝试获取整个推文的文本
                    if not found_content:
                        logger.info(f"  🔄 所有内容选择器失败，尝试获取整个推文文本...")
                        try:
                            all_text = await tweet_element.inner_text()
                            if all_text:
                                logger.info(f"  📝 整个推文文本: {all_text[:200]}...")
                                
                                # 分析文本结构
                                lines = all_text.split('\n')
                                logger.info(f"  📋 文本行数: {len(lines)}")
                                
                                for line_idx, line in enumerate(lines[:10]):  # 只显示前10行
                                    line = line.strip()
                                    if line:
                                        logger.info(f"    行 {line_idx+1}: {line[:50]}...")
                                
                                # 尝试智能过滤内容
                                filtered_lines = []
                                for line in lines:
                                    line = line.strip()
                                    # 跳过空行、用户名、时间戳等
                                    if (line and 
                                        not line.startswith('@') and 
                                        not line.endswith('h') and 
                                        not line.endswith('m') and 
                                        not line.endswith('s') and
                                        not line.isdigit() and
                                        len(line) > 3 and
                                        not line in ['Like', 'Reply', 'Retweet', 'Share', 'View']):
                                        filtered_lines.append(line)
                                
                                if filtered_lines:
                                    filtered_content = ' '.join(filtered_lines[:3])
                                    logger.info(f"  ✅ 过滤后内容: {filtered_content[:100]}...")
                                else:
                                    logger.warning(f"  ⚠️ 过滤后无有效内容")
                            else:
                                logger.warning(f"  ❌ 整个推文元素无文本内容")
                        except Exception as e:
                            logger.warning(f"  ❌ 获取整个推文文本失败: {e}")
                    
                    # 检查推文的特殊类型
                    logger.info(f"  🔍 检查推文特殊类型...")
                    
                    # 检查是否是转发
                    retweet_indicators = [
                        '[data-testid="socialContext"]',
                        'span[data-testid="socialContext"]',
                        '[aria-label*="retweeted"]',
                        '[aria-label*="Retweeted"]'
                    ]
                    
                    for indicator in retweet_indicators:
                        try:
                            retweet_element = await tweet_element.query_selector(indicator)
                            if retweet_element:
                                retweet_text = await retweet_element.inner_text()
                                logger.info(f"    🔄 转发指示器: {retweet_text}")
                                break
                        except Exception:
                            continue
                    
                    # 检查是否是引用推文
                    quote_indicators = [
                        '[data-testid="quoteTweet"]',
                        'div[role="blockquote"]',
                        '[data-testid="card.wrapper"]'
                    ]
                    
                    for indicator in quote_indicators:
                        try:
                            quote_element = await tweet_element.query_selector(indicator)
                            if quote_element:
                                logger.info(f"    📝 发现引用推文元素")
                                break
                        except Exception:
                            continue
                    
                    # 检查是否只有媒体内容
                    media_indicators = [
                        '[data-testid="tweetPhoto"]',
                        '[data-testid="videoPlayer"]',
                        'img[alt*="Image"]',
                        'video'
                    ]
                    
                    media_found = False
                    for indicator in media_indicators:
                        try:
                            media_element = await tweet_element.query_selector(indicator)
                            if media_element:
                                logger.info(f"    🖼️ 发现媒体内容: {indicator}")
                                media_found = True
                        except Exception:
                            continue
                    
                    if media_found and not found_content:
                        logger.info(f"    💡 可能是纯媒体推文（无文字内容）")
                    
                except Exception as e:
                    logger.error(f"  ❌ 分析推文 {i+1} 失败: {e}")
            
            logger.info("\n✅ 推文内容提取调试完成")
            
    except Exception as e:
        logger.error(f"❌ 调试失败: {e}")
        
    finally:
        # 清理资源
        if launcher:
            try:
                launcher.stop_browser()
                logger.info("✅ 浏览器已关闭")
            except Exception as e:
                logger.warning(f"关闭浏览器时出错: {e}")

if __name__ == "__main__":
    asyncio.run(debug_tweet_content_extraction())