import pytest
import json
from pathlib import Path
import sys
import os
from unittest.mock import Mock, patch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from performance_optimizer import TweetValueAnalyzer

class TestTweetValueAnalyzer:
    """推文价值分析模块测试类"""
    
    @pytest.fixture
    def sample_tweets(self):
        """加载示例推文数据"""
        fixtures_path = Path(__file__).parent / "fixtures" / "sample_tweets.json"
        with open(fixtures_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @pytest.fixture
    def value_analyzer(self):
        """创建价值分析器实例"""
        return TweetValueAnalyzer()
    
    @pytest.fixture
    def high_value_tweets(self):
        """创建高价值推文测试数据"""
        return [
            {
                "id": "1",
                "username": "elonmusk",
                "content": "Exciting breakthrough in AI technology! Our latest research shows remarkable progress in neural networks and machine learning capabilities. This could revolutionize how we approach artificial intelligence.",
                "timestamp": "2024-01-15 10:00:00",
                "url": "https://twitter.com/elonmusk/status/1",
                "likes": 25000,
                "retweets": 8000,
                "replies": 1500,
                "media_count": 2,
                "hashtags": ["#AI", "#Technology", "#Innovation"],
                "mentions": ["@openai", "@tesla"],
                "is_verified": True
            },
            {
                "id": "2",
                "username": "openai",
                "content": "GPT-4 represents a significant advancement in natural language processing. Our comprehensive evaluation shows improvements across multiple benchmarks and real-world applications.",
                "timestamp": "2024-01-15 11:00:00",
                "url": "https://twitter.com/openai/status/2",
                "likes": 18000,
                "retweets": 5500,
                "replies": 800,
                "media_count": 1,
                "hashtags": ["#GPT4", "#NLP", "#AI"],
                "mentions": [],
                "is_verified": True
            }
        ]
    
    @pytest.fixture
    def low_value_tweets(self):
        """创建低价值推文测试数据"""
        return [
            {
                "id": "3",
                "username": "randomuser",
                "content": "just had lunch",
                "timestamp": "2024-01-15 12:00:00",
                "url": "https://twitter.com/randomuser/status/3",
                "likes": 3,
                "retweets": 0,
                "replies": 1,
                "media_count": 0,
                "hashtags": [],
                "mentions": [],
                "is_verified": False
            },
            {
                "id": "4",
                "username": "spambot",
                "content": "Check this out!!!",
                "timestamp": "2024-01-15 13:00:00",
                "url": "https://twitter.com/spambot/status/4",
                "likes": 1,
                "retweets": 0,
                "replies": 0,
                "media_count": 0,
                "hashtags": [],
                "mentions": [],
                "is_verified": False
            }
        ]
    
    def test_analyzer_initialization(self, value_analyzer):
        """测试价值分析器初始化
        
        验证TweetValueAnalyzer能够正确初始化
        """
        assert value_analyzer is not None
        assert hasattr(value_analyzer, 'analyze_tweet_value')
        assert hasattr(value_analyzer, 'calculate_content_score')
        assert hasattr(value_analyzer, 'calculate_engagement_score')
        assert hasattr(value_analyzer, 'calculate_media_score')
    
    def test_content_score_calculation(self, value_analyzer):
        """测试内容评分计算
        
        验证内容评分算法的准确性
        """
        # 高质量内容
        high_quality_content = "Breakthrough in artificial intelligence research shows promising results for natural language understanding and generation capabilities."
        high_score = value_analyzer.calculate_content_score(high_quality_content)
        
        # 低质量内容
        low_quality_content = "just had lunch"
        low_score = value_analyzer.calculate_content_score(low_quality_content)
        
        # 验证评分差异
        assert high_score > low_score
        assert 0 <= high_score <= 5
        assert 0 <= low_score <= 5
    
    def test_engagement_score_calculation(self, value_analyzer):
        """测试互动评分计算
        
        验证互动评分基于点赞、转发、回复数量的准确性
        """
        # 高互动推文
        high_engagement = {
            "likes": 10000,
            "retweets": 3000,
            "replies": 500
        }
        high_score = value_analyzer.calculate_engagement_score(
            high_engagement["likes"],
            high_engagement["retweets"],
            high_engagement["replies"]
        )
        
        # 低互动推文
        low_engagement = {
            "likes": 5,
            "retweets": 1,
            "replies": 0
        }
        low_score = value_analyzer.calculate_engagement_score(
            low_engagement["likes"],
            low_engagement["retweets"],
            low_engagement["replies"]
        )
        
        # 验证评分差异
        assert high_score > low_score
        assert 0 <= high_score <= 5
        assert 0 <= low_score <= 5
    
    def test_media_score_calculation(self, value_analyzer):
        """测试媒体评分计算
        
        验证媒体评分基于媒体数量的准确性
        """
        # 包含媒体的推文
        media_score_2 = value_analyzer.calculate_media_score(2)
        media_score_1 = value_analyzer.calculate_media_score(1)
        media_score_0 = value_analyzer.calculate_media_score(0)
        
        # 验证评分递减
        assert media_score_2 >= media_score_1 >= media_score_0
        assert 0 <= media_score_2 <= 5
        assert 0 <= media_score_1 <= 5
        assert 0 <= media_score_0 <= 5
    
    def test_comprehensive_tweet_analysis(self, value_analyzer, high_value_tweets, low_value_tweets):
        """测试综合推文分析
        
        验证完整的推文价值分析流程
        """
        # 分析高价值推文
        high_value_results = []
        for tweet in high_value_tweets:
            result = value_analyzer.analyze_tweet_value(tweet)
            high_value_results.append(result)
        
        # 分析低价值推文
        low_value_results = []
        for tweet in low_value_tweets:
            result = value_analyzer.analyze_tweet_value(tweet)
            low_value_results.append(result)
        
        # 验证高价值推文得分更高
        avg_high_score = sum(r['total_score'] for r in high_value_results) / len(high_value_results)
        avg_low_score = sum(r['total_score'] for r in low_value_results) / len(low_value_results)
        
        assert avg_high_score > avg_low_score
        
        # 验证评分结构
        for result in high_value_results + low_value_results:
            assert 'content_score' in result
            assert 'engagement_score' in result
            assert 'media_score' in result
            assert 'total_score' in result
            assert 0 <= result['total_score'] <= 5
    
    @pytest.mark.parametrize("content_weight,engagement_weight,media_weight", [
        (0.5, 0.3, 0.2),
        (0.4, 0.4, 0.2),
        (0.6, 0.2, 0.2),
        (0.3, 0.5, 0.2)
    ])
    def test_weight_adjustment_effects(self, value_analyzer, content_weight, engagement_weight, media_weight):
        """测试权重调整对评分的影响
        
        验证不同权重配置对最终评分的影响
        """
        test_tweet = {
            "content": "Artificial intelligence breakthrough in natural language processing",
            "likes": 1000,
            "retweets": 200,
            "replies": 50,
            "media_count": 1
        }
        
        # 使用不同权重分析
        result = value_analyzer.analyze_tweet_value(
            test_tweet,
            weights={
                'content': content_weight,
                'engagement': engagement_weight,
                'media': media_weight
            }
        )
        
        # 验证权重生效
        assert 'weights_used' in result
        assert result['weights_used']['content'] == content_weight
        assert result['weights_used']['engagement'] == engagement_weight
        assert result['weights_used']['media'] == media_weight
        
        # 验证总分在合理范围内
        assert 0 <= result['total_score'] <= 5
    
    @pytest.mark.parametrize("threshold", [2.5, 3.0, 3.5, 4.0, 5.0])
    def test_value_threshold_filtering(self, value_analyzer, sample_tweets, threshold):
        """测试价值阈值筛选
        
        验证筛选阈值能够正确过滤低价值推文
        """
        # 分析所有推文
        analyzed_tweets = []
        for tweet in sample_tweets:
            result = value_analyzer.analyze_tweet_value(tweet)
            tweet['value_score'] = result['total_score']
            analyzed_tweets.append(tweet)
        
        # 应用阈值筛选
        filtered_tweets = value_analyzer.filter_by_value_threshold(
            analyzed_tweets, 
            threshold=threshold
        )
        
        # 验证筛选结果
        assert all(tweet['value_score'] >= threshold for tweet in filtered_tweets)
        assert len(filtered_tweets) <= len(analyzed_tweets)
        
        # 验证筛选统计
        filtered_count = len(filtered_tweets)
        total_count = len(analyzed_tweets)
        retention_rate = filtered_count / total_count if total_count > 0 else 0
        
        assert 0 <= retention_rate <= 1
    
    def test_score_range_validation(self, value_analyzer, sample_tweets):
        """测试评分范围验证
        
        验证所有评分都在0-5的有效范围内
        """
        for tweet in sample_tweets:
            result = value_analyzer.analyze_tweet_value(tweet)
            
            # 验证各项评分范围
            assert 0 <= result['content_score'] <= 5
            assert 0 <= result['engagement_score'] <= 5
            assert 0 <= result['media_score'] <= 5
            assert 0 <= result['total_score'] <= 5
    
    def test_verified_user_bonus(self, value_analyzer):
        """测试认证用户加分
        
        验证认证用户的推文能够获得额外加分
        """
        base_tweet = {
            "content": "Standard tweet content",
            "likes": 100,
            "retweets": 20,
            "replies": 5,
            "media_count": 0
        }
        
        # 非认证用户
        unverified_tweet = {**base_tweet, "is_verified": False}
        unverified_result = value_analyzer.analyze_tweet_value(unverified_tweet)
        
        # 认证用户
        verified_tweet = {**base_tweet, "is_verified": True}
        verified_result = value_analyzer.analyze_tweet_value(verified_tweet)
        
        # 验证认证用户获得更高评分
        assert verified_result['total_score'] >= unverified_result['total_score']
    
    def test_hashtag_and_mention_scoring(self, value_analyzer):
        """测试话题标签和提及的评分影响
        
        验证话题标签和用户提及对评分的积极影响
        """
        base_tweet = {
            "content": "Tweet about technology",
            "likes": 100,
            "retweets": 20,
            "replies": 5,
            "media_count": 0,
            "is_verified": False
        }
        
        # 无标签和提及
        plain_tweet = {**base_tweet, "hashtags": [], "mentions": []}
        plain_result = value_analyzer.analyze_tweet_value(plain_tweet)
        
        # 包含标签和提及
        enhanced_tweet = {
            **base_tweet, 
            "hashtags": ["#AI", "#Technology"], 
            "mentions": ["@openai"]
        }
        enhanced_result = value_analyzer.analyze_tweet_value(enhanced_tweet)
        
        # 验证标签和提及提升评分
        assert enhanced_result['total_score'] >= plain_result['total_score']
    
    def test_content_length_scoring(self, value_analyzer):
        """测试内容长度对评分的影响
        
        验证适当的内容长度能够获得更好的评分
        """
        # 过短内容
        short_content = "Hi"
        short_score = value_analyzer.calculate_content_score(short_content)
        
        # 适中内容
        medium_content = "This is a well-structured tweet about artificial intelligence and its impact on society."
        medium_score = value_analyzer.calculate_content_score(medium_content)
        
        # 过长内容
        long_content = "This is an extremely long tweet that goes on and on about various topics without really saying much of substance or providing any meaningful insights that would be valuable to readers who are looking for quality content." * 2
        long_score = value_analyzer.calculate_content_score(long_content)
        
        # 验证适中长度获得最高评分
        assert medium_score >= short_score
        assert medium_score >= long_score
    
    def test_keyword_relevance_scoring(self, value_analyzer):
        """测试关键词相关性评分
        
        验证包含相关关键词的推文获得更高评分
        """
        # 包含高价值关键词
        relevant_content = "Breakthrough in artificial intelligence and machine learning research"
        relevant_score = value_analyzer.calculate_content_score(relevant_content)
        
        # 普通内容
        generic_content = "Having a great day today"
        generic_score = value_analyzer.calculate_content_score(generic_content)
        
        # 验证相关内容获得更高评分
        assert relevant_score > generic_score
    
    def test_engagement_ratio_analysis(self, value_analyzer):
        """测试互动比例分析
        
        验证互动比例（转发/点赞比等）对评分的影响
        """
        # 高转发比例（病毒式传播）
        viral_tweet = {
            "likes": 1000,
            "retweets": 800,  # 高转发比例
            "replies": 100
        }
        viral_score = value_analyzer.calculate_engagement_score(
            viral_tweet["likes"], viral_tweet["retweets"], viral_tweet["replies"]
        )
        
        # 高点赞比例（受欢迎但不传播）
        liked_tweet = {
            "likes": 1000,
            "retweets": 50,   # 低转发比例
            "replies": 100
        }
        liked_score = value_analyzer.calculate_engagement_score(
            liked_tweet["likes"], liked_tweet["retweets"], liked_tweet["replies"]
        )
        
        # 验证不同互动模式的评分
        assert viral_score > 0
        assert liked_score > 0
        # 病毒式传播通常获得更高评分
        assert viral_score >= liked_score
    
    def test_batch_analysis_performance(self, value_analyzer):
        """测试批量分析性能
        
        验证大量推文的批量价值分析性能
        """
        # 生成大量测试数据
        large_dataset = []
        for i in range(1000):
            tweet = {
                "id": str(i),
                "content": f"Test tweet number {i} about various topics",
                "likes": i * 10,
                "retweets": i * 2,
                "replies": i,
                "media_count": i % 3,
                "hashtags": [f"#tag{i % 5}"],
                "mentions": [],
                "is_verified": i % 10 == 0
            }
            large_dataset.append(tweet)
        
        # 执行批量分析
        results = value_analyzer.batch_analyze(large_dataset)
        
        # 验证结果
        assert len(results) == len(large_dataset)
        assert all('total_score' in result for result in results)
        assert all(0 <= result['total_score'] <= 5 for result in results)
    
    def test_edge_case_handling(self, value_analyzer):
        """测试边界情况处理
        
        验证对异常数据的处理能力
        """
        edge_cases = [
            # 负数互动量
            {
                "content": "Test tweet",
                "likes": -10,
                "retweets": -5,
                "replies": -2,
                "media_count": 0
            },
            # 极大互动量
            {
                "content": "Viral tweet",
                "likes": 10000000,
                "retweets": 5000000,
                "replies": 1000000,
                "media_count": 10
            },
            # 空内容
            {
                "content": "",
                "likes": 100,
                "retweets": 20,
                "replies": 5,
                "media_count": 1
            }
        ]
        
        for tweet in edge_cases:
            result = value_analyzer.analyze_tweet_value(tweet)
            
            # 验证结果有效性
            assert isinstance(result, dict)
            assert 'total_score' in result
            assert 0 <= result['total_score'] <= 5
    
    def test_custom_scoring_criteria(self, value_analyzer):
        """测试自定义评分标准
        
        验证能够应用自定义的评分标准
        """
        custom_criteria = {
            'min_likes': 100,
            'min_content_length': 50,
            'required_hashtags': ['#AI', '#Technology'],
            'bonus_keywords': ['breakthrough', 'innovation', 'research']
        }
        
        test_tweet = {
            "content": "Breakthrough in AI research shows innovation in technology",
            "likes": 150,
            "retweets": 30,
            "replies": 10,
            "media_count": 1,
            "hashtags": ["#AI", "#Technology"]
        }
        
        # 应用自定义标准
        result = value_analyzer.analyze_tweet_value(
            test_tweet, 
            custom_criteria=custom_criteria
        )
        
        # 验证自定义标准生效
        assert 'custom_criteria_met' in result
        assert result['total_score'] > 0

if __name__ == "__main__":
    pytest.main(["-v", __file__])