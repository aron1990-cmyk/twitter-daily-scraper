#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter抓取Web管理系统 - 性能优化版本
提供Web界面进行关键词配置、任务管理和数据查看
集成了全面的性能优化功能
"""

import os
import json
import sqlite3
import subprocess
import tempfile
import time
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import asyncio
import threading
from dataclasses import asdict
import re
import logging

# 导入性能优化组件
from performance_config import PERFORMANCE_CONFIG
from performance_middleware import PerformanceMiddleware, cache_response, measure_time
from utils.api_cache_manager import APICacheManager, cached_api, invalidate_cache, api_cache
from utils.db_optimizer import DatabaseOptimizer, init_db_optimizer, query_timer, paginated_query
from utils.static_optimizer import StaticResourceOptimizer, init_static_optimizer, asset_url, cdn_url
from config.adspower_config import get_config as get_adspower_config, get_primary_user_id, get_all_user_ids
from config.feishu_config import get_config as get_feishu_config, update_config as update_feishu_config

# 导入现有模块
from models import TweetModel, ScrapingConfig
from utils.ads_browser_launcher import AdsPowerLauncher
from utils.adspower_manager import AdsPowerManager
from core.twitter_parser import TwitterParser
from utils.cloud_sync import CloudSyncManager
from utils.excel_writer import ExcelWriter
from core.refactored_task_manager import RefactoredTaskManager
from core.async_feishu_sync import get_async_sync_manager, init_async_sync_service, shutdown_async_sync_service
from scheduler import TaskScheduler, PredefinedTasks
from utils.system_monitor import SystemMonitor
from utils.resource_scheduler import ResourceScheduler
from utils.async_task_manager import AsyncTaskManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 默认配置定义（将从数据库加载覆盖）
TWITTER_TARGETS = {
    'accounts': [],
    'keywords': []
}

FILTER_CONFIG = {
    'min_likes': 50,
    'min_comments': 10,
    'min_retweets': 20,
    'keywords_filter': [],
    'max_tweets_per_target': 8,
    'max_total_tweets': 200,
    'min_content_length': 20,
    'max_content_length': 1000,
    'max_age_hours': 72,
}

OUTPUT_CONFIG = {
    'data_dir': './data',
    'excel_filename_format': 'twitter_daily_{date}.xlsx',
    'sheet_name': 'Twitter数据',
}

BROWSER_CONFIG = {
    'headless': False,
    'timeout': 8000,
    'wait_time': 0.3,
    'scroll_pause_time': 0.3,
    'navigation_timeout': 10000,
    'load_state_timeout': 4000,
    'fast_mode': True,
    'skip_images': True,
    'disable_animations': True,
}

LOG_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'filename': 'twitter_scraper.log'
}

CLOUD_SYNC_CONFIG = {
    'google_sheets': {
        'enabled': False,
        'credentials_file': './credentials/google-credentials.json',
        'spreadsheet_id': '',
        'worksheet_name': 'Twitter数据',
    },
    'feishu': {
        'enabled': False,
        'app_id': '',
        'app_secret': '',
        'spreadsheet_token': '',
        'sheet_id': '',
    }
}

# 飞书配置信息 - 从配置文件加载
FEISHU_CONFIG = get_feishu_config()

# AdsPower配置信息
# 从配置文件加载AdsPower配置
ADS_POWER_CONFIG = get_adspower_config()
ADS_POWER_CONFIG.update({
    'user_id': get_primary_user_id(),
    'multi_user_ids': get_all_user_ids()
})

# 创建Flask应用
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.debug = True
app.config['SECRET_KEY'] = 'twitter-scraper-web-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/aron/twitter-daily-scraper/instance/twitter_scraper.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_AS_ASCII'] = False

# 应用性能配置
for key, value in PERFORMANCE_CONFIG.items():
    app.config[key.upper()] = value

# 初始化性能中间件
performance_middleware = PerformanceMiddleware(app)

# 初始化Flask扩展
db = SQLAlchemy(app)

# 初始化优化组件
api_cache_manager = None
db_optimizer = None
static_optimizer = None

def init_optimizers():
    """初始化所有优化组件"""
    global api_cache_manager, db_optimizer, static_optimizer
    
    try:
        # 初始化数据库优化器
        db_optimizer = init_db_optimizer(db)
        logger.info('Database optimizer initialized')
        
        # 初始化静态资源优化器
        static_optimizer = init_static_optimizer(app)
        logger.info('Static resource optimizer initialized')
        
        # 初始化API缓存管理器
        api_cache_manager = APICacheManager()
        logger.info('API cache manager initialized')
        
        # 注册模板函数
        app.jinja_env.globals.update(
            asset_url=asset_url,
            cdn_url=cdn_url
        )
        
    except Exception as e:
        logger.error(f'Failed to initialize optimizers: {e}')

# 从原始web_app.py导入必要的函数和类
def load_config_from_database():
    """从数据库加载配置"""
    global TWITTER_TARGETS, FILTER_CONFIG, OUTPUT_CONFIG, BROWSER_CONFIG, FEISHU_CONFIG, ADS_POWER_CONFIG
    
    try:
        configs = SystemConfig.query.all()
        config_dict = {}
        
        # 分别处理不同类型的配置
        for config in configs:
            if config.value:
                # 对于JSON格式的配置，使用json.loads
                if config.key in ['twitter_targets', 'filter_config', 'output_config', 'browser_config', 'feishu_config', 'ads_power_config']:
                    try:
                        config_dict[config.key] = json.loads(config.value)
                    except json.JSONDecodeError:
                        config_dict[config.key] = config.value
                else:
                    # 对于简单字符串配置，直接使用原值
                    config_dict[config.key] = config.value
            else:
                config_dict[config.key] = {}
        
        # 更新配置
        if 'twitter_targets' in config_dict:
            TWITTER_TARGETS.update(config_dict['twitter_targets'])
        if 'filter_config' in config_dict:
            FILTER_CONFIG.update(config_dict['filter_config'])
        if 'output_config' in config_dict:
            OUTPUT_CONFIG.update(config_dict['output_config'])
        if 'browser_config' in config_dict:
            BROWSER_CONFIG.update(config_dict['browser_config'])
        # 飞书配置现在从配置文件加载，不再从数据库读取
        # if 'feishu_config' in config_dict:
        #     FEISHU_CONFIG.update(config_dict['feishu_config'])
        # AdsPower配置现在从配置文件加载，不再从数据库读取
        # if 'ads_power_config' in config_dict:
        #     ADS_POWER_CONFIG.update(config_dict['ads_power_config'])
        
        # AdsPower配置现在从配置文件加载，不再从数据库读取
        # 保持配置文件中的设置不变
            
        logger.info('Configuration loaded from database')
        
    except Exception as e:
        logger.error(f'Failed to load config from database: {e}')

def init_database():
    """初始化数据库"""
    try:
        with app.app_context():
            db.create_all()
            logger.info('Database initialized successfully')
    except Exception as e:
        logger.error(f'Database initialization failed: {e}')
        raise

# 数据库模型定义
class ScrapingTask(db.Model):
    __tablename__ = 'scraping_task'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    target_accounts = db.Column(db.Text)
    target_keywords = db.Column(db.Text)
    max_tweets = db.Column(db.Integer, default=50)
    min_likes = db.Column(db.Integer, default=0)
    min_retweets = db.Column(db.Integer, default=0)
    min_comments = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    result_count = db.Column(db.Integer, default=0)
    tweets_collected = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    notes = db.Column(db.Text)
    
    @property
    def keywords(self):
        try:
            return json.loads(self.target_keywords) if self.target_keywords else []
        except:
            return []
    
    @property
    def accounts(self):
        try:
            return json.loads(self.target_accounts) if self.target_accounts else []
        except:
            return []
    
    @property
    def tweets_collected(self):
        return TweetData.query.filter_by(task_id=self.id).count()
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'target_accounts': self.accounts,
            'target_keywords': self.keywords,
            'max_tweets': self.max_tweets,
            'min_likes': self.min_likes,
            'min_retweets': self.min_retweets,
            'min_comments': self.min_comments,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'result_count': self.result_count,
            'error_message': self.error_message,
            'notes': self.notes,
            'tweets_collected': self.tweets_collected
        }

class TweetData(db.Model):
    __tablename__ = 'tweet_data'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('scraping_task.id'), nullable=False)
    username = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    likes = db.Column(db.Integer, default=0)
    comments = db.Column(db.Integer, default=0)
    retweets = db.Column(db.Integer, default=0)
    publish_time = db.Column(db.String(100))
    link = db.Column(db.Text)
    hashtags = db.Column(db.Text)
    content_type = db.Column(db.String(50))
    scraped_at = db.Column(db.DateTime, default=datetime.utcnow)
    synced_to_feishu = db.Column(db.Boolean, default=False)
    full_content = db.Column(db.Text)
    media_content = db.Column(db.Text)
    thread_tweets = db.Column(db.Text)
    quoted_tweet = db.Column(db.Text)
    has_detailed_content = db.Column(db.Boolean, default=False)
    detail_error = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'username': self.username,
            'content': self.content,
            'likes': self.likes,
            'comments': self.comments,
            'retweets': self.retweets,
            'publish_time': self.publish_time,
            'link': self.link,
            'hashtags': json.loads(self.hashtags) if self.hashtags else [],
            'content_type': self.content_type,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None,
            'synced_to_feishu': self.synced_to_feishu,
            'full_content': self.full_content,
            'media_content': json.loads(self.media_content) if self.media_content else None,
            'thread_tweets': json.loads(self.thread_tweets) if self.thread_tweets else [],
            'quoted_tweet': json.loads(self.quoted_tweet) if self.quoted_tweet else None,
            'has_detailed_content': self.has_detailed_content,
            'detail_error': self.detail_error
        }

class SystemConfig(db.Model):
    __tablename__ = 'system_config'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class TwitterInfluencer(db.Model):
    __tablename__ = 'twitter_influencer'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), nullable=False)
    profile_url = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    followers_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    last_scraped = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'username': self.username,
            'profile_url': self.profile_url,
            'description': self.description,
            'category': self.category,
            'followers_count': self.followers_count,
            'is_active': self.is_active,
            'last_scraped': self.last_scraped.isoformat() if self.last_scraped else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# 全局变量
current_task = None
task_thread = None
task_executor = None
task_manager = None
optimized_scraper = None
task_scheduler = None

# 单个任务执行器（修改为支持指定用户ID）
class ScrapingTaskExecutor:
    def __init__(self, user_id=None):
        self.is_running = False
        self.current_task_id = None
        self.user_id = user_id or ADS_POWER_CONFIG['user_id']
        
    async def execute_task(self, task_id: int):
        """执行抓取任务"""
        global current_task
        
        try:
            print(f"[DEBUG] 开始执行任务 {task_id}")
            
            # 获取任务
            task = ScrapingTask.query.get(task_id)
            if not task:
                raise Exception(f"任务 {task_id} 不存在")
            
            print(f"[DEBUG] 任务信息: {task.name}")
            
            # 更新任务状态
            task.status = 'running'
            task.started_at = datetime.utcnow()
            db.session.commit()
            
            current_task = task
            self.is_running = True
            self.current_task_id = task_id
            
            # 解析配置
            target_accounts = json.loads(task.target_accounts or '[]')
            target_keywords = json.loads(task.target_keywords or '[]')
            
            print(f"[DEBUG] 目标账号: {target_accounts}")
            print(f"[DEBUG] 关键词: {target_keywords}")
            
            # 启动浏览器
            print(f"[DEBUG] 正在启动AdsPower浏览器...")
            app.logger.info(f"开始启动AdsPower浏览器，用户ID: {self.user_id}")
            
            browser_manager = AdsPowerLauncher(ADS_POWER_CONFIG)
            user_id = self.user_id  # 使用分配的用户ID
            
            try:
                # 进行完整的健康检查和浏览器启动
                app.logger.info("正在进行AdsPower健康检查...")
                browser_info = browser_manager.start_browser(user_id, skip_health_check=False)
                if not browser_info:
                    raise Exception("浏览器启动失败：未返回浏览器信息")
                
                app.logger.info(f"浏览器启动成功: {browser_info}")
                print(f"[DEBUG] 浏览器启动成功: {browser_info}")
                
            except Exception as e:
                app.logger.error(f"AdsPower浏览器启动失败: {str(e)}")
                
                # 获取详细的健康报告
                try:
                    health_report = browser_manager.get_health_report()
                    app.logger.error(f"系统健康报告: {health_report}")
                    
                    # 尝试自动修复
                    app.logger.info("尝试自动修复系统问题...")
                    if browser_manager.auto_optimize_system():
                        app.logger.info("系统优化完成，重新尝试启动浏览器...")
                        browser_info = browser_manager.start_browser(user_id, skip_health_check=True)
                        if browser_info:
                            app.logger.info("浏览器启动成功（修复后）")
                        else:
                            raise Exception("浏览器启动失败（修复后仍然失败）")
                    else:
                        raise Exception(f"AdsPower浏览器启动失败且自动修复失败: {str(e)}")
                        
                except Exception as repair_error:
                    app.logger.error(f"自动修复过程中发生错误: {str(repair_error)}")
                    raise Exception(f"AdsPower浏览器启动失败: {str(e)}。修复尝试也失败: {str(repair_error)}")
            
            debug_port = browser_info.get('ws', {}).get('puppeteer')
            print(f"[DEBUG] 调试端口: {debug_port}")
            
            # 连接解析器
            print(f"[DEBUG] 正在连接Twitter解析器...")
            parser = TwitterParser(debug_port)
            await parser.connect_browser()
            print(f"[DEBUG] Twitter解析器连接成功")
            
            all_tweets = []
            
            # 判断是否需要组合搜索（同时有账号和关键词）
            if target_accounts and target_keywords:
                print(f"[DEBUG] 检测到组合搜索模式：在指定博主下搜索关键词")
                print(f"[DEBUG] 目标博主: {target_accounts}")
                print(f"[DEBUG] 搜索关键词: {target_keywords}")
                
                # 组合搜索：在每个指定博主下搜索每个关键词
                for account in target_accounts:
                    if not self.is_running:
                        break
                    
                    # 清理用户名，去除@符号
                    clean_username = account.lstrip('@')
                    
                    for keyword in target_keywords:
                        if not self.is_running:
                            break
                        
                        try:
                            print(f"[DEBUG] 在博主 @{clean_username} 下搜索关键词 '{keyword}'")
                            tweets = await parser.scrape_user_keyword_tweets(
                                username=clean_username, 
                                keyword=keyword, 
                                max_tweets=task.max_tweets,
                                enable_enhanced=True
                            )
                            
                            # 过滤推文
                            filtered_tweets = self._filter_tweets(tweets, task)
                            all_tweets.extend(filtered_tweets)
                            
                            print(f"[DEBUG] 在博主 @{clean_username} 下搜索关键词 '{keyword}' 完成，获得 {len(filtered_tweets)} 条有效推文")
                            
                        except Exception as e:
                            print(f"在博主 @{clean_username} 下搜索关键词 '{keyword}' 失败: {e}")
                            continue
            else:
                # 分别抓取账号推文和关键词推文（原有逻辑）
                
                # 抓取账号推文
                for account in target_accounts:
                    if not self.is_running:  # 检查是否被停止
                        break
                    
                    # 清理用户名，去除@符号
                    clean_username = account.lstrip('@')
                        
                    try:
                        print(f"[DEBUG] 抓取博主 @{clean_username} 的推文")
                        tweets = await parser.scrape_user_tweets(username=clean_username, max_tweets=task.max_tweets, enable_enhanced=True)
                        
                        # 过滤推文
                        filtered_tweets = self._filter_tweets(tweets, task)
                        all_tweets.extend(filtered_tweets)
                        
                        print(f"[DEBUG] 博主 @{clean_username} 抓取完成，获得 {len(filtered_tweets)} 条有效推文")
                        
                    except Exception as e:
                        print(f"抓取账号 {clean_username} 失败: {e}")
                        continue
                
                # 抓取关键词推文
                for keyword in target_keywords:
                    if not self.is_running:
                        break
                        
                    try:
                        print(f"[DEBUG] 全局搜索关键词 '{keyword}'")
                        tweets = await parser.scrape_keyword_tweets(keyword, max_tweets=task.max_tweets, enable_enhanced=True)
                        filtered_tweets = self._filter_tweets(tweets, task)
                        all_tweets.extend(filtered_tweets)
                        
                        print(f"[DEBUG] 关键词 '{keyword}' 搜索完成，获得 {len(filtered_tweets)} 条有效推文")
                        
                    except Exception as e:
                        print(f"搜索关键词 {keyword} 失败: {e}")
                        continue
            
            # 保存到数据库
            saved_count = self._save_tweets_to_db(all_tweets, task_id)
            
            # 更新任务状态
            task.status = 'completed'
            task.completed_at = datetime.utcnow()
            task.result_count = saved_count
            db.session.commit()
            
            # 关闭浏览器
            await parser.close()
            
            print(f"任务 {task_id} 完成，共抓取 {saved_count} 条推文")
            
        except Exception as e:
            # 更新任务状态为失败
            task = ScrapingTask.query.get(task_id)
            if task:
                task.status = 'failed'
                task.error_message = str(e)
                task.completed_at = datetime.utcnow()
                db.session.commit()
            
            print(f"任务 {task_id} 执行失败: {e}")
            
        finally:
            self.is_running = False
            self.current_task_id = None
            current_task = None
    
    def _filter_tweets(self, tweets: List[Dict], task: ScrapingTask) -> List[Dict]:
        """过滤推文"""
        filtered = []
        for tweet in tweets:
            if (tweet.get('likes', 0) >= task.min_likes and
                tweet.get('retweets', 0) >= task.min_retweets and
                tweet.get('comments', 0) >= task.min_comments):
                filtered.append(tweet)
        return filtered
    
    def _save_tweets_to_db(self, tweets: List[Dict], task_id: int) -> int:
        """保存推文到数据库"""
        if not tweets:
            return 0
        
        saved_count = 0
        for tweet in tweets:
            try:
                tweet_data = TweetData(
                    task_id=task_id,
                    username=tweet.get('username', ''),
                    content=tweet.get('content', ''),
                    likes=tweet.get('likes', 0),
                    comments=tweet.get('comments', 0),
                    retweets=tweet.get('retweets', 0),
                    publish_time=tweet.get('publish_time', ''),
                    link=tweet.get('link', ''),
                    hashtags=json.dumps(tweet.get('hashtags', [])),
                    content_type=tweet.get('content_type', ''),
                    full_content=tweet.get('full_content', ''),
                    media_content=json.dumps(tweet.get('media', {'images': [], 'videos': []})),
                    thread_tweets=json.dumps(tweet.get('thread_tweets', [])),
                    quoted_tweet=json.dumps(tweet.get('quoted_tweet')) if tweet.get('quoted_tweet') else None,
                    has_detailed_content=tweet.get('has_detailed_content', False),
                    detail_error=tweet.get('detail_error')
                )
                db.session.add(tweet_data)
                saved_count += 1
            except Exception as e:
                print(f"保存推文失败: {e}")
                continue
        
        db.session.commit()
        return saved_count
    
    def stop_task(self):
        """停止当前任务"""
        self.is_running = False

def init_task_manager():
    """初始化任务管理器"""
    global task_manager, optimized_scraper
    
    # 检查是否已经初始化，避免重复初始化
    if task_manager is not None:
        logger.info("⚠️ TaskManager已经初始化，跳过重复初始化")
        return
    
    max_concurrent = ADS_POWER_CONFIG.get('max_concurrent_tasks', 2)
    user_ids = ADS_POWER_CONFIG.get('multi_user_ids', [])
    
    try:
        # 创建任务管理器
        task_manager = RefactoredTaskManager(
            max_concurrent_tasks=max_concurrent,
            user_ids=user_ids
        )
        
        logger.info(f"✅ TaskManager已初始化，最大并发任务数: {max_concurrent}")
        
    except Exception as e:
        logger.error(f"⚠️ TaskManager初始化失败: {e}")
        
def init_task_scheduler():
    """初始化定时任务调度器"""
    global task_scheduler
    
    if task_scheduler is not None:
        logger.info("⚠️ TaskScheduler已经初始化，跳过重复初始化")
        return
    
    try:
        task_scheduler = TaskScheduler()
        
        # 添加预定义的定时任务
        # 每日Twitter采集任务（每天早上9点执行）
        task_scheduler.add_task(
            task_id="daily_twitter_scraping",
            name="每日Twitter数据采集",
            schedule_time="09:00",  # 每天早上9点
            task_function=lambda: logger.info("执行每日Twitter采集任务"),
            description="自动执行Twitter数据采集任务",
            max_retries=2,
            timeout_minutes=30
        )
        
        # 启动调度器
        task_scheduler.start_scheduler()
        
        logger.info("✅ TaskScheduler已初始化并启动")
        
    except Exception as e:
        logger.error(f"⚠️ TaskScheduler初始化失败: {e}")

# 优化的API路由
@app.route('/')
@cached_api(timeout=300)
def index():
    """首页 - 带缓存优化"""
    try:
        # 获取统计数据
        total_tasks = ScrapingTask.query.count()
        completed_tasks = ScrapingTask.query.filter_by(status='completed').count()
        total_tweets = TweetData.query.count()
        active_influencers = TwitterInfluencer.query.filter_by(is_active=True).count()
        
        # 获取最近任务
        recent_tasks_query = ScrapingTask.query.order_by(ScrapingTask.created_at.desc()).limit(5).all()
        recent_tasks = [task.to_dict() for task in recent_tasks_query]
        
        return render_template('index_optimized.html', 
                             total_tasks=total_tasks,
                             completed_tasks=completed_tasks,
                             total_tweets=total_tweets,
                             active_influencers=active_influencers,
                             recent_tasks=recent_tasks)
    except Exception as e:
        logger.error(f'Error in index route: {e}')
        return render_template('error.html', error=str(e)), 500

@app.route('/tasks')
@cached_api(timeout=60)
def tasks():
    """任务列表页面 - 带缓存优化"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # 使用优化的分页查询
        query = ScrapingTask.query.order_by(ScrapingTask.created_at.desc())
        pagination_result = paginated_query(query, page, per_page)
        
        return render_template('tasks_optimized.html', 
                             tasks=pagination_result.items,
                             pagination=pagination_result)
    except Exception as e:
        logger.error(f'Error in tasks route: {e}')
        return render_template('error.html', error=str(e)), 500

