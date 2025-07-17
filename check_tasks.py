from web_app import app, db, ScrapingTask

with app.app_context():
    tasks = ScrapingTask.query.all()
    print('所有任务状态:')
    for t in tasks:
        print(f'ID: {t.id}, 名称: {t.name}, 状态: {t.status}')