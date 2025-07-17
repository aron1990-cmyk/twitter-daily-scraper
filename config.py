# -*- coding: utf-8 -*-
"""
配置文件 - Twitter 日报采集系统
"""

# AdsPower 配置
ADS_POWER_CONFIG = {
    'local_api_url': 'http://local.adspower.net:50325',  # AdsPower Local API 地址
    'user_id': 'k11p9ypc',  # AdsPower 用户ID（已配置）
    'group_id': '',  # AdsPower 分组ID（可选）
    
    # 多窗口模式配置 - 多个用户ID用于并行抓取
    # 注意：为了实现真正的并行抓取，每个用户ID应该对应不同的AdsPower浏览器实例
    # 如果只有一个AdsPower账号，可以创建多个浏览器配置文件
    'multi_user_ids': [
        'k11p9ypc',  # 窗口1 - 主要浏览器实例
        'k11p9y6f',  # 窗口2 - 如果有多个AdsPower账号，请替换为不同的user_id
        # 'user_id_4',  # 窗口4 - 可以添加更多用户ID
    ],
    
    # 并行任务配置
    'max_concurrent_tasks': 6,  # 最大并发任务数（进一步增加并发数）
    'task_timeout': 300,        # 单个任务超时时间（秒）- 极速模式
    'browser_startup_delay': 0.5, # 浏览器启动间隔（秒）- 极速启动
    
    # 混合模式增强配置
    'timeout': 15,          # 连接超时时间（秒）- 极速模式
    'retry_count': 2,       # 重试次数 - 减少重试
    'retry_delay': 2,       # 重试延迟（秒）- 极速重试
    'health_check': True,   # 启用健康检查
    'headless': False,      # 是否无头模式 - 设为False以显示浏览器窗口
    'window_visible': True, # 窗口是否可见 - 确保用户能看到操作过程
}

# Twitter 目标配置 - 混合模式策略
TWITTER_TARGETS = {
    # 目标账号列表（不包含@符号）- 高质量KOL博主
    'accounts': [
        # 科技创新领域
        'elonmusk',        # 特斯拉CEO，科技创新
        'OpenAI',          # OpenAI官方账号
        'sama',            # Sam Altman，OpenAI CEO
        'naval',           # Naval Ravikant，投资人思想家
        'paulg',           # Paul Graham，Y Combinator创始人
        
        # AI/技术专家
        'AndrewYNg',       # 吴恩达，AI专家
        'ylecun',          # Yann LeCun，深度学习之父
        'karpathy',        # Andrej Karpathy，AI研究员
        'fchollet',        # François Chollet，Keras创始人
        
        # 商业/创业
        'reidhoffman',     # Reid Hoffman，LinkedIn创始人
        'pmarca',          # Marc Andreessen，a16z创始人
        'balajis',         # Balaji Srinivasan，前Coinbase CTO
        'jason',           # Jason Calacanis，投资人
        
        # 中文科技博主
        'dotey',           # 宝玉，AI翻译专家
        'op7418',          # 歸藏，AI工具分享
        'nishuang',        # 倪爽，产品专家
        # 可以根据您的专注领域添加更多账号
    ],
    
    # 搜索关键词列表 - 热点话题追踪
    'keywords': [
        # AI相关
        'ChatGPT应用',
        'AI工具',
        '人工智能趋势',
        'GPT-4',
        'Claude',
        'Midjourney',
        
        # 创业/商业
        '副业赚钱',
        '创业思维',
        '商业模式',
        '产品思维',
        '增长黑客',
        
        # 技术趋势
        '技术趋势',
        '编程技巧',
        '开发工具',
        '自动化',
        
        # 个人成长
        '学习方法',
        '时间管理',
        '认知升级',
        '思维模型',
        
        # 可以根据您的兴趣添加更多关键词
    ]
}

# 筛选条件配置 - 混合模式优化
FILTER_CONFIG = {
    # 互动数筛选（降低门槛以获得更多优质内容）
    'min_likes': 50,       # 最小点赞数（降低以捕获更多内容）
    'min_comments': 10,    # 最小评论数
    'min_retweets': 20,    # 最小转发数
    
    # 特定关键词筛选（包含任一关键词即通过）
    'keywords_filter': [
        # AI相关
        'AI', '人工智能', 'ChatGPT', 'GPT', 'Claude', 'Midjourney',
        '机器学习', '深度学习', '大模型', 'LLM',
        
        # 创业/商业
        '副业', '创业', '商业', '产品', '增长', '营销',
        '思维', '认知', '方法论', '模式',
        
        # 技术
        '编程', '开发', '技术', '工具', '自动化',
        '效率', '生产力', 'productivity',
        
        # 学习成长
        '学习', '成长', '思考', '洞察', '经验',
        '方法', '技巧', '策略', '框架'
    ],
    
    # 采集数量配置
    'max_tweets_per_target': 8,   # 每个目标最大抓取数量（减少以提升速度）
    'max_total_tweets': 200,      # 总最大抓取数量限制
    
    # 内容质量筛选
    'min_content_length': 20,     # 最小内容长度
    'max_content_length': 1000,   # 最大内容长度
    
    # 时间筛选（小时）
    'max_age_hours': 72,          # 只采集72小时内的推文
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
    'timeout': 8000,        # 页面加载超时时间（毫秒）- 极速模式
    'wait_time': 0.3,       # 页面操作间隔时间（秒）- 极速等待
    'scroll_pause_time': 0.3, # 滚动间隔时间（秒）- 极速滚动
    'navigation_timeout': 10000,  # 导航超时时间（毫秒）- 极速导航
    'load_state_timeout': 4000,   # 加载状态超时时间（毫秒）- 极速加载
    'fast_mode': True,      # 启用快速模式
    'skip_images': True,    # 跳过图片加载以提升速度
    'disable_animations': True,  # 禁用动画效果
}

# 日志配置
LOG_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'filename': 'twitter_scraper.log'
}

# 云端同步配置
CLOUD_SYNC_CONFIG = {
    # Google Sheets 配置
    'google_sheets': {
        'enabled': False,  # 设置为True启用Google Sheets同步
        'credentials_file': './credentials/google-credentials.json',  # Google服务账号凭证文件路径
        'spreadsheet_id': '',  # Google表格ID（从URL中获取）
        'worksheet_name': 'Twitter数据',  # 工作表名称
    },
    
    # 飞书文档配置
    'feishu': {
        'enabled': False,  # 设置为True启用飞书同步
        'app_id': '',  # 飞书应用ID
        'app_secret': '',  # 飞书应用密钥
        'spreadsheet_token': '',  # 飞书表格token（从URL中获取）
        'sheet_id': '',  # 工作表ID（可选，留空使用第一个工作表）
    }
}

# 核心功能测试所需的配置项
ADSPOWER_API_URL = 'http://local.adspower.net:50325'
ADSPOWER_USER_ID = 'k11p9ypc'
ADSPOWER_GROUP_ID = ''
TWITTER_USERNAME = 'test_user'
TWITTER_PASSWORD = 'test_password'
DATA_EXPORT_PATH = './data/exports'