@app.route('/influencers')
@cached_api(timeout=120)
def influencers():
    """博主管理页面 - 带缓存优化"""
    return render_template('influencers_optimized.html')

@app.route('/data')
@cached_api(timeout=60)
def data():
    """数据查看页面 - 带缓存优化"""
    try:
        from datetime import date
        from sqlalchemy import func
        
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        search = request.args.get('search', '')
        task_id = request.args.get('task_id', type=int)
        
        # 构建查询
        query = TweetData.query
        
        # 搜索过滤
        if search:
            query = query.filter(
                db.or_(
                    TweetData.content.contains(search),
                    TweetData.username.contains(search)
                )
            )
        
        # 任务过滤
        if task_id:
            query = query.filter(TweetData.task_id == task_id)
        
        query = query.order_by(TweetData.scraped_at.desc())
        
        # 使用优化的分页查询
        pagination_result = paginated_query(query, page, per_page)
        
        # 计算统计数据
        today = date.today()
        data_stats = {
            'total_tweets': TweetData.query.count(),
            'today_tweets': TweetData.query.filter(func.date(TweetData.scraped_at) == today).count(),
            'avg_likes': db.session.query(func.avg(TweetData.likes)).filter(TweetData.likes.isnot(None)).scalar() or 0,
            'avg_retweets': db.session.query(func.avg(TweetData.retweets)).filter(TweetData.retweets.isnot(None)).scalar() or 0
        }
        
        # 格式化平均数
        data_stats['avg_likes'] = round(data_stats['avg_likes'], 1)
        data_stats['avg_retweets'] = round(data_stats['avg_retweets'], 1)
        
        # 获取任务列表用于筛选
        tasks = ScrapingTask.query.order_by(ScrapingTask.created_at.desc()).limit(50).all()
        
        return render_template('data_optimized.html',
                             tweets=pagination_result.items,
                             pagination=pagination_result,
                             data_stats=data_stats,
                             tasks=tasks,
                             search=search,
                             current_task_id=task_id)
    except Exception as e:
        logger.error(f'Error in data route: {e}')
        return render_template('error.html', error=str(e)), 500

