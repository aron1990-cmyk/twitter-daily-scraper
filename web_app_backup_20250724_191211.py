#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter抓取Web管理系统
提供Web界面进行关键词配置、任务管理和数据查看
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
    'enabled': False
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
from ads_browser_launcher import AdsPowerLauncher
from twitter_parser import TwitterParser
# from enhanced_twitter_parser import MultiWindowEnhancedScraper
# from optimized_scraping_engine import OptimizedScrapingEngine
from cloud_sync import CloudSyncManager
from excel_writer import ExcelWriter

# 创建Flask应用
app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'twitter-scraper-web-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///twitter_scraper.db'
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

# 减少werkzeug HTTP请求日志输出
logging.getLogger('werkzeug').setLevel(logging.WARNING)

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
        if 'adspower_api_status' in config_dict:
            ADS_POWER_CONFIG['api_status'] = config_dict['adspower_api_status']
        if 'adspower_api_key' in config_dict:
            ADS_POWER_CONFIG['api_key'] = config_dict['adspower_api_key']
        if 'adspower_user_id' in config_dict:
            ADS_POWER_CONFIG['user_id'] = config_dict['adspower_user_id']
        if 'adspower_group_id' in config_dict:
            ADS_POWER_CONFIG['group_id'] = config_dict['adspower_group_id']
        if 'adspower_multi_user_ids' in config_dict:
            multi_ids = config_dict['adspower_multi_user_ids']
            ADS_POWER_CONFIG['multi_user_ids'] = [uid.strip() for uid in multi_ids.split('\n') if uid.strip()] if multi_ids else []
            # 设置user_ids用于任务管理器
            if ADS_POWER_CONFIG['multi_user_ids']:
                ADS_POWER_CONFIG['user_ids'] = ADS_POWER_CONFIG['multi_user_ids']
            else:
                ADS_POWER_CONFIG['user_ids'] = [ADS_POWER_CONFIG['user_id']]
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
        
        print("✅ 配置已从数据库加载完成")
        
    except Exception as e:
        print(f"⚠️ 配置加载失败: {e}")

