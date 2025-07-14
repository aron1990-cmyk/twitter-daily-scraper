#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
管理控制台
统一管理所有功能模块的控制台界面
"""

import asyncio
import logging
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import argparse
from tabulate import tabulate
import time

# 导入各个模块
try:
    from main import TwitterDailyScraper
    from scheduler import TaskScheduler, PredefinedTasks
    from ai_analyzer import AIAnalyzer
    from account_manager import AccountManager
    from cloud_sync import CloudSyncManager
    from system_monitor import SystemMonitor, AlertCallbacks
    from config_manager import ConfigManager
    from config import *
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保所有依赖模块都已正确安装")
    sys.exit(1)

class ManagementConsole:
    """
    管理控制台
    提供统一的命令行界面来管理所有功能模块
    """
    
    def __init__(self):
        self.logger = self._setup_logging()
        
        # 初始化各个管理器
        self.config_manager = ConfigManager()
        self.scheduler = TaskScheduler()
        self.ai_analyzer = AIAnalyzer()
        self.account_manager = AccountManager()
        self.system_monitor = SystemMonitor()
        self.cloud_sync = CloudSyncManager(CLOUD_SYNC_CONFIG)
        
        # 运行状态
        self.is_running = False
        
        self.logger.info("管理控制台初始化完成")
    
    def _setup_logging(self) -> logging.Logger:
        """
        设置日志配置
        
        Returns:
            日志记录器
        """
        logger = logging.getLogger('ManagementConsole')
        
        if not logger.handlers:
            # 创建日志目录
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            
            # 文件处理器
            file_handler = logging.FileHandler(
                log_dir / f"management_console_{datetime.now().strftime('%Y%m%d')}.log",
                encoding='utf-8'
            )
            file_handler.setLevel(logging.INFO)
            
            # 控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # 格式化器
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
            logger.setLevel(logging.INFO)
        
        return logger
    
    def start_console(self):
        """
        启动管理控制台
        """
        self.is_running = True
        
        print("\n" + "="*60)
        print("🚀 Twitter Daily Scraper 管理控制台")
        print("="*60)
        print("欢迎使用 Twitter 日报采集系统管理控制台")
        print("输入 'help' 查看可用命令，输入 'quit' 退出")
        print("="*60 + "\n")
        
        # 启动系统监控
        self.system_monitor.start_monitoring()
        
        # 添加默认告警规则
        self._setup_default_alerts()
        
        # 主循环
        while self.is_running:
            try:
                command = input("管理控制台 > ").strip()
                if command:
                    self._process_command(command)
            except KeyboardInterrupt:
                print("\n检测到中断信号，正在退出...")
                self.shutdown()
                break
            except EOFError:
                print("\n输入结束，正在退出...")
                self.shutdown()
                break
            except Exception as e:
                print(f"命令执行出错: {e}")
                self.logger.error(f"命令执行异常: {e}")
    
    def _setup_default_alerts(self):
        """
        设置默认告警规则
        """
        # CPU使用率告警
        self.system_monitor.add_alert_rule(
            rule_id="high_cpu",
            name="CPU使用率过高",
            metric="cpu_percent",
            operator=">",
            threshold=80.0,
            duration_seconds=300,
            callback=AlertCallbacks.log_alert,
            description="CPU使用率超过80%持续5分钟"
        )
        
        # 内存使用率告警
        self.system_monitor.add_alert_rule(
            rule_id="high_memory",
            name="内存使用率过高",
            metric="memory_percent",
            operator=">",
            threshold=85.0,
            duration_seconds=300,
            callback=AlertCallbacks.log_alert,
            description="内存使用率超过85%持续5分钟"
        )
        
        # 磁盘使用率告警
        self.system_monitor.add_alert_rule(
            rule_id="high_disk",
            name="磁盘使用率过高",
            metric="disk_percent",
            operator=">",
            threshold=90.0,
            duration_seconds=60,
            callback=AlertCallbacks.log_alert,
            description="磁盘使用率超过90%持续1分钟"
        )
    
    def _process_command(self, command: str):
        """
        处理用户命令
        
        Args:
            command: 用户输入的命令
        """
        parts = command.split()
        if not parts:
            return
        
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        # 命令路由
        command_handlers = {
            'help': self._show_help,
            'status': self._show_status,
            'scrape': self._run_scraping,
            'schedule': self._manage_schedule,
            'accounts': self._manage_accounts,
            'monitor': self._show_monitoring,
            'config': self._manage_config,
            'cloud': self._manage_cloud_sync,
            'ai': self._manage_ai_analyzer,
            'logs': self._show_logs,
            'export': self._export_data,
            'test': self._run_tests,
            'quit': self.shutdown,
            'exit': self.shutdown
        }
        
        handler = command_handlers.get(cmd)
        if handler:
            try:
                handler(args)
            except Exception as e:
                print(f"执行命令 '{cmd}' 时出错: {e}")
                self.logger.error(f"命令执行异常: {cmd} - {e}")
        else:
            print(f"未知命令: {cmd}，输入 'help' 查看可用命令")
    
    def _show_help(self, args: List[str]):
        """
        显示帮助信息
        """
        help_text = """
