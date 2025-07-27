#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试飞书API连接
验证配置是否正确以及是否能成功连接到飞书API
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_app import app, db, TweetData, FEISHU_CONFIG
from cloud_sync import CloudSyncManager
import json
from datetime import datetime

def test_feishu_api_connection():
    """测试飞书API连接"""
    print("\n" + "="*80)
    print("🧪 飞书API连接测试")
    print("="*80)
    
    # 1. 检查飞书配置
    print("\n1. 检查飞书配置:")
    print(f"   - enabled: {FEISHU_CONFIG.get('enabled')}")
    print(f"   - app_id: {FEISHU_CONFIG.get('app_id', 'N/A')[:10]}...")
    print(f"   - app_secret: {FEISHU_CONFIG.get('app_secret', 'N/A')[:10]}...")
    print(f"   - spreadsheet_token: {FEISHU_CONFIG.get('spreadsheet_token', 'N/A')[:10]}...")
    print(f"   - table_id: {FEISHU_CONFIG.get('table_id', 'N/A')}")
    
    if not all([FEISHU_CONFIG.get('app_id'), FEISHU_CONFIG.get('app_secret'), 
               FEISHU_CONFIG.get('spreadsheet_token'), FEISHU_CONFIG.get('table_id')]):
        print("   ❌ 飞书配置不完整")
        return False
    
    print("   ✅ 飞书配置完整")
    
    # 2. 初始化CloudSyncManager
    print("\n2. 初始化CloudSyncManager:")
    try:
        sync_config = {
            'feishu': {
                'enabled': True,
                'app_id': FEISHU_CONFIG['app_id'],
                'app_secret': FEISHU_CONFIG['app_secret'],
                'spreadsheet_token': FEISHU_CONFIG['spreadsheet_token'],
                'table_id': FEISHU_CONFIG['table_id'],
                'base_url': 'https://open.feishu.cn/open-apis'
            }
        }
        
        sync_manager = CloudSyncManager(sync_config)
        print("   ✅ CloudSyncManager初始化成功")
        
    except Exception as e:
        print(f"   ❌ CloudSyncManager初始化失败: {e}")
        return False
    
    # 3. 测试获取访问令牌
    print("\n3. 测试获取飞书访问令牌:")
    try:
        access_token = sync_manager.get_feishu_access_token()
        if access_token:
            print(f"   ✅ 访问令牌获取成功: {access_token[:20]}...")
        else:
            print("   ❌ 访问令牌获取失败")
            return False
    except Exception as e:
        print(f"   ❌ 访问令牌获取异常: {e}")
        import traceback
        print(f"   📋 异常详情: {traceback.format_exc()}")
        return False
    
    # 4. 测试获取表格信息
    print("\n4. 测试获取飞书表格信息:")
    try:
        import requests
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # 获取表格基本信息
        app_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_CONFIG['spreadsheet_token']}"
        app_response = requests.get(app_url, headers=headers)
        
        if app_response.status_code == 200:
            app_result = app_response.json()
            if app_result.get('code') == 0:
                app_data = app_result.get('data', {})
                print(f"   ✅ 表格信息获取成功:")
                print(f"     - 表格名称: {app_data.get('name', 'N/A')}")
                print(f"     - 表格URL: {app_data.get('url', 'N/A')}")
            else:
                print(f"   ❌ 表格信息获取失败: {app_result.get('msg', 'Unknown error')}")
                return False
        else:
            print(f"   ❌ 表格信息请求失败: HTTP {app_response.status_code}")
            print(f"     响应内容: {app_response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ 获取表格信息异常: {e}")
        import traceback
        print(f"   📋 异常详情: {traceback.format_exc()}")
        return False
    
    # 5. 测试获取表格字段信息
    print("\n5. 测试获取表格字段信息:")
    try:
        fields_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_CONFIG['spreadsheet_token']}/tables/{FEISHU_CONFIG['table_id']}/fields"
        fields_response = requests.get(fields_url, headers=headers)
        
        if fields_response.status_code == 200:
            fields_result = fields_response.json()
            if fields_result.get('code') == 0:
                fields_data = fields_result.get('data', {}).get('items', [])
                print(f"   ✅ 字段信息获取成功 ({len(fields_data)} 个字段):")
                for field in fields_data:
                    field_name = field.get('field_name', 'N/A')
                    field_type = field.get('type', 'N/A')
                    print(f"     - {field_name} ({field_type})")
            else:
                print(f"   ❌ 字段信息获取失败: {fields_result.get('msg', 'Unknown error')}")
                return False
        else:
            print(f"   ❌ 字段信息请求失败: HTTP {fields_response.status_code}")
            print(f"     响应内容: {fields_response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ 获取字段信息异常: {e}")
        import traceback
        print(f"   📋 异常详情: {traceback.format_exc()}")
        return False
    
    # 6. 测试获取现有记录
    print("\n6. 测试获取现有记录:")
    try:
        records_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_CONFIG['spreadsheet_token']}/tables/{FEISHU_CONFIG['table_id']}/records"
        records_response = requests.get(records_url, headers=headers, params={'page_size': 5})
        
        if records_response.status_code == 200:
            records_result = records_response.json()
            if records_result.get('code') == 0:
                records_data = records_result.get('data', {}).get('items', [])
                total = records_result.get('data', {}).get('total', 0)
                print(f"   ✅ 记录获取成功 (总计 {total} 条记录，显示前 {len(records_data)} 条):")
                for i, record in enumerate(records_data, 1):
                    record_id = record.get('record_id', 'N/A')
                    fields = record.get('fields', {})
                    print(f"     记录 {i}: {record_id}")
                    for field_name, field_value in list(fields.items())[:3]:  # 只显示前3个字段
                        print(f"       - {field_name}: {str(field_value)[:50]}...")
            else:
                print(f"   ❌ 记录获取失败: {records_result.get('msg', 'Unknown error')}")
                return False
        else:
            print(f"   ❌ 记录请求失败: HTTP {records_response.status_code}")
            print(f"     响应内容: {records_response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ 获取记录异常: {e}")
        import traceback
        print(f"   📋 异常详情: {traceback.format_exc()}")
        return False
    
    print("\n" + "="*80)
    print("🎉 飞书API连接测试完成 - 所有测试通过！")
    print("✅ 飞书配置正确，API连接正常")
    print("✅ 可以正常访问表格和字段信息")
    print("✅ 飞书同步功能应该可以正常工作")
    print("="*80)
    
    return True

if __name__ == '__main__':
    with app.app_context():
        test_feishu_api_connection()