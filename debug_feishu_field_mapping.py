#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书字段映射调试脚本
用于检查飞书表格的实际字段名称和数据映射问题
"""

import os
import sys
import json
import requests
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入Flask应用和数据库
from web_app import app, db, TweetData, ScrapingTask, FEISHU_CONFIG
from cloud_sync import CloudSyncManager

def debug_feishu_field_mapping():
    """调试飞书字段映射问题"""
    print("🔍 飞书字段映射调试")
    print("=" * 60)
    
    with app.app_context():
        # 1. 检查飞书配置
        print("\n1. 检查飞书配置:")
        print(f"   - 启用状态: {FEISHU_CONFIG.get('enabled')}")
        print(f"   - App ID: {FEISHU_CONFIG.get('app_id', '')[:8]}...")
        print(f"   - 表格Token: {FEISHU_CONFIG.get('spreadsheet_token', '')[:10]}...")
        print(f"   - 表格ID: {FEISHU_CONFIG.get('table_id')}")
        
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
        
        # 3. 获取飞书访问令牌
        print("\n3. 获取飞书访问令牌:")
        access_token = sync_manager.get_feishu_access_token()
        if not access_token:
            print("   ❌ 获取访问令牌失败")
            return
        print(f"   ✅ 访问令牌获取成功: {access_token[:20]}...")
        
        # 4. 获取飞书表格字段信息
        print("\n4. 获取飞书表格字段信息:")
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # 获取字段列表
        fields_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_CONFIG['spreadsheet_token']}/tables/{FEISHU_CONFIG['table_id']}/fields"
        print(f"   - 请求URL: {fields_url}")
        
        try:
            fields_response = requests.get(fields_url, headers=headers, timeout=30)
            print(f"   - 响应状态码: {fields_response.status_code}")
            
            if fields_response.status_code == 200:
                fields_result = fields_response.json()
                print(f"   - API响应: code={fields_result.get('code')}, msg={fields_result.get('msg', 'N/A')}")
                
                if fields_result.get('code') == 0:
                    fields_data = fields_result.get('data', {}).get('items', [])
                    print(f"   ✅ 成功获取 {len(fields_data)} 个字段")
                    
                    print("\n   📋 飞书表格字段详情:")
                    available_fields = {}
                    field_types = {}
                    
                    for field in fields_data:
                        field_name = field.get('field_name', '')
                        field_type = field.get('type', 0)
                        field_id = field.get('field_id', '')
                        
                        available_fields[field_name] = field_id
                        field_types[field_name] = field_type
                        
                        print(f"     - 字段名: '{field_name}'")
                        print(f"       ID: {field_id}")
                        print(f"       类型: {field_type} ({get_field_type_name(field_type)})")
                        print()
                    
                    # 5. 检查字段映射匹配情况
                    print("\n5. 检查字段映射匹配情况:")
                    expected_fields = [
                        '推文原文内容',
                        '作者（账号）',
                        '推文链接',
                        '话题标签（Hashtag）',
                        '类型标签',
                        '评论',
                        '点赞',
                        '转发',
                        '发布时间',
                        '创建时间'
                    ]
                    
                    print("   📊 期望字段 vs 实际字段:")
                    matched_fields = []
                    missing_fields = []
                    
                    for expected_field in expected_fields:
                        if expected_field in available_fields:
                            matched_fields.append(expected_field)
                            print(f"     ✅ '{expected_field}' - 匹配")
                        else:
                            missing_fields.append(expected_field)
                            print(f"     ❌ '{expected_field}' - 缺失")
                    
                    print(f"\n   📈 匹配统计:")
                    print(f"     - 匹配字段: {len(matched_fields)}/{len(expected_fields)}")
                    print(f"     - 匹配率: {len(matched_fields)/len(expected_fields)*100:.1f}%")
                    
                    if missing_fields:
                        print(f"\n   ⚠️ 缺失字段: {missing_fields}")
                        print("\n   💡 建议检查:")
                        print("     1. 飞书表格字段名称是否与代码中的映射一致")
                        print("     2. 字段名称是否包含特殊字符或空格")
                        print("     3. 是否需要更新字段映射逻辑")
                    
                    # 6. 获取joshwoodward任务数据进行测试
                    print("\n6. 获取joshwoodward任务数据:")
                    tasks = ScrapingTask.query.filter(ScrapingTask.name.like('%joshwoodward%')).all()
                    print(f"   - 找到 {len(tasks)} 个相关任务")
                    
                    if tasks:
                        latest_task = max(tasks, key=lambda t: t.id)
                        print(f"   - 选择最新任务: ID {latest_task.id}, 名称: {latest_task.name}")
                        
                        # 获取推文数据
                        tweets = TweetData.query.filter_by(task_id=latest_task.id).limit(3).all()
                        print(f"   - 获取前3条推文数据进行测试")
                        
                        if tweets:
                            print("\n   📝 测试数据映射:")
                            for i, tweet in enumerate(tweets, 1):
                                print(f"\n     推文 {i} (ID: {tweet.id}):")
                                
                                # 模拟数据映射
                                hashtags_str = ', '.join(json.loads(tweet.hashtags) if tweet.hashtags else [])
                                
                                test_data = {
                                    '推文原文内容': tweet.content or '',
                                    '作者（账号）': tweet.username or '',
                                    '推文链接': tweet.link or '',
                                    '话题标签（Hashtag）': hashtags_str,
                                    '类型标签': tweet.content_type or '',
                                    '评论': tweet.comments or 0,
                                    '点赞': tweet.likes or 0,
                                    '转发': tweet.retweets or 0
                                }
                                
                                for field_name, field_value in test_data.items():
                                    status = "✅" if field_name in available_fields else "❌"
                                    value_preview = str(field_value)[:30] + "..." if len(str(field_value)) > 30 else str(field_value)
                                    print(f"       {status} {field_name}: {value_preview}")
                        else:
                            print("   ⚠️ 没有找到推文数据")
                    else:
                        print("   ⚠️ 没有找到joshwoodward相关任务")
                    
                    # 7. 提供修复建议
                    print("\n7. 修复建议:")
                    if len(matched_fields) < len(expected_fields):
                        print("   🔧 字段映射问题修复建议:")
                        print("     1. 检查飞书表格中的实际字段名称")
                        print("     2. 更新代码中的字段映射以匹配飞书表格")
                        print("     3. 确保字段类型正确（文本、数字、日期等）")
                        
                        print("\n   📋 实际可用字段列表:")
                        for field_name in available_fields.keys():
                            print(f"     - '{field_name}'")
                    else:
                        print("   ✅ 字段映射完全匹配，问题可能在其他地方")
                        print("   💡 其他可能的问题:")
                        print("     1. 数据值格式问题")
                        print("     2. 飞书API权限问题")
                        print("     3. 网络连接问题")
                        print("     4. 数据同步逻辑问题")
                
                else:
                    print(f"   ❌ 获取字段信息失败: {fields_result.get('msg')}")
            else:
                print(f"   ❌ 请求失败: HTTP {fields_response.status_code}")
                print(f"   - 响应内容: {fields_response.text[:200]}...")
                
        except Exception as e:
            print(f"   ❌ 请求异常: {e}")
            import traceback
            print(f"   - 详细错误: {traceback.format_exc()}")

def get_field_type_name(field_type):
    """获取字段类型名称"""
    type_mapping = {
        1: "文本",
        2: "数字",
        3: "单选",
        4: "多选",
        5: "日期时间",
        7: "复选框",
        11: "人员",
        13: "电话号码",
        15: "超链接",
        17: "附件",
        18: "关联",
        19: "公式",
        20: "双向关联",
        21: "地理位置",
        22: "群组",
        1001: "创建时间",
        1002: "最后更新时间",
        1003: "创建人",
        1004: "修改人"
    }
    return type_mapping.get(field_type, f"未知类型({field_type})")

if __name__ == "__main__":
    debug_feishu_field_mapping()