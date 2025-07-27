#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试单个字段的创建
逐个测试每个字段，找出哪些字段可以正常创建
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_app import FEISHU_CONFIG
import requests
import json
import time

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

def test_single_field_create():
    """测试单个字段创建"""
    print("🔍 测试单个字段创建")
    print("=" * 60)
    
    # 1. 获取访问令牌
    access_token = get_feishu_access_token()
    if not access_token:
        print("❌ 无法获取访问令牌")
        return
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # 2. 定义测试字段
    test_fields = [
        ('推文原文内容', 'fldP1JOumq', '这是一条测试推文内容'),
        ('作者（账号）', 'fldluRa5UH', '测试作者'),
        ('推文链接', 'fldfKOISxg', 'https://example.com/test'),
        ('话题标签（Hashtag）', 'fldtvHz8li', '#测试标签'),
        ('类型标签', 'fldujmCFCy', '测试类型'),
        ('评论', 'fldfaq1P64', 100),
        ('点赞', 'flduzds2Ju', 200),
        ('转发', 'fldJT2WAfe', 50)
    ]
    
    create_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_CONFIG['spreadsheet_token']}/tables/{FEISHU_CONFIG['table_id']}/records/batch_create"
    
    successful_fields = []
    failed_fields = []
    
    # 3. 逐个测试字段
    for field_name, field_id, test_value in test_fields:
        print(f"\n测试字段: {field_name} ({field_id})")
        print(f"测试值: {test_value}")
        
        payload = {
            "records": [
                {
                    "fields": {
                        field_id: test_value
                    }
                }
            ]
        }
        
        print(f"请求体: {json.dumps(payload, ensure_ascii=False)}")
        
        try:
            response = requests.post(create_url, headers=headers, json=payload)
            print(f"响应状态码: {response.status_code}")
            
            result = response.json()
            print(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            if result.get('code') == 0:
                print(f"✅ 字段 {field_name} 创建成功")
                successful_fields.append((field_name, field_id))
                
                # 获取创建的记录ID
                records = result.get('data', {}).get('records', [])
                if records:
                    record_id = records[0].get('record_id')
                    print(f"   创建的记录ID: {record_id}")
            else:
                print(f"❌ 字段 {field_name} 创建失败: {result.get('msg')}")
                failed_fields.append((field_name, field_id, result.get('msg')))
                
        except Exception as e:
            print(f"❌ 字段 {field_name} 请求异常: {e}")
            failed_fields.append((field_name, field_id, str(e)))
        
        # 等待一下避免请求过快
        time.sleep(1)
    
    # 4. 总结结果
    print("\n" + "=" * 60)
    print("测试结果总结:")
    print(f"成功字段数: {len(successful_fields)}")
    print(f"失败字段数: {len(failed_fields)}")
    
    if successful_fields:
        print("\n✅ 成功的字段:")
        for field_name, field_id in successful_fields:
            print(f"   - {field_name} ({field_id})")
    
    if failed_fields:
        print("\n❌ 失败的字段:")
        for field_name, field_id, error_msg in failed_fields:
            print(f"   - {field_name} ({field_id}): {error_msg}")
    
    # 5. 如果有成功的字段，测试组合创建
    if len(successful_fields) >= 2:
        print("\n" + "=" * 60)
        print("测试组合字段创建:")
        
        # 选择前3个成功的字段进行组合测试
        combo_fields = successful_fields[:3]
        combo_payload = {
            "records": [
                {
                    "fields": {}
                }
            ]
        }
        
        for field_name, field_id in combo_fields:
            # 根据字段类型设置测试值
            if '评论' in field_name or '点赞' in field_name or '转发' in field_name:
                test_value = 123
            else:
                test_value = f"组合测试-{field_name}"
            
            combo_payload['records'][0]['fields'][field_id] = test_value
            print(f"   添加字段: {field_name} = {test_value}")
        
        print(f"\n组合请求体: {json.dumps(combo_payload, ensure_ascii=False, indent=2)}")
        
        try:
            combo_response = requests.post(create_url, headers=headers, json=combo_payload)
            print(f"组合响应状态码: {combo_response.status_code}")
            
            combo_result = combo_response.json()
            print(f"组合响应内容: {json.dumps(combo_result, ensure_ascii=False, indent=2)}")
            
            if combo_result.get('code') == 0:
                print(f"✅ 组合字段创建成功")
            else:
                print(f"❌ 组合字段创建失败: {combo_result.get('msg')}")
                
        except Exception as e:
            print(f"❌ 组合字段请求异常: {e}")

if __name__ == "__main__":
    test_single_field_create()