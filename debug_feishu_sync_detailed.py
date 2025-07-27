#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细的飞书同步调试脚本
模拟完整的同步过程，找出数据丢失的具体原因
"""

import os
import sys
import json
import requests
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入Flask应用和数据库
from web_app import app, db, TweetData, ScrapingTask, FEISHU_CONFIG, classify_content_type
from cloud_sync import CloudSyncManager

def debug_detailed_feishu_sync():
    """详细调试飞书同步过程"""
    print("🔍 详细飞书同步调试")
    print("=" * 60)
    
    with app.app_context():
        # 1. 获取joshwoodward任务数据
        print("\n1. 获取joshwoodward任务数据:")
        task = ScrapingTask.query.filter_by(id=17).first()
        if not task:
            print("   ❌ 未找到任务ID 17")
            return
        
        print(f"   ✅ 找到任务: ID {task.id}, 名称: {task.name}")
        
        # 获取推文数据
        tweets = TweetData.query.filter_by(task_id=17).limit(2).all()  # 只取2条进行详细调试
        print(f"   ✅ 获取到 {len(tweets)} 条推文数据")
        
        if not tweets:
            print("   ❌ 没有推文数据")
            return
        
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
        print("   ✅ 云同步管理器初始化完成")
        
        # 3. 获取访问令牌
        print("\n3. 获取飞书访问令牌:")
        access_token = sync_manager.get_feishu_access_token()
        if not access_token:
            print("   ❌ 获取访问令牌失败")
            return
        print(f"   ✅ 访问令牌获取成功: {access_token[:20]}...")
        
        # 4. 准备数据（模拟web_app.py的逻辑）
        print("\n4. 准备数据（模拟web_app.py逻辑）:")
        data = []
        for i, tweet in enumerate(tweets):
            print(f"\n   处理推文 {i+1} (ID: {tweet.id}):")
            print(f"     - 原始内容: {tweet.content[:50] if tweet.content else '空'}...")
            print(f"     - 用户名: {tweet.username}")
            print(f"     - 点赞数: {tweet.likes}")
            print(f"     - 转发数: {tweet.retweets}")
            print(f"     - 评论数: {tweet.comments}")
            print(f"     - 链接: {tweet.link}")
            print(f"     - 标签: {tweet.hashtags}")
            
            # 使用用户设置的类型标签，如果为空则使用自动分类
            content_type = tweet.content_type or classify_content_type(tweet.content)
            print(f"     - 类型标签: {content_type}")
            
            # 处理标签
            hashtags_str = ', '.join(json.loads(tweet.hashtags) if tweet.hashtags else [])
            print(f"     - 处理后标签: {hashtags_str}")
            
            # 构建数据（按照web_app.py的逻辑）
            tweet_data = {
                '推文原文内容': tweet.content or '',
                '作者（账号）': tweet.username or '',
                '推文链接': tweet.link or '',
                '话题标签（Hashtag）': hashtags_str,
                '类型标签': content_type or '',
                '评论': tweet.comments or 0,
                '点赞': tweet.likes or 0,
                '转发': tweet.retweets or 0
            }
            
            print(f"     ✅ 数据映射完成:")
            for key, value in tweet_data.items():
                print(f"       - {key}: {value}")
            
            data.append(tweet_data)
        
        print(f"\n   ✅ 共准备 {len(data)} 条数据")
        
        # 5. 获取飞书表格字段信息
        print("\n5. 获取飞书表格字段信息:")
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        fields_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_CONFIG['spreadsheet_token']}/tables/{FEISHU_CONFIG['table_id']}/fields"
        fields_response = requests.get(fields_url, headers=headers, timeout=30)
        
        if fields_response.status_code == 200:
            fields_result = fields_response.json()
            if fields_result.get('code') == 0:
                fields_data = fields_result.get('data', {}).get('items', [])
                available_fields = {field.get('field_name', ''): field.get('field_id', '') for field in fields_data}
                field_types = {field.get('field_name', ''): field.get('type', 1) for field in fields_data}
                print(f"   ✅ 获取到 {len(available_fields)} 个字段")
            else:
                print(f"   ❌ 获取字段信息失败: {fields_result.get('msg')}")
                return
        else:
            print(f"   ❌ 请求失败: HTTP {fields_response.status_code}")
            return
        
        # 6. 模拟cloud_sync.py的数据处理逻辑
        print("\n6. 模拟cloud_sync.py数据处理:")
        records = []
        
        for idx, tweet in enumerate(data):
            print(f"\n   处理记录 {idx + 1}:")
            
            # 字段值格式化函数（来自cloud_sync.py）
            def format_field_value(field_name, value, field_type):
                """根据字段类型格式化字段值"""
                if field_type == 1:  # 文本字段
                    return str(value) if value is not None else ''
                elif field_type == 2:  # 数字字段
                    try:
                        if value is None or value == '':
                            return 0
                        return int(float(str(value)))
                    except (ValueError, TypeError):
                        return 0
                elif field_type == 5:  # 日期时间字段
                    if isinstance(value, (int, float)) and value > 0:
                        return int(value)
                    return 0
                else:
                    return str(value) if value is not None else ''
            
            # 构建所有可能的字段
            all_possible_fields = {
                '推文原文内容': format_field_value('推文原文内容', tweet.get('推文原文内容', ''), field_types.get('推文原文内容', 1)),
                '作者（账号）': format_field_value('作者（账号）', tweet.get('作者（账号）', ''), field_types.get('作者（账号）', 1)),
                '推文链接': format_field_value('推文链接', tweet.get('推文链接', ''), field_types.get('推文链接', 1)),
                '话题标签（Hashtag）': format_field_value('话题标签（Hashtag）', tweet.get('话题标签（Hashtag）', ''), field_types.get('话题标签（Hashtag）', 1)),
                '类型标签': format_field_value('类型标签', tweet.get('类型标签', ''), field_types.get('类型标签', 1)),
                '评论': format_field_value('评论', tweet.get('评论', 0), field_types.get('评论', 2)),
                '转发': format_field_value('转发', tweet.get('转发', 0), field_types.get('转发', 2)),
                '点赞': format_field_value('点赞', tweet.get('点赞', 0), field_types.get('点赞', 2))
            }
            
            # 只保留飞书表格中实际存在的字段
            record_fields = {}
            for field_name, field_value in all_possible_fields.items():
                if field_name in available_fields:
                    record_fields[field_name] = field_value
                    print(f"     ✅ 字段 '{field_name}': {field_value}")
                else:
                    print(f"     ❌ 跳过字段 '{field_name}' (不存在于飞书表格)")
            
            if record_fields:
                record = {'fields': record_fields}
                records.append(record)
                print(f"     ✅ 记录构建完成，包含 {len(record_fields)} 个字段")
            else:
                print(f"     ❌ 没有匹配的字段，跳过此记录")
        
        print(f"\n   ✅ 共构建 {len(records)} 条记录")
        
        # 7. 构建API请求载荷
        print("\n7. 构建API请求载荷:")
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_CONFIG['spreadsheet_token']}/tables/{FEISHU_CONFIG['table_id']}/records/batch_create"
        payload = {'records': records}
        
        print(f"   - 请求URL: {url}")
        print(f"   - 记录数量: {len(records)}")
        print(f"   - 载荷大小: {len(str(payload))} 字符")
        print(f"   - 载荷内容预览:")
        print(json.dumps(payload, ensure_ascii=False, indent=2)[:500] + "...")
        
        # 8. 发送API请求
        print("\n8. 发送飞书API请求:")
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            print(f"   - 响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   - API响应: code={result.get('code')}, msg={result.get('msg', 'N/A')}")
                
                if result.get('code') == 0:
                    created_records = result.get('data', {}).get('records', [])
                    print(f"   ✅ 成功创建 {len(created_records)} 条记录")
                    
                    # 显示创建的记录详情
                    print("\n   📋 创建的记录详情:")
                    for i, record in enumerate(created_records[:2]):  # 只显示前2条
                        print(f"     记录 {i+1}:")
                        print(f"       - 记录ID: {record.get('record_id')}")
                        fields = record.get('fields', {})
                        for field_name, field_value in fields.items():
                            print(f"       - {field_name}: {field_value}")
                else:
                    print(f"   ❌ API调用失败: {result.get('msg')}")
                    print(f"   - 完整响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            else:
                print(f"   ❌ HTTP请求失败: {response.status_code}")
                print(f"   - 响应内容: {response.text[:500]}...")
                
        except Exception as e:
            print(f"   ❌ 请求异常: {e}")
            import traceback
            print(f"   - 详细错误: {traceback.format_exc()}")
        
        # 9. 验证飞书表格中的数据
        print("\n9. 验证飞书表格中的数据:")
        try:
            # 获取表格记录
            records_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_CONFIG['spreadsheet_token']}/tables/{FEISHU_CONFIG['table_id']}/records"
            records_response = requests.get(records_url, headers=headers, params={'page_size': 5}, timeout=30)
            
            if records_response.status_code == 200:
                records_result = records_response.json()
                if records_result.get('code') == 0:
                    existing_records = records_result.get('data', {}).get('items', [])
                    print(f"   ✅ 表格中现有 {len(existing_records)} 条记录（显示前5条）")
                    
                    for i, record in enumerate(existing_records[:3]):
                        print(f"\n     记录 {i+1}:")
                        fields = record.get('fields', {})
                        for field_name, field_value in fields.items():
                            if field_value:  # 只显示非空字段
                                print(f"       - {field_name}: {field_value}")
                            else:
                                print(f"       - {field_name}: [空值]")
                else:
                    print(f"   ❌ 获取记录失败: {records_result.get('msg')}")
            else:
                print(f"   ❌ 请求失败: HTTP {records_response.status_code}")
                
        except Exception as e:
            print(f"   ❌ 验证异常: {e}")
        
        print("\n" + "=" * 60)
        print("🎯 调试总结:")
        print("   1. 检查字段映射是否正确")
        print("   2. 检查数据格式化是否正确")
        print("   3. 检查API请求是否成功")
        print("   4. 检查飞书表格中的实际数据")
        print("   5. 如果数据仍然为空，可能是飞书表格权限或配置问题")

if __name__ == "__main__":
    debug_detailed_feishu_sync()