#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import sqlite3
import requests
import json
from datetime import datetime
import time

def get_feishu_access_token(app_id, app_secret):
    """获取飞书访问令牌"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    headers = {
        'Content-Type': 'application/json'
    }
    payload = {
        'app_id': app_id,
        'app_secret': app_secret
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        
        if result.get('code') == 0:
            return result.get('tenant_access_token')
        else:
            print(f"获取访问令牌失败: {result.get('msg')}")
            return None
    except Exception as e:
        print(f"获取访问令牌异常: {e}")
        return None

def get_table_fields(access_token, spreadsheet_token, table_id):
    """获取多维表格的字段信息"""
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{spreadsheet_token}/tables/{table_id}/fields"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        if result.get('code') == 0:
            return result.get('data', {}).get('items', [])
        else:
            print(f"获取字段信息失败: {result.get('msg')}")
            return []
    except Exception as e:
        print(f"获取字段信息异常: {e}")
        return []

def test_single_record_sync(access_token, spreadsheet_token, table_id, record_data):
    """测试单条记录同步"""
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{spreadsheet_token}/tables/{table_id}/records"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'fields': record_data
    }
    
    try:
        print(f"\n=== 测试单条记录同步 ===")
        print(f"URL: {url}")
        print(f"Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        
        response = requests.post(url, headers=headers, json=payload)
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        result = response.json()
        print(f"Response Body: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if result.get('code') == 0:
            print("✅ 单条记录同步成功")
            return True
        else:
            print(f"❌ 单条记录同步失败: {result.get('msg')}")
            return False
            
    except Exception as e:
        print(f"❌ 单条记录同步异常: {e}")
        return False

def main():
    print("=== 飞书同步调试工具 ===")
    
    # 从数据库获取配置
    conn = sqlite3.connect('instance/twitter_scraper.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT key, value FROM system_config WHERE key LIKE "feishu%"')
    configs = {row[0]: row[1] for row in cursor.fetchall()}
    
    app_id = configs.get('feishu_app_id')
    app_secret = configs.get('feishu_app_secret')
    spreadsheet_token = configs.get('feishu_spreadsheet_token')
    table_id = configs.get('feishu_table_id')
    
    print(f"\n=== 飞书配置 ===")
    print(f"App ID: {app_id}")
    print(f"App Secret: {app_secret[:10]}...")
    print(f"Spreadsheet Token: {spreadsheet_token}")
    print(f"Table ID: {table_id}")
    
    # 获取访问令牌
    print(f"\n=== 获取访问令牌 ===")
    access_token = get_feishu_access_token(app_id, app_secret)
    if not access_token:
        print("❌ 无法获取访问令牌")
        return
    
    print(f"✅ 访问令牌获取成功: {access_token[:20]}...")
    
    # 获取表格字段信息
    print(f"\n=== 获取表格字段信息 ===")
    fields = get_table_fields(access_token, spreadsheet_token, table_id)
    if fields:
        print(f"✅ 找到 {len(fields)} 个字段:")
        for field in fields:
            print(f"  - {field.get('field_name')} ({field.get('type')})")
    else:
        print("❌ 无法获取字段信息")
        return
    
    # 获取任务3的一条推文数据进行测试
    cursor.execute('''
        SELECT content, username, link, hashtags, publish_time, likes, comments, retweets
        FROM tweet_data 
        WHERE task_id = 3 
        LIMIT 1
    ''')
    
    tweet = cursor.fetchone()
    if not tweet:
        print("❌ 未找到任务3的推文数据")
        return
    
    print(f"\n=== 测试数据 ===")
    print(f"推文内容: {tweet[0][:50]}...")
    print(f"用户名: {tweet[1]}")
    print(f"链接: {tweet[2]}")
    
    # 准备测试记录 - 根据字段类型格式化数据
    field_types = {field.get('field_name'): field.get('type') for field in fields}
    
    # 处理时间字段
    current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    current_timestamp = int(time.time() * 1000)
    
    test_record = {
        '推文原文内容': str(tweet[0] or ''),
        '作者（账号）': str(tweet[1] or ''),
        '推文链接': str(tweet[2] or ''),
        '话题标签（Hashtag）': str(tweet[3] or ''),
        '类型标签': '测试',
        '收藏数': int(tweet[5] or 0),
        '点赞数': int(tweet[5] or 0),
        '转发数': int(tweet[7] or 0),
        # 根据字段类型设置时间值
        '发布时间': current_timestamp if field_types.get('发布时间') == 5 else current_time_str,
        '创建时间': current_timestamp if field_types.get('创建时间') == 5 else current_time_str
    }
    
    # 测试单条记录同步
    success = test_single_record_sync(access_token, spreadsheet_token, table_id, test_record)
    
    conn.close()
    
    if success:
        print("\n🎉 飞书同步测试成功！")
    else:
        print("\n💥 飞书同步测试失败！")

if __name__ == "__main__":
    main()