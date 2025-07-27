#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细调试飞书API调用
检查字段ID映射和API请求/响应的详细信息
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_app import app, TweetData, FEISHU_CONFIG
import requests
import json

def get_feishu_access_token(app_id, app_secret):
    """获取飞书访问令牌"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = {
        "app_id": app_id,
        "app_secret": app_secret
    }
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        data = response.json()
        if data.get('code') == 0:
            return data.get('tenant_access_token')
    return None

def get_table_fields(access_token, app_token, table_id):
    """获取表格字段信息"""
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

def test_feishu_api_call():
    """测试飞书API调用的详细过程"""
    print("🔍 详细调试飞书API调用")
    print("=" * 60)
    
    # 1. 获取访问令牌
    print("\n1. 获取飞书访问令牌...")
    access_token = get_feishu_access_token(FEISHU_CONFIG['app_id'], FEISHU_CONFIG['app_secret'])
    
    if not access_token:
        print("   ❌ 无法获取访问令牌")
        return
    
    print("   ✅ 访问令牌获取成功")
    
    # 2. 获取字段映射
    print("\n2. 获取字段映射...")
    fields_data = get_table_fields(
        access_token, 
        FEISHU_CONFIG['spreadsheet_token'], 
        FEISHU_CONFIG['table_id']
    )
    
    if not fields_data or fields_data.get('code') != 0:
        print("   ❌ 无法获取字段信息")
        return
    
    fields = fields_data.get('data', {}).get('items', [])
    field_mapping = {}
    
    for field in fields:
        field_name = field.get('field_name', '')
        field_id = field.get('field_id', '')
        field_mapping[field_name] = field_id
    
    print(f"   ✅ 字段映射获取成功，共 {len(field_mapping)} 个字段")
    
    # 3. 准备测试数据
    print("\n3. 准备测试数据...")
    with app.app_context():
        tweet = TweetData.query.filter_by(task_id=20).first()
        if not tweet:
            print("   ❌ 没有找到测试数据")
            return
        
        # 使用字段名作为键的数据
        test_data_by_name = {
            '推文原文内容': tweet.content or '',
            '作者（账号）': tweet.username or '',
            '推文链接': tweet.link or '',
            '话题标签（Hashtag）': ', '.join(json.loads(tweet.hashtags) if tweet.hashtags else []),
            '类型标签': tweet.content_type or '',
            '评论': tweet.comments or 0,
            '点赞': tweet.likes or 0,
            '转发': tweet.retweets or 0
        }
        
        print("   ✅ 测试数据准备完成")
        print(f"   数据内容预览:")
        for key, value in test_data_by_name.items():
            preview = str(value)[:50] + '...' if len(str(value)) > 50 else str(value)
            print(f"     - {key}: '{preview}'")
    
    # 4. 转换为字段ID格式
    print("\n4. 转换为字段ID格式...")
    test_data_by_id = {}
    missing_fields = []
    
    for field_name, value in test_data_by_name.items():
        if field_name in field_mapping:
            field_id = field_mapping[field_name]
            test_data_by_id[field_id] = value
            print(f"   ✅ {field_name} -> {field_id}: '{str(value)[:30]}...'")
        else:
            missing_fields.append(field_name)
            print(f"   ❌ {field_name}: 字段不存在")
    
    if missing_fields:
        print(f"   ⚠️ 缺失字段: {missing_fields}")
    
    # 5. 构造API请求
    print("\n5. 构造API请求...")
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_CONFIG['spreadsheet_token']}/tables/{FEISHU_CONFIG['table_id']}/records/batch_create"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "records": [
            {
                "fields": test_data_by_id
            }
        ]
    }
    
    print(f"   请求URL: {url}")
    print(f"   请求头: {headers}")
    print(f"   请求体: {json.dumps(payload, ensure_ascii=False, indent=2)}")
    
    # 6. 发送API请求
    print("\n6. 发送API请求...")
    response = requests.post(url, headers=headers, json=payload)
    
    print(f"   响应状态码: {response.status_code}")
    print(f"   响应头: {dict(response.headers)}")
    
    try:
        response_data = response.json()
        print(f"   响应体: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
        
        if response_data.get('code') == 0:
            print("   ✅ API调用成功")
            
            # 检查创建的记录
            records = response_data.get('data', {}).get('records', [])
            if records:
                record = records[0]
                record_id = record.get('record_id', '')
                print(f"   创建的记录ID: {record_id}")
                
                # 显示创建的字段
                created_fields = record.get('fields', {})
                print(f"   创建的字段数: {len(created_fields)}")
                for field_id, value in created_fields.items():
                    # 找到字段名
                    field_name = None
                    for name, fid in field_mapping.items():
                        if fid == field_id:
                            field_name = name
                            break
                    
                    preview = str(value)[:50] + '...' if len(str(value)) > 50 else str(value)
                    print(f"     - {field_name or field_id}: '{preview}'")
        else:
            print(f"   ❌ API调用失败: {response_data.get('msg')}")
            
    except Exception as e:
        print(f"   ❌ 解析响应失败: {e}")
        print(f"   原始响应: {response.text}")

if __name__ == "__main__":
    test_feishu_api_call()