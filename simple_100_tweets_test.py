#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版100条推文抓取测试
从上到下抓取100条内容，放宽验证条件
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any, List

from twitter_parser import TwitterParser
from ads_browser_launcher import AdsPowerLauncher
from config import ADS_POWER_CONFIG

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Simple100TweetsTester:
    """简化版100条推文测试器"""
    
    def __init__(self, target_count: int = 100):
        self.launcher = None
        self.parser = None
        self.scraped_tweets = []
        self.target_count = target_count
        
    async def scrape_100_tweets(self) -> List[Dict[str, Any]]:
        """抓取100条推文"""
        logger.info("🚀 开始抓取100条推文（简化版本）...")
        
        try:
            # 启动浏览器
            self.launcher = AdsPowerLauncher(config=ADS_POWER_CONFIG)
            browser_info = self.launcher.start_browser()
            
            if not browser_info:
                logger.error("浏览器启动失败")
                return []
            
            # 创建解析器
            debug_url = browser_info.get('ws', {}).get('puppeteer', '')
            if not debug_url:
                logger.error("无法获取调试端口")
                return []
            
            self.parser = TwitterParser(debug_port=debug_url)
            
            # 初始化解析器
            await self.parser.initialize()
            logger.info("✅ 浏览器连接成功")
            
            # 导航到目标页面
            try:
                await self.parser.navigate_to_profile('elonmusk')
                logger.info("✅ 导航到 elonmusk 页面成功")
            except Exception as e:
                logger.error(f"导航失败: {e}")
                return []
            
            # 启用优化功能
            self.parser.optimization_enabled = True
            logger.info(f"优化功能状态: {self.parser.optimization_enabled}")
            
            # 使用简化的抓取策略
            tweets = await self.simple_scrape_strategy()
            
            logger.info(f"✅ 抓取完成，共获得 {len(tweets)} 条推文 (目标: {self.target_count})")
            return tweets
                
        except Exception as e:
            logger.error(f"抓取过程异常: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    async def simple_scrape_strategy(self) -> List[Dict[str, Any]]:
        """简化的抓取策略"""
        tweets = []
        scroll_count = 0
        no_new_tweets_count = 0  # 连续没有新推文的次数
        
        logger.info("开始简化抓取策略...")
        
        # 先等待页面初始加载
        try:
            await asyncio.sleep(3)  # 给页面更多时间加载
            logger.info("页面初始加载等待完成")
        except:
            pass
        
        while len(tweets) < self.target_count:
            try:
                # 不等待网络空闲，直接查找元素
                logger.info(f"第 {scroll_count + 1} 次尝试，当前推文数: {len(tweets)}/{self.target_count}")
                
                # 查找推文元素
                tweet_elements = await self.parser.page.query_selector_all('[data-testid="tweet"]')
                logger.info(f"第 {scroll_count + 1} 次滚动，找到 {len(tweet_elements)} 个推文元素")
                
                # 如果没有找到推文元素，尝试其他选择器
                if not tweet_elements:
                    alternative_selectors = [
                        'article[data-testid="tweet"]',
                        '[data-testid="cellInnerDiv"]',
                        'div[data-testid="tweet"]'
                    ]
                    
                    for selector in alternative_selectors:
                        tweet_elements = await self.parser.page.query_selector_all(selector)
                        if tweet_elements:
                            logger.info(f"使用备用选择器 '{selector}' 找到 {len(tweet_elements)} 个元素")
                            break
                
                # 记录解析前的推文数量
                tweets_before = len(tweets)
                
                # 解析推文元素
                for element in tweet_elements:
                    if len(tweets) >= self.target_count:
                        break
                    
                    try:
                        # 使用简化的解析方法
                        tweet_data = await self.simple_parse_tweet(element)
                        if tweet_data:
                            # 检查是否重复
                            link = tweet_data.get('link', '')
                            if link and not any(t.get('link') == link for t in tweets):
                                tweets.append(tweet_data)
                                logger.info(f"成功解析第 {len(tweets)} 条推文: {tweet_data.get('username', 'unknown')}")
                    
                    except Exception as e:
                        logger.debug(f"解析单条推文失败: {e}")
                        continue
                
                # 检查是否有新推文
                new_tweets_count = len(tweets) - tweets_before
                if new_tweets_count == 0:
                    no_new_tweets_count += 1
                    logger.warning(f"本次滚动没有获得新推文，连续 {no_new_tweets_count} 次")
                else:
                    no_new_tweets_count = 0  # 重置计数器
                
                # 检查是否达到目标或需要停止
                if len(tweets) >= self.target_count:
                    logger.info(f"✅ 已达到目标推文数量: {len(tweets)}/{self.target_count}")
                    break
                
                # 如果连续多次没有新推文，停止滚动（放宽条件）
                if no_new_tweets_count >= 8:  # 增加到8次，给更多机会
                    logger.warning(f"连续 {no_new_tweets_count} 次滚动都没有新推文，停止抓取")
                    break
                
                # 滚动页面（增加滚动距离）
                await self.parser.page.evaluate('window.scrollBy(0, 1500)')  # 增加滚动距离
                await asyncio.sleep(4)  # 增加等待时间
                scroll_count += 1
                logger.info(f"已滚动 {scroll_count} 次，当前推文数: {len(tweets)}/{self.target_count}")
                
                # 每10次滚动后额外等待，让页面充分加载
                if scroll_count % 10 == 0:
                    logger.info(f"第 {scroll_count} 次滚动，额外等待页面加载...")
                    await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"滚动过程异常: {e}")
                break
        
        logger.info(f"抓取策略完成，共获得 {len(tweets)} 条推文")
        return tweets
    
    async def simple_parse_tweet(self, element) -> Dict[str, Any]:
        """简化的推文解析方法"""
        try:
            # 提取用户名
            username = 'unknown'
            try:
                username_element = await element.query_selector('[data-testid="User-Name"] span')
                if username_element:
                    username_text = await username_element.text_content()
                    if username_text:
                        username = username_text.strip().split()[0]  # 取第一个词
            except:
                pass
            
            # 提取内容
            content = 'No content available'
            try:
                content_element = await element.query_selector('[data-testid="tweetText"]')
                if content_element:
                    content_text = await content_element.text_content()
                    if content_text:
                        content = content_text.strip()
            except:
                pass
            
            # 提取链接
            link = ''
            try:
                link_element = await element.query_selector('a[href*="/status/"]')
                if link_element:
                    href = await link_element.get_attribute('href')
                    if href:
                        if href.startswith('/'):
                            link = f'https://x.com{href}'
                        else:
                            link = href
            except:
                pass
            
            # 提取时间
            publish_time = ''
            try:
                time_element = await element.query_selector('time')
                if time_element:
                    datetime_attr = await time_element.get_attribute('datetime')
                    if datetime_attr:
                        publish_time = datetime_attr
            except:
                pass
            
            # 提取互动数据（简化版本）
            likes = 0
            comments = 0
            retweets = 0
            
            try:
                # 查找点赞数
                like_element = await element.query_selector('[data-testid="like"]')
                if like_element:
                    like_text = await like_element.text_content()
                    if like_text and any(c.isdigit() for c in like_text):
                        import re
                        numbers = re.findall(r'[\d,]+', like_text)
                        if numbers:
                            likes = int(numbers[0].replace(',', ''))
            except:
                pass
            
            # 构建推文数据
            tweet_data = {
                'username': username,
                'content': content,
                'publish_time': publish_time,
                'link': link,
                'likes': likes,
                'comments': comments,
                'retweets': retweets,
                'media': {'images': [], 'videos': []},
                'post_type': '纯文本'
            }
            
            # 简化的验证：只要有用户名或内容或链接就认为有效
            if (username and username != 'unknown') or \
               (content and content != 'No content available') or \
               (link and link.strip()):
                return tweet_data
            
            return None
            
        except Exception as e:
            logger.debug(f"简化解析推文失败: {e}")
            return None
    
    async def cleanup(self):
        """清理资源"""
        try:
            if self.parser:
                await self.parser.close()
            if self.launcher:
                self.launcher.stop_browser()
            logger.info("🧹 资源清理完成")
        except Exception as e:
            logger.error(f"清理资源失败: {e}")
    
    def save_results(self, tweets: List[Dict[str, Any]]):
        """保存结果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'simple_100_tweets_{timestamp}.json'
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'target_tweets': 100,
            'actual_tweets': len(tweets),
            'success': len(tweets) > 0,
            'tweets': tweets
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"📄 结果已保存到: {filename}")
        except Exception as e:
            logger.error(f"保存结果失败: {e}")

async def main(target_count: int = 100):
    """主函数"""
    tester = Simple100TweetsTester(target_count)
    
    try:
        # 抓取100条推文
        tweets = await tester.scrape_100_tweets()
        
        # 保存结果
        tester.save_results(tweets)
        
        # 打印摘要
        print("\n" + "="*50)
        print("📊 简化版推文抓取摘要")
        print("="*50)
        print(f"目标推文数: {tester.target_count}")
        print(f"实际抓取数: {len(tweets)}")
        print(f"完成率: {len(tweets)/tester.target_count*100:.1f}%")
        print(f"抓取状态: {'✅ 成功' if len(tweets) > 0 else '❌ 失败'}")
        
        if tweets:
            print(f"\n📝 前3条推文预览:")
            for i, tweet in enumerate(tweets[:3], 1):
                print(f"  {i}. {tweet.get('username', 'unknown')}: {tweet.get('content', 'No content')[:50]}...")
        
        print("="*50)
        
    except Exception as e:
        logger.error(f"主程序异常: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    finally:
        await tester.cleanup()

if __name__ == '__main__':
    import sys
    
    # 支持命令行参数指定目标数量
    target_count = 100
    if len(sys.argv) > 1:
        try:
            target_count = int(sys.argv[1])
            print(f"📋 设置目标推文数量: {target_count}")
        except ValueError:
            print("⚠️ 无效的目标数量参数，使用默认值 100")
    
    asyncio.run(main(target_count))