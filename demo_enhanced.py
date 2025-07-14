#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter Daily Scraper - Enhanced Features Demo
增强版功能演示脚本

此脚本演示如何使用增强版的各种功能，包括:
- AI内容分析
- 多账户管理
- 系统监控
- 任务调度
- 配置管理

使用方法:
    python3 demo_enhanced.py [功能名称]

可用功能:
    ai_analysis     - AI内容分析演示
    account_mgmt    - 账户管理演示
    monitoring      - 系统监控演示
    scheduling      - 任务调度演示
    config_mgmt     - 配置管理演示
    all             - 运行所有演示
"""

import sys
import os
import asyncio
import json
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_section(title):
    """打印章节标题"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_subsection(title):
    """打印子章节标题"""
    print(f"\n--- {title} ---")

async def demo_ai_analysis():
    """演示AI内容分析功能"""
    print_section("AI内容分析功能演示")
    
    try:
        from ai_analyzer import AIAnalyzer
        
        print_subsection("初始化AI分析器")
        analyzer = AIAnalyzer()
        print("✅ AI分析器初始化成功")
        
        # 模拟推文数据
        sample_tweets = [
            {
                'content': '人工智能技术的发展真是令人惊叹！ChatGPT的能力让我们看到了AI的巨大潜力。',
                'likes': 150,
                'retweets': 45,
                'comments': 23,
                'author': 'tech_enthusiast',
                'created_at': datetime.now().isoformat()
            },
            {
                'content': '今天的天气不错，适合出门散步。',
                'likes': 5,
                'retweets': 1,
                'comments': 2,
                'author': 'casual_user',
                'created_at': datetime.now().isoformat()
            },
            {
                'content': '区块链技术将彻底改变金融行业的未来，这是一个革命性的创新！',
                'likes': 89,
                'retweets': 34,
                'comments': 12,
                'author': 'blockchain_expert',
                'created_at': datetime.now().isoformat()
            }
        ]
        
        print_subsection("分析推文质量")
        for i, tweet in enumerate(sample_tweets, 1):
            quality_score = analyzer.assess_tweet_quality(tweet)
            print(f"推文 {i}: 质量评分 = {quality_score:.1f}/100")
            print(f"  内容: {tweet['content'][:50]}...")
        
        print_subsection("情感分析")
        for i, tweet in enumerate(sample_tweets, 1):
            sentiment = analyzer.analyze_sentiment(tweet['content'])
            print(f"推文 {i}: 情感倾向 = {sentiment}")
        
        print_subsection("参与度评分")
        for i, tweet in enumerate(sample_tweets, 1):
            engagement = analyzer.calculate_engagement_score(tweet)
            print(f"推文 {i}: 参与度评分 = {engagement:.1f}")
        
        print_subsection("趋势相关性分析")
        for i, tweet in enumerate(sample_tweets, 1):
            relevance = analyzer.analyze_trend_relevance(tweet['content'])
            print(f"推文 {i}: 趋势相关性 = {relevance:.1f}")
        
        print_subsection("批量分析")
        insights = await analyzer.analyze_tweets_batch(sample_tweets)
        print(f"✅ 批量分析完成，处理了 {len(insights)} 条推文")
        
        # 生成洞察报告
        print_subsection("生成洞察报告")
        report = await analyzer.generate_insights_report(sample_tweets)
        print(f"✅ 洞察报告生成完成")
        print(f"  - 总推文数: {report['summary']['total_tweets']}")
        print(f"  - 平均质量评分: {report['summary']['avg_quality_score']:.1f}")
        print(f"  - 情感分布: {report['summary']['sentiment_distribution']}")
        
    except Exception as e:
        print(f"❌ AI分析演示失败: {e}")

