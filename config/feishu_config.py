# -*- coding: utf-8 -*-
"""
飞书配置文件
包含所有飞书相关的配置信息
"""

# 飞书配置
FEISHU_CONFIG = {
    # 飞书应用ID
    'app_id': 'cli_a8f94354c178900b',
    
    # 飞书应用密钥
    'app_secret': 'HGQGTQyvr2QsWVmPMdY8Oe7A67J3ihVV',
    
    # 飞书表格Token
    'spreadsheet_token': 'V862biEswatwnRsGalochUI6n6d',
    
    # 飞书数据表ID
    'table_id': 'tblicDZl35dn2vZ9',
    
    # 是否启用飞书同步 (0=禁用, 1=启用)
    'enabled': 1,
    
    # 是否启用异步同步 (0=禁用, 1=启用)
    'async_enabled': 1,
    
    # 其他配置
    'base_url': 'https://open.feishu.cn/open-apis',
    'auto_sync': True,
    'async_max_workers': 3,
    'async_max_queue_size': 100,
    'async_max_retries': 3,
    'async_priority': 5,
    'sync_interval': 300
}

# 获取配置信息的便捷函数
def get_config():
    """获取飞书配置"""
    return FEISHU_CONFIG.copy()

# 检查飞书是否启用
def is_enabled():
    """检查飞书同步是否启用"""
    return FEISHU_CONFIG['enabled'] == 1

# 检查异步同步是否启用
def is_async_enabled():
    """检查异步同步是否启用"""
    return FEISHU_CONFIG['async_enabled'] == 1

# 获取飞书应用认证信息
def get_auth_config():
    """获取飞书应用认证配置"""
    return {
        'app_id': FEISHU_CONFIG['app_id'],
        'app_secret': FEISHU_CONFIG['app_secret'],
        'base_url': FEISHU_CONFIG['base_url']
    }

# 获取飞书表格配置
def get_table_config():
    """获取飞书表格配置"""
    return {
        'spreadsheet_token': FEISHU_CONFIG['spreadsheet_token'],
        'table_id': FEISHU_CONFIG['table_id']
    }

# 更新配置
def update_config(new_config):
    """更新飞书配置"""
    global FEISHU_CONFIG
    FEISHU_CONFIG.update(new_config)
    return True