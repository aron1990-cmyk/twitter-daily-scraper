#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter抓取Web管理系统
提供Web界面进行关键词配置、任务管理和数据查看

注意：此文件已被注释掉，请使用 web_app_optimized.py
"""

# 整个文件已被注释掉，请使用 web_app_optimized.py
# 以下代码已停用

'''
原始代码已注释掉，请使用优化版本 web_app_optimized.py

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

# 导入现有模块

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

# 飞书配置信息
FEISHU_CONFIG = {
    'app_id': '',
    'app_secret': '',
    'spreadsheet_token': '',
    'table_id': '',
    'enabled': True,  # 默认启用飞书同步
    # 自动同步功能已注释掉 - 不再需要
    # 'auto_sync': False,  # 自动同步
    'async_enabled': True,  # 异步同步启用（默认开启）
    'async_max_workers': 2,  # 异步工作线程数
    'async_max_queue_size': 100,  # 异步队列最大大小
    'async_max_retries': 3,  # 异步重试次数
    'async_priority': 2  # 异步任务优先级（普通优先级）
}

# AdsPower配置信息
ADS_POWER_CONFIG = {
    'local_api_url': 'http://local.adspower.net:50325',
    'user_id': 'k11p9ypc',
    'multi_user_ids': [],
    'max_concurrent_tasks': 2,
    'task_timeout': 900,
    'browser_startup_delay': 2,
    'headless': False,
    'health_check': True
}
from models import TweetModel, ScrapingConfig
from utils.ads_browser_launcher import AdsPowerLauncher
from core.twitter_parser import TwitterParser
# from enhanced_twitter_parser import MultiWindowEnhancedScraper
# from optimized_scraping_engine import OptimizedScrapingEngine
from utils.cloud_sync import CloudSyncManager
from utils.excel_writer import ExcelWriter
from core.refactored_task_manager import RefactoredTaskManager

# 导入异步飞书同步模块
from core.async_feishu_sync import get_async_sync_manager, init_async_sync_service, shutdown_async_sync_service

# 导入定时任务调度器
from scheduler import TaskScheduler, PredefinedTasks

# P0+优化：导入系统监控和资源调度组件
from utils.system_monitor import SystemMonitor
from utils.resource_scheduler import ResourceScheduler
from utils.async_task_manager import AsyncTaskManager

# 创建Flask应用
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.debug = True
app.config['SECRET_KEY'] = 'twitter-scraper-web-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/aron/twitter-daily-scraper/instance/twitter_scraper.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 设置字符编码
app.config['JSON_AS_ASCII'] = False

# 配置日志
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
app.logger.setLevel(logging.INFO)

# 启用werkzeug HTTP请求日志输出用于调试
logging.getLogger('werkzeug').setLevel(logging.INFO)

@app.after_request
def after_request(response):
    """设置响应头，确保正确处理中文字符"""
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response

# 初始化Flask扩展
db = SQLAlchemy(app)

def load_config_from_database():
    """从数据库加载配置"""
    global ADS_POWER_CONFIG, FEISHU_CONFIG, TWITTER_TARGETS, FILTER_CONFIG, OUTPUT_CONFIG, BROWSER_CONFIG, LOG_CONFIG, CLOUD_SYNC_CONFIG
    
    try:
        configs = SystemConfig.query.all()
        config_dict = {cfg.key: cfg.value for cfg in configs}
        
        # 加载AdsPower配置
        if 'adspower_api_url' in config_dict:
            ADS_POWER_CONFIG['local_api_url'] = config_dict['adspower_api_url']
        # 注意：AdsPower API 状态配置现在由配置文件管理，不再从数据库加载
        # 注意：AdsPower API Key、用户ID、多用户ID列表等配置现在由配置文件管理
        # 这些字段已从Web界面中移除，不再从数据库加载
        if 'max_concurrent_tasks' in config_dict:
            ADS_POWER_CONFIG['max_concurrent_tasks'] = int(config_dict['max_concurrent_tasks'])
        if 'task_timeout' in config_dict:
            ADS_POWER_CONFIG['task_timeout'] = int(config_dict['task_timeout'])
        if 'request_interval' in config_dict:
            ADS_POWER_CONFIG['request_interval'] = float(config_dict['request_interval'])
        if 'user_rotation_enabled' in config_dict:
            ADS_POWER_CONFIG['user_rotation_enabled'] = config_dict['user_rotation_enabled'].lower() == 'true'
        if 'user_switch_interval' in config_dict:
            ADS_POWER_CONFIG['user_switch_interval'] = int(config_dict['user_switch_interval'])
        if 'api_retry_delay' in config_dict:
            ADS_POWER_CONFIG['api_retry_delay'] = float(config_dict['api_retry_delay'])
        if 'browser_startup_delay' in config_dict:
            ADS_POWER_CONFIG['browser_startup_delay'] = float(config_dict['browser_startup_delay'])
        if 'adspower_timeout' in config_dict:
            ADS_POWER_CONFIG['timeout'] = int(config_dict['adspower_timeout'])
        if 'adspower_retry_count' in config_dict:
            ADS_POWER_CONFIG['retry_count'] = int(config_dict['adspower_retry_count'])
        if 'adspower_retry_delay' in config_dict:
            ADS_POWER_CONFIG['retry_delay'] = int(config_dict['adspower_retry_delay'])
        if 'adspower_headless' in config_dict:
            ADS_POWER_CONFIG['headless'] = config_dict['adspower_headless'].lower() == 'true'
        if 'adspower_health_check' in config_dict:
            ADS_POWER_CONFIG['health_check'] = config_dict['adspower_health_check'].lower() == 'true'
        if 'adspower_window_visible' in config_dict:
            ADS_POWER_CONFIG['window_visible'] = config_dict['adspower_window_visible'].lower() == 'true'
        
        # 加载飞书配置
        if 'feishu_app_id' in config_dict:
            FEISHU_CONFIG['app_id'] = config_dict['feishu_app_id']
        if 'feishu_app_secret' in config_dict:
            FEISHU_CONFIG['app_secret'] = config_dict['feishu_app_secret']
        if 'feishu_spreadsheet_token' in config_dict:
            FEISHU_CONFIG['spreadsheet_token'] = config_dict['feishu_spreadsheet_token']
        if 'feishu_table_id' in config_dict:
            FEISHU_CONFIG['table_id'] = config_dict['feishu_table_id']
        if 'feishu_enabled' in config_dict:
            FEISHU_CONFIG['enabled'] = config_dict['feishu_enabled'].lower() == 'true'
        # 自动同步功能已注释掉 - 不再需要
        # if 'feishu_auto_sync' in config_dict:
        #     FEISHU_CONFIG['auto_sync'] = config_dict['feishu_auto_sync'].lower() == 'true'
        
        # 加载异步飞书配置（默认开启）
        if 'async_enabled' in config_dict:
            FEISHU_CONFIG['async_enabled'] = config_dict['async_enabled'].lower() == 'true'
        else:
            FEISHU_CONFIG['async_enabled'] = True  # 默认开启异步同步
        if 'async_max_workers' in config_dict:
            FEISHU_CONFIG['async_max_workers'] = int(config_dict['async_max_workers'])
        if 'async_max_queue_size' in config_dict:
            FEISHU_CONFIG['async_max_queue_size'] = int(config_dict['async_max_queue_size'])
        if 'async_max_retries' in config_dict:
            FEISHU_CONFIG['async_max_retries'] = int(config_dict['async_max_retries'])
        if 'async_priority' in config_dict:
            FEISHU_CONFIG['async_priority'] = int(config_dict['async_priority'])
        
        print("✅ 配置已从数据库加载完成")
        
    except Exception as e:
        print(f"⚠️ 配置加载失败: {e}")

def init_database():
    """初始化数据库"""
    with app.app_context():
        db.create_all()
        
        # 确保notes字段存在
        try:
            # 尝试添加notes字段（如果不存在）
            with db.engine.connect() as conn:
                conn.execute(db.text('ALTER TABLE scraping_task ADD COLUMN notes TEXT'))
                conn.commit()
        except Exception:
            # 字段已存在或其他错误，忽略
            pass
        
        # 强制刷新数据库连接和元数据
        db.session.commit()
        db.session.close()
        
        # 重置所有running状态的任务为pending状态
        # 这是为了解决系统重启后任务状态不一致的问题
        # 暂时注释掉，等应用启动后再处理
        # try:
        #     running_tasks = ScrapingTask.query.filter_by(status='running').all()
        #     if running_tasks:
        #         for task in running_tasks:
        #             task.status = 'pending'
        #         db.session.commit()
        # except Exception as e:
        #     print(f"⚠️ 重置任务状态失败: {e}")
        
        # 从数据库加载配置
        try:
            load_config_from_database()
        except Exception as e:
            print(f"⚠️ 配置加载失败: {e}，使用默认配置")
        
        # 注意：任务管理器已在应用启动时初始化，这里不需要重复初始化

# 数据库模型
class ScrapingTask(db.Model):
    """抓取任务模型"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    target_accounts = db.Column(db.Text)  # JSON格式存储
    target_keywords = db.Column(db.Text)  # JSON格式存储
    max_tweets = db.Column(db.Integer, default=50)
    min_likes = db.Column(db.Integer, default=0)
    min_retweets = db.Column(db.Integer, default=0)
    min_comments = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed, queued
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    result_count = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    notes = db.Column(db.Text)  # 任务备注，用于存储内容不足等提醒信息
    
    @property
    def keywords(self):
        """获取关键词列表，用于模板兼容性"""
        try:
            keywords_list = json.loads(self.target_keywords or '[]')
            return ','.join(keywords_list) if keywords_list else ''
        except:
            return self.target_keywords or ''
    
    @property
    def accounts(self):
        """获取账号列表，用于模板兼容性"""
        try:
            accounts_list = json.loads(self.target_accounts or '[]')
            return ','.join(accounts_list) if accounts_list else ''
        except:
            return self.target_accounts or ''
    
    @property
    def tweets_collected(self):
        """获取已收集的推文数量"""
        return self.result_count or 0
    
    def to_dict(self):
        try:
            target_accounts = json.loads(self.target_accounts or '[]')
        except (json.JSONDecodeError, TypeError):
            target_accounts = []
            
        try:
            target_keywords = json.loads(self.target_keywords or '[]')
        except (json.JSONDecodeError, TypeError):
            target_keywords = []
            
        return {
            'id': self.id,
            'name': self.name,
            'target_accounts': target_accounts,
            'target_keywords': target_keywords,
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
            'notes': self.notes
        }

class TweetData(db.Model):
    """推文数据模型"""
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('scraping_task.id'), nullable=False)
    username = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    likes = db.Column(db.Integer, default=0)
    comments = db.Column(db.Integer, default=0)
    retweets = db.Column(db.Integer, default=0)
    publish_time = db.Column(db.String(100))
    link = db.Column(db.Text)
    hashtags = db.Column(db.Text)  # 话题标签，JSON格式存储
    content_type = db.Column(db.String(50))  # 类型标签：搞钱、投放、副业干货、情绪类等
    scraped_at = db.Column(db.DateTime, default=datetime.utcnow)
    synced_to_feishu = db.Column(db.Boolean, default=False)
    
    # 增强内容字段
    full_content = db.Column(db.Text)  # 完整推文内容（详情页抓取）
    media_content = db.Column(db.Text)  # 多媒体内容，JSON格式存储
    thread_tweets = db.Column(db.Text)  # 推文线程，JSON格式存储
    quoted_tweet = db.Column(db.Text)  # 引用推文，JSON格式存储
    has_detailed_content = db.Column(db.Boolean, default=False)  # 是否包含详情页内容
    detail_error = db.Column(db.Text)  # 详情抓取错误信息
    
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
            'hashtags': json.loads(self.hashtags or '[]'),
            'content_type': self.content_type,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None,
            'synced_to_feishu': self.synced_to_feishu,
            'full_content': self.full_content,
            'media_content': json.loads(self.media_content) if self.media_content else [],
            'thread_tweets': json.loads(self.thread_tweets) if self.thread_tweets else [],
            'quoted_tweet': json.loads(self.quoted_tweet) if self.quoted_tweet else None,
            'has_detailed_content': self.has_detailed_content,
            'detail_error': self.detail_error
        }