def demo_account_management():
    """演示账户管理功能"""
    print_section("多账户管理功能演示")
    
    try:
        from account_manager import AccountManager
        import json
        
        print_subsection("加载账户配置")
        # 加载accounts.json配置文件
        accounts_file = Path(__file__).parent / "accounts" / "accounts.json"
        if accounts_file.exists():
            with open(accounts_file, 'r', encoding='utf-8') as f:
                accounts_config = json.load(f)
            print(f"✅ 成功加载 {len(accounts_config)} 个账户配置")
        else:
            print("⚠️  accounts.json文件不存在，使用演示配置")
            accounts_config = [
                {
                    'user_id': 'demo_account_1',
                    'name': '演示账户1',
                    'priority': 1,
                    'daily_limit': 10,
                    'hourly_limit': 2
                }
            ]
        
        print_subsection("初始化账户管理器")
        manager = AccountManager(accounts_config)
        print("✅ 账户管理器初始化成功")
        
        print_subsection("显示已加载的账户")
        for account in manager.accounts:
            print(f"✅ 账户: {account.name} (ID: {account.user_id}) | 优先级: {account.priority} | 日限制: {account.daily_usage_limit}")
        
        print_subsection("查看账户状态")
        for account in manager.accounts:
            print(f"账户: {account.name} | 状态: {account.status.value} | 优先级: {account.priority} | 使用次数: {account.usage_count}")
        
        print_subsection("获取可用账户")
        available = manager.get_available_account()
        if available:
            print(f"✅ 获取到可用账户: {available.name} (ID: {available.user_id})")
        else:
            print("⚠️  当前没有可用账户")
        
        print_subsection("账户使用统计")
        stats = manager.get_account_statistics()
        print(f"总账户数: {stats['total_accounts']}")
        print(f"状态分布: {stats['status_distribution']}")
        print(f"总使用次数: {stats['total_usage_count']}")
        print(f"今日使用次数: {stats['total_daily_usage']}")
        
        print_subsection("测试账户使用流程")
        if available:
            print(f"尝试使用账户: {available.name}")
            if manager.use_account(available):
                print(f"✅ 成功开始使用账户: {available.name}")
                print(f"当前账户状态: {available.status.value}")
                # 模拟任务完成
                manager.release_account(available, success=True)
                print(f"✅ 任务完成，账户已释放")
                print(f"账户状态: {available.status.value}")
            else:
                print(f"❌ 无法使用账户: {available.name}")
        
    except Exception as e:
        print(f"❌ 账户管理演示失败: {e}")

def demo_system_monitoring():
    """演示系统监控功能"""
    print_section("系统监控功能演示")
    
    try:
        from system_monitor import SystemMonitor
        
        print_subsection("初始化系统监控器")
        monitor = SystemMonitor()
        print("✅ 系统监控器初始化成功")
        
        print_subsection("获取当前系统指标")
        metrics = monitor.get_current_metrics()
        print(f"CPU使用率: {metrics.cpu_percent:.1f}%")
        print(f"内存使用率: {metrics.memory_percent:.1f}%")
        print(f"磁盘使用率: {metrics.disk_percent:.1f}%")
        print(f"网络发送: {metrics.network_sent_mb:.1f} MB")
        print(f"网络接收: {metrics.network_recv_mb:.1f} MB")
        
        print_subsection("获取进程指标")
        process_metrics = monitor.get_process_metrics()
        print(f"进程CPU使用率: {process_metrics.cpu_percent:.1f}%")
        print(f"进程内存使用: {process_metrics.memory_mb:.1f} MB")
        print(f"进程线程数: {process_metrics.num_threads}")
        
        print_subsection("检查告警规则")
        alerts = monitor.check_alerts()
        if alerts:
            print(f"⚠️  发现 {len(alerts)} 个告警:")
            for alert in alerts:
                print(f"  - {alert['rule_name']}: {alert['message']}")
        else:
            print("✅ 当前没有告警")
        
        print_subsection("生成监控报告")
        report = monitor.generate_report()
        print(f"✅ 监控报告生成完成")
        print(f"  - 监控时长: {report['monitoring_duration']}")
        print(f"  - 数据点数: {report['total_data_points']}")
        print(f"  - 告警次数: {report['total_alerts']}")
        
    except Exception as e:
        print(f"❌ 系统监控演示失败: {e}")

async def demo_task_scheduling():
    """演示任务调度功能"""
    print_section("任务调度功能演示")
    
    try:
        from scheduler import TaskScheduler
        
        print_subsection("初始化任务调度器")
        scheduler = TaskScheduler()
        print("✅ 任务调度器初始化成功")
        
        print_subsection("添加测试任务")
        
        # 添加一个简单的测试任务
        def test_task():
            print(f"[{datetime.now()}] 测试任务执行中...")
            return "任务执行成功"
        
        task_id = scheduler.add_task(
            task_id='demo_task',
            name='演示任务',
            func=test_task,
            trigger='interval',
            seconds=10,
            enabled=False  # 不自动启用，仅用于演示
        )
        print(f"✅ 添加任务: {task_id}")
        
        print_subsection("查看任务列表")
        tasks = scheduler.get_all_tasks()
        for task in tasks:
            print(f"任务: {task.name} | 状态: {'启用' if task.enabled else '禁用'} | 触发器: {task.trigger}")
        
        print_subsection("手动执行任务")
        result = await scheduler.execute_task_once('demo_task')
        if result['success']:
            print(f"✅ 任务执行成功: {result['result']}")
        else:
            print(f"❌ 任务执行失败: {result['error']}")
        
        print_subsection("获取调度器状态")
        status = scheduler.get_scheduler_status()
        print(f"调度器状态: {status['status']}")
        print(f"总任务数: {status['total_tasks']}")
        print(f"启用任务数: {status['enabled_tasks']}")
        
    except Exception as e:
        print(f"❌ 任务调度演示失败: {e}")

