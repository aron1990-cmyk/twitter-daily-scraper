#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
比较实际的字段ID和使用的字段ID
找出不匹配的字段
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_app import app, FEISHU_CONFIG
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

def compare_field_ids():
    """比较字段ID"""
    print("🔍 比较字段ID")
    print("=" * 60)
    
    # 1. 获取访问令牌
    print("\n1. 获取飞书访问令牌...")
    access_token = get_feishu_access_token(FEISHU_CONFIG['app_id'], FEISHU_CONFIG['app_secret'])
    
    if not access_token:
        print("   ❌ 无法获取访问令牌")
        return
    
    print("   ✅ 访问令牌获取成功")
    
    # 2. 获取实际的字段信息
    print("\n2. 获取实际的字段信息...")
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_CONFIG['spreadsheet_token']}/tables/{FEISHU_CONFIG['table_id']}/fields"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"   ❌ 请求失败: HTTP {response.status_code}")
        return
    
    data = response.json()
    if data.get('code') != 0:
        print(f"   ❌ API调用失败: {data.get('msg')}")
        return
    
    fields = data.get('data', {}).get('items', [])
    print(f"   ✅ 获取到 {len(fields)} 个字段")
    
    # 3. 显示所有字段信息
    print("\n3. 所有字段信息:")
    actual_field_mapping = {}
    
    for field in fields:
        field_name = field.get('field_name', '')
        field_id = field.get('field_id', '')
        field_type = field.get('type', 0)
        actual_field_mapping[field_name] = field_id
        
        print(f"   - {field_name}:")
        print(f"     字段ID: {field_id}")
        print(f"     字段类型: {field_type}")
    
    # 4. 检查我们使用的字段
    print("\n4. 检查我们使用的字段:")
    our_fields = [
        '推文原文内容',
        '作者（账号）',
        '推文链接',
        '话题标签（Hashtag）',
        '类型标签',
        '评论',
        '点赞',
        '转发'
    ]
    
    missing_fields = []
    valid_fields = []
    
    for field_name in our_fields:
        if field_name in actual_field_mapping:
            field_id = actual_field_mapping[field_name]
            valid_fields.append((field_name, field_id))
            print(f"   ✅ {field_name}: {field_id}")
        else:
            missing_fields.append(field_name)
            print(f"   ❌ {field_name}: 字段不存在")
    
    # 5. 显示结果
    print("\n5. 检查结果:")
    print(f"   - 有效字段数: {len(valid_fields)}")
    print(f"   - 缺失字段数: {len(missing_fields)}")
    
    if missing_fields:
        print(f"   ⚠️ 缺失字段: {missing_fields}")
        print("\n   建议检查飞书表格中的字段名称是否正确")
    
    # 6. 生成正确的字段映射代码
    print("\n6. 正确的字段映射:")
    print("   field_name_to_id = {")
    for field_name, field_id in valid_fields:
        print(f"       '{field_name}': '{field_id}',")
    print("   }")
    
    # 7. 测试一个简单的API调用
    print("\n7. 测试简单的API调用:")
    if valid_fields:
        # 使用第一个有效字段进行测试
        test_field_name, test_field_id = valid_fields[0]
        test_payload = {
            "records": [
                {
                    "fields": {
                        test_field_id: "测试内容"
                    }
                }
            ]
        }
        
        create_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_CONFIG['spreadsheet_token']}/tables/{FEISHU_CONFIG['table_id']}/records/batch_create"
        
        print(f"   测试字段: {test_field_name} ({test_field_id})")
        print(f"   请求URL: {create_url}")
        print(f"   请求体: {json.dumps(test_payload, ensure_ascii=False)}")
        
        test_response = requests.post(create_url, headers=headers, json=test_payload)
        print(f"   响应状态码: {test_response.status_code}")
        
        try:
            test_result = test_response.json()
            print(f"   响应内容: {json.dumps(test_result, ensure_ascii=False, indent=2)}")
            
            if test_result.get('code') == 0:
                print("   ✅ 测试成功！字段ID是正确的")
            else:
                print(f"   ❌ 测试失败: {test_result.get('msg')}")
        except Exception as e:
            print(f"   ❌ 解析响应失败: {e}")
            print(f"   原始响应: {test_response.text}")

if __name__ == "__main__":
    compare_field_ids()