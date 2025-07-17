
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter采集系统性能优化器
解决效率、去重、内容丢失、搜索限制和价值识别问题
"""

import asyncio
import time
import threading
import logging
import hashlib
import re
from typing import List, Any, Callable, Optional, Dict, Set
from contextlib import asynccontextmanager
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from collections import defaultdict

# 简化版本，不依赖aiohttp
AIOHTTP_AVAILABLE = False

try:
    from models import PerformanceMetrics
except ImportError:
    # 如果models不存在，创建简单的数据类
    class PerformanceMetrics:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
        
        @property
        def success_rate(self):
            total = getattr(self, 'success_count', 0) + getattr(self, 'error_count', 0)
            return getattr(self, 'success_count', 0) / max(total, 1)

logger = logging.getLogger(__name__)


class AdvancedDeduplicator:
    """
    高级去重器 - 解决问题2：抓取的内容需要进行查重
    """
    
    def __init__(self):
        self.content_hashes: Set[str] = set()
        self.link_cache: Set[str] = set()
        self.similarity_cache: Dict[str, str] = {}
        self.stats = {'duplicates_removed': 0, 'total_processed': 0}
    
    def generate_content_hash(self, content: str) -> str:
        """生成内容哈希用于去重"""
        # 清理内容
        cleaned = re.sub(r'\s+', ' ', content.lower().strip())
        cleaned = re.sub(r'[^\w\s]', '', cleaned)  # 移除标点符号
        return hashlib.md5(cleaned.encode('utf-8')).hexdigest()
    
    def calculate_similarity(self, content1: str, content2: str) -> float:
        """计算两个内容的相似度"""
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        return intersection / union if union > 0 else 0.0
    
    def is_duplicate(self, tweet: Dict[str, Any], similarity_threshold: float = 0.8) -> bool:
        """高级去重检测"""
        self.stats['total_processed'] += 1
        
        content = tweet.get('content', '')
        link = tweet.get('link', '')
        
        # 1. 链接去重
        if link and link in self.link_cache:
            self.stats['duplicates_removed'] += 1
            return True
        
        # 2. 内容哈希去重
        content_hash = self.generate_content_hash(content)
        if content_hash in self.content_hashes:
            self.stats['duplicates_removed'] += 1
            return True
        
        # 3. 相似度去重
        for cached_hash, cached_content in self.similarity_cache.items():
            similarity = self.calculate_similarity(content, cached_content)
            if similarity >= similarity_threshold:
                self.stats['duplicates_removed'] += 1
                return True
        
        # 记录新内容
        if link:
            self.link_cache.add(link)
        self.content_hashes.add(content_hash)
        
        # 限制相似度缓存大小
        if len(self.similarity_cache) < 1000:
            self.similarity_cache[content_hash] = content
        
        return False


class TweetValueAnalyzer:
    """
    推文价值分析器 - 解决问题5：如何识别什么推文是没用的，什么推文是有用的
    """
    
    def __init__(self):
        # 高价值内容关键词
        self.value_keywords = {
            'tech': ['AI', 'GPT', '人工智能', '机器学习', 'ChatGPT', '深度学习', '算法', 'Python', 'JavaScript', '区块链', '加密货币'],
            'business': ['创业', '投资', '融资', '商业模式', '营销', '增长', '变现', '商业', '市场'],
            'trends': ['趋势', '未来', '预测', '分析', '洞察', '报告', '数据', '研究'],
            'engagement': ['讨论', '分享', '观点', '思考', '经验', '教程', '指南', '技巧']
        }
        
        # 无价值内容模式
        self.low_value_patterns = [
            r'^(转发|RT)\s*@',  # 纯转发
            r'^[😀-🙏]{3,}$',   # 纯表情
            r'^\s*$',          # 空内容
            r'^(好的|谢谢|👍|❤️)\s*$',  # 简单回复
            r'^(早安|晚安|午安)\s*[😀-🙏]*\s*$',  # 问候语
        ]
    
    def calculate_tweet_value_score(self, tweet: Dict[str, Any]) -> float:
        """计算推文价值分数"""
        score = 0.0
        content = tweet.get('content', '').lower()
        
        # 1. 检查是否为低价值内容
        for pattern in self.low_value_patterns:
            if re.match(pattern, content):
                return 0.0  # 直接判定为无价值
        
        # 2. 内容长度评分
        content_length = len(content)
        if content_length > 200:
            score += 2.0
        elif content_length > 100:
            score += 1.0
        elif content_length < 20:
            score -= 1.0
        
        # 3. 关键词匹配评分
        for category, keywords in self.value_keywords.items():
            matches = sum(1 for keyword in keywords if keyword.lower() in content)
            if matches > 0:
                score += matches * 1.5
        
        # 4. 互动数据评分
        likes = tweet.get('likes', 0)
        comments = tweet.get('comments', 0)
        retweets = tweet.get('retweets', 0)
        
        total_engagement = likes + comments * 2 + retweets * 3
        if total_engagement > 100:
            score += 3.0
        elif total_engagement > 50:
            score += 2.0
        elif total_engagement > 10:
            score += 1.0
        
        # 5. 媒体内容评分
        media = tweet.get('media', {})
        if media.get('images') or media.get('videos'):
            score += 1.5
        
        # 6. 时间新鲜度评分
        publish_time = tweet.get('publish_time')
        if publish_time:
            try:
                pub_time = datetime.fromisoformat(publish_time.replace('Z', '+00:00'))
                time_diff = datetime.now() - pub_time.replace(tzinfo=None)
                if time_diff < timedelta(hours=24):
                    score += 1.0
                elif time_diff < timedelta(days=7):
                    score += 0.5
            except:
                pass
        
        return max(0.0, score)
    
    def is_high_value_tweet(self, tweet: Dict[str, Any], threshold: float = 3.0) -> bool:
        """判断是否为高价值推文"""
        return self.calculate_tweet_value_score(tweet) >= threshold


class EnhancedSearchOptimizer:
    """
    增强搜索优化器 - 解决问题4：搜索关键词获得的推文很少
    """
    
    def get_enhanced_search_queries(self, keyword: str) -> List[str]:
        """生成增强的搜索查询，提高搜索结果数量"""
        queries = []
        
        # 1. 基础查询
        queries.append(keyword)
        
        # 2. 添加时间过滤（最近推文）
        queries.append(f"{keyword} since:2024-01-01")
        
        # 3. 添加语言过滤
        if any(ord(char) > 127 for char in keyword):  # 包含中文
            queries.append(f"{keyword} lang:zh")
        else:
            queries.append(f"{keyword} lang:en")
        
        # 4. 添加最小互动过滤
        queries.append(f"{keyword} min_replies:1")
        queries.append(f"{keyword} min_faves:5")
        
        # 5. 排除转发（获取原创内容）
        queries.append(f"{keyword} -filter:retweets")
        
        # 6. 包含链接的推文
        queries.append(f"{keyword} filter:links")
        
        # 7. 包含媒体的推文
        queries.append(f"{keyword} filter:media")
        
        return queries
    
    def optimize_scroll_strategy(self, current_tweets: int, target_tweets: int, 
                               scroll_attempts: int) -> Dict[str, Any]:
        """优化滚动策略 - 解决问题3：内容丢失问题"""
        # 计算滚动效率
        efficiency = current_tweets / max(scroll_attempts, 1)
        
        strategy = {
            'scroll_distance': 1500,  # 默认滚动距离
            'wait_time': 0.3,         # 默认等待时间
            'max_scrolls': 20,        # 最大滚动次数
            'should_continue': True,
            'aggressive_mode': False   # 激进模式
        }
        
        # 根据效率调整策略
        if efficiency < 0.5:  # 效率低，启用激进模式
            strategy['scroll_distance'] = 2500  # 大幅增加滚动距离
            strategy['wait_time'] = 0.8         # 增加等待时间
            strategy['max_scrolls'] = 50        # 大幅增加最大滚动次数
            strategy['aggressive_mode'] = True
        elif efficiency > 2.0:  # 效率高
            strategy['scroll_distance'] = 1000  # 减少滚动距离
            strategy['wait_time'] = 0.2         # 减少等待时间
        
        # 检查是否应该停止滚动
        if scroll_attempts > strategy['max_scrolls']:
            strategy['should_continue'] = False
        
        # 如果已达到目标数量的80%，可以考虑停止
        if current_tweets >= target_tweets * 0.8:
            strategy['should_continue'] = False
        
        return strategy


class HighSpeedCollector:
    """
    高速采集器 - 解决问题1：1小时内采集1500条推文
    """
    
    def __init__(self):
        self.deduplicator = AdvancedDeduplicator()
        self.value_analyzer = TweetValueAnalyzer()
        self.search_optimizer = EnhancedSearchOptimizer()
        self.stats = {
            'total_collected': 0,
            'high_value_tweets': 0,
            'processing_time': 0,
            'collection_rate': 0  # 推文/分钟
        }
    
    def calculate_target_rate(self, target_tweets: int = 1500, time_limit_hours: int = 1) -> float:
        """计算目标采集速率"""
        return target_tweets / (time_limit_hours * 60)  # 推文/分钟
    
    def process_tweets_batch(self, tweets: List[Dict[str, Any]], 
                           enable_dedup: bool = True,
                           enable_value_filter: bool = True) -> List[Dict[str, Any]]:
        """批量处理推文：去重、价值筛选、优化"""
        start_time = time.time()
        processed_tweets = []
        
        for tweet in tweets:
            # 去重检查
            if enable_dedup and self.deduplicator.is_duplicate(tweet):
                continue
            
            # 价值筛选
            if enable_value_filter:
                value_score = self.value_analyzer.calculate_tweet_value_score(tweet)
                tweet['value_score'] = value_score
                
                if self.value_analyzer.is_high_value_tweet(tweet):
                    self.stats['high_value_tweets'] += 1
                    processed_tweets.append(tweet)
                elif value_score > 1.0:  # 中等价值也保留
                    processed_tweets.append(tweet)
            else:
                tweet['value_score'] = self.value_analyzer.calculate_tweet_value_score(tweet)
                processed_tweets.append(tweet)
        
        # 按价值分数排序
        processed_tweets.sort(key=lambda x: x.get('value_score', 0), reverse=True)
        
        self.stats['total_collected'] += len(processed_tweets)
        self.stats['processing_time'] += time.time() - start_time
        
        # 计算采集速率
        if self.stats['processing_time'] > 0:
            self.stats['collection_rate'] = (self.stats['total_collected'] / self.stats['processing_time']) * 60
        
        return processed_tweets
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        return {
            'collection_stats': self.stats.copy(),
            'deduplication_stats': self.deduplicator.stats.copy(),
            'efficiency_metrics': {
                'deduplication_rate': self.deduplicator.stats['duplicates_removed'] / max(self.deduplicator.stats['total_processed'], 1),
                'high_value_rate': self.stats['high_value_tweets'] / max(self.stats['total_collected'], 1),
                'collection_rate_per_minute': self.stats['collection_rate'],
                'target_rate_1500_per_hour': 25.0,  # 目标：25推文/分钟
                'rate_achievement': (self.stats['collection_rate'] / 25.0) * 100 if self.stats['collection_rate'] > 0 else 0
            }
        }


class AsyncBatchProcessor:
    """异步批处理器"""
    
    def __init__(self, max_workers: int = 10, batch_size: int = 50):
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.semaphore = asyncio.Semaphore(max_workers)
    
    async def process_batch(self, items: List[Any], processor: Callable) -> List[Any]:
        """批量处理项目"""
        results = []
        
        # 分批处理
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batch_tasks = [self._process_item(item, processor) for item in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            results.extend(batch_results)
        
        return results
    
    async def _process_item(self, item: Any, processor: Callable) -> Any:
        """处理单个项目"""
        async with self.semaphore:
            try:
                if asyncio.iscoroutinefunction(processor):
                    return await processor(item)
                else:
                    loop = asyncio.get_event_loop()
                    return await loop.run_in_executor(None, processor, item)
            except Exception as e:
                logger.error(f"处理项目失败: {e}")
                return e



class MemoryOptimizer:
    """内存优化器"""
    
    def __init__(self, max_memory_mb: int = 1024):
        self.max_memory_mb = max_memory_mb
        self._data_cache = {}
        self._cache_size = 0
    
    def cache_data(self, key: str, data: Any, size_mb: float):
        """缓存数据"""
        # 检查内存限制
        if self._cache_size + size_mb > self.max_memory_mb:
            self._evict_cache()
        
        self._data_cache[key] = data
        self._cache_size += size_mb
    
    def get_cached_data(self, key: str) -> Optional[Any]:
        """获取缓存数据"""
        return self._data_cache.get(key)
    
    def get_memory_usage(self) -> float:
        """获取当前内存使用量（MB）"""
        return self._cache_size
    
    def _evict_cache(self):
        """清理缓存"""
        # 简单的LRU策略：清理一半缓存
        keys_to_remove = list(self._data_cache.keys())[:len(self._data_cache) // 2]
        for key in keys_to_remove:
            del self._data_cache[key]
        
        self._cache_size = self._cache_size // 2
        logger.info(f"缓存清理完成，当前大小: {self._cache_size}MB")

class ThreadSafeQueue:
    """线程安全队列"""
    
    def __init__(self, maxsize: int = 1000):
        self._queue = Queue(maxsize=maxsize)
        self._shutdown = threading.Event()
    
    def put(self, item: Any, timeout: Optional[float] = None):
        """添加项目到队列"""
        if not self._shutdown.is_set():
            self._queue.put(item, timeout=timeout)
    
    def get(self, timeout: Optional[float] = None) -> Optional[Any]:
        """从队列获取项目"""
        try:
            return self._queue.get(timeout=timeout)
        except Empty:
            return None
    
    def shutdown(self):
        """关闭队列"""
        self._shutdown.set()
    
    def is_shutdown(self) -> bool:
        """检查是否已关闭"""
        return self._shutdown.is_set()

class PerformanceProfiler:
    """性能分析器"""
    
    def __init__(self):
        self.metrics: List[PerformanceMetrics] = []
    
    @asynccontextmanager
    async def profile(self, operation_name: str):
        """性能分析上下文管理器"""
        import psutil
        
        start_time = time.time()
        start_memory = psutil.virtual_memory().percent
        start_cpu = psutil.cpu_percent()
        
        success_count = 0
        error_count = 0
        
        def _create_counter():
            """创建计数器"""
            nonlocal success_count, error_count
            
            class Counter:
                def success(self):
                    nonlocal success_count
                    success_count += 1
                
                def error(self):
                    nonlocal error_count
                    error_count += 1
            
            return Counter()
        
        try:
            yield _create_counter()
        finally:
            end_time = time.time()
            end_memory = psutil.virtual_memory().percent
            end_cpu = psutil.cpu_percent()
            
            metrics = PerformanceMetrics(
                start_time=start_time,
                end_time=end_time,
                duration=end_time - start_time,
                memory_usage=end_memory - start_memory,
                cpu_usage=end_cpu - start_cpu,
                success_count=success_count,
                error_count=error_count
            )
            
            self.metrics.append(metrics)
            
            logger.info(
                f"性能分析 - {operation_name}",
                extra={
                    'duration': metrics.duration,
                    'memory_delta': metrics.memory_usage,
                    'cpu_delta': metrics.cpu_usage,
                    'success_rate': metrics.success_rate
                }
            )
    
    def get_average_metrics(self) -> Optional[Dict[str, float]]:
        """获取平均性能指标"""
        if not self.metrics:
            return None
        
        return {
            'avg_duration': sum(m.duration for m in self.metrics) / len(self.metrics),
            'avg_memory_usage': sum(m.memory_usage for m in self.metrics) / len(self.metrics),
            'avg_cpu_usage': sum(m.cpu_usage for m in self.metrics) / len(self.metrics),
            'avg_success_rate': sum(m.success_rate for m in self.metrics) / len(self.metrics)
        }

# 全局实例
batch_processor = AsyncBatchProcessor()
memory_optimizer = MemoryOptimizer()
performance_profiler = PerformanceProfiler()
