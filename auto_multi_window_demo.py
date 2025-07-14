#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动运行的多窗口Twitter抓取演示
无需用户交互，直接展示多窗口并行抓取功能
"""

import asyncio
import logging
import time
import json
from datetime import datetime
from typing import List, Dict, Any
from ads_browser_launcher import AdsPowerLauncher
from twitter_parser import TwitterParser
from config import ADS_POWER_CONFIG, TWITTER_TARGETS

class AutoMultiWindowDemo:
    def __init__(self, num_windows: int = 2):
        self.num_windows = num_windows
        self.windows = []
        self.all_tweets = []
        self.logger = logging.getLogger(__name__)
        
    def distribute_targets(self, targets: List[str], num_windows: int) -> List[List[str]]:
        """
        将目标分配给不同窗口
        """
        if not targets:
            return [[] for _ in range(num_windows)]
        
        # 平均分配
        targets_per_window = len(targets) // num_windows
        remainder = len(targets) % num_windows
        
        distributed = []
        start_idx = 0
        
        for i in range(num_windows):
            # 前面的窗口多分配一个目标（如果有余数）
            window_size = targets_per_window + (1 if i < remainder else 0)
            end_idx = start_idx + window_size
            
            window_targets = targets[start_idx:end_idx]
            distributed.append(window_targets)
            start_idx = end_idx
        
        return distributed
    
    async def scrape_single_window(self, window_id: int, user_id: str, targets: List[str]):
        """
        单个窗口的抓取任务
        """
        window_tweets = []
        launcher = None
        parser = None
        
        try:
            print(f"\n🚀 窗口 {window_id} 开始启动...")
            
            # 启动AdsPower浏览器
            launcher = AdsPowerLauncher()
            browser_info = launcher.start_browser(user_id)
            
            if not browser_info:
                print(f"❌ 窗口 {window_id} 浏览器启动失败")
                return []
            
            # 获取调试端口
            debug_port = browser_info.get('ws', {}).get('puppeteer', '')
            print(f"✅ 窗口 {window_id} 浏览器启动成功")
            
            # 连接Twitter解析器
            parser = TwitterParser(debug_port)
            await parser.connect_browser()
            print(f"🔗 窗口 {window_id} 解析器连接成功")
            
            # 开始抓取目标
            for i, target in enumerate(targets, 1):
                try:
                    print(f"📱 窗口 {window_id} 正在抓取 @{target} ({i}/{len(targets)})...")
                    
                    # 抓取推文（限制数量以加快演示）
                    tweets = await parser.scrape_user_tweets(
                        username=target.replace('@', ''),
                        max_tweets=3  # 进一步限制数量以加快速度
                    )
                    
                    if tweets:
                        print(f"✅ 窗口 {window_id} 从 @{target} 抓取到 {len(tweets)} 条推文")
                        # 为推文添加窗口标识
                        for tweet in tweets:
                            tweet['window_id'] = window_id
                            tweet['scraped_from'] = f"@{target}"
                        window_tweets.extend(tweets)
                    else:
                        print(f"⚠️ 窗口 {window_id} 从 @{target} 未抓取到推文")
                    
                    # 短暂延迟
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    print(f"❌ 窗口 {window_id} 抓取 @{target} 时出错: {e}")
                    continue
            
            print(f"🎉 窗口 {window_id} 完成所有抓取任务，共获得 {len(window_tweets)} 条推文")
            return window_tweets
            
        except Exception as e:
            print(f"💥 窗口 {window_id} 出现严重错误: {e}")
            return []
        
        finally:
            # 清理资源
            try:
                if parser:
                    await parser.close()
                if launcher:
                    launcher.stop_browser(user_id)
                print(f"🧹 窗口 {window_id} 资源清理完成")
            except Exception as e:
                print(f"⚠️ 窗口 {window_id} 清理时出错: {e}")
    
    async def display_progress(self, tasks):
        """
        显示实时进度
        """
        start_time = time.time()
        
        while not all(task.done() for task in tasks):
            elapsed = int(time.time() - start_time)
            print(f"\r⏱️  运行时间: {elapsed}秒 | 🔄 窗口状态: {sum(1 for t in tasks if t.done())}/{len(tasks)} 完成", end="", flush=True)
            await asyncio.sleep(2)
        
        print("\n")
    
    async def run_auto_demo(self):
        """
        运行自动多窗口抓取演示
        """
        print("\n" + "="*80)
        print("🚀 自动多窗口Twitter抓取演示")
        print(f"📅 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🪟 窗口数量: {self.num_windows}")
        print("💡 此演示将自动运行，无需用户交互")
        print("="*80)
        
        # 获取配置
        multi_user_ids = ADS_POWER_CONFIG.get('multi_user_ids', [ADS_POWER_CONFIG['user_id']])
        twitter_accounts = TWITTER_TARGETS.get('accounts', [])
        
        # 调整窗口数量
        actual_windows = min(self.num_windows, len(multi_user_ids), len(twitter_accounts))
        
        if actual_windows < self.num_windows:
            print(f"⚠️ 调整窗口数量为 {actual_windows}（受用户ID或目标账号数量限制）")
        
        # 分配目标
        distributed_targets = self.distribute_targets(twitter_accounts[:actual_windows*2], actual_windows)
        
        print(f"\n📊 任务分配预览 ({actual_windows} 个窗口):")
        print("-"*60)
        for i in range(actual_windows):
            targets = distributed_targets[i]
            user_id_display = multi_user_ids[i][:8] + "..."
            print(f"🪟 窗口 {i+1} (用户ID: {user_id_display}):")
            print(f"   📱 目标账号: {', '.join(targets) if targets else '无'}")
        
        try:
            print(f"\n🚀 自动启动 {actual_windows} 个窗口的并行抓取任务...")
            print("⏳ 正在初始化，请稍等...")
            
            # 创建并行任务
            tasks = []
            for i in range(actual_windows):
                task = asyncio.create_task(self.scrape_single_window(
                    window_id=i+1,
                    user_id=multi_user_ids[i],
                    targets=distributed_targets[i]
                ))
                tasks.append(task)
            
            # 显示进度并等待完成
            progress_task = asyncio.create_task(self.display_progress(tasks))
            results = await asyncio.gather(*tasks, return_exceptions=True)
            progress_task.cancel()
            
            # 收集结果
            total_tweets = 0
            successful_windows = 0
            
            print("\n" + "="*80)
            print("📊 抓取结果汇总")
            print("="*80)
            
            for i, result in enumerate(results, 1):
                if isinstance(result, Exception):
                    print(f"❌ 窗口 {i} 抓取异常: {result}")
                elif isinstance(result, list):
                    tweet_count = len(result)
                    total_tweets += tweet_count
                    successful_windows += 1
                    self.all_tweets.extend(result)
                    print(f"✅ 窗口 {i} 成功抓取 {tweet_count} 条推文")
                else:
                    print(f"⚠️ 窗口 {i} 返回了意外结果")
            
            print(f"\n🎉 抓取完成！")
            print(f"📊 成功窗口: {successful_windows}/{actual_windows}")
            print(f"📱 总推文数: {total_tweets}")
            
            # 保存结果
            if self.all_tweets:
                output_file = f"auto_multi_window_tweets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(self.all_tweets, f, ensure_ascii=False, indent=2)
                print(f"💾 结果已保存到: {output_file}")
                
                # 显示部分推文示例
                print("\n📝 推文示例:")
                for i, tweet in enumerate(self.all_tweets[:3], 1):
                    text = tweet.get('text', '')[:80] + "..." if len(tweet.get('text', '')) > 80 else tweet.get('text', '')
                    print(f"   {i}. [{tweet.get('scraped_from', 'Unknown')}] {text}")
            
            # 演示多窗口的优势
            print(f"\n🚀 多窗口抓取优势演示:")
            print(f"   📈 并行效率: {actual_windows} 个窗口同时工作")
            print(f"   ⚡ 时间节省: 相比单窗口可节省约 {(actual_windows-1)*100//actual_windows}% 时间")
            print(f"   🎯 任务分配: 智能分配不同目标给不同窗口")
            print(f"   👀 可视化: 您可以看到多个浏览器窗口同步操作")
            
        except KeyboardInterrupt:
            print("\n⏹️ 用户中断操作")
        except Exception as e:
            print(f"\n💥 演示过程中出现错误: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "="*80)
        print("🏁 自动多窗口抓取演示结束")
        print(f"📅 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("💡 演示完成！您已经看到了多窗口并行抓取的强大功能")
        print("="*80)

async def main():
    """
    主函数
    """
    # 配置日志（减少输出）
    logging.basicConfig(
        level=logging.ERROR,  # 只显示错误日志
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 自动多窗口Twitter抓取演示")
    print("💡 这个演示将自动展示多个浏览器窗口同时抓取不同Twitter账号")
    print("📱 您将看到窗口同步移动、点击、滚动和抓取")
    print("⚡ 无需任何用户交互，程序将自动运行")
    
    try:
        # 获取窗口数量
        import sys
        if len(sys.argv) > 1:
            num_windows = int(sys.argv[1])
        else:
            num_windows = 2
        
        if num_windows < 1 or num_windows > 4:
            print("⚠️ 窗口数量应在 1-4 之间，使用默认值 2")
            num_windows = 2
        
        print(f"\n⏳ 3秒后自动开始 {num_windows} 窗口演示...")
        for i in range(3, 0, -1):
            print(f"\r🕐 倒计时: {i} 秒", end="", flush=True)
            await asyncio.sleep(1)
        print("\n")
        
        # 运行演示
        demo = AutoMultiWindowDemo(num_windows)
        await demo.run_auto_demo()
        
    except KeyboardInterrupt:
        print("\n👋 用户取消操作")
    except Exception as e:
        print(f"\n💥 程序启动失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())