#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后台任务运行器
用于在独立进程中执行抓取任务，确保任务不受窗口切换影响
"""

import sys
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# 添加当前目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

# 导入数据库和应用配置
from web_app import app, db, ScrapingTask, TweetData
from ads_browser_launcher import AdsPowerLauncher
from twitter_parser import TwitterParser
from cloud_sync import CloudSyncManager
from excel_writer import ExcelWriter
from exception_handler import ExceptionHandler, resilient_task_execution

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('background_task.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

@resilient_task_execution()
async def execute_scraping_task(task_id: int, user_id: str):
    """执行抓取任务的核心逻辑"""
    logger = logging.getLogger(__name__)
    
    with app.app_context():
        # 获取任务
        task = ScrapingTask.query.get(task_id)
        if not task:
            raise Exception(f"任务 {task_id} 不存在")
        
        logger.info(f"开始执行任务: {task.name}")
        
        # 更新任务状态
        task.status = 'running'
        task.started_at = datetime.utcnow()
        db.session.commit()
        
        try:
            # 解析配置
            target_accounts = json.loads(task.target_accounts or '[]')
            target_keywords = json.loads(task.target_keywords or '[]')
            
            # 启动浏览器
            logger.info(f"开始启动AdsPower浏览器，用户ID: {user_id}")
            
            # 导入配置
            from web_app import ADS_POWER_CONFIG
            browser_manager = AdsPowerLauncher(ADS_POWER_CONFIG)
            
            try:
                # 进行完整的健康检查和浏览器启动
                logger.info("正在进行AdsPower健康检查...")
                browser_info = browser_manager.start_browser(user_id, skip_health_check=False)
                if not browser_info:
                    raise Exception("浏览器启动失败：未返回浏览器信息")
                
                logger.info(f"浏览器启动成功: {browser_info}")
                
            except Exception as e:
                logger.error(f"AdsPower浏览器启动失败: {str(e)}")
                
                # 获取详细的健康报告
                try:
                    health_report = browser_manager.get_health_report()
                    logger.error(f"系统健康报告: {health_report}")
                    
                    # 尝试自动修复
                    logger.info("尝试自动修复系统问题...")
                    if browser_manager.auto_optimize_system():
                        logger.info("系统优化完成，重新尝试启动浏览器...")
                        browser_info = browser_manager.start_browser(user_id, skip_health_check=True)
                        if browser_info:
                            logger.info("浏览器启动成功（修复后）")
                        else:
                            raise Exception("浏览器启动失败（修复后仍然失败）")
                    else:
                        raise Exception(f"AdsPower浏览器启动失败且自动修复失败: {str(e)}")
                        
                except Exception as repair_error:
                    logger.error(f"自动修复过程中发生错误: {str(repair_error)}")
                    raise Exception(f"AdsPower浏览器启动失败: {str(e)}。修复尝试也失败: {str(repair_error)}")
            
            debug_port = browser_info.get('ws', {}).get('puppeteer')
            
            # 连接解析器
            parser = TwitterParser(debug_port)
            await parser.connect_browser()
            
            all_tweets = []
            
            # 抓取推文
            for account in target_accounts:
                try:
                    logger.info(f"抓取博主 @{account} 的推文")
                    await parser.navigate_to_profile(account)
                    tweets = await parser.scrape_tweets(max_tweets=task.max_tweets)
                    
                    # 过滤推文
                    filtered_tweets = []
                    for tweet in tweets:
                        if (tweet.likes >= task.min_likes and 
                            tweet.comments >= task.min_comments and 
                            tweet.retweets >= task.min_retweets):
                            filtered_tweets.append(tweet)
                    
                    all_tweets.extend(filtered_tweets)
                    logger.info(f"博主 @{account} 抓取完成，获得 {len(filtered_tweets)} 条有效推文")
                    
                except Exception as e:
                    logger.error(f"抓取博主 @{account} 失败: {e}")
                    continue
            
            # 抓取关键词推文
            for keyword in target_keywords:
                try:
                    logger.info(f"搜索关键词: {keyword}")
                    await parser.navigate_to_search(keyword)
                    tweets = await parser.scrape_tweets(max_tweets=task.max_tweets)
                    
                    # 过滤推文
                    filtered_tweets = []
                    for tweet in tweets:
                        if (tweet.likes >= task.min_likes and 
                            tweet.comments >= task.min_comments and 
                            tweet.retweets >= task.min_retweets):
                            filtered_tweets.append(tweet)
                    
                    all_tweets.extend(filtered_tweets)
                    logger.info(f"关键词 '{keyword}' 搜索完成，获得 {len(filtered_tweets)} 条有效推文")
                    
                except Exception as e:
                    logger.error(f"搜索关键词 '{keyword}' 失败: {e}")
                    continue
            
            # 保存到数据库
            saved_count = 0
            for tweet in all_tweets:
                try:
                    # 检查是否已存在
                    existing = db.session.query(TweetData).filter_by(
                        username=tweet.username,
                        content=tweet.content[:500]  # 截取前500字符比较
                    ).first()
                    
                    if not existing:
                        tweet_data = TweetData(
                            task_id=task_id,
                            username=tweet.username,
                            content=tweet.content,
                            likes=tweet.likes,
                            comments=tweet.comments,
                            retweets=tweet.retweets,
                            publish_time=tweet.publish_time,
                            link=tweet.link,
                            hashtags=json.dumps(tweet.hashtags) if tweet.hashtags else None
                        )
                        db.session.add(tweet_data)
                        saved_count += 1
                        
                except Exception as e:
                    logger.error(f"保存推文失败: {e}")
                    continue
            
            db.session.commit()
            
            # 更新任务状态
            task.status = 'completed'
            task.completed_at = datetime.utcnow()
            task.result_count = saved_count
            db.session.commit()
            
            # 导出Excel
            excel_writer = ExcelWriter()
            output_file = f"tweets_{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            excel_writer.write_tweets_to_excel(all_tweets, output_file)
            
            # 同步到云端（飞书）
            try:
                cloud_sync = CloudSyncManager()
                await cloud_sync.sync_to_feishu(all_tweets, max_retries=3, continue_on_failure=True)
                logger.info("飞书同步完成")
            except Exception as e:
                logger.warning(f"飞书同步失败，但任务继续执行: {e}")
            
            logger.info(f"任务完成，共保存 {saved_count} 条推文，导出文件: {output_file}")
            return output_file
            
        except Exception as e:
            # 更新任务状态为失败
            task.status = 'failed'
            task.completed_at = datetime.utcnow()
            task.error_message = str(e)
            db.session.commit()
            raise
        
        finally:
            # 关闭浏览器
            try:
                browser_manager.close_browser(user_id)
            except:
                pass

async def run_background_task(config_file: str):
    """运行后台任务"""
    logger = setup_logging()
    
    try:
        # 读取任务配置
        with open(config_file, 'r', encoding='utf-8') as f:
            task_config = json.load(f)
        
        task_id = task_config['task_id']
        user_id = task_config['kwargs']['user_id']
        
        logger.info(f"开始执行后台任务 {task_id}，用户ID: {user_id}")
        
        # 执行任务
        result = await execute_scraping_task(task_id, user_id)
        
        logger.info(f"后台任务 {task_id} 执行完成，结果: {result}")
        
        # 保存结果
        result_file = f"task_result_{task_id}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump({
                'task_id': task_id,
                'success': True,
                'completed_at': datetime.now().isoformat(),
                'result_file': result
            }, f, ensure_ascii=False, indent=2)
        
        return 0
        
    except Exception as e:
        logger.error(f"后台任务执行失败: {e}")
        
        # 保存错误信息
        error_file = f"task_error_{task_config.get('task_id', 'unknown')}.json"
        with open(error_file, 'w', encoding='utf-8') as f:
            json.dump({
                'task_id': task_config.get('task_id'),
                'error': str(e),
                'failed_at': datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
        
        return 1
    
    finally:
        # 清理配置文件
        try:
            if Path(config_file).exists():
                Path(config_file).unlink()
        except:
            pass

def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("用法: python background_task_runner.py <config_file>")
        sys.exit(1)
    
    config_file = sys.argv[1]
    
    if not Path(config_file).exists():
        print(f"配置文件不存在: {config_file}")
        sys.exit(1)
    
    # 运行异步任务
    try:
        exit_code = asyncio.run(run_background_task(config_file))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("任务被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"任务执行异常: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()