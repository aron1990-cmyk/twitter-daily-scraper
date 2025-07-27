#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Web应用的飞书配置加载
验证FEISHU_CONFIG是否正确从数据库加载
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_app import app, FEISHU_CONFIG, SystemConfig, load_config_from_database

def test_feishu_config():
    """测试飞书配置加载"""
    with app.app_context():
        print("🔧 测试Web应用飞书配置加载")
        print("=" * 50)
        
        # 1. 检查数据库中的飞书配置
        print("\n📊 数据库中的飞书配置:")
        feishu_keys = ['feishu_app_id', 'feishu_app_secret', 'feishu_spreadsheet_token', 'feishu_table_id', 'feishu_enabled', 'feishu_auto_sync']
        
        db_config = {}
        for key in feishu_keys:
            config = SystemConfig.query.filter_by(key=key).first()
            value = config.value if config else 'N/A'
            db_config[key] = value
            print(f"   - {key}: {value}")
        
        # 2. 检查当前FEISHU_CONFIG
        print("\n🔧 当前FEISHU_CONFIG:")
        for key, value in FEISHU_CONFIG.items():
            print(f"   - {key}: {value}")
        
        # 3. 重新加载配置
        print("\n🔄 重新加载配置...")
        load_config_from_database()
        
        # 4. 检查重新加载后的FEISHU_CONFIG
        print("\n🔧 重新加载后的FEISHU_CONFIG:")
        for key, value in FEISHU_CONFIG.items():
            print(f"   - {key}: {value}")
        
        # 5. 验证配置完整性
        print("\n✅ 配置验证:")
        required_fields = ['app_id', 'app_secret', 'spreadsheet_token', 'table_id']
        missing_fields = [field for field in required_fields if not FEISHU_CONFIG.get(field)]
        
        if missing_fields:
            print(f"   ❌ 配置不完整，缺少字段: {', '.join(missing_fields)}")
        else:
            print(f"   ✅ 基本配置完整")
        
        print(f"   - 飞书同步启用: {FEISHU_CONFIG.get('enabled', False)}")
        print(f"   - 自动同步启用: {FEISHU_CONFIG.get('auto_sync', False)}")
        
        # 6. 检查配置一致性
        print("\n🔍 配置一致性检查:")
        inconsistencies = []
        
        if db_config.get('feishu_app_id') != FEISHU_CONFIG.get('app_id'):
            inconsistencies.append('app_id')
        if db_config.get('feishu_app_secret') != FEISHU_CONFIG.get('app_secret'):
            inconsistencies.append('app_secret')
        if db_config.get('feishu_spreadsheet_token') != FEISHU_CONFIG.get('spreadsheet_token'):
            inconsistencies.append('spreadsheet_token')
        if db_config.get('feishu_table_id') != FEISHU_CONFIG.get('table_id'):
            inconsistencies.append('table_id')
        
        # 检查布尔值配置
        db_enabled = db_config.get('feishu_enabled', '').lower() == 'true'
        config_enabled = FEISHU_CONFIG.get('enabled', False)
        if db_enabled != config_enabled:
            inconsistencies.append('enabled')
        
        db_auto_sync = db_config.get('feishu_auto_sync', '').lower() == 'true'
        config_auto_sync = FEISHU_CONFIG.get('auto_sync', False)
        if db_auto_sync != config_auto_sync:
            inconsistencies.append('auto_sync')
        
        if inconsistencies:
            print(f"   ❌ 发现配置不一致: {', '.join(inconsistencies)}")
            return False
        else:
            print(f"   ✅ 配置一致")
            return True

if __name__ == '__main__':
    success = test_feishu_config()
    if success:
        print("\n🎉 飞书配置测试通过！")
    else:
        print("\n❌ 飞书配置测试失败！")