class SystemConfig(db.Model):
    """系统配置模型"""
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class TwitterInfluencer(db.Model):
    """Twitter博主管理模型"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # 博主名称
    username = db.Column(db.String(50), nullable=False)  # Twitter用户名
    profile_url = db.Column(db.Text, nullable=False)  # 博主主页URL
    description = db.Column(db.Text)  # 博主描述
    category = db.Column(db.String(50))  # 分类：搞钱、投放、副业干货、情绪类等
    followers_count = db.Column(db.Integer, default=0)  # 粉丝数
    is_active = db.Column(db.Boolean, default=True)  # 是否启用
    last_scraped = db.Column(db.DateTime)  # 最后抓取时间
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

# 内容分类函数
def classify_content_type(content: str) -> str:
    """
    根据推文内容自动分类（仅作为建议，用户可自定义）
    
    Args:
        content: 推文内容
        
    Returns:
        内容类型分类建议，如果没有明确匹配则返回空字符串
    """
    if not content:
        return ''
    
    content_lower = content.lower()
    
    # 搞钱类关键词
    money_keywords = ['赚钱', '收入', '盈利', '投资', '理财', '副业', '创业', '商机', '变现', '收益', 
                     '财富', '金钱', '挣钱', '月入', '年入', '被动收入', '现金流', '投资回报']
    
    # 投放类关键词
    ads_keywords = ['投放', '广告', '推广', '营销', 'roi', 'cpm', 'cpc', 'ctr', '转化率', 
                   '获客', '引流', '投放策略', '广告优化', '素材', '创意', '投放效果']
    
    # 副业干货类关键词
    side_hustle_keywords = ['副业', '兼职', '自媒体', '内容创作', '知识付费', '在线教育', 
                           '技能变现', '个人品牌', '流量', '粉丝', '运营', '增长', '干货']
    
    # 情绪类关键词
    emotion_keywords = ['焦虑', '压力', '迷茫', '困惑', '开心', '快乐', '感动', '激动', 
                       '沮丧', '失望', '愤怒', '无奈', '感慨', '思考', '反思', '感悟']
    
    # 技术类关键词
    tech_keywords = ['ai', '人工智能', '机器学习', '深度学习', '算法', '编程', '代码', 
                    '开发', '技术', '工具', '软件', '应用', 'chatgpt', 'gpt', '自动化']
    
    # 检查各类关键词，只有明确匹配才返回分类
    if any(keyword in content_lower for keyword in money_keywords):
        return '搞钱'
    elif any(keyword in content_lower for keyword in ads_keywords):
        return '投放'
    elif any(keyword in content_lower for keyword in side_hustle_keywords):
        return '副业干货'
    elif any(keyword in content_lower for keyword in emotion_keywords):
        return '情绪类'
    elif any(keyword in content_lower for keyword in tech_keywords):
        return '技术类'
    else:
        return ''  # 返回空字符串，让用户自定义

def detect_account_type(account_name: str, account_description: str = '') -> str:
    """
    根据账号信息检测账号类型
    
    Args:
        account_name: 账号名称
        account_description: 账号描述
        
    Returns:
        账号类型
    """
    combined_text = f"{account_name} {account_description}".lower()
    
    # 技术博主关键词
    tech_keywords = [
        '程序员', '开发者', '工程师', 'developer', 'engineer', 'programmer',
        '前端', '后端', '全栈', 'frontend', 'backend', 'fullstack',
        'python', 'javascript', 'java', 'go', 'rust', 'ai', '人工智能',
        '算法', '架构师', 'cto', '技术', 'tech', 'code', '编程'
    ]
    
    # 营销博主关键词
    marketing_keywords = [
        '营销', '推广', '增长', '运营', '广告', 'marketing', 'growth',
        '投放', '获客', '转化', 'roi', '流量', '引流', '变现',
        '电商', '直播', '带货', '网红', 'kol', '博主'
    ]
    
    # 投资博主关键词
    investment_keywords = [
        '投资', '理财', '股票', '基金', '期货', '外汇', 'investment',
        '财经', '金融', '券商', '分析师', '交易员', 'trader',
        '币圈', '区块链', 'crypto', 'bitcoin', '量化', '价值投资'
    ]
    
    # 检查各类型关键词
    if any(keyword in combined_text for keyword in tech_keywords):
        return '技术博主'
    elif any(keyword in combined_text for keyword in marketing_keywords):
        return '营销博主'
    elif any(keyword in combined_text for keyword in investment_keywords):
        return '投资博主'
    
    return 'general'


# 重构TaskManager的导入
import queue
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple

class TaskState(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"

@dataclass
class TaskRequest:
    """任务请求数据结构"""
    task_id: int
    use_background_process: bool = True
    priority: int = 0
    retry_count: int = 0
    max_retries: int = 3

@dataclass
class TaskSlot:
    """任务槽位数据结构"""
    task_id: int
    user_id: str
    process: Optional[subprocess.Popen] = None
    thread: Optional[threading.Thread] = None
    config_file: Optional[str] = None
    start_time: Optional[datetime] = None
    is_background: bool = True


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
            
            # 保存到数据库（支持异步插入）
            saved_count = self._save_tweets_to_db(all_tweets, task_id, async_insert=True)
            
            # 更新任务状态
            task.status = 'completed'
            task.completed_at = datetime.utcnow()
            task.result_count = saved_count
            db.session.commit()
            
            # 关闭浏览器
            await parser.close()
            
            print(f"任务 {task_id} 完成，共抓取 {saved_count} 条推文")
            
            # 检查是否需要自动同步到飞书
            self._check_auto_sync_feishu(task_id)
            
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
    
    def _save_tweets_to_db(self, tweets: List[Dict], task_id: int, async_insert: bool = False) -> int:
        """保存推文到数据库，支持异步插入"""
        if not tweets:
            return 0
            
        # 判断是否使用异步插入
        use_async = async_insert or len(tweets) > 500  # 数据量大于500条时自动异步
        
        if use_async:
            try:
                # 使用异步任务管理器进行数据库插入
                task_manager = get_task_manager()
                if task_manager:
                    # 准备插入数据
                    insert_data = []
                    for tweet in tweets:
                        tweet_record = {
                            'task_id': task_id,
                            'username': tweet.get('username', ''),
                            'content': tweet.get('content', ''),
                            'likes': tweet.get('likes', 0),
                            'comments': tweet.get('comments', 0),
                            'retweets': tweet.get('retweets', 0),
                            'publish_time': tweet.get('publish_time', ''),
                            'link': tweet.get('link', ''),
                            'hashtags': json.dumps(tweet.get('hashtags', [])),
                            'content_type': classify_content_type(tweet.get('content', '')),
                            'full_content': tweet.get('full_content', ''),
                            'media_content': json.dumps(tweet.get('media', {'images': [], 'videos': []})),
                            'thread_tweets': json.dumps(tweet.get('thread_tweets', [])),
                            'quoted_tweet': json.dumps(tweet.get('quoted_tweet')) if tweet.get('quoted_tweet') else None,
                            'has_detailed_content': tweet.get('has_detailed_content', False),
                            'detail_error': tweet.get('detail_error'),
                            'scraped_at': datetime.utcnow().isoformat(),
                            'synced_to_feishu': False
                        }
                        insert_data.append(tweet_record)
                    
                    # 获取数据库路径
                    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
                    
                    # 提交异步插入任务
                    async_task_id = task_manager.submit_sqlite_insert(
                        db_path=db_path,
                        table='tweet_data',
                        data=insert_data
                    )
                    
                    print(f"✅ [异步插入] 推文数据已提交到异步队列，任务ID: {async_task_id}，数据量: {len(insert_data)} 条")
                    return len(insert_data)  # 返回预期插入数量
                    
            except Exception as e:
                print(f"❌ [异步插入] 异步插入失败: {e}，回退到同步方式")
                # 回退到同步方式
        
        # 同步方式插入（原有逻辑）
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
                    content_type=classify_content_type(tweet.get('content', '')),
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
    
    def _check_auto_sync_feishu(self, task_id: int):
        """检查是否需要自动同步到飞书（已注释掉 - 不再需要）"""
        # 自动同步功能已注释掉 - 不再需要
        print(f"[调试] 自动同步功能已禁用，跳过任务 {task_id} 的自动同步")
        return
        
        # 以下代码已注释掉 - 自动同步功能不再需要
        """
        try:
            print(f"[调试] 开始检查任务 {task_id} 的自动同步...")
            
            # 检查飞书配置是否启用
            if not FEISHU_CONFIG.get('enabled'):
                print(f"[调试] 飞书配置未启用，跳过同步")
                return
            
            # 检查是否启用自动同步
            if not FEISHU_CONFIG.get('auto_sync', False):
                print(f"[调试] 自动同步未启用，跳过同步 (当前值: {FEISHU_CONFIG.get('auto_sync', False)})")
                return
            
            # 检查飞书配置完整性
            required_fields = ['app_id', 'app_secret', 'spreadsheet_token', 'table_id']
            missing_fields = [field for field in required_fields if not FEISHU_CONFIG.get(field)]
            if missing_fields:
                print(f"飞书自动同步跳过：配置不完整，缺少字段: {', '.join(missing_fields)}")
                return
            
            print(f"开始自动同步任务 {task_id} 的数据到飞书...")
            
            # 获取未同步的任务数据
            tweets = TweetData.query.filter_by(task_id=task_id, synced_to_feishu=False).all()
            if not tweets:
                print("没有新数据需要同步")
                return
            
            # 检查是否启用异步同步
            if FEISHU_CONFIG.get('async_enabled', True):
                print(f"[异步同步] 使用异步方式同步 {len(tweets)} 条数据")
                self._submit_async_sync_task(task_id, tweets)
            else:
                print(f"[同步同步] 使用同步方式同步 {len(tweets)} 条数据")
                self._sync_feishu_synchronously(task_id, tweets)
                
        except Exception as e:
            print(f"自动同步到飞书时发生错误: {e}")
        """
    
    def _submit_async_sync_task(self, task_id: int, tweets: List):
        """提交异步同步任务"""
        try:
            # 准备同步数据
            sync_data = []
            for tweet in tweets:
                # 解析hashtags
                try:
                    hashtags = json.loads(tweet.hashtags) if tweet.hashtags else []
                except:
                    hashtags = []
                
                # 处理发布时间
                publish_time = ''
                if tweet.publish_time:
                    try:
                        if isinstance(tweet.publish_time, str):
                            from dateutil import parser
                            dt = parser.parse(tweet.publish_time)
                            publish_time = int(dt.timestamp())
                        else:
                            publish_time = int(tweet.publish_time.timestamp())
                        
                        # 验证时间戳合理性
                        if publish_time < 946684800:  # 2000年1月1日
                            publish_time = int(datetime.now().timestamp())
                    except Exception as e:
                        print(f"发布时间解析失败: {e}")
                        publish_time = int(datetime.now().timestamp())
                else:
                    publish_time = int(datetime.now().timestamp())
                
                # 处理创建时间
                if tweet.scraped_at:
                    create_time = int(tweet.scraped_at.timestamp())
                else:
                    create_time = int(datetime.now().timestamp())
                
                # 验证创建时间戳合理性
                if create_time < 946684800:
                    create_time = int(datetime.now().timestamp())
                
                sync_data.append({
                    '推文原文内容': tweet.content or '',
                    '发布时间': publish_time,
                    '作者（账号）': tweet.username or '',
                    '推文链接': tweet.link or '',
                    '话题标签（Hashtag）': ', '.join(hashtags),
                    '类型标签': tweet.content_type or '',
                    '评论': tweet.comments or 0,
                    '点赞': tweet.likes or 0,
                    '转发': tweet.retweets or 0,
                    '创建时间': create_time
                })
            
            # 获取异步同步管理器
            async_manager = get_async_sync_manager()
            
            # 提交异步任务
            task_name = f"task_{task_id}"
            success = async_manager.submit_sync_task(
                task_id=task_name,
                data=sync_data,
                spreadsheet_token=FEISHU_CONFIG['spreadsheet_token'],
                table_id=FEISHU_CONFIG['table_id'],
                priority=FEISHU_CONFIG.get('async_priority', 1),
                max_retries=FEISHU_CONFIG.get('async_max_retries', 3)
            )
            
            if success:
                print(f"✅ [异步同步] 任务 {task_id} 已提交到异步队列，数据量: {len(sync_data)} 条")
            else:
                print(f"❌ [异步同步] 任务 {task_id} 提交失败，回退到同步方式")
                self._sync_feishu_synchronously(task_id, tweets)
                
        except Exception as e:
            print(f"❌ [异步同步] 提交异步任务失败: {e}，回退到同步方式")
            self._sync_feishu_synchronously(task_id, tweets)
    
    def _sync_feishu_synchronously(self, task_id: int, tweets: List):
        """同步方式执行飞书同步（保留原有逻辑作为备用）"""
        try:
            # 准备同步数据
            sync_data = []
            for tweet in tweets:
                # 解析hashtags
                try:
                    hashtags = json.loads(tweet.hashtags) if tweet.hashtags else []
                except:
                    hashtags = []
                
                sync_data.append({
                    '推文原文内容': tweet.content or '',
                    '作者（账号）': tweet.username or '',
                    '推文链接': tweet.link or '',
                    '话题标签（Hashtag）': ', '.join(hashtags),
                    '类型标签': tweet.content_type or '',
                    '评论': tweet.comments or 0,
                    '点赞': tweet.likes or 0,
                    '转发': tweet.retweets or 0
                })
            
            # 创建云同步管理器并同步
            from cloud_sync import CloudSyncManager
            sync_config = {
                'feishu': {
                    'enabled': True,
                    'app_id': FEISHU_CONFIG['app_id'],
                    'app_secret': FEISHU_CONFIG['app_secret'],
                    'spreadsheet_token': FEISHU_CONFIG['spreadsheet_token'],
                    'table_id': FEISHU_CONFIG['table_id'],
                    'base_url': 'https://open.feishu.cn/open-apis'
                }
            }
            sync_manager = CloudSyncManager(sync_config)
            
            # 执行同步
            success = sync_manager.sync_to_feishu(
                sync_data,
                FEISHU_CONFIG['spreadsheet_token'],
                FEISHU_CONFIG['table_id']
            )
            
            if success:
                # 更新同步状态
                for tweet in tweets:
                    tweet.synced_to_feishu = True
                db.session.commit()
                print(f"✅ [同步同步] 任务 {task_id} 同步成功，已更新 {len(tweets)} 条记录的同步状态")
            else:
                print(f"❌ [同步同步] 任务 {task_id} 同步失败")
                
        except Exception as e:
            print(f"❌ [同步同步] 同步执行失败: {e}")
    
    def stop_task(self):
        """停止当前任务"""
        self.is_running = False

# 全局并行任务管理器（将在配置加载后初始化）
task_manager = None
optimized_scraper = None

# 全局定时任务调度器
task_scheduler = None

# P0+优化：全局系统监控和资源管理组件
system_monitor = None
resource_scheduler = None
async_task_manager = None

def init_task_manager():
    """初始化任务管理器"""
    global task_manager, optimized_scraper
    
    # 检查是否已经初始化，避免重复初始化
    if task_manager is not None:
        print("⚠️ TaskManager已经初始化，跳过重复初始化")
        return
    
    max_concurrent = ADS_POWER_CONFIG.get('max_concurrent_tasks', 2)
    
    # 获取用户ID列表，优先使用user_ids，然后是multi_user_ids，最后是单个user_id
    user_ids = ADS_POWER_CONFIG.get('user_ids')
    if not user_ids:
        user_ids = ADS_POWER_CONFIG.get('multi_user_ids')
    if not user_ids:
        user_ids = [ADS_POWER_CONFIG.get('user_id', 'default')]
    
    print(f"[TaskManager] 配置信息:")
    print(f"  - 最大并发任务数: {max_concurrent}")
    print(f"  - 用户ID列表: {user_ids}")
    print(f"  - 用户ID数量: {len(user_ids)}")
    
    # 确保用户ID数量足够支持并发任务
    if len(user_ids) < max_concurrent:
        print(f"⚠️ 警告: 用户ID数量({len(user_ids)})少于最大并发任务数({max_concurrent})")
        print(f"⚠️ 建议配置至少 {max_concurrent} 个用户ID以支持完全并行")
    
    task_manager = RefactoredTaskManager(max_concurrent_tasks=max_concurrent, user_ids=user_ids)
    
    print(f"[RefactoredTaskManager] 初始化完成，最大并发: {max_concurrent}")
    
    # 初始化优化抓取器
    # optimized_scraper = MultiWindowEnhancedScraper(max_workers=max_concurrent)
    
    print(f"✅ TaskManager已初始化，最大并发任务数: {max_concurrent}")
    print(f"✅ 用户ID池大小: {len(user_ids)}")
    print(f"✅ OptimizedScraper已初始化，支持多窗口并发抓取")

def init_task_scheduler():
    """初始化定时任务调度器"""
    global task_scheduler
    
    if task_scheduler is not None:
        print("⚠️ TaskScheduler已经初始化，跳过重复初始化")
        return
    
    try:
        task_scheduler = TaskScheduler()
        
        # 添加预定义的定时任务
        # 每日Twitter采集任务（每天早上9点执行）
        task_scheduler.add_task(
            task_id="daily_twitter_scraping",
            name="每日Twitter采集",
            schedule_time="09:00",
            task_function=PredefinedTasks.daily_twitter_scraping,
            description="每日自动执行Twitter数据采集任务",
            max_retries=3,
            timeout_minutes=120
        )
        
        # 系统健康检查任务（每2小时执行一次）
        task_scheduler.add_task(
            task_id="system_health_check",
            name="系统健康检查",
            schedule_time="every 2 hours",
            task_function=PredefinedTasks.system_health_check,
            description="定期检查系统运行状态",
            max_retries=1,
            timeout_minutes=10
        )
        
        # 数据备份任务（每天凌晨2点执行）
        task_scheduler.add_task(
            task_id="data_backup",
            name="数据备份",
            schedule_time="02:00",
            task_function=PredefinedTasks.data_backup,
            description="每日自动备份数据库",
            max_retries=2,
            timeout_minutes=30
        )
        
        # 启动调度器
        task_scheduler.start_scheduler()
        
        print("✅ TaskScheduler已初始化并启动")
        
    except Exception as e:
        print(f"⚠️ TaskScheduler初始化失败: {e}")

def init_system_monitor():
    """P0+优化：初始化系统监控器"""
    global system_monitor
    
    if system_monitor is not None:
        print("⚠️ SystemMonitor已经初始化，跳过重复初始化")
        return
    
    try:
        system_monitor = SystemMonitor()
        system_monitor.start_monitoring()
        print("✅ SystemMonitor已初始化并启动")
    except Exception as e:
        print(f"⚠️ SystemMonitor初始化失败: {e}")

def init_resource_scheduler():
    """P0+优化：初始化资源调度器"""
    global resource_scheduler
    
    if resource_scheduler is not None:
        print("⚠️ ResourceScheduler已经初始化，跳过重复初始化")
        return
    
    try:
        resource_scheduler = ResourceScheduler()
        print("✅ ResourceScheduler已初始化")
    except Exception as e:
        print(f"⚠️ ResourceScheduler初始化失败: {e}")

def init_async_task_manager():
    """P0+优化：初始化异步任务管理器"""
    global async_task_manager
    
    if async_task_manager is not None:
        print("⚠️ AsyncTaskManager已经初始化，跳过重复初始化")
        return
    
    try:
        async_task_manager = AsyncTaskManager()
        print("✅ AsyncTaskManager已初始化")
    except Exception as e:
        print(f"⚠️ AsyncTaskManager初始化失败: {e}")

# 在模块加载时初始化
try:
    init_database()
    init_task_scheduler()
    # 确保任务管理器也被初始化
    if task_manager is None:
        init_task_manager()
    
    # P0+优化：初始化系统监控和资源管理组件
    init_system_monitor()
    init_resource_scheduler()
    init_async_task_manager()
except Exception as e:
    print(f"⚠️ 初始化失败: {e}")

# 路由定义
@app.route('/')
def index():
    """首页"""
    from datetime import datetime, date
    import sys
    import psutil
    from sqlalchemy import func
    
    # 优化统计数据查询 - 使用单个查询获取多个统计信息
    today = date.today()
    
    # 使用子查询优化统计数据获取
    task_stats = db.session.query(
        func.count().label('total'),
        func.sum(db.case((ScrapingTask.status == 'running', 1), else_=0)).label('running'),
        func.sum(db.case((ScrapingTask.status == 'completed', 1), else_=0)).label('completed')
    ).first()
    
    # 获取推文统计（限制查询范围以提升性能）
    tweet_stats = db.session.query(
        func.count().label('total'),
        func.sum(db.case((func.date(TweetData.scraped_at) == today, 1), else_=0)).label('today')
    ).first()
    
    stats = {
        'total_tasks': task_stats.total or 0,
        'total_tweets': tweet_stats.total or 0,
        'running_tasks': task_stats.running or 0,
        'completed_tasks': task_stats.completed or 0,
        'today_tweets': tweet_stats.today or 0
    }
    
    # 获取最近的任务（只获取必要字段）
    recent_tasks = ScrapingTask.query.with_entities(
        ScrapingTask.id, ScrapingTask.name, ScrapingTask.status, 
        ScrapingTask.created_at, ScrapingTask.result_count
    ).order_by(ScrapingTask.created_at.desc()).limit(5).all()
    
    # 获取系统信息（简化版本，减少性能开销）
    try:
        # 计算运行时间
        import time
        start_time = getattr(app, 'start_time', time.time())
        uptime_seconds = int(time.time() - start_time)
        uptime_hours = uptime_seconds // 3600
        uptime_minutes = (uptime_seconds % 3600) // 60
        uptime = f"{uptime_hours}小时{uptime_minutes}分钟"
        
        # 简化内存信息获取
        try:
            memory = psutil.virtual_memory()
            memory_usage = f"{memory.percent:.1f}%"
        except:
            memory_usage = "未知"
        
        # 获取Python版本
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        # 简化数据库大小获取（缓存结果）
        db_size = "计算中..."
        
        system_info = {
            'uptime': uptime,
            'memory_usage': memory_usage,
            'python_version': python_version,
            'db_size': db_size
        }
    except Exception as e:
        app.logger.error(f"获取系统信息失败: {e}")
        system_info = {
            'uptime': '未知',
            'memory_usage': '未知',
            'python_version': '未知',
            'db_size': '未知'
        }
    
    return render_template('index_optimized.html', stats=stats, recent_tasks=recent_tasks, system_info=system_info)

@app.route('/tasks')
def tasks():
    """任务管理页面"""
    tasks = ScrapingTask.query.order_by(ScrapingTask.created_at.desc()).all()
    
    # 计算任务统计数据
    task_stats = {
        'total': len(tasks),
        'pending': len([t for t in tasks if t.status == 'pending']),
        'running': len([t for t in tasks if t.status == 'running']),
        'completed': len([t for t in tasks if t.status == 'completed']),
        'failed': len([t for t in tasks if t.status == 'failed']),
        'queued': len([t for t in tasks if t.status == 'queued'])
    }
    
    return render_template('tasks_optimized.html', tasks=tasks, stats=task_stats)

@app.route('/create_task', methods=['GET', 'POST'])
def create_task():
    """创建任务页面和处理表单提交"""
    if request.method == 'POST':
        try:
            app.logger.info("收到创建任务请求")
            
            # 处理表单数据
            task_name = request.form.get('task_name', '').strip()
            keywords = request.form.get('keywords', '').strip()
            target_accounts = request.form.get('target_accounts', '').strip()
            max_tweets = int(request.form.get('max_tweets', 100))
            min_likes = int(request.form.get('min_likes', 0))
            min_retweets = int(request.form.get('min_retweets', 0))
            min_comments = int(request.form.get('min_comments', 0))
            
            app.logger.info(f"任务参数: name={task_name}, keywords={keywords}, accounts={target_accounts}, max_tweets={max_tweets}, min_likes={min_likes}, min_retweets={min_retweets}, min_comments={min_comments}")
            
            if not task_name:
                app.logger.warning("任务名称为空")
                flash('任务名称不能为空', 'error')
                return redirect(url_for('index'))
            
            # 验证关键词和目标账号至少填写一个
            if not keywords and not target_accounts:
                app.logger.warning("关键词和目标账号都为空")
                flash('关键词和目标账号至少需要填写一个', 'error')
                return redirect(url_for('index'))
            
            # 解析关键词和账号
            keywords_list = [k.strip() for k in keywords.split(',') if k.strip()]
            accounts_list = [a.strip() for a in target_accounts.split(',') if a.strip()] if target_accounts else []
            
            app.logger.info(f"解析后的参数: keywords_list={keywords_list}, accounts_list={accounts_list}")
            
            # 创建任务
            task = ScrapingTask(
                name=task_name,
                target_accounts=json.dumps(accounts_list),
                target_keywords=json.dumps(keywords_list),
                max_tweets=max_tweets,
                min_likes=min_likes,
                min_retweets=min_retweets,
                min_comments=min_comments
            )
            
            app.logger.info("正在保存任务到数据库")
            db.session.add(task)
            db.session.commit()
            app.logger.info(f"任务已保存，ID: {task.id}")
            
            # 自动启动任务
            app.logger.info("检查是否可以启动任务")
            if task_manager.can_start_task():
                app.logger.info(f"尝试启动任务 {task.id}")
                success, message = task_manager.start_task(task.id)
                if success:
                    app.logger.info(f"任务 {task.id} 启动成功")
                    flash(f'任务 "{task_name}" 创建成功并已开始执行！', 'success')
                else:
                    app.logger.warning(f"任务 {task.id} 启动失败: {message}")
                    flash(f'任务 "{task_name}" 创建成功，但启动失败: {message}', 'warning')
            else:
                status = task_manager.get_task_status()
                app.logger.info(f"无法启动任务，当前状态: {status}")
                flash(f'任务 "{task_name}" 创建成功！当前有 {status["running_count"]} 个任务正在运行，请稍后手动启动。', 'info')
            
            app.logger.info("重定向到任务页面")
            return redirect(url_for('tasks'))
            
        except Exception as e:
            app.logger.error(f"创建任务失败: {str(e)}", exc_info=True)
            flash(f'创建任务失败: {str(e)}', 'error')
            return redirect(url_for('index'))
    
    return render_template('create_task.html')

@app.route('/data')
def data():
    """数据查看页面"""
    from datetime import datetime, date
    from sqlalchemy import func
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search = request.args.get('search', '')
    task_id = request.args.get('task_id', type=int)
    min_likes = request.args.get('min_likes', type=int)
    min_retweets = request.args.get('min_retweets', type=int)
    sort = request.args.get('sort', 'created_desc')
    
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
    
    # 点赞数过滤
    if min_likes is not None:
        query = query.filter(TweetData.likes >= min_likes)
    
    # 转发数过滤
    if min_retweets is not None:
        query = query.filter(TweetData.retweets >= min_retweets)
    
    # 排序
    if sort == 'created_asc':
        query = query.order_by(TweetData.scraped_at.asc())
    elif sort == 'likes_desc':
        query = query.order_by(TweetData.likes.desc())
    elif sort == 'retweets_desc':
        query = query.filter(TweetData.retweets.isnot(None)).order_by(TweetData.retweets.desc())
    else:  # created_desc
        query = query.order_by(TweetData.scraped_at.desc())
    
    # 分页
    tweets = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
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
    
    # 获取所有任务用于筛选
    tasks = ScrapingTask.query.order_by(ScrapingTask.created_at.desc()).all()
    
    return render_template('data_optimized.html', 
                         tweets=tweets.items, 
                         pagination=tweets, 
                         data_stats=data_stats, 
                         tasks=tasks)

@app.route('/about')
def about():
    """关于我页面"""
    return render_template('about.html')

@app.route('/test-simple')
def test_simple():
    """简单测试页面"""
    return render_template('test_simple.html')

@app.route('/minimal')
def minimal():
    """最小化测试页面"""
    return render_template('index_minimal.html')

@app.route('/local')
def local_index():
    """本地化首页 - 无外部依赖"""
    return render_template('index_local.html')

@app.route('/config')
def config():
    """配置页面"""
    # 获取当前配置
    config_data = {}
    
    # 从数据库获取配置
    configs = SystemConfig.query.all()
    for cfg in configs:
        config_data[cfg.key] = cfg.value
    
    # AdsPower配置现在完全由配置文件管理，无需前端输入
    
    # 处理导出字段配置
    if 'export_fields' in config_data:
        config_data['export_fields'] = config_data['export_fields'].split(',') if config_data['export_fields'] else []
    else:
        config_data['export_fields'] = ['content', 'username', 'created_at', 'likes_count', 'retweets_count', 'hashtags']
    
    return render_template('config_optimized.html', config=config_data)

@app.route('/update_config', methods=['POST'])
def update_config():
    """更新配置"""
    try:
        config_type = request.form.get('config_type')
        
        if config_type == 'adspower':
            # AdsPower配置现在完全由配置文件管理，不再接受前端表单输入
            flash('AdsPower配置已移至配置文件管理，如需修改请联系系统管理员', 'info')
            return redirect(url_for('config'))
            
        elif config_type == 'general':
            # 处理基础设置
            general_configs = {
                'system_name': request.form.get('system_name', 'Twitter抓取管理系统'),
                'admin_email': request.form.get('admin_email', ''),
                'data_retention_days': request.form.get('data_retention_days', '30'),
                'auto_backup': 'auto_backup' in request.form
            }
            
            for key, value in general_configs.items():
                config = SystemConfig.query.filter_by(key=key).first()
                if config:
                    config.value = str(value)
                    config.updated_at = datetime.utcnow()
                else:
                    config = SystemConfig(
                        key=key,
                        value=str(value),
                        description=f'基础设置: {key}'
                    )
                    db.session.add(config)
            
            db.session.commit()
            flash('基础设置已更新', 'success')
            
        elif config_type == 'scraping':
            # 处理抓取配置
            scraping_configs = {
                'default_max_tweets': request.form.get('default_max_tweets', '100'),
                'request_delay': request.form.get('request_delay', '2'),
                'browser_timeout': request.form.get('browser_timeout', '30'),
                'retry_attempts': request.form.get('retry_attempts', '3'),
                'user_agents': request.form.get('user_agents', ''),
                'enable_proxy': 'enable_proxy' in request.form
            }
            
            for key, value in scraping_configs.items():
                config = SystemConfig.query.filter_by(key=key).first()
                if config:
                    config.value = str(value)
                    config.updated_at = datetime.utcnow()
                else:
                    config = SystemConfig(
                        key=key,
                        value=str(value),
                        description=f'抓取配置: {key}'
                    )
                    db.session.add(config)
            
            db.session.commit()
            flash('抓取配置已更新', 'success')
            
        elif config_type == 'feishu':
            # 处理飞书配置
            feishu_configs = {
                'feishu_app_id': request.form.get('feishu_app_id', ''),
                'feishu_app_secret': request.form.get('feishu_app_secret', ''),
                'feishu_spreadsheet_token': request.form.get('feishu_spreadsheet_token', ''),
                'feishu_table_id': request.form.get('feishu_table_id', ''),
                'feishu_enabled': 'feishu_enabled' in request.form,
                # 自动同步功能已注释掉 - 不再需要
                # 'feishu_auto_sync': 'feishu_auto_sync' in request.form,
                # 'sync_interval': request.form.get('sync_interval', '24'),
                # 异步同步配置
                'async_enabled': 'async_enabled' in request.form,
                'async_priority': int(request.form.get('async_priority', '2')),
                'async_max_workers': int(request.form.get('async_max_workers', '2')),
                'async_max_queue_size': int(request.form.get('async_max_queue_size', '100')),
                'async_max_retries': int(request.form.get('async_max_retries', '3'))
            }
            
            for key, value in feishu_configs.items():
                config = SystemConfig.query.filter_by(key=key).first()
                if config:
                    config.value = str(value)
                    config.updated_at = datetime.utcnow()
                else:
                    config = SystemConfig(
                        key=key,
                        value=str(value),
                        description=f'飞书配置: {key}'
                    )
                    db.session.add(config)
            
            # 更新全局飞书配置
            global FEISHU_CONFIG
            FEISHU_CONFIG.update({
                'app_id': feishu_configs['feishu_app_id'],
                'app_secret': feishu_configs['feishu_app_secret'],
                'spreadsheet_token': feishu_configs['feishu_spreadsheet_token'],
                'table_id': feishu_configs['feishu_table_id'],
                'enabled': feishu_configs['feishu_enabled'],
                # 自动同步功能已注释掉
                # 'auto_sync': feishu_configs['feishu_auto_sync'],
                # 异步同步配置
                'async_enabled': feishu_configs['async_enabled'],
                'async_priority': feishu_configs['async_priority'],
                'async_max_workers': feishu_configs['async_max_workers'],
                'async_max_queue_size': feishu_configs['async_max_queue_size'],
                'async_max_retries': feishu_configs['async_max_retries']
            })
            
            db.session.commit()
            flash('飞书配置已更新', 'success')
            
        elif config_type == 'export':
            # 处理导出设置
            export_configs = {
                'export_excel': 'export_excel' in request.form,
                'export_csv': 'export_csv' in request.form,
                'export_json': 'export_json' in request.form,
                'export_fields': ','.join(request.form.getlist('export_fields')),
                'export_filename_template': request.form.get('export_filename_template', 'twitter_data_{date}')
            }
            
            for key, value in export_configs.items():
                config = SystemConfig.query.filter_by(key=key).first()
                if config:
                    config.value = str(value)
                    config.updated_at = datetime.utcnow()
                else:
                    config = SystemConfig(
                        key=key,
                        value=str(value),
                        description=f'导出设置: {key}'
                    )
                    db.session.add(config)
            
            db.session.commit()
            flash('导出设置已更新', 'success')
        
        return redirect(url_for('config'))
        
    except Exception as e:
        flash(f'配置更新失败: {str(e)}', 'error')
        return redirect(url_for('config'))

@app.route('/influencers')
def influencers():
    """博主管理页面"""
    return render_template('influencers_optimized.html')

@app.route('/sync_feishu', methods=['POST'])
def sync_feishu():
    """同步数据到飞书（异步版本）"""
    print("\n" + "="*60)
    print("🚀 [后端] 开始处理飞书异步同步请求")
    try:
        # 获取请求参数
        data = request.form.to_dict()
        task_id = data.get('task_id')
        force_sync = data.get('force_sync', 'false').lower() == 'true'
        print(f"📋 [后端] 接收到请求参数: {data}")
        print(f"📋 [后端] 任务ID: {task_id}")
        print(f"📋 [后端] 强制同步: {force_sync}")
        
        # 检查飞书配置
        print(f"🔧 [后端] 检查飞书配置状态")
        print(f"   - 飞书启用状态: {FEISHU_CONFIG.get('enabled')}")
        if not FEISHU_CONFIG.get('enabled'):
            print("❌ [后端] 飞书同步未启用")
            return jsonify({'success': False, 'message': '飞书同步未启用'}), 400
        
        required_fields = ['app_id', 'app_secret', 'spreadsheet_token', 'table_id']
        missing_fields = [field for field in required_fields if not FEISHU_CONFIG.get(field)]
        print(f"🔧 [后端] 检查必需配置字段: {required_fields}")
        print(f"🔧 [后端] 缺少的配置字段: {missing_fields}")
        if missing_fields:
            print(f"❌ [后端] 飞书配置不完整，缺少字段: {missing_fields}")
            return jsonify({'success': False, 'message': f'飞书配置不完整，缺少字段: {", ".join(missing_fields)}'}), 400
        
        print(f"✅ [后端] 飞书配置检查通过")
        
        # 构建查询
        print(f"🔍 [后端] 构建数据库查询")
        query = TweetData.query
        if task_id:
            query = query.filter(TweetData.task_id == task_id)
            print(f"   - 按任务ID过滤: {task_id}")
        else:
            print(f"   - 查询所有任务的数据")
        
        # 根据是否强制同步决定查询条件
        if force_sync:
            all_tweets = query.all()
            unsynced_tweets = all_tweets  # 强制同步时，所有数据都视为未同步
            synced_tweets = []
            print(f"🔄 [后端] 强制同步模式：将重新同步所有数据")
        else:
            all_tweets = query.all()
            synced_tweets = [t for t in all_tweets if t.synced_to_feishu]
            unsynced_tweets = [t for t in all_tweets if not t.synced_to_feishu]
            print(f"📊 [后端] 增量同步模式：只同步未同步的数据")
        
        print(f"📊 [后端] 查询到总推文数: {len(all_tweets)}")
        print(f"📊 [后端] 数据统计:")
        print(f"   - 已同步推文数: {len(synced_tweets)}")
        print(f"   - 待同步推文数: {len(unsynced_tweets)}")
        
        # 构建详细的同步报告
        sync_report = {
            'total_tweets': len(all_tweets),
            'already_synced': len(synced_tweets),
            'to_sync': len(unsynced_tweets),
            'force_sync': force_sync
        }
        print(f"📊 [后端] 同步报告: {sync_report}")
        
        if not unsynced_tweets:
            message = f'内容已经同步过了，不用再同步了！'
            if task_id:
                message += f'任务 {task_id} 的所有数据（{len(all_tweets)} 条）都已在飞书中'
            else:
                message += f'所有数据（{len(all_tweets)} 条）都已在飞书中'
            print(f"ℹ️ [后端] 无新数据需要同步: {message}")
            return jsonify({
                'success': True, 
                'message': message,
                'report': sync_report
            })
        
        # 检查是否启用异步同步
        async_enabled = FEISHU_CONFIG.get('async_enabled', True)
        print(f"🔧 [后端] 异步同步状态: {async_enabled}")
        
        if async_enabled:
            print(f"🚀 [异步同步] 使用异步方式同步 {len(unsynced_tweets)} 条数据")
            return _handle_async_sync(task_id, unsynced_tweets, sync_report, force_sync)
        else:
            print(f"🔄 [同步同步] 使用同步方式同步 {len(unsynced_tweets)} 条数据")
            return _handle_sync_sync(task_id, unsynced_tweets, synced_tweets, sync_report)
            
    except Exception as e:
        print(f"❌ [后端] 飞书同步过程中发生异常")
        print(f"   - 异常类型: {type(e).__name__}")
        print(f"   - 异常消息: {str(e)}")
        db.session.rollback()
        print(f"🔄 [后端] 数据库回滚完成")
        import traceback
        error_details = traceback.format_exc()
        print(f"📊 [后端] 异常详情: {error_details}")
        print(f"❌ [后端] 返回错误响应: 同步失败: {str(e)}")
        print("="*60 + "\n")
        return jsonify({'success': False, 'message': f'同步失败: {str(e)}'}), 500

def _handle_async_sync(task_id, unsynced_tweets, sync_report, force_sync=False):
    """处理异步同步"""
    try:
        # 准备同步数据
        sync_data = _prepare_sync_data(unsynced_tweets)
        
        # 获取异步任务管理器
        from utils.async_task_manager import get_task_manager, TaskType, TaskPriority
        task_manager = get_task_manager()
        
        # 生成任务名称
        if task_id:
            async_task_name = f"manual_task_{task_id}_{int(datetime.now().timestamp())}"
        else:
            async_task_name = f"manual_all_{int(datetime.now().timestamp())}"
        
        # 根据数据量动态设置优先级
        data_count = len(unsynced_tweets)
        if data_count > 1000:
            priority = TaskPriority.LOW
        elif data_count > 100:
            priority = TaskPriority.NORMAL
        else:
            priority = TaskPriority.HIGH
        
        # 提交异步任务
        success = task_manager.submit_feishu_sync(
            data={
                'sync_data': sync_data,
                'spreadsheet_token': FEISHU_CONFIG['spreadsheet_token'],
                'table_id': FEISHU_CONFIG['table_id'],
                'tweet_ids': [tweet.id for tweet in unsynced_tweets],
                'force_sync': force_sync
            },
            priority=priority,
            max_retries=FEISHU_CONFIG.get('async_max_retries', 3)
        )
        
        if success:
            message = f'✅ 已提交 {len(unsynced_tweets)} 条数据到异步同步队列'
            if task_id:
                message += f'（任务 {task_id}）'
            if force_sync:
                message += '（强制重新同步）'
            message += f'\n🔄 任务ID: {async_task_name}\n⏱️ 请稍后查看同步状态'
            
            sync_report['async_task_id'] = async_task_name
            sync_report['submitted_count'] = len(unsynced_tweets)
            
            print(f"✅ [异步同步] 任务提交成功: {async_task_name}")
            
            return jsonify({
                'success': True,
                'message': message,
                'report': sync_report,
                'async_task_id': async_task_name,
                'is_async': True
            })
        else:
            print(f"❌ [异步同步] 任务提交失败，回退到同步方式")
            return _handle_sync_sync(task_id, unsynced_tweets, [], sync_report)
            
    except Exception as e:
        print(f"❌ [异步同步] 异步处理失败: {e}，回退到同步方式")
        return _handle_sync_sync(task_id, unsynced_tweets, [], sync_report)

def _handle_sync_sync(task_id, unsynced_tweets, synced_tweets, sync_report):
    """处理同步方式的飞书同步（保留原有逻辑作为备用）"""
    try:
        # 准备同步数据
        sync_data = _prepare_sync_data(unsynced_tweets)
        
        # 初始化同步管理器
        print(f"🔧 [同步同步] 初始化云同步管理器")
        sync_config = {
            'feishu': {
                'enabled': True,
                'app_id': FEISHU_CONFIG['app_id'],
                'app_secret': FEISHU_CONFIG['app_secret'],
                'spreadsheet_token': FEISHU_CONFIG['spreadsheet_token'],
                'table_id': FEISHU_CONFIG['table_id'],
                'base_url': 'https://open.feishu.cn/open-apis'
            }
        }
        sync_manager = CloudSyncManager(sync_config)
        
        # 执行同步
        print(f"🚀 [同步同步] 开始执行飞书同步")
        success = sync_manager.sync_to_feishu(
            sync_data,
            FEISHU_CONFIG['spreadsheet_token'],
            FEISHU_CONFIG['table_id']
        )
        
        if success:
            # 更新同步状态
            for tweet in unsynced_tweets:
                tweet.synced_to_feishu = True
            db.session.commit()
            
            # 构建成功消息
            message = f'✅ 成功同步 {len(unsynced_tweets)} 条新数据到飞书'
            if task_id:
                message += f'（任务 {task_id}）'
            
            if synced_tweets:
                message += f'，另有 {len(synced_tweets)} 条数据之前已同步'
            
            sync_report['synced_count'] = len(unsynced_tweets)
            print(f"✅ [同步同步] 同步完成: {message}")
            
            return jsonify({
                'success': True,
                'message': message,
                'report': sync_report,
                'is_async': False
            })
        else:
            print(f"❌ [同步同步] 同步失败")
            return jsonify({'success': False, 'message': '同步到飞书失败，请检查网络连接和飞书配置'}), 500
            
    except Exception as e:
        print(f"❌ [同步同步] 同步执行失败: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': f'同步失败: {str(e)}'}), 500

def _prepare_sync_data(tweets):
    """准备同步数据"""
    sync_data = []
    for idx, tweet in enumerate(tweets):
        print(f"📝 [数据准备] 处理第 {idx + 1}/{len(tweets)} 条推文")
        
        # 使用用户设置的类型标签，如果为空则使用自动分类
        content_type = tweet.content_type or classify_content_type(tweet.content)
        
        # 处理发布时间
        publish_time = ''
        if tweet.publish_time:
            try:
                if isinstance(tweet.publish_time, str):
                    from dateutil import parser
                    dt = parser.parse(tweet.publish_time)
                    publish_time = int(dt.timestamp())
                else:
                    publish_time = int(tweet.publish_time.timestamp())
                
                # 验证时间戳合理性
                if publish_time < 946684800:  # 2000年1月1日
                    publish_time = int(datetime.now().timestamp())
            except Exception as e:
                print(f"发布时间解析失败: {e}")
                publish_time = int(datetime.now().timestamp())
        else:
            publish_time = int(datetime.now().timestamp())
        
        # 处理创建时间
        if tweet.scraped_at:
            create_time = int(tweet.scraped_at.timestamp())
        else:
            create_time = int(datetime.now().timestamp())
        
        # 验证创建时间戳合理性
        if create_time < 946684800:
            create_time = int(datetime.now().timestamp())
        
        # 解析hashtags
        try:
            hashtags = json.loads(tweet.hashtags) if tweet.hashtags else []
        except:
            hashtags = []
        
        tweet_data = {
            '推文原文内容': tweet.content or '',
            '发布时间': publish_time,
            '作者（账号）': tweet.username or '',
            '推文链接': tweet.link or '',
            '话题标签（Hashtag）': ', '.join(hashtags),
            '类型标签': content_type,
            '评论': tweet.comments or 0,
            '点赞': tweet.likes or 0,
            '转发': tweet.retweets or 0,
            '创建时间': create_time
        }
        sync_data.append(tweet_data)
    
    print(f"✅ [数据准备] 数据准备完成，共 {len(sync_data)} 条记录")
    return sync_data

# API路由
@app.route('/api/tasks', methods=['GET'])
def api_get_tasks():
    """获取任务列表"""
    tasks = ScrapingTask.query.order_by(ScrapingTask.created_at.desc()).all()
    return jsonify([task.to_dict() for task in tasks])

@app.route('/api/tasks/status', methods=['GET'])
def api_get_async_tasks_status():
    """获取异步任务状态列表"""
    try:
        # 获取查询参数
        status_filter = request.args.get('status')
        task_type_filter = request.args.get('task_type')
        limit = request.args.get('limit', 100, type=int)
        
        # 获取异步任务管理器
        from utils.async_task_manager import get_task_manager
        async_task_manager = get_task_manager()
        if async_task_manager is None:
            return jsonify({
                'success': False,
                'error': '异步任务管理器未初始化'
            }), 500
        
        # 转换过滤参数
        from utils.async_task_manager import TaskStatus, TaskType
        
        status_enum = None
        if status_filter:
            try:
                status_enum = TaskStatus(status_filter)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': f'无效的状态值: {status_filter}'
                }), 400
        
        task_type_enum = None
        if task_type_filter:
            try:
                task_type_enum = TaskType(task_type_filter)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': f'无效的任务类型: {task_type_filter}'
                }), 400
        
        # 获取任务列表
        tasks = async_task_manager.get_task_list(
            status=status_enum,
            task_type=task_type_enum,
            limit=limit
        )
        
        # 计算耗时
        for task in tasks:
            if task.get('started_at') and task.get('completed_at'):
                from datetime import datetime
                start_time = datetime.fromisoformat(task['started_at'])
                end_time = datetime.fromisoformat(task['completed_at'])
                duration = (end_time - start_time).total_seconds()
                task['duration'] = f"{duration:.2f}s"
            elif task.get('started_at') and task['status'] == 'running':
                from datetime import datetime
                start_time = datetime.fromisoformat(task['started_at'])
                current_time = datetime.now()
                duration = (current_time - start_time).total_seconds()
                task['duration'] = f"{duration:.2f}s (运行中)"
            else:
                task['duration'] = '-'
        
        # 获取统计信息
        stats = async_task_manager.get_statistics()
        
        return jsonify({
            'success': True,
            'data': {
                'tasks': tasks,
                'total': len(tasks),
                'statistics': stats
            }
        })
        
    except Exception as e:
        app.logger.error(f"获取异步任务状态失败: {e}")
        return jsonify({
            'success': False,
            'error': f'获取任务状态失败: {str(e)}'
        }), 500

@app.route('/api/tasks/status/<task_id>', methods=['GET'])
def api_get_async_task_detail(task_id):
    """获取指定异步任务的详细信息"""
    try:
        # 获取异步任务管理器
        from utils.async_task_manager import get_task_manager
        async_task_manager = get_task_manager()
        if async_task_manager is None:
            return jsonify({
                'success': False,
                'error': '异步任务管理器未初始化'
            }), 500
        
        # 获取任务状态
        task_status = async_task_manager.get_task_status(task_id)
        
        if not task_status:
            return jsonify({
                'success': False,
                'error': '任务不存在'
            }), 404
        
        # 计算耗时
        if task_status.get('started_at') and task_status.get('completed_at'):
            from datetime import datetime
            start_time = datetime.fromisoformat(task_status['started_at'])
            end_time = datetime.fromisoformat(task_status['completed_at'])
            duration = (end_time - start_time).total_seconds()
            task_status['duration'] = f"{duration:.2f}s"
        elif task_status.get('started_at') and task_status['status'] == 'running':
            from datetime import datetime
            start_time = datetime.fromisoformat(task_status['started_at'])
            current_time = datetime.now()
            duration = (current_time - start_time).total_seconds()
            task_status['duration'] = f"{duration:.2f}s (运行中)"
        else:
            task_status['duration'] = '-'
        
        return jsonify({
            'success': True,
            'data': task_status
        })
        
    except Exception as e:
        app.logger.error(f"获取异步任务详情失败: {e}")
        return jsonify({
            'success': False,
            'error': f'获取任务详情失败: {str(e)}'
        }), 500

@app.route('/api/tasks', methods=['POST'])
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
                description=f"多博主并行任务，包含 {len(target_accounts)} 个博主: {', '.join(target_accounts)}"
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
                    description=f"子任务 {i}/{len(target_accounts)} - 博主: {account}"
                )
                
                db.session.add(sub_task)
                db.session.flush()  # 获取子任务ID
                sub_task_ids.append(sub_task.id)
            
            db.session.commit()
            
            app.logger.info(f"多博主任务创建成功: 主任务ID={main_task.id}, 子任务IDs={sub_task_ids}")
            
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
                min_comments=data.get('min_comments', 0)
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
        app.logger.error(f"创建任务失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/tasks/<int:task_id>/start', methods=['POST'])
def api_start_task(task_id):
    """启动任务"""
    app.logger.info(f"收到启动任务请求: task_id={task_id}")
    
    # 获取任务信息
    task = ScrapingTask.query.get(task_id)
    if not task:
        return jsonify({'success': False, 'error': '任务不存在'}), 404
    
    # 检查是否为多博主主任务
    is_multi_blogger_main = '(主任务)' in task.name and len(json.loads(task.target_accounts)) > 1
    
    if is_multi_blogger_main:
        app.logger.info(f"检测到多博主主任务: {task_id}，开始启动子任务")
        
        # 查找所有相关的子任务
        base_name = task.name.replace(' (主任务)', '')
        target_accounts = json.loads(task.target_accounts)
        
        sub_tasks = []
        for account in target_accounts:
            sub_task_name = f"{base_name} - {account}"
            sub_task = ScrapingTask.query.filter_by(name=sub_task_name).first()
            if sub_task:
                sub_tasks.append(sub_task)
        
        if not sub_tasks:
            return jsonify({'success': False, 'error': '未找到相关的子任务'}), 400
        
        # 启动所有子任务
        started_tasks = []
        failed_tasks = []
        queued_tasks = []
        
        for sub_task in sub_tasks:
            if task_manager.is_task_running(sub_task.id):
                app.logger.info(f"子任务 {sub_task.id} 已在运行中，跳过")
                continue
                
            try:
                if task_manager.can_start_task():
                    success, message = task_manager.start_task(sub_task.id)
                    if success:
                        started_tasks.append(sub_task.id)
                        app.logger.info(f"子任务 {sub_task.id} 启动成功")
                    else:
                        failed_tasks.append({'id': sub_task.id, 'error': message})
                        app.logger.error(f"子任务 {sub_task.id} 启动失败: {message}")
                else:
                    # 加入队列
                    success, message = task_manager.start_task(sub_task.id)  # 这会自动加入队列
                    if success:
                        queued_tasks.append(sub_task.id)
                        app.logger.info(f"子任务 {sub_task.id} 已加入队列")
                    else:
                        failed_tasks.append({'id': sub_task.id, 'error': message})
                        app.logger.error(f"子任务 {sub_task.id} 加入队列失败: {message}")
            except Exception as e:
                failed_tasks.append({'id': sub_task.id, 'error': str(e)})
                app.logger.error(f"子任务 {sub_task.id} 启动异常: {str(e)}")
        
        # 返回启动结果
        result = {
            'success': True,
            'task_type': 'multi_blogger',
            'started_tasks': started_tasks,
            'queued_tasks': queued_tasks,
            'failed_tasks': failed_tasks,
            'message': f'多博主任务启动完成: {len(started_tasks)} 个立即启动, {len(queued_tasks)} 个加入队列, {len(failed_tasks)} 个失败'
        }
        
        if failed_tasks and not started_tasks and not queued_tasks:
            result['success'] = False
            result['error'] = '所有子任务启动失败'
            return jsonify(result), 400
        
        return jsonify(result)
    
    # 检查任务是否已在运行
    if task_manager.is_task_running(task_id):
        error_msg = '该任务已在运行中'
        app.logger.warning(f"任务启动失败 - {error_msg}: task_id={task_id}")
        return jsonify({'success': False, 'error': error_msg}), 400
    
    # 检查是否可以启动新任务
    if not task_manager.can_start_task():
        status = task_manager.get_task_status()
        # 提供详细的失败原因
        error_details = {
            'running_count': status['running_count'],
            'max_concurrent': status['max_concurrent'],
            'available_slots': status['available_slots'],
            'available_browsers': status['available_browsers'],
            'current_tasks': status.get('current_tasks', []),
            'user_id_pool': len(task_manager.user_id_pool),
            'available_user_ids': task_manager.available_user_ids
        }
        
        # 当达到并发限制时，自动将任务加入队列
        if status['running_count'] >= status['max_concurrent']:
            app.logger.info(f"任务 {task_id} 将加入队列等待执行")
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
                app.logger.error(f"加入队列失败: {str(e)}")
                return jsonify({
                    'success': False, 
                    'error': f'加入队列失败: {str(e)}'
                }), 500
        elif len(task_manager.user_id_pool) == 0:
            error_msg = f'无可用的浏览器用户ID，可用用户ID池为空。配置的用户ID: {task_manager.available_user_ids}'
        else:
            error_msg = f'无法启动任务，原因未知。运行任务数: {status["running_count"]}/{status["max_concurrent"]}，可用浏览器: {len(task_manager.user_id_pool)}'
        
        app.logger.error(f"任务启动失败 - {error_msg}: task_id={task_id}, details={error_details}")
        
        return jsonify({
            'success': False, 
            'error': error_msg,
            'details': error_details
        }), 400
    
    try:
        app.logger.info(f"开始启动任务: task_id={task_id}")
        success, message = task_manager.start_task(task_id)
        if success:
            app.logger.info(f"任务启动成功: task_id={task_id}, message={message}")
            return jsonify({'success': True, 'message': message})
        else:
            # 获取更详细的状态信息
            status = task_manager.get_task_status()
            error_details = {
                'running_count': status['running_count'],
                'max_concurrent': status['max_concurrent'],
                'available_slots': status['available_slots'],
                'available_browsers': status['available_browsers'],
                'user_id_pool': len(task_manager.user_id_pool),
                'available_user_ids': task_manager.available_user_ids,
                'original_message': message
            }
            app.logger.error(f"任务启动失败: task_id={task_id}, message={message}, details={error_details}")
            return jsonify({
                'success': False, 
                'error': f'任务启动失败: {message}',
                'details': error_details
            }), 400
        
    except Exception as e:
        # 获取详细的异常信息
        import traceback
        error_details = {
            'exception_type': type(e).__name__,
            'exception_message': str(e),
            'traceback': traceback.format_exc()
        }
        app.logger.error(f"任务启动异常: task_id={task_id}, exception={str(e)}, traceback={traceback.format_exc()}")
        return jsonify({
            'success': False, 
            'error': f'任务启动异常: {str(e)}',
            'details': error_details
        }), 500

@app.route('/api/tasks/<int:task_id>/stop', methods=['POST'])
def api_stop_task(task_id):
    """停止任务"""
    try:
        success, message = task_manager.stop_task(task_id)
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/queue/status')
def api_queue_status():
    """获取任务队列状态"""
    try:
        queue_status = task_manager.get_queue_status()
        
        return jsonify({
            'success': True,
            'data': queue_status
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/queue/clear', methods=['POST'])
def api_clear_queue():
    """清空任务队列"""
    try:
        task_manager.clear_queue()
        return jsonify({
            'success': True,
            'message': '任务队列已清空'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/task-manager/status')
def api_task_manager_status():
    """获取任务管理器状态"""
    try:
        status = task_manager.get_status()
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>/restart', methods=['POST'])
def api_restart_task(task_id):
    """重新启动任务"""
    # 检查任务是否已在运行
    if task_manager.is_task_running(task_id):
        return jsonify({'success': False, 'error': '该任务已在运行中，请先停止'}), 400
    
    # 检查是否可以启动新任务
    if not task_manager.can_start_task():
        status = task_manager.get_task_status()
        # 提供详细的失败原因
        error_details = {
            'running_count': status['running_count'],
            'max_concurrent': status['max_concurrent'],
            'available_slots': status['available_slots'],
            'available_browsers': status['available_browsers'],
            'current_tasks': status.get('current_tasks', []),
            'user_id_pool': len(task_manager.user_id_pool),
            'available_user_ids': task_manager.available_user_ids
        }
        
        if status['running_count'] >= status['max_concurrent']:
            error_msg = f'已达到最大并发任务数限制({status["max_concurrent"]})，当前运行任务数: {status["running_count"]}'
        elif len(task_manager.user_id_pool) == 0:
            error_msg = f'无可用的浏览器用户ID，可用用户ID池为空。配置的用户ID: {task_manager.available_user_ids}'
        else:
            error_msg = f'无法重新启动任务，原因未知。运行任务数: {status["running_count"]}/{status["max_concurrent"]}，可用浏览器: {len(task_manager.user_id_pool)}'
        
        return jsonify({
            'success': False, 
            'error': error_msg,
            'details': error_details
        }), 400
    
    try:
        # 获取任务
        task = ScrapingTask.query.get_or_404(task_id)
        
        # 重置任务状态
        task.status = 'pending'
        task.result_count = 0
        task.started_at = None
        task.completed_at = None
        task.error_message = None
        
        # 删除该任务之前抓取的数据（可选，根据需求决定）
        # TweetData.query.filter_by(task_id=task_id).delete()
        
        db.session.commit()
        
        # 启动任务
        success, message = task_manager.start_task(task_id)
        if success:
            return jsonify({'success': True, 'message': '任务已重新启动'})
        else:
            # 获取更详细的状态信息
            status = task_manager.get_task_status()
            error_details = {
                'running_count': status['running_count'],
                'max_concurrent': status['max_concurrent'],
                'available_slots': status['available_slots'],
                'available_browsers': status['available_browsers'],
                'user_id_pool': len(task_manager.user_id_pool),
                'available_user_ids': task_manager.available_user_ids,
                'original_message': message
            }
            return jsonify({
                'success': False, 
                'error': f'重新启动失败: {message}',
                'details': error_details
            }), 400
        
    except Exception as e:
        # 获取详细的异常信息
        import traceback
        error_details = {
            'exception_type': type(e).__name__,
            'exception_message': str(e),
            'traceback': traceback.format_exc()
        }
        return jsonify({
            'success': False, 
            'error': f'重新启动异常: {str(e)}',
            'details': error_details
        }), 500

@app.route('/api/tasks/<int:task_id>', methods=['GET'])
def api_get_task(task_id):
    """获取单个任务详情"""
    try:
        task = ScrapingTask.query.get_or_404(task_id)
        
        # 获取任务相关的推文数据统计
        tweets_count = TweetData.query.filter_by(task_id=task_id).count()
        recent_tweets = TweetData.query.filter_by(task_id=task_id).order_by(TweetData.scraped_at.desc()).limit(5).all()
        
        task_data = task.to_dict()
        task_data['tweets_count'] = tweets_count
        task_data['recent_tweets'] = [tweet.to_dict() for tweet in recent_tweets]
        
        # 返回HTML格式的任务详情（用于模态框显示）
        return render_template('task_detail.html', task=task, tweets_count=tweets_count, recent_tweets=recent_tweets)
        
    except Exception as e:
        return f'<div class="alert alert-danger">加载任务详情失败: {str(e)}</div>', 500

@app.route('/api/tasks/<int:task_id>/tweets', methods=['GET'])
def api_get_task_tweets(task_id):
    """获取任务的推文数据（JSON格式）"""
    try:
        task = ScrapingTask.query.get_or_404(task_id)
        
        # 获取任务相关的推文数据
        tweets = TweetData.query.filter_by(task_id=task_id).order_by(TweetData.scraped_at.desc()).all()
        
        return jsonify({
            'success': True,
            'task': task.to_dict(),
            'tweets_count': len(tweets),
            'tweets': [tweet.to_dict() for tweet in tweets]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
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
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/data/<int:tweet_id>')
def tweet_detail(tweet_id):
    """推文详情页面"""
    try:
        tweet = TweetData.query.get_or_404(tweet_id)
        return render_template('tweet_detail.html', tweet=tweet)
    except Exception as e:
        flash(f'加载推文详情失败: {str(e)}', 'danger')
        return redirect(url_for('data'))


@app.route('/data/<int:tweet_id>', methods=['DELETE'])
def api_delete_tweet(tweet_id):
    """删除推文"""
    try:
        tweet = TweetData.query.get_or_404(tweet_id)
        db.session.delete(tweet)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '推文已删除'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/chart_data')
def api_chart_data():
    """获取图表数据"""
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import func, extract
        import re
        
        # 每日推文数量统计（最近30天）
        thirty_days_ago = datetime.now() - timedelta(days=30)
        daily_tweets = db.session.query(
            func.date(TweetData.scraped_at).label('date'),
            func.count(TweetData.id).label('count')
        ).filter(
            TweetData.scraped_at >= thirty_days_ago
        ).group_by(
            func.date(TweetData.scraped_at)
        ).order_by('date').all()
        
        # 格式化每日推文数据
        daily_data = {
            'labels': [item.date.strftime('%m-%d') if hasattr(item.date, 'strftime') else str(item.date) for item in daily_tweets],
            'data': [item.count for item in daily_tweets]
        }
        
        # 热门话题标签统计（提取#标签）
        tweets_with_hashtags = TweetData.query.filter(
            TweetData.content.like('%#%')
        ).limit(1000).all()  # 限制查询数量以提高性能
        
        hashtag_counts = {}
        for tweet in tweets_with_hashtags:
            # 使用正则表达式提取话题标签
            hashtags = re.findall(r'#\w+', tweet.content)
            for hashtag in hashtags:
                hashtag_counts[hashtag] = hashtag_counts.get(hashtag, 0) + 1
        
        # 取前10个热门标签
        top_hashtags = sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        hashtags_data = {
            'labels': [item[0] for item in top_hashtags],
            'data': [item[1] for item in top_hashtags]
        }
        
        # 互动数据趋势（最近30天的平均互动数）
        engagement_data = db.session.query(
            func.date(TweetData.scraped_at).label('date'),
            func.avg(TweetData.likes).label('avg_likes'),
            func.avg(TweetData.retweets).label('avg_retweets'),
            func.avg(TweetData.comments).label('avg_comments')
        ).filter(
            TweetData.scraped_at >= thirty_days_ago
        ).group_by(
            func.date(TweetData.scraped_at)
        ).order_by('date').all()
        
        # 格式化互动数据
        engagement_chart_data = {
            'labels': [item.date.strftime('%m-%d') if hasattr(item.date, 'strftime') else str(item.date) for item in engagement_data],
            'datasets': [
                {
                    'label': '平均点赞数',
                    'data': [float(item.avg_likes or 0) for item in engagement_data],
                    'borderColor': 'rgb(255, 99, 132)',
                    'backgroundColor': 'rgba(255, 99, 132, 0.2)'
                },
                {
                    'label': '平均转发数',
                    'data': [float(item.avg_retweets or 0) for item in engagement_data],
                    'borderColor': 'rgb(54, 162, 235)',
                    'backgroundColor': 'rgba(54, 162, 235, 0.2)'
                },
                {
                    'label': '平均评论数',
                    'data': [float(item.avg_comments or 0) for item in engagement_data],
                    'borderColor': 'rgb(255, 205, 86)',
                    'backgroundColor': 'rgba(255, 205, 86, 0.2)'
                }
            ]
        }
        
        return jsonify({
            'success': True,
            'data': {
                'daily_tweets': daily_data,
                'hashtags': hashtags_data,
                'engagement': engagement_chart_data
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取图表数据失败: {str(e)}'
        }), 500

@app.route('/api/data/export')
def api_export_data():
    """导出数据为Excel文件（支持异步处理）"""
    try:
        from datetime import datetime
        import io
        import pandas as pd
        from flask import send_file
        import json
        from utils.async_task_manager import get_task_manager, TaskType, TaskPriority
        
        # 获取筛选参数
        search = request.args.get('search', '')
        task_id = request.args.get('task_id', type=int)
        min_likes = request.args.get('min_likes', type=int)
        min_retweets = request.args.get('min_retweets', type=int)
        async_export = request.args.get('async', 'false').lower() == 'true'
        
        # 构建查询（与data页面相同的筛选逻辑）
        query = TweetData.query.join(ScrapingTask, TweetData.task_id == ScrapingTask.id)
        
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
        
        # 点赞数过滤
        if min_likes is not None:
            query = query.filter(TweetData.likes >= min_likes)
        
        # 转发数过滤
        if min_retweets is not None:
            query = query.filter(TweetData.retweets >= min_retweets)
        
        # 按抓取时间排序
        tweets = query.order_by(TweetData.scraped_at.desc()).all()
        
        if not tweets:
            return jsonify({'success': False, 'error': '没有数据可导出'}), 400
        
        # 根据数据量和用户选择决定是否使用异步处理
        data_count = len(tweets)
        should_use_async = async_export or data_count > 1000
        
        if should_use_async:
            # 使用异步任务管理器处理大量数据导出
            task_manager = get_task_manager()
            
            # 根据数据量设置优先级
            if data_count > 5000:
                priority = TaskPriority.LOW
            elif data_count > 1000:
                priority = TaskPriority.NORMAL
            else:
                priority = TaskPriority.HIGH
            
            # 生成异步任务ID
            async_task_id = f"excel_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{data_count}"
            
            # 提交异步导出任务
            success = task_manager.submit_excel_write(
                file_path=f"./data/export_{async_task_id}.xlsx",
                data={
                    'tweets': [tweet.to_dict() for tweet in tweets],
                    'search': search,
                    'task_id': task_id,
                    'min_likes': min_likes,
                    'min_retweets': min_retweets,
                    'export_type': 'filtered_data'
                },
                priority=priority,
                max_retries=2
            )
            
            if success:
                return jsonify({
                    'success': True,
                    'message': f'已提交 {data_count} 条数据到异步导出队列',
                    'async_task_id': async_task_id,
                    'data_count': data_count,
                    'is_async': True
                })
            else:
                # 异步提交失败，回退到同步处理
                pass
        
        # 准备导出数据 - 包含所有重要字段
        export_data = []
        # 缓存任务名称以提高性能
        task_name_cache = {}
        
        for tweet in tweets:
            # 获取任务名称
            task_name = ''
            if tweet.task_id:
                if tweet.task_id not in task_name_cache:
                    task = ScrapingTask.query.get(tweet.task_id)
                    task_name_cache[tweet.task_id] = task.name if task else ''
                task_name = task_name_cache[tweet.task_id]
            
            # 处理话题标签
            hashtags_str = ''
            if tweet.hashtags:
                try:
                    hashtags_list = json.loads(tweet.hashtags) if isinstance(tweet.hashtags, str) else tweet.hashtags
                    if isinstance(hashtags_list, list):
                        hashtags_str = ', '.join([f'#{tag}' for tag in hashtags_list if tag])
                    else:
                        hashtags_str = str(tweet.hashtags)
                except (json.JSONDecodeError, TypeError):
                    hashtags_str = str(tweet.hashtags) if tweet.hashtags else ''
            
            # 处理发布时间
            publish_time_str = ''
            if tweet.publish_time:
                if isinstance(tweet.publish_time, str):
                    publish_time_str = tweet.publish_time
                else:
                    publish_time_str = tweet.publish_time.strftime('%Y-%m-%d %H:%M:%S')
            
            # 处理多媒体内容
            media_info = ''
            if tweet.media_content:
                try:
                    media_list = json.loads(tweet.media_content) if isinstance(tweet.media_content, str) else tweet.media_content
                    if isinstance(media_list, list) and media_list:
                        media_types = [item.get('type', '未知') for item in media_list if isinstance(item, dict)]
                        media_info = ', '.join(media_types)
                except (json.JSONDecodeError, TypeError):
                    media_info = '有媒体内容' if tweet.media_content else ''
            
            # 构建导出行数据
            row = {
                'ID': tweet.id,
                '推文原文内容': tweet.content or '',
                '完整内容': tweet.full_content or tweet.content or '',
                '作者（账号）': tweet.username or '',
                '发布时间': publish_time_str,
                '推文链接': tweet.link or '',
                '话题标签': hashtags_str,
                '类型标签': tweet.content_type or '',
                '评论数': tweet.comments or 0,
                '点赞数': tweet.likes or 0,
                '转发数': tweet.retweets or 0,
                '多媒体内容': media_info,
                '抓取时间': tweet.scraped_at.strftime('%Y-%m-%d %H:%M:%S') if tweet.scraped_at else '',
                '任务名称': task_name,
                '任务ID': tweet.task_id,
                '是否已同步飞书': '是' if tweet.synced_to_feishu else '否',
                '是否包含详情内容': '是' if tweet.has_detailed_content else '否',
                '详情抓取错误': tweet.detail_error or ''
            }
            
            export_data.append(row)
        
        # 创建Excel文件
        df = pd.DataFrame(export_data)
        
        # 生成文件名
        filename_template = SystemConfig.query.filter_by(key='export_filename_template').first()
        
        # 获取任务名称
        task_name = 'all_data'
        if tweets and tweets[0].task_id:
            task = ScrapingTask.query.get(tweets[0].task_id)
            if task:
                task_name = task.name
        
        if filename_template and filename_template.value:
            filename = filename_template.value.format(
                date=datetime.now().strftime('%Y%m%d'),
                time=datetime.now().strftime('%H%M%S'),
                task_name=task_name
            )
        else:
            filename = f'twitter_data_{task_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        
        # 创建内存中的Excel文件
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 写入数据到Excel
            df.to_excel(writer, sheet_name='推文数据', index=False)
            
            # 获取工作表并设置列宽
            worksheet = writer.sheets['推文数据']
            
            # 设置列宽以适应内容
            column_widths = {
                'A': 8,   # ID
                'B': 50,  # 推文原文内容
                'C': 50,  # 完整内容
                'D': 20,  # 作者（账号）
                'E': 20,  # 发布时间
                'F': 40,  # 推文链接
                'G': 30,  # 话题标签
                'H': 15,  # 类型标签
                'I': 10,  # 评论数
                'J': 10,  # 点赞数
                'K': 10,  # 转发数
                'L': 20,  # 多媒体内容
                'M': 20,  # 抓取时间
                'N': 20,  # 任务名称
                'O': 10,  # 任务ID
                'P': 15,  # 是否已同步飞书
                'Q': 15,  # 是否包含详情内容
                'R': 30   # 详情抓取错误
            }
            
            for col, width in column_widths.items():
                worksheet.column_dimensions[col].width = width
            
            # 设置表头样式
            from openpyxl.styles import Font, PatternFill, Alignment
            header_font = Font(bold=True, color='FFFFFF')
            header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
            header_alignment = Alignment(horizontal='center', vertical='center')
            
            for cell in worksheet[1]:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_alignment
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'{filename}.xlsx'
        )
        
    except Exception as e:
        print(f"Excel导出错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'导出失败: {str(e)}'}), 500

@app.route('/api/data/export/<int:task_id>')
def api_export_task_data(task_id):
    """导出特定任务数据"""
    try:
        tweets = TweetData.query.filter_by(task_id=task_id).all()
        
        # 转换为字典格式
        data = [tweet.to_dict() for tweet in tweets]
        
        return jsonify({
            'success': True,
            'data': data,
            'count': len(data)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/data/sync_feishu/<int:task_id>', methods=['POST'])
def api_sync_feishu(task_id):
    """同步数据到飞书多维表格（支持异步）"""
    print(f"\n🔄 [FEISHU_SYNC] 开始同步任务 {task_id} 到飞书")
    print(f"⏰ [FEISHU_SYNC] 同步时间: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 检查飞书配置
        print(f"📋 [FEISHU_SYNC] 检查飞书配置...")
        if not FEISHU_CONFIG.get('enabled'):
            print(f"❌ [FEISHU_SYNC] 飞书同步未启用")
            return jsonify({'success': False, 'error': '飞书同步未启用'}), 400
        
        print(f"✅ [FEISHU_SYNC] 飞书同步已启用")
        
        # 检查飞书配置完整性
        print(f"🔍 [FEISHU_SYNC] 检查配置完整性...")
        required_fields = ['app_id', 'app_secret', 'spreadsheet_token', 'table_id']
        missing_fields = [field for field in required_fields if not FEISHU_CONFIG.get(field)]
        if missing_fields:
            print(f"❌ [FEISHU_SYNC] 配置不完整，缺少字段: {missing_fields}")
            return jsonify({
                'success': False, 
                'error': f'飞书配置不完整，缺少字段: {", ".join(missing_fields)}'
            }), 400
        
        print(f"✅ [FEISHU_SYNC] 配置完整性检查通过")
        print(f"📊 [FEISHU_SYNC] 配置信息: app_id={FEISHU_CONFIG.get('app_id')[:8]}..., spreadsheet_token={FEISHU_CONFIG.get('spreadsheet_token')[:8]}..., table_id={FEISHU_CONFIG.get('table_id')}")
        
        # 获取任务数据 - 只获取未同步的数据
        print(f"📊 [FEISHU_SYNC] 查询任务 {task_id} 的未同步数据...")
        # 使用0而不是False，因为SQLite中BOOLEAN存储为整数
        tweets = TweetData.query.filter_by(task_id=task_id, synced_to_feishu=0).all()
        print(f"📊 [FEISHU_SYNC] 找到 {len(tweets)} 条未同步数据")
        
        if not tweets:
            # 检查是否有已同步的数据
            print(f"🔍 [FEISHU_SYNC] 没有未同步数据，检查已同步数据...")
            # 使用1而不是True
            synced_count = TweetData.query.filter_by(task_id=task_id, synced_to_feishu=1).count()
            print(f"📊 [FEISHU_SYNC] 已同步数据数量: {synced_count}")
            if synced_count > 0:
                print(f"✅ [FEISHU_SYNC] 所有数据都已同步")
                return jsonify({'success': True, 'message': f'任务 {task_id} 的所有数据（{synced_count} 条）都已同步到飞书'})
            else:
                print(f"❌ [FEISHU_SYNC] 没有任何数据需要同步")
                return jsonify({'success': False, 'error': '没有数据需要同步'}), 400
        
        # 根据配置决定使用异步还是同步方式
        if FEISHU_CONFIG.get('async_enabled', False):
            return _handle_async_task_sync(task_id, tweets)
        else:
            return _handle_sync_task_sync(task_id, tweets)
        
    except Exception as e:
        print(f"❌ [FEISHU_SYNC] 同步过程中发生异常: {str(e)}")
        import traceback
        print(f"📋 [FEISHU_SYNC] 异常详情: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500

def _handle_async_task_sync(task_id, tweets):
    """处理异步任务同步"""
    try:
        print(f"🚀 [FEISHU_SYNC] 使用异步方式同步任务 {task_id}")
        
        # 准备同步数据
        data = _prepare_sync_data(tweets)
        
        # 获取异步同步管理器
        async_manager = get_async_sync_manager()
        if not async_manager:
            print(f"❌ [FEISHU_SYNC] 异步同步管理器未初始化，回退到同步方式")
            return _handle_sync_task_sync(task_id, tweets)
        
        # 提交异步任务
        feishu_credentials = {
            'app_id': FEISHU_CONFIG['app_id'],
            'app_secret': FEISHU_CONFIG['app_secret'],
            'spreadsheet_token': FEISHU_CONFIG['spreadsheet_token'],
            'table_id': FEISHU_CONFIG['table_id']
        }
        
        priority = FEISHU_CONFIG.get('async_priority', 5)
        sync_task_id = async_manager.submit_task(data, feishu_credentials, priority)
        
        if sync_task_id:
            print(f"✅ [FEISHU_SYNC] 异步任务已提交，任务ID: {sync_task_id}")
            return jsonify({
                'success': True, 
                'message': f'已提交 {len(data)} 条数据到异步同步队列',
                'async_task_id': sync_task_id,
                'data_count': len(data)
            })
        else:
            print(f"❌ [FEISHU_SYNC] 异步任务提交失败，回退到同步方式")
            return _handle_sync_task_sync(task_id, tweets)
            
    except Exception as e:
        print(f"❌ [FEISHU_SYNC] 异步同步异常: {e}，回退到同步方式")
        return _handle_sync_task_sync(task_id, tweets)

def _handle_sync_task_sync(task_id, tweets):
    """处理同步任务同步"""
    try:
        print(f"🔄 [FEISHU_SYNC] 使用同步方式同步任务 {task_id}")
        
        # 初始化云同步管理器
        print(f"🔧 [FEISHU_SYNC] 初始化云同步管理器...")
        sync_config = {
            'feishu': {
                'enabled': True,
                'app_id': FEISHU_CONFIG['app_id'],
                'app_secret': FEISHU_CONFIG['app_secret'],
                'spreadsheet_token': FEISHU_CONFIG['spreadsheet_token'],
                'table_id': FEISHU_CONFIG['table_id'],
                'base_url': 'https://open.feishu.cn/open-apis'
            }
        }
        sync_manager = CloudSyncManager(sync_config)
        print(f"✅ [FEISHU_SYNC] 云同步管理器初始化完成")
        
        # 准备数据
        data = _prepare_sync_data(tweets)
        
        # 同步到飞书多维表格
        print(f"🚀 [FEISHU_SYNC] 开始同步 {len(data)} 条数据到飞书多维表格...")
        success = sync_manager.sync_to_feishu(
            data,
            FEISHU_CONFIG['spreadsheet_token'],
            FEISHU_CONFIG['table_id']
        )
        
        if success:
            print(f"✅ [FEISHU_SYNC] 同步成功，开始更新数据库状态...")
            # 更新同步状态
            for tweet in tweets:
                tweet.synced_to_feishu = 1
                tweet.content_type = classify_content_type(tweet.content)
            
            db.session.commit()
            print(f"✅ [FEISHU_SYNC] 数据库更新完成")
            
            # 执行数据验证
            validation_msg = ""
            try:
                from feishu_data_validator import FeishuDataValidator
                validator = FeishuDataValidator()
                validation_result = validator.validate_sync_data(task_id=task_id)
                
                if validation_result.get('success'):
                    comparison = validation_result['comparison_result']
                    summary = comparison['summary']
                    validation_msg = f"，验证结果: 准确率 {summary['sync_accuracy']:.2f}% ({summary['matched_count']}/{summary['total_local']} 条匹配)"
                    if summary['sync_accuracy'] < 95:
                        validation_msg += f"，发现 {summary['field_mismatch_count']} 条字段不匹配"
                else:
                    validation_msg = "，数据验证失败"
            except Exception as e:
                validation_msg = "，数据验证异常"
            
            return jsonify({'success': True, 'message': f'成功同步 {len(data)} 条数据到飞书多维表格{validation_msg}'})
        else:
            return jsonify({'success': False, 'error': '飞书同步失败'}), 500
            
    except Exception as e:
        print(f"❌ [FEISHU_SYNC] 同步异常: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/status')
def api_status():
    """获取系统状态"""
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
        
        # 获取并行任务状态
        task_status = task_manager.get_task_status()
        
        # 获取当前运行的任务详情
        current_tasks = []
        for task_id in task_status['running_tasks']:
            task = ScrapingTask.query.get(task_id)
            if task:
                current_tasks.append({
                    'id': task.id,
                    'name': task.name,
                    'status': task.status,
                    'started_at': task.started_at.isoformat() if task.started_at else None
                })
        
        # 获取异步同步状态
        async_sync_status = {}
        try:
            async_manager = get_async_sync_manager()
            if async_manager:
                async_sync_status = async_manager.get_all_tasks_status()
        except Exception as e:
            print(f"获取异步同步状态失败: {e}")
        
        return jsonify({
            'success': True,
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
                'parallel_status': {
                    'running_count': task_status['running_count'],
                    'max_concurrent': task_status['max_concurrent'],
                    'available_slots': task_status['available_slots'],
                    'available_browsers': task_status['available_browsers'],
                    'current_tasks': current_tasks
                },
                'async_sync_status': async_sync_status,
                'system_running': task_status['running_count'] > 0
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/config/feishu', methods=['GET'])
def api_get_feishu_config():
    """获取飞书配置"""
    return jsonify({
        'app_id': FEISHU_CONFIG['app_id'],
        'app_secret': FEISHU_CONFIG['app_secret'] if FEISHU_CONFIG['app_secret'] else '未配置',
        'spreadsheet_token': FEISHU_CONFIG['spreadsheet_token'],
        'table_id': FEISHU_CONFIG['table_id'],
        'enabled': FEISHU_CONFIG['enabled'],
        'auto_sync': FEISHU_CONFIG.get('auto_sync', False)
    })

@app.route('/api/config/feishu', methods=['POST'])
def api_update_feishu_config():
    """更新飞书配置"""
    try:
        data = request.get_json()
        
        # 准备飞书配置数据
        feishu_configs = {
            'feishu_app_id': data.get('app_id', FEISHU_CONFIG['app_id']),
            'feishu_app_secret': data.get('app_secret', FEISHU_CONFIG['app_secret']),
            'feishu_spreadsheet_token': data.get('spreadsheet_token', FEISHU_CONFIG['spreadsheet_token']),
            'feishu_table_id': data.get('table_id', FEISHU_CONFIG['table_id']),
            'feishu_enabled': str(data.get('enabled', FEISHU_CONFIG['enabled'])),
            'feishu_auto_sync': str(data.get('auto_sync', FEISHU_CONFIG.get('auto_sync', False))),
            'feishu_async_enabled': str(data.get('async_enabled', FEISHU_CONFIG.get('async_enabled', False))),
            'feishu_async_max_workers': str(data.get('async_max_workers', FEISHU_CONFIG.get('async_max_workers', 3))),
            'feishu_async_max_queue_size': str(data.get('async_max_queue_size', FEISHU_CONFIG.get('async_max_queue_size', 100))),
            'feishu_async_max_retries': str(data.get('async_max_retries', FEISHU_CONFIG.get('async_max_retries', 3))),
            'feishu_async_priority': str(data.get('async_priority', FEISHU_CONFIG.get('async_priority', 5))),
            'sync_interval': str(data.get('sync_interval', 300))
        }
        
        # 更新或创建配置记录到数据库
        for key, value in feishu_configs.items():
            config = SystemConfig.query.filter_by(key=key).first()
            if config:
                config.value = str(value)
                config.updated_at = datetime.utcnow()
            else:
                config = SystemConfig(
                    key=key,
                    value=str(value),
                    description=f'飞书配置: {key}'
                )
                db.session.add(config)
        
        db.session.commit()
        
        # 更新全局配置（用于当前会话）
        FEISHU_CONFIG.update({
            'app_id': feishu_configs['feishu_app_id'],
            'app_secret': feishu_configs['feishu_app_secret'],
            'spreadsheet_token': feishu_configs['feishu_spreadsheet_token'],
            'table_id': feishu_configs['feishu_table_id'],
            'enabled': feishu_configs['feishu_enabled'].lower() == 'true',
            'auto_sync': feishu_configs['feishu_auto_sync'].lower() == 'true',
            'async_enabled': feishu_configs['feishu_async_enabled'].lower() == 'true',
            'async_max_workers': int(feishu_configs['feishu_async_max_workers']),
            'async_max_queue_size': int(feishu_configs['feishu_async_max_queue_size']),
            'async_max_retries': int(feishu_configs['feishu_async_max_retries']),
            'async_priority': int(feishu_configs['feishu_async_priority'])
        })
        
        return jsonify({'success': True, 'message': '飞书配置更新成功'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/async_sync/tasks', methods=['GET'])
def api_get_async_sync_tasks():
    """获取所有异步同步任务状态"""
    try:
        async_manager = get_async_sync_manager()
        if not async_manager:
            return jsonify({'success': False, 'error': '异步同步服务未启用'}), 400
        
        tasks_status = async_manager.get_all_tasks_status()
        return jsonify({'success': True, 'data': tasks_status})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/async_sync/tasks/<task_id>', methods=['GET'])
def api_get_async_sync_task(task_id):
    """获取指定异步同步任务状态"""
    try:
        async_manager = get_async_sync_manager()
        if not async_manager:
            return jsonify({'success': False, 'error': '异步同步服务未启用'}), 400
        
        task_status = async_manager.get_task_status(task_id)
        if task_status:
            return jsonify({'success': True, 'data': task_status})
        else:
            return jsonify({'success': False, 'error': f'任务 {task_id} 不存在'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/async_sync/tasks/<task_id>/cancel', methods=['POST'])
def api_cancel_async_sync_task(task_id):
    """取消指定异步同步任务"""
    try:
        async_manager = get_async_sync_manager()
        if not async_manager:
            return jsonify({'success': False, 'error': '异步同步服务未启用'}), 400
        
        success = async_manager.cancel_task(task_id)
        if success:
            return jsonify({'success': True, 'message': f'任务 {task_id} 已取消'})
        else:
            return jsonify({'success': False, 'error': f'无法取消任务 {task_id}，可能已完成或不存在'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# 定时任务管理API
@app.route('/api/scheduler/tasks', methods=['GET'])
def api_get_scheduled_tasks():
    """获取所有定时任务"""
    try:
        if not task_scheduler:
            return jsonify({'success': False, 'error': '定时任务调度器未初始化'}), 500
        
        tasks = task_scheduler.get_all_tasks()
        return jsonify({'success': True, 'data': tasks})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scheduler/tasks/<task_id>', methods=['GET'])
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
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scheduler/tasks', methods=['POST'])
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
            return jsonify({'success': True, 'message': f'定时任务 {data["task_id"]} 创建成功'})
        else:
            return jsonify({'success': False, 'error': '创建定时任务失败'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scheduler/tasks/<task_id>/enable', methods=['POST'])
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
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scheduler/tasks/<task_id>/disable', methods=['POST'])
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
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scheduler/tasks/<task_id>/run', methods=['POST'])
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
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scheduler/tasks/<task_id>', methods=['DELETE'])
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
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scheduler/status', methods=['GET'])
def api_get_scheduler_status():
    """获取调度器状态"""
    try:
        if not task_scheduler:
            return jsonify({'success': False, 'error': '定时任务调度器未初始化'}), 500
        
        status = task_scheduler.get_status()
        return jsonify({'success': True, 'data': status})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scheduler/statistics', methods=['GET'])
def api_get_scheduler_statistics():
    """获取调度器统计信息"""
    try:
        if not task_scheduler:
            return jsonify({'success': False, 'error': '定时任务调度器未初始化'}), 500
        
        stats = task_scheduler.get_statistics()
        return jsonify({'success': True, 'data': stats})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/data/validate_feishu/<int:task_id>', methods=['POST'])
def api_validate_feishu_data(task_id):
    """验证飞书数据同步准确性"""
    try:
        print(f"\n🔍 [FEISHU_VALIDATE] 开始验证任务 {task_id} 的飞书数据")
        print(f"⏰ [FEISHU_VALIDATE] 验证时间: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 检查飞书配置
        if not FEISHU_CONFIG.get('enabled'):
            return jsonify({'success': False, 'error': '飞书同步未启用'}), 400
        
        required_fields = ['app_id', 'app_secret', 'spreadsheet_token', 'table_id']
        missing_fields = [field for field in required_fields if not FEISHU_CONFIG.get(field)]
        if missing_fields:
            return jsonify({
                'success': False, 
                'error': f'飞书配置不完整，缺少字段: {", ".join(missing_fields)}'
            }), 400
        
        # 检查任务是否存在
        task = ScrapingTask.query.get(task_id)
        if not task:
            return jsonify({'success': False, 'error': f'任务 {task_id} 不存在'}), 404
        
        # 执行数据验证
        from feishu_data_validator import FeishuDataValidator
        validator = FeishuDataValidator()
        validation_result = validator.validate_sync_data(task_id=task_id)
        
        if validation_result.get('success'):
            comparison = validation_result['comparison_result']
            summary = comparison['summary']
            
            print(f"✅ [FEISHU_VALIDATE] 验证完成")
            print(f"📊 [FEISHU_VALIDATE] 同步准确率: {summary['sync_accuracy']:.2f}%")
            
            # 构建详细的验证报告
            validation_report = {
                'task_id': task_id,
                'task_name': task.name,
                'validation_time': validation_result.get('validation_time'),
                'summary': summary,
                'details': {
                    'matched_records_count': len(comparison['matched_records']),
                    'missing_in_feishu_count': len(comparison['missing_in_feishu']),
                    'extra_in_feishu_count': len(comparison['extra_in_feishu']),
                    'field_mismatches_count': len(comparison['field_mismatches'])
                },
                'quality_assessment': {
                    'level': 'excellent' if summary['sync_accuracy'] >= 95 else 'good' if summary['sync_accuracy'] >= 85 else 'needs_improvement',
                    'description': f"同步准确率 {summary['sync_accuracy']:.2f}%"
                }
            }
            
            # 如果有不匹配的数据，提供样例
            if comparison['missing_in_feishu']:
                validation_report['missing_samples'] = comparison['missing_in_feishu'][:3]
            
            if comparison['field_mismatches']:
                validation_report['mismatch_samples'] = comparison['field_mismatches'][:3]
            
            return jsonify({
                'success': True, 
                'message': f'数据验证完成，准确率 {summary["sync_accuracy"]:.2f}%',
                'validation_report': validation_report
            })
        else:
            # 确保错误信息完整
            error_msg = validation_result.get('error')
            if not error_msg:
                error_msg = '数据验证失败，但未提供具体错误信息'
                print(f"⚠️ [FEISHU_VALIDATE] 警告: 验证结果中缺少错误信息")
                print(f"📋 [FEISHU_VALIDATE] 完整验证结果: {validation_result}")
            
            print(f"❌ [FEISHU_VALIDATE] 验证失败: {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 500
            
    except Exception as e:
        print(f"❌ [FEISHU_VALIDATE] 验证异常: {e}")
        import traceback
        print(f"📋 [FEISHU_VALIDATE] 异常详情: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/config/feishu/test', methods=['POST'])
def api_test_feishu_connection():
    """测试飞书连接"""
    import io
    import sys
    from contextlib import redirect_stdout, redirect_stderr
    
    # 捕获日志输出
    log_capture = io.StringIO()
    
    try:
        # 从请求体获取配置
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False, 
                'error': '请提供飞书配置信息', 
                'status_code': 400,
                'logs': []
            }), 400
        
        # 检查必填字段
        required_fields = ['app_id', 'app_secret', 'spreadsheet_token', 'table_id']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({
                'success': False, 
                'error': f'飞书配置不完整，缺少字段: {", ".join(missing_fields)}',
                'status_code': 400,
                'logs': []
            }), 400
        
        # 创建测试配置
        test_config = {
            'feishu': {
                'enabled': True,
                'app_id': data['app_id'],
                'app_secret': data['app_secret'],
                'spreadsheet_token': data['spreadsheet_token'],
                'table_id': data['table_id']
            }
        }
        
        # 捕获控制台输出
        with redirect_stdout(log_capture), redirect_stderr(log_capture):
            print(f"[飞书测试] 开始测试连接...")
            print(f"[飞书测试] App ID: {data['app_id']}")
            print(f"[飞书测试] 文档Token: {data['spreadsheet_token']}")
            print(f"[飞书测试] 表格ID: {data['table_id']}")
            
            # 初始化云同步管理器
            sync_manager = CloudSyncManager(test_config)
            
            # 设置飞书配置
            print(f"[飞书测试] 正在设置飞书配置...")
            if not sync_manager.setup_feishu(data['app_id'], data['app_secret']):
                print(f"[飞书测试] 飞书配置设置失败")
                logs = log_capture.getvalue().split('\n')
                return jsonify({
                    'success': False, 
                    'error': '飞书配置设置失败', 
                    'status_code': 500,
                    'logs': logs
                }), 500
            
            print(f"[飞书测试] 飞书配置设置成功")
            
            # 测试连接（发送一条测试数据）
            current_time = datetime.utcnow()
            test_data = [{
                '推文原文内容': '测试连接 - ' + current_time.strftime('%Y-%m-%d %H:%M:%S'),
                '推文原 文内容': '测试连接 - ' + current_time.strftime('%Y-%m-%d %H:%M:%S'),
                '发布时间': current_time.strftime('%Y-%m-%d %H:%M:%S'),  # 使用字符串格式
                '作者（账号）': 'test_user',
                '推文链接': 'https://twitter.com/test',
                '话题标签（Hashtag）': '#测试',
                '类型标签': '测试',
                '评论': 0,
                '转发': 0,
                '点赞': 0,
                '创建时间': current_time.strftime('%Y-%m-%d %H:%M:%S')  # 使用字符串格式
            }]
            
            print(f"[飞书测试] 正在发送测试数据...")
            
            try:
                success = sync_manager.sync_to_feishu(
                    test_data,
                    data['spreadsheet_token'],
                    data['table_id']
                )
                
                # 获取捕获的日志
                logs = log_capture.getvalue().split('\n')
                logs = [log.strip() for log in logs if log.strip()]  # 过滤空行
                
                if success:
                    print(f"[飞书测试] 连接测试成功！")
                    logs = log_capture.getvalue().split('\n')
                    logs = [log.strip() for log in logs if log.strip()]
                    return jsonify({
                        'success': True, 
                        'message': '飞书连接测试成功', 
                        'status_code': 200,
                        'logs': logs
                    }), 200
                else:
                    print(f"[飞书测试] 同步操作返回失败")
                    logs = log_capture.getvalue().split('\n')
                    logs = [log.strip() for log in logs if log.strip()]
                    return jsonify({
                        'success': False, 
                        'error': '飞书连接测试失败：同步操作返回失败', 
                        'status_code': 500,
                        'logs': logs
                    }), 500
            except Exception as sync_error:
                print(f"[飞书测试] 同步异常: {str(sync_error)}")
                logs = log_capture.getvalue().split('\n')
                logs = [log.strip() for log in logs if log.strip()]
                return jsonify({
                    'success': False, 
                    'error': f'飞书连接测试失败：{str(sync_error)}', 
                    'status_code': 500,
                    'logs': logs
                }), 500
            
    except Exception as e:
        logs = log_capture.getvalue().split('\n')
        logs = [log.strip() for log in logs if log.strip()]
        return jsonify({
            'success': False, 
            'error': f'飞书连接测试失败: {str(e)}', 
            'status_code': 500,
            'logs': logs
        }), 500

@app.route('/api/tweet/update_content_type', methods=['POST'])
def api_update_tweet_content_type():
    """更新推文的类型标签"""
    try:
        data = request.get_json()
        tweet_id = data.get('tweet_id')
        content_type = data.get('content_type', '').strip()
        
        if not tweet_id:
            return jsonify({
                'success': False,
                'message': '缺少推文ID'
            })
        
        # 查找推文
        tweet = TweetData.query.get(tweet_id)
        if not tweet:
            return jsonify({
                'success': False,
                'message': '推文不存在'
            })
        
        # 更新类型标签
        tweet.content_type = content_type
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '类型标签更新成功',
            'tweet_id': tweet_id,
            'content_type': content_type
        })
        
    except Exception as e:
        logger.error(f"更新推文类型标签失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'更新失败: {str(e)}'
        })

@app.route('/api/check_adspower_installation', methods=['POST'])
def api_check_adspower_installation():
    """检测AdsPower安装状态"""
    try:
        app.logger.debug('Starting api_check_adspower_installation')
        
        # 从数据库获取配置信息
        configs = SystemConfig.query.all()
        config_dict = {cfg.key: cfg.value for cfg in configs}
        
        # 获取API配置信息 - AdsPower API 地址现在由配置文件管理
        # 注意：API状态检查已移除，现在直接从配置文件读取参数进行测试
        
        # 使用配置文件中的固定API地址
        api_url = ADS_POWER_CONFIG.get('local_api_url', 'http://local.adspower.net:50325')
        test_url = f"{api_url}/api/v1/user/list"
        
        # 准备请求头 - API Key 现在由配置文件管理
        headers = {}
        
        try:
            response = requests.get(test_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    # AdsPower正在运行
                    users = result.get('data', {}).get('list', [])
                    response = jsonify({
                        'success': True,
                        'message': 'AdsPower已安装并正在运行',
                        'user_count': len(users),
                        'api_url': api_url
                    })
                    response.headers['Content-Type'] = 'application/json'
                    return response
                else:
                    return jsonify({
                        'success': False,
                        'message': f'AdsPower API返回错误: {result.get("msg", "未知错误")}'
                    })
            elif response.status_code == 401:
                return jsonify({
                    'success': False,
                    'message': 'API Key验证失败，请检查API Key是否正确'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': f'HTTP错误: {response.status_code}'
                })
                
        except requests.exceptions.ConnectionError as e:
            return jsonify({
                'success': False,
                'message': f'连接失败: 无法连接到 {api_url}，请确保AdsPower已启动'
            })
        except requests.exceptions.Timeout as e:
            return jsonify({
                'success': False,
                'message': '连接超时: AdsPower响应超时'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'请求错误: {str(e)}'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'检测失败: {str(e)}'
        })

@app.route('/api/test_adspower_connection', methods=['POST'])
def api_test_adspower_connection():
    """测试AdsPower连接 - 直接从配置文件读取参数"""
    try:
        # 直接从AdsPower配置文件导入配置
        from config.adspower_config import get_config
        adspower_config = get_config()
        
        # 从配置文件获取所有必要参数
        api_host = adspower_config['api_host']
        api_port = adspower_config['api_port']
        api_key = adspower_config['api_key']
        user_ids = adspower_config['user_ids']
        
        app.logger.info(f"AdsPower Test - 从配置文件读取参数:")
        app.logger.info(f"AdsPower Test - api_host: {api_host}")
        app.logger.info(f"AdsPower Test - api_port: {api_port}")
        app.logger.info(f"AdsPower Test - api_key: {api_key[:8]}...")
        app.logger.info(f"AdsPower Test - user_ids: {user_ids}")
        
        if not user_ids:
            app.logger.error("AdsPower Test - 配置文件中未找到用户ID")
            return jsonify({'success': False, 'message': '配置文件中未找到用户ID，请检查 config/adspower_config.py'})
            
        # 使用第一个用户ID进行测试
        user_id = user_ids[0]
        app.logger.info(f"AdsPower Test - 使用用户ID进行测试: {user_id}")
        
        # AdsPower API 状态配置现在由配置文件管理
        
        # 构建API URL
        api_url = f'http://{api_host}:{api_port}'
        
        # 第一步：检查API接口状态
        status_url = f"{api_url}/status"
        
        try:
            status_response = requests.get(status_url, timeout=10)
            
            if status_response.status_code == 200:
                status_result = status_response.json()
                if status_result.get('code') != 0:
                    return jsonify({
                        'success': False,
                        'message': f'AdsPower API状态检查失败: {status_result.get("msg", "未知错误")}'
                    })
            else:
                return jsonify({
                    'success': False,
                    'message': f'AdsPower API状态检查失败，HTTP状态码: {status_response.status_code}'
                })
                
        except requests.exceptions.Timeout:
            return jsonify({
                'success': False,
                'message': 'AdsPower API状态检查超时，请检查AdsPower是否正在运行'
            })
        except requests.exceptions.ConnectionError:
            return jsonify({
                'success': False,
                'message': f'无法连接到AdsPower API ({api_url})，请检查AdsPower是否正在运行'
            })
        
        # 第二步：测试启动浏览器（使用官方文档的V2接口）
        start_browser_url = f"{api_url}/api/v2/browser-profile/start"
        
        # 准备请求数据
        browser_data = {
            'profile_id': user_id,
            'headless': '1',  # 使用headless模式进行测试
            'proxy_detection': '0',  # 关闭检测页面
            'last_opened_tabs': '0'  # 不打开上次的标签页
        }
        
        # 准备请求头
        headers = {'Content-Type': 'application/json'}
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        
        try:
            # 发送启动浏览器请求
            response = requests.post(start_browser_url, json=browser_data, headers=headers, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    # 启动成功，获取浏览器信息
                    browser_info = result.get('data', {})
                    ws_info = browser_info.get('ws', {})
                    
                    # 立即关闭浏览器（测试完成后清理）
                    close_url = f"{api_url}/api/v1/browser/stop"
                    close_params = {'user_id': user_id}
                    try:
                        requests.get(close_url, params=close_params, timeout=5)
                    except:
                        pass  # 忽略关闭浏览器的错误
                    
                    return jsonify({
                        'success': True, 
                        'message': f'AdsPower连接成功！环境ID {user_id} 可以正常启动',
                        'api_url': api_url,
                        'browser_info': {
                            'selenium_port': ws_info.get('selenium', ''),
                            'puppeteer_ws': ws_info.get('puppeteer', ''),
                            'debug_port': browser_info.get('debug_port', '')
                        }
                    })
                else:
                    error_msg = result.get('msg', '未知错误')
                    if 'not found' in error_msg.lower() or '不存在' in error_msg:
                        return jsonify({
                            'success': False, 
                            'message': f'环境ID {user_id} 不存在，请检查环境ID是否正确'
                        })
                    else:
                        return jsonify({
                            'success': False, 
                            'message': f'启动浏览器失败: {error_msg}'
                        })
            elif response.status_code == 401:
                return jsonify({
                    'success': False,
                    'message': 'API Key验证失败，请检查API Key是否正确'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': f'启动浏览器请求失败，HTTP状态码: {response.status_code}'
                })
                    
        except requests.exceptions.Timeout:
            return jsonify({
                'success': False,
                'message': '启动浏览器请求超时，请检查网络连接或AdsPower性能'
            })
        except requests.exceptions.ConnectionError:
            return jsonify({
                'success': False,
                'message': f'无法连接到AdsPower API ({api_url})'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'启动浏览器测试失败: {str(e)}'
            })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'连接测试失败: {str(e)}'})

@app.route('/api/test_open_adspower', methods=['POST'])
def api_test_open_adspower():
    """测试打开 AdsPower 浏览器窗口"""
    try:
        # 正确解析 JSON 数据
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        # AdsPower 配置现在由配置文件管理
        from config.adspower_config import get_config as get_adspower_config
        adspower_config = get_adspower_config()
        
        # 从配置文件获取配置信息
        user_id = data.get('user_id') or (adspower_config.user_ids[0] if adspower_config.user_ids else '')
        
        # AdsPower API 状态配置现在由配置文件管理
        
        if not user_id:
            return jsonify({'success': False, 'message': '请提供用户ID'})
        
        # 创建 AdsPowerLauncher 实例
        launcher_config = {
            'local_api_url': adspower_config['local_api_url'],
            'user_id': user_id,
            'api_key': adspower_config['api_key']
        }
        launcher = AdsPowerLauncher(launcher_config)
        
        # 调用 start_browser 方法
        browser_info = launcher.start_browser(user_id=user_id)
        
        if browser_info:
            return jsonify({
                'success': True,
                'message': 'AdsPower 浏览器窗口打开成功',
                'browser_info': browser_info
            })
        else:
            return jsonify({
                'success': False,
                'message': '打开浏览器失败'
            })
    except Exception as e:
        app.logger.error(f'Error in api_test_open_adspower: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'message': f'打开 AdsPower 失败: {str(e)}'
        })

# 页面结构分析相关API
@app.route('/page-analyzer')
def page_analyzer():
    """页面分析器"""
    return render_template('page_analyzer.html')

@app.route('/enhanced-scraping')
def enhanced_scraping():
    """增强推文抓取页面"""
    return render_template('enhanced_scraping.html')

@app.route('/scheduler')
def scheduler():
    """定时任务管理页面"""
    return render_template('scheduler.html')

@app.route('/tasks/status')
def tasks_status():
    """异步任务状态页面"""
    return render_template('tasks_status.html')

@app.route('/api/analyze-page-structure', methods=['POST'])
def api_analyze_page_structure():
    """分析页面结构API"""
    try:
        data = request.get_json()
        url = data.get('url')
        page_type = data.get('page_type', 'auto')
        
        if not url:
            return jsonify({'success': False, 'error': '请提供目标URL'}), 400
        
        # 启动浏览器
        browser_manager = AdsPowerLauncher(ADS_POWER_CONFIG)
        user_id = ADS_POWER_CONFIG['user_id']  # 从配置获取
        
        browser_info = browser_manager.start_browser(user_id)
        if not browser_info:
            return jsonify({'success': False, 'error': '浏览器启动失败'}), 500
        
        debug_port = browser_info.get('ws', {}).get('puppeteer')
        
        # 创建页面结构分析器
        analyzer = PageStructureAnalyzer(debug_port)
        
        # 分析页面结构
        def run_analysis():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(analyzer.analyze_page_structure(url, page_type))
            finally:
                loop.close()
        
        analysis_result = run_analysis()
        
        if analysis_result:
            return jsonify({
                'success': True,
                'data': analysis_result
            })
        else:
            return jsonify({'success': False, 'error': '页面结构分析失败'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': f'分析失败: {str(e)}'}), 500

# 全局智能采集任务管理
intelligent_scraping_tasks = {}

# 增强推文抓取任务管理
enhanced_scraping_tasks = {}

@app.route('/api/start-intelligent-scraping', methods=['POST'])
def api_start_intelligent_scraping():
    """启动智能采集API"""
    try:
        data = request.get_json()
        analysis = data.get('analysis')
        config = data.get('config', {})
        
        if not analysis:
            return jsonify({'success': False, 'error': '请先分析页面结构'}), 400
        
        # 生成任务ID
        task_id = f"intelligent_scraping_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # 启动浏览器
        browser_manager = AdsPowerLauncher(ADS_POWER_CONFIG)
        user_id = ADS_POWER_CONFIG['user_id']  # 从配置获取
        
        browser_info = browser_manager.start_browser(user_id)
        if not browser_info:
            return jsonify({'success': False, 'error': '浏览器启动失败'}), 500
        
        debug_port = browser_info.get('ws', {}).get('puppeteer')
        
        # 创建智能采集器
        scraper = IntelligentScraper(debug_port)
        
        # 初始化任务状态
        intelligent_scraping_tasks[task_id] = {
            'status': 'running',
            'collected_count': 0,
            'target_count': config.get('max_items', 50),
            'latest_data': [],
            'error': None,
            'scraper': scraper
        }
        
        # 在新线程中运行智能采集
        def run_intelligent_scraping():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # 执行智能采集
                collected_data = loop.run_until_complete(
                    scraper.intelligent_scrape(
                        analysis['page_info']['url'],
                        analysis,
                        config
                    )
                )
                
                # 更新任务状态
                intelligent_scraping_tasks[task_id].update({
                    'status': 'completed',
                    'collected_count': len(collected_data),
                    'latest_data': collected_data[-10:] if len(collected_data) > 10 else collected_data
                })
                
            except Exception as e:
                intelligent_scraping_tasks[task_id].update({
                    'status': 'failed',
                    'error': str(e)
                })
            finally:
                loop.close()
        
        # 启动采集线程
        scraping_thread = threading.Thread(target=run_intelligent_scraping)
        scraping_thread.start()
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': '智能采集已启动'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'启动智能采集失败: {str(e)}'}), 500

@app.route('/api/scraping-progress/<task_id>', methods=['GET'])
def api_get_scraping_progress(task_id):
    """获取智能采集进度API"""
    try:
        if task_id not in intelligent_scraping_tasks:
            return jsonify({'success': False, 'error': '任务不存在'}), 404
        
        task_info = intelligent_scraping_tasks[task_id]
        
        # 如果有新数据，模拟实时更新
        if task_info['status'] == 'running' and task_info['scraper']:
            # 这里可以从采集器获取实时进度
            # 暂时使用模拟数据
            pass
        
        return jsonify({
            'success': True,
            'data': {
                'status': task_info['status'],
                'collected_count': task_info['collected_count'],
                'target_count': task_info['target_count'],
                'latest_data': task_info['latest_data'],
                'error': task_info.get('error')
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'获取进度失败: {str(e)}'}), 500

@app.route('/api/start-optimized-scraping', methods=['POST'])
def api_start_optimized_scraping():
    """启动优化抓取API - 支持多窗口并发和实时数据保存"""
    try:
        data = request.get_json()
        target_accounts = data.get('target_accounts', [])
        target_keywords = data.get('target_keywords', [])
        max_tweets = data.get('max_tweets', 20)
        max_windows = data.get('max_windows', 2)
        
        if not target_accounts and not target_keywords:
            return jsonify({
                'success': False, 
                'error': '请至少提供一个目标账号或关键词'
            }), 400
        
        # 使用优化抓取器启动任务
        task_id = f"optimized_{int(datetime.now().timestamp())}"
        
        def run_optimized_scraping():
            try:
                with app.app_context():
                    # 创建任务记录
                    task = ScrapingTask(
                        name=f"优化抓取任务_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        target_accounts=json.dumps(target_accounts),
                        target_keywords=json.dumps(target_keywords),
                        max_tweets=max_tweets,
                        status='running',
                        started_at=datetime.utcnow()
                    )
                    db.session.add(task)
                    db.session.commit()
                    
                    # 启动优化抓取
                    results = optimized_scraper.scrape_multiple_accounts(
                        accounts=target_accounts,
                        keywords=target_keywords,
                        max_tweets_per_account=max_tweets,
                        max_windows=max_windows,
                        task_id=task.id
                    )
                    
                    # 更新任务状态
                    task.status = 'completed'
                    task.completed_at = datetime.utcnow()
                    task.result_count = len(results)
                    db.session.commit()
                    
                    print(f"✅ 优化抓取任务完成，共抓取 {len(results)} 条推文")
                    
            except Exception as e:
                print(f"❌ 优化抓取任务失败: {e}")
                with app.app_context():
                    task = ScrapingTask.query.filter_by(name__like=f"%{task_id}%").first()
                    if task:
                        task.status = 'failed'
                        task.error_message = str(e)
                        task.completed_at = datetime.utcnow()
                        db.session.commit()
        
        # 在后台线程中运行
        thread = threading.Thread(target=run_optimized_scraping)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': '优化抓取任务已启动',
            'task_id': task_id,
            'accounts': target_accounts,
            'keywords': target_keywords,
            'max_tweets': max_tweets,
            'max_windows': max_windows
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'启动优化抓取失败: {str(e)}'
        }), 500

@app.route('/api/start-enhanced-scraping', methods=['POST'])
def api_start_enhanced_scraping():
    """启动增强推文抓取API"""
    try:
        data = request.get_json()
        target_accounts = data.get('target_accounts', [])
        target_keywords = data.get('target_keywords', [])
        max_tweets = data.get('max_tweets', 20)
        enable_details = data.get('enable_details', True)
        task_name = data.get('task_name', f'增强抓取_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}')
        
        if not target_accounts and not target_keywords:
            return jsonify({'success': False, 'error': '请至少指定一个目标账号或关键词'}), 400
        
        # 生成任务ID
        task_id = f"enhanced_scraping_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # 使用用户输入的任务名称或默认名称
        if not task_name.strip():
            task_name = f'增强抓取_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}'
        
        # 初始化任务状态
        enhanced_scraping_tasks[task_id] = {
            'status': 'running',
            'collected_count': 0,
            'target_count': max_tweets,
            'details_scraped': 0,
            'latest_data': [],
            'error': None,
            'config': {
                'target_accounts': target_accounts,
                'target_keywords': target_keywords,
                'max_tweets': max_tweets,
                'enable_details': enable_details
            }
        }
        
        # 在新线程中运行增强抓取
        def run_enhanced_scraping():
            import time  # 确保time模块在函数内部可用
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # 启动浏览器
                browser_manager = AdsPowerLauncher(ADS_POWER_CONFIG)
                user_id = ADS_POWER_CONFIG['user_id']  # 从配置获取
                
                browser_info = browser_manager.start_browser(user_id)
                if not browser_info:
                    raise Exception('浏览器启动失败')
                
                debug_port = browser_info.get('ws', {}).get('puppeteer')
                
                # 创建增强Twitter解析器
                from enhanced_twitter_parser import EnhancedTwitterParser
                # from optimized_scraping_engine import OptimizedScrapingEngine
                
                # 创建抓取引擎
                # scraping_engine = OptimizedScrapingEngine(max_workers=4)
                # scraping_engine.start_engine()  # 启动抓取引擎
                
                # 创建增强解析器
                window_id = f"window_{user_id}_{int(time.time())}"
                parser = EnhancedTwitterParser(user_id, window_id)
                
                # 初始化解析器（连接到浏览器）
                loop.run_until_complete(parser.initialize_with_debug_port(debug_port))
                
                collected_tweets = []
                details_scraped = 0
                
                # 抓取用户推文
                for account in target_accounts:
                    if len(collected_tweets) >= max_tweets:
                        break
                    
                    try:
                        # 检测账号类型
                        account_type = detect_account_type(account)
                        
                        # 导航到用户页面并获取用户信息
                        loop.run_until_complete(parser.navigate_to_profile(account))
                        
                        # 使用增强抓取方法（每次滚动后立即抓取和保存）
                        user_tweets = loop.run_until_complete(
                            parser.enhanced_scrape_user_tweets(
                                username=account,
                                max_tweets=min(max_tweets - len(collected_tweets), 10),
                                enable_enhanced=enable_details
                            )
                        )
                        
                        # 对用户推文进行智能详情抓取
                        if enable_details:
                            enhanced_user_tweets = []
                            for tweet in user_tweets:
                                if (details_scraped < max_tweets // 2 and 
                                    tweet.get('link') and 
                                    parser.should_scrape_details(tweet, account_type)):
                                    
                                    try:
                                        details = loop.run_until_complete(
                                            parser.scrape_tweet_details(tweet['link'])
                                        )
                                        tweet.update(details)
                                        if tweet.get('has_detailed_content'):
                                            details_scraped += 1
                                    except Exception as e:
                                        tweet['detail_error'] = str(e)
                                
                                tweet['source'] = f'用户:{account}'
                                tweet['account_type'] = account_type
                                enhanced_user_tweets.append(tweet)
                            
                            collected_tweets.extend(enhanced_user_tweets)
                        else:
                            for tweet in user_tweets:
                                tweet['source'] = f'用户:{account}'
                                tweet['account_type'] = account_type
                            collected_tweets.extend(user_tweets)
                        
                        # 更新进度
                        enhanced_scraping_tasks[task_id].update({
                            'collected_count': len(collected_tweets),
                            'details_scraped': details_scraped,
                            'latest_data': collected_tweets[-5:] if len(collected_tweets) > 5 else collected_tweets
                        })
                        
                    except Exception as e:
                        continue
                
                # 抓取关键词推文
                for keyword in target_keywords:
                    if len(collected_tweets) >= max_tweets:
                        break
                    
                    try:
                        # 使用增强关键词抓取方法（每次滚动后立即抓取和保存）
                        keyword_tweets = loop.run_until_complete(
                            parser.enhanced_scrape_keyword_tweets(
                                keyword=keyword,
                                max_tweets=min(max_tweets - len(collected_tweets), 10),
                                enable_enhanced=enable_details
                            )
                        )
                        
                        # 对关键词推文进行详情抓取
                        if enable_details:
                            enhanced_keyword_tweets = []
                            for tweet in keyword_tweets:
                                if (details_scraped < max_tweets // 3 and 
                                    tweet.get('link') and 
                                    parser.should_scrape_details(tweet, 'general')):
                                    
                                    try:
                                        details = loop.run_until_complete(
                                            parser.scrape_tweet_details(tweet['link'])
                                        )
                                        tweet.update(details)
                                        if tweet.get('has_detailed_content'):
                                            details_scraped += 1
                                    except Exception as e:
                                        tweet['detail_error'] = str(e)
                                
                                tweet['source'] = f'关键词:{keyword}'
                                enhanced_keyword_tweets.append(tweet)
                            
                            collected_tweets.extend(enhanced_keyword_tweets)
                        else:
                            for tweet in keyword_tweets:
                                tweet['source'] = f'关键词:{keyword}'
                            collected_tweets.extend(keyword_tweets)
                        
                        # 更新进度
                        enhanced_scraping_tasks[task_id].update({
                            'collected_count': len(collected_tweets),
                            'details_scraped': details_scraped,
                            'latest_data': collected_tweets[-5:] if len(collected_tweets) > 5 else collected_tweets
                        })
                        
                    except Exception as e:
                        continue
                
                # 保存到数据库
                if collected_tweets:
                    # 创建新任务记录
                    task = ScrapingTask(
                        name=task_name,
                        target_accounts=json.dumps(target_accounts),
                        target_keywords=json.dumps(target_keywords),
                        max_tweets=max_tweets,
                        status='completed',
                        result_count=len(collected_tweets)
                    )
                    db.session.add(task)
                    db.session.commit()
                    
                    # 保存推文数据（支持异步插入）
                    saved_count = _save_tweets_to_db(collected_tweets, task.id, async_insert=True)
                    
                    enhanced_scraping_tasks[task_id].update({
                        'status': 'completed',
                        'task_db_id': task.id,
                        'saved_count': saved_count
                    })
                else:
                    enhanced_scraping_tasks[task_id]['status'] = 'completed'
                
                # 关闭解析器
                loop.run_until_complete(parser.close())
                
            except Exception as e:
                enhanced_scraping_tasks[task_id].update({
                    'status': 'failed',
                    'error': str(e)
                })
            finally:
                # 停止抓取引擎
                # try:
                #     scraping_engine.stop_engine()
                # except:
                #     pass
                loop.close()
        
        # 启动抓取线程
        scraping_thread = threading.Thread(target=run_enhanced_scraping)
        scraping_thread.start()
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': '增强推文抓取已启动'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'启动增强抓取失败: {str(e)}'}), 500

@app.route('/api/enhanced-scraping-progress/<task_id>', methods=['GET'])
def api_get_enhanced_scraping_progress(task_id):
    """获取增强推文抓取进度API"""
    try:
        if task_id not in enhanced_scraping_tasks:
            return jsonify({'success': False, 'error': '任务不存在'}), 404
        
        task_info = enhanced_scraping_tasks[task_id]
        
        return jsonify({
            'success': True,
            'data': {
                'status': task_info['status'],
                'collected_count': task_info['collected_count'],
                'target_count': task_info['target_count'],
                'details_scraped': task_info.get('details_scraped', 0),
                'latest_data': task_info['latest_data'],
                'error': task_info.get('error'),
                'config': task_info.get('config', {}),
                'task_db_id': task_info.get('task_db_id'),
                'saved_count': task_info.get('saved_count')
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'获取进度失败: {str(e)}'}), 500

# 博主管理相关API
@app.route('/api/influencers', methods=['GET'])
def api_get_influencers():
    """获取博主列表API"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        category = request.args.get('category')
        search = request.args.get('search')
        
        query = TwitterInfluencer.query
        
        # 分类筛选
        if category:
            query = query.filter(TwitterInfluencer.category == category)
        
        # 搜索筛选
        if search:
            query = query.filter(
                db.or_(
                    TwitterInfluencer.name.contains(search),
                    TwitterInfluencer.username.contains(search),
                    TwitterInfluencer.description.contains(search)
                )
            )
        
        # 分页
        pagination = query.order_by(TwitterInfluencer.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': {
                'influencers': [influencer.to_dict() for influencer in pagination.items],
                'total': pagination.total,
                'pages': pagination.pages,
                'current_page': page,
                'per_page': per_page
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'获取博主列表失败: {str(e)}'}), 500

