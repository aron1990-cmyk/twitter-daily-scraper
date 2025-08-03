#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter自动互动引擎

支持多账号、每日自动互动、可扩展配置的Twitter自动互动模块
功能包括：点赞、转发、评论、私信等，具备防封号机制
"""

import asyncio
import json
import logging
import random
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml
from playwright.async_api import Browser, Page, Playwright, async_playwright

# 导入现有模块
from utils.account_manager import AccountManager
from utils.ads_browser_launcher import AdsPowerLauncher
from utils.config_manager import ConfigManager
from utils.human_behavior_simulator import HumanBehaviorSimulator
from utils.retry_utils import retry_with_backoff
from utils.storage_manager import StorageManager


class TweetScorer:
    """推文内容评分模块"""
    
    def __init__(self, config: Dict):
        self.keywords_positive = config.get('keywords_positive', [])
        self.keywords_negative = config.get('keywords_negative', [])
        self.min_likes = config.get('min_likes', 10)
        self.min_retweets = config.get('min_retweets', 5)
        
    def score_tweet(self, tweet_data: Dict) -> float:
        """对推文进行评分，返回0-1之间的分数"""
        score = 0.5  # 基础分数
        
        content = tweet_data.get('content', '').lower()
        likes = tweet_data.get('likes', 0)
        retweets = tweet_data.get('retweets', 0)
        
        # 关键词评分
        for keyword in self.keywords_positive:
            if keyword.lower() in content:
                score += 0.1
                
        for keyword in self.keywords_negative:
            if keyword.lower() in content:
                score -= 0.2
                
        # 热度评分
        if likes >= self.min_likes:
            score += 0.1
        if retweets >= self.min_retweets:
            score += 0.1
            
        # 确保分数在0-1范围内
        return max(0.0, min(1.0, score))


class InteractionLogger:
    """互动行为日志记录器"""
    
    def __init__(self, profile_id: str, log_dir: str = "logs"):
        self.profile_id = profile_id
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # 创建日志文件
        today = datetime.now().strftime("%Y%m%d")
        self.log_file = self.log_dir / f"interaction_{profile_id}_{today}.log"
        
        # 配置日志
        self.logger = logging.getLogger(f"interaction_{profile_id}")
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.FileHandler(self.log_file, encoding='utf-8')
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def log_interaction(self, action: str, tweet_url: str, success: bool, 
                       details: Dict = None):
        """记录互动行为"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'profile_id': self.profile_id,
            'action': action,
            'tweet_url': tweet_url,
            'success': success,
            'details': details or {}
        }
        
        self.logger.info(json.dumps(log_data, ensure_ascii=False))


class DailyLimitTracker:
    """每日限额跟踪器"""
    
    def __init__(self, profile_id: str, limits: Dict):
        self.profile_id = profile_id
        self.limits = limits
        self.data_file = Path(f"data/daily_limits_{profile_id}.json")
        self.data_file.parent.mkdir(exist_ok=True)
        
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.counts = self._load_counts()
    
    def _load_counts(self) -> Dict:
        """加载今日计数"""
        if self.data_file.exists():
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get('date') == self.today:
                    return data.get('counts', {})
        
        return {action: 0 for action in self.limits.keys()}
    
    def _save_counts(self):
        """保存计数"""
        data = {
            'date': self.today,
            'counts': self.counts
        }
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def can_perform_action(self, action: str) -> bool:
        """检查是否可以执行某个动作"""
        current_count = self.counts.get(action, 0)
        limit = self.limits.get(action, 0)
        return current_count < limit
    
    def increment_count(self, action: str):
        """增加动作计数"""
        self.counts[action] = self.counts.get(action, 0) + 1
        self._save_counts()
    
    def get_remaining_count(self, action: str) -> int:
        """获取剩余次数"""
        current_count = self.counts.get(action, 0)
        limit = self.limits.get(action, 0)
        return max(0, limit - current_count)


