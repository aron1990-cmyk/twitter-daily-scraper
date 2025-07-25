#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复用户ID配置
"""

from web_app import app, db, SystemConfig

def fix_user_id_config():
    """修复AdsPower用户ID配置"""
    
    with app.app_context():
        print("=== 修复AdsPower用户ID配置 ===")
        
        # 正确的用户ID（从check_user_profiles.py的结果得知）
        correct_user_id = 'k11p9ypc'
        
        # 更新主要用户ID
        config = SystemConfig.query.filter_by(key='adspower_user_id').first()
        if config:
            old_value = config.value
            config.value = correct_user_id
            print(f"更新主要用户ID: {old_value} -> {correct_user_id}")
        else:
            config = SystemConfig(key='adspower_user_id', value=correct_user_id)
            db.session.add(config)
            print(f"创建主要用户ID配置: {correct_user_id}")
        
        # 更新多用户ID配置
        multi_config = SystemConfig.query.filter_by(key='adspower_multi_user_ids').first()
        if multi_config:
            old_value = multi_config.value
            multi_config.value = correct_user_id
            print(f"更新多用户ID配置: {old_value} -> {correct_user_id}")
        else:
            multi_config = SystemConfig(key='adspower_multi_user_ids', value=correct_user_id)
            db.session.add(multi_config)
            print(f"创建多用户ID配置: {correct_user_id}")
        
        # 提交更改
        db.session.commit()
        print("✅ 配置更新完成")
        
        # 验证更新
        print("\n=== 验证配置 ===")
        configs = SystemConfig.query.filter(SystemConfig.key.like('%adspower%user%')).all()
        for cfg in configs:
            print(f"{cfg.key}: {cfg.value}")

if __name__ == "__main__":
    fix_user_id_config()