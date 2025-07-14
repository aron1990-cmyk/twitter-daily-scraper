#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 内容分析模块
提供推文质量评估、情感分析、趋势预测等AI功能
"""

import re
import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from collections import Counter
import asyncio

class AIContentAnalyzer:
    """
    AI内容分析器
    提供推文质量评估、情感分析、趋势预测等功能
    """
    
    def __init__(self):
        self.logger = logging.getLogger('AIAnalyzer')
        
        # 情感词典
        self.positive_words = {
            '好', '棒', '赞', '优秀', '完美', '成功', '胜利', '喜欢', '爱', '开心',
            '快乐', '满意', '惊喜', '兴奋', '激动', '感谢', '支持', '推荐', '值得',
            'good', 'great', 'awesome', 'excellent', 'perfect', 'amazing', 'love',
            'like', 'happy', 'excited', 'wonderful', 'fantastic', 'brilliant'
        }
        
        self.negative_words = {
            '坏', '差', '糟糕', '失败', '错误', '问题', '困难', '麻烦', '讨厌', '愤怒',
            '失望', '沮丧', '担心', '害怕', '痛苦', '悲伤', '抱怨', '批评', '反对',
            'bad', 'terrible', 'awful', 'horrible', 'hate', 'angry', 'sad', 'disappointed',
            'worried', 'afraid', 'problem', 'issue', 'fail', 'wrong', 'difficult'
        }
        
        # 质量指标权重
        self.quality_weights = {
            'engagement_score': 0.3,    # 互动分数权重
            'content_quality': 0.25,    # 内容质量权重
            'sentiment_score': 0.2,     # 情感分数权重
            'trend_relevance': 0.15,    # 趋势相关性权重
            'author_influence': 0.1     # 作者影响力权重
        }
        
        # 热门话题关键词
        self.trending_keywords = {
            'AI': ['AI', '人工智能', 'ChatGPT', 'GPT', '机器学习', '深度学习', 'LLM'],
            '创业': ['创业', '副业', '赚钱', '商业', '投资', '融资', '估值'],
            '科技': ['科技', '技术', '互联网', '数字化', '区块链', '元宇宙'],
            '生活': ['生活', '日常', '分享', '体验', '感悟', '思考'],
            '学习': ['学习', '教育', '知识', '技能', '成长', '进步']
        }
    
    def analyze_content_quality(self, tweet: Dict[str, Any]) -> float:
        """
        分析推文内容质量
        
        Args:
            tweet: 推文数据
            
        Returns:
            内容质量分数 (0-1)
        """
        content = tweet.get('content', '')
        if not content:
            return 0.0
        
        score = 0.0
        
        # 1. 长度评分 (适中长度得分更高)
        length = len(content)
        if 50 <= length <= 280:
            score += 0.3
        elif 20 <= length < 50 or 280 < length <= 500:
            score += 0.2
        elif length > 500:
            score += 0.1
        
        # 2. 结构评分
        # 包含链接
        if 'http' in content or 'www.' in content:
            score += 0.1
        
        # 包含话题标签
        if '#' in content:
            score += 0.1
        
        # 包含@提及
        if '@' in content:
            score += 0.05
        
        # 3. 内容丰富度
        # 包含数字或数据
        if re.search(r'\d+', content):
            score += 0.1
        
        # 包含问号（互动性）
        if '?' in content or '？' in content:
            score += 0.05
        
        # 4. 语言质量
        # 避免过多重复字符
        if not re.search(r'(.)\1{3,}', content):
            score += 0.1
        
        # 避免过多感叹号
        exclamation_count = content.count('!') + content.count('！')
        if exclamation_count <= 2:
            score += 0.1
        
        # 5. 专业性评分
        professional_indicators = ['分析', '报告', '数据', '研究', '观点', '见解', '总结']
        if any(indicator in content for indicator in professional_indicators):
            score += 0.1
        
        return min(score, 1.0)
    
    def analyze_sentiment(self, tweet: Dict[str, Any]) -> Tuple[float, str]:
        """
        分析推文情感倾向
        
        Args:
            tweet: 推文数据
            
        Returns:
            (情感分数, 情感标签) - 分数范围 -1 到 1，标签为 positive/neutral/negative
        """
        content = tweet.get('content', '').lower()
        if not content:
            return 0.0, 'neutral'
        
        positive_count = sum(1 for word in self.positive_words if word in content)
        negative_count = sum(1 for word in self.negative_words if word in content)
        
        # 计算情感分数
        total_words = len(content.split())
        if total_words == 0:
            return 0.0, 'neutral'
        
        sentiment_score = (positive_count - negative_count) / max(total_words, 1)
        
        # 归一化到 -1 到 1 范围
        sentiment_score = max(-1.0, min(1.0, sentiment_score * 10))
        
        # 确定情感标签
        if sentiment_score > 0.1:
            label = 'positive'
        elif sentiment_score < -0.1:
            label = 'negative'
        else:
            label = 'neutral'
        
        return sentiment_score, label
    
    def calculate_engagement_score(self, tweet: Dict[str, Any]) -> float:
        """
        计算互动分数
        
        Args:
            tweet: 推文数据
            
        Returns:
            互动分数 (0-1)
        """
        likes = tweet.get('likes', 0)
        comments = tweet.get('comments', 0)
        retweets = tweet.get('retweets', 0)
        
        # 加权计算互动分数
        engagement = likes * 1 + comments * 3 + retweets * 2
        
        # 使用对数缩放避免极值影响
        import math
        if engagement > 0:
            score = math.log10(engagement + 1) / 6  # 假设最高分对应1M互动
        else:
            score = 0
        
        return min(score, 1.0)
    
    def analyze_trend_relevance(self, tweet: Dict[str, Any]) -> Tuple[float, List[str]]:
        """
        分析趋势相关性
        
        Args:
            tweet: 推文数据
            
        Returns:
            (趋势相关性分数, 匹配的趋势话题列表)
        """
        content = tweet.get('content', '').lower()
        matched_trends = []
        relevance_score = 0.0
        
        for trend_category, keywords in self.trending_keywords.items():
            for keyword in keywords:
                if keyword.lower() in content:
                    matched_trends.append(trend_category)
                    relevance_score += 0.2
                    break  # 每个类别只计算一次
        
        return min(relevance_score, 1.0), list(set(matched_trends))
    
    def estimate_author_influence(self, tweet: Dict[str, Any]) -> float:
        """
        估算作者影响力
        
        Args:
            tweet: 推文数据
            
        Returns:
            影响力分数 (0-1)
        """
        # 基于推文的平均互动数估算影响力
        likes = tweet.get('likes', 0)
        comments = tweet.get('comments', 0)
        retweets = tweet.get('retweets', 0)
        
        # 简单的影响力估算模型
        total_engagement = likes + comments * 2 + retweets * 3
        
        # 使用对数缩放
        import math
        if total_engagement > 0:
            influence_score = math.log10(total_engagement + 1) / 7  # 假设顶级影响者有10M互动
        else:
            influence_score = 0
        
        return min(influence_score, 1.0)
    
    def calculate_overall_quality_score(self, tweet: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算综合质量分数
        
        Args:
            tweet: 推文数据
            
        Returns:
            包含各项分数和综合分数的字典
        """
        # 计算各项分数
        engagement_score = self.calculate_engagement_score(tweet)
        content_quality = self.analyze_content_quality(tweet)
        sentiment_score, sentiment_label = self.analyze_sentiment(tweet)
        trend_relevance, matched_trends = self.analyze_trend_relevance(tweet)
        author_influence = self.estimate_author_influence(tweet)
        
        # 将情感分数转换为正向分数 (0-1)
        sentiment_positive_score = (sentiment_score + 1) / 2
        
        # 计算加权综合分数
        overall_score = (
            engagement_score * self.quality_weights['engagement_score'] +
            content_quality * self.quality_weights['content_quality'] +
            sentiment_positive_score * self.quality_weights['sentiment_score'] +
            trend_relevance * self.quality_weights['trend_relevance'] +
            author_influence * self.quality_weights['author_influence']
        )
        
        return {
            'overall_score': overall_score,
            'engagement_score': engagement_score,
            'content_quality': content_quality,
            'sentiment_score': sentiment_score,
            'sentiment_label': sentiment_label,
            'trend_relevance': trend_relevance,
            'matched_trends': matched_trends,
            'author_influence': author_influence,
            'quality_grade': self._get_quality_grade(overall_score)
        }
    
    def _get_quality_grade(self, score: float) -> str:
        """
        根据分数获取质量等级
        
        Args:
            score: 质量分数
            
        Returns:
            质量等级字符串
        """
        if score >= 0.8:
            return 'A+'
        elif score >= 0.7:
            return 'A'
        elif score >= 0.6:
            return 'B+'
        elif score >= 0.5:
            return 'B'
        elif score >= 0.4:
            return 'C+'
        elif score >= 0.3:
            return 'C'
        else:
            return 'D'
    
    def analyze_trending_topics(self, tweets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析推文中的热门话题趋势
        
        Args:
            tweets: 推文列表
            
        Returns:
            趋势分析结果
        """
        topic_counts = Counter()
        hashtag_counts = Counter()
        mention_counts = Counter()
        
        for tweet in tweets:
            content = tweet.get('content', '')
            
            # 统计话题标签
            hashtags = re.findall(r'#(\w+)', content)
            hashtag_counts.update(hashtags)
            
            # 统计提及
            mentions = re.findall(r'@(\w+)', content)
            mention_counts.update(mentions)
            
            # 统计趋势话题
            _, matched_trends = self.analyze_trend_relevance(tweet)
            topic_counts.update(matched_trends)
        
        return {
            'trending_topics': dict(topic_counts.most_common(10)),
            'popular_hashtags': dict(hashtag_counts.most_common(10)),
            'frequent_mentions': dict(mention_counts.most_common(10)),
            'total_tweets_analyzed': len(tweets)
        }
    
    def predict_viral_potential(self, tweet: Dict[str, Any]) -> Dict[str, Any]:
        """
        预测推文的病毒传播潜力
        
        Args:
            tweet: 推文数据
            
        Returns:
            病毒传播潜力分析结果
        """
        quality_analysis = self.calculate_overall_quality_score(tweet)
        
        # 病毒传播因子
        viral_factors = {
            'high_engagement': quality_analysis['engagement_score'] > 0.7,
            'positive_sentiment': quality_analysis['sentiment_label'] == 'positive',
            'trend_relevant': quality_analysis['trend_relevance'] > 0.4,
            'influential_author': quality_analysis['author_influence'] > 0.6,
            'quality_content': quality_analysis['content_quality'] > 0.6
        }
        
        # 计算病毒传播潜力分数
        viral_score = sum(viral_factors.values()) / len(viral_factors)
        
        # 预测等级
        if viral_score >= 0.8:
            viral_level = 'Very High'
        elif viral_score >= 0.6:
            viral_level = 'High'
        elif viral_score >= 0.4:
            viral_level = 'Medium'
        elif viral_score >= 0.2:
            viral_level = 'Low'
        else:
            viral_level = 'Very Low'
        
        return {
            'viral_score': viral_score,
            'viral_level': viral_level,
            'viral_factors': viral_factors,
            'recommendation': self._get_viral_recommendation(viral_score)
        }
    
    def _get_viral_recommendation(self, viral_score: float) -> str:
        """
        根据病毒传播分数给出建议
        
        Args:
            viral_score: 病毒传播分数
            
        Returns:
            推荐建议
        """
        if viral_score >= 0.8:
            return "强烈推荐：具有极高传播潜力，建议重点关注和推广"
        elif viral_score >= 0.6:
            return "推荐：具有较高传播潜力，值得关注和分享"
        elif viral_score >= 0.4:
            return "一般：具有中等传播潜力，可以考虑适度推广"
        elif viral_score >= 0.2:
            return "谨慎：传播潜力较低，建议优化内容质量"
        else:
            return "不推荐：传播潜力很低，建议重新创作内容"
    
    async def batch_analyze_tweets(self, tweets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量分析推文
        
        Args:
            tweets: 推文列表
            
        Returns:
            包含AI分析结果的推文列表
        """
        analyzed_tweets = []
        
        for i, tweet in enumerate(tweets):
            try:
                # 进行AI分析
                quality_analysis = self.calculate_overall_quality_score(tweet)
                viral_analysis = self.predict_viral_potential(tweet)
                
                # 添加AI分析结果到推文数据
                enhanced_tweet = tweet.copy()
                enhanced_tweet.update({
                    'ai_analysis': {
                        'quality': quality_analysis,
                        'viral_potential': viral_analysis,
                        'analyzed_at': datetime.now().isoformat()
                    }
                })
                
                analyzed_tweets.append(enhanced_tweet)
                
                # 每处理10条推文记录一次进度
                if (i + 1) % 10 == 0:
                    self.logger.info(f"AI分析进度: {i + 1}/{len(tweets)}")
                
            except Exception as e:
                self.logger.error(f"分析推文时出错: {e}")
                # 即使分析失败也保留原始推文
                analyzed_tweets.append(tweet)
        
        self.logger.info(f"AI分析完成，共处理 {len(analyzed_tweets)} 条推文")
        return analyzed_tweets
    
    def generate_ai_insights_report(self, tweets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        生成AI洞察报告
        
        Args:
            tweets: 已分析的推文列表
            
        Returns:
            AI洞察报告
        """
        if not tweets:
            return {}
        
        # 统计各项指标
        quality_scores = []
        viral_scores = []
        sentiment_distribution = {'positive': 0, 'neutral': 0, 'negative': 0}
        grade_distribution = Counter()
        
        for tweet in tweets:
            ai_analysis = tweet.get('ai_analysis', {})
            if ai_analysis:
                quality = ai_analysis.get('quality', {})
                viral = ai_analysis.get('viral_potential', {})
                
                if quality:
                    quality_scores.append(quality.get('overall_score', 0))
                    sentiment_distribution[quality.get('sentiment_label', 'neutral')] += 1
                    grade_distribution[quality.get('quality_grade', 'D')] += 1
                
                if viral:
                    viral_scores.append(viral.get('viral_score', 0))
        
        # 计算统计数据
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        avg_viral = sum(viral_scores) / len(viral_scores) if viral_scores else 0
        
        # 趋势分析
        trend_analysis = self.analyze_trending_topics(tweets)
        
        return {
            'summary': {
                'total_tweets': len(tweets),
                'average_quality_score': round(avg_quality, 3),
                'average_viral_score': round(avg_viral, 3),
                'sentiment_distribution': sentiment_distribution,
                'quality_grade_distribution': dict(grade_distribution)
            },
            'trending_analysis': trend_analysis,
            'recommendations': self._generate_recommendations(tweets),
            'generated_at': datetime.now().isoformat()
        }
    
    def _generate_recommendations(self, tweets: List[Dict[str, Any]]) -> List[str]:
        """
        基于分析结果生成推荐建议
        
        Args:
            tweets: 已分析的推文列表
            
        Returns:
            推荐建议列表
        """
        recommendations = []
        
        if not tweets:
            return recommendations
        
        # 分析高质量推文特征
        high_quality_tweets = [
            tweet for tweet in tweets 
            if tweet.get('ai_analysis', {}).get('quality', {}).get('overall_score', 0) > 0.7
        ]
        
        if high_quality_tweets:
            recommendations.append(f"发现 {len(high_quality_tweets)} 条高质量推文，建议重点关注和学习其内容特征")
        
        # 分析情感倾向
        positive_tweets = [
            tweet for tweet in tweets 
            if tweet.get('ai_analysis', {}).get('quality', {}).get('sentiment_label') == 'positive'
        ]
        
        if len(positive_tweets) / len(tweets) > 0.6:
            recommendations.append("正面情感推文占比较高，有利于品牌形象建设")
        
        # 分析病毒传播潜力
        high_viral_tweets = [
            tweet for tweet in tweets 
            if tweet.get('ai_analysis', {}).get('viral_potential', {}).get('viral_score', 0) > 0.6
        ]
        
        if high_viral_tweets:
            recommendations.append(f"发现 {len(high_viral_tweets)} 条具有高传播潜力的推文，建议优先推广")
        
        # 趋势话题建议
        trend_analysis = self.analyze_trending_topics(tweets)
        top_topics = list(trend_analysis.get('trending_topics', {}).keys())[:3]
        if top_topics:
            recommendations.append(f"当前热门话题：{', '.join(top_topics)}，建议围绕这些话题创作内容")
        
        return recommendations