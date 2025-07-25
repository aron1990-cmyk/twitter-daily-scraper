#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化飞书配置到数据库
确保飞书同步功能默认启用
"""

import json
from web_app import app, SystemConfig, db

def init_feishu_config():
    """初始化飞书配置到数据库"""
    with app.app_context():
        # 读取feishu_config.json文件
        try:
            with open('feishu_config.json', 'r', encoding='utf-8') as f:
                feishu_config = json.load(f)
        except FileNotFoundError:
            print("❌ feishu_config.json文件不存在")
            return False
        
        # 默认飞书配置（启用状态）
        default_feishu_configs = {
            'feishu_app_id': feishu_config.get('app_id', ''),
            'feishu_app_secret': feishu_config.get('app_secret', ''),
            'feishu_spreadsheet_token': feishu_config.get('spreadsheet_token', ''),
            'feishu_table_id': feishu_config.get('table_id', ''),
            'feishu_enabled': 'true',  # 默认启用
            'feishu_auto_sync': 'true',  # 默认启用自动同步
            'sync_interval': '300'  # 5分钟同步间隔
        }
        
        print("🔧 正在初始化飞书配置...")
        
        # 更新或创建配置记录到数据库
        for key, value in default_feishu_configs.items():
            config = SystemConfig.query.filter_by(key=key).first()
            if config:
                # 如果配置已存在，只更新enabled状态确保默认启用
                if key == 'feishu_enabled':
                    config.value = 'true'
                    config.updated_at = db.func.now()
                    print(f"✅ 更新配置: {key} = true")
                elif not config.value or config.value in ['', 'your_feishu_app_id', 'your_feishu_app_secret', 'your_spreadsheet_token', 'your_table_id']:
                    # 如果是占位符值，则更新为新值
                    config.value = str(value)
                    config.updated_at = db.func.now()
                    print(f"✅ 更新配置: {key} = {value}")
                else:
                    print(f"⏭️  保持现有配置: {key} = {config.value}")
            else:
                # 创建新配置
                config = SystemConfig(
                    key=key,
                    value=str(value),
                    description=f'飞书配置: {key}'
                )
                db.session.add(config)
                print(f"✅ 创建配置: {key} = {value}")
        
        try:
            db.session.commit()
            print("\n🎉 飞书配置初始化完成！")
            print("📋 配置摘要:")
            print("   - 飞书同步: 已启用")
            print("   - 自动同步: 已启用")
            print("   - 同步间隔: 5分钟")
            print("\n💡 提示: 请在Web界面的配置页面中填写正确的飞书应用信息")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"❌ 配置保存失败: {e}")
            return False

def check_feishu_config():
    """检查当前飞书配置状态"""
    with app.app_context():
        print("\n📊 当前飞书配置状态:")
        feishu_configs = SystemConfig.query.filter(SystemConfig.key.like('feishu_%')).all()
        
        if not feishu_configs:
            print("   ❌ 未找到飞书配置")
            return False
        
        for config in feishu_configs:
            if config.key == 'feishu_enabled':
                status = "✅ 已启用" if config.value.lower() == 'true' else "❌ 未启用"
                print(f"   - {config.key}: {config.value} {status}")
            else:
                # 隐藏敏感信息
                if 'secret' in config.key.lower():
                    display_value = config.value[:10] + '...' if config.value and len(config.value) > 10 else config.value
                else:
                    display_value = config.value
                print(f"   - {config.key}: {display_value}")
        
        return True

if __name__ == '__main__':
    print("🚀 飞书配置初始化工具")
    print("=" * 50)
    
    # 检查当前配置
    check_feishu_config()
    
    # 初始化配置
    print("\n" + "=" * 50)
    if init_feishu_config():
        print("\n" + "=" * 50)
        # 再次检查配置
        check_feishu_config()
    else:
        print("\n❌ 初始化失败")