# -*- coding: utf-8 -*-
"""
推文筛选器
根据配置的条件筛选推文数据
"""

import logging
from typing import List, Dict, Any
from config import FILTER_CONFIG

class TweetFilter:
    def __init__(self):
        self.min_likes = FILTER_CONFIG['min_likes']
        self.min_comments = FILTER_CONFIG['min_comments']
        self.min_retweets = FILTER_CONFIG['min_retweets']
        self.keywords_filter = FILTER_CONFIG['keywords_filter']
        self.logger = logging.getLogger(__name__)
    
    def check_engagement_threshold(self, tweet: Dict[str, Any]) -> bool:
        """
        检查推文是否满足互动数阈值
        
        Args:
            tweet: 推文数据字典
            
        Returns:
            是否满足阈值条件
        """
        likes = tweet.get('likes', 0)
        comments = tweet.get('comments', 0)
        retweets = tweet.get('retweets', 0)
        
        # 满足任一条件即通过
        if likes >= self.min_likes:
            self.logger.debug(f"推文通过点赞数筛选: {likes} >= {self.min_likes}")
            return True
        
        if comments >= self.min_comments:
            self.logger.debug(f"推文通过评论数筛选: {comments} >= {self.min_comments}")
            return True
        
        if retweets >= self.min_retweets:
            self.logger.debug(f"推文通过转发数筛选: {retweets} >= {self.min_retweets}")
            return True
        
        return False
    
    def check_keyword_filter(self, tweet: Dict[str, Any]) -> bool:
        """
        检查推文内容是否包含指定关键词
        
        Args:
            tweet: 推文数据字典
            
        Returns:
            是否包含关键词
        """
        content = tweet.get('content', '').lower()
        
        for keyword in self.keywords_filter:
            if keyword.lower() in content:
                self.logger.debug(f"推文包含关键词 '{keyword}': {content[:50]}...")
                return True
        
        return False
    
    def is_valid_tweet(self, tweet: Dict[str, Any]) -> bool:
        """
        检查推文是否有效（包含基本必要信息）
        
        Args:
            tweet: 推文数据字典
            
        Returns:
            是否为有效推文
        """
        # 检查必要字段
        required_fields = ['username', 'content']
        for field in required_fields:
            if not tweet.get(field):
                self.logger.debug(f"推文缺少必要字段: {field}")
                return False
        
        # 检查内容长度
        content = tweet.get('content', '')
        if len(content.strip()) < 10:  # 内容太短可能是无效推文
            self.logger.debug(f"推文内容过短: {content}")
            return False
        
        return True
    
    def filter_tweet(self, tweet: Dict[str, Any]) -> Dict[str, Any]:
        """
        对单条推文进行筛选并添加筛选原因
        
        Args:
            tweet: 推文数据字典
            
        Returns:
            包含筛选结果的推文数据
        """
        # 复制推文数据
        filtered_tweet = tweet.copy()
        
        # 初始化筛选结果
        filtered_tweet['filter_passed'] = False
        filtered_tweet['filter_reasons'] = []
        
        # 检查推文有效性
        if not self.is_valid_tweet(tweet):
            filtered_tweet['filter_reasons'].append('无效推文')
            return filtered_tweet
        
        # 检查互动数阈值
        engagement_passed = self.check_engagement_threshold(tweet)
        if engagement_passed:
            filtered_tweet['filter_reasons'].append('满足互动数阈值')
        
        # 检查关键词
        keyword_passed = self.check_keyword_filter(tweet)
        if keyword_passed:
            filtered_tweet['filter_reasons'].append('包含目标关键词')
        
        # 满足任一条件即通过筛选
        if engagement_passed or keyword_passed:
            filtered_tweet['filter_passed'] = True
            self.logger.info(f"推文通过筛选: @{tweet.get('username')} - {', '.join(filtered_tweet['filter_reasons'])}")
        else:
            filtered_tweet['filter_reasons'].append('未满足任何筛选条件')
            self.logger.debug(f"推文未通过筛选: @{tweet.get('username')}")
        
        return filtered_tweet
    
    def filter_tweets(self, tweets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量筛选推文
        
        Args:
            tweets: 推文数据列表
            
        Returns:
            筛选后的推文数据列表
        """
        if not tweets:
            self.logger.warning("没有推文数据需要筛选")
            return []
        
        self.logger.info(f"开始筛选 {len(tweets)} 条推文")
        
        filtered_tweets = []
        passed_count = 0
        
        for i, tweet in enumerate(tweets):
            try:
                filtered_tweet = self.filter_tweet(tweet)
                filtered_tweets.append(filtered_tweet)
                
                if filtered_tweet['filter_passed']:
                    passed_count += 1
                    
            except Exception as e:
                self.logger.error(f"筛选第 {i+1} 条推文时发生错误: {e}")
                # 添加错误信息到推文数据中
                error_tweet = tweet.copy()
                error_tweet['filter_passed'] = False
                error_tweet['filter_reasons'] = [f'筛选过程出错: {str(e)}']
                filtered_tweets.append(error_tweet)
        
        self.logger.info(f"筛选完成: {passed_count}/{len(tweets)} 条推文通过筛选")
        return filtered_tweets
    
    def get_passed_tweets(self, filtered_tweets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        获取通过筛选的推文
        
        Args:
            filtered_tweets: 已筛选的推文数据列表
            
        Returns:
            通过筛选的推文列表
        """
        passed_tweets = [tweet for tweet in filtered_tweets if tweet.get('filter_passed', False)]
        self.logger.info(f"获取到 {len(passed_tweets)} 条通过筛选的推文")
        return passed_tweets
    
    def get_filter_statistics(self, filtered_tweets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        获取筛选统计信息
        
        Args:
            filtered_tweets: 已筛选的推文数据列表
            
        Returns:
            筛选统计信息
        """
        total_count = len(filtered_tweets)
        passed_count = len([t for t in filtered_tweets if t.get('filter_passed', False)])
        
        # 统计各种筛选原因
        reason_stats = {}
        for tweet in filtered_tweets:
            reasons = tweet.get('filter_reasons', [])
            for reason in reasons:
                reason_stats[reason] = reason_stats.get(reason, 0) + 1
        
        # 统计互动数据
        engagement_stats = {
            'total_likes': sum(t.get('likes', 0) for t in filtered_tweets),
            'total_comments': sum(t.get('comments', 0) for t in filtered_tweets),
            'total_retweets': sum(t.get('retweets', 0) for t in filtered_tweets),
            'avg_likes': sum(t.get('likes', 0) for t in filtered_tweets) / total_count if total_count > 0 else 0,
            'avg_comments': sum(t.get('comments', 0) for t in filtered_tweets) / total_count if total_count > 0 else 0,
            'avg_retweets': sum(t.get('retweets', 0) for t in filtered_tweets) / total_count if total_count > 0 else 0,
        }
        
        statistics = {
            'total_tweets': total_count,
            'passed_tweets': passed_count,
            'pass_rate': passed_count / total_count if total_count > 0 else 0,
            'filter_reasons': reason_stats,
            'engagement_stats': engagement_stats,
            'filter_config': {
                'min_likes': self.min_likes,
                'min_comments': self.min_comments,
                'min_retweets': self.min_retweets,
                'keywords': self.keywords_filter
            }
        }
        
        return statistics
    
    def update_filter_config(self, **kwargs):
        """
        更新筛选配置
        
        Args:
            **kwargs: 配置参数
        """
        if 'min_likes' in kwargs:
            self.min_likes = kwargs['min_likes']
            self.logger.info(f"更新最小点赞数阈值: {self.min_likes}")
        
        if 'min_comments' in kwargs:
            self.min_comments = kwargs['min_comments']
            self.logger.info(f"更新最小评论数阈值: {self.min_comments}")
        
        if 'min_retweets' in kwargs:
            self.min_retweets = kwargs['min_retweets']
            self.logger.info(f"更新最小转发数阈值: {self.min_retweets}")
        
        if 'keywords_filter' in kwargs:
            self.keywords_filter = kwargs['keywords_filter']
            self.logger.info(f"更新关键词筛选: {self.keywords_filter}")

# 使用示例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 示例推文数据
    sample_tweets = [
        {
            'username': 'elonmusk',
            'content': 'AI is the future of humanity',
            'likes': 1500,
            'comments': 200,
            'retweets': 800,
            'publish_time': '2024-01-01T12:00:00Z',
            'link': 'https://twitter.com/elonmusk/status/123'
        },
        {
            'username': 'openai',
            'content': 'Just a regular tweet about technology',
            'likes': 50,
            'comments': 10,
            'retweets': 20,
            'publish_time': '2024-01-01T13:00:00Z',
            'link': 'https://twitter.com/openai/status/124'
        },
        {
            'username': 'techuser',
            'content': '今天学习了一个新的副业技巧',
            'likes': 80,
            'comments': 25,
            'retweets': 15,
            'publish_time': '2024-01-01T14:00:00Z',
            'link': 'https://twitter.com/techuser/status/125'
        }
    ]
    
    # 创建筛选器
    filter_engine = TweetFilter()
    
    # 筛选推文
    filtered_tweets = filter_engine.filter_tweets(sample_tweets)
    
    # 获取通过筛选的推文
    passed_tweets = filter_engine.get_passed_tweets(filtered_tweets)
    
    # 显示结果
    print(f"\n筛选结果:")
    for tweet in passed_tweets:
        print(f"@{tweet['username']}: {tweet['content'][:50]}...")
        print(f"筛选原因: {', '.join(tweet['filter_reasons'])}")
        print("-" * 50)
    
    # 显示统计信息
    stats = filter_engine.get_filter_statistics(filtered_tweets)
    print(f"\n统计信息:")
    print(f"总推文数: {stats['total_tweets']}")
    print(f"通过筛选: {stats['passed_tweets']}")
    print(f"通过率: {stats['pass_rate']:.2%}")