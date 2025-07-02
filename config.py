# -*- coding: utf-8 -*-
"""
配置文件 - Twitter 日报采集系统
"""

# AdsPower 配置
ADS_POWER_CONFIG = {
    'local_api_url': 'http://local.adspower.net:50325',  # AdsPower Local API 地址
    'user_id': '',  # AdsPower 用户ID，需要在实际使用时填入
    'group_id': '',  # AdsPower 分组ID（可选）
}

# Twitter 目标配置
TWITTER_TARGETS = {
    # 目标账号列表（不包含@符号）
    'accounts': [
        'elonmusk',
        'OpenAI',
        'sama',
        # 可以添加更多账号
    ],
    
    # 搜索关键词列表
    'keywords': [
        'AI',
        '副业',
        'daily',
        '人工智能',
        'ChatGPT',
        # 可以添加更多关键词
    ]
}

# 筛选条件配置
FILTER_CONFIG = {
    'min_likes': 100,      # 最小点赞数
    'min_comments': 30,    # 最小评论数
    'min_retweets': 50,    # 最小转发数
    
    # 特定关键词筛选（包含任一关键词即通过）
    'keywords_filter': ['AI', '副业', 'daily', '人工智能', 'ChatGPT'],
    
    # 最大抓取数量
    'max_tweets_per_target': 10,
}

# 输出配置
OUTPUT_CONFIG = {
    'data_dir': './data',
    'excel_filename_format': 'twitter_daily_{date}.xlsx',  # {date} 会被替换为当前日期
    'sheet_name': 'Twitter数据',
}

# 浏览器配置
BROWSER_CONFIG = {
    'headless': False,      # 是否无头模式
    'timeout': 30000,       # 页面加载超时时间（毫秒）
    'wait_time': 2,         # 页面操作间隔时间（秒）
    'scroll_pause_time': 1, # 滚动间隔时间（秒）
}

# 日志配置
LOG_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'filename': 'twitter_scraper.log'
}