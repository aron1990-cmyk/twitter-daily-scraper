#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
推特博主推文批量抓取系统 - 主程序入口
提供命令行接口和Web API接口，支持配置管理、任务调度和监控
"""

import asyncio
import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml

from batch_scraper import BatchScraper, BatchConfig, BatchProgress, BatchStatus
from twitter_scraping_engine import TwitterScrapingEngine
from storage_manager import StorageManager
from account_state_tracker import AccountStateTracker
from exception_handler import ExceptionHandler


class BatchScrapingSystem:
    """批量抓取系统主类"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "config/batch_config.yaml"
        self.logger = self._setup_logging()
        
        # 加载配置
        self.config = self._load_config()
        
        # 初始化组件
        self.storage_manager = StorageManager()
        self.state_tracker = AccountStateTracker()
        self.exception_handler = ExceptionHandler()
        
        # 当前批次
        self.current_scraper: Optional[BatchScraper] = None
        self.current_batch_id: Optional[str] = None
        
        # 历史记录
        self.batch_history: List[Dict[str, Any]] = []
    
    def _setup_logging(self) -> logging.Logger:
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/batch_scraper.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # 创建日志目录
        Path('logs').mkdir(exist_ok=True)
        
        return logging.getLogger(__name__)
    
    def _load_config(self) -> BatchConfig:
        """加载配置文件"""
        try:
            config_path = Path(self.config_file)
            
            if not config_path.exists():
                # 创建默认配置
                self._create_default_config(config_path)
            
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix.lower() == '.yaml' or config_path.suffix.lower() == '.yml':
                    config_data = yaml.safe_load(f)
                else:
                    config_data = json.load(f)
            
            # 转换为BatchConfig对象
            return BatchConfig(**config_data)
            
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
            # 返回默认配置
            return self._get_default_config()
    
    def _create_default_config(self, config_path: Path):
        """创建默认配置文件"""
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            default_config = {
                "target_accounts": [
                    "elonmusk",
                    "openai",
                    "github",
                    "vercel",
                    "reactjs"
                ],
                "max_tweets_per_account": 50,
                "max_concurrent_accounts": 3,
                "delay_between_accounts": 5.0,
                "filters": {
                    "min_likes": 10,
                    "min_retweets": 5,
                    "exclude_retweets": True,
                    "exclude_replies": True,
                    "max_age_days": 7,
                    "keywords": ["AI", "技术", "开发", "编程"]
                },
                "output_formats": ["json", "csv", "excel"],
                "output_directory": "./data/batch_results",
                "headless": True,
                "max_browser_instances": 3,
                "max_retries_per_account": 3,
                "retry_delay_minutes": 30,
                "enable_progress_callback": True,
                "save_intermediate_results": True
            }
            
            if config_path.suffix.lower() in ['.yaml', '.yml']:
                with open(config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
            else:
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"已创建默认配置文件: {config_path}")
            
        except Exception as e:
            self.logger.error(f"创建默认配置文件失败: {e}")
    
    def _get_default_config(self) -> BatchConfig:
        """获取默认配置"""
        return BatchConfig(
            target_accounts=["elonmusk", "openai", "github"],
            max_tweets_per_account=20,
            max_concurrent_accounts=2,
            output_formats=["json", "csv"]
        )
    
    async def start_batch_scraping(self, custom_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """开始批量抓取"""
        try:
            # 使用自定义配置或默认配置
            if custom_config:
                config = BatchConfig(**custom_config)
            else:
                config = self.config
            
            # 验证配置
            if not config.validate():
                raise ValueError("配置验证失败")
            
            # 创建批量抓取器
            self.current_scraper = BatchScraper(config)
            self.current_batch_id = self.current_scraper.batch_id
            
            # 设置回调函数
            self.current_scraper.set_progress_callback(self._on_progress_update)
            self.current_scraper.set_completion_callback(self._on_batch_completion)
            self.current_scraper.set_error_callback(self._on_error)
            
            self.logger.info(f"开始批量抓取，批次ID: {self.current_batch_id}")
            
            # 执行抓取
            summary = await self.current_scraper.start_batch_scraping()
            
            # 记录到历史
            self.batch_history.append({
                "batch_id": self.current_batch_id,
                "summary": summary,
                "completed_at": datetime.now().isoformat()
            })
            
            return summary
            
        except Exception as e:
            self.logger.error(f"批量抓取失败: {e}")
            raise e
        
        finally:
            self.current_scraper = None
            self.current_batch_id = None
    
    def _on_progress_update(self, progress: BatchProgress):
        """进度更新回调"""
        self.logger.info(
            f"进度更新 [{progress.batch_id}]: "
            f"{progress.overall_progress:.1f}% - "
            f"完成: {progress.completed_accounts}/{progress.total_accounts} - "
            f"当前: @{progress.current_account}"
        )
    
    def _on_batch_completion(self, summary: Dict[str, Any]):
        """批次完成回调"""
        batch_id = summary.get("batch_info", {}).get("batch_id", "unknown")
        total_tweets = summary.get("results", {}).get("total_tweets", 0)
        success_rate = summary.get("results", {}).get("success_rate", 0)
        
        self.logger.info(
            f"批次完成 [{batch_id}]: "
            f"获得 {total_tweets} 条推文，"
            f"成功率 {success_rate:.1f}%"
        )
    
    def _on_error(self, error: Exception, context: str):
        """错误回调"""
        self.logger.error(f"抓取错误 [{context}]: {error}")
    
    def pause_current_batch(self):
        """暂停当前批次"""
        if self.current_scraper:
            self.current_scraper.pause()
            self.logger.info(f"已暂停批次: {self.current_batch_id}")
        else:
            self.logger.warning("没有正在运行的批次")
    
    def resume_current_batch(self):
        """恢复当前批次"""
        if self.current_scraper:
            self.current_scraper.resume()
            self.logger.info(f"已恢复批次: {self.current_batch_id}")
        else:
            self.logger.warning("没有暂停的批次")
    
    def cancel_current_batch(self):
        """取消当前批次"""
        if self.current_scraper:
            self.current_scraper.cancel()
            self.logger.info(f"已取消批次: {self.current_batch_id}")
        else:
            self.logger.warning("没有正在运行的批次")
    
    def get_current_progress(self) -> Optional[BatchProgress]:
        """获取当前进度"""
        if self.current_scraper:
            return self.current_scraper.get_progress()
        return None
    
    def get_batch_history(self) -> List[Dict[str, Any]]:
        """获取批次历史"""
        return self.batch_history.copy()
    
    def get_account_states(self) -> Dict[str, Any]:
        """获取账号状态"""
        return self.state_tracker.get_statistics()
    
    def reset_account_state(self, username: str):
        """重置账号状态"""
        self.state_tracker.reset_account_state(username)
        self.logger.info(f"已重置账号状态: @{username}")
    
    def export_results(self, batch_id: str, format_type: str = "json") -> str:
        """导出结果"""
        try:
            # 查找批次结果
            batch_data = None
            for batch in self.batch_history:
                if batch["batch_id"] == batch_id:
                    batch_data = batch
                    break
            
            if not batch_data:
                raise ValueError(f"未找到批次: {batch_id}")
            
            # 导出文件
            output_file = f"exports/{batch_id}_export.{format_type}"
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format_type == "json":
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(batch_data, f, ensure_ascii=False, indent=2)
            elif format_type == "yaml":
                with open(output_path, 'w', encoding='utf-8') as f:
                    yaml.dump(batch_data, f, default_flow_style=False, allow_unicode=True)
            else:
                raise ValueError(f"不支持的导出格式: {format_type}")
            
            self.logger.info(f"结果已导出: {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"导出结果失败: {e}")
            raise e


def create_cli_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="推特博主推文批量抓取系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python3 main_batch_scraper.py start --config config/my_config.yaml
python3 main_batch_scraper.py start --accounts elonmusk openai --max-tweets 30
python3 main_batch_scraper.py status
python3 main_batch_scraper.py export batch_123456 --format json
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # start 命令
    start_parser = subparsers.add_parser('start', help='开始批量抓取')
    start_parser.add_argument('--config', '-c', help='配置文件路径')
    start_parser.add_argument('--accounts', '-a', nargs='+', help='目标账号列表')
    start_parser.add_argument('--max-tweets', '-m', type=int, help='每个账号最大推文数')
    start_parser.add_argument('--concurrent', type=int, help='并发账号数')
    start_parser.add_argument('--output-dir', '-o', help='输出目录')
    start_parser.add_argument('--formats', nargs='+', choices=['json', 'csv', 'excel'], help='输出格式')
    start_parser.add_argument('--headless', action='store_true', help='无头模式')
    start_parser.add_argument('--no-headless', action='store_true', help='非无头模式')
    
    # status 命令
    status_parser = subparsers.add_parser('status', help='查看状态')
    status_parser.add_argument('--batch-id', help='特定批次ID')
    
    # control 命令
    control_parser = subparsers.add_parser('control', help='控制当前批次')
    control_parser.add_argument('action', choices=['pause', 'resume', 'cancel'], help='控制动作')
    
    # export 命令
    export_parser = subparsers.add_parser('export', help='导出结果')
    export_parser.add_argument('batch_id', help='批次ID')
    export_parser.add_argument('--format', '-f', choices=['json', 'yaml'], default='json', help='导出格式')
    
    # accounts 命令
    accounts_parser = subparsers.add_parser('accounts', help='账号管理')
    accounts_parser.add_argument('action', choices=['list', 'reset'], help='账号操作')
    accounts_parser.add_argument('--username', help='用户名（用于reset操作）')
    
    # history 命令
    history_parser = subparsers.add_parser('history', help='查看历史记录')
    history_parser.add_argument('--limit', '-l', type=int, default=10, help='显示数量限制')
    
    return parser


async def main():
    """主函数"""
    parser = create_cli_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 创建系统实例
    system = BatchScrapingSystem(args.config if hasattr(args, 'config') else None)
    
    try:
        if args.command == 'start':
            # 构建自定义配置
            custom_config = {}
            
            if args.accounts:
                custom_config['target_accounts'] = args.accounts
            if args.max_tweets:
                custom_config['max_tweets_per_account'] = args.max_tweets
            if args.concurrent:
                custom_config['max_concurrent_accounts'] = args.concurrent
            if args.output_dir:
                custom_config['output_directory'] = args.output_dir
            if args.formats:
                custom_config['output_formats'] = args.formats
            if args.headless:
                custom_config['headless'] = True
            elif args.no_headless:
                custom_config['headless'] = False
            
            # 开始抓取
            print("开始批量抓取...")
            summary = await system.start_batch_scraping(custom_config if custom_config else None)
            
            print("\n=== 抓取完成 ===")
            print(f"批次ID: {summary['batch_info']['batch_id']}")
            print(f"总推文数: {summary['results']['total_tweets']}")
            print(f"成功率: {summary['results']['success_rate']:.1f}%")
            print(f"用时: {summary['batch_info']['duration']}")
        
        elif args.command == 'status':
            if args.batch_id:
                # 显示特定批次状态
                history = system.get_batch_history()
                batch_data = next((b for b in history if b['batch_id'] == args.batch_id), None)
                
                if batch_data:
                    print(f"批次 {args.batch_id} 状态:")
                    print(json.dumps(batch_data['summary'], ensure_ascii=False, indent=2))
                else:
                    print(f"未找到批次: {args.batch_id}")
            else:
                # 显示当前状态
                progress = system.get_current_progress()
                if progress:
                    print(f"当前批次: {progress.batch_id}")
                    print(f"状态: {progress.status.value}")
                    print(f"进度: {progress.overall_progress:.1f}%")
                    print(f"完成账号: {progress.completed_accounts}/{progress.total_accounts}")
                    print(f"总推文数: {progress.total_tweets}")
                    if progress.current_account:
                        print(f"当前账号: @{progress.current_account}")
                else:
                    print("没有正在运行的批次")
        
        elif args.command == 'control':
            if args.action == 'pause':
                system.pause_current_batch()
                print("已暂停当前批次")
            elif args.action == 'resume':
                system.resume_current_batch()
                print("已恢复当前批次")
            elif args.action == 'cancel':
                system.cancel_current_batch()
                print("已取消当前批次")
        
        elif args.command == 'export':
            output_file = system.export_results(args.batch_id, args.format)
            print(f"结果已导出到: {output_file}")
        
        elif args.command == 'accounts':
            if args.action == 'list':
                states = system.get_account_states()
                print("账号状态统计:")
                print(json.dumps(states, ensure_ascii=False, indent=2))
            elif args.action == 'reset':
                if not args.username:
                    print("请指定用户名: --username <username>")
                    return
                system.reset_account_state(args.username)
                print(f"已重置账号状态: @{args.username}")
        
        elif args.command == 'history':
            history = system.get_batch_history()
            if not history:
                print("没有历史记录")
                return
            
            print(f"最近 {min(args.limit, len(history))} 次批量抓取:")
            for batch in history[-args.limit:]:
                batch_info = batch['summary']['batch_info']
                results = batch['summary']['results']
                print(f"\n批次: {batch_info['batch_id']}")
                print(f"  时间: {batch_info['start_time']} - {batch_info['end_time']}")
                print(f"  状态: {batch_info['status']}")
                print(f"  推文: {results['total_tweets']} 条")
                print(f"  成功率: {results['success_rate']:.1f}%")
    
    except KeyboardInterrupt:
        print("\n用户中断操作")
        if system.current_scraper:
            system.cancel_current_batch()
    
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # 运行主程序
    asyncio.run(main())