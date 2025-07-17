import pytest
import json
import hashlib
from pathlib import Path
import sys
import os
from unittest.mock import Mock, patch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from performance_optimizer import AdvancedDeduplicator

class TestAdvancedDeduplicator:
    """高级去重模块测试类"""
    
    @pytest.fixture
    def sample_tweets(self):
        """加载示例推文数据"""
        fixtures_path = Path(__file__).parent / "fixtures" / "sample_tweets.json"
        with open(fixtures_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @pytest.fixture
    def deduplicator(self):
        """创建去重器实例"""
        return AdvancedDeduplicator()
    
    @pytest.fixture
    def duplicate_tweets(self):
        """创建包含重复推文的测试数据"""
        return [
            {
                "id": "1",
                "username": "user1",
                "content": "This is a test tweet about AI technology",
                "timestamp": "2024-01-15 10:00:00",
                "url": "https://twitter.com/user1/status/1",
                "likes": 100,
                "retweets": 20,
                "replies": 5
            },
            {
                "id": "2",
                "username": "user2",
                "content": "This is a test tweet about AI technology",  # 完全相同内容
                "timestamp": "2024-01-15 11:00:00",
                "url": "https://twitter.com/user2/status/2",
                "likes": 50,
                "retweets": 10,
                "replies": 2
            },
            {
                "id": "3",
                "username": "user3",
                "content": "This is a test tweet about artificial intelligence technology",  # 相似内容
                "timestamp": "2024-01-15 12:00:00",
                "url": "https://twitter.com/user3/status/3",
                "likes": 75,
                "retweets": 15,
                "replies": 3
            },
            {
                "id": "1",  # 重复ID
                "username": "user1",
                "content": "This is a test tweet about AI technology",
                "timestamp": "2024-01-15 10:00:00",
                "url": "https://twitter.com/user1/status/1",  # 重复URL
                "likes": 100,
                "retweets": 20,
                "replies": 5
            },
            {
                "id": "4",
                "username": "user4",
                "content": "Completely different tweet about sports",
                "timestamp": "2024-01-15 13:00:00",
                "url": "https://twitter.com/user4/status/4",
                "likes": 30,
                "retweets": 5,
                "replies": 1
            }
        ]
    
    def test_deduplicator_initialization(self, deduplicator):
        """测试去重器初始化
        
        验证AdvancedDeduplicator能够正确初始化
        """
        assert deduplicator is not None
        assert hasattr(deduplicator, 'remove_duplicates')
        assert hasattr(deduplicator, 'calculate_similarity')
        assert hasattr(deduplicator, 'generate_content_hash')
    
    def test_url_based_deduplication(self, deduplicator, duplicate_tweets):
        """测试基于URL的去重
        
        验证能够正确识别和移除具有相同URL的重复推文
        """
        # 执行去重
        unique_tweets, stats = deduplicator.remove_duplicates(
            duplicate_tweets, 
            method='url'
        )
        
        # 验证去重结果
        urls = [tweet['url'] for tweet in unique_tweets]
        assert len(urls) == len(set(urls))  # 所有URL都是唯一的
        
        # 验证统计信息
        assert 'duplicates_removed' in stats
        assert stats['duplicates_removed'] > 0
        assert len(unique_tweets) < len(duplicate_tweets)
    
    def test_content_based_deduplication(self, deduplicator, duplicate_tweets):
        """测试基于内容的去重
        
        验证能够正确识别和移除具有相同内容的重复推文
        """
        # 执行去重
        unique_tweets, stats = deduplicator.remove_duplicates(
            duplicate_tweets, 
            method='content'
        )
        
        # 验证去重结果
        contents = [tweet['content'] for tweet in unique_tweets]
        assert len(contents) == len(set(contents))  # 所有内容都是唯一的
        
        # 验证统计信息
        assert stats['duplicates_removed'] > 0
    
    def test_hash_based_deduplication(self, deduplicator, duplicate_tweets):
        """测试基于哈希的去重
        
        验证能够使用内容哈希正确识别重复推文
        """
        # 执行去重
        unique_tweets, stats = deduplicator.remove_duplicates(
            duplicate_tweets, 
            method='hash'
        )
        
        # 验证去重结果
        hashes = [deduplicator.generate_content_hash(tweet['content']) for tweet in unique_tweets]
        assert len(hashes) == len(set(hashes))  # 所有哈希都是唯一的
        
        # 验证统计信息
        assert stats['duplicates_removed'] > 0
    
    def test_timestamp_based_deduplication(self, deduplicator):
        """测试基于时间戳的去重
        
        验证能够识别在相同时间发布的重复推文
        """
        timestamp_duplicates = [
            {
                "id": "1",
                "content": "Tweet 1",
                "timestamp": "2024-01-15 10:00:00",
                "url": "https://twitter.com/user1/status/1"
            },
            {
                "id": "2",
                "content": "Tweet 2",
                "timestamp": "2024-01-15 10:00:00",  # 相同时间戳
                "url": "https://twitter.com/user2/status/2"
            },
            {
                "id": "3",
                "content": "Tweet 3",
                "timestamp": "2024-01-15 11:00:00",
                "url": "https://twitter.com/user3/status/3"
            }
        ]
        
        # 执行去重
        unique_tweets, stats = deduplicator.remove_duplicates(
            timestamp_duplicates, 
            method='timestamp'
        )
        
        # 验证去重结果
        timestamps = [tweet['timestamp'] for tweet in unique_tweets]
        assert len(timestamps) == len(set(timestamps))  # 所有时间戳都是唯一的
    
    @pytest.mark.parametrize("similarity_threshold", [0.8, 0.85, 0.9, 0.95])
    def test_similarity_threshold_adjustment(self, deduplicator, similarity_threshold):
        """测试相似度阈值调整
        
        验证不同相似度阈值对去重结果的影响
        """
        similar_tweets = [
            {
                "id": "1",
                "content": "AI technology is advancing rapidly",
                "url": "https://twitter.com/user1/status/1"
            },
            {
                "id": "2",
                "content": "Artificial intelligence technology is advancing quickly",
                "url": "https://twitter.com/user2/status/2"
            },
            {
                "id": "3",
                "content": "Machine learning is a subset of AI",
                "url": "https://twitter.com/user3/status/3"
            }
        ]
        
        # 执行去重
        unique_tweets, stats = deduplicator.remove_duplicates(
            similar_tweets, 
            method='similarity',
            similarity_threshold=similarity_threshold
        )
        
        # 验证阈值影响
        assert len(unique_tweets) <= len(similar_tweets)
        assert 'similarity_threshold' in stats
        assert stats['similarity_threshold'] == similarity_threshold
    
    def test_calculate_similarity_function(self, deduplicator):
        """测试相似度计算函数
        
        验证相似度计算的准确性
        """
        text1 = "This is a test tweet about AI"
        text2 = "This is a test tweet about AI"  # 完全相同
        text3 = "This is a test tweet about artificial intelligence"  # 相似
        text4 = "Completely different content about sports"  # 完全不同
        
        # 测试完全相同的文本
        similarity1 = deduplicator.calculate_similarity(text1, text2)
        assert similarity1 == 1.0
        
        # 测试相似文本
        similarity2 = deduplicator.calculate_similarity(text1, text3)
        assert 0.5 < similarity2 < 1.0
        
        # 测试完全不同的文本
        similarity3 = deduplicator.calculate_similarity(text1, text4)
        assert similarity3 < 0.5
    
    def test_content_hash_generation(self, deduplicator):
        """测试内容哈希生成
        
        验证内容哈希生成的一致性和唯一性
        """
        content1 = "This is a test tweet"
        content2 = "This is a test tweet"  # 相同内容
        content3 = "This is a different tweet"  # 不同内容
        
        hash1 = deduplicator.generate_content_hash(content1)
        hash2 = deduplicator.generate_content_hash(content2)
        hash3 = deduplicator.generate_content_hash(content3)
        
        # 验证相同内容生成相同哈希
        assert hash1 == hash2
        
        # 验证不同内容生成不同哈希
        assert hash1 != hash3
        
        # 验证哈希格式
        assert isinstance(hash1, str)
        assert len(hash1) > 0
    
    def test_deduplication_statistics(self, deduplicator, duplicate_tweets):
        """测试去重统计信息
        
        验证去重过程中统计信息的准确性
        """
        original_count = len(duplicate_tweets)
        
        # 执行去重
        unique_tweets, stats = deduplicator.remove_duplicates(duplicate_tweets)
        
        # 验证统计信息
        assert 'original_count' in stats
        assert 'unique_count' in stats
        assert 'duplicates_removed' in stats
        assert 'deduplication_rate' in stats
        
        assert stats['original_count'] == original_count
        assert stats['unique_count'] == len(unique_tweets)
        assert stats['duplicates_removed'] == original_count - len(unique_tweets)
        
        # 验证去重率计算
        expected_rate = stats['duplicates_removed'] / original_count
        assert abs(stats['deduplication_rate'] - expected_rate) < 0.01
    
    def test_deduplication_rate_calculation(self, deduplicator):
        """测试去重率计算准确性
        
        验证去重率在报告中的准确体现
        """
        test_tweets = [
            {"id": "1", "content": "Tweet 1", "url": "url1"},
            {"id": "2", "content": "Tweet 2", "url": "url2"},
            {"id": "1", "content": "Tweet 1", "url": "url1"},  # 重复
            {"id": "3", "content": "Tweet 3", "url": "url3"},
            {"id": "2", "content": "Tweet 2", "url": "url2"},  # 重复
        ]
        
        unique_tweets, stats = deduplicator.remove_duplicates(test_tweets)
        
        # 验证去重率
        expected_rate = 2 / 5  # 5个推文中移除2个重复
        assert abs(stats['deduplication_rate'] - expected_rate) < 0.01
        assert len(unique_tweets) == 3
    
    def test_empty_input_handling(self, deduplicator):
        """测试空输入处理
        
        验证当输入为空时的处理逻辑
        """
        empty_tweets = []
        
        unique_tweets, stats = deduplicator.remove_duplicates(empty_tweets)
        
        assert len(unique_tweets) == 0
        assert stats['original_count'] == 0
        assert stats['unique_count'] == 0
        assert stats['duplicates_removed'] == 0
        assert stats['deduplication_rate'] == 0.0
    
    def test_single_tweet_handling(self, deduplicator):
        """测试单条推文处理
        
        验证只有一条推文时的处理逻辑
        """
        single_tweet = [{
            "id": "1",
            "content": "Single tweet",
            "url": "https://twitter.com/user/status/1"
        }]
        
        unique_tweets, stats = deduplicator.remove_duplicates(single_tweet)
        
        assert len(unique_tweets) == 1
        assert stats['original_count'] == 1
        assert stats['unique_count'] == 1
        assert stats['duplicates_removed'] == 0
        assert stats['deduplication_rate'] == 0.0
    
    @pytest.mark.parametrize("method", ['url', 'content', 'hash', 'similarity'])
    def test_different_deduplication_methods(self, deduplicator, duplicate_tweets, method):
        """测试不同去重方法
        
        验证各种去重方法都能正常工作
        """
        unique_tweets, stats = deduplicator.remove_duplicates(
            duplicate_tweets, 
            method=method
        )
        
        # 验证基本结果
        assert isinstance(unique_tweets, list)
        assert isinstance(stats, dict)
        assert len(unique_tweets) <= len(duplicate_tweets)
        
        # 验证统计信息
        assert 'method' in stats
        assert stats['method'] == method
    
    def test_preserve_highest_engagement(self, deduplicator):
        """测试保留最高互动量的推文
        
        验证在去重时保留互动量最高的推文版本
        """
        engagement_duplicates = [
            {
                "id": "1",
                "content": "Same content",
                "url": "url1",
                "likes": 100,
                "retweets": 20,
                "replies": 5
            },
            {
                "id": "2",
                "content": "Same content",
                "url": "url2",
                "likes": 500,  # 更高的互动量
                "retweets": 100,
                "replies": 25
            }
        ]
        
        unique_tweets, stats = deduplicator.remove_duplicates(
            engagement_duplicates, 
            method='content',
            preserve_highest_engagement=True
        )
        
        # 验证保留了互动量更高的推文
        assert len(unique_tweets) == 1
        assert unique_tweets[0]['likes'] == 500
        assert unique_tweets[0]['id'] == "2"
    
    def test_batch_deduplication_performance(self, deduplicator):
        """测试批量去重性能
        
        验证大量数据的去重性能
        """
        # 生成大量测试数据
        large_dataset = []
        for i in range(1000):
            tweet = {
                "id": str(i % 100),  # 创建重复ID
                "content": f"Tweet content {i % 50}",  # 创建重复内容
                "url": f"https://twitter.com/user/status/{i % 100}",
                "likes": i,
                "retweets": i // 2,
                "replies": i // 5
            }
            large_dataset.append(tweet)
        
        # 执行去重
        unique_tweets, stats = deduplicator.remove_duplicates(large_dataset)
        
        # 验证性能和结果
        assert len(unique_tweets) < len(large_dataset)
        assert stats['duplicates_removed'] > 0
        assert 'processing_time' in stats  # 假设去重器记录处理时间
    
    def test_malformed_data_handling(self, deduplicator):
        """测试畸形数据处理
        
        验证对缺少必需字段的推文的处理
        """
        malformed_tweets = [
            {
                "id": "1",
                "content": "Normal tweet",
                "url": "https://twitter.com/user/status/1"
            },
            {
                "id": "2",
                # 缺少content字段
                "url": "https://twitter.com/user/status/2"
            },
            {
                # 缺少id字段
                "content": "Tweet without ID",
                "url": "https://twitter.com/user/status/3"
            }
        ]
        
        # 执行去重，应该能够处理畸形数据
        unique_tweets, stats = deduplicator.remove_duplicates(malformed_tweets)
        
        # 验证结果
        assert isinstance(unique_tweets, list)
        assert isinstance(stats, dict)
        # 具体行为取决于实现，可能过滤掉畸形数据或保留它们
    
    def test_unicode_content_deduplication(self, deduplicator):
        """测试Unicode内容去重
        
        验证包含Unicode字符的推文去重
        """
        unicode_tweets = [
            {
                "id": "1",
                "content": "推文内容包含中文字符 😀🚀",
                "url": "https://twitter.com/user1/status/1"
            },
            {
                "id": "2",
                "content": "推文内容包含中文字符 😀🚀",  # 相同Unicode内容
                "url": "https://twitter.com/user2/status/2"
            },
            {
                "id": "3",
                "content": "Different content with émojis 🎉",
                "url": "https://twitter.com/user3/status/3"
            }
        ]
        
        unique_tweets, stats = deduplicator.remove_duplicates(
            unicode_tweets, 
            method='content'
        )
        
        # 验证Unicode内容去重
        assert len(unique_tweets) == 2  # 应该移除一个重复的中文推文
        contents = [tweet['content'] for tweet in unique_tweets]
        assert len(set(contents)) == 2

if __name__ == "__main__":
    pytest.main(["-v", __file__])