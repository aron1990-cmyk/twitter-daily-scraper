#!/usr/bin/env python3
import sqlite3

def check_adspower_config():
    """检查数据库中的AdsPower配置"""
    try:
        conn = sqlite3.connect('instance/twitter_scraper.db')
        cursor = conn.cursor()
        
        # 查询AdsPower相关配置
        cursor.execute("SELECT key, value FROM system_config WHERE key LIKE '%adspower%'")
        configs = cursor.fetchall()
        
        print('AdsPower配置:')
        for key, value in configs:
            print(f'{key}: {value}')
            
        # 如果没有配置，插入默认配置
        if not configs:
            print('\n数据库中没有AdsPower配置，插入默认配置...')
            default_configs = [
                ('adspower_api_host', 'local.adspower.net'),
                ('adspower_api_port', '50325'),
                ('adspower_user_id', 'k11p9ypc'),
                ('adspower_enabled', 'true')
            ]
            
            for key, value in default_configs:
                cursor.execute("INSERT OR REPLACE INTO system_config (key, value) VALUES (?, ?)", (key, value))
            
            conn.commit()
            print('默认配置已插入')
            
        conn.close()
        
    except Exception as e:
        print(f'错误: {e}')

if __name__ == '__main__':
    check_adspower_config()