def init_database():
    """初始化数据库"""
    with app.app_context():
        db.create_all()
        
        # 重置所有running状态的任务为pending状态
        # 这是为了解决系统重启后任务状态不一致的问题
        running_tasks = ScrapingTask.query.filter_by(status='running').all()
        if running_tasks:
            for task in running_tasks:
                task.status = 'pending'
            db.session.commit()
        
        # 从数据库加载配置
        load_config_from_database()
        
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
        return {
            'id': self.id,
            'name': self.name,
            'target_accounts': json.loads(self.target_accounts or '[]'),
            'target_keywords': json.loads(self.target_keywords or '[]'),
            'max_tweets': self.max_tweets,
            'min_likes': self.min_likes,
            'min_retweets': self.min_retweets,
            'min_comments': self.min_comments,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'result_count': self.result_count,
            'error_message': self.error_message
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

# 并行任务管理器
class ParallelTaskManager:
    def __init__(self, max_concurrent_tasks=3):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.running_tasks = {}  # {task_id: {'executor': executor, 'thread': thread}}
        self.background_processes = {}  # {task_id: {'process': process, 'user_id': user_id}}
        self.task_queue = []  # 任务队列，存储等待执行的task_id
        # 从配置文件读取可用的AdsPower用户ID池
        # 配置已在文件开头定义，无需导入
        self.config = ADS_POWER_CONFIG
        self.available_user_ids = ADS_POWER_CONFIG.get('user_ids', [ADS_POWER_CONFIG['user_id']])
        self.user_id_pool = self.available_user_ids.copy()
        self.lock = threading.Lock()
        
        # 请求频率控制配置
        self.request_interval = ADS_POWER_CONFIG.get('request_interval', 2.0)
        self.user_rotation_enabled = ADS_POWER_CONFIG.get('user_rotation_enabled', True)
        self.user_switch_interval = ADS_POWER_CONFIG.get('user_switch_interval', 30)
        self.api_retry_delay = ADS_POWER_CONFIG.get('api_retry_delay', 5.0)
        
        # 用户轮询状态跟踪
        self.user_last_used = {}  # {user_id: timestamp}
        self.user_request_count = {}  # {user_id: count}
        self.current_user_index = 0
        
        # 确保max_concurrent_tasks不超过可用用户ID数量
        if self.max_concurrent_tasks > len(self.available_user_ids):
            self.max_concurrent_tasks = len(self.available_user_ids)
            
        print(f"[TaskManager] 初始化完成，支持 {len(self.available_user_ids)} 个用户ID，最大并发 {self.max_concurrent_tasks}")
        print(f"[TaskManager] 请求间隔: {self.request_interval}s，用户轮询: {self.user_rotation_enabled}")
    
    def get_available_user_id(self):
        """获取可用的用户ID（支持轮询机制）"""
        with self.lock:
            if not self.user_id_pool:
                return None
                
            if self.user_rotation_enabled:
                # 使用轮询机制选择用户ID
                return self._get_rotated_user_id()
            else:
                # 原有逻辑：简单弹出第一个
                return self.user_id_pool.pop(0)
    
    def _get_rotated_user_id(self):
        """轮询获取用户ID，避免频率限制"""
        import time
        current_time = time.time()
        
        # 寻找最适合的用户ID
        best_user_id = None
        best_score = -1
        
        for user_id in self.user_id_pool:
            # 计算用户ID的适用性得分
            last_used = self.user_last_used.get(user_id, 0)
            time_since_last_use = current_time - last_used
            request_count = self.user_request_count.get(user_id, 0)
            
            # 得分计算：时间间隔越长越好，请求次数越少越好
            score = time_since_last_use - (request_count * 10)
            
            # 如果距离上次使用时间超过切换间隔，优先选择
            if time_since_last_use >= self.user_switch_interval:
                score += 1000
            
            if score > best_score:
                best_score = score
                best_user_id = user_id
        
        if best_user_id:
            # 更新使用记录
            self.user_last_used[best_user_id] = current_time
            self.user_request_count[best_user_id] = self.user_request_count.get(best_user_id, 0) + 1
            
            # 从池中移除
            self.user_id_pool.remove(best_user_id)
            
            print(f"[TaskManager] 选择用户ID: {best_user_id}，得分: {best_score:.2f}")
            return best_user_id
        
        return None
    
    def return_user_id(self, user_id):
        """归还用户ID到池中（支持请求间隔控制）"""
        import time
        
        with self.lock:
            if user_id not in self.user_id_pool:
                # 如果启用了请求间隔控制，延迟归还
                if self.request_interval > 0:
                    # 记录归还时间，确保下次使用时有足够间隔
                    current_time = time.time()
                    self.user_last_used[user_id] = current_time
                    
                    print(f"[TaskManager] 归还用户ID: {user_id}，下次可用时间: {current_time + self.request_interval:.2f}")
                
                self.user_id_pool.append(user_id)
    
    def _wait_for_request_interval(self, user_id):
        """检查请求间隔时间（不阻塞）"""
        import time
        
        if self.request_interval <= 0:
            return True
            
        last_used = self.user_last_used.get(user_id, 0)
        current_time = time.time()
        time_since_last_use = current_time - last_used
        
        if time_since_last_use < self.request_interval:
            wait_time = self.request_interval - time_since_last_use
            print(f"[TaskManager] 用户ID {user_id} 需要等待 {wait_time:.2f}s 以避免频率限制")
            # 不在主线程中阻塞等待，而是返回False表示需要等待
            return False
        
        # 更新最后使用时间
        self.user_last_used[user_id] = current_time
        return True
    
    def can_start_task(self):
        """检查是否可以启动新任务"""
        total_running = len(self.running_tasks) + len(self.background_processes)
        return total_running < self.max_concurrent_tasks and len(self.user_id_pool) > 0
    
    def get_running_task_count(self):
        """获取正在运行的任务数量"""
        return len(self.running_tasks) + len(self.background_processes)
    
    def is_task_running(self, task_id):
        """检查特定任务是否正在运行"""
        return task_id in self.running_tasks or task_id in self.background_processes
    
    def start_task(self, task_id, use_background_process=True):
        """启动任务（支持请求频率控制和队列管理）"""
        result = None
        with self.lock:
            # 检查任务是否已在运行或队列中
            if self.is_task_running(task_id) or task_id in self.task_queue:
                return False, "任务已在运行或队列中"
            
            # 如果可以立即启动任务
            if self.can_start_task():
                return self._start_task_immediately(task_id, use_background_process)
            else:
                # 将任务加入队列
                result = self._add_task_to_queue(task_id)
        
        # 在锁外更新数据库状态
        if result and result[0]:  # 如果成功加入队列
            try:
                task = ScrapingTask.query.get(task_id)
                if task:
                    task.status = 'queued'
                    db.session.commit()
            except Exception as e:
                print(f"[TaskManager] 更新任务状态失败: {str(e)}")
        
        return result
    
    def _start_task_immediately(self, task_id, use_background_process=True):
        """立即启动任务"""
        # 先在锁外获取任务信息，避免在锁内进行数据库查询
        task = ScrapingTask.query.get(task_id)
        if not task:
            return False, f"任务 {task_id} 不存在"
        
        user_id = self.get_available_user_id()
        if not user_id:
            return False, "无可用的浏览器用户ID"
        
        try:
            # 检查请求间隔控制
            if not self._wait_for_request_interval(user_id):
                # 如果需要等待，归还用户ID并将任务加入队列
                self.return_user_id(user_id)
                return self._add_task_to_queue(task_id)
            
            print(f"[TaskManager] 启动任务 {task_id}，使用用户ID: {user_id}")
            
            if use_background_process:
                return self._start_background_task(task_id, user_id, task)
            else:
                return self._start_thread_task(task_id, user_id)
                
        except Exception as e:
            self.return_user_id(user_id)
            return False, f"任务启动失败: {str(e)}"
    
    def _add_task_to_queue(self, task_id):
        """将任务加入队列"""
        if task_id not in self.task_queue:
            self.task_queue.append(task_id)
            print(f"[TaskManager] 任务 {task_id} 已加入队列，当前队列长度: {len(self.task_queue)}")
            return True, "任务窗口已满，当前任务进入排队队列，等待执行"
        return False, "任务已在队列中"
    
    def _start_background_task(self, task_id, user_id, task=None):
        """在后台进程中启动任务"""
        try:
            print(f"[TaskManager] 开始启动后台任务 {task_id}，用户ID: {user_id}")
            
            # 如果没有传入task对象，则查询数据库
            if task is None:
                task = ScrapingTask.query.get(task_id)
                if not task:
                    raise Exception(f"任务 {task_id} 不存在")
            
            print(f"[TaskManager] 任务信息获取成功: {task.name}")
            
            # 创建任务配置文件
            config_data = {
                'task_id': task_id,
                'task_type': 'daily',  # 默认类型
                'kwargs': {
                    'user_id': user_id
                }
            }
            
            # 创建临时配置文件
            config_file = tempfile.NamedTemporaryFile(
                mode='w', 
                suffix='.json', 
                delete=False,
                encoding='utf-8'
            )
            json.dump(config_data, config_file, ensure_ascii=False, indent=2)
            config_file.close()
            
            print(f"[TaskManager] 配置文件已创建: {config_file.name}")
            
            # 启动后台进程 - 不重定向输出，让日志直接显示在终端
            cmd = ['python3', 'background_task_runner.py', config_file.name]
            print(f"[TaskManager] 启动命令: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                cwd=os.path.dirname(os.path.abspath(__file__)),
                # 移除stdout和stderr重定向，让输出直接显示
                # stdout=subprocess.PIPE,
                # stderr=subprocess.PIPE,
                text=True
            )
            
            print(f"[TaskManager] 后台进程已启动，PID: {process.pid}")
            
            # 记录后台进程
            self.background_processes[task_id] = {
                'process': process,
                'user_id': user_id,
                'config_file': config_file.name,
                'start_time': datetime.utcnow()
            }
            
            print(f"[TaskManager] 后台任务 {task_id} 启动成功")
            return True, "后台任务启动成功"
            
        except Exception as e:
            print(f"[TaskManager] 后台任务启动失败: {str(e)}")
            raise Exception(f"后台任务启动失败: {str(e)}")
    
    def _start_thread_task(self, task_id, user_id):
        """在线程中启动任务（原有方式）"""
        try:
            # 创建任务执行器
            executor = ScrapingTaskExecutor(user_id)
            
            # 在新线程中运行任务
            def run_task():
                try:
                    with app.app_context():
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(executor.execute_task(task_id))
                        loop.close()
                finally:
                    # 任务完成后清理
                    self.cleanup_task(task_id, user_id)
            
            task_thread = threading.Thread(target=run_task)
            task_thread.start()
            
            # 记录运行中的任务
            self.running_tasks[task_id] = {
                'executor': executor,
                'thread': task_thread,
                'user_id': user_id,
                'start_time': datetime.utcnow()
            }
            
            return True, "任务启动成功"
            
        except Exception as e:
            raise Exception(f"线程任务启动失败: {str(e)}")
    
    def stop_task(self, task_id):
        """停止特定任务"""
        if task_id not in self.running_tasks and task_id not in self.background_processes:
            return False, "任务未在运行中"
        
        try:
            # 停止后台进程任务
            if task_id in self.background_processes:
                process_info = self.background_processes[task_id]
                process = process_info['process']
                user_id = process_info['user_id']
                config_file = process_info.get('config_file')
                
                # 终止进程
                process.terminate()
                try:
                    process.wait(timeout=5)  # 等待5秒
                except subprocess.TimeoutExpired:
                    process.kill()  # 强制杀死进程
                
                # 清理配置文件
                if config_file and os.path.exists(config_file):
                    try:
                        os.unlink(config_file)
                    except:
                        pass
                
                # 清理任务
                self.cleanup_background_task(task_id, user_id)
                
                return True, "后台任务已停止"
            
            # 停止线程任务
            elif task_id in self.running_tasks:
                task_info = self.running_tasks[task_id]
                executor = task_info['executor']
                user_id = task_info['user_id']
                
                # 停止执行器
                executor.stop_task()
                
                # 清理任务
                self.cleanup_task(task_id, user_id)
                
                return True, "任务已停止"
            
        except Exception as e:
            return False, f"停止任务失败: {str(e)}"
    
    def cleanup_task(self, task_id, user_id):
        """清理已完成的线程任务"""
        with self.lock:
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
            self.return_user_id(user_id)
            # 处理队列中的下一个任务
            self._process_next_task_in_queue()
    
    def cleanup_background_task(self, task_id, user_id):
        """清理已完成的后台进程任务"""
        with self.lock:
            if task_id in self.background_processes:
                del self.background_processes[task_id]
            self.return_user_id(user_id)
            # 处理队列中的下一个任务
            self._process_next_task_in_queue()
    
    def get_task_status(self):
        """获取所有任务状态"""
        total_running = len(self.running_tasks) + len(self.background_processes)
        status = {
            'running_count': total_running,
            'thread_tasks': len(self.running_tasks),
            'background_tasks': len(self.background_processes),
            'max_concurrent': self.max_concurrent_tasks,
            'available_slots': self.max_concurrent_tasks - total_running,
            'available_browsers': len(self.user_id_pool),
            'running_tasks': list(self.running_tasks.keys()),
            'background_task_ids': list(self.background_processes.keys()),
            'queued_tasks': len(self.task_queue)
        }
        return status
    
    def _process_next_task_in_queue(self):
        """处理队列中的下一个任务"""
        if not self.task_queue:
            return
        
        # 检查是否有可用槽位
        if not self.can_start_task():
            return
        
        # 获取队列中的下一个任务
        next_task_id = self.task_queue.pop(0)
        
        # 获取任务信息
        task = ScrapingTask.query.get(next_task_id)
        if not task:
            return
        
        # 更新任务状态为pending
        task.status = 'pending'
        db.session.commit()
        
        # 启动任务
        try:
            self._start_task_immediately(next_task_id, task.name, task.target_username, task.use_background_process)
        except Exception as e:
            print(f"启动队列任务失败: {e}")
            task.status = 'failed'
            db.session.commit()
    
    def get_queue_status(self):
        """获取队列状态"""
        with self.lock:
            return {
                'queue_length': len(self.task_queue),
                'queued_task_ids': self.task_queue.copy()
            }
    
    def clear_queue(self):
        """清空队列"""
        with self.lock:
            # 将队列中的任务状态重置为pending
            for task_id in self.task_queue:
                task = ScrapingTask.query.get(task_id)
                if task and task.status == 'queued':
                    task.status = 'pending'
            db.session.commit()
            self.task_queue.clear()

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
                    
                    for keyword in target_keywords:
                        if not self.is_running:
                            break
                        
                        try:
                            print(f"[DEBUG] 在博主 @{account} 下搜索关键词 '{keyword}'")
                            tweets = await parser.scrape_user_keyword_tweets(
                                username=account, 
                                keyword=keyword, 
                                max_tweets=task.max_tweets,
                                enable_enhanced=True
                            )
                            
                            # 过滤推文
                            filtered_tweets = self._filter_tweets(tweets, task)
                            all_tweets.extend(filtered_tweets)
                            
                            print(f"[DEBUG] 在博主 @{account} 下搜索关键词 '{keyword}' 完成，获得 {len(filtered_tweets)} 条有效推文")
                            
                        except Exception as e:
                            print(f"在博主 @{account} 下搜索关键词 '{keyword}' 失败: {e}")
                            continue
            else:
                # 分别抓取账号推文和关键词推文（原有逻辑）
                
                # 抓取账号推文
                for account in target_accounts:
                    if not self.is_running:  # 检查是否被停止
                        break
                        
                    try:
                        print(f"[DEBUG] 抓取博主 @{account} 的推文")
                        tweets = await parser.scrape_user_tweets(username=account, max_tweets=task.max_tweets, enable_enhanced=True)
                        
                        # 过滤推文
                        filtered_tweets = self._filter_tweets(tweets, task)
                        all_tweets.extend(filtered_tweets)
                        
                        print(f"[DEBUG] 博主 @{account} 抓取完成，获得 {len(filtered_tweets)} 条有效推文")
                        
                    except Exception as e:
                        print(f"抓取账号 {account} 失败: {e}")
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
    
    def _save_tweets_to_db(self, tweets: List[Dict], task_id: int) -> int:
        """保存推文到数据库"""
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
        """检查是否需要自动同步到飞书"""
        try:
            print(f"[调试] 开始检查任务 {task_id} 的自动同步...")
            
            # 检查飞书配置是否启用
            if not FEISHU_CONFIG.get('enabled'):
                print(f"[调试] 飞书配置未启用，跳过同步")
                return
            
            # 检查是否启用自动同步
            auto_sync_config = SystemConfig.query.filter_by(key='feishu_auto_sync').first()
            if not auto_sync_config or auto_sync_config.value.lower() not in ['true', '1']:
                print(f"[调试] 自动同步未启用，跳过同步 (当前值: {auto_sync_config.value if auto_sync_config else 'None'})")
                return
            
            # 检查飞书配置完整性
            required_fields = ['app_id', 'app_secret', 'spreadsheet_token', 'table_id']
            missing_fields = [field for field in required_fields if not FEISHU_CONFIG.get(field)]
            if missing_fields:
                print(f"飞书自动同步跳过：配置不完整，缺少字段: {', '.join(missing_fields)}")
                return
            
            print(f"开始自动同步任务 {task_id} 的数据到飞书...")
            
            # 获取任务数据
            tweets = TweetData.query.filter_by(task_id=task_id).all()
            if not tweets:
                print("没有数据需要同步")
                return
            
            # 准备同步数据
            sync_data = []
            for tweet in tweets:
                # 解析hashtags
                try:
                    hashtags = json.loads(tweet.hashtags) if tweet.hashtags else []
                except:
                    hashtags = []
                
                # 转换发布时间为毫秒时间戳
                publish_timestamp = ''
                if tweet.publish_time:
                    try:
                        if isinstance(tweet.publish_time, str):
                            dt = datetime.fromisoformat(tweet.publish_time.replace('Z', '+00:00'))
                        else:
                            dt = tweet.publish_time
                        publish_timestamp = str(int(dt.timestamp() * 1000))
                    except:
                        publish_timestamp = ''
                
                # 转换创建时间为毫秒时间戳
                created_timestamp = ''
                if tweet.scraped_at:
                    try:
                        created_timestamp = str(int(tweet.scraped_at.timestamp() * 1000))
                    except:
                        created_timestamp = ''
                
                sync_data.append({
                    '推文原文内容': tweet.content or '',
                    '发布时间': publish_timestamp,
                    '作者（账号）': tweet.username or '',
                    '推文链接': tweet.link or '',
                    '话题标签（Hashtag）': ', '.join(hashtags),
                    '类型标签': tweet.content_type or '',
                    '收藏数': tweet.likes or 0,
                    '点赞数': tweet.likes or 0,
                    '转发数': tweet.retweets or 0,
                    '创建时间': created_timestamp
                })
            
            # 创建云同步管理器并同步
            from cloud_sync import CloudSyncManager
            sync_manager = CloudSyncManager()
            
            # 设置飞书配置
            if sync_manager.setup_feishu(FEISHU_CONFIG['app_id'], FEISHU_CONFIG['app_secret']):
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
                    print(f"任务 {task_id} 自动同步到飞书成功，已更新 {len(tweets)} 条记录的同步状态")
                else:
                    print(f"任务 {task_id} 自动同步到飞书失败")
            else:
                print(f"任务 {task_id} 自动同步失败：飞书配置设置失败")
                
        except Exception as e:
            print(f"自动同步到飞书时发生错误: {e}")
    
    def stop_task(self):
        """停止当前任务"""
        self.is_running = False

# 全局并行任务管理器（将在配置加载后初始化）
task_manager = None
optimized_scraper = None

def init_task_manager():
    """初始化任务管理器"""
    global task_manager, optimized_scraper
    
    # 检查是否已经初始化，避免重复初始化
    if task_manager is not None:
        print("⚠️ TaskManager已经初始化，跳过重复初始化")
        return
    
    max_concurrent = ADS_POWER_CONFIG.get('max_concurrent_tasks', 2)
    task_manager = ParallelTaskManager(max_concurrent_tasks=max_concurrent)
    
    # 初始化优化抓取器
    # optimized_scraper = MultiWindowEnhancedScraper(max_workers=max_concurrent)
    
    print(f"✅ TaskManager已初始化，最大并发任务数: {max_concurrent}")
    print(f"✅ OptimizedScraper已初始化，支持多窗口并发抓取")

# 在模块加载时初始化
try:
    init_database()
except Exception as e:
    print(f"⚠️ 初始化失败: {e}")

# 路由定义
@app.route('/')
def index():
    """首页"""
    from datetime import datetime, date
    
    # 计算统计数据
    today = date.today()
    stats = {
        'total_tasks': ScrapingTask.query.count(),
        'total_tweets': TweetData.query.count(),
        'running_tasks': ScrapingTask.query.filter_by(status='running').count(),
        'completed_tasks': ScrapingTask.query.filter_by(status='completed').count(),
        'today_tweets': TweetData.query.filter(db.func.date(TweetData.scraped_at) == today).count()
    }
    
    # 获取最近的任务
    recent_tasks = ScrapingTask.query.order_by(ScrapingTask.created_at.desc()).limit(5).all()
    
    return render_template('index.html', stats=stats, recent_tasks=recent_tasks)

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
    
    return render_template('tasks.html', tasks=tasks, task_stats=task_stats)

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
    
    return render_template('data.html', 
                         tweets=tweets.items, 
                         pagination=tweets, 
                         data_stats=data_stats, 
                         tasks=tasks)

@app.route('/config')
def config():
    """配置页面"""
    # 获取当前配置
    config_data = {}
    
    # 从数据库获取配置
    configs = SystemConfig.query.all()
    for cfg in configs:
        config_data[cfg.key] = cfg.value
    
    # 处理AdsPower API地址的向后兼容性
    if 'adspower_api_url' in config_data and ('adspower_api_host' not in config_data or 'adspower_api_port' not in config_data):
        # 从完整URL中解析主机和端口
        api_url = config_data['adspower_api_url']
        if api_url.startswith('http://'):
            url_parts = api_url.replace('http://', '').split(':')
            if len(url_parts) == 2:
                config_data['adspower_api_host'] = url_parts[0]
                config_data['adspower_api_port'] = url_parts[1]
            else:
                config_data['adspower_api_host'] = 'localhost'
                config_data['adspower_api_port'] = '50325'
    
    # 设置默认值
    if 'adspower_api_host' not in config_data:
        config_data['adspower_api_host'] = 'localhost'
    if 'adspower_api_port' not in config_data:
        config_data['adspower_api_port'] = '50325'
    
    # 处理导出字段配置
    if 'export_fields' in config_data:
        config_data['export_fields'] = config_data['export_fields'].split(',') if config_data['export_fields'] else []
    else:
        config_data['export_fields'] = ['content', 'username', 'created_at', 'likes_count', 'retweets_count', 'hashtags']
    
    return render_template('config.html', config=config_data)

@app.route('/update_config', methods=['POST'])
def update_config():
    """更新配置"""
    try:
        config_type = request.form.get('config_type')
        
        if config_type == 'adspower':
            # 处理AdsPower配置
            api_host = request.form.get('adspower_api_host', 'local.adspower.net')
            api_port = request.form.get('adspower_api_port', '50325')
            api_url = f'http://{api_host}:{api_port}'
            
            adspower_configs = {
                'adspower_api_host': api_host,
                'adspower_api_port': api_port,
                'adspower_api_url': api_url,  # 保持向后兼容
                'adspower_api_status': request.form.get('adspower_api_status', ''),
                'adspower_api_key': request.form.get('adspower_api_key', ''),
                'adspower_user_id': request.form.get('adspower_user_id', ''),
                'adspower_multi_user_ids': request.form.get('adspower_multi_user_ids', ''),
                'max_concurrent_tasks': request.form.get('max_concurrent_tasks', '2'),
                'task_timeout': request.form.get('task_timeout', '900'),
                'browser_startup_delay': request.form.get('browser_startup_delay', '2'),
                'request_interval': request.form.get('request_interval', '2.0'),
                'user_switch_interval': request.form.get('user_switch_interval', '30'),
                'adspower_headless': 'adspower_headless' in request.form,
                'adspower_health_check': 'adspower_health_check' in request.form,
                'user_rotation_enabled': 'user_rotation_enabled' in request.form
            }
            
            # 更新或创建配置记录
            for key, value in adspower_configs.items():
                config = SystemConfig.query.filter_by(key=key).first()
                if config:
                    config.value = str(value)
                    config.updated_at = datetime.utcnow()
                else:
                    config = SystemConfig(
                        key=key,
                        value=str(value),
                        description=f'AdsPower配置: {key}'
                    )
                    db.session.add(config)
            
            # 更新全局配置（用于当前会话）
            global ADS_POWER_CONFIG
            ADS_POWER_CONFIG.update({
                'local_api_url': adspower_configs['adspower_api_url'],
                'user_id': adspower_configs['adspower_user_id'],
                'multi_user_ids': [uid.strip() for uid in adspower_configs['adspower_multi_user_ids'].split('\n') if uid.strip()],
                'max_concurrent_tasks': int(adspower_configs['max_concurrent_tasks']),
                'task_timeout': int(adspower_configs['task_timeout']),
                'browser_startup_delay': float(adspower_configs['browser_startup_delay']),
                'request_interval': float(adspower_configs['request_interval']),
                'user_switch_interval': int(adspower_configs['user_switch_interval']),
                'user_rotation_enabled': adspower_configs['user_rotation_enabled'],
                'headless': adspower_configs['adspower_headless'],
                'health_check': adspower_configs['adspower_health_check']
            })
            
            # 更新任务管理器的配置
            if hasattr(task_manager, 'max_concurrent_tasks'):
                task_manager.max_concurrent_tasks = int(adspower_configs['max_concurrent_tasks'])
            if hasattr(task_manager, 'user_id_pool'):
                task_manager.user_id_pool = [uid.strip() for uid in adspower_configs['adspower_multi_user_ids'].split('\n') if uid.strip()]
            if hasattr(task_manager, 'request_interval'):
                task_manager.request_interval = float(adspower_configs['request_interval'])
            if hasattr(task_manager, 'user_switch_interval'):
                task_manager.user_switch_interval = int(adspower_configs['user_switch_interval'])
            if hasattr(task_manager, 'user_rotation_enabled'):
                task_manager.user_rotation_enabled = adspower_configs['user_rotation_enabled']
            
            db.session.commit()
            flash('AdsPower配置已更新', 'success')
            
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
                'feishu_auto_sync': 'feishu_auto_sync' in request.form,
                'sync_interval': request.form.get('sync_interval', '24')
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
                'enabled': feishu_configs['feishu_enabled']
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
    return render_template('influencers.html')

@app.route('/sync_feishu', methods=['POST'])
def sync_feishu():
    """同步数据到飞书（支持全部同步或按任务ID同步）"""
    try:
        # 获取请求参数
        data = request.form.to_dict()
        task_id = data.get('task_id')
        
        # 检查飞书配置
        feishu_config = SystemConfig.query.filter_by(key='feishu_config').first()
        if not feishu_config or not feishu_config.value:
            return jsonify({'success': False, 'message': '飞书配置未设置'}), 400
        
        config = json.loads(feishu_config.value)
        required_fields = ['app_id', 'app_secret', 'app_token', 'table_id']
        if not all(config.get(field) for field in required_fields):
            return jsonify({'success': False, 'message': '飞书配置不完整'}), 400
        
        # 构建查询
        query = TweetData.query
        if task_id:
            query = query.filter(TweetData.task_id == task_id)
        
        # 获取未同步的推文数据
        tweets = query.filter(TweetData.synced_to_feishu != True).all()
        
        if not tweets:
            message = f'任务 {task_id} 没有需要同步的数据' if task_id else '没有需要同步的数据'
            return jsonify({'success': True, 'message': message})
        
        # 初始化同步管理器
        sync_manager = CloudSyncManager()
        sync_manager.set_feishu_config(
            app_id=config['app_id'],
            app_secret=config['app_secret'],
            app_token=config['app_token'],
            table_id=config['table_id']
        )
        
        # 格式化数据并同步
        formatted_data = []
        for tweet in tweets:
            # 使用修复后的格式化函数
            from enhanced_tweet_scraper import format_tweets_for_feishu
            tweet_dict = {
                'content': tweet.content,
                'username': tweet.username,
                'tweet_url': tweet.tweet_url,
                'hashtags': tweet.hashtags,
                'likes': tweet.likes,
                'retweets': tweet.retweets,
                'replies': tweet.replies,
                'scraped_at': tweet.scraped_at
            }
            
            # 格式化单条推文数据
            formatted_tweet = format_tweets_for_feishu([tweet_dict])[0]
            formatted_data.append(formatted_tweet)
        
        # 同步到飞书
        success = sync_manager.sync_to_feishu(formatted_data)
        
        if success:
            # 更新同步状态
            for tweet in tweets:
                tweet.synced_to_feishu = True
            db.session.commit()
            
            message = f'成功同步 {len(tweets)} 条数据到飞书'
            if task_id:
                message += f'（任务 {task_id}）'
            
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': '同步到飞书失败'}), 500
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'同步失败: {str(e)}'}), 500

