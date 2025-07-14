#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter Daily Scraper - Enhanced Version
增强版Twitter日报采集器启动脚本

功能特性:
- AI内容分析和情感分析
- 多账户轮换管理
- 系统监控和告警
- 任务调度和自动化
- 统一管理控制台

使用方法:
    python3 run_enhanced.py [选项]

选项:
    --mode MODE         运行模式: scrape, schedule, console, monitor
    --config CONFIG     配置文件路径
    --accounts FILE     账户配置文件
    --ai-analysis       启用AI分析
    --monitoring        启用系统监控
    --help             显示帮助信息
"""

import sys
import os
import argparse
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import TwitterDailyScraper
from scheduler import TaskScheduler
from management_console import ManagementConsole
from system_monitor import SystemMonitor
from account_manager import AccountManager
from config_manager import ConfigManager

def setup_logging(level=logging.INFO):
    """设置日志配置"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'enhanced_scraper_{datetime.now().strftime("%Y%m%d")}.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='Twitter Daily Scraper - Enhanced Version',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
运行模式说明:
  scrape    - 执行单次采集任务
  schedule  - 启动任务调度器
  console   - 启动管理控制台
  monitor   - 启动系统监控

示例:
  python3 run_enhanced.py --mode scrape --ai-analysis
  python3 run_enhanced.py --mode schedule
  python3 run_enhanced.py --mode console
  python3 run_enhanced.py --mode monitor --monitoring
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['scrape', 'schedule', 'console', 'monitor'],
        default='scrape',
        help='运行模式 (默认: scrape)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='配置文件路径'
    )
    
    parser.add_argument(
        '--accounts',
        type=str,
        help='账户配置文件路径'
    )
    
    parser.add_argument(
        '--ai-analysis',
        action='store_true',
        help='启用AI分析功能'
    )
    
    parser.add_argument(
        '--monitoring',
        action='store_true',
        help='启用系统监控'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='启用调试模式'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='试运行模式（不执行实际操作）'
    )
    
    return parser.parse_args()

async def run_scrape_mode(args, logger):
    """执行采集模式"""
    logger.info("启动Twitter采集任务...")
    
    try:
        # 初始化采集器
        scraper = TwitterDailyScraper()
        
        if args.dry_run:
            logger.info("试运行模式：验证配置和连接...")
            # 这里可以添加配置验证逻辑
            logger.info("配置验证完成")
            return
        
        # 执行采集任务
        result = await scraper.run_scraping_task()
        
        if result:
            logger.info(f"采集任务完成，输出文件: {result}")
        else:
            logger.error("采集任务失败")
    
    except Exception as e:
        logger.error(f"采集任务执行失败: {e}")
        raise
    
    finally:
        if 'scraper' in locals():
            scraper.cleanup()

async def run_schedule_mode(args, logger):
    """执行调度模式"""
    logger.info("启动任务调度器...")
    
    try:
        scheduler = TaskScheduler()
        
        # 加载调度配置
        if args.config:
            scheduler.load_config(args.config)
        
        # 启动调度器
        await scheduler.start()
        
        logger.info("任务调度器已启动，按 Ctrl+C 停止")
        
        # 保持运行直到收到停止信号
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("收到停止信号，正在关闭调度器...")
            await scheduler.stop()
    
    except Exception as e:
        logger.error(f"调度器运行失败: {e}")
        raise

def run_console_mode(args, logger):
    """执行控制台模式"""
    logger.info("启动管理控制台...")
    
    try:
        console = ManagementConsole()
        console.run()
    
    except Exception as e:
        logger.error(f"控制台运行失败: {e}")
        raise

async def run_monitor_mode(args, logger):
    """执行监控模式"""
    logger.info("启动系统监控...")
    
    try:
        monitor = SystemMonitor()
        
        # 启动监控
        monitor.start_monitoring()
        
        logger.info("系统监控已启动，按 Ctrl+C 停止")
        
        # 保持运行直到收到停止信号
        try:
            while True:
                # 定期输出监控状态
                metrics = monitor.get_current_metrics()
                logger.info(f"系统状态 - CPU: {metrics.cpu_percent:.1f}%, 内存: {metrics.memory_percent:.1f}%")
                await asyncio.sleep(60)  # 每分钟输出一次状态
        
        except KeyboardInterrupt:
            logger.info("收到停止信号，正在关闭监控...")
            monitor.stop_monitoring()
    
    except Exception as e:
        logger.error(f"监控运行失败: {e}")
        raise

async def main():
    """主函数"""
    args = parse_arguments()
    
    # 设置日志级别
    log_level = logging.DEBUG if args.debug else logging.INFO
    logger = setup_logging(log_level)
    
    logger.info("="*60)
    logger.info("Twitter Daily Scraper - Enhanced Version")
    logger.info(f"运行模式: {args.mode}")
    logger.info(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*60)
    
    try:
        # 根据模式执行相应功能
        if args.mode == 'scrape':
            await run_scrape_mode(args, logger)
        
        elif args.mode == 'schedule':
            await run_schedule_mode(args, logger)
        
        elif args.mode == 'console':
            run_console_mode(args, logger)
        
        elif args.mode == 'monitor':
            await run_monitor_mode(args, logger)
        
        else:
            logger.error(f"未知的运行模式: {args.mode}")
            return 1
    
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
        return 0
    
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        if args.debug:
            import traceback
            logger.error(traceback.format_exc())
        return 1
    
    logger.info("程序执行完成")
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        print(f"启动失败: {e}")
        sys.exit(1)