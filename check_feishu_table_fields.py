#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查飞书表格的字段配置
获取飞书表格的字段信息，确认字段名称和类型是否正确
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_app import app, FEISHU_CONFIG
from cloud_sync import CloudSyncManager
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

def get_table_records(access_token, app_token, table_id, page_size=5):
    """获取表格记录"""
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    params = {
        "page_size": page_size
    }
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    return None

def check_feishu_table():
    """检查飞书表格配置"""
    print("🔍 检查飞书表格字段配置")
    print("=" * 60)
    
    # 1. 获取访问令牌
    print("\n1. 获取飞书访问令牌...")
    access_token = get_feishu_access_token(FEISHU_CONFIG['app_id'], FEISHU_CONFIG['app_secret'])
    
    if not access_token:
        print("   ❌ 无法获取访问令牌")
        return
    
    print("   ✅ 访问令牌获取成功")
    
    # 2. 获取表格字段信息
    print("\n2. 获取表格字段信息...")
    fields_data = get_table_fields(
        access_token, 
        FEISHU_CONFIG['spreadsheet_token'], 
        FEISHU_CONFIG['table_id']
    )
    
    if not fields_data:
        print("   ❌ 无法获取字段信息")
        return
    
    if fields_data.get('code') != 0:
        print(f"   ❌ 获取字段信息失败: {fields_data.get('msg')}")
        return
    
    fields = fields_data.get('data', {}).get('items', [])
    print(f"   ✅ 找到 {len(fields)} 个字段")
    
    # 3. 分析字段配置
    print("\n3. 字段配置详情:")
    key_fields = ['推文原文内容', '作者（账号）', '推文链接', '话题标签（Hashtag）']
    
    for field in fields:
        field_name = field.get('field_name', '')
        field_type = field.get('type', 0)
        field_id = field.get('field_id', '')
        
        type_map = {
            1: '多行文本',
            2: '数字', 
            3: '单选',
            4: '多选',
            5: '日期',
            7: '复选框',
            11: '人员',
            13: '电话号码',
            15: '超链接',
            17: '附件',
            18: '单向关联',
            19: '查找引用',
            20: '公式',
            21: '双向关联',
            22: '地理位置',
            23: '群组',
            1001: '创建时间',
            1002: '最后更新时间',
            1003: '创建人',
            1004: '修改人',
            1005: '自动编号'
        }
        
        type_name = type_map.get(field_type, f'未知类型({field_type})')
        
        if field_name in key_fields:
            print(f"   🔑 {field_name}:")
        else:
            print(f"   📝 {field_name}:")
        
        print(f"      - 字段ID: {field_id}")
        print(f"      - 字段类型: {type_name}")
        
        # 检查字段属性
        if 'property' in field and field['property'] is not None:
            prop = field['property']
            if field_type == 1:  # 多行文本
                print(f"      - 自动换行: {prop.get('auto_fill', False)}")
            elif field_type == 15:  # 超链接
                print(f"      - 链接属性: {prop}")
    
    # 4. 获取最新记录
    print("\n4. 获取最新记录样本:")
    records_data = get_table_records(
        access_token,
        FEISHU_CONFIG['spreadsheet_token'],
        FEISHU_CONFIG['table_id'],
        page_size=3
    )
    
    if not records_data or records_data.get('code') != 0:
        print("   ❌ 无法获取记录数据")
        return
    
    records = records_data.get('data', {}).get('items', [])
    print(f"   ✅ 找到 {len(records)} 条记录")
    
    for idx, record in enumerate(records[:2]):
        print(f"\n   记录 {idx + 1}:")
        fields_data = record.get('fields', {})
        
        for field_name in key_fields:
            value = fields_data.get(field_name, '未找到字段')
            if isinstance(value, list) and len(value) > 0:
                # 处理富文本或链接字段
                if isinstance(value[0], dict):
                    if 'text' in value[0]:
                        display_value = value[0]['text'][:50] + '...' if len(value[0]['text']) > 50 else value[0]['text']
                    elif 'link' in value[0]:
                        display_value = value[0].get('text', value[0].get('link', ''))[:50]
                    else:
                        display_value = str(value[0])[:50]
                else:
                    display_value = str(value)[:50]
            else:
                display_value = str(value)[:50] if value else '空值'
            
            print(f"     - {field_name}: '{display_value}'")

if __name__ == "__main__":
    check_feishu_table()