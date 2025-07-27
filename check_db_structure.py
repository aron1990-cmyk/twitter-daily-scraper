#!/usr/bin/env python3
import sqlite3

def check_database_structure():
    conn = sqlite3.connect('twitter_scraper.db')
    cursor = conn.cursor()
    
    # 检查tweet_data表结构
    print('tweet_data表字段:')
    cursor.execute('PRAGMA table_info(tweet_data)')
    columns = cursor.fetchall()
    for col in columns:
        print(f'  {col[1]} ({col[2]})')
    
    # 检查所有任务的数据分布
    print('\n各任务的推文数量:')
    cursor.execute('SELECT task_id, COUNT(*) FROM tweet_data GROUP BY task_id ORDER BY task_id')
    results = cursor.fetchall()
    for r in results:
        print(f'  任务{r[0]}: {r[1]}条')
    
    # 检查任务5的数据
    print('\n任务5的推文数据:')
    cursor.execute('SELECT COUNT(*) FROM tweet_data WHERE task_id = 5')
    total = cursor.fetchone()[0]
    print(f'  总数: {total}')
    
    # 检查synced_to_feishu字段的状态
    if total > 0:
        cursor.execute('SELECT COUNT(*) FROM tweet_data WHERE task_id = 5 AND synced_to_feishu = 1')
        synced = cursor.fetchone()[0]
        print(f'  已同步到飞书: {synced}')
        print(f'  同步率: {synced/total*100:.1f}%')
    else:
        print('  没有数据，可能任务还未完成或数据存储在其他位置')
    
    conn.close()

if __name__ == '__main__':
    check_database_structure()