#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立的数据库模型文件
用于后台任务运行器，避免导入整个Flask应用
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 创建独立的Flask应用实例
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{project_root}/instance/twitter_scraper.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 创建数据库实例
db = SQLAlchemy(app)

class ScrapingTask(db.Model):
    """抓取任务模型"""
    __tablename__ = 'scraping_task'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    target_keywords = db.Column(db.Text)
    target_accounts = db.Column(db.Text)
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

class TweetData(db.Model):
    """推文数据模型"""
    __tablename__ = 'tweet_data'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('scraping_task.id'), nullable=False)
    tweet_id = db.Column(db.String(50), unique=True, nullable=False)
    author = db.Column(db.String(100))
    content = db.Column(db.Text)
    likes = db.Column(db.Integer, default=0)
    retweets = db.Column(db.Integer, default=0)
    comments = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tweet_url = db.Column(db.String(500))
    author_url = db.Column(db.String(500))
    media_urls = db.Column(db.Text)
    hashtags = db.Column(db.Text)
    mentions = db.Column(db.Text)
    is_retweet = db.Column(db.Boolean, default=False)
    original_tweet_id = db.Column(db.String(50))
    collected_at = db.Column(db.DateTime, default=datetime.utcnow)