@app.route('/api/influencers', methods=['POST'])
def api_add_influencer():
    """添加博主API"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['name', 'profile_url']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'缺少必填字段: {field}'}), 400
        
        profile_url = data['profile_url'].strip()
        
        # 从URL提取用户名
        username = ''
        if 'x.com/' in profile_url or 'twitter.com/' in profile_url:
            try:
                username = profile_url.split('/')[-1].split('?')[0]
                if username.startswith('@'):
                    username = username[1:]
            except:
                pass
        
        # 检查是否已存在
        existing = TwitterInfluencer.query.filter(
            db.or_(
                TwitterInfluencer.profile_url == profile_url,
                TwitterInfluencer.username == username
            )
        ).first()
        
        if existing:
            return jsonify({'success': False, 'error': '该博主已存在'}), 400
        
        # 创建新博主
        influencer = TwitterInfluencer(
            name=data['name'].strip(),
            username=username,
            profile_url=profile_url,
            description=data.get('description', '').strip(),
            category=data.get('category', '其他'),
            followers_count=data.get('followers_count', 0)
        )
        
        db.session.add(influencer)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': influencer.to_dict(),
            'message': '博主添加成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'添加博主失败: {str(e)}'}), 500

@app.route('/api/influencers/<int:influencer_id>', methods=['PUT'])
def api_update_influencer(influencer_id):
    """更新博主信息API"""
    try:
        influencer = TwitterInfluencer.query.get(influencer_id)
        if not influencer:
            return jsonify({'success': False, 'error': '博主不存在'}), 404
        
        data = request.get_json()
        
        # 更新字段
        if 'name' in data:
            influencer.name = data['name'].strip()
        if 'description' in data:
            influencer.description = data['description'].strip()
        if 'category' in data:
            influencer.category = data['category']
        if 'followers_count' in data:
            influencer.followers_count = data['followers_count']
        if 'is_active' in data:
            influencer.is_active = data['is_active']
        
        influencer.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': influencer.to_dict(),
            'message': '博主信息更新成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'更新博主失败: {str(e)}'}), 500

@app.route('/api/influencers/<int:influencer_id>', methods=['GET'])
def api_get_influencer(influencer_id):
    """获取单个博主信息API"""
    try:
        influencer = TwitterInfluencer.query.get(influencer_id)
        if not influencer:
            return jsonify({'success': False, 'error': '博主不存在'}), 404
        
        return jsonify({
            'success': True,
            'data': influencer.to_dict()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'获取博主失败: {str(e)}'}), 500

@app.route('/api/influencers/batch-scrape', methods=['POST'])
def api_batch_scrape_influencers():
    """批量抓取博主推文API"""
    try:
        data = request.get_json()
        influencer_ids = data.get('influencer_ids', [])
        
        if not influencer_ids:
            return jsonify({'success': False, 'error': '请选择要抓取的博主'}), 400
        
        # 验证博主是否存在
        influencers = TwitterInfluencer.query.filter(TwitterInfluencer.id.in_(influencer_ids)).all()
        if len(influencers) != len(influencer_ids):
            return jsonify({'success': False, 'error': '部分博主不存在'}), 400
        
        # 创建批量抓取任务
        task_name = f"批量抓取博主推文 - {len(influencers)}个博主"
        target_accounts = [inf.username for inf in influencers if inf.username]
        
        if not target_accounts:
            return jsonify({'success': False, 'error': '选中的博主没有有效的用户名'}), 400
        
        # 创建抓取任务
        task = ScrapingTask(
            name=task_name,
            target_accounts=json.dumps(target_accounts),
            target_keywords=json.dumps([]),
            max_tweets=data.get('max_tweets', 50),
            min_likes=data.get('min_likes', 0),
            min_retweets=data.get('min_retweets', 0),
            min_comments=data.get('min_comments', 0),
            status='pending'
        )
        
        db.session.add(task)
        db.session.commit()
        
        # 启动异步抓取任务
        def run_batch_scraping():
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(task_executor.execute_task(task.id))
                
                # 更新博主的最后抓取时间
                for influencer in influencers:
                    influencer.last_scraped = datetime.utcnow()
                db.session.commit()
                
            except Exception as e:
                pass
            finally:
                loop.close()
        
        # 启动抓取线程
        import threading
        scraping_thread = threading.Thread(target=run_batch_scraping)
        scraping_thread.start()
        
        return jsonify({
            'success': True,
            'task_id': task.id,
            'message': f'已启动批量抓取任务，将抓取 {len(influencers)} 个博主的推文'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'启动批量抓取失败: {str(e)}'}), 500

@app.route('/api/influencers/<int:influencer_id>', methods=['DELETE'])
def api_delete_influencer(influencer_id):
    """删除博主API"""
    try:
        influencer = TwitterInfluencer.query.get(influencer_id)
        if not influencer:
            return jsonify({'success': False, 'error': '博主不存在'}), 404
        
        db.session.delete(influencer)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '博主删除成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'删除博主失败: {str(e)}'}), 500

@app.route('/api/influencers/<int:influencer_id>/toggle-status', methods=['PATCH'])
def api_toggle_influencer_status(influencer_id):
    """切换博主状态API"""
    try:
        influencer = TwitterInfluencer.query.get(influencer_id)
        if not influencer:
            return jsonify({'success': False, 'error': '博主不存在'}), 404
        
        # 切换状态
        influencer.is_active = not influencer.is_active
        influencer.updated_at = datetime.utcnow()
        db.session.commit()
        
        status_text = '启用' if influencer.is_active else '禁用'
        
        return jsonify({
            'success': True,
            'data': influencer.to_dict(),
            'message': f'博主已{status_text}'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'切换状态失败: {str(e)}'}), 500

@app.route('/api/influencers/stats', methods=['GET'])
def api_get_influencer_stats():
    """获取博主统计数据API"""
    try:
        from datetime import datetime, timedelta
        import json
        
        # 从任务中提取所有使用过的博主
        all_tasks = ScrapingTask.query.all()
        task_influencers = set()
        
        for task in all_tasks:
            if task.target_accounts:
                try:
                    accounts = json.loads(task.target_accounts)
                    for account in accounts:
                        # 清理用户名，去除@符号
                        clean_username = account.lstrip('@') if account.startswith('@') else account
                        task_influencers.add(clean_username.lower())
                except:
                    continue
        
        # 总博主数（任务中使用的博主数量）
        total_influencers = len(task_influencers)
        
        # TwitterInfluencer表中的博主数
        managed_influencers = TwitterInfluencer.query.count()
        
        # 启用博主数（TwitterInfluencer表中启用的）
        active_influencers = TwitterInfluencer.query.filter(TwitterInfluencer.is_active == True).count()
        
        # 分类数量（有博主的分类）
        categories_with_influencers = db.session.query(TwitterInfluencer.category).filter(
            TwitterInfluencer.category.isnot(None)
        ).distinct().count()
        
        # 今日抓取数量（最近24小时内有任务的博主数）
        today_start = datetime.now() - timedelta(days=1)
        recent_tasks = ScrapingTask.query.filter(
            ScrapingTask.created_at >= today_start
        ).all()
        
        scraped_today = set()
        for task in recent_tasks:
            if task.target_accounts:
                try:
                    accounts = json.loads(task.target_accounts)
                    for account in accounts:
                        clean_username = account.lstrip('@') if account.startswith('@') else account
                        scraped_today.add(clean_username.lower())
                except:
                    continue
        
        return jsonify({
            'success': True,
            'data': {
                'total_influencers': total_influencers,  # 任务中使用的博主总数
                'active_influencers': active_influencers,  # 管理表中启用的博主数
                'managed_influencers': managed_influencers,  # 管理表中的博主总数
                'total_categories': categories_with_influencers,
                'scraped_today': len(scraped_today)  # 今日任务涉及的博主数
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'获取统计数据失败: {str(e)}'}), 500

@app.route('/api/influencers/categories', methods=['GET'])
def api_get_influencer_categories():
    """获取博主分类列表API"""
    try:
        categories = ['搞钱', '投放', '副业干货', '情绪类', '其他']
        
        # 统计每个分类的博主数量
        category_stats = []
        for category in categories:
            count = TwitterInfluencer.query.filter(TwitterInfluencer.category == category).count()
            category_stats.append({
                'name': category,
                'count': count
            })
        
        return jsonify({
            'success': True,
            'data': category_stats
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'获取分类失败: {str(e)}'}), 500

# 初始化数据库
def init_db():
    """初始化数据库"""
    with app.app_context():
        db.create_all()
        
        # 重置所有running状态的任务为pending状态
        # 这是为了解决系统重启后任务状态不一致的问题
        try:
            running_tasks = ScrapingTask.query.filter_by(status='running').all()
            if running_tasks:
                for task in running_tasks:
                    task.status = 'pending'
                db.session.commit()
        except Exception as e:
            print(f"⚠️ 重置任务状态失败: {e}")
        
        # 从数据库加载配置
        try:
            load_config_from_database()
        except Exception as e:
            print(f"⚠️ 配置加载失败: {e}，使用默认配置")
        
        # 初始化任务管理器（在配置加载后）
        try:
            init_task_manager()
        except Exception as e:
            print(f"⚠️ 任务管理器初始化失败: {e}")

@app.route('/debug-adspower')
def debug_adspower():
    """AdsPower调试页面"""
    with open('debug_adspower.html', 'r', encoding='utf-8') as f:
        return f.read()

# 系统管理API端点
@app.route('/api/backup-database', methods=['POST'])
def api_backup_database():
    """备份数据库API"""
    try:
        import shutil
        from datetime import datetime
        
        # 获取数据库文件路径
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        if not os.path.exists(db_path):
            return jsonify({'success': False, 'error': '数据库文件不存在'}), 404
        
        # 创建备份目录
        backup_dir = './backups'
        os.makedirs(backup_dir, exist_ok=True)
        
        # 生成备份文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'twitter_scraper_backup_{timestamp}.db'
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # 复制数据库文件
        shutil.copy2(db_path, backup_path)
        
        return jsonify({
            'success': True,
            'message': f'数据库备份成功，文件保存为: {backup_filename}',
            'backup_path': backup_path
        })
        
    except Exception as e:
        app.logger.error(f"数据库备份失败: {e}")
        return jsonify({'success': False, 'error': f'备份失败: {str(e)}'}), 500

@app.route('/api/clean-expired-data', methods=['POST'])
def api_clean_expired_data():
    """清理过期数据API"""
    try:
        from datetime import datetime, timedelta
        
        # 清理30天前的推文数据
        cutoff_date = datetime.now() - timedelta(days=30)
        expired_tweets = TweetData.query.filter(TweetData.scraped_at < cutoff_date).all()
        count = len(expired_tweets)
        
        for tweet in expired_tweets:
            db.session.delete(tweet)
        
        # 清理已完成的任务（保留最近7天）
        task_cutoff_date = datetime.now() - timedelta(days=7)
        expired_tasks = ScrapingTask.query.filter(
            ScrapingTask.status.in_(['completed', 'failed']),
            ScrapingTask.created_at < task_cutoff_date
        ).all()
        
        task_count = len(expired_tasks)
        for task in expired_tasks:
            db.session.delete(task)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'count': count + task_count,
            'message': f'清理完成：删除了 {count} 条推文数据和 {task_count} 个过期任务'
        })
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"清理过期数据失败: {e}")
        return jsonify({'success': False, 'error': f'清理失败: {str(e)}'}), 500

@app.route('/api/export-logs', methods=['GET'])
def api_export_logs():
    """导出日志API"""
    try:
        import zipfile
        from flask import send_file
        import tempfile
        
        # 创建临时zip文件
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        
        with zipfile.ZipFile(temp_file.name, 'w') as zipf:
            # 添加应用日志
            log_files = ['twitter_scraper.log', 'app.log']
            for log_file in log_files:
                if os.path.exists(log_file):
                    zipf.write(log_file, log_file)
            
            # 添加系统信息
            import sys
            import psutil
            system_info = f"""系统信息导出
