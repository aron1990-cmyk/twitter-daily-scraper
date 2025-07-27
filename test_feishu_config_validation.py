#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试飞书配置验证功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入web_app模块来修改全局配置
import web_app
from feishu_data_validator import FeishuDataValidator

def test_incomplete_config():
    """
    测试配置不完整的情况
    """
    print("\n" + "="*80)
    print("🧪 测试飞书配置验证功能")
    print("="*80)
    
    # 保存原始配置
    original_config = web_app.FEISHU_CONFIG.copy()
    
    # 测试1: 缺少app_id
    print("\n📋 测试1: 缺少app_id")
    web_app.FEISHU_CONFIG = {
        'app_secret': 'test_secret',
        'spreadsheet_token': 'test_token',
        'table_id': 'test_table_id',
        'enabled': True
    }
    
    try:
        validator1 = FeishuDataValidator()
        result1 = validator1.validate_sync_data(task_id=1)
        print(f"✅ 测试1结果: {result1}")
    except Exception as e:
        print(f"❌ 测试1异常: {e}")
    
    # 测试2: 缺少app_secret
    print("\n📋 测试2: 缺少app_secret")
    web_app.FEISHU_CONFIG = {
        'app_id': 'test_app_id',
        'spreadsheet_token': 'test_token',
        'table_id': 'test_table_id',
        'enabled': True
    }
    
    try:
        validator2 = FeishuDataValidator()
        result2 = validator2.validate_sync_data(task_id=1)
        print(f"✅ 测试2结果: {result2}")
    except Exception as e:
        print(f"❌ 测试2异常: {e}")
    
    # 测试3: 飞书功能未启用
    print("\n📋 测试3: 飞书功能未启用")
    web_app.FEISHU_CONFIG = {
        'app_id': 'test_app_id',
        'app_secret': 'test_secret',
        'spreadsheet_token': 'test_token',
        'table_id': 'test_table_id',
        'enabled': False
    }
    
    try:
        validator3 = FeishuDataValidator()
        result3 = validator3.validate_sync_data(task_id=1)
        print(f"✅ 测试3结果: {result3}")
    except Exception as e:
        print(f"❌ 测试3异常: {e}")
    
    # 测试4: 完整配置但无效的凭据
    print("\n📋 测试4: 完整配置但无效的凭据")
    web_app.FEISHU_CONFIG = {
        'app_id': 'invalid_app_id',
        'app_secret': 'invalid_secret',
        'spreadsheet_token': 'invalid_token',
        'table_id': 'invalid_table_id',
        'enabled': True
    }
    
    try:
        validator4 = FeishuDataValidator()
        result4 = validator4.validate_sync_data(task_id=1)
        print(f"✅ 测试4结果: {result4}")
    except Exception as e:
        print(f"❌ 测试4异常: {e}")
    
    # 恢复原始配置
    web_app.FEISHU_CONFIG = original_config
    
    print("\n" + "="*80)
    print("🎯 测试完成")
    print("="*80)

if __name__ == "__main__":
    test_incomplete_config()