@app.route('/config')
@cached_api(timeout=300)
def config():
    """系统配置页面 - 带缓存优化"""
    try:
        # 获取当前配置
        config_data = {}
        
        # 从数据库获取配置
        configs = SystemConfig.query.all()
        for cfg in configs:
            config_data[cfg.key] = cfg.value
        
        # 从配置文件加载AdsPower配置
        # AdsPower 配置现在由配置文件管理，不再传递给模板
        # adspower_config = get_adspower_config()
        
        return render_template('config_optimized.html', config=config_data)
    except Exception as e:
        logger.error(f'Error in config route: {e}')
        return render_template('error.html', error=str(e)), 500

@app.route('/scheduler')
@cached_api(timeout=120)
def scheduler():
    """任务调度页面 - 带缓存优化"""
    try:
        return render_template('scheduler.html')
    except Exception as e:
        logger.error(f'Error in scheduler route: {e}')
        return render_template('error.html', error=str(e)), 500

# 优化的API接口
@app.route('/api/status')
@cached_api(timeout=30)
@measure_time
def api_status():
    """系统状态API - 带缓存和性能监控"""
    try:
        # 获取任务统计
        total_tasks = ScrapingTask.query.count()
        running_tasks = ScrapingTask.query.filter_by(status='running').count()
        completed_tasks = ScrapingTask.query.filter_by(status='completed').count()
        failed_tasks = ScrapingTask.query.filter_by(status='failed').count()
        queued_tasks = ScrapingTask.query.filter_by(status='queued').count()
        
        # 获取推文统计
        total_tweets = TweetData.query.count()
        today_tweets = TweetData.query.filter(
            db.func.date(TweetData.scraped_at) == db.func.date(db.func.now())
        ).count()
        
        # 获取性能统计
        performance_stats = performance_middleware.get_stats()
        cache_stats = api_cache.get_stats() if api_cache else {}
        
        # 兼容前端期望的数据结构
        return jsonify({
            'success': True,
            'is_running': running_tasks > 0,  # 兼容base_optimized.html中的is_running字段
            'data': {
                'tasks': {
                    'total': total_tasks,
                    'running': running_tasks,
                    'completed': completed_tasks,
                    'failed': failed_tasks,
                    'queued': queued_tasks
                },
                'tweets': {
                    'total': total_tweets,
                    'today': today_tweets
                },
                'performance': performance_stats,
                'cache': cache_stats,
                'system_running': running_tasks > 0,
                'timestamp': datetime.utcnow().isoformat()
            }
        })
    except Exception as e:
        logger.error(f'Error in api_status: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/influencers', methods=['GET'])
