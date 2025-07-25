#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新AdsPower配置脚本
"""

import sqlite3

def update_adspower_config():
    """更新AdsPower配置"""
    try:
        conn = sqlite3.connect('instance/twitter_scraper.db')
        cursor = conn.cursor()
        
        # 更新用户ID为正确的值
        cursor.execute('UPDATE system_config SET value = ? WHERE key = ?', ('k11p9ypc', 'adspower_user_id'))
        
        # 如果记录不存在，则插入
        cursor.execute('INSERT OR IGNORE INTO system_config (key, value) VALUES (?, ?)', ('adspower_user_id', 'k11p9ypc'))
        
        conn.commit()
        
        # 查询所有AdsPower相关配置
        cursor.execute("SELECT key, value FROM system_config WHERE key LIKE '%adspower%'")
        configs = cursor.fetchall()
        
        print('更新后的AdsPower配置:')
        for key, value in configs:
            print(f'{key}: {value}')
        
        conn.close()
        print('\n✅ AdsPower配置更新成功！')
        
    except Exception as e:
        print(f'❌ 更新配置失败: {e}')

if __name__ == '__main__':
    update_adspower_config()