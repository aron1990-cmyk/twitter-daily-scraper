#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from web_app import app, db, TwitterInfluencer

with app.app_context():
    try:
        # 检查表是否存在
        count = TwitterInfluencer.query.count()
        print(f'TwitterInfluencer表中的记录数: {count}')
        
        if count > 0:
            print('\n前5条记录:')
            for inf in TwitterInfluencer.query.limit(5).all():
                print(f'ID: {inf.id}, Name: {inf.name}, Username: {inf.username}, Category: {inf.category}')
        else:
            print('\n表中没有数据')
            
        # 检查表结构
        print('\n表结构:')
        for column in TwitterInfluencer.__table__.columns:
            print(f'  {column.name}: {column.type}')
            
    except Exception as e:
        print(f'错误: {e}')
        import traceback
        traceback.print_exc()