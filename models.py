
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模型和验证 - 简化版本
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field

class SentimentLabel(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"

class QualityGrade(str, Enum):
    A_PLUS = "A+"
    A = "A"
    B_PLUS = "B+"
    B = "B"
    C_PLUS = "C+"
    C = "C"
    D = "D"

@dataclass
class TweetModel:
    """推文数据模型"""
    username: str
    content: str
    likes: int = 0
    comments: int = 0
    retweets: int = 0
    publish_time: Optional[str] = None
    link: Optional[str] = None
    
    def __post_init__(self):
        """数据验证"""
        if len(self.username) < 1 or len(self.username) > 50:
            raise ValueError('用户名长度必须在1-50之间')
        if len(self.content) < 1 or len(self.content) > 2000:
            raise ValueError('内容长度必须在1-2000之间')
        if not self.content.strip():
            raise ValueError('推文内容不能为空')
        self.content = self.content.strip()
        
        if not self.username.replace('_', '').replace('-', '').isalnum():
            raise ValueError('用户名格式无效')
        self.username = self.username.lower()
        
        if self.likes < 0 or self.comments < 0 or self.retweets < 0:
            raise ValueError('计数不能为负数')

# 为了兼容性，添加别名
TweetData = TweetModel

@dataclass
class AIAnalysisModel:
    """AI分析结果模型"""
    overall_score: float
    engagement_score: float
    content_quality: float
    sentiment_score: float
    sentiment_label: SentimentLabel
    trend_relevance: float
    author_influence: float
    quality_grade: QualityGrade
    matched_trends: List[str] = field(default_factory=list)
    analyzed_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """数据验证"""
        if not (0 <= self.overall_score <= 1):
            raise ValueError('overall_score必须在0-1之间')
        if not (0 <= self.engagement_score <= 1):
            raise ValueError('engagement_score必须在0-1之间')
        if not (0 <= self.content_quality <= 1):
            raise ValueError('content_quality必须在0-1之间')
        if not (-1 <= self.sentiment_score <= 1):
            raise ValueError('sentiment_score必须在-1到1之间')
        if not (0 <= self.trend_relevance <= 1):
            raise ValueError('trend_relevance必须在0-1之间')
        if not (0 <= self.author_influence <= 1):
            raise ValueError('author_influence必须在0-1之间')

@dataclass
class ConfigModel:
    """配置模型"""
    adspower_user_id: str
    max_tweets_per_target: int = 50
    max_total_tweets: int = 200
    timeout: int = 30
    retry_count: int = 3
    
    def __post_init__(self):
        """数据验证"""
        if len(self.adspower_user_id) < 1:
            raise ValueError('AdsPower用户ID不能为空')
        self.adspower_user_id = self.adspower_user_id.strip()
        
        if not (1 <= self.max_tweets_per_target <= 1000):
            raise ValueError('max_tweets_per_target必须在1-1000之间')
        if not (1 <= self.max_total_tweets <= 5000):
            raise ValueError('max_total_tweets必须在1-5000之间')
        if not (5 <= self.timeout <= 300):
            raise ValueError('timeout必须在5-300之间')
        if not (1 <= self.retry_count <= 10):
             raise ValueError('retry_count必须在1-10之间')

@dataclass
class PerformanceMetrics:
    """性能指标模型"""
    start_time: float
    end_time: float
    duration: float
    memory_usage: float
    cpu_usage: float
    success_count: int = 0
    error_count: int = 0
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        total = self.success_count + self.error_count
        return (self.success_count / total * 100) if total > 0 else 0.0

@dataclass
class HealthStatus:
    """健康状态模型"""
    service_name: str
    status: str
    response_time: float
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """数据验证"""
        valid_statuses = ['healthy', 'unhealthy', 'degraded', 'unknown']
        if self.status not in valid_statuses:
            raise ValueError(f'状态必须是以下之一: {valid_statuses}')

@dataclass
class UserModel:
    """用户模型"""
    username: str
    display_name: str
    followers_count: int = 0
    following_count: int = 0
    bio: Optional[str] = None
    verified: bool = False
    
    def __post_init__(self):
        """数据验证"""
        if not self.username or len(self.username.strip()) == 0:
            raise ValueError('用户名不能为空')
        self.username = self.username.strip()
        if self.followers_count < 0 or self.following_count < 0:
            raise ValueError('关注数不能为负数')

# 为了兼容性，添加UserData别名
@dataclass
class UserData:
    """用户数据模型"""
    id: str
    username: str
    display_name: str
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    followers_count: int = 0
    following_count: int = 0
    tweets_count: int = 0
    verified: bool = False
    created_at: Optional[str] = None
    profile_image_url: Optional[str] = None
    banner_image_url: Optional[str] = None
    scraped_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """数据验证"""
        if not self.username or len(self.username.strip()) == 0:
            raise ValueError('用户名不能为空')
        self.username = self.username.strip()

@dataclass
class ScrapingConfig:
    """采集配置模型"""
    target_accounts: List[str] = field(default_factory=list)
    target_keywords: List[str] = field(default_factory=list)
    max_tweets_per_target: int = 50
    max_total_tweets: int = 1000
    min_likes: int = 0
    min_retweets: int = 0
    min_comments: int = 0
    include_retweets: bool = True
    include_replies: bool = False
    language_filter: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    
    def __post_init__(self):
        """数据验证"""
        if self.max_tweets_per_target <= 0 or self.max_total_tweets <= 0:
            raise ValueError('最大数量必须大于0')
