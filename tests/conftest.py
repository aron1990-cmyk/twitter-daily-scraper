
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pytest 配置和固件
"""

import pytest
import asyncio
import json
import tempfile
from pathlib import Path
import sys
import os
from unittest.mock import Mock, AsyncMock, patch
from models import TweetModel, ConfigModel

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 全局测试配置
pytest_plugins = ['pytest_asyncio']

@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环用于异步测试"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_data_dir():
    """测试数据目录"""
    return Path(__file__).parent / "fixtures"

@pytest.fixture(scope="session")
def sample_tweets_fixture():
    """会话级别的示例推文数据"""
    fixtures_path = Path(__file__).parent / "fixtures" / "sample_tweets.json"
    with open(fixtures_path, 'r', encoding='utf-8') as f:
        return json.load(f)

@pytest.fixture
def temp_workspace():
    """临时工作空间"""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir)
        # 创建子目录结构
        (workspace / "exports").mkdir()
        (workspace / "data").mkdir()
        (workspace / "logs").mkdir()
        yield workspace

@pytest.fixture
def sample_tweet():
    """示例推文数据"""
    return TweetModel(
        username="testuser",
        content="这是一条测试推文 #AI #测试",
        likes=100,
        comments=10,
        retweets=20,
        publish_time="2024-01-01T12:00:00",
        link="https://twitter.com/testuser/status/123"
    )

@pytest.fixture
def sample_config():
    """示例配置"""
    return ConfigModel(
        adspower_user_id="test_user_id",
        max_tweets_per_target=50,
        max_total_tweets=200,
        timeout=30,
        retry_count=3
    )

@pytest.fixture
def mock_config():
    """模拟配置对象"""
    config = Mock()
    config.HEADLESS = True
    config.MAX_TWEETS = 50
    config.SCROLL_PAUSE_TIME = 2
    config.MAX_SCROLL_ATTEMPTS = 10
    config.CONCURRENT_WINDOWS = 1
    config.DEDUPLICATION_THRESHOLD = 0.85
    config.VALUE_THRESHOLD = 3.0
    config.EXPORT_FORMAT = "excel"
    return config

@pytest.fixture
def high_quality_tweet():
    """高质量推文示例"""
    return {
        "id": "hq_1",
        "username": "tech_expert",
        "content": "Revolutionary breakthrough in artificial intelligence: New neural architecture achieves unprecedented performance in natural language understanding and generation tasks.",
        "timestamp": "2024-01-15 10:00:00",
        "url": "https://twitter.com/tech_expert/status/hq_1",
        "likes": 15000,
        "retweets": 4500,
        "replies": 800,
        "media_count": 2,
        "hashtags": ["#AI", "#Breakthrough", "#Technology"],
        "mentions": ["@openai", "@deepmind"],
        "is_verified": True
    }

@pytest.fixture
def low_quality_tweet():
    """低质量推文示例"""
    return {
        "id": "lq_1",
        "username": "random_user",
        "content": "just woke up",
        "timestamp": "2024-01-15 11:00:00",
        "url": "https://twitter.com/random_user/status/lq_1",
        "likes": 2,
        "retweets": 0,
        "replies": 0,
        "media_count": 0,
        "hashtags": [],
        "mentions": [],
        "is_verified": False
    }

@pytest.fixture
def mock_browser():
    """模拟浏览器"""
    with patch('ads_browser_launcher.AdsPowerLauncher') as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        yield mock

@pytest.fixture
def duplicate_tweets_set():
    """重复推文集合"""
    base_tweet = {
        "username": "test_user",
        "content": "This is a test tweet about AI technology",
        "timestamp": "2024-01-15 12:00:00",
        "likes": 100,
        "retweets": 20,
        "replies": 5,
        "media_count": 1,
        "hashtags": ["#AI"],
        "mentions": [],
        "is_verified": False
    }
    
    return [
        {**base_tweet, "id": "1", "url": "https://twitter.com/test_user/status/1"},
        {**base_tweet, "id": "2", "url": "https://twitter.com/test_user/status/2"},  # 内容重复
        {**base_tweet, "id": "1", "url": "https://twitter.com/test_user/status/1"},  # 完全重复
        {
            **base_tweet, 
            "id": "3", 
            "url": "https://twitter.com/test_user/status/3",
            "content": "This is a test tweet about artificial intelligence technology",  # 相似内容
        }
    ]

@pytest.fixture
def test_parameters():
    """测试参数组合"""
    return {
        "usernames": ["elonmusk", "openai", "sundarpichai"],
        "keywords": ["AI", "GPT4", "technology", "innovation"],
        "export_formats": ["excel", "json", "sqlite"],
        "dedup_thresholds": [0.8, 0.85, 0.9, 0.95],
        "value_thresholds": [2.0, 2.5, 3.0, 3.5, 4.0],
        "max_tweets": [10, 25, 50, 100]
    }

# 测试标记定义
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.performance = pytest.mark.performance
pytest.mark.slow = pytest.mark.slow

# 自定义断言帮助函数
class TestAssertions:
    """自定义测试断言类"""
    
    @staticmethod
    def assert_tweet_structure(tweet, required_fields=None):
        """断言推文结构完整性"""
        if required_fields is None:
            required_fields = ['id', 'username', 'content', 'timestamp', 'url']
        
        for field in required_fields:
            assert field in tweet, f"Missing required field: {field}"
        
        # 验证数据类型
        assert isinstance(tweet.get('likes', 0), int)
        assert isinstance(tweet.get('retweets', 0), int)
        assert isinstance(tweet.get('replies', 0), int)
        assert isinstance(tweet['content'], str)
        assert len(tweet['content']) > 0
    
    @staticmethod
    def assert_score_range(score, min_val=0, max_val=5):
        """断言评分在有效范围内"""
        assert isinstance(score, (int, float)), f"Score must be numeric, got {type(score)}"
        assert min_val <= score <= max_val, f"Score {score} not in range [{min_val}, {max_val}]"
    
    @staticmethod
    def assert_deduplication_stats(stats):
        """断言去重统计信息完整性"""
        required_stats = ['original_count', 'unique_count', 'duplicates_removed', 'deduplication_rate']
        for stat in required_stats:
            assert stat in stats, f"Missing stat: {stat}"
        
        assert stats['original_count'] >= stats['unique_count']
        assert stats['duplicates_removed'] >= 0
        assert 0 <= stats['deduplication_rate'] <= 1
    
    @staticmethod
    def assert_file_export_success(file_path, min_size=0):
        """断言文件导出成功"""
        file_path = Path(file_path)
        assert file_path.exists(), f"Export file does not exist: {file_path}"
        assert file_path.stat().st_size > min_size, f"Export file too small: {file_path.stat().st_size} bytes"

@pytest.fixture
def assert_helper():
    """提供断言帮助函数"""
    return TestAssertions()_instance

@pytest.fixture
def mock_requests():
    """模拟HTTP请求"""
    with patch('requests.get') as mock:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'success': True}
        mock.return_value = mock_response
        yield mock