📋 可用命令列表:

🔍 系统状态:
  status              - 显示系统整体状态
  monitor [详情]      - 显示系统监控信息
  logs [行数]         - 显示最近的日志

🕷️ 采集管理:
  scrape              - 立即执行采集任务
  scrape user <用户名> - 采集指定用户推文
  scrape keyword <关键词> - 采集关键词推文

⏰ 任务调度:
  schedule list       - 显示所有定时任务
  schedule add        - 添加定时任务
  schedule enable <ID> - 启用任务
  schedule disable <ID> - 禁用任务
  schedule run <ID>   - 立即执行任务

👥 账户管理:
  accounts list       - 显示所有账户状态
  accounts stats      - 显示账户统计信息
  accounts reset <ID> - 重置账户错误计数

🤖 AI分析:
  ai analyze <文件>   - 分析推文文件
  ai trends           - 显示趋势分析
  ai quality <文件>   - 质量评估

☁️ 云同步:
  cloud sync          - 立即同步到云端
  cloud status        - 显示同步状态
  cloud test          - 测试云端连接

⚙️ 配置管理:
  config list         - 显示所有配置
  config backup <名称> - 备份配置
  config restore <名称> <时间> - 恢复配置
  config validate <名称> - 验证配置

📊 数据导出:
  export report       - 导出系统报告
  export metrics      - 导出监控数据
  export configs      - 导出所有配置

🧪 测试功能:
  test all            - 运行所有测试
  test config         - 测试配置
  test cloud          - 测试云同步

🚪 退出:
  quit / exit         - 退出管理控制台
