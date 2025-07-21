#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整工作流测试脚本
测试100条推文的抓取、数据库保存和飞书同步
"""

import asyncio
import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any, List

from twitter_parser import TwitterParser
from ads_browser_launcher import AdsPowerLauncher
from web_app import app, db, TweetData, ScrapingTask, FEISHU_CONFIG, load_config_from_database
from cloud_sync import CloudSyncManager
from config import ADS_POWER_CONFIG

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CompleteWorkflowTester:
    """完整工作流测试器"""
    
    def __init__(self, target_tweets: int = 100):
        self.target_tweets = target_tweets
        self.launcher = None
        self.parser = None
        self.scraped_tweets = []
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'target_tweets': target_tweets,
            'scraping': {'success': False, 'tweet_count': 0},
            'database_save': {'success': False, 'saved_count': 0},
            'feishu_sync': {'success': False, 'synced_count': 0},
            'overall_success': False
        }
    
    async def test_scraping(self) -> bool:
        """测试推文抓取"""
        logger.info(f"🚀 开始抓取 {self.target_tweets} 条推文...")
        
        try:
            # 启动浏览器
            self.launcher = AdsPowerLauncher(config=ADS_POWER_CONFIG)
            browser_info = self.launcher.start_browser()
            
            if not browser_info:
                logger.error("浏览器启动失败")
                return False
            
            # 创建解析器
            debug_url = browser_info.get('ws', {}).get('puppeteer', '')
            if not debug_url:
                logger.error("无法获取调试端口")
                return False
            
            self.parser = TwitterParser(debug_port=debug_url)
            
            # 初始化解析器
            await self.parser.initialize()
            logger.info("✅ 浏览器连接成功")
            
            # 导航到目标页面
            try:
                await self.parser.navigate_to_profile('elonmusk')
                logger.info("✅ 导航成功")
            except Exception as e:
                logger.error(f"导航失败: {e}")
                return False
            
            # 重新启用优化功能进行调试
            self.parser.optimization_enabled = True
            logger.info(f"优化功能状态: {self.parser.optimization_enabled}")
            
            # 抓取推文
            tweets = await self.parser.scrape_tweets(self.target_tweets)
            
            if tweets:
                self.scraped_tweets = tweets
                self.test_results['scraping'] = {
                    'success': True,
                    'tweet_count': len(tweets)
                }
                logger.info(f"✅ 成功抓取 {len(tweets)} 条推文")
                return True
            else:
                logger.error("抓取推文失败")
                return False
                
        except Exception as e:
            logger.error(f"抓取过程异常: {e}")
            return False
    
    def test_database_save(self) -> bool:
        """测试数据库保存"""
        logger.info("💾 开始保存到数据库...")
        
        if not self.scraped_tweets:
            logger.error("没有推文数据可保存")
            return False
        
        try:
            with app.app_context():
                # 创建或获取测试任务
                test_task = ScrapingTask.query.filter_by(name='完整工作流测试').first()
                if not test_task:
                    test_task = ScrapingTask(
                        name='完整工作流测试',
                        target_accounts=json.dumps(['elonmusk']),
                        target_keywords=json.dumps([]),
                        max_tweets=self.target_tweets,
                        status='completed'
                    )
                    db.session.add(test_task)
                    db.session.commit()
                
                # 保存推文到数据库
                saved_count = 0
                for tweet in self.scraped_tweets:
                    try:
                        # 检查数据格式
                        if isinstance(tweet, str):
                            logger.warning(f"跳过字符串格式的推文数据: {tweet[:50]}...")
                            continue
                        
                        if not isinstance(tweet, dict):
                            logger.warning(f"跳过非字典格式的推文数据: {type(tweet)}")
                            continue
                        
                        # 检查是否已存在
                        link = tweet.get('link') or tweet.get('url', '')
                        if link:
                            existing_tweet = TweetData.query.filter_by(link=link).first()
                            if existing_tweet:
                                continue
                        
                        # 创建新记录
                        tweet_data = TweetData(
                            task_id=test_task.id,
                            username=tweet.get('username', ''),
                            content=tweet.get('content', ''),
                            publish_time=tweet.get('timestamp') or tweet.get('publish_time', ''),
                            likes=int(tweet.get('likes', 0)),
                            comments=int(tweet.get('comments', 0)),
                            retweets=int(tweet.get('retweets', 0)),
                            link=link,
                            hashtags=json.dumps(tweet.get('tags', []), ensure_ascii=False),
                            content_type='测试数据'
                        )
                        
                        db.session.add(tweet_data)
                        saved_count += 1
                        
                    except Exception as e:
                        logger.error(f"保存单条推文失败: {e}")
                        continue
                
                # 提交到数据库
                db.session.commit()
                
                self.test_results['database_save'] = {
                    'success': True,
                    'saved_count': saved_count
                }
                
                logger.info(f"✅ 成功保存 {saved_count} 条推文到数据库")
                return True
                
        except Exception as e:
            logger.error(f"数据库保存失败: {e}")
            if 'db' in locals():
                db.session.rollback()
            return False
    
    def test_feishu_sync(self) -> bool:
        """测试飞书同步"""
        logger.info("📊 开始同步到飞书...")
        
        if not self.scraped_tweets:
            logger.error("没有推文数据可同步")
            return False
        
        try:
            with app.app_context():
                # 重新加载配置
                load_config_from_database()
                
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
                for i, tweet in enumerate(self.scraped_tweets, 1):
                    # 检查数据格式
                    if isinstance(tweet, str):
                        logger.warning(f"跳过字符串格式的推文数据: {tweet[:50]}...")
                        continue
                    
                    if not isinstance(tweet, dict):
                        logger.warning(f"跳过非字典格式的推文数据: {type(tweet)}")
                        continue
                    
                    feishu_data.append({
                        '序号': i,
                        '用户名': tweet.get('username', ''),
                        '推文内容': tweet.get('content', ''),
                        '发布时间': tweet.get('timestamp') or tweet.get('publish_time', ''),
                        '点赞数': int(tweet.get('likes', 0)),
                        '评论数': int(tweet.get('comments', 0)),
                        '转发数': int(tweet.get('retweets', 0)),
                        '链接': tweet.get('link') or tweet.get('url', ''),
                        '标签': ', '.join(tweet.get('tags', [])),
                        '筛选状态': '测试数据'
                    })
                
                # 执行飞书同步
                success = sync_manager._execute_feishu_sync(
                    feishu_data,
                    FEISHU_CONFIG['spreadsheet_token'],
                    FEISHU_CONFIG['table_id'],
                    access_token
                )
                
                if success:
                    self.test_results['feishu_sync'] = {
                        'success': True,
                        'synced_count': len(self.scraped_tweets)
                    }
                    logger.info(f"✅ 成功同步 {len(self.scraped_tweets)} 条推文到飞书")
                    return True
                else:
                    logger.error("飞书同步失败")
                    return False
                    
        except Exception as e:
            logger.error(f"飞书同步异常: {e}")
            return False
    
    async def run_complete_test(self) -> Dict[str, Any]:
        """运行完整测试"""
        logger.info("🎯 开始完整工作流测试")
        
        try:
            # 1. 测试抓取
            scraping_success = await self.test_scraping()
            
            # 2. 测试数据库保存
            database_success = False
            if scraping_success:
                database_success = self.test_database_save()
            
            # 3. 测试飞书同步
            feishu_success = False
            if scraping_success:
                feishu_success = self.test_feishu_sync()
            
            # 更新总体结果
            self.test_results['overall_success'] = scraping_success and database_success and feishu_success
            
            return self.test_results
            
        except Exception as e:
            logger.error(f"完整测试异常: {e}")
            return self.test_results
        
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """清理资源"""
        try:
            if self.parser:
                await self.parser.close()
            if self.launcher:
                self.launcher.stop_browser()
            logger.info("🧹 资源清理完成")
        except Exception as e:
            logger.error(f"清理资源失败: {e}")
    
    def save_results(self):
        """保存测试结果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'complete_workflow_test_{timestamp}.json'
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False)
            logger.info(f"📄 测试结果已保存到: {filename}")
        except Exception as e:
            logger.error(f"保存测试结果失败: {e}")

async def main():
    """主函数"""
    target_tweets = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    
    tester = CompleteWorkflowTester(target_tweets=target_tweets)
    
    # 运行完整测试
    results = await tester.run_complete_test()
    
    # 保存结果
    tester.save_results()
    
    # 打印摘要
    print("\n" + "="*60)
    print("📊 完整工作流测试摘要")
    print("="*60)
    print(f"目标推文数: {target_tweets}")
    print(f"抓取结果: {'✅ 成功' if results['scraping']['success'] else '❌ 失败'} ({results['scraping']['tweet_count']} 条)")
    print(f"数据库保存: {'✅ 成功' if results['database_save']['success'] else '❌ 失败'} ({results['database_save']['saved_count']} 条)")
    print(f"飞书同步: {'✅ 成功' if results['feishu_sync']['success'] else '❌ 失败'} ({results['feishu_sync']['synced_count']} 条)")
    print(f"整体状态: {'✅ 成功' if results['overall_success'] else '❌ 失败'}")
    print("="*60)

if __name__ == '__main__':
    asyncio.run(main())