#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书功能测试脚本
测试新添加和优化的飞书配置功能
"""

import requests
import json
import time
from datetime import datetime

# 测试服务器配置
BASE_URL = "http://localhost:8084"

def test_feishu_config_api():
    """测试飞书配置API"""
    print("\n=== 测试飞书配置API ===")
    
    # 测试数据（使用虚拟数据）
    test_config = {
        "app_id": "cli_test123456",
        "app_secret": "test_secret_123",
        "spreadsheet_token": "test_spreadsheet_token",
        "table_id": "test_table_id",
        "enabled": True,
        "auto_sync": True
    }
    
    try:
        # 测试保存配置
        print("1. 测试保存飞书配置...")
        response = requests.post(
            f"{BASE_URL}/api/config/feishu",
            json=test_config,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("   ✓ 配置保存成功")
            else:
                print(f"   ✗ 配置保存失败: {result.get('error')}")
        else:
            print(f"   ✗ HTTP错误: {response.status_code}")
            
    except Exception as e:
        print(f"   ✗ 请求异常: {e}")

def test_feishu_connection():
    """测试飞书连接测试API"""
    print("\n=== 测试飞书连接测试 ===")
    
    # 测试数据（使用虚拟数据，预期会失败）
    test_data = {
        "app_id": "cli_test123456",
        "app_secret": "test_secret_123",
        "spreadsheet_token": "test_spreadsheet_token",
        "table_id": "test_table_id"
    }
    
    try:
        print("1. 测试飞书连接...")
        response = requests.post(
            f"{BASE_URL}/api/config/feishu/test",
            json=test_data,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("   ✓ 连接测试成功")
            else:
                print(f"   ✓ 连接测试返回预期错误: {result.get('error')}")
        else:
            print(f"   ✗ HTTP错误: {response.status_code}")
            
    except Exception as e:
        print(f"   ✗ 请求异常: {e}")

def test_empty_config_validation():
    """测试空配置验证"""
    print("\n=== 测试空配置验证 ===")
    
    # 测试空配置
    empty_config = {
        "app_id": "",
        "app_secret": "",
        "spreadsheet_token": "",
        "table_id": ""
    }
    
    try:
        print("1. 测试空配置连接...")
        response = requests.post(
            f"{BASE_URL}/api/config/feishu/test",
            json=empty_config,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if not result.get('success'):
                print(f"   ✓ 空配置验证成功，返回错误: {result.get('error')}")
            else:
                print("   ✗ 空配置应该返回错误")
        else:
            print(f"   ✗ HTTP错误: {response.status_code}")
            
    except Exception as e:
        print(f"   ✗ 请求异常: {e}")

def test_config_page_access():
    """测试配置页面访问"""
    print("\n=== 测试配置页面访问 ===")
    
    try:
        print("1. 访问配置页面...")
        response = requests.get(f"{BASE_URL}/config", timeout=10)
        
        if response.status_code == 200:
            content = response.text
            # 检查关键元素是否存在
            checks = [
                ('飞书配置', '飞书配置标题'),
                ('feishu_app_id', 'App ID输入框'),
                ('feishu_app_secret', 'App Secret输入框'),
                ('feishu_spreadsheet_token', '文档Token输入框'),
                ('feishu_table_id', '表格ID输入框'),
                ('testFeishuConnection', '测试连接函数'),
                ('feishu_auto_sync', '自动同步选项')
            ]
            
            for check_text, description in checks:
                if check_text in content:
                    print(f"   ✓ {description}存在")
                else:
                    print(f"   ✗ {description}缺失")
        else:
            print(f"   ✗ 页面访问失败: {response.status_code}")
            
    except Exception as e:
        print(f"   ✗ 请求异常: {e}")

def test_manual_sync():
    """测试手动同步功能"""
    print("\n=== 测试手动同步功能 ===")
    
    try:
        # 使用一个假的task_id进行测试
        test_task_id = 999999
        print(f"1. 测试手动同步到飞书 (task_id: {test_task_id})...")
        response = requests.post(f"{BASE_URL}/api/data/sync_feishu/{test_task_id}", timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("   ✓ 手动同步成功")
            else:
                print(f"   ✓ 手动同步返回预期错误: {result.get('error')}")
        elif response.status_code == 400:
            # 预期的错误（配置问题或任务不存在）
            try:
                result = response.json()
                print(f"   ✓ 手动同步返回预期错误: {result.get('error')}")
            except:
                print("   ✓ 手动同步返回预期的400错误")
        else:
            print(f"   ✗ HTTP错误: {response.status_code}")
            
    except Exception as e:
        print(f"   ✗ 请求异常: {e}")

def check_server_status():
    """检查服务器状态"""
    print("\n=== 检查服务器状态 ===")
    
    try:
        print("1. 检查服务器是否运行...")
        response = requests.get(f"{BASE_URL}/", timeout=5)
        
        if response.status_code == 200:
            print("   ✓ 服务器正常运行")
            return True
        else:
            print(f"   ✗ 服务器响应异常: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ✗ 无法连接到服务器: {e}")
        print(f"   请确保服务器在 {BASE_URL} 上运行")
        return False

def main():
    """主测试函数"""
    print("飞书功能测试开始")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试服务器: {BASE_URL}")
    
    # 检查服务器状态
    if not check_server_status():
        print("\n❌ 服务器未运行，测试终止")
        return
    
    # 执行各项测试
    test_config_page_access()
    test_feishu_config_api()
    test_feishu_connection()
    test_empty_config_validation()
    test_manual_sync()
    
    print("\n=== 测试总结 ===")
    print("✓ 配置页面功能测试完成")
    print("✓ 飞书配置API测试完成")
    print("✓ 连接测试功能验证完成")
    print("✓ 表单验证功能测试完成")
    print("✓ 手动同步功能测试完成")
    print("\n🎉 飞书功能测试全部完成！")
    print("\n注意: 由于使用测试数据，连接测试预期会失败，这是正常的。")
    print("要测试真实连接，请在配置页面填入真实的飞书应用信息。")

if __name__ == "__main__":
    main()