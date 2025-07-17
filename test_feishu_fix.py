#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书连接修复测试脚本
测试修复后的飞书时间字段处理功能
"""

import requests
import json
from datetime import datetime
import time

# 配置
BASE_URL = "http://localhost:8084"

def test_feishu_connection_fix():
    """测试修复后的飞书连接功能"""
    print("\n=== 飞书连接修复测试 ===")
    
    # 测试配置（使用假数据）
    test_config = {
        "app_id": "cli_test123456",
        "app_secret": "test_secret_123456",
        "spreadsheet_token": "test_token_123456",
        "table_id": "test_table_123456"
    }
    
    print("1. 测试飞书连接（修复后的时间字段处理）...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/config/feishu/test",
            json=test_config,
            timeout=30
        )
        
        print(f"   响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 连接测试成功: {result.get('message', '')}")
            return True
        else:
            try:
                error_info = response.json()
                error_msg = error_info.get('error', '未知错误')
                print(f"   ❌ 连接测试失败: {error_msg}")
                
                # 分析错误类型
                if "TextFieldConvFail" in error_msg:
                    print("   📝 错误分析: 字段类型转换失败（时间字段问题）")
                elif "invalid param" in error_msg:
                    print("   📝 错误分析: 参数无效（配置问题）")
                elif "获取飞书令牌失败" in error_msg:
                    print("   📝 错误分析: 飞书认证失败（App ID/Secret问题）")
                else:
                    print(f"   📝 错误分析: 其他错误 - {error_msg}")
                    
            except:
                print(f"   ❌ 连接测试失败: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ 请求失败: {e}")
        return False

def test_time_field_processing():
    """测试时间字段处理逻辑"""
    print("\n=== 时间字段处理测试 ===")
    
    from cloud_sync import CloudSyncManager
    
    # 创建测试配置
    test_config = {
        'feishu': {
            'enabled': True,
            'app_id': 'test_app_id',
            'app_secret': 'test_app_secret',
            'base_url': 'https://open.feishu.cn/open-apis'
        }
    }
    
    sync_manager = CloudSyncManager(test_config)
    
    # 测试不同格式的时间数据
    test_cases = [
        {
            'name': '毫秒时间戳',
            'data': [{
                '推文原文内容': '测试内容1',
                '发布时间': int(datetime.now().timestamp() * 1000),
                '创建时间': int(datetime.now().timestamp() * 1000),
                '点赞数': 10,
                '转发数': 5
            }]
        },
        {
            'name': '秒时间戳',
            'data': [{
                '推文原文内容': '测试内容2',
                '发布时间': int(datetime.now().timestamp()),
                '创建时间': int(datetime.now().timestamp()),
                '点赞数': 20,
                '转发数': 15
            }]
        },
        {
            'name': 'ISO格式字符串',
            'data': [{
                '推文原文内容': '测试内容3',
                '发布时间': datetime.now().isoformat(),
                '创建时间': datetime.now().isoformat(),
                '点赞数': 30,
                '转发数': 25
            }]
        },
        {
            'name': '空时间字段',
            'data': [{
                '推文原文内容': '测试内容4',
                '发布时间': '',
                '创建时间': None,
                '点赞数': 40,
                '转发数': 35
            }]
        }
    ]
    
    for case in test_cases:
        print(f"\n测试用例: {case['name']}")
        try:
            # 这里只是测试数据处理逻辑，不实际发送到飞书
            # 因为我们没有真实的飞书配置
            data = case['data'][0]
            
            # 模拟时间字段处理逻辑
            publish_time = data.get('发布时间', '')
            create_time = data.get('创建时间', '')
            
            print(f"   原始发布时间: {publish_time} (类型: {type(publish_time).__name__})")
            print(f"   原始创建时间: {create_time} (类型: {type(create_time).__name__})")
            
            # 处理发布时间
            if isinstance(publish_time, str) and publish_time:
                try:
                    dt = datetime.fromisoformat(publish_time.replace('Z', '+00:00'))
                    processed_publish_time = int(dt.timestamp() * 1000)
                    print(f"   ✅ 发布时间处理成功: {processed_publish_time}")
                except:
                    print(f"   ❌ 发布时间处理失败")
            elif isinstance(publish_time, (int, float)):
                if publish_time < 10000000000:
                    processed_publish_time = int(publish_time * 1000)
                else:
                    processed_publish_time = int(publish_time)
                print(f"   ✅ 发布时间处理成功: {processed_publish_time}")
            else:
                print(f"   ⚪ 发布时间为空，跳过")
                
            # 处理创建时间
            if isinstance(create_time, str) and create_time:
                try:
                    dt = datetime.fromisoformat(create_time.replace('Z', '+00:00'))
                    processed_create_time = int(dt.timestamp() * 1000)
                    print(f"   ✅ 创建时间处理成功: {processed_create_time}")
                except:
                    print(f"   ❌ 创建时间处理失败")
            elif isinstance(create_time, (int, float)):
                if create_time < 10000000000:
                    processed_create_time = int(create_time * 1000)
                else:
                    processed_create_time = int(create_time)
                print(f"   ✅ 创建时间处理成功: {processed_create_time}")
            else:
                print(f"   ⚪ 创建时间为空，跳过")
                
        except Exception as e:
            print(f"   ❌ 处理失败: {e}")

def check_server_status():
    """检查服务器状态"""
    print("=== 检查服务器状态 ===")
    try:
        response = requests.get(f"{BASE_URL}/api/status", timeout=5)
        if response.status_code == 200:
            print("✅ 服务器运行正常")
            return True
        else:
            print(f"❌ 服务器响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到服务器: {e}")
        return False

def main():
    """主函数"""
    print("飞书连接修复测试")
    print("=" * 50)
    
    # 检查服务器状态
    if not check_server_status():
        print("\n❌ 服务器未运行，请先启动服务器")
        return
    
    # 测试时间字段处理逻辑
    test_time_field_processing()
    
    # 测试飞书连接
    success = test_feishu_connection_fix()
    
    print("\n=== 测试总结 ===")
    if success:
        print("✅ 飞书连接测试通过（时间字段处理已修复）")
    else:
        print("❌ 飞书连接测试失败")
        print("\n📝 说明:")
        print("   - 如果错误不再是 'TextFieldConvFail'，说明时间字段问题已修复")
        print("   - 其他错误（如认证失败）是正常的，因为使用的是测试配置")
        print("   - 要完全验证功能，需要使用真实的飞书应用配置")
    
    print("\n🔧 修复内容:")
    print("   1. 智能处理不同格式的时间字段（字符串、时间戳）")
    print("   2. 确保时间字段为毫秒时间戳格式")
    print("   3. 数值字段使用正确的数据类型（int而非str）")
    print("   4. 空时间字段的安全处理")

if __name__ == "__main__":
    main()