@cached_api(timeout=60)
@measure_time
def api_get_influencers():
    """获取博主列表API - 带缓存和分页优化"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        category = request.args.get('category')
        is_active = request.args.get('is_active')
        
        # 构建查询
        query = TwitterInfluencer.query
        
        if category:
            query = query.filter(TwitterInfluencer.category == category)
        if is_active is not None:
            query = query.filter(TwitterInfluencer.is_active == (is_active.lower() == 'true'))
        
        query = query.order_by(TwitterInfluencer.updated_at.desc())
        
        # 使用优化的分页查询
        pagination_result = paginated_query(query, page, per_page)
        
        return jsonify({
            'success': True,
            'data': {
                'influencers': [inf.to_dict() for inf in pagination_result.items],
                'pagination': {
                    'page': pagination_result.page,
                    'per_page': pagination_result.per_page,
                    'total': pagination_result.total,
                    'pages': pagination_result.pages,
                    'has_prev': pagination_result.has_prev,
                    'has_next': pagination_result.has_next
                }
            }
        })
    except Exception as e:
        logger.error(f'Error in api_get_influencers: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/influencers', methods=['POST'])
@invalidate_cache(['/api/influencers', '/api/influencers/stats', '/api/influencers/categories'])
@measure_time
def api_add_influencer():
    """添加博主API - 带缓存失效"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['name', 'username', 'profile_url']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # 检查用户名是否已存在
        existing = TwitterInfluencer.query.filter_by(username=data['username']).first()
        if existing:
            return jsonify({'success': False, 'error': 'Username already exists'}), 400
        
        # 创建新博主
        influencer = TwitterInfluencer(
            name=data['name'],
            username=data['username'],
            profile_url=data['profile_url'],
            description=data.get('description', ''),
            category=data.get('category', ''),
            followers_count=data.get('followers_count', 0)
        )
        
        db.session.add(influencer)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': influencer.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error in api_add_influencer: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tasks', methods=['POST'])
