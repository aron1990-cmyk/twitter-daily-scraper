#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版推文抓取器 - 支持数据库保存和飞书同步
"""

import os
import sys
import json
import time
import argparse
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入项目模块
from simple_100_tweets_test import Simple100TweetsTester
from cloud_sync import CloudSyncManager
from models import TweetModel

# 数据库相关导入
try:
    from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.exc import IntegrityError
except ImportError:
    print("请安装SQLAlchemy: pip install sqlalchemy")
    sys.exit(1)

# 添加项目根目录到Python路径，以便导入web_app模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enhanced_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EnhancedScraper')

# 数据库模型
Base = declarative_base()

class TweetData(Base):
    """推文数据模型"""
    __tablename__ = 'tweet_data'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    retweets = Column(Integer, default=0)
    publish_time = Column(String(100))
    link = Column(Text)
    hashtags = Column(Text)  # JSON格式存储
    content_type = Column(String(50))
    scraped_at = Column(DateTime, default=datetime.utcnow)
    synced_to_feishu = Column(Boolean, default=False)
    
    # 增强内容字段
    full_content = Column(Text)
    media_content = Column(Text)  # JSON格式存储
    thread_tweets = Column(Text)  # JSON格式存储
    quoted_tweet = Column(Text)  # JSON格式存储
    has_detailed_content = Column(Boolean, default=False)
    detail_error = Column(Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'content': self.content,
            'likes': self.likes,
            'comments': self.comments,
            'retweets': self.retweets,
            'publish_time': self.publish_time,
            'link': self.link,
            'hashtags': json.loads(self.hashtags or '[]'),
            'content_type': self.content_type,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None,
            'synced_to_feishu': self.synced_to_feishu,
            'full_content': self.full_content,
            'media_content': json.loads(self.media_content) if self.media_content else [],
            'thread_tweets': json.loads(self.thread_tweets) if self.thread_tweets else [],
            'quoted_tweet': json.loads(self.quoted_tweet) if self.quoted_tweet else None,
            'has_detailed_content': self.has_detailed_content,
            'detail_error': self.detail_error
        }

class EnhancedTwitterScraper:
    """增强版Twitter抓取器"""
    
    def __init__(self, db_path: str = "twitter_scraper.db"):
        self.db_path = db_path
        self.engine = None
        self.Session = None
        self.tester = None
        self.sync_manager = CloudSyncManager()
        self.setup_database()
        
    def setup_database(self):
        """设置数据库连接"""
        try:
            self.engine = create_engine(f'sqlite:///{self.db_path}')
            Base.metadata.create_all(self.engine)
            self.Session = sessionmaker(bind=self.engine)
            logger.info(f"数据库连接成功: {self.db_path}")
        except Exception as e:
            logger.error(f"数据库设置失败: {e}")
            raise
    
    def save_tweets_to_database(self, tweets: List[Dict[str, Any]]) -> int:
        """保存推文到数据库"""
        if not tweets:
            logger.warning("没有推文数据需要保存")
            return 0
            
        session = self.Session()
        saved_count = 0
        
        try:
            for tweet_data in tweets:
                # 检查是否已存在（基于链接去重）
                existing = session.query(TweetData).filter_by(
                    link=tweet_data.get('link', '')
                ).first()
                
                if existing:
                    logger.debug(f"推文已存在，跳过: {tweet_data.get('link', '')}")
                    continue
                
                # 创建新的推文记录
                tweet = TweetData(
                    username=tweet_data.get('username', ''),
                    content=tweet_data.get('content', ''),
                    likes=int(tweet_data.get('likes', 0) or 0),
                    comments=int(tweet_data.get('comments', 0) or 0),
                    retweets=int(tweet_data.get('retweets', 0) or 0),
                    publish_time=tweet_data.get('publish_time', tweet_data.get('timestamp', '')),
                    link=tweet_data.get('link', ''),
                    hashtags=json.dumps(tweet_data.get('hashtags', [])),
                    content_type=tweet_data.get('content_type', ''),
                    full_content=tweet_data.get('full_content', ''),
                    media_content=json.dumps(tweet_data.get('media_content', [])),
                    thread_tweets=json.dumps(tweet_data.get('thread_tweets', [])),
                    quoted_tweet=json.dumps(tweet_data.get('quoted_tweet')) if tweet_data.get('quoted_tweet') else None,
                    has_detailed_content=tweet_data.get('has_detailed_content', False),
                    detail_error=tweet_data.get('detail_error', '')
                )
                
                session.add(tweet)
                saved_count += 1
            
            session.commit()
            logger.info(f"成功保存 {saved_count} 条推文到数据库")
            return saved_count
            
        except Exception as e:
            session.rollback()
            logger.error(f"保存推文到数据库失败: {e}")
            return 0
        finally:
            session.close()
    
    def get_unsync_tweets(self) -> List[Dict[str, Any]]:
        """获取未同步到飞书的推文"""
        session = self.Session()
        try:
            tweets = session.query(TweetData).filter_by(synced_to_feishu=False).all()
            logger.info(f"数据库中找到 {len(tweets)} 条未同步推文")
            return [tweet.to_dict() for tweet in tweets]
        except Exception as e:
            logger.error(f"获取未同步推文失败: {e}")
            return []
        finally:
            session.close()
    
    def mark_tweets_synced(self, tweet_ids: List[int]):
        """标记推文为已同步"""
        if not tweet_ids:
            return
            
        session = self.Session()
        try:
            updated_count = session.query(TweetData).filter(TweetData.id.in_(tweet_ids)).update(
                {TweetData.synced_to_feishu: True}, synchronize_session=False
            )
            session.commit()
            logger.info(f"✅ 标记 {updated_count} 条推文为已同步")
        except Exception as e:
            session.rollback()
            logger.error(f"❌ 标记推文同步状态失败: {e}")
            raise
        finally:
            session.close()
    
    def format_tweets_for_feishu(self, tweets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """格式化推文数据用于飞书同步"""
        formatted_tweets = []
        
        for tweet in tweets:
            formatted_tweet = {
                '作者（账号）': tweet.get('username', ''),
                '推文原文内容': tweet.get('content', ''),
                '推文链接': tweet.get('link', ''),
                '话题标签（Hashtag）': ', '.join(tweet.get('hashtags', [])),
                '类型标签': tweet.get('content_type', ''),
                '评论数': tweet.get('comments', 0),
                '转发数': tweet.get('retweets', 0),
                '点赞数': tweet.get('likes', 0),
                '创建时间': tweet.get('scraped_at', '')
            }
            formatted_tweets.append(formatted_tweet)
        
        return formatted_tweets
    
    def sync_to_feishu(self, feishu_config: Dict[str, Any]) -> bool:
        """同步数据到飞书"""
        try:
            logger.info(f"开始飞书同步，配置状态: enabled={feishu_config.get('enabled')}")
            
            # 设置飞书配置
            if not self.sync_manager.setup_feishu(
                feishu_config.get('app_id'),
                feishu_config.get('app_secret')
            ):
                logger.error("飞书配置设置失败")
                return False
            
            # 获取未同步的推文
            unsync_tweets = self.get_unsync_tweets()
            if not unsync_tweets:
                logger.info("没有需要同步的推文")
                return True
            
            logger.info(f"找到 {len(unsync_tweets)} 条未同步推文")
            
            # 格式化数据
            formatted_tweets = self.format_tweets_for_feishu(unsync_tweets)
            
            # 同步到飞书
            logger.info(f"开始同步到飞书表格: {feishu_config.get('spreadsheet_token')[:10]}...")
            success = self.sync_manager.sync_to_feishu(
                formatted_tweets,
                feishu_config.get('spreadsheet_token'),
                feishu_config.get('table_id')
            )
            
            if success:
                # 标记为已同步
                tweet_ids = [tweet['id'] for tweet in unsync_tweets]
                self.mark_tweets_synced(tweet_ids)
                logger.info(f"✅ 成功同步 {len(unsync_tweets)} 条推文到飞书")
            else:
                logger.error("❌ 飞书同步失败")
            
            return success
            
        except Exception as e:
            logger.error(f"飞书同步异常: {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return False
    
    async def scrape_and_save(self, target_count: int = 100, username: str = "elonmusk") -> Dict[str, Any]:
        """抓取推文并保存到数据库"""
        try:
            # 初始化抓取器
            self.tester = Simple100TweetsTester(target_count)
            
            # 执行抓取
            logger.info(f"开始抓取 {username} 的 {target_count} 条推文")
            
            # 执行抓取
            tweets = await self.tester.scrape_100_tweets()
            
            # 构建结果格式
            results = {
                'tweets': tweets,
                'target_count': target_count,
                'actual_count': len(tweets),
                'success': len(tweets) > 0
            }
            
            if not results or not results.get('tweets'):
                logger.warning("没有抓取到推文数据")
                return {'success': False, 'message': '没有抓取到推文数据'}
            
            tweets = results['tweets']
            logger.info(f"成功抓取到 {len(tweets)} 条推文")
            
            # 保存到数据库
            saved_count = self.save_tweets_to_database(tweets)
            
            # 保存到JSON文件（备份）
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            json_file = f"enhanced_tweets_{timestamp}.json"
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'target_count': target_count,
                    'actual_count': len(tweets),
                    'username': username,
                    'scraped_at': timestamp,
                    'tweets': tweets
                }, f, ensure_ascii=False, indent=2)
            
            logger.info(f"推文数据已保存到: {json_file}")
            
            return {
                'success': True,
                'scraped_count': len(tweets),
                'saved_count': saved_count,
                'json_file': json_file,
                'tweets': tweets
            }
            
        except Exception as e:
            logger.error(f"抓取和保存失败: {e}")
            return {'success': False, 'message': str(e)}
        finally:
            if self.tester:
                await self.tester.cleanup()

def load_feishu_config_from_database() -> Dict[str, Any]:
    """从数据库加载飞书配置"""
    try:
        # 导入Flask应用和数据库模型
        from web_app import app, SystemConfig
        
        with app.app_context():
            # 从数据库读取飞书配置
            configs = SystemConfig.query.filter(
                SystemConfig.key.in_([
                    'feishu_app_id', 'feishu_app_secret', 
                    'feishu_spreadsheet_token', 'feishu_table_id', 
                    'feishu_enabled'
                ])
            ).all()
            
            config_dict = {cfg.key: cfg.value for cfg in configs}
            
            feishu_config = {
                'app_id': config_dict.get('feishu_app_id', ''),
                'app_secret': config_dict.get('feishu_app_secret', ''),
                'spreadsheet_token': config_dict.get('feishu_spreadsheet_token', ''),
                'table_id': config_dict.get('feishu_table_id', ''),
                'enabled': config_dict.get('feishu_enabled', 'false').lower() == 'true'
            }
            
            logger.info("已从数据库加载飞书配置")
            return feishu_config
            
    except Exception as e:
        logger.error(f"从数据库加载飞书配置失败: {e}")
        
        # 回退到JSON文件配置
        return load_feishu_config_from_file()

def load_feishu_config_from_file() -> Dict[str, Any]:
    """从JSON文件加载飞书配置（回退方案）"""
    config_file = 'feishu_config.json'
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logger.info("已从JSON文件加载飞书配置")
                return config
        except Exception as e:
            logger.error(f"加载飞书配置文件失败: {e}")
    
    # 默认配置模板
    default_config = {
        'app_id': '',
        'app_secret': '',
        'spreadsheet_token': '',
        'table_id': '',
        'enabled': False
    }
    
    logger.warning("使用默认飞书配置，请在Web管理界面或feishu_config.json中配置")
    return default_config

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='增强版Twitter推文抓取器')
    parser.add_argument('--count', type=int, default=100, help='目标推文数量')
    parser.add_argument('--username', type=str, default='elonmusk', help='Twitter用户名')
    parser.add_argument('--db-path', type=str, default='twitter_scraper.db', help='数据库文件路径')
    parser.add_argument('--sync-feishu', action='store_true', help='同步到飞书文档')
    parser.add_argument('--only-sync', action='store_true', help='仅同步现有数据到飞书')
    
    args = parser.parse_args()
    
    try:
        # 创建增强抓取器
        scraper = EnhancedTwitterScraper(args.db_path)
        
        if not args.only_sync:
            # 抓取并保存推文
            import asyncio
            result = await scraper.scrape_and_save(args.count, args.username)
            
            if not result['success']:
                logger.error(f"抓取失败: {result.get('message', '未知错误')}")
                return
            
            logger.info(f"抓取完成: 抓取 {result['scraped_count']} 条，保存 {result['saved_count']} 条")
        
        # 同步到飞书
        if args.sync_feishu or args.only_sync:
            feishu_config = load_feishu_config_from_database()
            
            # 检查飞书配置是否完整
            if not feishu_config.get('enabled'):
                logger.warning("飞书同步未启用，请在Web管理界面启用")
                return
                
            required_fields = ['app_id', 'app_secret', 'spreadsheet_token', 'table_id']
            missing_fields = [field for field in required_fields if not feishu_config.get(field)]
            
            if missing_fields:
                logger.warning(f"飞书配置不完整，缺少字段: {', '.join(missing_fields)}")
                logger.warning("请在Web管理界面 (http://localhost:8084/config) 完成飞书配置")
                return
            
            logger.info("开始同步到飞书文档...")
            sync_success = scraper.sync_to_feishu(feishu_config)
            
            if sync_success:
                logger.info("飞书同步完成")
            else:
                logger.error("飞书同步失败")
        
        logger.info("任务完成")
        
    except KeyboardInterrupt:
        logger.info("用户中断操作")
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())