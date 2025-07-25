import sqlite3

conn = sqlite3.connect('twitter_scraper.db')
cursor = conn.cursor()

# 获取所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('数据库中的表:', tables)

# 检查每个表的结构
for table in tables:
    table_name = table[0]
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    print(f'{table_name}表结构:', columns)
    
    # 如果是任务相关的表，显示内容
    if 'task' in table_name.lower():
        cursor.execute(f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT 5")
        rows = cursor.fetchall()
        print(f'{table_name}最新5条记录:', rows)

conn.close()