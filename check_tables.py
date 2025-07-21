from web_app import app, db
import os

with app.app_context():
    print('数据库表:')
    for table in db.metadata.tables.values():
        print(f'- {table.name}')
    
    print('\n检查数据文件夹:')
    data_dir = './data'
    if os.path.exists(data_dir):
        print(f'数据文件夹存在: {data_dir}')
        for root, dirs, files in os.walk(data_dir):
            for file in files:
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)
                print(f'  {file_path} ({file_size} bytes)')
    else:
        print('数据文件夹不存在')
    
    print('\n检查日志文件:')
    log_files = ['scraping.log', 'app.log', 'twitter_scraper.log']
    for log_file in log_files:
        if os.path.exists(log_file):
            size = os.path.getsize(log_file)
            print(f'{log_file} 存在 ({size} bytes)')
        else:
            print(f'{log_file} 不存在')