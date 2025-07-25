#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试AdsPower浏览器启动
"""

import sqlite3
from ads_browser_launcher import AdsPowerLauncher

def test_adspower_start():
    """测试AdsPower浏览器启动"""
    try:
        # 从数据库加载配置
        conn = sqlite3.connect('instance/twitter_scraper.db')
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM system_config WHERE key LIKE '%adspower%'")
        configs = cursor.fetchall()
        
        config_dict = {}
        for key, value in configs:
            config_dict[key] = value
        
        conn.close()
        
        print('当前AdsPower配置:')
        for key, value in config_dict.items():
            print(f'  {key}: {value}')
        
        # 构建启动器配置
        launcher_config = {
            'local_api_url': config_dict.get('adspower_api_url', 'http://127.0.0.1:50325'),
            'user_id': config_dict.get('adspower_user_id', 'k11p9ypc')
        }
        
        print(f'\n使用配置: {launcher_config}')
        
        # 创建启动器
        launcher = AdsPowerLauncher(launcher_config)
        
        print('\n测试AdsPower浏览器启动...')
        user_id = config_dict.get('adspower_user_id', 'k11p9ypc')
        print(f'使用用户ID: {user_id}')
        
        # 启动浏览器
        browser_info = launcher.start_browser(user_id)
        
        if browser_info:
            print(f'✅ 浏览器启动成功!')
            print(f'浏览器信息: {browser_info}')
        else:
            print('❌ 浏览器启动失败')
            
    except Exception as e:
        print(f'❌ 测试失败: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_adspower_start()