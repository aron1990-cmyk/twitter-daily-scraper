# -*- coding: utf-8 -*-
"""
AdsPower 配置文件
包含所有AdsPower相关的配置信息
"""

# AdsPower API 配置
ADSPOWER_CONFIG = {
    # API 主机地址
    'api_host': '127.0.0.1',
    
    # API 端口
    'api_port': 50325,
    
    # API Key
    'api_key': 'bbe17be66473a96fad115ef70b5c170c',
    
    # 多用户ID列表
    'user_ids': [
        'k12q6fj7',
        'k12q6cbi'
    ],
    
    # 无头模式设置
    'headless': False,
    
    # 其他配置
    'max_concurrent_tasks': 2,
    'task_timeout': 900,
    'browser_startup_delay': 2,
    'health_check': True
}

# 构建完整的API URL
def get_api_url():
    """获取完整的API URL"""
    return f"http://{ADSPOWER_CONFIG['api_host']}:{ADSPOWER_CONFIG['api_port']}"

# 获取配置信息的便捷函数
def get_config():
    """获取AdsPower配置"""
    config = ADSPOWER_CONFIG.copy()
    config['local_api_url'] = get_api_url()
    return config

# 获取主用户ID
def get_primary_user_id():
    """获取主用户ID（第一个用户ID）"""
    user_ids = ADSPOWER_CONFIG['user_ids']
    return user_ids[0] if user_ids else ''

# 获取所有用户ID
def get_all_user_ids():
    """获取所有用户ID列表"""
    return ADSPOWER_CONFIG['user_ids'].copy()