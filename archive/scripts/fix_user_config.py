#!/usr/bin/env python3
from web_app import app, db, SystemConfig

def fix_adspower_user_config():
    """修复AdsPower用户配置，移除无效的用户ID"""
    
    with app.app_context():
        print("=== 修复AdsPower用户配置 ===")
        
        # 查找multi_user_ids配置
        config = SystemConfig.query.filter_by(key='adspower_multi_user_ids').first()
        
        if config:
            print(f"\n当前配置: {config.value}")
            
            # 解析当前配置
            current_ids = [uid.strip() for uid in config.value.split('\n') if uid.strip()]
            print(f"当前用户ID列表: {current_ids}")
            
            # 只保留有效的用户ID (k11p9ypc)
            valid_ids = ['k11p9ypc']
            new_config_value = '\n'.join(valid_ids)
            
            print(f"\n修复后的用户ID列表: {valid_ids}")
            print(f"新配置值: {new_config_value}")
            
            # 更新配置
            config.value = new_config_value
            db.session.commit()
            
            print(f"\n✅ 配置已更新")
            
            # 验证更新
            updated_config = SystemConfig.query.filter_by(key='adspower_multi_user_ids').first()
            print(f"验证更新后的配置: {updated_config.value}")
            
        else:
            print("\n❌ 未找到adspower_multi_user_ids配置")

if __name__ == "__main__":
    fix_adspower_user_config()