class InteractionEngine:
    """Twitter自动互动引擎"""
    
    def __init__(self, profile_id: str, config_path: str):
        self.profile_id = profile_id
        self.config = self._load_config(config_path)
        
        # 初始化组件
        self.scorer = TweetScorer(self.config.get('scoring', {}))
        self.logger = InteractionLogger(profile_id)
        self.limit_tracker = DailyLimitTracker(
            profile_id, 
            self.config.get('daily_limit', {})
        )
        self.behavior_simulator = None  # 将在浏览器初始化后创建
        self.ads_launcher = AdsPowerLauncher()
        
        # 浏览器相关
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
        # 评论语料池
        self.comment_pool = self.config.get('comment_pool', [])
        
        # 行为配置
        self.delay_range = self.config.get('delay_range', {'min': 2, 'max': 6})
        self.random_behavior = self.config.get('random_behavior', {})
        
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
            
        with open(config_file, 'r', encoding='utf-8') as f:
            if config_file.suffix.lower() == '.yaml':
                return yaml.safe_load(f)
            else:
                return json.load(f)
    
    async def _init_browser(self) -> bool:
        """初始化浏览器"""
        try:
            # 使用AdsPower启动浏览器
            browser_info = self.ads_launcher.start_browser(self.profile_id)
            if not browser_info:
                self.logger.log_interaction(
                    'browser_init', '', False, 
                    {'error': 'Failed to launch AdsPower browser'}
                )
                return False
            
            playwright = await async_playwright().start()
            # 获取WebSocket端点
            ws_endpoint = browser_info.get('ws', {}).get('puppeteer')
            if not ws_endpoint:
                self.logger.log_interaction(
                    'browser_init', '', False, 
                    {'error': 'No WebSocket endpoint found'}
                )
                return False
                
            self.browser = await playwright.chromium.connect_over_cdp(ws_endpoint)
            
            # 获取或创建页面
            pages = self.browser.contexts[0].pages
            if pages:
                self.page = pages[0]
            else:
                self.page = await self.browser.contexts[0].new_page()
            
            # 设置用户代理和视口
            await self.page.set_viewport_size({"width": 1920, "height": 1080})
            
            # 初始化行为模拟器
            self.behavior_simulator = HumanBehaviorSimulator(self.page)
            
            self.logger.log_interaction(
                'browser_init', '', True, 
                {'profile_id': self.profile_id}
            )
            return True
            
        except Exception as e:
            self.logger.log_interaction(
                'browser_init', '', False, 
                {'error': str(e)}
            )
            return False
    
    async def _close_browser(self):
        """关闭浏览器"""
        try:
            if self.browser:
                await self.browser.close()
            self.ads_launcher.stop_browser(self.profile_id)
            
        except Exception as e:
            self.logger.logger.error(f"关闭浏览器失败: {e}")
    
    async def _random_delay(self):
        """随机延迟"""
        delay = random.uniform(
            self.delay_range['min'], 
            self.delay_range['max']
        )
        await asyncio.sleep(delay)
    
    async def _navigate_to_tweet(self, tweet_url: str) -> bool:
        """导航到推文页面"""
        try:
            await self.page.goto(tweet_url, wait_until='networkidle')
            await self._random_delay()
            
            # 等待页面加载完成
            await self.page.wait_for_selector('[data-testid="tweet"]', timeout=10000)
            return True
            
        except Exception as e:
            self.logger.log_interaction(
                'navigate', tweet_url, False, 
                {'error': str(e)}
            )
            return False
    
    @retry_with_backoff(max_attempts=3, base_delay=1)
    async def like(self, tweet_url: str) -> bool:
        """点赞推文"""
        if not self.limit_tracker.can_perform_action('like'):
            self.logger.log_interaction(
                'like', tweet_url, False, 
                {'error': 'Daily limit reached'}
            )
            return False
        
        try:
            if not await self._navigate_to_tweet(tweet_url):
                return False
            
            # 查找点赞按钮
            like_button = await self.page.query_selector(
                '[data-testid="like"]'
            )
            
            if not like_button:
                self.logger.log_interaction(
                    'like', tweet_url, False, 
                    {'error': 'Like button not found'}
                )
                return False
            
            # 检查是否已经点赞
            is_liked = await like_button.get_attribute('data-testid') == 'unlike'
            if is_liked:
                self.logger.log_interaction(
                    'like', tweet_url, False, 
                    {'error': 'Already liked'}
                )
                return False
            
            # 模拟人类行为点击
            await self.behavior_simulator.human_like_click(like_button)
            await self._random_delay()
            
            # 验证点赞成功
            await asyncio.sleep(1)
            updated_button = await self.page.query_selector(
                '[data-testid="unlike"]'
            )
            
            success = updated_button is not None
            if success:
                self.limit_tracker.increment_count('like')
            
            self.logger.log_interaction('like', tweet_url, success)
            return success
            
        except Exception as e:
            self.logger.log_interaction(
                'like', tweet_url, False, 
                {'error': str(e)}
            )
            return False
    
    @retry_with_backoff(max_attempts=3, base_delay=1)
    async def retweet(self, tweet_url: str) -> bool:
        """转发推文"""
        if not self.limit_tracker.can_perform_action('retweet'):
            self.logger.log_interaction(
                'retweet', tweet_url, False, 
                {'error': 'Daily limit reached'}
            )
            return False
        
        try:
            if not await self._navigate_to_tweet(tweet_url):
                return False
            
            # 查找转发按钮
            retweet_button = await self.page.query_selector(
                '[data-testid="retweet"]'
            )
            
            if not retweet_button:
                self.logger.log_interaction(
                    'retweet', tweet_url, False, 
                    {'error': 'Retweet button not found'}
                )
                return False
            
            # 点击转发按钮
            await self.behavior_simulator.human_like_click(retweet_button)
            await self._random_delay()
            
            # 点击确认转发
            confirm_button = await self.page.query_selector(
                '[data-testid="retweetConfirm"]'
            )
            
            if confirm_button:
                await self.behavior_simulator.human_like_click(confirm_button)
                await self._random_delay()
                
                self.limit_tracker.increment_count('retweet')
                self.logger.log_interaction('retweet', tweet_url, True)
                return True
            else:
                self.logger.log_interaction(
                    'retweet', tweet_url, False, 
                    {'error': 'Confirm button not found'}
                )
                return False
            
        except Exception as e:
            self.logger.log_interaction(
                'retweet', tweet_url, False, 
                {'error': str(e)}
            )
            return False
    
    @retry_with_backoff(max_attempts=3, base_delay=1)
    async def comment(self, tweet_url: str, text: str = None) -> bool:
        """评论推文"""
        if not self.limit_tracker.can_perform_action('comment'):
            self.logger.log_interaction(
                'comment', tweet_url, False, 
                {'error': 'Daily limit reached'}
            )
            return False
        
        # 如果没有提供评论内容，从语料池随机选择
        if not text and self.comment_pool:
            text = random.choice(self.comment_pool)
        
        if not text:
            self.logger.log_interaction(
                'comment', tweet_url, False, 
                {'error': 'No comment text provided'}
            )
            return False
        
        try:
            if not await self._navigate_to_tweet(tweet_url):
                return False
            
            # 查找评论输入框
            comment_box = await self.page.query_selector(
                '[data-testid="tweetTextarea_0"]'
            )
            
            if not comment_box:
                self.logger.log_interaction(
                    'comment', tweet_url, False, 
                    {'error': 'Comment box not found'}
                )
                return False
            
            # 点击评论框并输入内容
            await comment_box.click()
            await self._random_delay()
            
            # 模拟人类打字
            await self.behavior_simulator.human_like_type(comment_box, text)
            await self._random_delay()
            
            # 查找并点击发送按钮
            send_button = await self.page.query_selector(
                '[data-testid="tweetButtonInline"]'
            )
            
            if send_button:
                await self.behavior_simulator.human_like_click(send_button)
                await self._random_delay()
                
                self.limit_tracker.increment_count('comment')
                self.logger.log_interaction(
                    'comment', tweet_url, True, 
                    {'text': text}
                )
                return True
            else:
                self.logger.log_interaction(
                    'comment', tweet_url, False, 
                    {'error': 'Send button not found'}
                )
                return False
            
        except Exception as e:
            self.logger.log_interaction(
                'comment', tweet_url, False, 
                {'error': str(e), 'text': text}
            )
            return False
    
    @retry_with_backoff(max_attempts=3, base_delay=1)
    async def send_dm(self, user_url: str, message: str) -> bool:
        """发送私信"""
        if not self.limit_tracker.can_perform_action('dm'):
            self.logger.log_interaction(
                'dm', user_url, False, 
                {'error': 'Daily limit reached'}
            )
            return False
        
        try:
            # 导航到用户页面
            await self.page.goto(user_url, wait_until='networkidle')
            await self._random_delay()
            
            # 查找私信按钮
            dm_button = await self.page.query_selector(
                '[data-testid="sendDMFromProfile"]'
            )
            
            if not dm_button:
                self.logger.log_interaction(
                    'dm', user_url, False, 
                    {'error': 'DM button not found'}
                )
                return False
            
            # 点击私信按钮
            await self.behavior_simulator.human_like_click(dm_button)
            await self._random_delay()
            
            # 查找消息输入框
            message_box = await self.page.query_selector(
                '[data-testid="dmComposerTextInput"]'
            )
            
            if not message_box:
                self.logger.log_interaction(
                    'dm', user_url, False, 
                    {'error': 'Message box not found'}
                )
                return False
            
            # 输入消息
            await self.behavior_simulator.human_like_type(message_box, message)
            await self._random_delay()
            
            # 发送消息
            send_button = await self.page.query_selector(
                '[data-testid="dmComposerSendButton"]'
            )
            
            if send_button:
                await self.behavior_simulator.human_like_click(send_button)
                await self._random_delay()
                
                self.limit_tracker.increment_count('dm')
                self.logger.log_interaction(
                    'dm', user_url, True, 
                    {'message': message}
                )
                return True
            else:
                self.logger.log_interaction(
                    'dm', user_url, False, 
                    {'error': 'Send button not found'}
                )
                return False
            
        except Exception as e:
            self.logger.log_interaction(
                'dm', user_url, False, 
                {'error': str(e), 'message': message}
            )
            return False
    
    def _should_interact(self, action: str, tweet_score: float) -> bool:
        """根据配置和评分决定是否执行互动"""
        probability = self.random_behavior.get(f'{action}_probability', 0.5)
        
        # 结合推文评分调整概率
        adjusted_probability = probability * tweet_score
        
        return random.random() < adjusted_probability
    
    async def run(self, tweet_list: List[Dict]) -> Dict:
        """主执行函数：传入推文列表，按配置执行互动"""
        if not await self._init_browser():
            return {'success': False, 'error': 'Failed to initialize browser'}
        
        results = {
            'total_tweets': len(tweet_list),
            'interactions': {
                'like': 0,
                'retweet': 0,
                'comment': 0,
                'dm': 0
            },
            'errors': []
        }
        
        try:
            for tweet_data in tweet_list:
                tweet_url = tweet_data.get('url')
                if not tweet_url:
                    continue
                
                # 评分推文
                tweet_score = self.scorer.score_tweet(tweet_data)
                
                # 随机延迟
                await self._random_delay()
                
                # 执行互动
                actions = ['like', 'retweet', 'comment']
                for action in actions:
                    if not self.limit_tracker.can_perform_action(action):
                        continue
                    
                    if self._should_interact(action, tweet_score):
                        success = False
                        
                        if action == 'like':
                            success = await self.like(tweet_url)
                        elif action == 'retweet':
                            success = await self.retweet(tweet_url)
                        elif action == 'comment':
                            success = await self.comment(tweet_url)
                        
                        if success:
                            results['interactions'][action] += 1
                        
                        # 动作间延迟
                        await self._random_delay()
                
                # 处理私信（针对高分推文的作者）
                if (tweet_score > 0.8 and 
                    self.limit_tracker.can_perform_action('dm') and 
                    self._should_interact('dm', tweet_score)):
                    
                    user_url = tweet_data.get('user_url')
                    if user_url:
                        dm_message = random.choice(
                            self.config.get('dm_templates', ['Hello!'])
                        )
                        if await self.send_dm(user_url, dm_message):
                            results['interactions']['dm'] += 1
            
            results['success'] = True
            
        except Exception as e:
            results['success'] = False
            results['error'] = str(e)
            self.logger.logger.error(f"执行互动任务失败: {e}")
            
        finally:
            await self._close_browser()
        
        return results
    
    def get_daily_stats(self) -> Dict:
        """获取今日统计信息"""
        stats = {
            'profile_id': self.profile_id,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'limits': self.config.get('daily_limit', {}),
            'used': self.limit_tracker.counts,
            'remaining': {}
        }
        
        for action, limit in stats['limits'].items():
            used = stats['used'].get(action, 0)
            stats['remaining'][action] = max(0, limit - used)
        
        return stats