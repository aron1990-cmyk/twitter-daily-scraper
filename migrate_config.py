#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置迁移脚本 - 将config.py中的AdsPower配置迁移到数据库
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_app import app, db, SystemConfig
from config import ADS_POWER_CONFIG, TWITTER_TARGETS, FILTER_CONFIG, OUTPUT_CONFIG, BROWSER_CONFIG, LOG_CONFIG, CLOUD_SYNC_CONFIG
import json

def migrate_adspower_config():
    """迁移AdsPower配置到数据库"""
    print("🔄 开始迁移AdsPower配置...")
    
    with app.app_context():
        # 确保数据库表存在
        db.create_all()
        
        # 迁移AdsPower基础配置
        configs_to_migrate = [
            # API配置
            ('adspower_api_url', ADS_POWER_CONFIG.get('local_api_url', 'http://local.adspower.net:50325'), 'AdsPower API地址'),
            ('adspower_api_host', 'local.adspower.net', 'AdsPower API主机'),
            ('adspower_api_port', '50325', 'AdsPower API端口'),
            
            # 用户配置
            ('adspower_user_id', ADS_POWER_CONFIG.get('user_id', ''), 'AdsPower用户ID'),
            ('adspower_group_id', ADS_POWER_CONFIG.get('group_id', ''), 'AdsPower分组ID'),
            ('adspower_multi_user_ids', '\n'.join(ADS_POWER_CONFIG.get('multi_user_ids', [])), '多用户ID列表'),
            
            # 并发配置
            ('max_concurrent_tasks', str(ADS_POWER_CONFIG.get('max_concurrent_tasks', 2)), '最大并发任务数'),
            ('task_timeout', str(ADS_POWER_CONFIG.get('task_timeout', 300)), '任务超时时间(秒)'),
            
            # 频率控制配置
            ('request_interval', str(ADS_POWER_CONFIG.get('request_interval', 2.0)), '请求间隔时间(秒)'),
            ('user_rotation_enabled', str(ADS_POWER_CONFIG.get('user_rotation_enabled', True)), '启用用户轮询'),
            ('user_switch_interval', str(ADS_POWER_CONFIG.get('user_switch_interval', 30)), '用户切换间隔(秒)'),
            ('api_retry_delay', str(ADS_POWER_CONFIG.get('api_retry_delay', 5.0)), 'API重试延迟(秒)'),
            ('browser_startup_delay', str(ADS_POWER_CONFIG.get('browser_startup_delay', 0.5)), '浏览器启动延迟(秒)'),
            
            # 连接配置
            ('adspower_timeout', str(ADS_POWER_CONFIG.get('timeout', 15)), '连接超时时间(秒)'),
            ('adspower_retry_count', str(ADS_POWER_CONFIG.get('retry_count', 2)), '重试次数'),
            ('adspower_retry_delay', str(ADS_POWER_CONFIG.get('retry_delay', 2)), '重试延迟(秒)'),
            ('adspower_health_check', str(ADS_POWER_CONFIG.get('health_check', True)), '启用健康检查'),
            ('adspower_headless', str(ADS_POWER_CONFIG.get('headless', False)), '无头模式'),
            ('adspower_window_visible', str(ADS_POWER_CONFIG.get('window_visible', True)), '窗口可见'),
            
            # Twitter目标配置
            ('twitter_target_accounts', json.dumps(TWITTER_TARGETS.get('accounts', []), ensure_ascii=False), 'Twitter目标账号列表'),
            ('twitter_target_keywords', json.dumps(TWITTER_TARGETS.get('keywords', []), ensure_ascii=False), 'Twitter目标关键词列表'),
            
            # 筛选配置
            ('filter_min_likes', str(FILTER_CONFIG.get('min_likes', 50)), '最小点赞数'),
            ('filter_min_comments', str(FILTER_CONFIG.get('min_comments', 10)), '最小评论数'),
            ('filter_min_retweets', str(FILTER_CONFIG.get('min_retweets', 20)), '最小转发数'),
            ('filter_keywords', json.dumps(FILTER_CONFIG.get('keywords_filter', []), ensure_ascii=False), '筛选关键词'),
            ('filter_max_tweets_per_target', str(FILTER_CONFIG.get('max_tweets_per_target', 8)), '每个目标最大抓取数'),
            ('filter_max_total_tweets', str(FILTER_CONFIG.get('max_total_tweets', 200)), '总最大抓取数'),
            ('filter_min_content_length', str(FILTER_CONFIG.get('min_content_length', 20)), '最小内容长度'),
            ('filter_max_content_length', str(FILTER_CONFIG.get('max_content_length', 1000)), '最大内容长度'),
            ('filter_max_age_hours', str(FILTER_CONFIG.get('max_age_hours', 72)), '最大时间范围(小时)'),
            
            # 输出配置
            ('output_data_dir', OUTPUT_CONFIG.get('data_dir', './data'), '数据目录'),
            ('output_excel_filename_format', OUTPUT_CONFIG.get('excel_filename_format', 'twitter_daily_{date}.xlsx'), 'Excel文件名格式'),
            ('output_sheet_name', OUTPUT_CONFIG.get('sheet_name', 'Twitter数据'), '工作表名称'),
            
            # 浏览器配置
            ('browser_headless', str(BROWSER_CONFIG.get('headless', False)), '浏览器无头模式'),
            ('browser_timeout', str(BROWSER_CONFIG.get('timeout', 8000)), '页面加载超时(毫秒)'),
            ('browser_wait_time', str(BROWSER_CONFIG.get('wait_time', 0.3)), '页面操作间隔(秒)'),
            ('browser_scroll_pause_time', str(BROWSER_CONFIG.get('scroll_pause_time', 0.3)), '滚动间隔(秒)'),
            ('browser_navigation_timeout', str(BROWSER_CONFIG.get('navigation_timeout', 10000)), '导航超时(毫秒)'),
            ('browser_load_state_timeout', str(BROWSER_CONFIG.get('load_state_timeout', 4000)), '加载状态超时(毫秒)'),
            ('browser_fast_mode', str(BROWSER_CONFIG.get('fast_mode', True)), '快速模式'),
            ('browser_skip_images', str(BROWSER_CONFIG.get('skip_images', True)), '跳过图片加载'),
            ('browser_disable_animations', str(BROWSER_CONFIG.get('disable_animations', True)), '禁用动画'),
            
            # 日志配置
            ('log_level', LOG_CONFIG.get('level', 'INFO'), '日志级别'),
            ('log_format', LOG_CONFIG.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'), '日志格式'),
            ('log_filename', LOG_CONFIG.get('filename', 'twitter_scraper.log'), '日志文件名'),
            
            # 云端同步配置
            ('google_sheets_enabled', str(CLOUD_SYNC_CONFIG.get('google_sheets', {}).get('enabled', False)), 'Google Sheets同步'),
            ('google_sheets_credentials_file', CLOUD_SYNC_CONFIG.get('google_sheets', {}).get('credentials_file', ''), 'Google凭证文件路径'),
            ('google_sheets_spreadsheet_id', CLOUD_SYNC_CONFIG.get('google_sheets', {}).get('spreadsheet_id', ''), 'Google表格ID'),
            ('google_sheets_worksheet_name', CLOUD_SYNC_CONFIG.get('google_sheets', {}).get('worksheet_name', 'Twitter数据'), 'Google工作表名称'),
        ]
        
        migrated_count = 0
        updated_count = 0
        
        for key, value, description in configs_to_migrate:
            existing_config = SystemConfig.query.filter_by(key=key).first()
            
            if existing_config:
                # 更新现有配置
                existing_config.value = value
                existing_config.description = description
                updated_count += 1
                print(f"✅ 更新配置: {key} = {value}")
            else:
                # 创建新配置
                new_config = SystemConfig(
                    key=key,
                    value=value,
                    description=description
                )
                db.session.add(new_config)
                migrated_count += 1
                print(f"➕ 新增配置: {key} = {value}")
        
        # 提交所有更改
        db.session.commit()
        
        print(f"\n🎉 配置迁移完成!")
        print(f"📊 新增配置: {migrated_count} 项")
        print(f"🔄 更新配置: {updated_count} 项")
        print(f"📝 总计配置: {migrated_count + updated_count} 项")
        
        return True

def verify_migration():
    """验证迁移结果"""
    print("\n🔍 验证迁移结果...")
    
    with app.app_context():
        configs = SystemConfig.query.all()
        config_dict = {cfg.key: cfg.value for cfg in configs}
        
        # 验证关键配置项
        key_configs = [
            'adspower_api_url',
            'adspower_user_id',
            'adspower_multi_user_ids',
            'max_concurrent_tasks',
            'request_interval',
            'user_rotation_enabled'
        ]
        
        print(f"\n📋 关键配置验证:")
        for key in key_configs:
            value = config_dict.get(key, '未找到')
            print(f"  {key}: {value}")
        
        print(f"\n📊 总配置数量: {len(configs)}")
        
        return len(configs) > 0

if __name__ == '__main__':
    print("🚀 开始配置迁移...")
    
    try:
        # 执行迁移
        if migrate_adspower_config():
            # 验证迁移
            if verify_migration():
                print("\n✅ 配置迁移成功完成!")
                print("\n📝 下一步:")
                print("  1. 更新web_app.py中的配置加载逻辑")
                print("  2. 删除config.py文件")
                print("  3. 测试功能")
                print("  4. 提交到GitHub")
            else:
                print("\n❌ 迁移验证失败!")
                sys.exit(1)
        else:
            print("\n❌ 配置迁移失败!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 迁移过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)