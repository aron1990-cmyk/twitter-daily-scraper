#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter Daily Scraper - Enhanced Configuration Example
增强版Twitter日报采集器配置示例

此文件展示了所有可用的配置选项，包括新增的AI分析、账户管理、
系统监控和任务调度等功能的配置。

使用方法:
1. 复制此文件为 config_enhanced.py
2. 根据实际需求修改配置参数
3. 使用 run_enhanced.py --config config_enhanced.py 启动
"""

from datetime import datetime, time
import os

# ============================================================================
# 基础配置 (继承原有配置)
# ============================================================================

# AdsPower 配置
ADS_POWER_CONFIG = {
    'base_url': 'http://local.adspower.net:50325',
    'user_ids': ['your_user_id_1', 'your_user_id_2'],  # 支持多账户
    'timeout': 30,
    'retry_count': 3,
    'retry_delay': 5
}

# Twitter 目标配置
TWITTER_TARGETS = {
    'users': [
        {'username': 'elonmusk', 'max_tweets': 50},
        {'username': 'OpenAI', 'max_tweets': 30},
        {'username': 'Microsoft', 'max_tweets': 20}
    ],
    'keywords': [
        {'keyword': 'AI人工智能', 'max_tweets': 100},
        {'keyword': 'ChatGPT', 'max_tweets': 80},
        {'keyword': '机器学习', 'max_tweets': 60}
    ],
    'hashtags': [
        {'hashtag': '#AI', 'max_tweets': 50},
        {'hashtag': '#MachineLearning', 'max_tweets': 40}
    ]
}

# 过滤器配置
FILTER_CONFIG = {
    'min_likes': 10,
    'min_retweets': 5,
    'min_comments': 2,
    'exclude_keywords': ['广告', 'spam', '垃圾'],
    'include_keywords': ['技术', '创新', '科技'],
    'min_content_length': 20,
    'max_content_length': 1000,
    'language_filter': ['zh', 'en'],
    'time_range': {
        'start_hours_ago': 24,
        'end_hours_ago': 0
    }
}

# 云同步配置
CLOUD_SYNC_CONFIG = {
    'google_sheets': {
        'enabled': True,
        'credentials_file': 'path/to/google_credentials.json',
        'spreadsheet_id': 'your_spreadsheet_id',
        'worksheet_name': 'Twitter_Data',
        'auto_create_worksheet': True
    },
    'feishu': {
        'enabled': True,
        'app_id': 'your_feishu_app_id',
        'app_secret': 'your_feishu_app_secret',
        'folder_token': 'your_folder_token',
        'auto_create_doc': True
    }
}

# ============================================================================
# AI分析器配置
# ============================================================================

AI_ANALYZER_CONFIG = {
    # 质量评估权重
    'quality_weights': {
        'content_length': 0.15,
        'structure_score': 0.20,
        'richness_score': 0.25,
        'language_quality': 0.20,
        'professionalism': 0.20
    },
    
    # 情感分析词典
    'sentiment_keywords': {
        'positive': [
            '好', '棒', '优秀', '成功', '创新', '突破', '进步', '发展',
            'great', 'excellent', 'amazing', 'success', 'innovation', 'breakthrough'
        ],
        'negative': [
            '差', '糟糕', '失败', '问题', '错误', '困难', '挑战',
            'bad', 'terrible', 'failure', 'problem', 'error', 'difficult'
        ]
    },
    
    # 参与度评分权重
    'engagement_weights': {
        'likes': 0.4,
        'retweets': 0.35,
        'comments': 0.25
    },
    
    # 趋势关键词（定期更新）
    'trending_keywords': [
        'AI', '人工智能', 'ChatGPT', 'GPT-4', '机器学习', '深度学习',
        '区块链', '元宇宙', 'Web3', 'NFT', '加密货币',
        '自动驾驶', '新能源', '电动车', '可持续发展'
    ],
    
    # 作者影响力评估
    'author_influence_thresholds': {
        'followers_high': 100000,
        'followers_medium': 10000,
        'verified_bonus': 0.2,
        'engagement_rate_good': 0.05
    },
    
    # 批处理设置
    'batch_processing': {
        'batch_size': 50,
        'max_concurrent': 5,
        'timeout_per_tweet': 10
    }
}

# ============================================================================
# 账户管理器配置
# ============================================================================

ACCOUNT_MANAGER_CONFIG = {
    # 账户配置文件路径
    'accounts_file': 'accounts.json',
    
    # 轮换策略
    'rotation_strategy': 'priority',  # 'round_robin', 'priority', 'random'
    
    # 使用限制
    'usage_limits': {
        'daily_max_usage': 10,
        'hourly_max_usage': 2,
        'min_cooldown_minutes': 30,
        'max_error_count': 3
    },
    
    # 健康检查
    'health_check': {
        'enabled': True,
        'interval_minutes': 60,
        'timeout_seconds': 30
    },
    
    # 自动恢复
    'auto_recovery': {
        'enabled': True,
        'retry_after_minutes': 120,
        'max_retry_count': 3
    }
}

# 账户列表示例
ACCOUNTS_EXAMPLE = [
    {
        'user_id': 'ads_user_1',
        'name': '主账户',
        'priority': 1,
        'daily_limit': 15,
        'hourly_limit': 3,
        'tags': ['primary', 'high_quality']
    },
    {
        'user_id': 'ads_user_2',
        'name': '备用账户1',
        'priority': 2,
        'daily_limit': 10,
        'hourly_limit': 2,
        'tags': ['backup', 'medium_quality']
    },
    {
        'user_id': 'ads_user_3',
        'name': '备用账户2',
        'priority': 3,
        'daily_limit': 8,
        'hourly_limit': 1,
        'tags': ['backup', 'low_priority']
    }
]

# ============================================================================
# 系统监控配置
# ============================================================================

SYSTEM_MONITOR_CONFIG = {
    # 监控间隔
    'monitoring_interval': 60,  # 秒
    
    # 数据保留
    'data_retention': {
        'max_records': 1440,  # 24小时的分钟数
        'cleanup_interval': 3600  # 每小时清理一次
    },
    
    # 告警规则
    'alert_rules': [
        {
            'name': 'high_cpu_usage',
            'metric': 'cpu_percent',
            'operator': '>',
            'threshold': 80.0,
            'duration': 300,  # 持续5分钟
            'severity': 'warning',
            'enabled': True
        },
        {
            'name': 'high_memory_usage',
            'metric': 'memory_percent',
            'operator': '>',
            'threshold': 85.0,
            'duration': 300,
            'severity': 'warning',
            'enabled': True
        },
        {
            'name': 'low_disk_space',
            'metric': 'disk_percent',
            'operator': '>',
            'threshold': 90.0,
            'duration': 60,
            'severity': 'critical',
            'enabled': True
        },
        {
            'name': 'process_memory_leak',
            'metric': 'process_memory_mb',
            'operator': '>',
            'threshold': 1000.0,
            'duration': 600,
            'severity': 'warning',
            'enabled': True
        }
    ],
    
    # 告警通知
    'alert_notifications': {
        'email': {
            'enabled': False,
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'username': 'your_email@gmail.com',
            'password': 'your_app_password',
            'recipients': ['admin@example.com']
        },
        'webhook': {
            'enabled': False,
            'url': 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK',
            'timeout': 10
        }
    }
}

# ============================================================================
# 任务调度器配置
# ============================================================================

SCHEDULER_CONFIG = {
    # 调度器设置
    'timezone': 'Asia/Shanghai',
    'max_workers': 3,
    'job_defaults': {
        'coalesce': True,
        'max_instances': 1,
        'misfire_grace_time': 300
    },
    
    # 预定义任务
    'scheduled_tasks': [
        {
            'id': 'daily_scraping',
            'name': '每日Twitter采集',
            'function': 'daily_twitter_scraping',
            'trigger': 'cron',
            'hour': 9,
            'minute': 0,
            'enabled': True,
            'max_runtime': 3600,  # 1小时超时
            'retry_count': 2,
            'retry_delay': 300
        },
        {
            'id': 'hourly_monitoring',
            'name': '系统健康检查',
            'function': 'system_health_check',
            'trigger': 'interval',
            'hours': 1,
            'enabled': True,
            'max_runtime': 300,
            'retry_count': 1
        },
        {
            'id': 'weekly_report',
            'name': '周报生成',
            'function': 'weekly_report_generation',
            'trigger': 'cron',
            'day_of_week': 'mon',
            'hour': 10,
            'minute': 0,
            'enabled': True,
            'max_runtime': 1800
        },
        {
            'id': 'data_backup',
            'name': '数据备份',
            'function': 'data_backup',
            'trigger': 'cron',
            'hour': 2,
            'minute': 0,
            'enabled': True,
            'max_runtime': 1200
        }
    ]
}

# ============================================================================
# 配置管理器配置
# ============================================================================

CONFIG_MANAGER_CONFIG = {
    # 配置文件路径
    'config_dir': 'configs',
    'backup_dir': 'config_backups',
    
    # 备份设置
    'backup_settings': {
        'auto_backup': True,
        'backup_before_change': True,
        'max_backups': 10,
        'backup_interval_hours': 24
    },
    
    # 配置验证
    'validation': {
        'strict_mode': True,
        'validate_on_load': True,
        'validate_on_save': True
    }
}

# ============================================================================
# 输出和报告配置
# ============================================================================

OUTPUT_CONFIG = {
    # Excel输出设置
    'excel': {
        'include_ai_analysis': True,
        'include_charts': True,
        'auto_format': True,
        'password_protect': False
    },
    
    # 报告生成
    'reports': {
        'daily_summary': True,
        'ai_insights': True,
        'trend_analysis': True,
        'performance_metrics': True
    },
    
    # 文件命名
    'file_naming': {
        'include_timestamp': True,
        'include_source': True,
        'include_count': True
    }
}

# ============================================================================
# 日志配置
# ============================================================================

LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file_handler': {
        'enabled': True,
        'filename': 'twitter_scraper_enhanced.log',
        'max_bytes': 10 * 1024 * 1024,  # 10MB
        'backup_count': 5
    },
    'console_handler': {
        'enabled': True,
        'level': 'INFO'
    }
}

# ============================================================================
# 性能优化配置
# ============================================================================

PERFORMANCE_CONFIG = {
    # 并发设置
    'concurrency': {
        'max_concurrent_requests': 5,
        'request_delay': 2,
        'batch_size': 20
    },
    
    # 缓存设置
    'caching': {
        'enabled': True,
        'cache_dir': 'cache',
        'max_cache_size_mb': 100,
        'cache_ttl_hours': 24
    },
    
    # 资源限制
    'resource_limits': {
        'max_memory_mb': 2048,
        'max_cpu_percent': 80,
        'max_runtime_hours': 6
    }
}

# ============================================================================
# 安全配置
# ============================================================================

SECURITY_CONFIG = {
    # 数据加密
    'encryption': {
        'enabled': False,
        'key_file': 'encryption.key'
    },
    
    # 访问控制
    'access_control': {
        'require_auth': False,
        'allowed_ips': ['127.0.0.1'],
        'api_key_required': False
    },
    
    # 数据脱敏
    'data_anonymization': {
        'enabled': False,
        'mask_user_info': True,
        'mask_sensitive_content': True
    }
}

# ============================================================================
# 导出所有配置
# ============================================================================

# 将所有配置合并到一个字典中，便于管理
ALL_CONFIGS = {
    'ads_power': ADS_POWER_CONFIG,
    'twitter_targets': TWITTER_TARGETS,
    'filter': FILTER_CONFIG,
    'cloud_sync': CLOUD_SYNC_CONFIG,
    'ai_analyzer': AI_ANALYZER_CONFIG,
    'account_manager': ACCOUNT_MANAGER_CONFIG,
    'system_monitor': SYSTEM_MONITOR_CONFIG,
    'scheduler': SCHEDULER_CONFIG,
    'config_manager': CONFIG_MANAGER_CONFIG,
    'output': OUTPUT_CONFIG,
    'logging': LOGGING_CONFIG,
    'performance': PERFORMANCE_CONFIG,
    'security': SECURITY_CONFIG
}

if __name__ == "__main__":
    print("Twitter Daily Scraper - Enhanced Configuration")
    print("配置模块列表:")
    for key in ALL_CONFIGS.keys():
        print(f"  - {key}")
    print("\n请复制此文件为 config_enhanced.py 并根据需要修改配置")