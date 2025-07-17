#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务3自动同步功能最终验证脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_app import app, db, load_config_from_database, FEISHU_CONFIG, SystemConfig, TweetData
from sqlalchemy import text

def test_task3_auto_sync():
    """测试任务3的自动同步功能"""
    with app.app_context():
        print("=== 任务3自动同步功能验证 ===")
        
        # 加载配置
        load_config_from_database()
        
        # 检查配置状态
        feishu_enabled = FEISHU_CONFIG.get('enabled', False)
        auto_sync_config = SystemConfig.query.filter_by(key='feishu_auto_sync').first()
        auto_sync_enabled = auto_sync_config and auto_sync_config.value.lower() in ['true', '1']
        
        print(f"飞书配置启用状态: {feishu_enabled}")
        print(f"自动同步配置: {auto_sync_enabled}")
        
        # 检查配置完整性
        required_fields = ['app_id', 'app_secret', 'spreadsheet_token', 'table_id']
        missing_fields = [field for field in required_fields if not FEISHU_CONFIG.get(field)]
        
        if missing_fields:
            print(f"❌ 飞书配置不完整，缺少字段: {', '.join(missing_fields)}")
            return False
        else:
            print("✅ 飞书配置完整")
        
        # 查询任务3的推文数据
        result = db.session.execute(text("""
            SELECT COUNT(*) as total_tweets, 
                   COUNT(CASE WHEN synced_to_feishu = 1 THEN 1 END) as synced_tweets 
            FROM tweet_data WHERE task_id = 3
        """)).fetchone()
        
        total_tweets = result.total_tweets
        synced_tweets = result.synced_tweets
        
        print(f"\n任务3推文统计:")
        print(f"  总推文数: {total_tweets}")
        print(f"  已同步数: {synced_tweets}")
        print(f"  同步率: {(synced_tweets/total_tweets*100):.1f}%" if total_tweets > 0 else "  同步率: 0%")
        
        # 验证自动同步功能
        if feishu_enabled and auto_sync_enabled and not missing_fields:
            if total_tweets > 0 and synced_tweets == total_tweets:
                print("\n✅ 任务3自动同步功能验证成功！")
                print("   - 飞书配置已启用且完整")
                print("   - 自动同步已启用")
                print("   - 所有推文数据已成功同步到飞书")
                return True
            elif total_tweets > 0 and synced_tweets < total_tweets:
                print("\n⚠️ 部分数据未同步，可能需要手动触发同步")
                return False
            elif total_tweets == 0:
                print("\n⚠️ 任务3暂无推文数据")
                return False
        else:
            print("\n❌ 自动同步配置不完整")
            return False

if __name__ == '__main__':
    success = test_task3_auto_sync()
    sys.exit(0 if success else 1)