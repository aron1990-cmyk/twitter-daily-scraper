#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件
定义系统的各种配置参数
"""

# AdsPower配置
ADS_POWER_CONFIG = {
    'local_api_url': 'http://local.adspower.net:50325',
    'user_id': 'k11p9ypc',
    'group_id': '',
    'user_ids': ['k11p9ypc'],
    'max_concurrent': 3,
    'retry_attempts': 3,
    'retry_delay': 5
}

# 飞书配置
FEISHU_CONFIG = {
    'app_id': '',
    'app_secret': '',
    'webhook_url': '',
    'enabled': False
}

# Twitter目标配置
TWITTER_TARGETS = {
    'keywords': [],  # 暂时不抓取关键词
    'accounts': ['elonmusk']  # 只抓取Musk的推文
}

# 过滤配置
FILTER_CONFIG = {
    'min_likes': 1,  # 至少1个赞以满足验证条件
    'min_retweets': 0,
    'min_comments': 0,
    'min_replies': 0,
    'max_tweets_per_target': 100,  # 每个目标最多抓取100条推文
    'keywords_filter': [''],  # 添加空字符串以满足验证条件
    'exclude_retweets': False,
    'exclude_replies': False
}

# 输出配置
OUTPUT_CONFIG = {
    'format': 'json',
    'include_metadata': True,
    'save_images': False
}

# 浏览器配置
BROWSER_CONFIG = {
    'headless': False,
    'window_size': (1920, 1080),
    'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}

# 日志配置
LOG_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'filename': 'twitter_scraper.log'
}

# 云同步配置
CLOUD_SYNC_CONFIG = {
    'enabled': False,
    'provider': 'local',
    'sync_interval': 3600
}

# 导出所有配置变量
__all__ = [
    'ADS_POWER_CONFIG',
    'FEISHU_CONFIG',
    'TWITTER_TARGETS', 
    'FILTER_CONFIG',
    'OUTPUT_CONFIG',
    'BROWSER_CONFIG',
    'LOG_CONFIG',
    'CLOUD_SYNC_CONFIG'
]