时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Python版本: {sys.version}
内存使用: {psutil.virtual_memory().percent}%
磁盘使用: {psutil.disk_usage('/').percent}%
"""
            zipf.writestr('system_info.txt', system_info)
        
        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=f'twitter_scraper_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip',
            mimetype='application/zip'
        )
        
    except Exception as e:
        app.logger.error(f"导出日志失败: {e}")
        return jsonify({'success': False, 'error': f'导出失败: {str(e)}'}), 500

@app.route('/api/restart-system', methods=['POST'])
def api_restart_system():
    """重启系统API"""
    try:
        # 停止所有运行中的任务
        running_tasks = ScrapingTask.query.filter_by(status='running').all()
        for task in running_tasks:
            task.status = 'pending'
        db.session.commit()
        
        # 延迟重启，给前端时间显示消息
        def delayed_restart():
            import time
            time.sleep(3)
            os._exit(0)  # 强制退出，由进程管理器重启
        
        import threading
        restart_thread = threading.Thread(target=delayed_restart)
        restart_thread.start()
        
        return jsonify({
            'success': True,
            'message': '系统将在3秒后重启...'
        })
        
    except Exception as e:
        app.logger.error(f"重启系统失败: {e}")
        return jsonify({'success': False, 'error': f'重启失败: {str(e)}'}), 500

# 模块级别初始化已移除，避免Flask debug模式下的重复初始化

if __name__ == '__main__':
    # 记录应用启动时间
    import time
    app.start_time = time.time()
    
    # 初始化数据库
    init_db()
    
    # 初始化异步同步服务
    if FEISHU_CONFIG.get('async_enabled', False):
        print("🚀 [ASYNC_SYNC] 初始化异步飞书同步服务...")
        try:
            init_async_sync_service(
                max_workers_count=FEISHU_CONFIG.get('async_max_workers', 3),
                max_queue_size=FEISHU_CONFIG.get('async_max_queue_size', 100),
                max_retries=FEISHU_CONFIG.get('async_max_retries', 3)
            )
            print("✅ [ASYNC_SYNC] 异步飞书同步服务初始化完成")
        except Exception as e:
            print(f"❌ [ASYNC_SYNC] 异步飞书同步服务初始化失败: {e}")
    else:
        print("ℹ️ [ASYNC_SYNC] 异步飞书同步服务未启用")
    
    try:
        print("🚀 启动Flask Web应用...")
        print(f"📍 访问地址: http://localhost:8090")
        print(f"📍 访问地址: http://0.0.0.0:8090")
        # 启动Web应用（禁用debug模式避免闪退）
        app.run(debug=False, host='0.0.0.0', port=8090, threaded=True)
    finally:
        # 应用关闭时清理异步同步服务
        if FEISHU_CONFIG.get('async_enabled', False):
            print("🔄 [ASYNC_SYNC] 关闭异步飞书同步服务...")
            try:
                shutdown_async_sync_service()
                print("✅ [ASYNC_SYNC] 异步飞书同步服务已关闭")
            except Exception as e:
                print(f"❌ [ASYNC_SYNC] 关闭异步飞书同步服务失败: {e}")
'''
# 文件结束 - 所有代码已被注释掉，请使用 web_app_optimized.py