# API路由
@app.route('/api/tasks', methods=['GET'])
def api_get_tasks():
    """获取任务列表"""
    tasks = ScrapingTask.query.order_by(ScrapingTask.created_at.desc()).all()
    return jsonify([task.to_dict() for task in tasks])

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
        
        return jsonify({'success': True, 'task_id': task.id})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/tasks/<int:task_id>/start', methods=['POST'])
def api_start_task(task_id):
    """启动任务"""
    app.logger.info(f"收到启动任务请求: task_id={task_id}")
    
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
        
        if status['running_count'] >= status['max_concurrent']:
            error_msg = f'已达到最大并发任务数限制({status["max_concurrent"]})，当前运行任务数: {status["running_count"]}'
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
        task_status = task_manager.get_task_status()
        
        return jsonify({
            'success': True,
            'data': {
                'queue_length': queue_status['queue_length'],
                'queued_task_ids': queue_status['queued_task_ids'],
                'available_slots': task_status['available_slots'],
                'is_queue_full': task_status['available_slots'] <= 0
            }
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

@app.route('/api/data/export')
def api_export_data():
    """导出数据为Excel文件"""
    try:
        from datetime import datetime
        import io
        import pandas as pd
        from flask import send_file
        
        # 获取筛选参数
        search = request.args.get('search', '')
        task_id = request.args.get('task_id', type=int)
        min_likes = request.args.get('min_likes', type=int)
        min_retweets = request.args.get('min_retweets', type=int)
        
        # 构建查询（与data页面相同的筛选逻辑）
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
        
        # 按抓取时间排序
        tweets = query.order_by(TweetData.scraped_at.desc()).all()
        
        if not tweets:
            return jsonify({'success': False, 'error': '没有数据可导出'}), 400
        
        # 获取导出配置
        export_fields_config = SystemConfig.query.filter_by(key='export_fields').first()
        if export_fields_config and export_fields_config.value:
            selected_fields = export_fields_config.value.split(',')
        else:
            # 默认导出字段
            selected_fields = ['content', 'username', 'created_at', 'likes_count', 'retweets_count', 'hashtags']
        
        # 准备导出数据
        export_data = []
        for tweet in tweets:
            row = {}
            if 'content' in selected_fields:
                row['推文内容'] = tweet.content
            if 'username' in selected_fields:
                row['用户名'] = tweet.username
            if 'created_at' in selected_fields:
                row['发布时间'] = tweet.created_at.strftime('%Y-%m-%d %H:%M:%S') if tweet.created_at else ''
            if 'likes_count' in selected_fields:
                row['点赞数'] = tweet.likes_count or 0
            if 'retweets_count' in selected_fields:
                row['转发数'] = tweet.retweets_count or 0
            if 'hashtags' in selected_fields:
                row['话题标签'] = tweet.hashtags or ''
            
            # 添加其他字段
            row['抓取时间'] = tweet.scraped_at.strftime('%Y-%m-%d %H:%M:%S')
            if tweet.task:
                row['任务名称'] = tweet.task.name
            
            export_data.append(row)
        
        # 创建Excel文件
        df = pd.DataFrame(export_data)
        
        # 生成文件名
        filename_template = SystemConfig.query.filter_by(key='export_filename_template').first()
        if filename_template and filename_template.value:
            filename = filename_template.value.format(
                date=datetime.now().strftime('%Y%m%d'),
                time=datetime.now().strftime('%H%M%S'),
                task_name='all_data'
            )
        else:
            filename = f'twitter_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        
        # 创建内存中的Excel文件
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='推文数据', index=False)
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'{filename}.xlsx'
        )
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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
    """同步数据到飞书多维表格"""
    try:
        # 检查飞书配置
        if not FEISHU_CONFIG.get('enabled'):
            return jsonify({'success': False, 'error': '飞书同步未启用'}), 400
        
        # 检查飞书配置完整性
        required_fields = ['app_id', 'app_secret', 'spreadsheet_token', 'table_id']
        missing_fields = [field for field in required_fields if not FEISHU_CONFIG.get(field)]
        if missing_fields:
            return jsonify({
                'success': False, 
                'error': f'飞书配置不完整，缺少字段: {", ".join(missing_fields)}'
            }), 400
        
        # 获取任务数据
        tweets = TweetData.query.filter_by(task_id=task_id).all()
        
        if not tweets:
            return jsonify({'success': False, 'error': '没有数据需要同步'}), 400
        
        # 初始化云同步管理器
        sync_config = {
            'feishu': {
                'enabled': True,
                'app_id': FEISHU_CONFIG['app_id'],
                'app_secret': FEISHU_CONFIG['app_secret'],
                'spreadsheet_token': FEISHU_CONFIG['spreadsheet_token'],
                'table_id': FEISHU_CONFIG['table_id']
            }
        }
        sync_manager = CloudSyncManager(sync_config)
        
        # 准备数据，按照飞书多维表格字段映射
        data = []
        for tweet in tweets:
            # 使用用户设置的类型标签，如果为空则使用自动分类
            content_type = tweet.content_type or classify_content_type(tweet.content)
            
            # 处理发布时间
            publish_time = ''
            if tweet.publish_time:
                try:
                    if isinstance(tweet.publish_time, str):
                        # 如果是字符串，尝试解析为datetime
                        from dateutil import parser
                        dt = parser.parse(tweet.publish_time)
                        publish_time = int(dt.timestamp() * 1000)
                    else:
                        # 如果已经是datetime对象
                        publish_time = int(tweet.publish_time.timestamp() * 1000)
                except:
                    publish_time = ''
            
            data.append({
                '推文原文内容': tweet.content,
                '发布时间': publish_time,
                '作者（账号）': tweet.username,
                '推文链接': tweet.link or '',
                '话题标签': ', '.join(json.loads(tweet.hashtags or '[]')),
                '类型标签': content_type,
                '收藏数': 0,  # Twitter API限制，暂时设为0
                '点赞数': tweet.likes,
                '转发数': tweet.retweets,
                '创建时间': int(tweet.scraped_at.timestamp() * 1000)
            })
        
        # 同步到飞书多维表格
        success = sync_manager.sync_to_feishu(
            data,
            FEISHU_CONFIG['spreadsheet_token'],
            FEISHU_CONFIG['table_id']
        )
        
        if success:
            # 更新同步状态和内容类型
            for i, tweet in enumerate(tweets):
                tweet.synced_to_feishu = True
                tweet.content_type = classify_content_type(tweet.content)
            db.session.commit()
            
            return jsonify({'success': True, 'message': f'成功同步 {len(data)} 条数据到飞书多维表格'})
        else:
            return jsonify({'success': False, 'error': '飞书同步失败'}), 500
            
    except Exception as e:
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
        'spreadsheet_token': FEISHU_CONFIG['spreadsheet_token'],
        'table_id': FEISHU_CONFIG['table_id'],
        'enabled': FEISHU_CONFIG['enabled']
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
            'auto_sync': feishu_configs['feishu_auto_sync'].lower() == 'true'
        })
        
        return jsonify({'success': True, 'message': '飞书配置更新成功'})
        
    except Exception as e:
        db.session.rollback()
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
        app.logger.debug('Starting api_test_open_adspower')
        data = request.form.to_dict()
        
        # 从数据库获取配置信息
        configs = SystemConfig.query.all()
        config_dict = {cfg.key: cfg.value for cfg in configs}
        
        # 获取API配置信息
        api_host = data.get('api_host') or config_dict.get('adspower_api_host', 'localhost')
        api_port = data.get('api_port') or config_dict.get('adspower_api_port', '50325')
        api_status = config_dict.get('adspower_api_status', '')
        api_key = config_dict.get('adspower_api_key', '')
        
        # 如果API状态为关闭，直接返回失败
        if api_status == '关闭':
            return jsonify({
                'success': False,
                'message': 'AdsPower API接口状态已设置为关闭'
            })
        
        # 构建API URL
        api_url = f'http://{api_host}:{api_port}'
        test_url = f"{api_url}/api/v1/user/list"
        
        # 准备请求头
        headers = {}
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        
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
    """测试AdsPower连接"""
    try:
        data = request.get_json() or {}
        
        # 从数据库获取配置信息
        configs = SystemConfig.query.all()
        config_dict = {cfg.key: cfg.value for cfg in configs}
        
        # 获取API配置信息
        api_host = data.get('api_host') or config_dict.get('adspower_api_host', 'localhost')
        api_port = data.get('api_port') or config_dict.get('adspower_api_port', '50325')
        api_status = config_dict.get('adspower_api_status', '')
        api_key = config_dict.get('adspower_api_key', '')
        user_id = data.get('user_id') or config_dict.get('adspower_user_id', '')
        
        if not user_id:
            return jsonify({'success': False, 'message': '请提供用户ID'})
        
        # 如果API状态为关闭，直接返回失败
        if api_status == '关闭':
            return jsonify({
                'success': False,
                'message': 'AdsPower API接口状态已设置为关闭'
            })
        
        # 测试AdsPower API连接
        
        # 构建API URL
        api_url = f'http://{api_host}:{api_port}'
        test_url = f"{api_url}/api/v1/user/list"
        
        # 准备请求头
        headers = {}
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        
        try:
            response = requests.get(test_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    # 检查指定用户是否存在
                    users = result.get('data', {}).get('list', [])
                    user_exists = any(user.get('user_id') == user_id for user in users)
                    
                    if user_exists:
                        return jsonify({
                            'success': True, 
                            'message': f'AdsPower连接成功，用户ID {user_id} 存在',
                            'api_url': api_url
                        })
                    else:
                        return jsonify({
                            'success': False, 
                            'message': f'AdsPower连接成功，但用户ID {user_id} 不存在。可用用户: {", ".join([u.get("user_id", "未知") for u in users])}'
                        })
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
                    
        except requests.exceptions.Timeout as e:
            return jsonify({
                'success': False,
                'message': f'连接超时: {str(e)}'
            })
        except requests.exceptions.ConnectionError as e:
            return jsonify({
                'success': False,
                'message': f'连接失败: {str(e)}'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'请求错误: {str(e)}'
            })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'连接测试失败: {str(e)}'})

