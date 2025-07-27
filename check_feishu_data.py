#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查飞书文档中的实际数据
验证数据是否真的同步进去了
"""

import sys
import os
import requests
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_app import app, FEISHU_CONFIG
from cloud_sync import CloudSyncManager

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

def get_feishu_table_records(access_token):
    """获取飞书表格记录"""
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_CONFIG['spreadsheet_token']}/tables/{FEISHU_CONFIG['table_id']}/records"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    # 添加查询参数，获取记录
    params = {
        "page_size": 50  # 获取更多记录
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        result = response.json()
        
        if result.get('code') == 0:
            return result.get('data', {}).get('items', [])
        else:
            print(f"❌ 获取表格记录失败: {result}")
            return []
    except Exception as e:
        print(f"❌ 获取表格记录异常: {e}")
        return []

def get_feishu_table_fields(access_token):
    """获取飞书表格字段信息"""
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_CONFIG['spreadsheet_token']}/tables/{FEISHU_CONFIG['table_id']}/fields"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        result = response.json()
        
        if result.get('code') == 0:
            return result.get('data', {}).get('items', [])
        else:
            print(f"❌ 获取表格字段失败: {result}")
            return []
    except Exception as e:
        print(f"❌ 获取表格字段异常: {e}")
        return []

def check_feishu_data():
    """检查飞书文档中的数据"""
    print("🔍 开始检查飞书文档中的实际数据")
    print("="*60)
    
    # 1. 获取访问令牌
    print("\n🔑 步骤1: 获取飞书访问令牌")
    access_token = get_feishu_access_token()
    if not access_token:
        print("❌ 无法获取访问令牌，停止检查")
        return
    print(f"✅ 成功获取访问令牌: {access_token[:20]}...")
    
    # 2. 获取表格字段信息
    print("\n📋 步骤2: 获取表格字段信息")
    fields = get_feishu_table_fields(access_token)
    if fields:
        print(f"✅ 找到 {len(fields)} 个字段:")
        field_map = {}
        for field in fields:
            field_name = field.get('field_name', '')
            field_id = field.get('field_id', '')
            field_type = field.get('type', '')
            field_map[field_id] = field_name
            print(f"   - {field_name} (ID: {field_id}, 类型: {field_type})")
            # 特别检查推文原文内容字段
            if field_name == '推文原文内容':
                print(f"     🎯 找到推文原文内容字段: ID={field_id}, 类型={field_type}")
    else:
        print("❌ 无法获取字段信息")
        field_map = {}
    
    # 3. 获取表格记录
    print("\n📊 步骤3: 获取表格记录")
    records = get_feishu_table_records(access_token)
    if records:
        print(f"✅ 找到 {len(records)} 条记录")
        
        # 查找包含推文原文内容的记录
        content_records = []
        for record in records:
            fields_data = record.get('fields', {})
            for field_id, value in fields_data.items():
                field_name = field_map.get(field_id, f"未知字段({field_id})")
                if field_name == '推文原文内容' and value and str(value).strip():
                    content_records.append(record)
                    break
        
        print(f"\n   🎯 找到 {len(content_records)} 条包含推文原文内容的记录")
        
        # 显示包含内容的记录
        for i, record in enumerate(content_records[:5]):
            print(f"\n   📝 内容记录 {i+1}:")
            print(f"      - 记录ID: {record.get('record_id', '')}")
            print(f"      - 创建时间: {record.get('created_time', '')}")
            print(f"      - 修改时间: {record.get('last_modified_time', '')}")
            
            fields_data = record.get('fields', {})
            print(f"      - 字段数据:")
            
            for field_id, value in fields_data.items():
                field_name = field_map.get(field_id, f"未知字段({field_id})")
                
                # 特别关注推文原文内容字段
                if field_name == '推文原文内容':
                    print(f"        🎯 {field_name}: {repr(str(value)[:200])}")
                else:
                    print(f"        - {field_name}: {repr(str(value)[:50])}")
        
        # 如果没有找到内容记录，显示最近的几条记录
        if not content_records:
            print(f"\n   ⚠️ 没有找到包含推文原文内容的记录，显示最近的5条记录:")
            for i, record in enumerate(records[:5]):
                print(f"\n   📝 记录 {i+1}:")
                print(f"      - 记录ID: {record.get('record_id', '')}")
                print(f"      - 创建时间: {record.get('created_time', '')}")
                print(f"      - 修改时间: {record.get('last_modified_time', '')}")
                
                fields_data = record.get('fields', {})
                print(f"      - 字段数据:")
                
                for field_id, value in fields_data.items():
                     field_name = field_map.get(field_id, f"未知字段({field_id})")
                     print(f"        - {field_name} (ID:{field_id}): {repr(str(value)[:50])}")
                     # 特别检查是否有推文原文内容字段ID
                     if field_id == 'fldP1JOumq':
                         print(f"          🎯 这是推文原文内容字段！值: {repr(str(value)[:100])}")
    else:
        print("❌ 没有找到任何记录")
    
    # 4. 检查是否有推文原文内容字段
    print("\n🎯 步骤4: 检查推文原文内容字段")
    content_fields = [f for f in fields if '推文' in f.get('field_name', '') or 'content' in f.get('field_name', '').lower()]
    if content_fields:
        print(f"✅ 找到 {len(content_fields)} 个相关字段:")
        for field in content_fields:
            print(f"   - {field.get('field_name')} (ID: {field.get('field_id')})")
    else:
        print("❌ 没有找到推文原文内容相关字段")
    
    print("\n" + "="*60)
    print("🏁 检查完成")

if __name__ == "__main__":
    with app.app_context():
        check_feishu_data()