@invalidate_cache(['/api/tasks', '/api/status'])
@measure_time
def api_create_task():
    """创建新任务"""
    try:
        data = request.get_json()
        
        # 验证任务名称
        task_name = data.get('name', '').strip()
        if not task_name:
            return jsonify({'success': False, 'error': '任务名称不能为空'}), 400
        
        # 验证关键词和目标账号至少填写一个
        target_keywords = data.get('target_keywords', [])
        target_accounts = data.get('target_accounts', [])
        
        if not target_keywords and not target_accounts:
            return jsonify({'success': False, 'error': '关键词和目标账号至少需要填写一个'}), 400
        
        # 检查是否为多博主任务（多个目标账号）
        if len(target_accounts) > 1:
            app.logger.info(f"检测到多博主任务，将拆分为 {len(target_accounts)} 个子任务")
            
            # 创建主任务（用于统计和管理）
            main_task = ScrapingTask(
                name=f"{task_name} (主任务)",
                target_accounts=json.dumps(target_accounts),
                target_keywords=json.dumps(target_keywords),
                max_tweets=data.get('max_tweets', 50),
                min_likes=data.get('min_likes', 0),
                min_retweets=data.get('min_retweets', 0),
                min_comments=data.get('min_comments', 0),
                status='pending',
                notes=f"多博主并行任务，包含 {len(target_accounts)} 个博主: {', '.join(target_accounts)}"
            )
            
            db.session.add(main_task)
            db.session.flush()  # 获取主任务ID
            
            # 为每个博主创建子任务
            sub_task_ids = []
            for i, account in enumerate(target_accounts, 1):
                sub_task = ScrapingTask(
                    name=f"{task_name} - {account}",
                    target_accounts=json.dumps([account]),
                    target_keywords=json.dumps(target_keywords),
                    max_tweets=data.get('max_tweets', 50),
                    min_likes=data.get('min_likes', 0),
                    min_retweets=data.get('min_retweets', 0),
                    min_comments=data.get('min_comments', 0),
                    status='pending',
                    notes=f"子任务 {i}/{len(target_accounts)} - 博主: {account}"
                )
                
                db.session.add(sub_task)
                db.session.flush()  # 获取子任务ID
                sub_task_ids.append(sub_task.id)
            
            db.session.commit()
            
            logger.info(f"多博主任务创建成功: 主任务ID={main_task.id}, 子任务IDs={sub_task_ids}")
            
            return jsonify({
                'success': True, 
                'task_id': main_task.id,
                'sub_task_ids': sub_task_ids,
                'task_type': 'multi_blogger',
                'message': f'成功创建多博主任务，包含 {len(target_accounts)} 个子任务'
            })
        
        else:
            # 单博主任务，保持原有逻辑
            task = ScrapingTask(
                name=task_name,
                target_accounts=json.dumps(target_accounts),
                target_keywords=json.dumps(target_keywords),
                max_tweets=data.get('max_tweets', 50),
                min_likes=data.get('min_likes', 0),
                min_retweets=data.get('min_retweets', 0),
                min_comments=data.get('min_comments', 0),
                status='pending'
            )
            
            db.session.add(task)
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'task_id': task.id,
                'task_type': 'single_blogger'
            })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建任务失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/tasks', methods=['GET'])
