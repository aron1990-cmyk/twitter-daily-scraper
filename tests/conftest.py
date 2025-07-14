
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pytest 配置和固件
"""

import pytest
from unittest.mock import Mock, patch
from models import TweetModel, ConfigModel

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
def mock_browser():
    """模拟浏览器"""
    with patch('ads_browser_launcher.AdsPowerLauncher') as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_requests():
    """模拟HTTP请求"""
    with patch('requests.get') as mock:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'success': True}
        mock.return_value = mock_response
        yield mock
