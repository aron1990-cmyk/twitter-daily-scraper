#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试单条推文数据插入飞书表格
"""

import sqlite3
import json
from cloud_sync import CloudSyncManager

def test_single_feishu_insert():
    """测试从数据库读取一条推文并插入到飞书表格"""
    
    # 从数据库获取飞书配置
    feishu_config = {}
    
    # 连接数据库获取配置
    config_conn = sqlite3.connect('instance/twitter_scraper.db')
    config_cursor = config_conn.cursor()
    
    try:
        config_cursor.execute('SELECT key, value FROM system_config WHERE key LIKE "feishu%"')
        config_rows = config_cursor.fetchall()
        
        for key, value in config_rows:
            # 移除feishu_前缀
            config_key = key.replace('feishu_', '')
            # 处理布尔值
            if value in ('true', 'false'):
                feishu_config[config_key] = value == 'true'
            else:
                feishu_config[config_key] = value
                
        print(f"飞书配置: {feishu_config}")
        
    finally:
        config_conn.close()
    
    # 连接数据库
    db_path = 'instance/twitter_scraper.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 查询一条推文数据
        cursor.execute("""
            SELECT username, content, likes, comments, retweets, 
                   publish_time, link, hashtags, content_type, 
                   full_content, media_content
            FROM tweet_data 
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        if not row:
            print("数据库中没有推文数据")
            return
        
        # 构造推文数据
        tweet_data = {
            'username': row[0],
            'content': row[1],
            'likes': row[2] or 0,
            'comments': row[3] or 0,
            'retweets': row[4] or 0,
            'publish_time': row[5],
            'link': row[6],
            'hashtags': row[7] or '',
            'content_type': row[8] or 'text',
            'full_content': row[9] or '',
            'media_content': row[10] or ''
        }
        
        print(f"读取到推文数据: {tweet_data['username']} - {tweet_data['content'][:50]}...")
        
        # 添加base_url到飞书配置
        feishu_config['base_url'] = 'https://open.feishu.cn/open-apis'
        
        # 初始化云端同步管理器
        cloud_sync = CloudSyncManager({'feishu': feishu_config})
        
        # 检查飞书配置
        if not feishu_config.get('enabled', False):
            print("飞书功能未启用，请检查配置")
            return
        
        # 获取飞书访问令牌
        access_token = cloud_sync.get_feishu_access_token()
        if not access_token:
            print("无法获取飞书访问令牌")
            return
        
        print(f"成功获取飞书访问令牌: {access_token[:20]}...")
        
        # 准备单条数据进行同步
        tweets_to_sync = [tweet_data]
        
        # 同步到飞书
        result = cloud_sync.sync_to_feishu(
            tweets_to_sync, 
            feishu_config['spreadsheet_token'], 
            feishu_config['table_id']
        )
        
        if result:
            print("✅ 成功将推文插入到飞书表格")
        else:
            print("❌ 插入飞书表格失败")
            
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()

if __name__ == "__main__":
    test_single_feishu_insert()