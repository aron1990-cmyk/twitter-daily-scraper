#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter抓取Web管理系统
提供Web界面进行关键词配置、任务管理和数据查看
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import asyncio
import threading
from dataclasses import asdict
import re

# 导入现有模块
from config import TWITTER_TARGETS, FILTER_CONFIG, CLOUD_SYNC_CONFIG
from page_structure_analyzer import PageStructureAnalyzer, IntelligentScraper

# 飞书配置信息
FEISHU_CONFIG = {
    'app_id': 'cli_a8f94354c178900b',
    'app_secret': 'HGQGTQyvr2QsWVmPMdY8Oe7A67J3ihVV',
    'spreadsheet_token': 'V862biEswatwnRsGalochUI6n6d',
    'table_id': 'tblicDZl35dn2vZ9',
    'enabled': True
}
from models import TweetModel, ScrapingConfig
from ads_browser_launcher import AdsPowerLauncher
from twitter_parser import TwitterParser
from cloud_sync import CloudSyncManager
from excel_writer import ExcelWriter

# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'twitter-scraper-web-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///twitter_scraper.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化Flask扩展
db = SQLAlchemy(app)

def init_database():
    """初始化数据库"""
    with app.app_context():
        db.create_all()
        print("数据库表创建完成")

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
    status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed
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
    根据推文内容自动分类
    
    Args:
        content: 推文内容
        
    Returns:
        内容类型分类
    """
    if not content:
        return '未分类'
    
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
    
    # 检查各类关键词
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
        return '其他'

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

# 抓取任务执行器
class ScrapingTaskExecutor:
    def __init__(self):
        self.is_running = False
        self.current_task_id = None
        
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
            browser_manager = AdsPowerLauncher()
            user_id = "k11p9ypc"  # 从配置获取
            
            browser_info = browser_manager.start_browser(user_id)
            if not browser_info:
                raise Exception("浏览器启动失败")
            
            print(f"[DEBUG] 浏览器启动成功: {browser_info}")
            
            debug_port = browser_info.get('ws', {}).get('puppeteer')
            print(f"[DEBUG] 调试端口: {debug_port}")
            
            # 连接解析器
            print(f"[DEBUG] 正在连接Twitter解析器...")
            parser = TwitterParser(debug_port)
            await parser.connect_browser()
            print(f"[DEBUG] Twitter解析器连接成功")
            
            all_tweets = []
            
            # 抓取账号推文
            for account in target_accounts:
                if not self.is_running:  # 检查是否被停止
                    break
                    
                try:
                    await parser.navigate_to_profile(account)
                    tweets = await parser.scrape_tweets(max_tweets=task.max_tweets)
                    
                    # 过滤推文
                    filtered_tweets = self._filter_tweets(tweets, task)
                    all_tweets.extend(filtered_tweets)
                    
                except Exception as e:
                    print(f"抓取账号 {account} 失败: {e}")
                    continue
            
            # 抓取关键词推文
            for keyword in target_keywords:
                if not self.is_running:
                    break
                    
                try:
                    tweets = await parser.scrape_keyword_tweets(keyword, max_tweets=task.max_tweets)
                    filtered_tweets = self._filter_tweets(tweets, task)
                    all_tweets.extend(filtered_tweets)
                    
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
                    media_content=json.dumps(tweet.get('media_content', [])),
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

# 全局任务执行器
task_executor = ScrapingTaskExecutor()

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
        'failed': len([t for t in tasks if t.status == 'failed'])
    }
    
    return render_template('tasks.html', tasks=tasks, task_stats=task_stats)

@app.route('/create_task', methods=['GET', 'POST'])
def create_task():
    """创建任务页面和处理表单提交"""
    if request.method == 'POST':
        try:
            # 处理表单数据
            task_name = request.form.get('task_name', '').strip()
            keywords = request.form.get('keywords', '').strip()
            target_accounts = request.form.get('target_accounts', '').strip()
            max_tweets = int(request.form.get('max_tweets', 100))
            
            if not task_name or not keywords:
                flash('任务名称和关键词不能为空', 'error')
                return redirect(url_for('index'))
            
            # 解析关键词和账号
            keywords_list = [k.strip() for k in keywords.split(',') if k.strip()]
            accounts_list = [a.strip() for a in target_accounts.split(',') if a.strip()] if target_accounts else []
            
            # 创建任务
            task = ScrapingTask(
                name=task_name,
                target_accounts=json.dumps(accounts_list),
                target_keywords=json.dumps(keywords_list),
                max_tweets=max_tweets,
                min_likes=0,
                min_retweets=0,
                min_comments=0
            )
            
            db.session.add(task)
            db.session.commit()
            
            flash(f'任务 "{task_name}" 创建成功！', 'success')
            return redirect(url_for('tasks'))
            
        except Exception as e:
            flash(f'创建任务失败: {str(e)}', 'error')
            return redirect(url_for('index'))
    
    return render_template('create_task.html')

@app.route('/data')
def data():
    """数据查看页面"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    tweets = TweetData.query.order_by(TweetData.scraped_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('data.html', tweets=tweets)

