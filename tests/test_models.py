
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模型测试
"""

import pytest
from pydantic import ValidationError
from models import TweetModel, AIAnalysisModel, ConfigModel

class TestTweetModel:
    """推文模型测试"""
    
    def test_valid_tweet(self, sample_tweet):
        """测试有效推文"""
        assert sample_tweet.username == "testuser"
        assert sample_tweet.content == "这是一条测试推文 #AI #测试"
        assert sample_tweet.likes == 100
    
    def test_empty_content_validation(self):
        """测试空内容验证"""
        with pytest.raises(ValidationError):
            TweetModel(
                username="testuser",
                content="",
                likes=0
            )
    
    def test_invalid_username(self):
        """测试无效用户名"""
        with pytest.raises(ValidationError):
            TweetModel(
                username="invalid@user",
                content="测试内容",
                likes=0
            )
    
    def test_negative_metrics(self):
        """测试负数指标"""
        with pytest.raises(ValidationError):
            TweetModel(
                username="testuser",
                content="测试内容",
                likes=-1
            )

class TestConfigModel:
    """配置模型测试"""
    
    def test_valid_config(self, sample_config):
        """测试有效配置"""
        assert sample_config.adspower_user_id == "test_user_id"
        assert sample_config.max_tweets_per_target == 50
    
    def test_empty_user_id(self):
        """测试空用户ID"""
        with pytest.raises(ValidationError):
            ConfigModel(
                adspower_user_id="",
                max_tweets_per_target=50
            )
    
    def test_invalid_ranges(self):
        """测试无效范围"""
        with pytest.raises(ValidationError):
            ConfigModel(
                adspower_user_id="test",
                max_tweets_per_target=0  # 应该 >= 1
            )
