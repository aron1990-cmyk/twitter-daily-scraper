#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import json

def check_joshwoodward_data():
    """检查joshwoodward任务的推文数据"""
    conn = sqlite3.connect('/Users/aron/twitter-daily-scraper/instance/twitter_scraper.db')
    cursor = conn.cursor()
    
    # 获取有数据的joshwoodward任务
    cursor.execute("""
        SELECT id, name, created_at, result_count 
        FROM scraping_task 
        WHERE name LIKE '%joshwoodward%' AND result_count > 0
        ORDER BY created_at DESC 
        LIMIT 1
    """)
    
    task = cursor.fetchone()
    if not task:
        print("没有找到joshwoodward任务")
        return
    
    task_id, name, created_at, result_count = task
    print(f"joshwoodward任务: ID={task_id}, 名称={name}, 创建时间={created_at}, 结果数={result_count}")
    print("="*80)
    
    # 获取该任务的推文数据
    cursor.execute("""
        SELECT id, content, username, link, hashtags, content_type, 
               comments, retweets, likes, publish_time, synced_to_feishu
        FROM tweet_data 
        WHERE task_id = ? 
        ORDER BY id DESC 
        LIMIT 10
    """, (task_id,))
    
    tweets = cursor.fetchall()
    print(f"找到 {len(tweets)} 条推文数据:")
    print()
    
    for i, tweet in enumerate(tweets, 1):
        tweet_id, content, username, link, hashtags, content_type, comments, retweets, likes, publish_time, synced_to_feishu = tweet
        
        print(f"推文 {i}:")
        print(f"  ID: {tweet_id}")
        print(f"  内容: {content[:100] if content else '空'}{'...' if content and len(content) > 100 else ''}")
        print(f"  作者: {username if username else '空'}")
        print(f"  链接: {link if link else '空'}")
        print(f"  话题标签: {hashtags if hashtags else '空'}")
        print(f"  类型标签: {content_type if content_type else '空'}")
        print(f"  已同步飞书: {'是' if synced_to_feishu else '否'}")
        print(f"  评论数: {comments if comments is not None else '空'}")
        print(f"  转发数: {retweets if retweets is not None else '空'}")
        print(f"  点赞数: {likes if likes is not None else '空'}")
        print(f"  发布时间: {publish_time if publish_time else '空'}")
        print("-" * 60)
    
    conn.close()

if __name__ == "__main__":
    check_joshwoodward_data()