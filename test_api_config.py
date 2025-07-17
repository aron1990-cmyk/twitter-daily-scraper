#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AdsPower API配置功能测试脚本
测试新的主机和端口分离配置功能
"""

import requests
import json
import time

def test_config_page():
    """测试配置页面是否正常加载"""
    print("\n🔍 测试配置页面加载...")
    try:
        response = requests.get('http://127.0.0.1:8086/config', timeout=10)
        if response.status_code == 200:
            content = response.text
            # 检查新的配置字段是否存在
            required_fields = [
                'adspower_api_host',
                'adspower_api_port', 
                'adspower_api_url_display',
                'request_interval',
                'user_switch_interval',
                'user_rotation_enabled'
            ]
            
            missing_fields = []
            for field in required_fields:
                if f'id="{field}"' not in content:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"❌ 配置页面缺少字段: {missing_fields}")
                return False
            else:
                print("✅ 配置页面包含所有新字段")
                return True
        else:
            print(f"❌ 配置页面加载失败，状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 配置页面测试失败: {e}")
        return False

def test_api_config_update():
    """测试API配置更新功能"""
    print("\n🔍 测试API配置更新...")
    try:
        # 测试数据
        test_data = {
            'config_type': 'adspower',
            'adspower_api_host': 'test.adspower.net',
            'adspower_api_port': '60325',
            'adspower_user_id': 'test_user_123',
            'adspower_multi_user_ids': 'user1\nuser2\nuser3',
            'max_concurrent_tasks': '3',
            'task_timeout': '1200',
            'browser_startup_delay': '3.5',
            'request_interval': '1.5',
            'user_switch_interval': '45',
            'user_rotation_enabled': 'on'
        }
        
        response = requests.post(
            'http://127.0.0.1:8086/update_config',
            data=test_data,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ 配置更新请求成功")
            return True
        else:
            print(f"❌ 配置更新失败，状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 配置更新测试失败: {e}")
        return False

def test_api_installation_check():
    """测试AdsPower安装检测API"""
    print("\n🔍 测试AdsPower安装检测API...")
    try:
        test_data = {
            'api_host': 'local.adspower.net',
            'api_port': '50325',
            'api_url': 'http://local.adspower.net:50325'
        }
        
        response = requests.post(
            'http://127.0.0.1:8086/api/check_adspower_installation',
            json=test_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 安装检测API响应: {result.get('message', 'Unknown')}")
            return True
        else:
            print(f"❌ 安装检测API失败，状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 安装检测API测试失败: {e}")
        return False

def test_api_connection_test():
    """测试AdsPower连接测试API"""
    print("\n🔍 测试AdsPower连接测试API...")
    try:
        test_data = {
            'api_host': 'local.adspower.net',
            'api_port': '50325',
            'api_url': 'http://local.adspower.net:50325',
            'user_id': 'test_user'
        }
        
        response = requests.post(
            'http://127.0.0.1:8086/api/test_adspower_connection',
            json=test_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 连接测试API响应: {result.get('message', 'Unknown')}")
            return True
        else:
            print(f"❌ 连接测试API失败，状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 连接测试API测试失败: {e}")
        return False

def test_config_persistence():
    """测试配置持久化"""
    print("\n🔍 测试配置持久化...")
    try:
        # 先更新配置
        test_data = {
            'config_type': 'adspower',
            'adspower_api_host': 'persist.test.net',
            'adspower_api_port': '12345',
            'adspower_user_id': 'persist_user',
            'max_concurrent_tasks': '5'
        }
        
        # 更新配置
        update_response = requests.post(
            'http://127.0.0.1:8086/update_config',
            data=test_data,
            timeout=10
        )
        
        if update_response.status_code != 200:
            print("❌ 配置更新失败")
            return False
        
        time.sleep(1)  # 等待配置保存
        
        # 重新加载配置页面检查是否保存
        config_response = requests.get('http://127.0.0.1:8086/config', timeout=10)
        if config_response.status_code == 200:
            content = config_response.text
            if 'persist.test.net' in content and '12345' in content:
                print("✅ 配置持久化成功")
                return True
            else:
                print("❌ 配置未正确保存")
                return False
        else:
            print("❌ 无法重新加载配置页面")
            return False
    except Exception as e:
        print(f"❌ 配置持久化测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始AdsPower API配置功能测试")
    print("=" * 50)
    
    tests = [
        ("配置页面加载", test_config_page),
        ("API配置更新", test_api_config_update),
        ("安装检测API", test_api_installation_check),
        ("连接测试API", test_api_connection_test),
        ("配置持久化", test_config_persistence)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 测试: {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} - 通过")
            else:
                print(f"❌ {test_name} - 失败")
        except Exception as e:
            print(f"❌ {test_name} - 异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！AdsPower API配置功能正常工作")
    else:
        print(f"⚠️  有 {total - passed} 个测试失败，请检查相关功能")
    
    return passed == total

if __name__ == '__main__':
    main()