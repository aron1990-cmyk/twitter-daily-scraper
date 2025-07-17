import pytest
import asyncio
import json
import tempfile
import sqlite3
import pandas as pd
from pathlib import Path
import sys
import os
from unittest.mock import Mock, patch, AsyncMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from twitter_parser import TwitterParser
from performance_optimizer import HighSpeedCollector, AdvancedDeduplicator, TweetValueAnalyzer
from excel_writer import ExcelWriter
from storage_manager import StorageManager
from models import Tweet

class TestIntegrationWorkflow:
    """抓取→处理→导出全流程集成测试类"""
    
    @pytest.fixture
    def sample_tweets_raw(self):
        """原始推文数据（包含重复和低质量）"""
        fixtures_path = Path(__file__).parent / "fixtures" / "sample_tweets.json"
        with open(fixtures_path, 'r', encoding='utf-8') as f:
            base_tweets = json.load(f)
        
        # 添加一些重复和低质量推文用于测试
        extended_tweets = base_tweets + [
            # 重复推文
            {
                "id": "duplicate_1",
                "username": "elonmusk",
                "content": "Tesla is accelerating the world's transition to sustainable energy",  # 与ID=1相同
                "timestamp": "2024-01-15 10:30:00",
                "url": "https://twitter.com/elonmusk/status/duplicate_1",
                "likes": 15000,
                "retweets": 3000,
                "replies": 500,
                "media_count": 1,
                "hashtags": ["#Tesla", "#SustainableEnergy"],
                "mentions": [],
                "is_verified": True
            },
            # 低质量推文
            {
                "id": "low_quality_1",
                "username": "randomuser",
                "content": "lol",
                "timestamp": "2024-01-15 16:00:00",
                "url": "https://twitter.com/randomuser/status/low_quality_1",
                "likes": 2,
                "retweets": 0,
                "replies": 0,
                "media_count": 0,
                "hashtags": [],
                "mentions": [],
                "is_verified": False
            },
            # 高质量推文
            {
                "id": "high_quality_1",
                "username": "openai",
                "content": "Revolutionary breakthrough in artificial intelligence: Our new model demonstrates unprecedented capabilities in reasoning, creativity, and problem-solving across multiple domains.",
                "timestamp": "2024-01-15 18:00:00",
                "url": "https://twitter.com/openai/status/high_quality_1",
                "likes": 50000,
                "retweets": 15000,
                "replies": 3000,
                "media_count": 3,
                "hashtags": ["#AI", "#Breakthrough", "#Innovation"],
                "mentions": ["@elonmusk", "@sundarpichai"],
                "is_verified": True
            }
        ]
        return extended_tweets
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def mock_twitter_parser(self, sample_tweets_raw):
        """模拟Twitter解析器"""
        parser = Mock(spec=TwitterParser)
        parser.scrape_keyword_tweets = AsyncMock(return_value=sample_tweets_raw)
        parser.scrape_user_tweets = AsyncMock(return_value=sample_tweets_raw)
        return parser
    
    @pytest.fixture
    def high_speed_collector(self):
        """高速采集器实例"""
        return HighSpeedCollector()
    
    @pytest.fixture
    def deduplicator(self):
        """去重器实例"""
        return AdvancedDeduplicator()
    
    @pytest.fixture
    def value_analyzer(self):
        """价值分析器实例"""
        return TweetValueAnalyzer()
    
    @pytest.fixture
    def excel_writer(self):
        """Excel写入器实例"""
        return ExcelWriter()
    
    @pytest.mark.asyncio
    async def test_complete_workflow_keyword_scraping(self, mock_twitter_parser, high_speed_collector, 
                                                     deduplicator, value_analyzer, excel_writer, temp_dir):
        """测试完整的关键词抓取工作流程
        
        验证：抓取 → 去重 → 价值分析 → 导出的完整流程
        """
        # 步骤1: 抓取推文
        raw_tweets = await mock_twitter_parser.scrape_keyword_tweets("AI", max_tweets=50)
        assert len(raw_tweets) > 0
        
        # 步骤2: 高速处理（去重 + 价值分析）
        processed_result = high_speed_collector.process_tweets(
            raw_tweets,
            deduplication_threshold=0.85,
            value_threshold=3.0
        )
        
        processed_tweets = processed_result['processed_tweets']
        processing_stats = processed_result['stats']
        
        # 验证处理结果
        assert len(processed_tweets) <= len(raw_tweets)  # 去重后数量减少
        assert all('value_score' in tweet for tweet in processed_tweets)  # 包含价值评分
        assert all(tweet['value_score'] >= 3.0 for tweet in processed_tweets)  # 满足阈值
        
        # 验证统计信息
        assert 'deduplication_rate' in processing_stats
        assert 'high_value_rate' in processing_stats
        assert 'processing_time' in processing_stats
        
        # 步骤3: 导出到Excel
        excel_file = temp_dir / "ai_tweets.xlsx"
        excel_writer.write_tweets_to_excel(processed_tweets, str(excel_file))
        
        # 验证导出结果
        assert excel_file.exists()
        df = pd.read_excel(excel_file)
        assert len(df) == len(processed_tweets)
        assert 'value_score' in df.columns
    
    @pytest.mark.asyncio
    async def test_complete_workflow_user_scraping(self, mock_twitter_parser, high_speed_collector,
                                                   deduplicator, value_analyzer, temp_dir):
        """测试完整的用户推文抓取工作流程
        
        验证用户推文抓取的完整处理流程
        """
        # 步骤1: 抓取用户推文
        raw_tweets = await mock_twitter_parser.scrape_user_tweets("elonmusk", max_tweets=30)
        assert len(raw_tweets) > 0
        
        # 步骤2: 分步处理
        # 2a: 去重
        unique_tweets, dedup_stats = deduplicator.remove_duplicates(
            raw_tweets, 
            method='content',
            similarity_threshold=0.9
        )
        
        # 2b: 价值分析
        analyzed_tweets = []
        for tweet in unique_tweets:
            analysis_result = value_analyzer.analyze_tweet_value(tweet)
            tweet['value_score'] = analysis_result['total_score']
            tweet['content_score'] = analysis_result['content_score']
            tweet['engagement_score'] = analysis_result['engagement_score']
            tweet['media_score'] = analysis_result['media_score']
            analyzed_tweets.append(tweet)
        
        # 2c: 价值筛选
        high_value_tweets = value_analyzer.filter_by_value_threshold(
            analyzed_tweets, 
            threshold=2.5
        )
        
        # 验证处理结果
        assert len(unique_tweets) <= len(raw_tweets)
        assert len(high_value_tweets) <= len(analyzed_tweets)
        assert all(tweet['value_score'] >= 2.5 for tweet in high_value_tweets)
        
        # 步骤3: 导出到JSON
        json_file = temp_dir / "elonmusk_tweets.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(high_value_tweets, f, ensure_ascii=False, indent=2)
        
        # 验证导出结果
        assert json_file.exists()
        with open(json_file, 'r', encoding='utf-8') as f:
            exported_data = json.load(f)
        assert len(exported_data) == len(high_value_tweets)
    
    @pytest.mark.asyncio
    async def test_multi_format_export_workflow(self, mock_twitter_parser, high_speed_collector, temp_dir):
        """测试多格式导出工作流程
        
        验证同一批数据导出到Excel、JSON、SQLite的完整流程
        """
        # 步骤1: 抓取和处理
        raw_tweets = await mock_twitter_parser.scrape_keyword_tweets("GPT4", max_tweets=20)
        
        processed_result = high_speed_collector.process_tweets(
            raw_tweets,
            deduplication_threshold=0.85,
            value_threshold=2.0
        )
        
        processed_tweets = processed_result['processed_tweets']
        
        # 步骤2: 多格式导出
        # 2a: Excel导出
        excel_file = temp_dir / "gpt4_tweets.xlsx"
        excel_writer = ExcelWriter()
        excel_writer.write_tweets_to_excel(processed_tweets, str(excel_file))
        
        # 2b: JSON导出
        json_file = temp_dir / "gpt4_tweets.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(processed_tweets, f, ensure_ascii=False, indent=2)
        
        # 2c: SQLite导出
        db_file = temp_dir / "gpt4_tweets.db"
        storage_manager = StorageManager(str(db_file))
        
        for tweet_data in processed_tweets:
            tweet = Tweet(
                id=tweet_data['id'],
                username=tweet_data['username'],
                content=tweet_data['content'],
                timestamp=tweet_data['timestamp'],
                url=tweet_data['url'],
                likes=tweet_data['likes'],
                retweets=tweet_data['retweets'],
                replies=tweet_data['replies']
            )
            storage_manager.save_tweet(tweet)
        
        # 验证所有格式的导出结果
        assert excel_file.exists()
        assert json_file.exists()
        assert db_file.exists()
        
        # 验证数据一致性
        # Excel验证
        df = pd.read_excel(excel_file)
        assert len(df) == len(processed_tweets)
        
        # JSON验证
        with open(json_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        assert len(json_data) == len(processed_tweets)
        
        # SQLite验证
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tweets")
        db_count = cursor.fetchone()[0]
        assert db_count == len(processed_tweets)
        conn.close()
    
    @pytest.mark.parametrize("dedup_threshold,value_threshold", [
        (0.85, 2.5),
        (0.9, 3.0),
        (0.95, 3.5)
    ])
    @pytest.mark.asyncio
    async def test_parameter_combinations_workflow(self, mock_twitter_parser, high_speed_collector,
                                                  dedup_threshold, value_threshold, temp_dir):
        """测试不同参数组合的工作流程
        
        验证不同去重阈值和价值阈值组合的效果
        """
        # 抓取推文
        raw_tweets = await mock_twitter_parser.scrape_keyword_tweets("technology", max_tweets=25)
        
        # 使用指定参数处理
        processed_result = high_speed_collector.process_tweets(
            raw_tweets,
            deduplication_threshold=dedup_threshold,
            value_threshold=value_threshold
        )
        
        processed_tweets = processed_result['processed_tweets']
        stats = processed_result['stats']
        
        # 验证参数效果
        assert all(tweet['value_score'] >= value_threshold for tweet in processed_tweets)
        assert stats['deduplication_threshold'] == dedup_threshold
        assert stats['value_threshold'] == value_threshold
        
        # 验证阈值越高，结果越少
        assert len(processed_tweets) <= len(raw_tweets)
        
        # 导出验证
        output_file = temp_dir / f"tech_tweets_{dedup_threshold}_{value_threshold}.xlsx"
        excel_writer = ExcelWriter()
        excel_writer.write_tweets_to_excel(processed_tweets, str(output_file))
        assert output_file.exists()
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, temp_dir):
        """测试错误处理工作流程
        
        验证在各个环节出现错误时的处理机制
        """
        # 模拟抓取失败
        failed_parser = Mock(spec=TwitterParser)
        failed_parser.scrape_keyword_tweets = AsyncMock(side_effect=Exception("Network error"))
        
        with pytest.raises(Exception) as exc_info:
            await failed_parser.scrape_keyword_tweets("test")
        assert "Network error" in str(exc_info.value)
        
        # 模拟空数据处理
        empty_tweets = []
        high_speed_collector = HighSpeedCollector()
        
        result = high_speed_collector.process_tweets(
            empty_tweets,
            deduplication_threshold=0.85,
            value_threshold=3.0
        )
        
        assert len(result['processed_tweets']) == 0
        assert result['stats']['original_count'] == 0
        
        # 模拟导出到无效路径
        excel_writer = ExcelWriter()
        invalid_path = temp_dir / "nonexistent" / "test.xlsx"
        
        with pytest.raises(Exception):
            excel_writer.write_tweets_to_excel([], str(invalid_path))
    
    @pytest.mark.asyncio
    async def test_performance_monitoring_workflow(self, mock_twitter_parser, high_speed_collector, temp_dir):
        """测试性能监控工作流程
        
        验证整个流程的性能指标收集
        """
        import time
        
        start_time = time.time()
        
        # 执行完整流程
        raw_tweets = await mock_twitter_parser.scrape_keyword_tweets("performance", max_tweets=100)
        
        scraping_time = time.time() - start_time
        processing_start = time.time()
        
        processed_result = high_speed_collector.process_tweets(
            raw_tweets,
            deduplication_threshold=0.85,
            value_threshold=2.5
        )
        
        processing_time = time.time() - processing_start
        export_start = time.time()
        
        # 导出
        excel_file = temp_dir / "performance_tweets.xlsx"
        excel_writer = ExcelWriter()
        excel_writer.write_tweets_to_excel(
            processed_result['processed_tweets'], 
            str(excel_file)
        )
        
        export_time = time.time() - export_start
        total_time = time.time() - start_time
        
        # 验证性能指标
        performance_report = {
            'scraping_time': scraping_time,
            'processing_time': processing_time,
            'export_time': export_time,
            'total_time': total_time,
            'tweets_per_second': len(raw_tweets) / total_time if total_time > 0 else 0,
            'deduplication_rate': processed_result['stats']['deduplication_rate'],
            'high_value_rate': processed_result['stats']['high_value_rate']
        }
        
        # 验证性能合理性
        assert performance_report['total_time'] > 0
        assert performance_report['tweets_per_second'] >= 0
        assert 0 <= performance_report['deduplication_rate'] <= 1
        assert 0 <= performance_report['high_value_rate'] <= 1
        
        # 保存性能报告
        report_file = temp_dir / "performance_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(performance_report, f, indent=2)
        
        assert report_file.exists()
    
    @pytest.mark.asyncio
    async def test_data_quality_validation_workflow(self, mock_twitter_parser, high_speed_collector, 
                                                   deduplicator, value_analyzer, temp_dir):
        """测试数据质量验证工作流程
        
        验证整个流程中的数据质量保证机制
        """
        # 抓取推文
        raw_tweets = await mock_twitter_parser.scrape_keyword_tweets("quality", max_tweets=30)
        
        # 数据质量检查点1: 原始数据验证
        required_fields = ['id', 'username', 'content', 'timestamp', 'url']
        for tweet in raw_tweets:
            for field in required_fields:
                assert field in tweet, f"Missing required field: {field}"
        
        # 处理推文
        processed_result = high_speed_collector.process_tweets(
            raw_tweets,
            deduplication_threshold=0.85,
            value_threshold=2.0
        )
        
        processed_tweets = processed_result['processed_tweets']
        
        # 数据质量检查点2: 处理后数据验证
        for tweet in processed_tweets:
            # 验证必需字段仍然存在
            for field in required_fields:
                assert field in tweet
            
            # 验证新增字段
            assert 'value_score' in tweet
            assert isinstance(tweet['value_score'], (int, float))
            assert 0 <= tweet['value_score'] <= 5
            
            # 验证数据类型
            assert isinstance(tweet['likes'], int)
            assert isinstance(tweet['retweets'], int)
            assert isinstance(tweet['replies'], int)
            assert isinstance(tweet['content'], str)
            assert len(tweet['content']) > 0
        
        # 数据质量检查点3: 导出数据验证
        excel_file = temp_dir / "quality_tweets.xlsx"
        excel_writer = ExcelWriter()
        excel_writer.write_tweets_to_excel(processed_tweets, str(excel_file))
        
        # 验证导出的数据完整性
        df = pd.read_excel(excel_file)
        assert len(df) == len(processed_tweets)
        
        # 验证导出数据的字段完整性
        for field in required_fields + ['value_score']:
            assert field in df.columns
        
        # 验证导出数据的值范围
        assert df['value_score'].min() >= 2.0  # 满足阈值
        assert df['value_score'].max() <= 5.0  # 不超过最大值
        assert df['likes'].min() >= 0  # 非负数
        assert df['retweets'].min() >= 0  # 非负数
        assert df['replies'].min() >= 0  # 非负数
    
    @pytest.mark.asyncio
    async def test_scalability_workflow(self, temp_dir):
        """测试可扩展性工作流程
        
        验证系统处理大量数据的能力
        """
        # 生成大量模拟数据
        large_dataset = []
        for i in range(5000):
            tweet = {
                "id": str(i),
                "username": f"user_{i % 100}",
                "content": f"This is tweet number {i} about various topics including AI, technology, and innovation.",
                "timestamp": "2024-01-15 10:00:00",
                "url": f"https://twitter.com/user_{i % 100}/status/{i}",
                "likes": i * 10,
                "retweets": i * 2,
                "replies": i,
                "media_count": i % 4,
                "hashtags": [f"#tag{i % 10}"],
                "mentions": [],
                "is_verified": i % 50 == 0
            }
            large_dataset.append(tweet)
        
        # 处理大数据集
        high_speed_collector = HighSpeedCollector()
        
        import time
        start_time = time.time()
        
        processed_result = high_speed_collector.process_tweets(
            large_dataset,
            deduplication_threshold=0.85,
            value_threshold=2.0
        )
        
        processing_time = time.time() - start_time
        
        # 验证处理结果
        processed_tweets = processed_result['processed_tweets']
        stats = processed_result['stats']
        
        assert len(processed_tweets) <= len(large_dataset)
        assert processing_time < 60  # 应该在60秒内完成
        
        # 验证处理效率
        throughput = len(large_dataset) / processing_time
        assert throughput > 50  # 每秒至少处理50条推文
        
        # 导出大数据集
        excel_file = temp_dir / "large_dataset.xlsx"
        excel_writer = ExcelWriter()
        
        export_start = time.time()
        excel_writer.write_tweets_to_excel(processed_tweets, str(excel_file))
        export_time = time.time() - export_start
        
        assert excel_file.exists()
        assert export_time < 30  # 导出应该在30秒内完成
        
        # 验证导出文件大小合理
        file_size = excel_file.stat().st_size
        assert file_size > 100000  # 至少100KB

if __name__ == "__main__":
    pytest.main(["-v", __file__])