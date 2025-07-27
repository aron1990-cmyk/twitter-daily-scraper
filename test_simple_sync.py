#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试飞书同步
直接同步一条测试数据，然后立即查看结果
"""

import sys
import os
import requests
import json
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_app import app, FEISHU_CONFIG

def get_feishu_access_token():
    """获取飞书访问令牌"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    headers = {
        "Content-Type": "application/json; charset=utf-8"
    }
    data = {
        "app_id": FEISHU_CONFIG['app_id'],
        "app_secret": FEISHU_CONFIG['app_secret']
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        result = response.json()
        
        if result.get('code') == 0:
            return result.get('tenant_access_token')
        else:
            print(f"❌ 获取访问令牌失败: {result}")
            return None
    except Exception as e:
        print(f"❌ 获取访问令牌异常: {e}")
        return None

def test_simple_sync():
    """简单测试飞书同步"""
    print("🧪 开始简单飞书同步测试")
    print("="*50)
    
    # 1. 获取访问令牌
    print("\n🔑 步骤1: 获取飞书访问令牌")
    access_token = get_feishu_access_token()
    if not access_token:
        print("❌ 无法获取访问令牌，停止测试")
        return
    print(f"✅ 成功获取访问令牌")
    
    # 2. 准备测试数据
    print("\n📝 步骤2: 准备测试数据")
    test_content = f"测试推文内容 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    test_data = {
        'records': [
            {
                'fields': {
                    '推文原文内容': test_content
                }
            }
        ]
    }
    print(f"   - 测试内容: {test_content}")
    print(f"   - 测试数据: {test_data}")
    
    # 3. 发送同步请求
    print("\n🚀 步骤3: 发送同步请求")
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_CONFIG['spreadsheet_token']}/tables/{FEISHU_CONFIG['table_id']}/records/batch_create"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    print(f"   - 请求URL: {url}")
    print(f"   - 请求头: {headers}")
    
    try:
        response = requests.post(url, headers=headers, json=test_data, timeout=60)
        print(f"   - 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   - 响应结果: {result}")
            
            if result.get('code') == 0:
                print("✅ 同步请求成功")
                created_records = result.get('data', {}).get('records', [])
                print(f"   - 创建的记录数: {len(created_records)}")
                if created_records:
                    print(f"   - 第一条记录ID: {created_records[0].get('record_id')}")
                    return created_records[0].get('record_id')
            else:
                print(f"❌ 同步请求失败: {result.get('msg')}")
                return None
        else:
            print(f"❌ HTTP请求失败: {response.status_code}")
            print(f"   - 响应内容: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 同步请求异常: {e}")
        return None

def check_record(record_id, access_token):
    """检查指定记录"""
    print(f"\n🔍 步骤4: 检查记录 {record_id}")
    
    # 等待一下，确保记录已经创建
    time.sleep(2)
    
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_CONFIG['spreadsheet_token']}/tables/{FEISHU_CONFIG['table_id']}/records/{record_id}"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"   - 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   - 响应结果: {result}")
            
            if result.get('code') == 0:
                record_data = result.get('data', {}).get('record', {})
                fields = record_data.get('fields', {})
                print(f"✅ 记录查询成功")
                print(f"   - 记录字段: {fields}")
                
                # 检查推文原文内容字段
                content = fields.get('推文原文内容')
                if content:
                    print(f"🎯 找到推文原文内容: {content}")
                else:
                    print(f"❌ 推文原文内容字段为空")
                    print(f"   - 所有字段: {list(fields.keys())}")
            else:
                print(f"❌ 记录查询失败: {result.get('msg')}")
        else:
            print(f"❌ HTTP请求失败: {response.status_code}")
            print(f"   - 响应内容: {response.text}")
            
    except Exception as e:
        print(f"❌ 记录查询异常: {e}")

if __name__ == "__main__":
    with app.app_context():
        record_id = test_simple_sync()
        if record_id:
            access_token = get_feishu_access_token()
            if access_token:
                check_record(record_id, access_token)
        
        print("\n" + "="*50)
        print("🏁 测试完成")