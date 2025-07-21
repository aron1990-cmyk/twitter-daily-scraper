#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
from enhanced_tweet_scraper import EnhancedTwitterScraper, load_feishu_config_from_file
from cloud_sync import CloudSyncManager

def analyze_local_data_only():
    """仅分析本地数据的字段映射"""
    print("\n📊 分析本地推文数据...")
    
    # 检查数据库中的推文样例
    conn = sqlite3.connect('twitter_scraper.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT username, content, publish_time, likes, comments, retweets, link, hashtags, scraped_at
        FROM tweet_data 
        ORDER BY id DESC 
        LIMIT 5
    """)
    
    tweets = cursor.fetchall()
    
    # 统计时间字段情况
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN publish_time IS NOT NULL AND publish_time != '' THEN 1 END) as has_publish_time,
            COUNT(CASE WHEN scraped_at IS NOT NULL THEN 1 END) as has_scraped_at
        FROM tweet_data
    """)
    
    stats = cursor.fetchone()
    conn.close()
    
    total, has_publish_time, has_scraped_at = stats
    
    print(f"\n📈 数据库统计:")
    print(f"  总推文数: {total}")
    print(f"  有发布时间的推文: {has_publish_time} ({has_publish_time/total*100:.1f}%)")
    print(f"  有抓取时间的推文: {has_scraped_at} ({has_scraped_at/total*100:.1f}%)")
    
    print("\n📝 推文样例:")
    for i, (username, content, publish_time, likes, comments, retweets, link, hashtags, scraped_at) in enumerate(tweets, 1):
        print(f"  {i}. 用户: {username}")
        print(f"     内容: {content[:50]}...")
        print(f"     发布时间: {publish_time or '❌ 无'}")
        print(f"     抓取时间: {scraped_at or '❌ 无'}")
        print(f"     互动: 👍{likes} 💬{comments} 🔄{retweets}")
        print()
    
    # 模拟格式化数据
    print("📝 模拟飞书数据格式化...")
    scraper = EnhancedTwitterScraper()
    
    # 构建测试数据
    test_tweets = []
    for username, content, publish_time, likes, comments, retweets, link, hashtags, scraped_at in tweets:
        tweet_dict = {
            'username': username,
            'content': content,
            'publish_time': publish_time,
            'likes': likes,
            'comments': comments,
            'retweets': retweets,
            'link': link,
            'hashtags': hashtags.split(',') if hashtags else [],
            'scraped_at': scraped_at
        }
        test_tweets.append(tweet_dict)
    
    formatted_tweets = scraper.format_tweets_for_feishu(test_tweets)
    
    print("\n🎯 格式化后的字段分析:")
    if formatted_tweets:
        sample_tweet = formatted_tweets[0]
        print("飞书同步字段映射:")
        for key, value in sample_tweet.items():
            status = "✅ 有值" if value else "❌ 空值"
            print(f"  - {key}: {status}")
            if not value and key in ['发布时间', '创建时间']:
                print(f"    ⚠️ 时间字段为空可能导致飞书显示异常")
    
    print("\n🔍 问题诊断:")
    empty_publish_time = total - has_publish_time
    if empty_publish_time > 0:
        print(f"  ❌ {empty_publish_time} 条推文缺少发布时间")
        print(f"     这可能导致飞书中这些推文的时间字段显示异常")
    
    if has_publish_time > 0:
        print(f"  ✅ {has_publish_time} 条推文有发布时间")
        print(f"     这些推文在飞书中应该显示正常")
    
    print("\n💡 解决方案建议:")
    if empty_publish_time > 0:
        print("  1. 修复抓取器以正确获取推文发布时间")
        print("  2. 对于已有的无时间推文，可以使用抓取时间作为替代")
        print("  3. 重新抓取这些推文以获取完整的时间信息")

