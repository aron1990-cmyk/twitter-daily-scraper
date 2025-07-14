#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据提取模块 - 从Twitter页面中提取推文内容、用户信息和相关数据
支持多种数据格式提取、内容清理和数据验证
"""

import re
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from urllib.parse import urlparse, parse_qs
import html
from bs4 import BeautifulSoup

from exception_handler import (
    ParsingException, ValidationException, 
    handle_exception, retry_on_error
)
from browser_manager import BrowserInstance


@dataclass
class TweetData:
    """推文数据模型"""
    # 基本信息
    tweet_id: str
    user_id: str
    username: str
    display_name: str
    content: str
    
    # 时间信息
    created_at: datetime
    scraped_at: datetime = field(default_factory=datetime.now)
    
    # 互动数据
    likes_count: int = 0
    retweets_count: int = 0
    replies_count: int = 0
    quotes_count: int = 0
    views_count: int = 0
    
    # 媒体信息
    media_urls: List[str] = field(default_factory=list)
    media_types: List[str] = field(default_factory=list)
    
    # 链接信息
    urls: List[str] = field(default_factory=list)
    hashtags: List[str] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)
    
    # 推文类型
    is_retweet: bool = False
    is_reply: bool = False
    is_quote: bool = False
    is_thread: bool = False
    
    # 原始推文信息（如果是转推）
    original_tweet_id: Optional[str] = None
    original_user_id: Optional[str] = None
    original_username: Optional[str] = None
    
    # 回复信息
    reply_to_tweet_id: Optional[str] = None
    reply_to_user_id: Optional[str] = None
    reply_to_username: Optional[str] = None
    
    # 位置信息
    location: Optional[str] = None
    
    # 语言
    language: Optional[str] = None
    
    # 原始数据
    raw_html: Optional[str] = None
    raw_json: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 处理datetime对象
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data
    
    @property
    def engagement_rate(self) -> float:
        """互动率"""
        total_engagement = self.likes_count + self.retweets_count + self.replies_count
        if self.views_count > 0:
            return (total_engagement / self.views_count) * 100
        return 0.0
    
    @property
    def content_length(self) -> int:
        """内容长度"""
        return len(self.content)
    
    @property
    def has_media(self) -> bool:
        """是否包含媒体"""
        return len(self.media_urls) > 0
    
    @property
    def has_links(self) -> bool:
        """是否包含链接"""
        return len(self.urls) > 0


@dataclass
class UserData:
    """用户数据模型"""
    user_id: str
    username: str
    display_name: str
    bio: str = ""
    location: str = ""
    website: str = ""
    
    # 统计信息
    followers_count: int = 0
    following_count: int = 0
    tweets_count: int = 0
    likes_count: int = 0
    
    # 账号信息
    verified: bool = False
    protected: bool = False
    created_at: Optional[datetime] = None
    
    # 头像和背景
    profile_image_url: str = ""
    banner_image_url: str = ""
    
    # 抓取信息
    scraped_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 处理datetime对象
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data


class DataExtractor:
    """数据提取器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 编译正则表达式
        self.url_pattern = re.compile(r'https?://[^\s]+')
        self.hashtag_pattern = re.compile(r'#\w+')
        self.mention_pattern = re.compile(r'@\w+')
        self.tweet_id_pattern = re.compile(r'/status/(\d+)')
        self.user_id_pattern = re.compile(r'/user/(\d+)')
        
        # 时间格式
        self.time_formats = [
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%dT%H:%M:%SZ',
            '%a %b %d %H:%M:%S %z %Y',
        ]
    
    async def extract_tweets_from_page(self, browser_instance: BrowserInstance, 
                                     max_tweets: int = 50) -> List[TweetData]:
        """从页面提取推文数据"""
        try:
            tweets = []
            
            # 等待推文加载
            await browser_instance.page.wait_for_selector('[data-testid="tweet"]', timeout=10000)
            
            # 获取所有推文元素
            tweet_elements = await browser_instance.page.query_selector_all('[data-testid="tweet"]')
            
            self.logger.info(f"找到 {len(tweet_elements)} 个推文元素")
            
            for i, element in enumerate(tweet_elements[:max_tweets]):
                try:
                    tweet_data = await self._extract_single_tweet(browser_instance, element)
                    if tweet_data:
                        tweets.append(tweet_data)
                        self.logger.debug(f"提取推文 {i+1}: {tweet_data.tweet_id}")
                except Exception as e:
                    self.logger.warning(f"提取第 {i+1} 个推文失败: {e}")
                    continue
            
            self.logger.info(f"成功提取 {len(tweets)} 条推文")
            return tweets
            
        except Exception as e:
            self.logger.error(f"从页面提取推文失败: {e}")
            handle_exception(e, {"max_tweets": max_tweets})
            return []
    
    async def _extract_single_tweet(self, browser_instance: BrowserInstance, 
                                   tweet_element) -> Optional[TweetData]:
        """提取单条推文数据"""
        try:
            # 获取推文HTML
            tweet_html = await tweet_element.inner_html()
            
            # 使用BeautifulSoup解析
            soup = BeautifulSoup(tweet_html, 'html.parser')
            
            # 提取基本信息
            tweet_id = await self._extract_tweet_id(tweet_element)
            if not tweet_id:
                return None
            
            # 提取用户信息
            user_info = await self._extract_user_info(tweet_element)
            if not user_info:
                return None
            
            # 提取推文内容
            content = await self._extract_tweet_content(tweet_element)
            
            # 提取时间
            created_at = await self._extract_tweet_time(tweet_element)
            
            # 提取互动数据
            engagement = await self._extract_engagement_data(tweet_element)
            
            # 提取媒体信息
            media_info = await self._extract_media_info(tweet_element)
            
            # 提取链接、标签、提及
            links_info = await self._extract_links_info(content)
            
            # 检测推文类型
            tweet_type = await self._detect_tweet_type(tweet_element, content)
            
            # 创建推文数据对象
            tweet_data = TweetData(
                tweet_id=tweet_id,
                user_id=user_info.get('user_id', ''),
                username=user_info.get('username', ''),
                display_name=user_info.get('display_name', ''),
                content=content,
                created_at=created_at,
                
                # 互动数据
                likes_count=engagement.get('likes', 0),
                retweets_count=engagement.get('retweets', 0),
                replies_count=engagement.get('replies', 0),
                quotes_count=engagement.get('quotes', 0),
                views_count=engagement.get('views', 0),
                
                # 媒体信息
                media_urls=media_info.get('urls', []),
                media_types=media_info.get('types', []),
                
                # 链接信息
                urls=links_info.get('urls', []),
                hashtags=links_info.get('hashtags', []),
                mentions=links_info.get('mentions', []),
                
                # 推文类型
                is_retweet=tweet_type.get('is_retweet', False),
                is_reply=tweet_type.get('is_reply', False),
                is_quote=tweet_type.get('is_quote', False),
                is_thread=tweet_type.get('is_thread', False),
                
                # 原始数据
                raw_html=tweet_html
            )
            
            return tweet_data
            
        except Exception as e:
            self.logger.error(f"提取单条推文失败: {e}")
            return None
    
    async def _extract_tweet_id(self, tweet_element) -> Optional[str]:
        """提取推文ID"""
        try:
            # 查找包含推文链接的元素
            link_elements = await tweet_element.query_selector_all('a[href*="/status/"]')
            
            for link_element in link_elements:
                href = await link_element.get_attribute('href')
                if href:
                    match = self.tweet_id_pattern.search(href)
                    if match:
                        return match.group(1)
            
            return None
            
        except Exception as e:
            self.logger.debug(f"提取推文ID失败: {e}")
            return None
    
    async def _extract_user_info(self, tweet_element) -> Dict[str, str]:
        """提取用户信息"""
        try:
            user_info = {}
            
            # 提取用户名
            username_element = await tweet_element.query_selector('[data-testid="User-Name"] a')
            if username_element:
                href = await username_element.get_attribute('href')
                if href:
                    username = href.strip('/').split('/')[-1]
                    user_info['username'] = username
            
            # 提取显示名称
            display_name_element = await tweet_element.query_selector('[data-testid="User-Name"] span')
            if display_name_element:
                display_name = await display_name_element.inner_text()
                user_info['display_name'] = display_name.strip()
            
            return user_info
            
        except Exception as e:
            self.logger.debug(f"提取用户信息失败: {e}")
            return {}
    
    async def _extract_tweet_content(self, tweet_element) -> str:
        """提取推文内容"""
        try:
            # 查找推文文本元素
            content_element = await tweet_element.query_selector('[data-testid="tweetText"]')
            if content_element:
                content = await content_element.inner_text()
                return self._clean_text(content)
            
            return ""
            
        except Exception as e:
            self.logger.debug(f"提取推文内容失败: {e}")
            return ""
    
    async def _extract_tweet_time(self, tweet_element) -> datetime:
        """提取推文时间"""
        try:
            # 查找时间元素 - 使用多种选择器
            time_selectors = [
                'time',
                '[datetime]',
                'a[href*="/status/"] time',
                '[data-testid="Time"] time'
            ]
            
            for selector in time_selectors:
                try:
                    time_element = await tweet_element.query_selector(selector)
                    if time_element:
                        # 优先使用datetime属性
                        datetime_attr = await time_element.get_attribute('datetime')
                        if datetime_attr:
                            parsed_time = self._parse_datetime(datetime_attr)
                            if parsed_time is not None:
                                return parsed_time
                        
                        # 备用：使用title属性
                        title_attr = await time_element.get_attribute('title')
                        if title_attr:
                            parsed_time = self._parse_datetime(title_attr)
                            if parsed_time is not None:
                                return parsed_time
                        
                        # 备用：使用文本内容
                        time_text = await time_element.inner_text()
                        if time_text:
                            parsed_time = self._parse_relative_time(time_text)
                            if parsed_time:
                                return parsed_time
                except Exception:
                    continue
            
            # 如果没有找到时间，返回当前时间
            self.logger.warning("未能提取到推文时间，使用当前时间")
            return datetime.now(timezone.utc)
            
        except Exception as e:
            self.logger.debug(f"提取推文时间失败: {e}")
            return datetime.now(timezone.utc)
    
    async def _extract_engagement_data(self, tweet_element) -> Dict[str, int]:
        """提取互动数据"""
        try:
            engagement = {
                'likes': 0,
                'retweets': 0,
                'replies': 0,
                'quotes': 0,
                'views': 0
            }
            
            # 使用更精确的选择器提取点赞数
            like_selectors = [
                '[data-testid="like"]',
                '[aria-label*="like"]',
                '[aria-label*="Like"]',
                '[data-testid="heart"]'
            ]
            
            for selector in like_selectors:
                try:
                    like_element = await tweet_element.query_selector(selector)
                    if like_element:
                        like_text = await like_element.get_attribute('aria-label') or ''
                        if like_text:
                            engagement['likes'] = self._extract_count_from_label(like_text)
                            break
                except Exception:
                    continue
            
            # 提取评论数
            reply_selectors = [
                '[data-testid="reply"]',
                '[aria-label*="repl"]',
                '[aria-label*="Reply"]',
                '[aria-label*="comment"]'
            ]
            
            for selector in reply_selectors:
                try:
                    reply_element = await tweet_element.query_selector(selector)
                    if reply_element:
                        reply_text = await reply_element.get_attribute('aria-label') or ''
                        if reply_text:
                            engagement['replies'] = self._extract_count_from_label(reply_text)
                            break
                except Exception:
                    continue
            
            # 提取转发数
            retweet_selectors = [
                '[data-testid="retweet"]',
                '[aria-label*="retweet"]',
                '[aria-label*="Retweet"]',
                '[aria-label*="repost"]'
            ]
            
            for selector in retweet_selectors:
                try:
                    retweet_element = await tweet_element.query_selector(selector)
                    if retweet_element:
                        retweet_text = await retweet_element.get_attribute('aria-label') or ''
                        if retweet_text:
                            engagement['retweets'] = self._extract_count_from_label(retweet_text)
                            break
                except Exception:
                    continue
            
            # 提取引用数
            quote_selectors = [
                '[data-testid="quote"]',
                '[aria-label*="quote"]',
                '[aria-label*="Quote"]'
            ]
            
            for selector in quote_selectors:
                try:
                    quote_element = await tweet_element.query_selector(selector)
                    if quote_element:
                        quote_text = await quote_element.get_attribute('aria-label') or ''
                        if quote_text:
                            engagement['quotes'] = self._extract_count_from_label(quote_text)
                            break
                except Exception:
                    continue
            
            # 提取浏览量
            view_selectors = [
                '[aria-label*="view"]',
                '[aria-label*="View"]',
                '[data-testid="analytics"]'
            ]
            
            for selector in view_selectors:
                try:
                    view_element = await tweet_element.query_selector(selector)
                    if view_element:
                        view_text = await view_element.get_attribute('aria-label') or ''
                        if view_text and ('view' in view_text.lower()):
                            engagement['views'] = self._extract_count_from_label(view_text)
                            break
                except Exception:
                    continue
            
            # 备用方法：查找所有互动按钮
            if all(v == 0 for v in engagement.values()):
                action_buttons = await tweet_element.query_selector_all('[role="group"] [role="button"]')
                
                for button in action_buttons:
                    try:
                        aria_label = await button.get_attribute('aria-label')
                        if aria_label:
                            count = self._extract_count_from_label(aria_label)
                            aria_lower = aria_label.lower()
                            
                            if 'like' in aria_lower and engagement['likes'] == 0:
                                engagement['likes'] = count
                            elif ('retweet' in aria_lower or 'repost' in aria_lower) and engagement['retweets'] == 0:
                                engagement['retweets'] = count
                            elif 'repl' in aria_lower and engagement['replies'] == 0:
                                engagement['replies'] = count
                            elif 'quote' in aria_lower and engagement['quotes'] == 0:
                                engagement['quotes'] = count
                            elif 'view' in aria_lower and engagement['views'] == 0:
                                engagement['views'] = count
                    except Exception:
                        continue
            
            return engagement
            
        except Exception as e:
            self.logger.debug(f"提取互动数据失败: {e}")
            return {'likes': 0, 'retweets': 0, 'replies': 0, 'quotes': 0, 'views': 0}
    
    async def _extract_media_info(self, tweet_element) -> Dict[str, List[str]]:
        """提取媒体信息"""
        try:
            media_info = {'urls': [], 'types': []}
            
            # 查找图片 - 使用多种选择器
            image_selectors = [
                '[data-testid="tweetPhoto"] img',
                'img[src*="pbs.twimg.com"]',
                'div[data-testid="tweetPhoto"] img',
                '[data-testid="card.layoutLarge.media"] img',
                'img[alt*="Image"]'
            ]
            
            for selector in image_selectors:
                try:
                    img_elements = await tweet_element.query_selector_all(selector)
                    for img in img_elements:
                        src = await img.get_attribute('src')
                        if src and 'profile_images' not in src and src not in media_info['urls']:
                            # 获取高质量图片URL
                            if 'pbs.twimg.com' in src:
                                # 移除尺寸限制，获取原图
                                high_quality_src = src.split('?')[0] + '?format=jpg&name=large'
                                media_info['urls'].append(high_quality_src)
                            else:
                                media_info['urls'].append(src)
                            media_info['types'].append('image')
                except Exception:
                    continue
            
            # 查找视频
            video_selectors = [
                'video',
                '[data-testid="videoPlayer"] video',
                'div[data-testid="videoComponent"] video'
            ]
            
            for selector in video_selectors:
                try:
                    video_elements = await tweet_element.query_selector_all(selector)
                    for video in video_elements:
                        # 尝试获取视频源
                        src = await video.get_attribute('src')
                        if src and src not in media_info['urls']:
                            media_info['urls'].append(src)
                            media_info['types'].append('video')
                        
                        # 尝试获取poster图片
                        poster = await video.get_attribute('poster')
                        if poster and poster not in media_info['urls']:
                            media_info['urls'].append(poster)
                            media_info['types'].append('video_thumbnail')
                except Exception:
                    continue
            
            # 查找GIF
            gif_selectors = [
                'img[src*="tweet_video_thumb"]',
                '[data-testid="gif"] img'
            ]
            
            for selector in gif_selectors:
                try:
                    gif_elements = await tweet_element.query_selector_all(selector)
                    for gif in gif_elements:
                        src = await gif.get_attribute('src')
                        if src and src not in media_info['urls']:
                            media_info['urls'].append(src)
                            media_info['types'].append('gif')
                except Exception:
                    continue
            
            # 查找外部链接的预览图
            try:
                card_img_elements = await tweet_element.query_selector_all('[data-testid="card.layoutLarge.media"] img, [data-testid="card.layoutSmall.media"] img')
                for img in card_img_elements:
                    src = await img.get_attribute('src')
                    if src and src not in media_info['urls']:
                        media_info['urls'].append(src)
                        media_info['types'].append('link_preview')
            except Exception:
                pass
            
            return media_info
            
        except Exception as e:
            self.logger.debug(f"提取媒体信息失败: {e}")
            return {'urls': [], 'types': []}
    
    async def _extract_links_info(self, content: str) -> Dict[str, List[str]]:
        """提取链接、标签、提及信息"""
        try:
            links_info = {
                'urls': [],
                'hashtags': [],
                'mentions': []
            }
            
            # 提取URL
            urls = self.url_pattern.findall(content)
            links_info['urls'] = list(set(urls))  # 去重
            
            # 提取标签
            hashtags = self.hashtag_pattern.findall(content)
            links_info['hashtags'] = [tag[1:] for tag in set(hashtags)]  # 去掉#号并去重
            
            # 提取提及
            mentions = self.mention_pattern.findall(content)
            links_info['mentions'] = [mention[1:] for mention in set(mentions)]  # 去掉@号并去重
            
            return links_info
            
        except Exception as e:
            self.logger.debug(f"提取链接信息失败: {e}")
            return {'urls': [], 'hashtags': [], 'mentions': []}
    
    async def _detect_tweet_type(self, tweet_element, content: str) -> Dict[str, bool]:
        """检测推文类型"""
        try:
            tweet_type = {
                'is_retweet': False,
                'is_reply': False,
                'is_quote': False,
                'is_thread': False
            }
            
            # 检测转推
            retweet_indicator = await tweet_element.query_selector('[data-testid="socialContext"]')
            if retweet_indicator:
                text = await retweet_indicator.inner_text()
                if 'retweeted' in text.lower() or 'reposted' in text.lower():
                    tweet_type['is_retweet'] = True
            
            # 检测回复
            reply_indicator = await tweet_element.query_selector('[data-testid="reply"]')
            if reply_indicator or content.startswith('@'):
                tweet_type['is_reply'] = True
            
            # 检测引用推文
            quote_indicator = await tweet_element.query_selector('[data-testid="quoteTweet"]')
            if quote_indicator:
                tweet_type['is_quote'] = True
            
            # 检测推文串（简单检测）
            if '🧵' in content or 'thread' in content.lower() or '/1' in content:
                tweet_type['is_thread'] = True
            
            return tweet_type
            
        except Exception as e:
            self.logger.debug(f"检测推文类型失败: {e}")
            return {'is_retweet': False, 'is_reply': False, 'is_quote': False, 'is_thread': False}
    
    def _extract_count_from_label(self, label: str) -> int:
        """从aria-label中提取数量"""
        try:
            if not label:
                return 0
            
            # 移除逗号和空格
            label = label.replace(',', '').replace(' ', '').lower()
            
            # 提取数字和单位
            match = re.search(r'([0-9.]+)([km]?)', label)
            if not match:
                # 备用方法：直接查找数字
                numbers = re.findall(r'\d+', label)
                if numbers:
                    return int(numbers[0])
                return 0
            
            number = float(match.group(1))
            unit = match.group(2)
            
            if unit == 'k':
                return int(number * 1000)
            elif unit == 'm':
                return int(number * 1000000)
            else:
                return int(number)
                
        except Exception as e:
            self.logger.debug(f"解析数量失败: {label}, 错误: {e}")
            return 0
    
    def _parse_datetime(self, datetime_str: str) -> Optional[datetime]:
        """解析时间字符串"""
        if not datetime_str:
            return None
            
        # 清理时间字符串
        datetime_str = datetime_str.strip()
        
        # 扩展时间格式列表
        extended_formats = [
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%dT%H:%M:%S.%f%z',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%m/%d/%Y %H:%M:%S',
            '%m/%d/%Y %H:%M',
            '%d/%m/%Y %H:%M:%S',
            '%d/%m/%Y %H:%M',
            '%B %d, %Y at %H:%M',
            '%b %d, %Y · %H:%M',
            '%b %d, %Y',
            '%B %d, %Y',
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d/%m/%Y'
        ]
        
        # 合并原有格式和扩展格式
        all_formats = self.time_formats + extended_formats
        
        for fmt in all_formats:
            try:
                # 解析时间并确保时区一致性
                dt = datetime.strptime(datetime_str, fmt)
                # 如果没有时区信息，假设为UTC
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue
        
        # 尝试使用dateutil解析
        try:
            from dateutil import parser
            dt = parser.parse(datetime_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            pass
        
        # 如果所有格式都失败，返回None
        self.logger.warning(f"无法解析时间格式: {datetime_str}")
        return None
    
    def _parse_relative_time(self, time_text: str) -> Optional[datetime]:
        """解析相对时间（如2h、1d、3m等）"""
        if not time_text:
            return None
            
        try:
            time_text = time_text.strip().lower()
            now = datetime.now(timezone.utc)
            
            # 匹配相对时间格式
            patterns = [
                (r'(\d+)s', 1),      # 秒
                (r'(\d+)m', 60),     # 分钟
                (r'(\d+)h', 3600),   # 小时
                (r'(\d+)d', 86400),  # 天
                (r'(\d+)w', 604800), # 周
            ]
            
            for pattern, multiplier in patterns:
                match = re.search(pattern, time_text)
                if match:
                    value = int(match.group(1))
                    seconds_ago = value * multiplier
                    return now - timedelta(seconds=seconds_ago)
            
            # 处理特殊情况
            if 'now' in time_text or 'just now' in time_text:
                return now
            elif 'yesterday' in time_text:
                return now - timedelta(days=1)
            elif 'today' in time_text:
                return now.replace(hour=12, minute=0, second=0, microsecond=0)
            
            return None
            
        except Exception as e:
            self.logger.debug(f"解析相对时间失败: {time_text}, 错误: {e}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """清理文本"""
        if not text:
            return ""
        
        # HTML解码
        text = html.unescape(text)
        
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 去除首尾空白
        text = text.strip()
        
        return text
    
    async def extract_user_profile(self, browser_instance: BrowserInstance) -> Optional[UserData]:
        """提取用户资料信息"""
        try:
            # 等待用户资料加载
            await browser_instance.page.wait_for_selector('[data-testid="UserName"]', timeout=10000)
            
            # 提取用户名
            username_element = await browser_instance.page.query_selector('[data-testid="UserName"] span')
            username = await username_element.inner_text() if username_element else ""
            
            # 提取显示名称
            display_name_element = await browser_instance.page.query_selector('[data-testid="UserName"] div span')
            display_name = await display_name_element.inner_text() if display_name_element else ""
            
            # 提取简介
            bio_element = await browser_instance.page.query_selector('[data-testid="UserDescription"]')
            bio = await bio_element.inner_text() if bio_element else ""
            
            # 提取统计信息
            stats = await self._extract_user_stats(browser_instance)
            
            # 提取其他信息
            profile_info = await self._extract_profile_info(browser_instance)
            
            user_data = UserData(
                user_id=profile_info.get('user_id', ''),
                username=username.replace('@', ''),
                display_name=display_name,
                bio=bio,
                location=profile_info.get('location', ''),
                website=profile_info.get('website', ''),
                
                followers_count=stats.get('followers', 0),
                following_count=stats.get('following', 0),
                tweets_count=stats.get('tweets', 0),
                
                verified=profile_info.get('verified', False),
                protected=profile_info.get('protected', False),
                
                profile_image_url=profile_info.get('profile_image', ''),
                banner_image_url=profile_info.get('banner_image', '')
            )
            
            return user_data
            
        except Exception as e:
            self.logger.error(f"提取用户资料失败: {e}")
            handle_exception(e)
            return None
    
    async def _extract_user_stats(self, browser_instance: BrowserInstance) -> Dict[str, int]:
        """提取用户统计信息"""
        try:
            stats = {'followers': 0, 'following': 0, 'tweets': 0}
            
            # 查找统计链接
            stat_links = await browser_instance.page.query_selector_all('a[href*="/followers"], a[href*="/following"]')
            
            for link in stat_links:
                href = await link.get_attribute('href')
                text = await link.inner_text()
                
                if '/followers' in href:
                    stats['followers'] = self._parse_stat_number(text)
                elif '/following' in href:
                    stats['following'] = self._parse_stat_number(text)
            
            return stats
            
        except Exception as e:
            self.logger.debug(f"提取用户统计失败: {e}")
            return {'followers': 0, 'following': 0, 'tweets': 0}
    
    async def _extract_profile_info(self, browser_instance: BrowserInstance) -> Dict[str, Any]:
        """提取资料信息"""
        try:
            profile_info = {}
            
            # 提取头像
            avatar_element = await browser_instance.page.query_selector('[data-testid="UserAvatar-Container-unknown"] img')
            if avatar_element:
                src = await avatar_element.get_attribute('src')
                if src:
                    profile_info['profile_image'] = src
            
            # 检测认证状态
            verified_element = await browser_instance.page.query_selector('[data-testid="icon-verified"]')
            profile_info['verified'] = verified_element is not None
            
            # 检测保护状态
            protected_element = await browser_instance.page.query_selector('[data-testid="icon-lock"]')
            profile_info['protected'] = protected_element is not None
            
            return profile_info
            
        except Exception as e:
            self.logger.debug(f"提取资料信息失败: {e}")
            return {}
    
    def _parse_stat_number(self, text: str) -> int:
        """解析统计数字"""
        try:
            # 移除非数字字符，保留K、M
            clean_text = re.sub(r'[^\d\.KM]', '', text.upper())
            
            if 'K' in clean_text:
                number = float(clean_text.replace('K', ''))
                return int(number * 1000)
            elif 'M' in clean_text:
                number = float(clean_text.replace('M', ''))
                return int(number * 1000000)
            else:
                return int(float(clean_text)) if clean_text else 0
                
        except:
            return 0
    
    def validate_tweet_data(self, tweet_data: TweetData) -> bool:
        """验证推文数据"""
        try:
            # 基本字段验证
            if not tweet_data.tweet_id or not tweet_data.username:
                return False
            
            # 内容长度验证
            if len(tweet_data.content) > 10000:  # Twitter最大长度限制
                return False
            
            # 时间验证
            current_time = datetime.now(timezone.utc)
            tweet_time = tweet_data.created_at
            # 确保时区一致性
            if tweet_time.tzinfo is None:
                tweet_time = tweet_time.replace(tzinfo=timezone.utc)
            if tweet_time > current_time:
                return False
            
            # 互动数据验证
            if any(count < 0 for count in [
                tweet_data.likes_count, tweet_data.retweets_count, 
                tweet_data.replies_count, tweet_data.quotes_count
            ]):
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"验证推文数据失败: {e}")
            return False
    
    def filter_tweets(self, tweets: List[TweetData], 
                     filters: Dict[str, Any]) -> List[TweetData]:
        """过滤推文"""
        try:
            filtered_tweets = []
            
            for tweet in tweets:
                # 验证数据
                if not self.validate_tweet_data(tweet):
                    continue
                
                # 应用过滤条件
                if self._apply_filters(tweet, filters):
                    filtered_tweets.append(tweet)
            
            return filtered_tweets
            
        except Exception as e:
            self.logger.error(f"过滤推文失败: {e}")
            return tweets
    
    def _apply_filters(self, tweet: TweetData, filters: Dict[str, Any]) -> bool:
        """应用过滤条件"""
        try:
            # 最小点赞数
            if 'min_likes' in filters and tweet.likes_count < filters['min_likes']:
                return False
            
            # 最小转发数
            if 'min_retweets' in filters and tweet.retweets_count < filters['min_retweets']:
                return False
            
            # 内容长度
            if 'min_content_length' in filters and len(tweet.content) < filters['min_content_length']:
                return False
            
            # 排除转推
            if filters.get('exclude_retweets', False) and tweet.is_retweet:
                return False
            
            # 排除回复
            if filters.get('exclude_replies', False) and tweet.is_reply:
                return False
            
            # 必须包含媒体
            if filters.get('require_media', False) and not tweet.has_media:
                return False
            
            # 关键词过滤
            if 'keywords' in filters:
                keywords = filters['keywords']
                if isinstance(keywords, str):
                    keywords = [keywords]
                
                content_lower = tweet.content.lower()
                if not any(keyword.lower() in content_lower for keyword in keywords):
                    return False
            
            return True
            
        except Exception as e:
            self.logger.debug(f"应用过滤条件失败: {e}")
            return True


# 使用示例
if __name__ == "__main__":
    import asyncio
    from browser_manager import BrowserManager
    
    async def test_data_extractor():
        extractor = DataExtractor()
        
        async with BrowserManager() as browser_manager:
            instance = await browser_manager.get_available_instance()
            if instance:
                # 导航到Twitter
                success = await browser_manager.navigate_to_page(instance, "https://twitter.com/elonmusk")
                if success:
                    # 提取推文
                    tweets = await extractor.extract_tweets_from_page(instance, max_tweets=10)
                    print(f"提取了 {len(tweets)} 条推文")
                    
                    # 提取用户资料
                    user_data = await extractor.extract_user_profile(instance)
                    if user_data:
                        print(f"用户: {user_data.display_name} (@{user_data.username})")
                
                await browser_manager.release_instance(instance)
    
    # 运行测试
    # asyncio.run(test_data_extractor())