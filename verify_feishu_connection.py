#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证飞书API连接
检查应用权限、表格访问权限等
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_app import FEISHU_CONFIG
import requests
import json

def verify_feishu_connection():
    """验证飞书连接"""
    print("🔍 验证飞书API连接")
    print("=" * 60)
    
    # 1. 获取访问令牌
    print("\n1. 获取访问令牌...")
    token_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    token_payload = {
        "app_id": FEISHU_CONFIG['app_id'],
        "app_secret": FEISHU_CONFIG['app_secret']
    }
    
    print(f"   请求URL: {token_url}")
    print(f"   应用ID: {FEISHU_CONFIG['app_id']}")
    print(f"   应用密钥: {FEISHU_CONFIG['app_secret'][:10]}...")
    
    token_response = requests.post(token_url, json=token_payload)
    print(f"   响应状态码: {token_response.status_code}")
    
    if token_response.status_code != 200:
        print(f"   ❌ 获取令牌失败: HTTP {token_response.status_code}")
        print(f"   响应内容: {token_response.text}")
        return
    
    token_data = token_response.json()
    print(f"   响应内容: {json.dumps(token_data, ensure_ascii=False, indent=2)}")
    
    if token_data.get('code') != 0:
        print(f"   ❌ 获取令牌失败: {token_data.get('msg')}")
        return
    
    access_token = token_data.get('tenant_access_token')
    print(f"   ✅ 访问令牌获取成功: {access_token[:20]}...")
    
    # 2. 验证应用信息
    print("\n2. 验证应用信息...")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # 3. 检查多维表格应用访问权限
    print("\n3. 检查多维表格应用访问权限...")
    app_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_CONFIG['spreadsheet_token']}"
    print(f"   请求URL: {app_url}")
    
    app_response = requests.get(app_url, headers=headers)
    print(f"   响应状态码: {app_response.status_code}")
    
    if app_response.status_code != 200:
        print(f"   ❌ 访问应用失败: HTTP {app_response.status_code}")
        print(f"   响应内容: {app_response.text}")
        return
    
    app_data = app_response.json()
    print(f"   响应内容: {json.dumps(app_data, ensure_ascii=False, indent=2)}")
    
    if app_data.get('code') != 0:
        print(f"   ❌ 访问应用失败: {app_data.get('msg')}")
        return
    
    print(f"   ✅ 应用访问成功")
    app_info = app_data.get('data', {}).get('app', {})
    print(f"   应用名称: {app_info.get('name', 'N/A')}")
    print(f"   应用版本: {app_info.get('version', 'N/A')}")
    
    # 4. 检查表格列表
    print("\n4. 检查表格列表...")
    tables_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_CONFIG['spreadsheet_token']}/tables"
    print(f"   请求URL: {tables_url}")
    
    tables_response = requests.get(tables_url, headers=headers)
    print(f"   响应状态码: {tables_response.status_code}")
    
    if tables_response.status_code != 200:
        print(f"   ❌ 获取表格列表失败: HTTP {tables_response.status_code}")
        print(f"   响应内容: {tables_response.text}")
        return
    
    tables_data = tables_response.json()
    print(f"   响应内容: {json.dumps(tables_data, ensure_ascii=False, indent=2)}")
    
    if tables_data.get('code') != 0:
        print(f"   ❌ 获取表格列表失败: {tables_data.get('msg')}")
        return
    
    tables = tables_data.get('data', {}).get('items', [])
    print(f"   ✅ 找到 {len(tables)} 个表格")
    
    target_table_found = False
    for table in tables:
        table_id = table.get('table_id', '')
        table_name = table.get('name', '')
        print(f"   - 表格: {table_name} (ID: {table_id})")
        
        if table_id == FEISHU_CONFIG['table_id']:
            target_table_found = True
            print(f"     ✅ 这是目标表格")
    
    if not target_table_found:
        print(f"   ❌ 未找到目标表格 ID: {FEISHU_CONFIG['table_id']}")
        return
    
    # 5. 检查目标表格的字段
    print("\n5. 检查目标表格的字段...")
    fields_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_CONFIG['spreadsheet_token']}/tables/{FEISHU_CONFIG['table_id']}/fields"
    print(f"   请求URL: {fields_url}")
    
    fields_response = requests.get(fields_url, headers=headers)
    print(f"   响应状态码: {fields_response.status_code}")
    
    if fields_response.status_code != 200:
        print(f"   ❌ 获取字段失败: HTTP {fields_response.status_code}")
        print(f"   响应内容: {fields_response.text}")
        return
    
    fields_data = fields_response.json()
    print(f"   响应内容: {json.dumps(fields_data, ensure_ascii=False, indent=2)}")
    
    if fields_data.get('code') != 0:
        print(f"   ❌ 获取字段失败: {fields_data.get('msg')}")
        return
    
    fields = fields_data.get('data', {}).get('items', [])
    print(f"   ✅ 找到 {len(fields)} 个字段")
    
    # 6. 尝试读取现有记录
    print("\n6. 尝试读取现有记录...")
    records_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_CONFIG['spreadsheet_token']}/tables/{FEISHU_CONFIG['table_id']}/records"
    records_params = {"page_size": 1}
    print(f"   请求URL: {records_url}")
    
    records_response = requests.get(records_url, headers=headers, params=records_params)
    print(f"   响应状态码: {records_response.status_code}")
    
    if records_response.status_code != 200:
        print(f"   ❌ 读取记录失败: HTTP {records_response.status_code}")
        print(f"   响应内容: {records_response.text}")
        return
    
    records_data = records_response.json()
    print(f"   响应内容: {json.dumps(records_data, ensure_ascii=False, indent=2)}")
    
    if records_data.get('code') != 0:
        print(f"   ❌ 读取记录失败: {records_data.get('msg')}")
        return
    
    records = records_data.get('data', {}).get('items', [])
    print(f"   ✅ 读取记录成功，共 {len(records)} 条记录")
    
    print("\n✅ 所有检查完成，飞书API连接正常")

if __name__ == "__main__":
    verify_feishu_connection()