@app.route('/config')
def config():
    """配置页面"""
    return render_template('config.html')

@app.route('/influencers')
def influencers():
    """博主管理页面"""
    return render_template('influencers.html')

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
        
        task = ScrapingTask(
            name=data.get('name', ''),
            target_accounts=json.dumps(data.get('target_accounts', [])),
            target_keywords=json.dumps(data.get('target_keywords', [])),
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
    global task_thread
    
    if task_executor.is_running:
        return jsonify({'success': False, 'error': '已有任务在运行中'}), 400
    
    try:
        # 在新线程中运行异步任务
        def run_task():
            with app.app_context():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(task_executor.execute_task(task_id))
                loop.close()
        
        task_thread = threading.Thread(target=run_task)
        task_thread.start()
        
        return jsonify({'success': True, 'message': '任务已启动'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>/stop', methods=['POST'])
def api_stop_task(task_id):
    """停止任务"""
    if task_executor.current_task_id == task_id:
        task_executor.stop_task()
        return jsonify({'success': True, 'message': '任务已停止'})
    else:
        return jsonify({'success': False, 'error': '任务未在运行中'}), 400

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

@app.route('/api/data/export/<int:task_id>')
def api_export_data(task_id):
    """导出任务数据"""
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
            # 自动分类内容类型
            content_type = classify_content_type(tweet.content)
            
            data.append({
                '推文原文内容': tweet.content,
                '发布时间': tweet.publish_time or '',
                '作者（账号）': tweet.username,
                '推文链接': tweet.link or '',
                '话题标签': ', '.join(json.loads(tweet.hashtags or '[]')),
                '类型标签': content_type,
                '收藏数': 0,  # Twitter API限制，暂时设为0
                '点赞数': tweet.likes,
                '转发数': tweet.retweets,
                '创建时间': tweet.scraped_at.strftime('%Y-%m-%d %H:%M:%S')
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
    return jsonify({
        'is_running': task_executor.is_running,
        'current_task_id': task_executor.current_task_id,
        'current_task': current_task.to_dict() if current_task else None
    })

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
        
        # 更新全局配置
        FEISHU_CONFIG.update({
            'app_id': data.get('app_id', FEISHU_CONFIG['app_id']),
            'app_secret': data.get('app_secret', FEISHU_CONFIG['app_secret']),
            'spreadsheet_token': data.get('spreadsheet_token', FEISHU_CONFIG['spreadsheet_token']),
            'table_id': data.get('table_id', FEISHU_CONFIG['table_id']),
            'enabled': data.get('enabled', FEISHU_CONFIG['enabled'])
        })
        
        return jsonify({'success': True, 'message': '飞书配置更新成功'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/config/feishu/test', methods=['POST'])
def api_test_feishu_connection():
    """测试飞书连接"""
    try:
        # 创建测试配置
        test_config = {
            'feishu': {
                'enabled': True,
                'app_id': FEISHU_CONFIG['app_id'],
                'app_secret': FEISHU_CONFIG['app_secret'],
                'spreadsheet_token': FEISHU_CONFIG['spreadsheet_token'],
                'table_id': FEISHU_CONFIG['table_id']
            }
        }
        
        # 初始化云同步管理器
        sync_manager = CloudSyncManager(test_config)
        
        # 测试连接（发送一条测试数据）
        test_data = [{
            '推文原文内容': '测试连接 - ' + datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            '发布时间': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            '作者（账号）': 'test_user',
            '推文链接': 'https://twitter.com/test',
            '话题标签': '#测试',
            '类型标签': '其他',
            '收藏数': 0,
            '点赞数': 0,
            '转发数': 0,
            '创建时间': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }]
        
        success = sync_manager.sync_to_feishu(
            test_data,
            FEISHU_CONFIG['spreadsheet_token'],
            FEISHU_CONFIG['table_id']
        )
        
        if success:
            return jsonify({'success': True, 'message': '飞书连接测试成功'})
        else:
            return jsonify({'success': False, 'error': '飞书连接测试失败'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': f'飞书连接测试失败: {str(e)}'}), 500

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
        browser_manager = AdsPowerLauncher()
        user_id = "k11p9ypc"  # 从配置获取
        
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
        browser_manager = AdsPowerLauncher()
        user_id = "k11p9ypc"  # 从配置获取
        
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

@app.route('/api/start-enhanced-scraping', methods=['POST'])
def api_start_enhanced_scraping():
    """启动增强推文抓取API"""
    try:
        data = request.get_json()
        target_accounts = data.get('target_accounts', [])
        target_keywords = data.get('target_keywords', [])
        max_tweets = data.get('max_tweets', 20)
        enable_details = data.get('enable_details', True)
        
        if not target_accounts and not target_keywords:
            return jsonify({'success': False, 'error': '请至少指定一个目标账号或关键词'}), 400
        
        # 生成任务ID
        task_id = f"enhanced_scraping_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
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
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # 启动浏览器
                browser_manager = AdsPowerLauncher()
                user_id = "k11p9ypc"  # 从配置获取
                
                browser_info = browser_manager.start_browser(user_id)
                if not browser_info:
                    raise Exception('浏览器启动失败')
                
                debug_port = browser_info.get('ws', {}).get('puppeteer')
                
                # 创建Twitter解析器
                parser = TwitterParser(debug_port)
                
                collected_tweets = []
                details_scraped = 0
                
                # 抓取用户推文
                for account in target_accounts:
                    if len(collected_tweets) >= max_tweets:
                        break
                    
                    try:
                        # 检测账号类型
                        account_type = detect_account_type(account)
                        print(f"检测到账号 {account} 的类型: {account_type}")
                        
                        # 导航到用户页面并获取用户信息
                        loop.run_until_complete(parser.navigate_to_profile(account))
                        
                        # 抓取用户推文
                        user_tweets = loop.run_until_complete(
                            parser.scrape_user_tweets(
                                account,
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
                        print(f"抓取用户 {account} 失败: {e}")
                        continue
                
                # 抓取关键词推文
                for keyword in target_keywords:
                    if len(collected_tweets) >= max_tweets:
                        break
                    
                    try:
                        keyword_tweets = loop.run_until_complete(
                            parser.scrape_keyword_tweets(
                                keyword,
                                max_tweets=min(max_tweets - len(collected_tweets), 10)
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
                        print(f"抓取关键词 {keyword} 失败: {e}")
                        continue
                
                # 保存到数据库
                if collected_tweets:
                    # 创建新任务记录
                    task = ScrapingTask(
                        name=f"增强抓取_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
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
        return jsonify({'success': False, 'error': f'获取博主信息失败: {str(e)}'}), 500

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
        print("数据库初始化完成")

if __name__ == '__main__':
    # 初始化数据库
    init_db()
    
    # 初始化任务执行器
    task_executor = ScrapingTaskExecutor()
    
    # 启动Web应用
    print("🚀 Twitter抓取Web管理系统启动中...")
    print("📱 访问地址: http://localhost:8086")
    print("🎯 功能: 关键词配置、任务管理、数据查看、飞书同步、博主管理")
    
    app.run(debug=False, host='0.0.0.0', port=8086)