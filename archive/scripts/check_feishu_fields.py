#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查飞书表格字段映射
用于诊断字段匹配问题
"""

import json
import requests
from cloud_sync import CloudSyncManager

def check_feishu_fields():
    """检查飞书表格的实际字段"""
    print("🔍 检查飞书表格字段映射")
    print("=" * 50)
    
    try:
        # 加载飞书配置
        with open('feishu_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if not config.get('enabled'):
            print("❌ 飞书同步未启用")
            return
        
        print("✅ 飞书配置加载成功")
        print(f"   - App ID: {config['app_id'][:8]}...")
        print(f"   - 表格Token: {config['spreadsheet_token'][:10]}...")
        print(f"   - 表格ID: {config['table_id']}")
        
        # 初始化同步管理器
        feishu_config = {
            'feishu': {
                'app_id': config['app_id'],
                'app_secret': config['app_secret'],
                'base_url': 'https://open.feishu.cn/open-apis'
            }
        }
        sync_manager = CloudSyncManager(feishu_config)
        
        # 获取访问令牌
        print("\n🔑 获取飞书访问令牌...")
        access_token = sync_manager.get_feishu_access_token()
        if not access_token:
            print("❌ 无法获取访问令牌")
            return
        print("✅ 访问令牌获取成功")
        
        # 获取表格字段信息
        print("\n📋 获取飞书表格字段信息...")
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        fields_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{config['spreadsheet_token']}/tables/{config['table_id']}/fields"
        print(f"   - 请求URL: {fields_url}")
        
        response = requests.get(fields_url, headers=headers, timeout=30)
        print(f"   - 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   - API响应: code={result.get('code')}, msg={result.get('msg', 'N/A')}")
            
            if result.get('code') == 0:
                fields_data = result.get('data', {}).get('items', [])
                print(f"\n✅ 飞书表格字段信息 (共{len(fields_data)}个字段):")
                
                for i, field in enumerate(fields_data, 1):
                    field_name = field.get('field_name', '')
                    field_type = field.get('type', '')
                    field_id = field.get('field_id', '')
                    print(f"   {i:2d}. {field_name} (类型: {field_type}, ID: {field_id})")
                
                # 检查程序中的字段映射
                print("\n🔄 检查程序字段映射:")
                program_fields = {
                    '推文原文内容': '推文内容',
                    '发布时间': '发布时间',
                    '作者（账号）': '作者账号',
                    '推文链接': '推文链接',
                    '话题标签（Hashtag）': '话题标签',
                    '类型标签': '类型标签',
                    '评论': '评论数',
                    '点赞': '点赞数',
                    '转发': '转发数',
                    '创建时间': '创建时间'
                }
                
                available_fields = [field.get('field_name') for field in fields_data]
                
                print("\n📊 字段匹配分析:")
                matched_fields = []
                unmatched_fields = []
                
                for prog_field, desc in program_fields.items():
                    if prog_field in available_fields:
                        matched_fields.append(prog_field)
                        print(f"   ✅ {prog_field} -> 匹配")
                    else:
                        unmatched_fields.append(prog_field)
                        print(f"   ❌ {prog_field} -> 不匹配")
                
                print(f"\n📈 匹配统计:")
                print(f"   - 匹配字段: {len(matched_fields)}/{len(program_fields)}")
                print(f"   - 匹配率: {len(matched_fields)/len(program_fields)*100:.1f}%")
                
                if unmatched_fields:
                    print(f"\n⚠️ 不匹配的字段: {unmatched_fields}")
                    print("\n💡 建议的字段映射修正:")
                    for field in unmatched_fields:
                        # 寻找相似的字段
                        similar_fields = []
                        for avail_field in available_fields:
                            if any(keyword in avail_field for keyword in field.split('（')[0].split()):
                                similar_fields.append(avail_field)
                        
                        if similar_fields:
                            print(f"   - '{field}' 可能对应: {similar_fields}")
                        else:
                            print(f"   - '{field}' 未找到相似字段")
                
                print("\n🎯 飞书表格中的所有字段:")
                for field in available_fields:
                    print(f"   - {field}")
                    
            else:
                print(f"❌ 获取字段信息失败: {result.get('msg')}")
        else:
            print(f"❌ 请求失败: HTTP {response.status_code}")
            print(f"   - 响应内容: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ 检查过程中发生错误: {e}")
        import traceback
        print(f"   - 错误详情: {traceback.format_exc()}")

if __name__ == '__main__':
    check_feishu_fields()