import sqlite3

conn = sqlite3.connect('instance/twitter_scraper.db')
cursor = conn.cursor()

# 检查最近的任务
cursor.execute('SELECT * FROM scraping_task ORDER BY id DESC LIMIT 10')
results = cursor.fetchall()
print('最近10个任务:')
for r in results:
    print(f'ID: {r[0]}, 名称: {r[1]}, 状态: {r[8]}, 创建时间: {r[9]}')

# 检查任务总数
cursor.execute('SELECT COUNT(*) FROM scraping_task')
count = cursor.fetchone()[0]
print(f'\n任务总数: {count}')

# 检查各状态的任务数量
cursor.execute('SELECT status, COUNT(*) FROM scraping_task GROUP BY status')
status_counts = cursor.fetchall()
print('\n各状态任务数量:')
for status, count in status_counts:
    print(f'{status}: {count}')

conn.close()