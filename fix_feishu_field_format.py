#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复飞书字段格式问题
检查字段类型并使用正确的格式
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

def fix_feishu_field_format():
    """修复飞书字段格式问题"""
    print("🔧 修复飞书字段格式问题")
    print("=" * 50)
    
    with app.app_context():
        # 1. 检查飞书配置
        print("\n1. 检查飞书配置:")
        if not FEISHU_CONFIG.get('enabled'):
            print("   ❌ 飞书同步未启用")
            return
        
        print(f"   ✅ 飞书同步已启用")
        
        # 2. 初始化云同步管理器
        print("\n2. 初始化云同步管理器:")
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
        
        # 3. 获取访问令牌
        print("\n3. 获取飞书访问令牌:")
        access_token = sync_manager.get_feishu_access_token()
        if not access_token:
            print("   ❌ 访问令牌获取失败")
            return
        
        print(f"   ✅ 访问令牌获取成功")
        
        # 4. 获取详细的表格字段信息
        print("\n4. 获取详细的表格字段信息:")
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
                    print(f"   ✅ 字段信息获取成功")
                    print(f"   - 字段数量: {len(fields_data)}")
                    
                    # 详细分析每个字段的类型
                    field_types = {}
                    print(f"\n   📊 字段详细信息:")
                    for field in fields_data:
                        field_name = field.get('field_name')
                        field_type = field.get('type')
                        field_id = field.get('field_id')
                        
                        field_types[field_name] = field_type
                        print(f"     - {field_name}: 类型={field_type}, ID={field_id}")
                        
                        # 特别关注可能有问题的字段
                        if field_name in ['推文原文内容', '话题标签（Hashtag）', '类型标签']:
                            print(f"       ⭐ 重点字段: {field_name} -> 类型: {field_type}")
                    
                    # 5. 根据字段类型构建正确的数据格式
                    print("\n5. 根据字段类型构建正确的数据格式:")
                    
                    # 获取测试数据
                    tweet = TweetData.query.order_by(TweetData.id.desc()).first()
                    if not tweet:
                        print("   ❌ 没有找到推文数据")
                        return
                    
                    print(f"   - 使用推文 ID: {tweet.id}")
                    print(f"   - 内容长度: {len(tweet.content or '')}")
                    
                    # 构建正确格式的记录
                    def format_field_value(field_name, value, field_type):
                        """根据字段类型格式化字段值"""
                        if field_type == 1:  # 文本
                            return str(value) if value is not None else ''
                        elif field_type == 2:  # 数字
                            return int(value) if value is not None else 0
                        elif field_type == 3:  # 单选
                            return str(value) if value is not None else ''
                        elif field_type == 4:  # 多选
                            return [str(value)] if value else []
                        elif field_type == 5:  # 日期时间
                            return int(value) if value is not None else 0
                        elif field_type == 15:  # 超链接
                            return str(value) if value is not None else ''
                        elif field_type == 19:  # 多行文本
                            return str(value) if value is not None else ''
                        else:
                            # 默认作为字符串处理
                            return str(value) if value is not None else ''
                    
                    # 准备数据
                    test_data = {
                        '推文原文内容': tweet.content or '',
                        '发布时间': int(datetime.now().timestamp()),
                        '作者（账号）': tweet.username or '',
                        '推文链接': tweet.link or '',
                        '话题标签（Hashtag）': '',  # 空字符串
                        '类型标签': '',  # 空字符串
                        '评论': tweet.comments or 0,
                        '点赞': tweet.likes or 0,
                        '转发': tweet.retweets or 0,
                        '创建时间': int(datetime.now().timestamp())
                    }
                    
                    # 构建飞书格式的记录
                    record_fields = {}
                    for field_name, value in test_data.items():
                        if field_name in field_types:
                            field_type = field_types[field_name]
                            formatted_value = format_field_value(field_name, value, field_type)
                            record_fields[field_name] = formatted_value
                            
                            print(f"     - {field_name}: {formatted_value} (类型: {field_type})")
                            
                            if field_name == '推文原文内容':
                                print(f"       📝 推文内容长度: {len(str(formatted_value))}")
                                print(f"       📝 推文内容预览: '{str(formatted_value)[:50]}...'")
                    
                    # 6. 测试新格式的API调用
                    print("\n6. 测试新格式的API调用:")
                    record = {
                        'fields': record_fields
                    }
                    
                    url = f"{sync_config['feishu']['base_url']}/bitable/v1/apps/{FEISHU_CONFIG['spreadsheet_token']}/tables/{FEISHU_CONFIG['table_id']}/records/batch_create"
                    payload = {
                        'records': [record]
                    }
                    
                    print(f"   - 创建URL: {url}")
                    print(f"   - 载荷大小: {len(str(payload))} 字符")
                    
                    # 检查载荷中的推文原文内容
                    payload_content = payload['records'][0]['fields'].get('推文原文内容', '')
                    print(f"   - 载荷中的推文原文内容长度: {len(str(payload_content))}")
                    print(f"   - 载荷中的推文原文内容预览: '{str(payload_content)[:100]}...'")
                    
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
                                
                                if created_records:
                                    record_id = created_records[0].get('record_id')
                                    print(f"   - 记录ID: {record_id}")
                                    
                                    # 验证创建的记录
                                    print(f"\n7. 验证创建的记录:")
                                    query_url = f"{sync_config['feishu']['base_url']}/bitable/v1/apps/{FEISHU_CONFIG['spreadsheet_token']}/tables/{FEISHU_CONFIG['table_id']}/records/{record_id}"
                                    
                                    query_response = requests.get(query_url, headers=headers, timeout=30)
                                    if query_response.status_code == 200:
                                        query_result = query_response.json()
                                        if query_result.get('code') == 0:
                                            record_data = query_result.get('data', {}).get('record', {})
                                            fields = record_data.get('fields', {})
                                            
                                            print(f"   📊 验证结果:")
                                            content_field = fields.get('推文原文内容', '')
                                            print(f"     - 推文原文内容: '{str(content_field)[:50]}...' (长度: {len(str(content_field))})")
                                            
                                            if len(str(content_field)) > 0:
                                                print(f"     ✅ 推文原文内容同步成功！")
                                                print(f"     🎉 问题已解决：使用正确的字段格式")
                                            else:
                                                print(f"     ❌ 推文原文内容仍然为空")
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
                else:
                    print(f"   ❌ 字段信息获取失败: {fields_result.get('msg')}")
            else:
                print(f"   ❌ 字段查询请求失败: HTTP {fields_response.status_code}")
        except Exception as e:
            print(f"   ❌ 字段查询异常: {e}")
        
        print(f"\n🎉 测试完成")

if __name__ == '__main__':
    fix_feishu_field_format()