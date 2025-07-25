#!/usr/bin/env python3
import sqlite3

def check_task_status():
    conn = sqlite3.connect('twitter_scraper.db')
    cursor = conn.cursor()
    
    # 查询最近的任务
    cursor.execute('SELECT id, name, status, created_at FROM tasks ORDER BY id DESC LIMIT 5')
    tasks = cursor.fetchall()
    
    print('Recent tasks:')
    for task in tasks:
        print(f'ID: {task[0]}, Name: {task[1]}, Status: {task[2]}, Created: {task[3]}')
    
    # 查询任务ID为2的详细信息
    cursor.execute('SELECT * FROM tasks WHERE id = 2')
    task_2 = cursor.fetchone()
    
    if task_2:
        print('\nTask ID 2 details:')
        print(f'ID: {task_2[0]}')
        print(f'Name: {task_2[1]}')
        print(f'Status: {task_2[2]}')
        print(f'Target Accounts: {task_2[3]}')
        print(f'Max Tweets: {task_2[4]}')
        print(f'Created At: {task_2[5]}')
        print(f'Updated At: {task_2[6]}')
    
    conn.close()

if __name__ == '__main__':
    check_task_status()