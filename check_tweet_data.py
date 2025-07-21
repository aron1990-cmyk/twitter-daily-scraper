import sqlite3

conn = sqlite3.connect('twitter_scraper.db')
cursor = conn.cursor()

# 检查推文数据样例
cursor.execute('SELECT username, content, publish_time, likes, comments, retweets, hashtags FROM tweet_data LIMIT 5')
rows = cursor.fetchall()

print('📊 数据库中的推文样例:')
for i, row in enumerate(rows, 1):
    username, content, publish_time, likes, comments, retweets, hashtags = row
    print(f'{i}. 用户: {username}')
    print(f'   内容: {content[:50]}...')
    print(f'   时间: {publish_time}')
    print(f'   点赞: {likes}, 评论: {comments}, 转发: {retweets}')
    print(f'   标签: {hashtags}')
    print()

# 检查空值情况
cursor.execute('''
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN content IS NULL OR content = '' THEN 1 ELSE 0 END) as empty_content,
        SUM(CASE WHEN username IS NULL OR username = '' THEN 1 ELSE 0 END) as empty_username,
        SUM(CASE WHEN publish_time IS NULL OR publish_time = '' THEN 1 ELSE 0 END) as empty_time,
        SUM(CASE WHEN likes IS NULL THEN 1 ELSE 0 END) as null_likes,
        SUM(CASE WHEN comments IS NULL THEN 1 ELSE 0 END) as null_comments,
        SUM(CASE WHEN retweets IS NULL THEN 1 ELSE 0 END) as null_retweets
    FROM tweet_data
''')
stats = cursor.fetchone()

print('🔍 数据完整性统计:')
print(f'总推文数: {stats[0]}')
print(f'空内容: {stats[1]}')
print(f'空用户名: {stats[2]}')
print(f'空时间: {stats[3]}')
print(f'空点赞数: {stats[4]}')
print(f'空评论数: {stats[5]}')
print(f'空转发数: {stats[6]}')

conn.close()