def debug_feishu_field_mapping():
    """调试飞书字段映射问题"""
    print("🔍 调试飞书字段映射问题...")
    
    # 加载飞书配置
    feishu_config = load_feishu_config_from_file()
    if not feishu_config:
        print("❌ 无法加载飞书配置")
        return
    
    if not feishu_config.get('enabled'):
        print("⚠️ 飞书配置未启用，但继续分析字段映射...")
    
    # 检查是否为占位符配置
    is_placeholder = (
        feishu_config.get('app_id') == 'your_feishu_app_id' or
        feishu_config.get('spreadsheet_token') == 'your_spreadsheet_token'
    )
    
    if is_placeholder:
        print("⚠️ 检测到占位符配置，跳过飞书API调用，仅分析本地数据...")
        analyze_local_data_only()
        return
    
    # 创建同步管理器
    sync_manager = CloudSyncManager()
    sync_manager.setup_feishu(
        feishu_config.get('app_id'),
        feishu_config.get('app_secret')
    )
    
    # 获取飞书表格字段信息
    print("\n📋 获取飞书表格字段信息...")
    fields_info = sync_manager._get_feishu_table_fields(
        feishu_config.get('spreadsheet_token'),
        feishu_config.get('table_id')
    )
    
    if fields_info:
        print(f"✅ 飞书表格字段获取成功，共 {len(fields_info)} 个字段:")
        for i, field in enumerate(fields_info, 1):
            field_name = field.get('field_name', '未知')
            field_type = field.get('type', '未知')
            print(f"  {i}. {field_name} ({field_type})")
    else:
        print("❌ 无法获取飞书表格字段")
        return
    
    # 检查数据库中的推文样例
    print("\n📊 检查数据库中的推文样例...")
    conn = sqlite3.connect('twitter_scraper.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT username, content, publish_time, likes, comments, retweets, link, hashtags
        FROM tweet_data 
        ORDER BY id DESC 
        LIMIT 3
    """)
    
    tweets = cursor.fetchall()
    conn.close()
    
    print("数据库中的推文样例:")
    for i, (username, content, publish_time, likes, comments, retweets, link, hashtags) in enumerate(tweets, 1):
        print(f"  {i}. 用户: {username}")
        print(f"     内容: {content[:50]}...")
        print(f"     发布时间: {publish_time or '无'}")
        print(f"     互动: 👍{likes} 💬{comments} 🔄{retweets}")
        print(f"     链接: {link[:50]}..." if link else "     链接: 无")
        print(f"     标签: {hashtags}")
        print()
    
    # 模拟格式化数据
    print("📝 模拟格式化数据用于飞书同步...")
    scraper = EnhancedTwitterScraper()
    
    # 构建测试数据
    test_tweets = []
    for username, content, publish_time, likes, comments, retweets, link, hashtags in tweets:
        tweet_dict = {
            'username': username,
            'content': content,
            'publish_time': publish_time,
            'likes': likes,
            'comments': comments,
            'retweets': retweets,
            'link': link,
            'hashtags': hashtags.split(',') if hashtags else []
        }
        test_tweets.append(tweet_dict)
    
    formatted_tweets = scraper.format_tweets_for_feishu(test_tweets)
    
    print("格式化后的飞书数据样例:")
    for i, tweet in enumerate(formatted_tweets, 1):
        print(f"  {i}. 格式化数据:")
        for key, value in tweet.items():
            print(f"     {key}: {value}")
        print()
    
    # 检查字段匹配情况
    print("🔍 检查字段匹配情况...")
    feishu_field_names = [field.get('field_name') for field in fields_info]
    formatted_field_names = list(formatted_tweets[0].keys()) if formatted_tweets else []
    
    print("飞书表格字段:")
    for field in feishu_field_names:
        print(f"  - {field}")
    
    print("\n格式化数据字段:")
    for field in formatted_field_names:
        print(f"  - {field}")
    
    print("\n字段匹配分析:")
    matched_fields = []
    unmatched_feishu_fields = []
    unmatched_data_fields = []
    
    for field in formatted_field_names:
        if field in feishu_field_names:
            matched_fields.append(field)
        else:
            unmatched_data_fields.append(field)
    
    for field in feishu_field_names:
        if field not in formatted_field_names:
            unmatched_feishu_fields.append(field)
    
    print(f"✅ 匹配的字段 ({len(matched_fields)}):")
    for field in matched_fields:
        print(f"  - {field}")
    
    print(f"\n⚠️ 飞书表格中存在但数据中没有的字段 ({len(unmatched_feishu_fields)}):")
    for field in unmatched_feishu_fields:
        print(f"  - {field}")
    
    print(f"\n❌ 数据中存在但飞书表格中没有的字段 ({len(unmatched_data_fields)}):")
    for field in unmatched_data_fields:
        print(f"  - {field}")
    
    # 分析问题
    print("\n🎯 问题分析:")
    if '发布时间' in unmatched_feishu_fields:
        print("  - 飞书表格有'发布时间'字段但数据中没有使用")
    if '创建时间' in unmatched_feishu_fields:
        print("  - 飞书表格有'创建时间'字段但数据中没有使用")
    
    time_related_issues = []
    for tweet in formatted_tweets:
        if not tweet.get('发布时间'):
            time_related_issues.append(tweet.get('作者（账号）', '未知用户'))
    
    if time_related_issues:
        print(f"  - {len(time_related_issues)} 条推文缺少发布时间数据")
        print(f"    涉及用户: {', '.join(time_related_issues[:5])}{'...' if len(time_related_issues) > 5 else ''}")

if __name__ == '__main__':
    debug_feishu_field_mapping()