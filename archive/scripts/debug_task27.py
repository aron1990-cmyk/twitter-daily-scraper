#!/usr/bin/env python3
from web_app import app, db, SystemConfig
import json

def debug_task_manager_config():
    """调试任务管理器的用户ID配置"""
    
    with app.app_context():
        # 手动加载配置
        from web_app import load_config_from_database, init_task_manager
        load_config_from_database()
        init_task_manager()
        
        # 获取配置
        configs = SystemConfig.query.all()
        config_dict = {cfg.key: cfg.value for cfg in configs}
        
        print("=== 任务管理器配置调试 ===")
        
        # 检查ADS_POWER_CONFIG
        from web_app import ADS_POWER_CONFIG
        print(f"\n1. ADS_POWER_CONFIG内容:")
        for key, value in ADS_POWER_CONFIG.items():
            print(f"   {key}: {value}")
        
        # 检查user_ids设置
        user_ids = ADS_POWER_CONFIG.get('user_ids', [ADS_POWER_CONFIG['user_id']])
        print(f"\n2. 任务管理器使用的用户ID池:")
        print(f"   user_ids: {user_ids}")
        
        # 检查multi_user_ids配置
        multi_user_ids_config = config_dict.get('adspower_multi_user_ids', '')
        print(f"\n3. 数据库中的多用户ID配置:")
        print(f"   adspower_multi_user_ids: '{multi_user_ids_config}'")
        
        if multi_user_ids_config:
            multi_ids = [uid.strip() for uid in multi_user_ids_config.split('\n') if uid.strip()]
            print(f"   解析后的多用户ID列表: {multi_ids}")
        else:
            print(f"   未配置多用户ID")
        
        # 检查任务管理器实例
        from web_app import task_manager
        print(f"\n4. 当前任务管理器状态:")
        print(f"   available_user_ids: {task_manager.available_user_ids}")
        print(f"   user_id_pool: {task_manager.user_id_pool}")
        print(f"   max_concurrent_tasks: {task_manager.max_concurrent_tasks}")
        
        # 模拟获取用户ID
        print(f"\n5. 模拟获取用户ID:")
        available_id = task_manager.get_available_user_id()
        print(f"   获取到的用户ID: {available_id}")
        
        if available_id:
            # 归还用户ID
            task_manager.return_user_id(available_id)
            print(f"   已归还用户ID: {available_id}")

if __name__ == "__main__":
    debug_task_manager_config()