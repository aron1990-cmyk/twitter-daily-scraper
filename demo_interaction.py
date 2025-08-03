#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter自动互动引擎演示脚本
展示如何使用InteractionEngine进行自动化Twitter互动
"""

import asyncio
import json
from pathlib import Path
from core.interaction_engine import InteractionEngine


def create_demo_tweets():
    """
    创建演示用的推文数据
    """
    return [
        {
            'url': 'https://twitter.com/elonmusk/status/1234567890',
            'content': 'Exciting developments in AI and robotics! The future is here 🚀 #AI #Innovation',
            'likes': 2500,
            'retweets': 850,
            'user_url': 'https://twitter.com/elonmusk',
            'user_name': 'Elon Musk',
            'timestamp': '2024-01-15T10:30:00Z'
        },
        {
            'url': 'https://twitter.com/openai/status/1234567891',
            'content': 'New research paper on large language models published! Check out our latest findings.',
            'likes': 1200,
            'retweets': 400,
            'user_url': 'https://twitter.com/openai',
            'user_name': 'OpenAI',
            'timestamp': '2024-01-15T11:15:00Z'
        },
        {
            'url': 'https://twitter.com/github/status/1234567892',
            'content': 'GitHub Copilot now supports even more programming languages! 💻 #coding #developer',
            'likes': 800,
            'retweets': 200,
            'user_url': 'https://twitter.com/github',
            'user_name': 'GitHub',
            'timestamp': '2024-01-15T12:00:00Z'
        }
    ]


async def demo_basic_usage():
    """
    演示基本使用方法
    """
    print("🎯 Twitter自动互动引擎 - 基本使用演示")
    print("=" * 60)
    
    # 配置参数
    profile_id = "demo_profile_001"
    config_path = "config/interaction_config.yaml"
    
    try:
        # 初始化引擎
        print(f"🚀 初始化互动引擎...")
        print(f"   Profile ID: {profile_id}")
        print(f"   配置文件: {config_path}")
        
        engine = InteractionEngine(profile_id, config_path)
        
        # 显示配置信息
        print("\n⚙️ 当前配置:")
        print(f"   每日点赞限额: {engine.config['daily_limit']['like']}")
        print(f"   每日转发限额: {engine.config['daily_limit']['retweet']}")
        print(f"   每日评论限额: {engine.config['daily_limit']['comment']}")
        print(f"   每日私信限额: {engine.config['daily_limit']['dm']}")
        
        # 显示当前限额状态
        stats = engine.get_daily_stats()
        print("\n📊 当前限额状态:")
        for action, remaining in stats['remaining'].items():
            used = stats['used'].get(action, 0)
            total = stats['limits'].get(action, 0)
            print(f"   {action}: {used}/{total} (剩余: {remaining})")
        
        # 加载演示推文
        tweets = create_demo_tweets()
        print(f"\n📝 加载了 {len(tweets)} 条演示推文")
        
        # 显示推文评分
        print("\n🎯 推文评分分析:")
        for i, tweet in enumerate(tweets, 1):
            score = engine.scorer.score_tweet(tweet)
            print(f"   推文 {i}: {score:.2f} 分 - {tweet['content'][:60]}...")
        
        # 显示行为决策
        print("\n🎲 行为决策预测:")
        actions = ['like', 'retweet', 'comment', 'dm']
        for tweet in tweets:
            score = engine.scorer.score_tweet(tweet)
            print(f"\n   推文评分 {score:.2f}:")
            for action in actions:
                should_interact = engine._should_interact(action, score)
                probability = engine.random_behavior.get(f'{action}_probability', 0.5)
                adjusted_prob = probability * score
                status = "✅ 执行" if should_interact else "❌ 跳过"
                print(f"     {action}: {status} (基础概率: {probability:.1f}, 调整后: {adjusted_prob:.2f})")
            break  # 只显示第一条推文的决策
        
        print("\n⚠️ 注意: 完整的互动功能需要AdsPower浏览器环境")
        print("如需运行完整流程，请确保:")
        print("1. AdsPower客户端正在运行")
        print("2. 已创建对应的浏览器配置")
        print("3. 账号已登录Twitter")
        
        # 如果要执行真实互动，取消注释下面的代码
        # print("\n🤖 开始执行自动互动...")
        # results = await engine.run(tweets)
        # print(f"📈 执行结果: {json.dumps(results, indent=2, ensure_ascii=False)}")
        
    except FileNotFoundError as e:
        print(f"❌ 配置文件未找到: {e}")
        print("请确保 config/interaction_config.yaml 文件存在")
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


def demo_configuration():
    """
    演示配置文件的使用
    """
    print("\n🔧 配置文件演示")
    print("=" * 40)
    
    config_file = Path("config/interaction_config.yaml")
    if config_file.exists():
        print(f"✅ 配置文件存在: {config_file}")
        print("\n📋 配置文件内容预览:")
        with open(config_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()[:20]  # 只显示前20行
            for i, line in enumerate(lines, 1):
                print(f"   {i:2d}: {line.rstrip()}")
        if len(lines) >= 20:
            print("   ... (更多内容请查看完整配置文件)")
    else:
        print(f"❌ 配置文件不存在: {config_file}")
        print("请先运行主程序创建配置文件")


def demo_logs():
    """
    演示日志功能
    """
    print("\n📝 日志功能演示")
    print("=" * 40)
    
    logs_dir = Path("logs")
    if logs_dir.exists():
        log_files = list(logs_dir.glob("*.log"))
        if log_files:
            print(f"📁 发现 {len(log_files)} 个日志文件:")
            for log_file in log_files[:5]:  # 只显示前5个
                print(f"   📄 {log_file.name}")
            
            # 显示示例日志内容
            example_log = logs_dir / "interaction_example.log"
            if example_log.exists():
                print(f"\n📖 日志内容示例 ({example_log.name}):")
                with open(example_log, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[:10]  # 只显示前10行
                    for line in lines:
                        print(f"   {line.rstrip()}")
                if len(lines) >= 10:
                    print("   ... (更多内容请查看完整日志文件)")
        else:
            print("📁 日志目录存在但暂无日志文件")
    else:
        print("📁 日志目录不存在，将在首次运行时创建")


def main():
    """
    主演示函数
    """
    print("🎭 Twitter自动互动引擎 - 完整演示")
    print("=" * 80)
    
    try:
        # 配置演示
        demo_configuration()
        
        # 日志演示
        demo_logs()
        
        # 基本使用演示
        asyncio.run(demo_basic_usage())
        
        print("\n🎉 演示完成!")
        print("\n📚 更多信息请查看:")
        print("   📖 docs/interaction_engine_guide.md - 详细使用指南")
        print("   📄 README_INTERACTION_ENGINE.md - 模块说明")
        print("   ⚙️ config/interaction_config.yaml - 配置文件")
        print("   🧪 test_interaction.py - 测试脚本")
        
    except KeyboardInterrupt:
        print("\n⏹️ 演示被用户中断")
    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()