def demo_config_management():
    """演示配置管理功能"""
    print_section("配置管理功能演示")
    
    try:
        from config_manager import ConfigManager
        
        print_subsection("初始化配置管理器")
        config_mgr = ConfigManager()
        print("✅ 配置管理器初始化成功")
        
        print_subsection("创建测试配置")
        test_config = {
            'demo_setting': {
                'enabled': True,
                'value': 42,
                'description': '这是一个演示配置'
            },
            'created_at': datetime.now().isoformat()
        }
        
        config_mgr.save_config('demo_config', test_config)
        print("✅ 保存测试配置")
        
        print_subsection("加载配置")
        loaded_config = config_mgr.load_config('demo_config')
        if loaded_config:
            print(f"✅ 加载配置成功: {loaded_config['demo_setting']['description']}")
        else:
            print("❌ 配置加载失败")
        
        print_subsection("备份配置")
        backup_path = config_mgr.backup_config('demo_config')
        if backup_path:
            print(f"✅ 配置备份成功: {backup_path}")
        else:
            print("❌ 配置备份失败")
        
        print_subsection("列出备份")
        backups = config_mgr.list_backups('demo_config')
        print(f"找到 {len(backups)} 个备份文件:")
        for backup in backups[:3]:  # 只显示前3个
            print(f"  - {backup}")
        
        print_subsection("验证配置")
        is_valid = config_mgr.validate_config('demo_config', loaded_config)
        print(f"配置验证结果: {'✅ 有效' if is_valid else '❌ 无效'}")
        
    except Exception as e:
        print(f"❌ 配置管理演示失败: {e}")

async def run_all_demos():
    """运行所有演示"""
    print_section("Twitter Daily Scraper - 增强功能全面演示")
    print(f"演示开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    demos = [
        ("AI内容分析", demo_ai_analysis),
        ("多账户管理", demo_account_management),
        ("系统监控", demo_system_monitoring),
        ("任务调度", demo_task_scheduling),
        ("配置管理", demo_config_management)
    ]
    
    for demo_name, demo_func in demos:
        try:
            print(f"\n🚀 开始演示: {demo_name}")
            if asyncio.iscoroutinefunction(demo_func):
                await demo_func()
            else:
                demo_func()
            print(f"✅ {demo_name} 演示完成")
        except Exception as e:
            print(f"❌ {demo_name} 演示失败: {e}")
    
    print_section("演示总结")
    print("🎉 所有功能演示完成！")
    print("\n📚 更多信息请查看:")
    print("  - README.md - 完整使用指南")
    print("  - config_enhanced_example.py - 配置示例")
    print("  - run_enhanced.py - 增强版启动脚本")
    print("\n🚀 开始使用:")
    print("  python3 setup_enhanced.py        # 一键设置")
    print("  python3 run_enhanced.py --help   # 查看帮助")
    print("  ./quick_start.sh                 # 快速开始")

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python3 demo_enhanced.py [功能名称]")
        print("\n可用功能:")
        print("  ai_analysis  - AI内容分析演示")
        print("  account_mgmt - 账户管理演示")
        print("  monitoring   - 系统监控演示")
        print("  scheduling   - 任务调度演示")
        print("  config_mgmt  - 配置管理演示")
        print("  all          - 运行所有演示")
        return 1
    
    demo_type = sys.argv[1].lower()
    
    try:
        if demo_type == 'ai_analysis':
            asyncio.run(demo_ai_analysis())
        elif demo_type == 'account_mgmt':
            demo_account_management()
        elif demo_type == 'monitoring':
            demo_system_monitoring()
        elif demo_type == 'scheduling':
            asyncio.run(demo_task_scheduling())
        elif demo_type == 'config_mgmt':
            demo_config_management()
        elif demo_type == 'all':
            asyncio.run(run_all_demos())
        else:
            print(f"❌ 未知的演示类型: {demo_type}")
            return 1
    
    except KeyboardInterrupt:
        print("\n\n⚠️  演示被用户中断")
        return 0
    except Exception as e:
        print(f"\n❌ 演示执行失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)