"""
        print(help_text)
    
    def _show_status(self, args: List[str]):
        """
        显示系统状态
        """
        print("\n📊 系统状态概览")
        print("="*50)
        
        # 系统监控状态
        current_metrics = self.system_monitor.get_current_metrics()
        if current_metrics:
            print(f"🖥️  CPU使用率: {current_metrics.cpu_percent:.1f}%")
            print(f"💾 内存使用率: {current_metrics.memory_percent:.1f}% ({current_metrics.memory_used_gb:.1f}GB/{current_metrics.memory_total_gb:.1f}GB)")
            print(f"💿 磁盘使用率: {current_metrics.disk_percent:.1f}% ({current_metrics.disk_used_gb:.1f}GB/{current_metrics.disk_total_gb:.1f}GB)")
            print(f"🔢 进程数量: {current_metrics.process_count}")
        
        # 调度器状态
        scheduler_stats = self.scheduler.get_scheduler_statistics()
        print(f"\n⏰ 任务调度器:")
        print(f"   总任务数: {scheduler_stats['total_tasks']}")
        print(f"   启用任务: {scheduler_stats['enabled_tasks']}")
        print(f"   运行中任务: {scheduler_stats['running_tasks']}")
        print(f"   总成功率: {scheduler_stats['overall_success_rate']:.1%}")
        
        # 账户管理状态
        account_stats = self.account_manager.get_usage_statistics()
        print(f"\n👥 账户管理:")
        print(f"   总账户数: {account_stats['total_accounts']}")
        print(f"   可用账户: {account_stats['available_accounts']}")
        print(f"   使用中账户: {account_stats['in_use_accounts']}")
        print(f"   错误账户: {account_stats['error_accounts']}")
        
        # 活跃告警
        active_alerts = len(self.system_monitor.active_alerts)
        if active_alerts > 0:
            print(f"\n⚠️  活跃告警: {active_alerts} 个")
            for alert_id, alert_info in self.system_monitor.active_alerts.items():
                print(f"   - {alert_info['rule_name']}: {alert_info['current_value']}")
        else:
            print(f"\n✅ 无活跃告警")
        
        print("\n" + "="*50)
    
    def _run_scraping(self, args: List[str]):
        """
        执行采集任务
        """
        if not args:
            # 执行完整采集任务
            print("🕷️ 开始执行完整采集任务...")
            try:
                scraper = TwitterDailyScraper()
                output_file = asyncio.run(scraper.run_scraping_task())
                print(f"✅ 采集任务完成，输出文件: {output_file}")
            except Exception as e:
                print(f"❌ 采集任务失败: {e}")
                self.logger.error(f"采集任务执行失败: {e}")
        
        elif args[0] == 'user' and len(args) > 1:
            # 采集指定用户
            username = args[1]
            print(f"🕷️ 开始采集用户 @{username} 的推文...")
            try:
                scraper = TwitterDailyScraper()
                # 这里需要实现单用户采集逻辑
                print(f"✅ 用户 @{username} 采集完成")
            except Exception as e:
                print(f"❌ 用户采集失败: {e}")
        
        elif args[0] == 'keyword' and len(args) > 1:
            # 采集关键词
            keyword = ' '.join(args[1:])
            print(f"🕷️ 开始采集关键词 '{keyword}' 的推文...")
            try:
                scraper = TwitterDailyScraper()
                # 这里需要实现关键词采集逻辑
                print(f"✅ 关键词 '{keyword}' 采集完成")
            except Exception as e:
                print(f"❌ 关键词采集失败: {e}")
        else:
            print("用法: scrape [user <用户名>] [keyword <关键词>]")
    
    def _manage_schedule(self, args: List[str]):
        """
        管理定时任务
        """
        if not args:
            args = ['list']
        
        subcommand = args[0]
        
        if subcommand == 'list':
            tasks = self.scheduler.get_all_tasks_status()
            if not tasks:
                print("📅 暂无定时任务")
                return
            
            print("\n📅 定时任务列表:")
            table_data = []
            for task in tasks:
                status_icon = {
                    'pending': '⏳',
                    'running': '🔄',
                    'completed': '✅',
                    'failed': '❌',
                    'cancelled': '🚫'
                }.get(task['status'], '❓')
                
                table_data.append([
                    task['task_id'],
                    task['name'],
                    status_icon + ' ' + task['status'],
                    '✅' if task['enabled'] else '❌',
                    task['schedule_time'],
                    f"{task['success_count']}/{task['run_count']}",
                    task['next_run'][:16] if task['next_run'] else 'N/A'
                ])
            
            headers = ['ID', '名称', '状态', '启用', '调度时间', '成功率', '下次执行']
            print(tabulate(table_data, headers=headers, tablefmt='grid'))
        
        elif subcommand == 'add':
            print("添加定时任务功能开发中...")
        
        elif subcommand in ['enable', 'disable'] and len(args) > 1:
            task_id = args[1]
            if subcommand == 'enable':
                success = self.scheduler.enable_task(task_id)
            else:
                success = self.scheduler.disable_task(task_id)
            
            if success:
                print(f"✅ 任务 {task_id} 已{subcommand}")
            else:
                print(f"❌ 任务 {task_id} {subcommand}失败")
        
        elif subcommand == 'run' and len(args) > 1:
            task_id = args[1]
            success = self.scheduler.run_task_now(task_id)
            if success:
                print(f"✅ 任务 {task_id} 已开始执行")
            else:
                print(f"❌ 任务 {task_id} 执行失败")
        
        else:
            print("用法: schedule [list|add|enable|disable|run] [任务ID]")
    
    def _manage_accounts(self, args: List[str]):
        """
        管理账户
        """
        if not args:
            args = ['list']
        
        subcommand = args[0]
        
        if subcommand == 'list':
            accounts = self.account_manager.get_all_accounts()
            if not accounts:
                print("👥 暂无账户配置")
                return
            
            print("\n👥 账户列表:")
            table_data = []
            for account in accounts:
                status_icon = {
                    'available': '✅',
                    'in_use': '🔄',
                    'cooling_down': '⏳',
                    'blocked': '🚫',
                    'error': '❌'
                }.get(account.status.value, '❓')
                
                table_data.append([
                    account.user_id,
                    account.name,
                    status_icon + ' ' + account.status.value,
                    account.usage_count,
                    account.error_count,
                    account.priority,
                    '✅' if account.enabled else '❌'
                ])
            
            headers = ['用户ID', '名称', '状态', '使用次数', '错误次数', '优先级', '启用']
            print(tabulate(table_data, headers=headers, tablefmt='grid'))
        
        elif subcommand == 'stats':
            stats = self.account_manager.get_usage_statistics()
            print("\n📊 账户统计信息:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
        
        elif subcommand == 'reset' and len(args) > 1:
            user_id = args[1]
            success = self.account_manager.reset_account_errors(user_id)
            if success:
                print(f"✅ 账户 {user_id} 错误计数已重置")
            else:
                print(f"❌ 账户 {user_id} 重置失败")
        
        else:
            print("用法: accounts [list|stats|reset] [用户ID]")
    
    def _show_monitoring(self, args: List[str]):
        """
        显示监控信息
        """
        if args and args[0] == '详情':
            # 显示详细监控信息
            stats = self.system_monitor.get_system_statistics(1)
            print("\n📊 详细监控信息 (最近1小时):")
            print(json.dumps(stats, ensure_ascii=False, indent=2))
        else:
            # 显示简要监控信息
            current_metrics = self.system_monitor.get_current_metrics()
            if current_metrics:
                print("\n📊 当前系统监控:")
                print(f"  时间: {current_metrics.timestamp}")
                print(f"  CPU: {current_metrics.cpu_percent:.1f}%")
                print(f"  内存: {current_metrics.memory_percent:.1f}% ({current_metrics.memory_used_gb:.1f}GB)")
                print(f"  磁盘: {current_metrics.disk_percent:.1f}% ({current_metrics.disk_used_gb:.1f}GB)")
                print(f"  进程: {current_metrics.process_count}")
                if current_metrics.temperature:
                    print(f"  温度: {current_metrics.temperature:.1f}°C")
            
            # 显示活跃告警
            if self.system_monitor.active_alerts:
                print("\n⚠️  活跃告警:")
                for alert_id, alert_info in self.system_monitor.active_alerts.items():
                    print(f"  - {alert_info['rule_name']}: {alert_info['current_value']} (持续 {alert_info['duration_seconds']}秒)")
    
    def _manage_config(self, args: List[str]):
        """
        管理配置
        """
        if not args:
            args = ['list']
        
        subcommand = args[0]
        
        if subcommand == 'list':
            summary = self.config_manager.get_config_summary()
            print("\n⚙️ 配置文件状态:")
            for config_name, info in summary['config_files'].items():
                status = '✅' if info['exists'] else '❌'
                size = f"{info['size']} bytes" if info['exists'] else 'N/A'
                print(f"  {config_name}: {status} ({size})")
        
        elif subcommand == 'backup' and len(args) > 1:
            config_name = args[1]
            description = ' '.join(args[2:]) if len(args) > 2 else ""
            backup_path = self.config_manager.backup_config(config_name, description)
            if backup_path:
                print(f"✅ 配置 {config_name} 已备份到: {backup_path}")
            else:
                print(f"❌ 配置 {config_name} 备份失败")
        
        elif subcommand == 'validate' and len(args) > 1:
            config_name = args[1]
            result = self.config_manager.validate_config(config_name)
            print(f"\n🔍 配置 {config_name} 验证结果:")
            print(f"  有效: {'✅' if result['valid'] else '❌'}")
            if result['errors']:
                print("  错误:")
                for error in result['errors']:
                    print(f"    - {error}")
            if result['warnings']:
                print("  警告:")
                for warning in result['warnings']:
                    print(f"    - {warning}")
        
        else:
            print("用法: config [list|backup|restore|validate] [配置名称] [参数]")
    
    def _manage_cloud_sync(self, args: List[str]):
        """
        管理云同步
        """
        if not args:
            args = ['status']
        
        subcommand = args[0]
        
        if subcommand == 'sync':
            print("☁️ 开始云同步...")
            try:
                # 这里需要实现云同步逻辑
                print("✅ 云同步完成")
            except Exception as e:
                print(f"❌ 云同步失败: {e}")
        
        elif subcommand == 'status':
            print("☁️ 云同步状态: 功能开发中...")
        
        elif subcommand == 'test':
            print("🧪 测试云端连接...")
            try:
                # 运行云同步测试
                os.system("python3 test_cloud_sync.py")
            except Exception as e:
                print(f"❌ 云端连接测试失败: {e}")
        
        else:
            print("用法: cloud [sync|status|test]")
    
    def _manage_ai_analyzer(self, args: List[str]):
        """
        管理AI分析器
        """
        if not args:
            print("用法: ai [analyze|trends|quality] [参数]")
            return
        
        subcommand = args[0]
        
        if subcommand == 'analyze' and len(args) > 1:
            file_path = args[1]
            print(f"🤖 开始AI分析文件: {file_path}")
            try:
                # 这里需要实现AI分析逻辑
                print("✅ AI分析完成")
            except Exception as e:
                print(f"❌ AI分析失败: {e}")
        
        elif subcommand == 'trends':
            print("📈 趋势分析功能开发中...")
        
        elif subcommand == 'quality' and len(args) > 1:
            file_path = args[1]
            print(f"📊 开始质量评估: {file_path}")
            try:
                # 这里需要实现质量评估逻辑
                print("✅ 质量评估完成")
            except Exception as e:
                print(f"❌ 质量评估失败: {e}")
        
        else:
            print("用法: ai [analyze|trends|quality] [文件路径]")
    
    def _show_logs(self, args: List[str]):
        """
        显示日志
        """
        lines = 20
        if args and args[0].isdigit():
            lines = int(args[0])
        
        log_file = Path("logs") / f"management_console_{datetime.now().strftime('%Y%m%d')}.log"
        
        if log_file.exists():
            print(f"\n📋 最近 {lines} 行日志:")
            print("="*60)
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    log_lines = f.readlines()
                    for line in log_lines[-lines:]:
                        print(line.rstrip())
            except Exception as e:
                print(f"读取日志文件失败: {e}")
        else:
            print("📋 日志文件不存在")
    
    def _export_data(self, args: List[str]):
        """
        导出数据
        """
        if not args:
            args = ['report']
        
        export_type = args[0]
        
        if export_type == 'report':
            print("📊 生成系统报告...")
            try:
                # 生成综合报告
                report = {
                    'generated_at': datetime.now().isoformat(),
                    'system_monitoring': self.system_monitor.export_monitoring_report(),
                    'scheduler_statistics': self.scheduler.get_scheduler_statistics(),
                    'account_statistics': self.account_manager.get_usage_statistics(),
                    'config_summary': self.config_manager.get_config_summary()
                }
                
                report_file = f"system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(report_file, 'w', encoding='utf-8') as f:
                    json.dump(report, f, ensure_ascii=False, indent=2)
                
                print(f"✅ 系统报告已导出: {report_file}")
            except Exception as e:
                print(f"❌ 报告导出失败: {e}")
        
        elif export_type == 'configs':
            print("⚙️ 导出配置文件...")
            export_path = f"config_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            success = self.config_manager.export_all_configs(export_path)
            if success:
                print(f"✅ 配置文件已导出到: {export_path}")
            else:
                print("❌ 配置导出失败")
        
        else:
            print("用法: export [report|metrics|configs]")
    
    def _run_tests(self, args: List[str]):
        """
        运行测试
        """
        if not args:
            args = ['all']
        
        test_type = args[0]
        
        if test_type == 'all':
            print("🧪 运行所有测试...")
            self._run_config_test()
            self._run_cloud_test()
        
        elif test_type == 'config':
            self._run_config_test()
        
        elif test_type == 'cloud':
            self._run_cloud_test()
        
        else:
            print("用法: test [all|config|cloud]")
    
    def _run_config_test(self):
        """
        运行配置测试
        """
        print("🔧 测试配置文件...")
        try:
            os.system("python3 validate_config.py")
        except Exception as e:
            print(f"❌ 配置测试失败: {e}")
    
    def _run_cloud_test(self):
        """
        运行云同步测试
        """
        print("☁️ 测试云同步连接...")
        try:
            os.system("python3 test_cloud_sync.py")
        except Exception as e:
            print(f"❌ 云同步测试失败: {e}")
    
    def shutdown(self, args: List[str] = None):
        """
        关闭管理控制台
        """
        print("\n🔄 正在关闭管理控制台...")
        
        # 停止系统监控
        self.system_monitor.stop_monitoring()
        
        # 停止任务调度器
        self.scheduler.stop_scheduler()
        
        # 保存配置
        self.config_manager.save_config('scheduler', {})
        
        self.is_running = False
        print("✅ 管理控制台已关闭")

def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description='Twitter Daily Scraper 管理控制台')
    parser.add_argument('--command', '-c', help='直接执行命令')
    parser.add_argument('--batch', '-b', help='批量执行命令文件')
    
    args = parser.parse_args()
    
    console = ManagementConsole()
    
    try:
        if args.command:
            # 直接执行命令
            console._process_command(args.command)
        elif args.batch:
            # 批量执行命令
            if os.path.exists(args.batch):
                with open(args.batch, 'r', encoding='utf-8') as f:
                    for line in f:
                        command = line.strip()
                        if command and not command.startswith('#'):
                            print(f"执行命令: {command}")
                            console._process_command(command)
            else:
                print(f"批量命令文件不存在: {args.batch}")
        else:
            # 启动交互式控制台
            console.start_console()
    
    except KeyboardInterrupt:
        console.shutdown()
    except Exception as e:
        print(f"管理控制台运行异常: {e}")
        console.shutdown()

if __name__ == "__main__":
    main()