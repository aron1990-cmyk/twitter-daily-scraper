#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查飞书配置脚本
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web_app import app, db, SystemConfig, FEISHU_CONFIG, load_config_from_database

def check_feishu_config():
    """检查飞书配置"""
    print("🔍 检查飞书配置")
    print("=" * 50)
    
    with app.app_context():
        # 1. 检查数据库中的飞书配置
        print("\n1. 数据库中的飞书配置:")
        feishu_configs = SystemConfig.query.filter(
            SystemConfig.key.like('feishu_%')
        ).all()
        
        if not feishu_configs:
            print("   ❌ 数据库中没有飞书配置")
        else:
            for config in feishu_configs:
                value_display = config.value[:10] + '...' if len(config.value) > 10 else config.value
                print(f"   - {config.key}: {value_display}")
        
        # 2. 检查加载前的FEISHU_CONFIG
        print("\n2. 加载前的FEISHU_CONFIG:")
        for key, value in FEISHU_CONFIG.items():
            value_display = str(value)[:10] + '...' if len(str(value)) > 10 else str(value)
            print(f"   - {key}: {value_display}")
        
        # 3. 加载配置
        print("\n3. 加载配置...")
        load_config_from_database()
        
        # 4. 检查加载后的FEISHU_CONFIG
        print("\n4. 加载后的FEISHU_CONFIG:")
        for key, value in FEISHU_CONFIG.items():
            value_display = str(value)[:10] + '...' if len(str(value)) > 10 else str(value)
            print(f"   - {key}: {value_display}")
        
        # 5. 检查配置完整性
        print("\n5. 配置完整性检查:")
        required_fields = ['app_id', 'app_secret', 'spreadsheet_token', 'table_id']
        missing_fields = []
        
        for field in required_fields:
            if not FEISHU_CONFIG.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            print(f"   ❌ 缺少必要配置: {missing_fields}")
        else:
            print("   ✅ 所有必要配置都已设置")
        
        # 6. 如果配置不完整，提供设置建议
        if missing_fields:
            print("\n6. 设置建议:")
            print("   请通过Web界面的'系统配置'页面设置以下飞书配置:")
            for field in missing_fields:
                print(f"   - feishu_{field}")
            print("   或者直接在数据库中插入配置记录")
    
    print("\n" + "=" * 50)
    print("🔍 飞书配置检查完成")

if __name__ == '__main__':
    check_feishu_config()