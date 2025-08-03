#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from web_app_optimized import app, ScrapingTask
import datetime

with app.app_context():
    tasks = ScrapingTask.query.order_by(ScrapingTask.created_at.desc()).limit(10).all()
    print('最近10个任务:')
    for t in tasks:
        print(f'ID: {t.id}, 名称: {t.name}, 状态: {t.status}, 创建时间: {t.created_at}')
    
    # 查找包含"调试任务_UI创建"的任务
    debug_tasks = ScrapingTask.query.filter(ScrapingTask.name.like('%调试任务_UI创建%')).all()
    print(f'\n找到 {len(debug_tasks)} 个调试任务:')
    for t in debug_tasks:
        print(f'ID: {t.id}, 名称: {t.name}, 状态: {t.status}, 创建时间: {t.created_at}')