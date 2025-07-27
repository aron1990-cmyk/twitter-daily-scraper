#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试飞书同步时间戳问题
检查最新任务的推文数据和飞书同步过程中的时间戳处理
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import ScrapingTask, TweetData, db
from datetime import datetime
import json
from cloud_sync import CloudSyncManager
from config import FEISHU_CONFIG

def debug_timestamp_issue():
    """调试时间戳问题"""
    print("🔍 开始调试飞书同步时间戳问题")
    
    # 获取最新的任务
    latest_task = ScrapingTask.query.order_by(ScrapingTask.id.desc()).first()
    if not latest_task:
        print("❌ 没有找到任务")
        return
    
    print(f"📋 最新任务: ID={latest_task.id}, 名称={latest_task.name}")
    
    # 获取该任务的推文数据
    tweets = TweetData.query.filter_by(task_id=latest_task.id).limit(5).all()
    print(f"📊 找到 {len(tweets)} 条推文数据")
    
    for i, tweet in enumerate(tweets):
        print(f"\n📝 推文 {i+1} (ID: {tweet.id}):")
        print(f"   - 内容: {(tweet.content or '')[:50]}...")
        print(f"   - 用户名: {tweet.username}")
        print(f"   - 发布时间原始: {tweet.publish_time}")
        print(f"   - 发布时间类型: {type(tweet.publish_time