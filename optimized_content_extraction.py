#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化的推文内容提取
解决推文内容重复和格式问题
"""

import asyncio
import logging
import sys
import os
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any

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

class OptimizedContentExtractor:
    """优化的推文内容提取器"""
    
    def __init__(self, parser: TwitterParser):
        self.parser = parser
        self.logger = logging.getLogger(__name__)
    
    def clean_tweet_content(self, content: str) -> str:
        """清理推文内容，去除重复和格式问题"""
        if not content:
            return ""
        
        # 去除多余的空白字符
        content = re.sub(r'\s+', ' ', content.strip())
        
        # 去除重复的用户名模式 (如: "Elon Musk Elon Musk @elonmusk")
        content = re.sub(r'(\w+\s+\w+)\s+\1', r'\1', content)
        
        # 去除重复的数字模式 (如: "4,8K 4,8K 4,8K")
        content = re.sub(r'(\d+[,.]?\d*[KMB]?)\s+\1(\s+\1)*', r'\1', content)
        
        # 去除重复的符号模式
        content = re.sub(r'(·\s*)+', '· ', content)
        
        # 去除末尾的统计数据模式
        content = re.sub(r'\s*·\s*[\d,KMB.\s]+$', '', content)
        
        # 去除开头的用户名重复
        content = re.sub(r'^(@?\w+\s+){2,}', '', content)
        
        # 去除多余的点和空格
        content = re.sub(r'\s*·\s*$', '', content)
        
        return content.strip()
    
    def extract_clean_username(self, element) -> str:
        """提取干净的用户名"""
        try:
            # 尝试多种选择器
            username_selectors = [
                '[data-testid="User-Name"] [dir="ltr"]',
                '[data-testid="User-Name"] span',
                'a[href^="/"][role="link"] span',
                '[dir="ltr"] span'
            ]
            
            for selector in username_selectors:
                username_element = element.query_selector(selector)
                if username_element:
                    username = username_element.text_content().strip()
                    # 清理用户名
                    username = re.sub(r'^@', '', username)
                    username = re.sub(r'\s.*', '', username)  # 只保留第一个词
                    if username and not re.match(r'^\d+[KMB]?$', username):
                        return username
            
            # 从链接中提取用户名
            link_element = element.query_selector('a[href^="/"][role="link"]')
            if link_element:
                href = link_element.get_attribute('href')
                if href:
                    match = re.match(r'^/([^/]+)', href)
                    if match:
                        return match.group(1)
            
            return 'unknown'
            
        except Exception as e:
            self.logger.debug(f"提取用户名失败: {e}")
            return 'unknown'
    
    def extract_clean_content(self, element) -> str:
        """提取干净的推文内容"""
        try:
            # 尝试多种内容选择器
            content_selectors = [
                '[data-testid="tweetText"]',
                '[lang] span',
                'div[dir="auto"] span'
            ]
            
            content_parts = []
            
            for selector in content_selectors:
                content_elements = element.query_selector_all(selector)
                for content_element in content_elements:
                    text = content_element.text_content().strip()
                    if text and text not in content_parts:
                        content_parts.append(text)
            
            # 合并内容
            raw_content = ' '.join(content_parts)
            
            # 清理内容
            clean_content = self.clean_tweet_content(raw_content)
            
            return clean_content if clean_content else 'No content available'
            
        except Exception as e:
            self.logger.debug(f"提取推文内容失败: {e}")
            return 'No content available'
    
    def extract_engagement_data(self, element) -> Dict[str, int]:
        """提取互动数据"""
        engagement = {'likes': 0, 'comments': 0, 'retweets': 0}
        
        try:
            # 查找互动数据
            engagement_selectors = {
                'likes': ['[data-testid="like"]', '[aria-label*="like"]'],
                'comments': ['[data-testid="reply"]', '[aria-label*="repl"]'],
                'retweets': ['[data-testid="retweet"]', '[aria-label*="repost"]']
            }
            
            for metric, selectors in engagement_selectors.items():
                for selector in selectors:
                    metric_element = element.query_selector(selector)
                    if metric_element:
                        # 查找数字
                        text = metric_element.text_content()
                        numbers = re.findall(r'[\d,]+[KMB]?', text)
                        if numbers:
                            engagement[metric] = self.parse_number(numbers[0])
                            break
            
            return engagement
            
        except Exception as e:
            self.logger.debug(f"提取互动数据失败: {e}")
            return engagement
    
    def parse_number(self, num_str: str) -> int:
        """解析数字字符串 (如: 1.2K -> 1200)"""
        try:
            num_str = num_str.replace(',', '')
            if num_str.endswith('K'):
                return int(float(num_str[:-1]) * 1000)
            elif num_str.endswith('M'):
                return int(float(num_str[:-1]) * 1000000)
            elif num_str.endswith('B'):
                return int(float(num_str[:-1]) * 1000000000)
            else:
                return int(num_str)
        except (ValueError, IndexError):
            return 0
    
    def extract_media_content(self, element) -> Dict[str, List[Dict]]:
        """提取媒体内容"""
        media = {'images': [], 'videos': []}
        
        try:
            # 提取图片
            img_elements = element.query_selector_all('img[src*="pbs.twimg.com"]')
            for img in img_elements:
                src = img.get_attribute('src')
                alt = img.get_attribute('alt') or 'Image'
                if src:
                    media['images'].append({
                        'type': 'image',
                        'url': src,
                        'description': alt,
                        'original_url': src
                    })
            
            # 提取视频
            video_elements = element.query_selector_all('video, [data-testid="videoPlayer"]')
            for video in video_elements:
                poster = video.get_attribute('poster')
                if poster:
                    media['videos'].append({
                        'type': 'video',
                        'poster': poster,
                        'description': 'Video content'
                    })
            
            return media
            
        except Exception as e:
            self.logger.debug(f"提取媒体内容失败: {e}")
            return media
    
    async def parse_tweet_element_optimized(self, element) -> Optional[Dict[str, Any]]:
        """优化的推文元素解析"""
        try:
            # 提取基本信息
            username = self.extract_clean_username(element)
            content = self.extract_clean_content(element)
            
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
            except Exception:
                pass
            
            # 提取时间
            publish_time = ''
            try:
                time_element = await element.query_selector('time')
                if time_element:
                    datetime_attr = await time_element.get_attribute('datetime')
                    if datetime_attr:
                        publish_time = datetime_attr
            except Exception:
                pass
            
            # 提取互动数据
            engagement = self.extract_engagement_data(element)
            
            # 提取媒体内容
            media = self.extract_media_content(element)
            
            # 确定帖子类型
            post_type = '纯文本'
            if media['images']:
                post_type = '图文'
            elif media['videos']:
                post_type = '视频'
            
            # 构建推文数据
            tweet_data = {
                'username': username,
                'content': content,
                'publish_time': publish_time,
                'link': link,
                'likes': engagement['likes'],
                'comments': engagement['comments'],
                'retweets': engagement['retweets'],
                'media': media,
                'post_type': post_type
            }
            
            # 验证数据有效性
            if username != 'unknown' and (content != 'No content available' or media['images'] or media['videos']):
                return tweet_data
            
            return None
            
        except Exception as e:
            self.logger.debug(f"解析推文元素失败: {e}")
            return None

async def test_optimized_content_extraction():
    """测试优化的内容提取"""
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
        
        # 导航到测试页面
        logger.info("🔄 导航到@elonmusk页面...")
        try:
            await parser.navigate_to_profile('elonmusk')
        except Exception:
            await parser.page.goto('https://x.com/elonmusk', wait_until='domcontentloaded')
        
        await asyncio.sleep(5)
        
        # 创建优化内容提取器
        extractor = OptimizedContentExtractor(parser)
        
        # 获取推文元素
        logger.info("🔍 获取推文元素...")
        await parser.page.wait_for_selector('[data-testid="tweet"]', timeout=10000)
        tweet_elements = await parser.page.query_selector_all('[data-testid="tweet"]')
        
        logger.info(f"📊 找到 {len(tweet_elements)} 个推文元素")
        
        # 对比测试：原始解析 vs 优化解析
        original_tweets = []
        optimized_tweets = []
        
        for i, element in enumerate(tweet_elements[:5]):  # 测试前5条
            logger.info(f"\n🔍 测试推文 {i+1}:")
            
            # 原始解析
            try:
                original_tweet = await parser.parse_tweet_element(element)
                original_tweets.append(original_tweet)
                logger.info(f"  📝 原始内容: {original_tweet.get('content', 'N/A')[:100]}...")
            except Exception as e:
                logger.warning(f"  ❌ 原始解析失败: {e}")
                original_tweets.append(None)
            
            # 优化解析
            try:
                optimized_tweet = await extractor.parse_tweet_element_optimized(element)
                optimized_tweets.append(optimized_tweet)
                if optimized_tweet:
                    logger.info(f"  ✨ 优化内容: {optimized_tweet.get('content', 'N/A')[:100]}...")
                    logger.info(f"  👤 用户名: {optimized_tweet.get('username', 'N/A')}")
                    logger.info(f"  💖 互动: {optimized_tweet.get('likes', 0)} 赞, {optimized_tweet.get('comments', 0)} 评论")
                else:
                    logger.warning("  ❌ 优化解析返回空结果")
            except Exception as e:
                logger.warning(f"  ❌ 优化解析失败: {e}")
                optimized_tweets.append(None)
        
        # 生成对比报告
        comparison_report = {
            'timestamp': datetime.now().isoformat(),
            'test_type': 'content_extraction_optimization',
            'total_tweets_tested': len(tweet_elements[:5]),
            'original_success_count': len([t for t in original_tweets if t]),
            'optimized_success_count': len([t for t in optimized_tweets if t]),
            'improvements': [],
            'original_tweets': original_tweets,
            'optimized_tweets': optimized_tweets
        }
        
        # 分析改进
        for i, (orig, opt) in enumerate(zip(original_tweets, optimized_tweets)):
            if orig and opt:
                improvement = {
                    'tweet_index': i + 1,
                    'content_length_change': len(opt.get('content', '')) - len(orig.get('content', '')),
                    'content_cleaned': orig.get('content', '') != opt.get('content', ''),
                    'username_improved': orig.get('username', 'unknown') != opt.get('username', 'unknown'),
                    'engagement_data_complete': all([
                        opt.get('likes', 0) > 0,
                        opt.get('comments', 0) >= 0,
                        opt.get('retweets', 0) >= 0
                    ])
                }
                comparison_report['improvements'].append(improvement)
        
        # 保存对比报告
        report_file = f"content_extraction_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(comparison_report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n💾 对比报告已保存到: {report_file}")
        
        # 输出测试结果
        logger.info("\n📊 内容提取优化测试结果:")
        logger.info(f"  🎯 测试推文数量: {comparison_report['total_tweets_tested']}")
        logger.info(f"  ✅ 原始解析成功: {comparison_report['original_success_count']}")
        logger.info(f"  🚀 优化解析成功: {comparison_report['optimized_success_count']}")
        
        # 计算改进指标
        content_improvements = sum(1 for imp in comparison_report['improvements'] if imp['content_cleaned'])
        username_improvements = sum(1 for imp in comparison_report['improvements'] if imp['username_improved'])
        engagement_complete = sum(1 for imp in comparison_report['improvements'] if imp['engagement_data_complete'])
        
        logger.info(f"  🧹 内容清理改进: {content_improvements}/{len(comparison_report['improvements'])}")
        logger.info(f"  👤 用户名提取改进: {username_improvements}/{len(comparison_report['improvements'])}")
        logger.info(f"  💖 完整互动数据: {engagement_complete}/{len(comparison_report['improvements'])}")
        
        # 评估优化效果
        total_improvements = content_improvements + username_improvements + engagement_complete
        max_possible_improvements = len(comparison_report['improvements']) * 3
        
        if max_possible_improvements > 0:
            improvement_rate = total_improvements / max_possible_improvements
            logger.info(f"  📈 总体改进率: {improvement_rate:.1%}")
            
            if improvement_rate >= 0.7:
                logger.info("🎉 内容提取优化效果显著！")
                return True
            elif improvement_rate >= 0.4:
                logger.info("✅ 内容提取优化有效果")
                return True
            else:
                logger.warning("⚠️ 内容提取优化效果有限")
                return False
        else:
            logger.warning("⚠️ 无法评估优化效果")
            return False
            
    except Exception as e:
        logger.error(f"❌ 内容提取优化测试失败: {e}")
        return False
        
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
    success = asyncio.run(test_optimized_content_extraction())
    if success:
        logger.info("\n🎊 内容提取优化测试成功！")
    else:
        logger.error("\n💥 内容提取优化测试失败")
        sys.exit(1)