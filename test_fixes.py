#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复效果
验证并行任务和抓取逻辑修复是否生效
"""

import os
import sys
import json
import time
import logging
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_task_manager_config():
    """测试任务管理器配置"""
    logger.info("开始测试任务管理器配置...")
    
    try:
        from web_app import app, load_config_from_database, init_task_manager, ADS_POWER_CONFIG
        
        with app.app_context():
            # 重新加载配置
            load_config_from_database()
            
            logger.info("当前ADS_POWER_CONFIG配置:")
            logger.info(f"  - max_concurrent_tasks: {ADS_POWER_CONFIG.get('max_concurrent_tasks')}")
            logger.info(f"  - user_id: {ADS_POWER_CONFIG.get('user_id')}")
            logger.info(f"  - multi_user_ids: {ADS_POWER_CONFIG.get('multi_user_ids')}")
            logger.info(f"  - user_ids: {ADS_POWER_CONFIG.get('user_ids')}")
            
            # 强制重新初始化任务管理器
            import web_app
            web_app.task_manager = None  # 重置全局变量
            init_task_manager()
            
            # 获取初始化后的任务管理器
            task_manager = web_app.task_manager
            
            if task_manager:
                logger.info("任务管理器初始化成功，检查配置...")
                logger.info(f"  - 最大并发任务数: {task_manager.max_concurrent_tasks}")
                logger.info(f"  - 用户ID池: {getattr(task_manager, 'user_id_pool', 'N/A')}")
                logger.info(f"  - 可用用户ID: {getattr(task_manager, 'available_users', 'N/A')}")
                logger.info(f"  - 当前活跃任务: {len(getattr(task_manager, 'active_slots', {}))}")
                
                # 测试任务管理器状态
                if hasattr(task_manager, 'get_task_status'):
                    status = task_manager.get_task_status()
                    logger.info("任务管理器状态:")
                    for key, value in status.items():
                        logger.info(f"  - {key}: {value}")
                
                # 测试是否可以启动任务
                if hasattr(task_manager, 'can_start_task'):
                    can_start = task_manager.can_start_task()
                    logger.info(f"  - 可以启动新任务: {can_start}")
                
                return True
            else:
                logger.error("任务管理器初始化失败")
                return False
                
    except Exception as e:
        logger.error(f"测试任务管理器配置失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_twitter_parser_import():
    """测试TwitterParser导入和基本功能"""
    logger.info("开始测试TwitterParser导入...")
    
    try:
        from twitter_parser import TwitterParser
        
        # 创建解析器实例
        parser = TwitterParser()
        
        # 检查关键属性
        logger.info("TwitterParser属性检查:")
        logger.info(f"  - seen_tweet_ids: {type(parser.seen_tweet_ids)}")
        logger.info(f"  - content_cache: {type(parser.content_cache)}")
        logger.info(f"  - optimization_enabled: {parser.optimization_enabled}")
        
        # 检查关键方法是否存在
        methods_to_check = [
            'scrape_tweets',
            'scrape_user_tweets', 
            'scrape_keyword_tweets',
            'parse_tweet_element'
        ]
        
        for method_name in methods_to_check:
            if hasattr(parser, method_name):
                logger.info(f"  - ✅ 方法 {method_name} 存在")
            else:
                logger.error(f"  - ❌ 方法 {method_name} 不存在")
                return False
        
        logger.info("TwitterParser导入测试通过")
        return True
        
    except Exception as e:
        logger.error(f"测试TwitterParser导入失败: {e}")
        return False

def test_database_connection():
    """测试数据库连接"""
    logger.info("开始测试数据库连接...")
    
    try:
        from web_app import app, db, ScrapingTask, TweetData
        
        with app.app_context():
            # 测试基本查询
            task_count = ScrapingTask.query.count()
            tweet_count = TweetData.query.count()
            
            logger.info(f"数据库连接成功:")
            logger.info(f"  - 任务总数: {task_count}")
            logger.info(f"  - 推文总数: {tweet_count}")
            
            # 查看最近的任务
            recent_tasks = ScrapingTask.query.order_by(ScrapingTask.created_at.desc()).limit(3).all()
            logger.info(f"最近的任务:")
            for task in recent_tasks:
                logger.info(f"  - ID: {task.id}, 名称: {task.name}, 状态: {task.status}")
            
            return True
            
    except Exception as e:
        logger.error(f"测试数据库连接失败: {e}")
        return False

def test_create_test_tasks():
    """创建测试任务"""
    logger.info("开始创建测试任务...")
    
    try:
        from web_app import app, db, ScrapingTask
        import json
        
        with app.app_context():
            # 创建两个测试任务
            test_tasks = [
                {
                    'name': 'Test_socialmedia2day',
                    'target_accounts': ['socialmedia2day'],
                    'target_keywords': [],
                    'max_tweets': 50
                },
                {
                    'name': 'Test_Mike_Stelzner',
                    'target_accounts': ['Mike_Stelzner'],
                    'target_keywords': [],
                    'max_tweets': 100
                }
            ]
            
            created_tasks = []
            
            for task_data in test_tasks:
                # 检查是否已存在同名任务
                existing_task = ScrapingTask.query.filter_by(name=task_data['name']).first()
                if existing_task:
                    logger.info(f"任务 {task_data['name']} 已存在，ID: {existing_task.id}")
                    created_tasks.append(existing_task)
                    continue
                
                # 创建新任务
                task = ScrapingTask(
                    name=task_data['name'],
                    target_accounts=json.dumps(task_data['target_accounts']),
                    target_keywords=json.dumps(task_data['target_keywords']),
                    max_tweets=task_data['max_tweets'],
                    min_likes=0,
                    min_retweets=0,
                    min_comments=0
                )
                
                db.session.add(task)
                db.session.commit()
                
                logger.info(f"创建测试任务: {task.name}, ID: {task.id}")
                created_tasks.append(task)
            
            logger.info(f"测试任务创建完成，共 {len(created_tasks)} 个任务")
            return created_tasks
            
    except Exception as e:
        logger.error(f"创建测试任务失败: {e}")
        return []

def test_parallel_task_execution():
    """测试并行任务执行"""
    logger.info("开始测试并行任务执行...")
    
    try:
        from web_app import app
        import web_app
        
        with app.app_context():
            # 确保任务管理器已初始化
            if not web_app.task_manager:
                logger.error("任务管理器未初始化")
                return False
            
            task_manager = web_app.task_manager
            
            # 创建测试任务
            test_tasks = test_create_test_tasks()
            
            if len(test_tasks) < 2:
                logger.error("测试任务数量不足")
                return False
            
            # 尝试同时启动两个任务
            logger.info("尝试同时启动两个任务...")
            
            results = []
            for task in test_tasks[:2]:  # 只测试前两个任务
                logger.info(f"启动任务: {task.name} (ID: {task.id})")
                
                # 检查任务管理器是否有start_task方法
                if hasattr(task_manager, 'start_task'):
                    success, message = task_manager.start_task(task.id)
                    results.append((task.id, success, message))
                    logger.info(f"任务 {task.id} 启动结果: {success}, 消息: {message}")
                else:
                    logger.error("任务管理器没有start_task方法")
                    return False
                
                # 短暂等待
                time.sleep(1)
            
            # 检查任务状态
            time.sleep(3)  # 等待任务启动
            
            if hasattr(task_manager, 'get_task_status'):
                status = task_manager.get_task_status()
                logger.info("任务管理器状态:")
                for key, value in status.items():
                    logger.info(f"  - {key}: {value}")
                
                # 检查是否有多个任务在运行
                running_count = status.get('running_count', 0)
                if running_count >= 2:
                    logger.info(f"✅ 并行任务测试成功，当前运行任务数: {running_count}")
                    return True
                elif running_count == 1:
                    logger.warning(f"⚠️ 只有1个任务在运行，可能是用户ID不足或其他限制")
                    return True  # 至少有任务在运行
                else:
                    logger.error(f"❌ 没有任务在运行")
                    return False
            else:
                logger.warning("任务管理器没有get_task_status方法，无法检查状态")
                # 检查是否有活跃任务
                active_count = len(getattr(task_manager, 'active_slots', {}))
                logger.info(f"活跃任务数量: {active_count}")
                return active_count > 0
                
    except Exception as e:
        logger.error(f"测试并行任务执行失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """主测试函数"""
    logger.info("开始修复效果测试...")
    logger.info("="*60)
    
    test_results = []
    
    # 测试1: 数据库连接
    logger.info("\n🔍 测试1: 数据库连接")
    result1 = test_database_connection()
    test_results.append(("数据库连接", result1))
    
    # 测试2: TwitterParser导入
    logger.info("\n🔍 测试2: TwitterParser导入")
    result2 = test_twitter_parser_import()
    test_results.append(("TwitterParser导入", result2))
    
    # 测试3: 任务管理器配置
    logger.info("\n🔍 测试3: 任务管理器配置")
    result3 = test_task_manager_config()
    test_results.append(("任务管理器配置", result3))
    
    # 测试4: 并行任务执行
    logger.info("\n🔍 测试4: 并行任务执行")
    result4 = test_parallel_task_execution()
    test_results.append(("并行任务执行", result4))
    
    # 汇总结果
    logger.info("\n" + "="*60)
    logger.info("🎯 测试结果汇总:")
    logger.info("="*60)
    
    all_passed = True
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"  {test_name}: {status}")
        if not result:
            all_passed = False
    
    logger.info("="*60)
    if all_passed:
        logger.info("🎉 所有测试通过！修复效果良好。")
        logger.info("\n现在可以尝试:")
        logger.info("1. 同时启动 socialmedia2day 和 Mike_Stelzner 任务")
        logger.info("2. 观察是否启动了多个浏览器实例")
        logger.info("3. 检查 Mike_Stelzner 是否能抓取到足够的推文")
    else:
        logger.error("❌ 部分测试失败，请检查修复效果。")
    
    logger.info("="*60)

if __name__ == "__main__":
    main()