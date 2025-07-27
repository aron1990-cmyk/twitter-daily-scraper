#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试飞书API调用过程
检查推文原文内容是否在API调用中丢失
"""

import sys
import os
import json
import requests
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web_app import app, db, TweetData, FEISHU_CONFIG
from cloud_sync import CloudSyncManager

def test_feishu_api_call():
    """测试飞书API调用过程"""
    print("🧪 测试飞书API调用过程")
    print("=" * 50)
    
    with app.app_context():
        # 1. 检查飞书配置
        print("\n1. 检查飞书配置:")
        if not FEISHU_CONFIG.get('enabled'):
            print("   ❌ 飞书同步未启用")
            return
        
        print(f"   ✅ 飞书同步已启用")
        print(f"   - App ID: {FEISHU_CONFIG.get('app_id', '')[:8]}...")
        print(f"   - 表格Token: {FEISHU_CONFIG.get('spreadsheet_token', '')[:8]}...")
        print(f"   - 表格ID: {FEISHU_CONFIG.get('table_id')}")
        
        # 2. 获取测试数据
        print("\n2. 获取测试数据:")
        tweet = TweetData.query.order_by(TweetData.id.desc()).first()
        if not tweet:
            print("   ❌ 没有找到推文数据")
            return
        
        print(f"   ✅ 找到推文 ID: {tweet.id}")
        print(f"   - 内容长度: {len(tweet.content or '')}")
        print(f"   - 内容预览: {(tweet.content or '')[:100]}...")
        
        # 3. 初始化云同步管理器
        print("\n3. 初始化云同步管理器:")
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
        print(f"   ✅ 云同步管理器初始化完成")
        
        # 4. 获取访问令牌
        print("\n4. 获取飞书访问令牌:")
        access_token = sync_manager.get_feishu_access_token()
        if not access_token:
            print("   ❌ 访问令牌获取失败")
            return
        
        print(f"   ✅ 访问令牌获取成功: {access_token[:20]}...")
        
        # 5. 获取表格字段信息
        print("\n5. 获取表格字段信息:")
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        fields_url = f"{sync_config['feishu']['base_url']}/bitable/v1/apps/{FEISHU_CONFIG['spreadsheet_token']}/tables/{FEISHU_CONFIG['table_id']}/fields"
        print(f"   - 字段查询URL: {fields_url}")
        
        try:
            fields_response = requests.get(fields_url, headers=headers, timeout=30)
            print(f"   - 响应状态码: {fields_response.status_code}")
            
            if fields_response.status_code == 200:
                fields_result = fields_response.json()
                print(f"   - API响应: code={fields_result.get('code')}, msg={fields_result.get('msg', 'N/A')}")
                
                if fields_result.get('code') == 0:
                    fields_data = fields_result.get('data', {}).get('items', [])
                    available_fields = [field.get('field_name') for field in fields_data]
                    print(f"   ✅ 字段信息获取成功")
                    print(f"   - 可用字段数量: {len(available_fields)}")
                    print(f"   - 可用字段列表: {available_fields}")
                    
                    # 检查推文原文内容字段是否存在
                    if '推文原文内容' in available_fields:
                        print(f"   ✅ '推文原文内容' 字段存在于飞书表格中")
                    else:
                        print(f"   ❌ '推文原文内容' 字段不存在于飞书表格中")
                        print(f"   💡 可能的原因: 字段名称不匹配")
                        return
                else:
                    print(f"   ❌ 字段信息获取失败: {fields_result.get('msg')}")
                    return
            else:
                print(f"   ❌ 字段查询请求失败: HTTP {fields_response.status_code}")
                print(f"   - 响应内容: {fields_response.text[:200]}...")
                return
        except Exception as e:
            print(f"   ❌ 字段查询异常: {e}")
            return
        
        # 6. 准备测试数据
        print("\n6. 准备测试数据:")
        test_data = {
            '推文原文内容': tweet.content or '',
            '发布时间': int(datetime.now().timestamp()),
            '作者（账号）': tweet.username or '',
            '推文链接': tweet.link or '',
            '话题标签（Hashtag）': '',
            '类型标签': '',
            '评论': tweet.comments or 0,
            '点赞': tweet.likes or 0,
            '转发': tweet.retweets or 0,
            '创建时间': int(datetime.now().timestamp())
        }
        
        print(f"   📊 测试数据:")
        for key, value in test_data.items():
            if key == '推文原文内容':
                print(f"     - {key}: '{value[:50]}...' (长度: {len(str(value))})")
            else:
                print(f"     - {key}: {value}")
        
        # 7. 构建飞书API记录
        print("\n7. 构建飞书API记录:")
        record = {
            'fields': {
                '推文原文内容': {'type': 'text', 'text': test_data['推文原文内容']},
                '发布时间': {'type': 'number', 'number': test_data['发布时间']},
                '作者（账号）': {'type': 'text', 'text': test_data['作者（账号）']},
                '推文链接': {'type': 'url', 'link': test_data['推文链接']},
                '话题标签（Hashtag）': {'type': 'text', 'text': test_data['话题标签（Hashtag）']},
                '类型标签': {'type': 'text', 'text': test_data['类型标签']},
                '评论': {'type': 'number', 'number': test_data['评论']},
                '点赞': {'type': 'number', 'number': test_data['点赞']},
                '转发': {'type': 'number', 'number': test_data['转发']},
                '创建时间': {'type': 'number', 'number': test_data['创建时间']}
            }
        }
        
        print(f"   📊 飞书API记录:")
        for field_name, field_data in record['fields'].items():
            if field_name == '推文原文内容':
                content = field_data.get('text', '')
                print(f"     - {field_name}: '{content[:50]}...' (长度: {len(content)})")
            else:
                print(f"     - {field_name}: {field_data}")
        
        # 8. 发送API请求
        print("\n8. 发送飞书API请求:")
        url = f"{sync_config['feishu']['base_url']}/bitable/v1/apps/{FEISHU_CONFIG['spreadsheet_token']}/tables/{FEISHU_CONFIG['table_id']}/records/batch_create"
        print(f"   - 创建URL: {url}")
        
        payload = {
            'records': [record]
        }
        
        print(f"   - 载荷大小: {len(str(payload))} 字符")
        print(f"   - 载荷示例: {str(payload)[:200]}...")
        
        # 检查载荷中的推文原文内容
        payload_content = payload['records'][0]['fields']['推文原文内容']['text']
        print(f"   - 载荷中的推文原文内容长度: {len(payload_content)}")
        print(f"   - 载荷中的推文原文内容预览: '{payload_content[:100]}...'")
        
        try:
            print(f"   🌐 发送请求...")
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            print(f"   - 响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   - API响应: code={result.get('code')}, msg={result.get('msg', 'N/A')}")
                
                if result.get('code') == 0:
                    created_records = result.get('data', {}).get('records', [])
                    print(f"   ✅ 记录创建成功")
                    print(f"   - 创建记录数: {len(created_records)}")
                    
                    # 检查创建的记录
                    if created_records:
                        first_record = created_records[0]
                        record_id = first_record.get('record_id')
                        print(f"   - 记录ID: {record_id}")
                        
                        # 立即查询刚创建的记录
                        print(f"\n9. 验证创建的记录:")
                        query_url = f"{sync_config['feishu']['base_url']}/bitable/v1/apps/{FEISHU_CONFIG['spreadsheet_token']}/tables/{FEISHU_CONFIG['table_id']}/records/{record_id}"
                        print(f"   - 查询URL: {query_url}")
                        
                        query_response = requests.get(query_url, headers=headers, timeout=30)
                        print(f"   - 查询响应状态码: {query_response.status_code}")
                        
                        if query_response.status_code == 200:
                            query_result = query_response.json()
                            print(f"   - 查询API响应: code={query_result.get('code')}")
                            
                            if query_result.get('code') == 0:
                                record_data = query_result.get('data', {}).get('record', {})
                                fields = record_data.get('fields', {})
                                
                                print(f"   📊 查询到的记录字段:")
                                for field_name, field_value in fields.items():
                                    if field_name == '推文原文内容':
                                        content = field_value if isinstance(field_value, str) else str(field_value)
                                        print(f"     - {field_name}: '{content[:50]}...' (长度: {len(content)})")
                                        
                                        if len(content) == 0:
                                            print(f"     ❌ 推文原文内容为空！")
                                            print(f"     💡 问题确认: 数据在飞书API调用后丢失")
                                        else:
                                            print(f"     ✅ 推文原文内容正常")
                                    else:
                                        print(f"     - {field_name}: {field_value}")
                            else:
                                print(f"   ❌ 查询记录失败: {query_result.get('msg')}")
                        else:
                            print(f"   ❌ 查询记录请求失败: HTTP {query_response.status_code}")
                else:
                    print(f"   ❌ 记录创建失败: {result.get('msg')}")
                    print(f"   - 错误详情: {result}")
            else:
                print(f"   ❌ API请求失败: HTTP {response.status_code}")
                print(f"   - 响应内容: {response.text[:500]}...")
        except Exception as e:
            print(f"   ❌ API请求异常: {e}")
            import traceback
            print(f"   - 详细错误: {traceback.format_exc()}")
        
        print(f"\n🎉 测试完成")

if __name__ == '__main__':
    test_feishu_api_call()