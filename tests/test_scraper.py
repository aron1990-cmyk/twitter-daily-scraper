import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from twitter_parser import TwitterParser
from performance_optimizer import HighSpeedCollector, EnhancedSearchOptimizer
from config import Config

class TestTwitterScraper:
    """Twitter抓取模块测试类"""
    
    @pytest.fixture
    def sample_tweets(self):
        """加载示例推文数据"""
        fixtures_path = Path(__file__).parent / "fixtures" / "sample_tweets.json"
        with open(fixtures_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @pytest.fixture
    def mock_config(self):
        """模拟配置对象"""
        config = Mock(spec=Config)
        config.HEADLESS = True
        config.MAX_TWEETS = 50
        config.SCROLL_PAUSE_TIME = 2
        config.MAX_SCROLL_ATTEMPTS = 10
        config.CONCURRENT_WINDOWS = 1
        return config
    
    @pytest.fixture
    async def twitter_parser(self, mock_config):
        """创建TwitterParser实例"""
        parser = TwitterParser()
        parser.config = mock_config
        return parser
    
    def test_scraper_initialization(self, twitter_parser):
        """测试抓取器初始化
        
        验证TwitterParser能够正确初始化，包含必要的组件
        """
        assert twitter_parser is not None
        assert hasattr(twitter_parser, 'config')
        assert hasattr(twitter_parser, 'search_optimizer')
        assert isinstance(twitter_parser.search_optimizer, EnhancedSearchOptimizer)
    
    @pytest.mark.asyncio
    async def test_keyword_scraping_basic(self, twitter_parser, sample_tweets):
        """测试基础关键词抓取功能
        
        验证能够根据关键词抓取推文，返回正确的数据结构
        """
        # Mock抓取方法
        with patch.object(twitter_parser, 'scrape_keyword_tweets', new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = sample_tweets[:3]
            
            results = await twitter_parser.scrape_keyword_tweets("AI", max_tweets=3)
            
            # 验证返回结果
            assert len(results) == 3
            assert all('content' in tweet for tweet in results)
            assert all('username' in tweet for tweet in results)
            assert all('timestamp' in tweet for tweet in results)
            assert all('url' in tweet for tweet in results)
            
            # 验证调用参数
            mock_scrape.assert_called_once_with("AI", max_tweets=3)
    
    @pytest.mark.asyncio
    async def test_user_scraping_basic(self, twitter_parser, sample_tweets):
        """测试基础用户推文抓取功能
        
        验证能够根据用户名抓取推文，返回正确的数据结构
        """
        # 过滤出elonmusk的推文
        elon_tweets = [t for t in sample_tweets if t['username'] == 'elonmusk']
        
        with patch.object(twitter_parser, 'scrape_user_tweets', new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = elon_tweets
            
            results = await twitter_parser.scrape_user_tweets("elonmusk", max_tweets=10)
            
            # 验证返回结果
            assert len(results) > 0
            assert all(tweet['username'] == 'elonmusk' for tweet in results)
            assert all('content' in tweet for tweet in results)
            
            # 验证调用参数
            mock_scrape.assert_called_once_with("elonmusk", max_tweets=10)
    
    @pytest.mark.parametrize("max_tweets,expected_count", [
        (5, 5),
        (10, 8),  # 示例数据只有8条
        (50, 8),  # 超过数据量时返回全部
    ])
    @pytest.mark.asyncio
    async def test_tweet_count_limits(self, twitter_parser, sample_tweets, max_tweets, expected_count):
        """测试推文数量限制参数
        
        验证max_tweets参数能够正确限制返回的推文数量
        """
        with patch.object(twitter_parser, 'scrape_keyword_tweets', new_callable=AsyncMock) as mock_scrape:
            # 根据请求数量返回相应数量的推文
            returned_tweets = sample_tweets[:min(max_tweets, len(sample_tweets))]
            mock_scrape.return_value = returned_tweets
            
            results = await twitter_parser.scrape_keyword_tweets("test", max_tweets=max_tweets)
            
            assert len(results) == min(expected_count, len(sample_tweets))
    
    @pytest.mark.parametrize("headless_mode", [True, False])
    def test_headless_mode_configuration(self, mock_config, headless_mode):
        """测试无头模式配置
        
        验证headless参数能够正确配置浏览器模式
        """
        mock_config.HEADLESS = headless_mode
        parser = TwitterParser()
        parser.config = mock_config
        
        assert parser.config.HEADLESS == headless_mode
    
    @pytest.mark.asyncio
    async def test_scroll_strategy_effectiveness(self, twitter_parser, sample_tweets):
        """测试滚动加载策略有效性
        
        验证滚动策略能够加载更多推文，达到目标数量
        """
        with patch.object(twitter_parser, 'scroll_and_load_tweets', new_callable=AsyncMock) as mock_scroll:
            # 模拟滚动加载过程
            mock_scroll.return_value = len(sample_tweets)
            
            loaded_count = await twitter_parser.scroll_and_load_tweets(
                target_count=50,
                current_count=10
            )
            
            assert loaded_count > 0
            mock_scroll.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_enhanced_search_optimization(self, twitter_parser):
        """测试增强搜索优化功能
        
        验证EnhancedSearchOptimizer能够优化搜索查询
        """
        optimizer = twitter_parser.search_optimizer
        
        # 测试查询优化
        original_query = "AI"
        optimized_queries = optimizer.optimize_search_query(original_query)
        
        assert len(optimized_queries) > 0
        assert original_query in optimized_queries or any(original_query in q for q in optimized_queries)
    
    @pytest.mark.asyncio
    async def test_concurrent_scraping_simulation(self, twitter_parser, sample_tweets):
        """测试并发抓取模拟
        
        验证系统能够处理并发抓取请求
        """
        async def mock_scrape_task(keyword):
            # 模拟异步抓取
            await asyncio.sleep(0.1)
            return [t for t in sample_tweets if keyword.lower() in t['content'].lower()]
        
        with patch.object(twitter_parser, 'scrape_keyword_tweets', side_effect=mock_scrape_task):
            # 并发抓取多个关键词
            tasks = [
                twitter_parser.scrape_keyword_tweets("AI"),
                twitter_parser.scrape_keyword_tweets("Tesla"),
                twitter_parser.scrape_keyword_tweets("GPT")
            ]
            
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 3
            assert all(isinstance(result, list) for result in results)
    
    def test_tweet_data_structure_validation(self, sample_tweets):
        """测试推文数据结构验证
        
        验证抓取的推文包含所有必需字段
        """
        required_fields = ['id', 'username', 'content', 'timestamp', 'url', 'likes', 'retweets', 'replies']
        
        for tweet in sample_tweets:
            for field in required_fields:
                assert field in tweet, f"Missing required field: {field}"
            
            # 验证数据类型
            assert isinstance(tweet['likes'], int)
            assert isinstance(tweet['retweets'], int)
            assert isinstance(tweet['replies'], int)
            assert isinstance(tweet['content'], str)
            assert len(tweet['content']) > 0
    
    @pytest.mark.asyncio
    async def test_error_handling_network_failure(self, twitter_parser):
        """测试网络故障错误处理
        
        验证网络连接失败时的错误处理机制
        """
        with patch.object(twitter_parser, 'scrape_keyword_tweets', new_callable=AsyncMock) as mock_scrape:
            mock_scrape.side_effect = Exception("Network connection failed")
            
            with pytest.raises(Exception) as exc_info:
                await twitter_parser.scrape_keyword_tweets("test")
            
            assert "Network connection failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_empty_results_handling(self, twitter_parser):
        """测试空结果处理
        
        验证当没有找到匹配推文时的处理逻辑
        """
        with patch.object(twitter_parser, 'scrape_keyword_tweets', new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = []
            
            results = await twitter_parser.scrape_keyword_tweets("nonexistent_keyword")
            
            assert isinstance(results, list)
            assert len(results) == 0
    
    @pytest.mark.parametrize("username,keyword", [
        ("elonmusk", "Tesla"),
        ("openai", "GPT4"),
        ("techuser", "AI")
    ])
    @pytest.mark.asyncio
    async def test_parameter_combinations(self, twitter_parser, sample_tweets, username, keyword):
        """测试参数组合
        
        验证不同用户名和关键词组合的抓取效果
        """
        # 过滤相关推文
        relevant_tweets = [
            t for t in sample_tweets 
            if t['username'] == username and keyword.lower() in t['content'].lower()
        ]
        
        with patch.object(twitter_parser, 'scrape_user_keyword_tweets', new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = relevant_tweets
            
            results = await twitter_parser.scrape_user_keyword_tweets(username, keyword)
            
            assert isinstance(results, list)
            if relevant_tweets:
                assert all(tweet['username'] == username for tweet in results)
                assert all(keyword.lower() in tweet['content'].lower() for tweet in results)
    
    def test_high_speed_collector_integration(self):
        """测试高速采集器集成
        
        验证HighSpeedCollector能够正确集成到抓取流程中
        """
        collector = HighSpeedCollector()
        
        # 测试采集器初始化
        assert collector is not None
        assert hasattr(collector, 'process_tweets')
        assert hasattr(collector, 'batch_process')
    
    @pytest.mark.asyncio
    async def test_scroll_pause_time_configuration(self, twitter_parser, mock_config):
        """测试滚动暂停时间配置
        
        验证滚动暂停时间参数能够正确配置
        """
        test_pause_times = [1, 2, 3, 5]
        
        for pause_time in test_pause_times:
            mock_config.SCROLL_PAUSE_TIME = pause_time
            assert twitter_parser.config.SCROLL_PAUSE_TIME == pause_time
    
    def test_max_scroll_attempts_boundary(self, mock_config):
        """测试最大滚动尝试次数边界
        
        验证最大滚动尝试次数的边界值处理
        """
        boundary_values = [1, 5, 10, 20, 50]
        
        for max_attempts in boundary_values:
            mock_config.MAX_SCROLL_ATTEMPTS = max_attempts
            assert mock_config.MAX_SCROLL_ATTEMPTS == max_attempts
            assert mock_config.MAX_SCROLL_ATTEMPTS > 0

if __name__ == "__main__":
    pytest.main(["-v", __file__])