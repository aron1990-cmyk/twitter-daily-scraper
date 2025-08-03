#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后台任务运行器
用于在独立进程中执行抓取任务，确保任务不受窗口切换影响
"""

import sys
import os
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent))

# 导入数据库和应用配置
from models import app, db, ScrapingTask, TweetData
from utils.ads_browser_launcher import AdsPowerLauncher
from core.twitter_parser import TwitterParser
from utils.cloud_sync import CloudSyncManager
from utils.excel_writer import ExcelWriter
from utils.exception_handler import ExceptionHandler, resilient_task_execution

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

def load_adspower_config_from_db():
    """
    从数据库加载AdsPower配置
    
    Returns:
        AdsPower配置字典
    """
    try:
        import sqlite3
        conn = sqlite3.connect('instance/twitter_scraper.db')
        cursor = conn.cursor()
        
        # 查询AdsPower相关配置
        cursor.execute("SELECT key, value FROM system_config WHERE key LIKE '%adspower%'")
        configs = cursor.fetchall()
        
        # AdsPower 配置现在由配置文件管理
        from config.adspower_config import get_config as get_adspower_config
        adspower_config = get_adspower_config()
        
        config_dict = {
            'local_api_url': adspower_config.local_api_url,
            'api_key': adspower_config.api_key,
            'user_id': adspower_config.user_ids[0] if adspower_config.user_ids else ''
        }
        
        # 处理其他配置项
        for key, value in configs:
            if key == 'adspower_user_id':
                # 兼容性处理，但优先使用配置文件
                if not config_dict['user_id']:
                    config_dict['user_id'] = value
            elif key == 'adspower_group_id':
                config_dict['group_id'] = value
            # api_status 配置现在由配置文件管理，不再从数据库获取
        else:
            config_dict['local_api_url'] = 'http://local.adspower.net:50325'
        
        conn.close()
        
        # 如果没有用户ID，使用默认值
        if 'user_id' not in config_dict or not config_dict['user_id']:
            config_dict['user_id'] = 'k11p9ypc'
        
        print(f"从数据库加载AdsPower配置: {config_dict}")
        return config_dict
        
    except Exception as e:
        print(f"从数据库加载AdsPower配置失败: {e}，使用默认配置")
        return {
            'local_api_url': 'http://local.adspower.net:50325',
            'user_id': 'k11p9ypc',
            'group_id': ''
        }

@resilient_task_execution()
async def execute_scraping_task(task_id: int, user_id: str):
    """执行抓取任务的核心逻辑"""
    logger = logging.getLogger(__name__)
    
    with app.app_context():
        logger.info(f"="*60)
        logger.info(f"🚀 任务启动流程开始 - 任务ID: {task_id}")
        logger.info(f"="*60)
        
        # 获取任务
        logger.info(f"📋 步骤1: 获取任务信息")
        task = ScrapingTask.query.get(task_id)
        if not task:
            logger.error(f"❌ 任务 {task_id} 不存在")
            raise Exception(f"任务 {task_id} 不存在")
        
        logger.info(f"✅ 任务信息获取成功:")
        logger.info(f"   - 任务名称: {task.name}")
        logger.info(f"   - 任务ID: {task.id}")
        logger.info(f"   - 最大推文数: {task.max_tweets}")
        logger.info(f"   - 最小点赞数: {task.min_likes}")
        logger.info(f"   - 最小评论数: {task.min_comments}")
        logger.info(f"   - 最小转发数: {task.min_retweets}")
        logger.info(f"   - 任务状态: {task.status}")
        
        # 更新任务状态
        logger.info(f"📝 步骤2: 更新任务状态为运行中")
        task.status = 'running'
        task.started_at = datetime.utcnow()
        db.session.commit()
        logger.info(f"✅ 任务状态更新成功，开始时间: {task.started_at}")
        
        try:
            # 解析配置
            logger.info(f"🔧 步骤3: 解析任务配置")
            target_accounts = json.loads(task.target_accounts or '[]')
            target_keywords = json.loads(task.target_keywords or '[]')
            logger.info(f"✅ 配置解析完成:")
            logger.info(f"   - 目标账号数量: {len(target_accounts)}")
            logger.info(f"   - 目标账号列表: {target_accounts}")
            logger.info(f"   - 目标关键词数量: {len(target_keywords)}")
            logger.info(f"   - 目标关键词列表: {target_keywords}")
            
            # 启动浏览器
            logger.info(f"🌐 步骤4: 启动AdsPower浏览器")
            logger.info(f"   - 使用用户ID: {user_id}")
            
            # 从数据库加载配置
            adspower_config = load_adspower_config_from_db()
            logger.info(f"   - AdsPower配置加载完成")
            logger.info(f"   - API URL: {adspower_config.get('local_api_url', 'N/A')}")
            logger.info(f"   - 用户ID: {adspower_config.get('user_id', 'N/A')}")
            browser_manager = AdsPowerLauncher(adspower_config)
            
            try:
                # 进行完整的健康检查和浏览器启动
                logger.info(f"🔍 步骤4.1: 进行AdsPower健康检查")
                logger.info(f"   - 检查AdsPower服务状态")
                logger.info(f"   - 检查用户配置文件")
                logger.info(f"   - 验证浏览器环境")
                
                browser_info = browser_manager.start_browser(user_id, skip_health_check=False)
                if not browser_info:
                    logger.error(f"❌ 浏览器启动失败：未返回浏览器信息")
                    raise Exception("浏览器启动失败：未返回浏览器信息")
                
                logger.info(f"✅ 浏览器启动成功:")
                logger.info(f"   - 浏览器信息: {browser_info}")
                logger.info(f"   - WebSocket端口: {browser_info.get('ws', {}).get('puppeteer', 'N/A')}")
                logger.info(f"   - 调试端口: {browser_info.get('debug_port', 'N/A')}")
                logger.info(f"   - 浏览器状态: 已启动并就绪")
                
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
            logger.info(f"🔗 步骤5: 连接Twitter解析器")
            logger.info(f"   - 使用调试端口: {debug_port}")
            parser = TwitterParser(debug_port)
            await parser.connect_browser()
            
            # 确保优化功能已启用
            parser.enable_optimizations()
            logger.info(f"✅ Twitter解析器连接成功，优化功能已启用")
            logger.info(f"   - 优化状态: {parser.optimization_enabled}")
            logger.info(f"   - 已见推文ID集合大小: {len(parser.seen_tweet_ids)}")
            logger.info(f"   - 内容缓存大小: {len(parser.content_cache)}")
            
            all_tweets = []
            content_shortage_details = []  # 记录内容不足的详细信息
            
            # 抓取推文
            logger.info(f"📊 步骤6: 开始数据抓取")
            logger.info(f"   - 总计需要抓取 {len(target_accounts)} 个账号")
            logger.info(f"   - 总计需要搜索 {len(target_keywords)} 个关键词")
            
            for i, account in enumerate(target_accounts, 1):
                try:
                    # 清理用户名，去除@符号
                    clean_username = account.lstrip('@') if account.startswith('@') else account
                    logger.info(f"📱 步骤6.{i}: 抓取博主 @{clean_username} 的推文")
                    logger.info(f"   - 进度: {i}/{len(target_accounts)}")
                    logger.info(f"   - 目标推文数: {task.max_tweets}")
                    logger.info(f"   - 原始输入: {account}")
                    logger.info(f"   - 清理后用户名: {clean_username}")
                    
                    await parser.navigate_to_profile(clean_username)
                    logger.info(f"   - 已导航到用户主页")
                    
                    # 构建筛选条件
                    filter_criteria = {
                        'min_likes': task.min_likes,
                        'min_comments': task.min_comments,
                        'min_retweets': task.min_retweets
                    }
                    logger.info(f"   - 筛选条件: 最小点赞{task.min_likes}, 最小评论{task.min_comments}, 最小转发{task.min_retweets}")
                    
                    # 使用带筛选条件的抓取方法
                    tweets = await parser.scrape_tweets(max_tweets=task.max_tweets, filter_criteria=filter_criteria)
                    logger.info(f"   - 抓取到满足条件的推文数: {len(tweets)}")
                    
                    # 检查是否达到目标数量
                    if len(tweets) < task.max_tweets:
                        shortage_count = task.max_tweets - len(tweets)
                        shortage_info = f"博主 @{clean_username}: 目标{task.max_tweets}条，实际{len(tweets)}条，不足{shortage_count}条"
                        content_shortage_details.append(shortage_info)
                        logger.warning(f"⚠️ 博主 @{clean_username} 满足条件的推文不足：")
                        logger.warning(f"   - 目标数量: {task.max_tweets} 条")
                        logger.warning(f"   - 实际满足条件数量: {len(tweets)} 条")
                        logger.warning(f"   - 不足 {shortage_count} 条")
                        logger.info(f"📊 将使用所有可用的 {len(tweets)} 条满足条件的推文")
                    
                    # 直接添加到结果中（已经过筛选）
                    all_tweets.extend(tweets)
                    logger.info(f"✅ 博主 @{clean_username} 抓取完成:")
                    logger.info(f"   - 满足条件推文数: {len(tweets)}")
                    logger.info(f"   - 累计有效推文数: {len(all_tweets)}")
                    
                    # 如果满足条件的推文不足，记录到任务结果中
                    if len(tweets) < task.max_tweets:
                        logger.info(f"📝 记录满足条件推文不足信息到任务结果")
                    
                except Exception as e:
                    logger.error(f"❌ 抓取博主 @{clean_username} 失败: {e}")
                    continue
            
            # 抓取关键词推文
            if target_keywords:
                logger.info(f"🔍 步骤7: 开始关键词搜索")
                for j, keyword in enumerate(target_keywords, 1):
                    try:
                        logger.info(f"🔎 步骤7.{j}: 搜索关键词 '{keyword}'")
                        logger.info(f"   - 进度: {j}/{len(target_keywords)}")
                        logger.info(f"   - 目标推文数: {task.max_tweets}")
                        
                        await parser.search_tweets(keyword)
                        logger.info(f"   - 已导航到搜索页面")
                        
                        # 构建筛选条件
                        filter_criteria = {
                            'min_likes': task.min_likes,
                            'min_comments': task.min_comments,
                            'min_retweets': task.min_retweets
                        }
                        logger.info(f"   - 筛选条件: 最小点赞{task.min_likes}, 最小评论{task.min_comments}, 最小转发{task.min_retweets}")
                        
                        # 使用带筛选条件的抓取方法
                        tweets = await parser.scrape_tweets(max_tweets=task.max_tweets, filter_criteria=filter_criteria)
                        logger.info(f"   - 抓取到满足条件的推文数: {len(tweets)}")
                        
                        # 检查是否达到目标数量
                        if len(tweets) < task.max_tweets:
                            shortage_count = task.max_tweets - len(tweets)
                            shortage_info = f"关键词 '{keyword}': 目标{task.max_tweets}条，实际{len(tweets)}条，不足{shortage_count}条"
                            content_shortage_details.append(shortage_info)
                            logger.warning(f"⚠️ 关键词 '{keyword}' 满足条件的推文不足：")
                            logger.warning(f"   - 目标数量: {task.max_tweets} 条")
                            logger.warning(f"   - 实际满足条件数量: {len(tweets)} 条")
                            logger.warning(f"   - 不足 {shortage_count} 条")
                            logger.info(f"📊 将使用所有可用的 {len(tweets)} 条满足条件的推文")
                        
                        # 直接添加到结果中（已经过筛选）
                        all_tweets.extend(tweets)
                        logger.info(f"✅ 关键词 '{keyword}' 搜索完成:")
                        logger.info(f"   - 满足条件推文数: {len(tweets)}")
                        logger.info(f"   - 累计有效推文数: {len(all_tweets)}")
                        
                    except Exception as e:
                        logger.error(f"❌ 搜索关键词 '{keyword}' 失败: {e}")
                        continue
            else:
                logger.info(f"ℹ️ 跳过关键词搜索：未配置关键词")
            
            # 保存到数据库
            logger.info(f"💾 步骤8: 保存数据到数据库")
            logger.info(f"   - 总计抓取推文数: {len(all_tweets)}")
            logger.info(f"   - 开始去重和保存")
            
            saved_count = 0
            duplicate_count = 0
            error_count = 0
            
            for i, tweet in enumerate(all_tweets, 1):
                try:
                    # 检查是否已存在
                    existing = db.session.query(TweetData).filter_by(
                        username=tweet.get('username', ''),
                        content=tweet.get('content', '')[:500]  # 截取前500字符比较
                    ).first()
                    
                    if not existing:
                        tweet_data = TweetData(
                            task_id=task_id,
                            username=tweet.get('username', ''),
                            content=tweet.get('content', ''),
                            likes=tweet.get('likes', 0),
                            comments=tweet.get('comments', 0),
                            retweets=tweet.get('retweets', 0),
                            publish_time=tweet.get('publish_time', ''),
                            link=tweet.get('link', ''),
                            hashtags=json.dumps(tweet.get('hashtags', [])) if tweet.get('hashtags') else None
                        )
                        db.session.add(tweet_data)
                        saved_count += 1
                        if i % 10 == 0 or i == len(all_tweets):
                            logger.info(f"   - 处理进度: {i}/{len(all_tweets)}, 已保存: {saved_count}, 重复: {duplicate_count}")
                    else:
                        duplicate_count += 1
                        
                except Exception as e:
                    error_count += 1
                    logger.error(f"❌ 保存推文失败 (第{i}条): {e}")
                    continue
            
            db.session.commit()
            logger.info(f"✅ 数据库保存完成:")
            logger.info(f"   - 总处理推文数: {len(all_tweets)}")
            logger.info(f"   - 成功保存数: {saved_count}")
            logger.info(f"   - 重复跳过数: {duplicate_count}")
            logger.info(f"   - 保存失败数: {error_count}")
            
            # 更新任务状态
            logger.info(f"📝 步骤9: 更新任务状态")
            task.status = 'completed'
            task.completed_at = datetime.utcnow()
            task.result_count = saved_count
            
            # 检查是否有内容不足的情况，并添加到任务备注中
            if content_shortage_details:
                # 将详细的内容不足信息添加到任务备注
                if hasattr(task, 'notes'):
                    existing_notes = task.notes or ''
                    shortage_note = f"[内容不足提醒] {'; '.join(content_shortage_details)}"
                    task.notes = f"{existing_notes}\n{shortage_note}" if existing_notes else shortage_note
                
                logger.warning(f"⚠️ 任务完成但部分内容不足：")
                for detail in content_shortage_details:
                    logger.warning(f"   - {detail}")
            else:
                logger.info(f"✅ 所有内容抓取充足，无内容不足情况")
            
            db.session.commit()
            logger.info(f"✅ 任务状态更新完成:")
            logger.info(f"   - 状态: {task.status}")
            logger.info(f"   - 完成时间: {task.completed_at}")
            logger.info(f"   - 结果数量: {task.result_count}")
            if content_shortage_details:
                logger.info(f"   - 内容不足详情: {len(content_shortage_details)} 项")
                for detail in content_shortage_details:
                    logger.info(f"     * {detail}")
            else:
                logger.info(f"   - 内容抓取状态: 充足")
            
            # 导出Excel
            logger.info(f"📊 步骤10: 导出Excel文件")
            excel_writer = ExcelWriter()
            output_file = os.path.join("data", f"tweets_{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
            logger.info(f"   - 导出文件路径: {output_file}")
            logger.info(f"   - 导出推文数量: {len(all_tweets)}")
            
            excel_writer.write_tweets_to_excel(all_tweets, output_file)
            logger.info(f"✅ Excel文件导出完成: {output_file}")
            
            # 同步到云端（飞书）
            logger.info(f"☁️ 步骤11: 同步数据到飞书")
            try:
                # 检查飞书配置
                from config.feishu_config import get_config as get_feishu_config
                feishu_config = get_feishu_config()
                logger.info(f"   - 检查飞书配置状态")
                logger.info(f"   - 飞书同步启用: {feishu_config.get('enabled', False)}")
                
                if not feishu_config.get('enabled'):
                    logger.info(f"ℹ️ 飞书同步未启用，跳过同步")
                else:
                    # 检查必要的飞书配置参数
                    spreadsheet_token = feishu_config.get('spreadsheet_token')
                    table_id = feishu_config.get('table_id')
                    
                    if not spreadsheet_token:
                        logger.warning(f"⚠️ 飞书表格Token未配置，跳过同步")
                    elif not table_id:
                        logger.warning(f"⚠️ 飞书表格ID未配置，跳过同步")
                    else:
                        logger.info(f"   - 开始飞书同步，推文数量: {len(all_tweets)}")
                        logger.info(f"   - 表格Token: {spreadsheet_token[:10]}...")
                        logger.info(f"   - 表格ID: {table_id}")
                        logger.info(f"   - 最大重试次数: 3")
                        logger.info(f"   - 失败时继续执行: True")
                        
                        # 构建飞书配置
                        feishu_sync_config = {
                            'feishu': {
                                'app_id': feishu_config.get('app_id'),
                                'app_secret': feishu_config.get('app_secret'),
                                'base_url': 'https://open.feishu.cn/open-apis'
                            }
                        }
                        
                        cloud_sync = CloudSyncManager(feishu_sync_config)
                        sync_result = cloud_sync.sync_to_feishu(
                            all_tweets, 
                            spreadsheet_token=spreadsheet_token,
                            table_id=table_id,
                            max_retries=3, 
                            continue_on_failure=True
                        )
                        
                        if sync_result:
                            logger.info(f"✅ 飞书同步完成")
                            logger.info(f"   - 同步状态: 成功")
                            logger.info(f"   - 同步推文数: {len(all_tweets)}")
                            
                            # 更新数据库中的同步状态
                            try:
                                synced_tweets = db.session.query(TweetData).filter_by(task_id=task_id).all()
                                for tweet_data in synced_tweets:
                                    tweet_data.synced_to_feishu = True
                                db.session.commit()
                                logger.info(f"✅ 数据库同步状态更新完成，共更新 {len(synced_tweets)} 条记录")
                            except Exception as update_e:
                                logger.warning(f"⚠️ 更新数据库同步状态失败: {update_e}")
                        else:
                            logger.warning(f"⚠️ 飞书同步失败，但任务继续执行")
                        
            except Exception as e:
                logger.warning(f"⚠️ 飞书同步异常，但任务继续执行: {e}")
                logger.warning(f"   - 异常类型: {type(e).__name__}")
                logger.warning(f"   - 异常详情: {str(e)}")
                import traceback
                logger.warning(f"   - 异常堆栈: {traceback.format_exc()}")
            
            logger.info(f"🎉 步骤12: 任务执行完成")
            logger.info(f"✅ 任务执行总结:")
            logger.info(f"   - 任务ID: {task_id}")
            logger.info(f"   - 任务名称: {task.name}")
            logger.info(f"   - 抓取推文总数: {len(all_tweets)}")
            logger.info(f"   - 保存推文数: {saved_count}")
            logger.info(f"   - 导出文件: {output_file}")
            logger.info(f"   - 执行时长: {datetime.utcnow() - task.started_at}")
            logger.info(f"="*60)
            
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
                browser_manager.stop_browser(user_id)
            except:
                pass

async def run_background_task(config_file: str):
    """运行后台任务"""
    logger = setup_logging()
    task_config = None
    
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
        task_id = task_config.get('task_id', 'unknown') if task_config else 'unknown'
        error_file = f"task_error_{task_id}.json"
        with open(error_file, 'w', encoding='utf-8') as f:
            json.dump({
                'task_id': task_id,
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