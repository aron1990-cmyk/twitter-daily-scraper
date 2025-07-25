import sqlite3
import json

conn = sqlite3.connect('instance/twitter_scraper.db')
cursor = conn.cursor()

cursor.execute('SELECT target_accounts FROM scraping_task WHERE id = 1')
result = cursor.fetchone()

print(f'原始数据: {result[0]}')
print(f'原始数据类型: {type(result[0])}')
print(f'原始数据长度: {len(result[0])}')

try:
    accounts = json.loads(result[0])
    print(f'解析后: {accounts}')
    print(f'账号数量: {len(accounts)}')
    for i, acc in enumerate(accounts):
        print(f'账号{i+1}: "{acc}" (长度: {len(acc)})')
except Exception as e:
    print(f'JSON解析错误: {e}')

conn.close()