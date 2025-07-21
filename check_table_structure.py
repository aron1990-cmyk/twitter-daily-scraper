import sqlite3

conn = sqlite3.connect('twitter_scraper.db')
cursor = conn.cursor()

# 检查表结构
cursor.execute('PRAGMA table_info(tweet_data)')
columns = cursor.fetchall()
print('表结构:')
for col in columns:
    print(f'  {col[1]} ({col[2]})')

# 检查总体同步状态
cursor.execute('SELECT COUNT(*) as total, SUM(CASE WHEN synced_to_feishu = 1 THEN 1 ELSE 0 END) as synced FROM tweet_data')
result = cursor.fetchone()
print(f'\n总推文数: {result[0]}, 已同步: {result[1]}, 同步率: {result[1]/result[0]*100:.1f}%')

conn.close()