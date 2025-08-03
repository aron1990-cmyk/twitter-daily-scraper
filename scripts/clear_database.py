#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库清理脚本
用于清除所有任务数据库内容
"""

import os
import sys
import sqlite3
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def get_database_path():
    """获取数据库文件路径"""
    # 尝试多个可能的数据库路径
    possible_paths = [
        project_root / 'instance' / 'twitter_scraper.db',
        project_root / 'twitter_scraper.db',
        project_root / 'data' / 'twitter_scraper.db'
    ]
    
    for path in possible_paths:
        if path.exists():
            return str(path)
    
    # 如果都不存在，返回默认路径
    return str(project_root / 'instance' / 'twitter_scraper.db')

def backup_database(db_path):
    """备份数据库"""
    if not os.path.exists(db_path):
        print(f"⚠️  数据库文件不存在: {db_path}")
        return None
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{db_path}.backup_{timestamp}"
    
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ 数据库已备份到: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ 备份失败: {e}")
        return None

def get_table_info(cursor):
    """获取数据库表信息"""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    table_info = {}
    for table in tables:
        table_name = table[0]
        if table_name != 'sqlite_sequence':  # 跳过系统表
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            table_info[table_name] = count
    
    return table_info

def clear_database(db_path, confirm=True):
    """清理数据库"""
    if not os.path.exists(db_path):
        print(f"⚠️  数据库文件不存在: {db_path}")
        return False
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取清理前的表信息
        print("\n📊 清理前的数据统计:")
        before_info = get_table_info(cursor)
        total_records = 0
        for table_name, count in before_info.items():
            print(f"  {table_name}: {count} 条记录")
            total_records += count
        
        if total_records == 0:
            print("\n✅ 数据库已经是空的，无需清理")
            conn.close()
            return True
        
        # 安全确认
        if confirm:
            print(f"\n⚠️  即将清除 {total_records} 条记录，此操作不可逆！")
            response = input("确认清除所有数据？(输入 'YES' 确认): ")
            if response != 'YES':
                print("❌ 操作已取消")
                conn.close()
                return False
        
        print("\n🧹 开始清理数据库...")
        
        # 禁用外键约束
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # 清理主要数据表
        tables_to_clear = [
            'tweet_data',
            'scraping_task', 
            'twitter_influencer',
            'system_config',
            'user_data'
        ]
        
        cleared_tables = []
        for table_name in tables_to_clear:
            try:
                # 检查表是否存在
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                if cursor.fetchone():
                    cursor.execute(f"DELETE FROM {table_name}")
                    cleared_count = cursor.rowcount
                    if cleared_count > 0:
                        print(f"  ✅ 清理 {table_name}: {cleared_count} 条记录")
                        cleared_tables.append(table_name)
                    else:
                        print(f"  ℹ️  {table_name}: 表为空")
                else:
                    print(f"  ⚠️  表 {table_name} 不存在")
            except Exception as e:
                print(f"  ❌ 清理 {table_name} 失败: {e}")
        
        # 重置自增ID
        print("\n🔄 重置自增ID...")
        try:
            cursor.execute("DELETE FROM sqlite_sequence")
            print("  ✅ 自增ID已重置")
        except Exception as e:
            print(f"  ⚠️  重置自增ID失败: {e}")
        
        # 重新启用外键约束
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # 提交更改
        conn.commit()
        
        # 清理后的统计
        print("\n📊 清理后的数据统计:")
        after_info = get_table_info(cursor)
        remaining_records = 0
        for table_name, count in after_info.items():
            if count > 0:
                print(f"  {table_name}: {count} 条记录")
                remaining_records += count
        
        if remaining_records == 0:
            print("  ✅ 所有数据已清理完成")
        
        # 优化数据库
        print("\n🔧 优化数据库...")
        cursor.execute("VACUUM")
        print("  ✅ 数据库优化完成")
        
        conn.close()
        
        print(f"\n🎉 数据库清理完成！")
        print(f"   清理的表: {', '.join(cleared_tables)}")
        print(f"   清理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 清理数据库失败: {e}")
        return False

def main():
    """主函数"""
    print("🗄️  Twitter采集系统 - 数据库清理工具")
    print("=" * 50)
    
    # 获取数据库路径
    db_path = get_database_path()
    print(f"📍 数据库路径: {db_path}")
    
    # 检查是否需要跳过确认（用于自动化脚本）
    skip_confirm = '--force' in sys.argv or '-f' in sys.argv
    
    # 备份数据库
    if not skip_confirm:
        print("\n💾 创建数据库备份...")
        backup_path = backup_database(db_path)
        if not backup_path:
            print("❌ 备份失败，为安全起见，停止清理操作")
            return False
    
    # 清理数据库
    success = clear_database(db_path, confirm=not skip_confirm)
    
    if success:
        print("\n✅ 数据库清理成功完成！")
        return True
    else:
        print("\n❌ 数据库清理失败")
        return False

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  操作被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生未预期的错误: {e}")
        sys.exit(1)