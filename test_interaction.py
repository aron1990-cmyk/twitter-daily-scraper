#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter自动互动引擎测试脚本

演示如何使用InteractionEngine进行Twitter自动互动
包括点赞、转发、评论、私信等功能的测试
"""

import asyncio
import json
from pathlib import Path
from typing import List, Dict

from core.interaction_engine import InteractionEngine


def load_sample_tweets() -> List[Dict]:
    """
    加载示例推文数据
    在实际使用中，这些数据应该来自Twitter抓取系统
    """
    sample_tweets = [
        {
            'url': 'https://twitter.com/user1/status/1234567890',
            'content': 'Excited to share our new AI research on machine learning algorithms! #AI #MachineLearning',
            'likes': 25,
            'retweets': 8,
            'user_url': 'https://twitter.com/user1',
            'user_name': 'AI Researcher',
            'timestamp': '2024-01-15T10:30:00Z'
        },
        {
            'url': 'https://twitter.com/user2/status/1234567891',
            'content': 'Just published a comprehensive guide on Python programming best practices. Check it out!',
            'likes': 45,
            'retweets': 12,
            'user_url': 'https://twitter.com/user2',
            'user_name': 'Python Developer',
            'timestamp': '2024-01-15T11:15:00Z'
        },
        {
            'url': 'https://twitter.com/user3/status/1234567892',
            'content': 'Blockchain technology is revolutionizing the way we think about data security and transparency.',
            'likes': 18,
            'retweets': 6,
            'user_url': 'https://twitter.com/user3',
            'user_name': 'Blockchain Expert',
            'timestamp': '2024-01-15T12:00:00Z'
        },
        {
            'url': 'https://twitter.com/user4/status/1234567893',
            'content': 'This is just another promotional tweet with lots of ads and spam content.',
            'likes': 2,
            'retweets': 0,
            'user_url': 'https://twitter.com/user4',
            'user_name': 'Spammer',
            'timestamp': '2024-01-15T13:30:00Z'
        },
        {
            'url': 'https://twitter.com/user5/status/1234567894',
            'content': 'Deep learning models are achieving unprecedented accuracy in natural language processing tasks!',
            'likes': 67,
            'retweets': 23,
            'user_url': 'https://twitter.com/user5',
            'user_name': 'NLP Scientist',
            'timestamp': '2024-01-15T14:45:00Z'
        }
    ]
    
    return sample_tweets


async def test_interaction_engine():
    """
    测试InteractionEngine的主要功能
    """
    # 配置参数
    profile_id = "test_profile_001"  # AdsPower浏览器配置ID
    config_path = "config/interaction_config.yaml"
    
    print(f"🚀 开始测试Twitter自动互动引擎")
    print(f"📋 Profile ID: {profile_id}")
    print(f"⚙️ 配置文件: {config_path}")
    print("-" * 50)
    
    try:
        # 初始化互动引擎
        engine = InteractionEngine(profile_id, config_path)
        
        # 显示当前限额状态
        stats = engine.get_daily_stats()
        print("📊 当前每日限额状态:")
        for action, remaining in stats['remaining'].items():
            used = stats['used'].get(action, 0)
            total = stats['limits'].get(action, 0)
            print(f"  {action}: {used}/{total} (剩余: {remaining})")
        print()
        
        # 加载测试推文
        tweets = load_sample_tweets()
        print(f"📝 加载了 {len(tweets)} 条测试推文")
        
        # 显示推文评分
        print("\n🎯 推文评分结果:")
        for i, tweet in enumerate(tweets, 1):
            score = engine.scorer.score_tweet(tweet)
            print(f"  推文 {i}: {score:.2f} - {tweet['content'][:50]}...")
        print()
        
        # 执行互动任务
        print("🤖 开始执行自动互动任务...")
        results = await engine.run(tweets)
        
        # 显示结果
        print("\n📈 互动任务执行结果:")
        if results['success']:
            print(f"  ✅ 任务执行成功")
            print(f"  📊 处理推文数: {results['total_tweets']}")
            print(f"  💖 点赞次数: {results['interactions']['like']}")
            print(f"  🔄 转发次数: {results['interactions']['retweet']}")
            print(f"  💬 评论次数: {results['interactions']['comment']}")
            print(f"  📩 私信次数: {results['interactions']['dm']}")
        else:
            print(f"  ❌ 任务执行失败: {results.get('error', '未知错误')}")
        
        # 显示更新后的限额状态
        updated_stats = engine.get_daily_stats()
        print("\n📊 更新后的每日限额状态:")
        for action, remaining in updated_stats['remaining'].items():
            used = updated_stats['used'].get(action, 0)
            total = updated_stats['limits'].get(action, 0)
            print(f"  {action}: {used}/{total} (剩余: {remaining})")
        
    except FileNotFoundError as e:
        print(f"❌ 配置文件未找到: {e}")
        print("请确保 config/interaction_config.yaml 文件存在")
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


async def test_individual_functions():
    """
    测试单个功能函数
    """
    profile_id = "test_profile_002"
    config_path = "config/interaction_config.yaml"
    
    print("\n🔧 测试单个功能函数")
    print("-" * 50)
    
    try:
        engine = InteractionEngine(profile_id, config_path)
        
        # 测试推文评分
        test_tweet = {
            'content': 'Amazing breakthrough in AI and machine learning research! #AI #Innovation',
            'likes': 100,
            'retweets': 50
        }
        
        score = engine.scorer.score_tweet(test_tweet)
        print(f"📊 推文评分测试: {score:.2f}")
        
        # 测试限额检查
        print("\n🚦 限额检查测试:")
        actions = ['like', 'retweet', 'comment', 'dm']
        for action in actions:
            can_perform = engine.limit_tracker.can_perform_action(action)
            remaining = engine.limit_tracker.get_remaining_count(action)
            print(f"  {action}: {'✅' if can_perform else '❌'} (剩余: {remaining})")
        
        # 测试行为决策
        print("\n🎲 行为决策测试:")
        for action in actions:
            should_interact = engine._should_interact(action, score)
            probability = engine.random_behavior.get(f'{action}_probability', 0.5)
            print(f"  {action}: {'✅' if should_interact else '❌'} (概率: {probability}, 调整后: {probability * score:.2f})")
        
        # 行为模拟器需要page对象，在实际使用时才初始化
        print("\n✅ 核心功能测试通过")
        
    except Exception as e:
        print(f"❌ 单个功能测试失败: {e}")


def main():
    """
    主函数
    """
    print("🎯 Twitter自动互动引擎测试程序")
    print("=" * 60)
    
    # 检查配置文件是否存在
    config_file = Path("config/interaction_config.yaml")
    if not config_file.exists():
        print("❌ 配置文件不存在，请先创建 config/interaction_config.yaml")
        return
    
    # 运行测试
    try:
        # 测试单个功能
        asyncio.run(test_individual_functions())
        
        # 测试完整流程（注释掉，因为需要真实的AdsPower环境）
        print("\n⚠️ 完整互动测试需要真实的AdsPower浏览器环境")
        print("如需测试完整流程，请确保:")
        print("1. AdsPower客户端正在运行")
        print("2. 已创建对应的浏览器配置")
        print("3. 账号已登录Twitter")
        print("\n取消注释下面的代码行来运行完整测试:")
        print("# await test_interaction_engine()")
        
        # 如果要测试完整流程，取消注释下面这行
        # asyncio.run(test_interaction_engine())
        
    except KeyboardInterrupt:
        print("\n⏹️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生未预期的错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ 测试完成")


if __name__ == "__main__":
    main()