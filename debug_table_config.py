#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试表格配置问题
检查表格ID、应用ID等配置是否正确
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_app import FEISHU_CONFIG
import requests
import json

def get_feishu_access_token():
    """获取飞书访问令牌"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = {
        "app_id": FEISHU_CONFIG['app_id'],
        "app_secret": FEISHU_CONFIG['app_secret']
    }
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        data = response.json()
        if data.get('code') == 0:
            return data.get('tenant_access_token')
    return None

def debug_table_config():
    """调试表格配置"""
    print("🔍 调试表格配置")
    print("=" * 60)
    
    # 1. 显示当前配置
    print("当前配置:")
    print(f"   app_id: {FEISHU_CONFIG['app_id']}")
    print(f"   spreadsheet_token: {FEISHU_CONFIG['spreadsheet_token']}")
    print(f"   table_id: {FEISHU_CONFIG['table_id']}")
    
    # 2. 获取访问令牌
    access_token = get_feishu_access_token()
    if not access_token:
        print("❌ 无法获取访问令牌")
        return
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # 3. 检查应用信息
    print("\n3. 检查应用信息...")
    app_url = "https://open.feishu.cn/open-apis/bitable/v1/apps"
    try:
        response = requests.get(app_url, headers=headers)
        print(f"   请求URL: {app_url}")
        print(f"   响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 检查我们的应用是否在列表中
            if result.get('code') == 0:
                apps = result.get('data', {}).get('items', [])
                target_app = None
                for app in apps:
                    if app.get('app_token') == FEISHU_CONFIG['spreadsheet_token']:
                        target_app = app
                        break
                
                if target_app:
                    print(f"   ✅ 找到目标应用: {target_app.get('name')}")
                    print(f"   应用状态: {target_app.get('is_advanced', 'unknown')}")
                else:
                    print(f"   ❌ 未找到目标应用 {FEISHU_CONFIG['spreadsheet_token']}")
                    print("   可用的应用列表:")
                    for app in apps:
                        print(f"     - {app.get('name')} ({app.get('app_token')})")
        else:
            print(f"   ❌ 请求失败: {response.text}")
    except Exception as e:
        print(f"   ❌ 请求异常: {e}")
    
    # 4. 检查表格列表
    print("\n4. 检查表格列表...")
    tables_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_CONFIG['spreadsheet_token']}/tables"
    try:
        response = requests.get(tables_url, headers=headers)
        print(f"   请求URL: {tables_url}")
        print(f"   响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            if result.get('code') == 0:
                tables = result.get('data', {}).get('items', [])
                target_table = None
                for table in tables:
                    if table.get('table_id') == FEISHU_CONFIG['table_id']:
                        target_table = table
                        break
                
                if target_table:
                    print(f"   ✅ 找到目标表格: {target_table.get('name')}")
                else:
                    print(f"   ❌ 未找到目标表格 {FEISHU_CONFIG['table_id']}")
                    print("   可用的表格列表:")
                    for table in tables:
                        print(f"     - {table.get('name')} ({table.get('table_id')})")
        else:
            print(f"   ❌ 请求失败: {response.text}")
    except Exception as e:
        print(f"   ❌ 请求异常: {e}")
    
    # 5. 再次检查字段（使用正确的URL格式）
    print("\n5. 再次检查字段...")
    fields_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_CONFIG['spreadsheet_token']}/tables/{FEISHU_CONFIG['table_id']}/fields"
    try:
        response = requests.get(fields_url, headers=headers)
        print(f"   请求URL: {fields_url}")
        print(f"   响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            if result.get('code') == 0:
                fields = result.get('data', {}).get('items', [])
                print(f"   ✅ 找到 {len(fields)} 个字段")
                
                # 检查我们需要的字段
                target_fields = {
                    'fldP1JOumq': '推文原文内容',
                    'fldluRa5UH': '作者（账号）',
                    'fldfKOISxg': '推文链接',
                    'fldtvHz8li': '话题标签（Hashtag）',
                    'fldujmCFCy': '类型标签',
                    'fldfaq1P64': '评论',
                    'flduzds2Ju': '点赞',
                    'fldJT2WAfe': '转发'
                }
                
                found_fields = {}
                for field in fields:
                    field_id = field.get('field_id')
                    field_name = field.get('field_name')
                    if field_id in target_fields:
                        found_fields[field_id] = field_name
                        print(f"   ✅ 找到字段: {field_name} ({field_id})")
                
                missing_fields = set(target_fields.keys()) - set(found_fields.keys())
                if missing_fields:
                    print(f"   ❌ 缺失字段:")
                    for field_id in missing_fields:
                        print(f"     - {target_fields[field_id]} ({field_id})")
                else:
                    print(f"   ✅ 所有目标字段都存在")
        else:
            print(f"   ❌ 请求失败: {response.text}")
    except Exception as e:
        print(f"   ❌ 请求异常: {e}")
    
    # 6. 测试一个简单的记录创建（使用字段名而不是字段ID）
    print("\n6. 测试使用字段名创建记录...")
    create_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_CONFIG['spreadsheet_token']}/tables/{FEISHU_CONFIG['table_id']}/records/batch_create"
    
    # 尝试使用字段名
    payload_with_names = {
        "records": [
            {
                "fields": {
                    "推文原文内容": "测试内容-使用字段名"
                }
            }
        ]
    }
    
    print(f"   使用字段名的请求体: {json.dumps(payload_with_names, ensure_ascii=False)}")
    
    try:
        response = requests.post(create_url, headers=headers, json=payload_with_names)
        print(f"   响应状态码: {response.status_code}")
        
        result = response.json()
        print(f"   响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if result.get('code') == 0:
            print(f"   ✅ 使用字段名创建成功")
        else:
            print(f"   ❌ 使用字段名创建失败: {result.get('msg')}")
            
    except Exception as e:
        print(f"   ❌ 请求异常: {e}")

if __name__ == "__main__":
    debug_table_config()