@cached_api(timeout=30)
@measure_time
def api_get_tasks():
    """获取任务列表API - 带缓存和分页优化"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        status = request.args.get('status')
        
        # 构建查询
        query = ScrapingTask.query
        
        if status:
            query = query.filter(ScrapingTask.status == status)
        
        query = query.order_by(ScrapingTask.created_at.desc())
        
        # 使用优化的分页查询
        pagination_result = paginated_query(query, page, per_page)
        
        # 计算统计数据
        total_tasks = ScrapingTask.query.count()
        pending_tasks = ScrapingTask.query.filter_by(status='pending').count()
        running_tasks = ScrapingTask.query.filter_by(status='running').count()
        completed_tasks = ScrapingTask.query.filter_by(status='completed').count()
        failed_tasks = ScrapingTask.query.filter_by(status='failed').count()
        
        return jsonify({
            'success': True,
            'tasks': [task.to_dict() for task in pagination_result.items],
            'stats': {
                'total': total_tasks,
                'pending': pending_tasks,
                'running': running_tasks,
                'completed': completed_tasks,
                'failed': failed_tasks
            },
            'pagination': {
                'page': pagination_result.page,
                'per_page': pagination_result.per_page,
                'total': pagination_result.total,
                'pages': pagination_result.pages,
                'has_prev': pagination_result.has_prev,
                'has_next': pagination_result.has_next
            }
        })
    except Exception as e:
        logger.error(f'Error in api_get_tasks: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@invalidate_cache(['/api/tasks', '/api/status'])
@measure_time
def api_delete_task(task_id):
    """删除任务"""
    try:
        task = ScrapingTask.query.get_or_404(task_id)
        
        # 删除相关的推文数据
        TweetData.query.filter_by(task_id=task_id).delete()
        
        # 删除任务
        db.session.delete(task)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '任务已删除'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error in api_delete_task: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>/start', methods=['POST'])
@invalidate_cache(['/api/tasks', '/api/status'])
@measure_time
def api_start_task(task_id):
    """启动任务"""
    logger.info(f"收到启动任务请求: task_id={task_id}")
    
    try:
        # 获取任务信息
        task = ScrapingTask.query.get(task_id)
        if not task:
            return jsonify({'success': False, 'error': '任务不存在'}), 404
        
        # 检查任务管理器是否可用
        if not task_manager:
            return jsonify({'success': False, 'error': '任务管理器未初始化'}), 500
        
        # 检查任务是否已在运行
        if task_manager.is_task_running(task_id):
            error_msg = '该任务已在运行中'
            logger.warning(f"任务启动失败 - {error_msg}: task_id={task_id}")
            return jsonify({'success': False, 'error': error_msg}), 400
        
        # 检查是否可以启动新任务
        if not task_manager.can_start_task():
            status = task_manager.get_task_status()
            # 当达到并发限制时，自动将任务加入队列
            if status['running_count'] >= status['max_concurrent']:
                logger.info(f"任务 {task_id} 将加入队列等待执行")
                try:
                    success, message = task_manager.start_task(task_id)  # 这会自动加入队列
                    if success:
                        return jsonify({
                            'success': True, 
                            'message': f'任务已加入队列，{message}',
                            'queued': True
                        })
                    else:
                        return jsonify({
                            'success': False, 
                            'error': f'加入队列失败: {message}'
                        }), 400
                except Exception as e:
                    logger.error(f"加入队列失败: {str(e)}")
                    return jsonify({
                        'success': False, 
                        'error': f'加入队列失败: {str(e)}'
                    }), 500
            else:
                error_msg = f'无法启动任务，运行任务数: {status["running_count"]}/{status["max_concurrent"]}'
                logger.error(f"任务启动失败 - {error_msg}: task_id={task_id}")
                return jsonify({
                    'success': False, 
                    'error': error_msg
                }), 400
        
        # 启动任务
        logger.info(f"开始启动任务: task_id={task_id}")
        success, message = task_manager.start_task(task_id)
        if success:
            logger.info(f"任务启动成功: task_id={task_id}, message={message}")
            return jsonify({'success': True, 'message': message})
        else:
            logger.error(f"任务启动失败: task_id={task_id}, message={message}")
            return jsonify({
                'success': False, 
                'error': f'任务启动失败: {message}'
            }), 400
        
    except Exception as e:
        logger.error(f"任务启动异常: task_id={task_id}, exception={str(e)}")
        return jsonify({
            'success': False, 
            'error': f'任务启动异常: {str(e)}'
        }), 500

@app.route('/api/tasks/<int:task_id>/stop', methods=['POST'])
@invalidate_cache(['/api/tasks', '/api/status'])
@measure_time
def api_stop_task(task_id):
    """停止任务"""
    try:
        # 检查任务管理器是否可用
        if not task_manager:
            return jsonify({'success': False, 'error': '任务管理器未初始化'}), 500
        
        success, message = task_manager.stop_task(task_id)
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400
    except Exception as e:
        logger.error(f'Error in api_stop_task: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>/restart', methods=['POST'])
@invalidate_cache(['/api/tasks', '/api/status'])
@measure_time
def api_restart_task(task_id):
    """重新启动任务"""
    try:
        # 检查任务管理器是否可用
        if not task_manager:
            return jsonify({'success': False, 'error': '任务管理器未初始化'}), 500
        
        # 检查任务是否已在运行
        if task_manager.is_task_running(task_id):
            return jsonify({'success': False, 'error': '该任务已在运行中，请先停止'}), 400
        
        # 获取任务
        task = ScrapingTask.query.get(task_id)
        if not task:
            return jsonify({'success': False, 'error': '任务不存在'}), 404
        
        # 重置任务状态
        task.status = 'pending'
        task.progress = 0
        task.error_message = None
        task.started_at = None
        task.completed_at = None
        db.session.commit()
        
        # 启动任务
        success, message = task_manager.start_task(task_id)
        if success:
            return jsonify({'success': True, 'message': f'任务重启成功: {message}'})
        else:
            return jsonify({'success': False, 'error': f'任务重启失败: {message}'}), 400
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error in api_restart_task: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

# 性能监控API
@app.route('/api/performance/stats')
def api_performance_stats():
    """获取性能统计信息"""
    try:
        stats = {
            'middleware': performance_middleware.get_stats(),
            'cache': api_cache.get_stats() if api_cache else {},
            'database': db_optimizer.get_query_stats() if db_optimizer else {},
            'static': static_optimizer.get_optimization_stats() if static_optimizer else {}
        }
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        logger.error(f'Error in api_performance_stats: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/performance/clear-cache', methods=['POST'])
def api_clear_cache():
    """清除所有缓存"""
    try:
        if api_cache:
            api_cache.invalidate()
        
        return jsonify({
            'success': True,
            'message': 'Cache cleared successfully'
        })
    except Exception as e:
        logger.error(f'Error in api_clear_cache: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

# 定时任务管理API
@app.route('/api/scheduler/tasks', methods=['GET'])
@cached_api(timeout=30)
@measure_time
def api_get_scheduled_tasks():
    """获取所有定时任务"""
    try:
        if not task_scheduler:
            return jsonify({'success': False, 'error': '定时任务调度器未初始化'}), 500
        
        tasks = task_scheduler.get_all_tasks()
        return jsonify({'success': True, 'data': tasks})
        
    except Exception as e:
        logger.error(f'Error in api_get_scheduled_tasks: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scheduler/tasks/<task_id>', methods=['GET'])
@cached_api(timeout=30)
@measure_time
def api_get_scheduled_task(task_id):
    """获取指定定时任务详情"""
    try:
        if not task_scheduler:
            return jsonify({'success': False, 'error': '定时任务调度器未初始化'}), 500
        
        task = task_scheduler.get_task(task_id)
        if task:
            return jsonify({'success': True, 'data': task})
        else:
            return jsonify({'success': False, 'error': f'任务 {task_id} 不存在'}), 404
            
    except Exception as e:
        logger.error(f'Error in api_get_scheduled_task: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scheduler/tasks', methods=['POST'])
@invalidate_cache(['/api/scheduler/tasks', '/api/scheduler/status'])
@measure_time
def api_create_scheduled_task():
    """创建新的定时任务"""
    try:
        if not task_scheduler:
            return jsonify({'success': False, 'error': '定时任务调度器未初始化'}), 500
        
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['task_id', 'name', 'schedule_time', 'task_function']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({
                'success': False, 
                'error': f'缺少必填字段: {", ".join(missing_fields)}'
            }), 400
        
        # 验证任务函数是否存在
        task_function_name = data['task_function']
        if not hasattr(PredefinedTasks, task_function_name):
            return jsonify({
                'success': False, 
                'error': f'任务函数 {task_function_name} 不存在'
            }), 400
        
        task_function = getattr(PredefinedTasks, task_function_name)
        
        # 添加任务
        success = task_scheduler.add_task(
            task_id=data['task_id'],
            name=data['name'],
            schedule_time=data['schedule_time'],
            task_function=task_function,
            description=data.get('description', ''),
            max_retries=data.get('max_retries', 3),
            timeout_minutes=data.get('timeout_minutes', 60),
            enabled=data.get('enabled', True)
        )
        
        if success:
            return jsonify({'success': True, 'message': f'任务 {data["task_id"]} 创建成功'})
        else:
            return jsonify({'success': False, 'error': '任务创建失败'}), 400
            
    except Exception as e:
        logger.error(f'Error in api_create_scheduled_task: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scheduler/tasks/<task_id>/enable', methods=['POST'])
@invalidate_cache(['/api/scheduler/tasks', '/api/scheduler/status'])
@measure_time
def api_enable_scheduled_task(task_id):
    """启用定时任务"""
    try:
        if not task_scheduler:
            return jsonify({'success': False, 'error': '定时任务调度器未初始化'}), 500
        
        success = task_scheduler.enable_task(task_id)
        if success:
            return jsonify({'success': True, 'message': f'任务 {task_id} 已启用'})
        else:
            return jsonify({'success': False, 'error': f'任务 {task_id} 不存在'}), 404
            
    except Exception as e:
        logger.error(f'Error in api_enable_scheduled_task: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scheduler/tasks/<task_id>/disable', methods=['POST'])
@invalidate_cache(['/api/scheduler/tasks', '/api/scheduler/status'])
@measure_time
def api_disable_scheduled_task(task_id):
    """禁用定时任务"""
    try:
        if not task_scheduler:
            return jsonify({'success': False, 'error': '定时任务调度器未初始化'}), 500
        
        success = task_scheduler.disable_task(task_id)
        if success:
            return jsonify({'success': True, 'message': f'任务 {task_id} 已禁用'})
        else:
            return jsonify({'success': False, 'error': f'任务 {task_id} 不存在'}), 404
            
    except Exception as e:
        logger.error(f'Error in api_disable_scheduled_task: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scheduler/tasks/<task_id>/run', methods=['POST'])
@invalidate_cache(['/api/scheduler/tasks', '/api/scheduler/status'])
@measure_time
def api_run_scheduled_task(task_id):
    """立即执行定时任务"""
    try:
        if not task_scheduler:
            return jsonify({'success': False, 'error': '定时任务调度器未初始化'}), 500
        
        success = task_scheduler.run_task_now(task_id)
        if success:
            return jsonify({'success': True, 'message': f'任务 {task_id} 已开始执行'})
        else:
            return jsonify({'success': False, 'error': f'任务 {task_id} 不存在或无法执行'}), 404
            
    except Exception as e:
        logger.error(f'Error in api_run_scheduled_task: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scheduler/tasks/<task_id>', methods=['DELETE'])
@invalidate_cache(['/api/scheduler/tasks', '/api/scheduler/status'])
@measure_time
def api_delete_scheduled_task(task_id):
    """删除定时任务"""
    try:
        if not task_scheduler:
            return jsonify({'success': False, 'error': '定时任务调度器未初始化'}), 500
        
        success = task_scheduler.remove_task(task_id)
        if success:
            return jsonify({'success': True, 'message': f'任务 {task_id} 已删除'})
        else:
            return jsonify({'success': False, 'error': f'任务 {task_id} 不存在'}), 404
            
    except Exception as e:
        logger.error(f'Error in api_delete_scheduled_task: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scheduler/status', methods=['GET'])
@cached_api(timeout=30)
@measure_time
def api_get_scheduler_status():
    """获取调度器状态"""
    try:
        if not task_scheduler:
            return jsonify({'success': False, 'error': '定时任务调度器未初始化'}), 500
        
        status = task_scheduler.get_status()
        return jsonify({'success': True, 'data': status})
        
    except Exception as e:
        logger.error(f'Error in api_get_scheduler_status: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scheduler/statistics', methods=['GET'])
@cached_api(timeout=30)
@measure_time
def api_get_scheduler_statistics():
    """获取调度器统计信息"""
    try:
        if not task_scheduler:
            return jsonify({'success': False, 'error': '定时任务调度器未初始化'}), 500
        
        stats = task_scheduler.get_statistics()
        return jsonify({'success': True, 'data': stats})
        
    except Exception as e:
        logger.error(f'Error in api_get_scheduler_statistics: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/update_config', methods=['POST'])
@invalidate_cache(['/config', '/api/status'])
def update_config():
    """更新配置"""
    try:
        # 处理所有配置字段
        # AdsPower 配置现在由配置文件管理，不再从表单获取
        
        configs_to_update = {
            
            # 飞书配置
            'feishu_app_id': request.form.get('feishu_app_id', ''),
            'feishu_app_secret': request.form.get('feishu_app_secret', ''),
            'feishu_spreadsheet_token': request.form.get('feishu_spreadsheet_token', ''),
            'feishu_table_id': request.form.get('feishu_table_id', ''),
            'feishu_enabled': request.form.get('feishu_enabled', 'false'),
            'feishu_async_enabled': request.form.get('feishu_async_enabled', 'false'),
            
            # 导出配置
            'export_fields': request.form.get('export_fields', ''),
            'max_tweets_per_target': request.form.get('max_tweets_per_target', '8'),
            'max_total_tweets': request.form.get('max_total_tweets', '200'),
            'min_likes': request.form.get('min_likes', '50'),
            'min_comments': request.form.get('min_comments', '10'),
            'min_retweets': request.form.get('min_retweets', '20'),
            
            # 系统配置
            'auto_backup': request.form.get('auto_backup', 'false'),
            'enable_notifications': request.form.get('enable_notifications', 'false')
        }
        
        # 更新或创建配置记录
        for key, value in configs_to_update.items():
            # 清理配置值，避免重复拼接
            clean_value = str(value).strip()
            
            # AdsPower API Key 等配置现在由配置文件管理，不再进行特殊处理
            
            config = SystemConfig.query.filter_by(key=key).first()
            if config:
                config.value = clean_value
                config.updated_at = datetime.utcnow()
            else:
                config = SystemConfig(
                    key=key,
                    value=clean_value,
                    description=f'系统配置: {key}'
                )
                db.session.add(config)
        
        # 更新全局配置
        global ADS_POWER_CONFIG, FEISHU_CONFIG, FILTER_CONFIG
        
        # AdsPower 配置现在由配置文件管理，不再从表单更新
        
        # AdsPower 配置现在由配置文件管理，不再保存到独立文件
        
        # 更新飞书配置到配置文件
        try:
            feishu_config_data = {
                'app_id': configs_to_update['feishu_app_id'],
                'app_secret': configs_to_update['feishu_app_secret'],
                'spreadsheet_token': configs_to_update['feishu_spreadsheet_token'],
                'table_id': configs_to_update['feishu_table_id'],
                'enabled': configs_to_update['feishu_enabled'] == 'true',
                'async_enabled': configs_to_update['feishu_async_enabled'] == 'true'
            }
            update_feishu_config(feishu_config_data)
            
            # 重新加载配置到内存
            global FEISHU_CONFIG
            FEISHU_CONFIG = get_feishu_config()
            
            logger.info("飞书配置已保存到 config/feishu_config.py")
        except Exception as e:
            logger.error(f"保存飞书配置文件失败: {str(e)}")
        
        # 更新过滤配置
        FILTER_CONFIG.update({
            'max_tweets_per_target': int(configs_to_update['max_tweets_per_target']),
            'max_total_tweets': int(configs_to_update['max_total_tweets']),
            'min_likes': int(configs_to_update['min_likes']),
            'min_comments': int(configs_to_update['min_comments']),
            'min_retweets': int(configs_to_update['min_retweets'])
        })
        
        db.session.commit()
        logger.info('Configuration updated successfully')
        
        return jsonify({
            'success': True,
            'message': '配置保存成功！'
        })
        
    except Exception as e:
        logger.error(f'Error in update_config: {e}')
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'配置保存失败: {str(e)}'
        }), 500

@app.route('/api/config/feishu/test', methods=['POST'])
def api_test_feishu_connection():
    """测试飞书连接"""
    try:
        # 从feishu_config.py文件获取配置
        feishu_config = get_feishu_config()
        
        # 检查飞书是否启用
        if not feishu_config.get('enabled'):
            return jsonify({
                'success': False,
                'error': '飞书同步未启用，请在配置文件中启用后重试',
                'status_code': 400,
                'logs': ['飞书同步状态: 未启用']
            }), 400
        
        # 检查必填字段
        required_fields = ['app_id', 'app_secret', 'spreadsheet_token', 'table_id']
        missing_fields = []
        for field in required_fields:
            if not feishu_config.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            return jsonify({
                'success': False,
                'error': f'飞书配置不完整，缺少字段: {", ".join(missing_fields)}。请检查 config/feishu_config.py 文件',
                'status_code': 400,
                'logs': [f'配置文件路径: config/feishu_config.py', f'缺少字段: {", ".join(missing_fields)}']
            }), 400
        
        # 尝试创建CloudSyncManager并测试连接
        try:
            from utils.cloud_sync import CloudSyncManager
            
            # 创建测试配置
            test_config = {
                'feishu': {
                    'enabled': True,
                    'app_id': feishu_config['app_id'],
                    'app_secret': feishu_config['app_secret'],
                    'spreadsheet_token': feishu_config['spreadsheet_token'],
                    'table_id': feishu_config['table_id']
                }
            }
            
            # 创建CloudSyncManager实例
            sync_manager = CloudSyncManager(test_config)
            
            # 尝试设置飞书配置
            setup_result = sync_manager.setup_feishu(
                feishu_config['app_id'],
                feishu_config['app_secret']
            )
            
            if setup_result:
                return jsonify({
                    'success': True,
                    'message': '飞书连接测试成功！配置有效，可以正常使用',
                    'logs': [
                        '✅ 飞书配置加载成功',
                        '✅ CloudSyncManager 初始化成功',
                        '✅ 飞书API连接测试通过',
                        f'📊 表格Token: {feishu_config["spreadsheet_token"][:10]}...',
                        f'📋 数据表ID: {feishu_config["table_id"]}',
                        f'🔄 异步同步: {"启用" if feishu_config.get("async_enabled") else "禁用"}'
                    ]
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '飞书配置设置失败，请检查配置参数是否正确',
                    'logs': [
                        '❌ 飞书配置设置失败',
                        '💡 请检查App ID、App Secret、表格Token和数据表ID是否正确',
                        '💡 请确保飞书应用有访问表格的权限'
                    ]
                })
                
        except ImportError as e:
            return jsonify({
                'success': False,
                'error': 'CloudSyncManager模块导入失败',
                'logs': [f'导入错误: {str(e)}']
            }), 500
            
        except Exception as sync_error:
            logger.error(f'飞书连接测试失败: {sync_error}')
            return jsonify({
                'success': False,
                'error': f'飞书连接测试失败: {str(sync_error)}',
                'logs': [
                    f'❌ 连接测试失败: {str(sync_error)}',
                    '💡 请检查网络连接和飞书配置参数',
                    '💡 确保飞书应用权限配置正确'
                ]
            }), 500
        
    except Exception as e:
        logger.error(f'Error in api_test_feishu_connection: {e}')
        return jsonify({
            'success': False,
            'error': f'飞书连接测试失败: {str(e)}',
            'logs': [f'系统错误: {str(e)}']
        }), 500

@app.route('/api/test_adspower_connection', methods=['POST'])
def api_test_adspower_connection():
    """测试AdsPower连接和环境检测（优化版）"""
    try:
        data = request.get_json() or {}
        
        # 从数据库获取配置信息
        configs = SystemConfig.query.all()
        config_dict = {cfg.key: cfg.value for cfg in configs}
        
        # 获取API配置信息
        # 使用配置文件中的 AdsPower 配置
        adspower_config = get_adspower_config()
        api_host = adspower_config['local_api_url']
        user_ids = adspower_config['user_ids']
        api_key = adspower_config.get('api_key', '')  # 从配置中获取 api_key
        
        # 直接进行连接测试，不检查 API 状态
        
        # 创建临时AdsPowerManager进行诊断
        from utils.adspower_manager import AdsPowerManager, AdsPowerConfig
        
        # 从完整URL中解析主机和端口
        import re
        url_match = re.match(r'https?://([^:]+)(?::(\d+))?', api_host)
        if url_match:
            host = url_match.group(1)
            port = int(url_match.group(2)) if url_match.group(2) else 50325
        else:
            # 如果不是完整URL，假设是主机名
            host = api_host.replace('http://', '').replace('https://', '').split(':')[0]
            port_part = api_host.replace('http://', '').replace('https://', '').split(':')
            port = int(port_part[1]) if len(port_part) > 1 and port_part[1].isdigit() else 50325
        
        temp_config = AdsPowerConfig(
            host=host,
            port=port,
            api_key=api_key,
            user_ids=user_ids if isinstance(user_ids, list) else []
        )
        
        # 创建临时管理器（不保存配置文件）
        manager = AdsPowerManager(temp_config)
        
        # 执行增强的健康检查
        health_report = manager.perform_health_check()
        
        # 检查AdsPower是否可用
        if not health_report['adspower_available']:
            return jsonify({
                'success': False,
                'message': health_report['message'],
                'diagnosis': health_report.get('diagnosis', {}),
                'download_url': 'https://www.adspower.net/share/hftJaRHMQl1r7jw'
            })
        
        # 检查用户ID验证结果
        if len(health_report['user_validation']['invalid_ids']) > 0:
            invalid_ids = health_report['user_validation']['invalid_ids']
            return jsonify({
                'success': False,
                'message': f'用户ID验证失败，以下用户ID不存在: {", ".join(invalid_ids)}',
                'user_validation': health_report['user_validation'],
                'active_browsers': health_report.get('active_browsers', []),
                'browser_status': health_report.get('browser_status', {}),
                'diagnosis': health_report.get('diagnosis', {}),
                'download_url': 'https://www.adspower.net/share/hftJaRHMQl1r7jw'
            })
        
        # 返回成功结果
        return jsonify({
            'success': True,
            'message': health_report['message'],
            'user_validation': health_report['user_validation'],
            'active_browsers': health_report.get('active_browsers', []),
            'browser_status': health_report.get('browser_status', {}),
            'api_url': api_host
        })
            
    except Exception as e:
        logger.error(f'Error in api_test_adspower_connection: {e}')
        return jsonify({
            'success': False,
            'message': f'测试失败: {str(e)}',
            'download_url': 'https://www.adspower.net/share/hftJaRHMQl1r7jw'
        })

@app.route('/api/validate_adspower_environment', methods=['GET'])
def validate_adspower_environment():
    """验证AdsPower运行环境（系统启动前检查）"""
    try:
        adspower_manager = AdsPowerManager()
        
        # 检查AdsPower是否可用
        is_available, message = adspower_manager.check_availability()
        
        if not is_available:
            return jsonify({
                'success': False,
                'message': message,
                'download_url': 'https://www.adspower.net/share/hftJaRHMQl1r7jw'
            })
        
        # 获取配置的用户ID列表
        config = adspower_manager.load_config()
        user_ids = config.user_ids
        
        if not user_ids:
            return jsonify({
                'success': False,
                'message': '未配置AdsPower用户ID，请先在系统配置中添加用户ID'
            })
        
        # 验证用户ID
        valid_users = adspower_manager.get_valid_user_ids(user_ids)
        invalid_users = [uid for uid in user_ids if uid not in valid_users]
        
        if invalid_users:
            return jsonify({
                'success': False,
                'message': f'以下用户ID无效: {", ".join(invalid_users)}，请检查配置',
                'valid_users': valid_users,
                'invalid_users': invalid_users
            })
        
        return jsonify({
            'success': True,
            'message': f'AdsPower环境验证通过，{len(valid_users)} 个用户ID可用',
            'valid_users': valid_users
        })
        
    except Exception as e:
        logger.error(f"验证AdsPower环境时发生错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'环境验证失败: {str(e)}'
        })

@app.route('/api/diagnose/adspower', methods=['GET'])
def diagnose_adspower():
    """AdsPower系统诊断接口"""
    try:
        # AdsPower 配置现在由配置文件管理
        adspower_config = get_adspower_config()
        
        # 创建AdsPowerManager进行诊断
        from utils.adspower_manager import AdsPowerManager
        
        manager = AdsPowerManager()
        manager._config = temp_config
        
        # 执行诊断
        diagnosis = manager.diagnose_adspower()
        
        return jsonify({
            'success': True,
            'diagnosis': diagnosis
        })
        
    except Exception as e:
        logger.error(f'Error in diagnose_adspower: {e}')
        return jsonify({
            'success': False,
            'message': f'诊断失败: {str(e)}',
            'diagnosis': {
                'reachable': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'recommendation': '系统诊断过程中发生错误，请检查配置或联系技术支持。',
                'suggestions': [
                    "✅ 检查AdsPower是否已正确安装",
                    "✅ 确认系统配置是否正确",
                    "✅ 重启AdsPower后重试"
                ],
                'download_url': 'https://www.adspower.net/share/hftJaRHMQl1r7jw'
            }
        })

# 错误处理
@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error='Page not found'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('error.html', error='Internal server error'), 500

# 初始化应用
try:
    with app.app_context():
        init_database()
        load_config_from_database()
        init_optimizers()
        # 初始化任务管理器和调度器
        init_task_manager()
        init_task_scheduler()
        logger.info('Application initialized successfully')
except Exception as e:
    logger.error(f'Application initialization failed: {e}')
    raise

if __name__ == '__main__':
    try:
        app.start_time = time.time()
        
        # 预热缓存
        if api_cache:
            from utils.api_cache_manager import warm_up_cache
            warm_up_cache()
        
        logger.info('🚀 启动优化版Flask Web应用...')
        logger.info(f'📍 访问地址: http://localhost:8091')
        
        # 启动应用
        app.run(
            host='0.0.0.0',
            port=8091,
            debug=False,  # 生产环境关闭debug
            threaded=True,
            use_reloader=False
        )
    except KeyboardInterrupt:
        logger.info('Application stopped by user')
    except Exception as e:
        logger.error(f'Application error: {e}')
    finally:
        logger.info('Application shutdown complete')