@app.route('/api/test_open_adspower', methods=['POST'])
def api_test_open_adspower():
    """测试打开 AdsPower 浏览器窗口"""
    try:
        data = request.form.to_dict()
        
        # 从数据库获取配置信息
        configs = SystemConfig.query.all()
        config_dict = {cfg.key: cfg.value for cfg in configs}
        
        # 获取API配置信息
        api_host = data.get('api_host') or config_dict.get('adspower_api_host', 'localhost')
        api_port = data.get('api_port') or config_dict.get('adspower_api_port', '50325')
        api_status = config_dict.get('adspower_api_status', '')
        api_key = config_dict.get('adspower_api_key', '')
        user_id = data.get('user_id') or config_dict.get('adspower_user_id', '')
        
        if not user_id:
            return jsonify({'success': False, 'message': '请提供用户ID'})
        
        if api_status == '关闭':
            return jsonify({
                'success': False,
                'message': 'AdsPower API接口状态已设置为关闭'
            })
        
        # 创建 AdsPowerLauncher 实例
        launcher_config = {
            'local_api_url': f'http://{api_host}:{api_port}',
            'user_id': user_id,
            'api_status': api_status,
            'api_key': api_key
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
                    
                    # 保存推文数据
                    saved_count = _save_tweets_to_db(collected_tweets, task.id)
                    
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
        running_tasks = ScrapingTask.query.filter_by(status='running').all()
        if running_tasks:
            for task in running_tasks:
                task.status = 'pending'
            db.session.commit()
        
        # 从数据库加载配置
        load_config_from_database()
        
        # 初始化任务管理器（在配置加载后）
        init_task_manager()

@app.route('/debug-adspower')
def debug_adspower():
    """AdsPower调试页面"""
    with open('debug_adspower.html', 'r', encoding='utf-8') as f:
        return f.read()

if __name__ == '__main__':
    # 初始化数据库
    init_db()
    
    # 初始化任务执行器
    task_executor = ScrapingTaskExecutor()
    
    # 启动Web应用
    
    app.run(debug=True, host='0.0.0.0', port=8088)