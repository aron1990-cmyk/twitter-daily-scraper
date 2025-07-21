#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整数据同步脚本
将JSON文件中的推文数据同步到数据库和飞书
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# 导入应用模块
from web_app import app, db, TweetData, ScrapingTask, FEISHU_CONFIG, load_config_from_database
from cloud_sync import CloudSyncManager

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_tweets_from_json(json_file_path: str) -> List[Dict[str, Any]]:
    """从JSON文件加载推文数据"""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('tweets', [])
    except Exception as e:
        logger.error(f"加载JSON文件失败 {json_file_path}: {e}")
        return []

def sync_tweets_to_database(tweets: List[Dict[str, Any]], source_file: str, task_id: int = 1) -> int:
    """将推文数据同步到数据库"""
    synced_count = 0
    
    for tweet in tweets:
        try:
            # 检查是否已存在（基于链接去重）
            existing_tweet = TweetData.query.filter_by(link=tweet.get('link')).first()
            if existing_tweet:
                logger.debug(f"推文已存在，跳过: {tweet.get('link')}")
                continue
            
            # 创建新的推文记录
            tweet_data = TweetData(
                task_id=task_id,
                username=tweet.get('username', ''),
                content=tweet.get('content', ''),
                publish_time=tweet.get('timestamp', ''),
                likes=int(tweet.get('likes', 0)),
                comments=int(tweet.get('comments', 0)),
                retweets=int(tweet.get('retweets', 0)),
                link=tweet.get('link', ''),
                hashtags=json.dumps(tweet.get('tags', []), ensure_ascii=False),
                content_type='未分类'
            )
            
            db.session.add(tweet_data)
            synced_count += 1
            
        except Exception as e:
            logger.error(f"同步推文到数据库失败: {e}")
            continue
    
    try:
        db.session.commit()
        logger.info(f"成功同步 {synced_count} 条推文到数据库")
    except Exception as e:
        db.session.rollback()
        logger.error(f"数据库提交失败: {e}")
        synced_count = 0
    
    return synced_count

def sync_to_feishu(tweets: List[Dict[str, Any]]) -> bool:
    """同步数据到飞书"""
    try:
        # 检查飞书配置
        if not FEISHU_CONFIG.get('enabled'):
            logger.warning("飞书同步未启用")
            return False
        
        required_fields = ['app_id', 'app_secret', 'spreadsheet_token', 'table_id']
        missing_fields = [field for field in required_fields if not FEISHU_CONFIG.get(field)]
        if missing_fields:
            logger.error(f"飞书配置不完整，缺少字段: {', '.join(missing_fields)}")
            return False
        
        # 创建同步管理器
        sync_manager = CloudSyncManager()
        sync_manager.setup_feishu(
            FEISHU_CONFIG['app_id'], 
            FEISHU_CONFIG['app_secret']
        )
        
        # 获取访问令牌
        access_token = sync_manager.get_feishu_access_token()
        if not access_token:
            logger.error("获取飞书访问令牌失败")
            return False
        
        # 准备数据格式
        feishu_data = []
        for i, tweet in enumerate(tweets, 1):
            feishu_data.append({
                '序号': i,
                '用户名': tweet.get('username', ''),
                '推文内容': tweet.get('content', ''),
                '发布时间': tweet.get('timestamp', ''),
                '点赞数': int(tweet.get('likes', 0)),
                '评论数': int(tweet.get('comments', 0)),
                '转发数': int(tweet.get('retweets', 0)),
                '链接': tweet.get('link', ''),
                '标签': ', '.join(tweet.get('tags', [])),
                '筛选状态': '未筛选'
            })
        
        # 执行飞书同步
        success = sync_manager._execute_feishu_sync(
            feishu_data,
            FEISHU_CONFIG['spreadsheet_token'],
            FEISHU_CONFIG['table_id'],
            access_token
        )
        
        if success:
            logger.info(f"成功同步 {len(tweets)} 条推文到飞书")
        else:
            logger.error("飞书同步失败")
        
        return success
        
    except Exception as e:
        logger.error(f"飞书同步异常: {e}")
        return False

def main():
    """主函数"""
    with app.app_context():
        # 重新加载配置
        load_config_from_database()
        
        logger.info("=== 开始数据同步任务 ===")
        
        # 创建或获取默认任务
        default_task = ScrapingTask.query.filter_by(name='批量数据同步任务').first()
        if not default_task:
            default_task = ScrapingTask(
                name='批量数据同步任务',
                target_accounts=json.dumps(['elonmusk', 'TaoTaoOps', 'Consumentenbond', 'MinPres', 'tesla_semi', 'Rijkswaterstaat', 'neilpatel']),
                target_keywords=json.dumps([]),
                max_tweets=100,
                status='completed'
            )
            db.session.add(default_task)
            db.session.commit()
            logger.info(f"创建默认任务，ID: {default_task.id}")
        
        task_id = default_task.id
        
        # 查找所有JSON文件
        tweets_dir = Path('data/tweets')
        json_files = list(tweets_dir.rglob('*.json'))
        
        if not json_files:
            logger.warning("未找到任何推文JSON文件")
            return
        
        logger.info(f"找到 {len(json_files)} 个JSON文件")
        
        # 收集所有推文数据
        all_tweets = []
        total_synced_to_db = 0
        
        for json_file in json_files:
            logger.info(f"处理文件: {json_file}")
            
            # 加载推文数据
            tweets = load_tweets_from_json(str(json_file))
            if not tweets:
                logger.warning(f"文件 {json_file} 中没有推文数据")
                continue
            
            logger.info(f"文件 {json_file.name} 包含 {len(tweets)} 条推文")
            
            # 同步到数据库
            synced_count = sync_tweets_to_database(tweets, json_file.name, task_id)
            total_synced_to_db += synced_count
            
            # 添加到总列表（用于飞书同步）
            all_tweets.extend(tweets)
        
        logger.info(f"数据库同步完成，总共同步 {total_synced_to_db} 条新推文")
        
        # 同步到飞书
        if all_tweets:
            logger.info(f"开始同步 {len(all_tweets)} 条推文到飞书...")
            feishu_success = sync_to_feishu(all_tweets)
            
            if feishu_success:
                logger.info("✅ 飞书同步成功")
            else:
                logger.error("❌ 飞书同步失败")
        else:
            logger.warning("没有推文数据需要同步到飞书")
        
        # 输出统计信息
        logger.info("=== 同步任务完成 ===")
        logger.info(f"处理文件数: {len(json_files)}")
        logger.info(f"总推文数: {len(all_tweets)}")
        logger.info(f"新增到数据库: {total_synced_to_db}")
        logger.info(f"飞书同步: {'成功' if feishu_success else '失败'}")
        
        # 验证数据库中的数据
        db_tweet_count = TweetData.query.count()
        logger.info(f"数据库中总推文数: {db_tweet_count}")

if __name__ == '__main__':
    main()