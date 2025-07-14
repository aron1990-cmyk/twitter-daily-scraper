#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版多窗口演示
测试多个AdsPower浏览器窗口的启动和显示
"""

import asyncio
import logging
import time
from datetime import datetime
from ads_browser_launcher import AdsPowerLauncher
from twitter_parser import TwitterParser
from config import ADS_POWER_CONFIG

class SimpleWindowDemo:
    def __init__(self, num_windows: int = 2):
        self.num_windows = num_windows
        self.windows = []
        self.logger = logging.getLogger(__name__)
        
    async def start_single_window(self, window_id: int, user_id: str):
        """
        启动单个窗口
        """
        try:
            print(f"🚀 启动窗口 {window_id}...")
            
            # 启动AdsPower浏览器
            launcher = AdsPowerLauncher()
            browser_info = launcher.start_browser(user_id)
            
            if not browser_info:
                print(f"❌ 窗口 {window_id} 启动失败")
                return None
            
            # 获取调试端口
            debug_port = browser_info.get('ws', {}).get('puppeteer', '')
            print(f"✅ 窗口 {window_id} 启动成功，调试端口: {debug_port}")
            
            # 连接Twitter解析器
            parser = TwitterParser(debug_port)
            await parser.connect_browser()
            print(f"🔗 窗口 {window_id} 解析器连接成功")
            
            # 模拟一些操作
            print(f"📱 窗口 {window_id} 开始模拟操作...")
            await asyncio.sleep(5)  # 模拟操作时间
            
            return {
                'window_id': window_id,
                'launcher': launcher,
                'parser': parser,
                'user_id': user_id
            }
            
        except Exception as e:
            print(f"❌ 窗口 {window_id} 出现错误: {e}")
            return None
    
    async def run_demo(self):
        """
        运行多窗口演示
        """
        print("\n" + "="*60)
        print("🚀 简化版多窗口演示")
        print(f"📅 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🪟 窗口数量: {self.num_windows}")
        print("="*60)
        
        # 获取用户ID列表
        multi_user_ids = ADS_POWER_CONFIG.get('multi_user_ids', [ADS_POWER_CONFIG['user_id']])
        actual_windows = min(self.num_windows, len(multi_user_ids))
        
        print(f"\n🎯 将启动 {actual_windows} 个窗口")
        for i in range(actual_windows):
            print(f"   窗口 {i+1}: 用户ID {multi_user_ids[i]}")
        
        try:
            # 并行启动所有窗口
            print("\n🔄 开始并行启动窗口...")
            tasks = []
            for i in range(actual_windows):
                task = self.start_single_window(i+1, multi_user_ids[i])
                tasks.append(task)
            
            # 等待所有窗口启动完成
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 统计结果
            successful_windows = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"❌ 窗口 {i+1} 启动异常: {result}")
                elif result is not None:
                    successful_windows.append(result)
                    print(f"✅ 窗口 {i+1} 启动成功")
                else:
                    print(f"❌ 窗口 {i+1} 启动失败")
            
            print(f"\n📊 启动结果: {len(successful_windows)}/{actual_windows} 个窗口成功")
            
            if successful_windows:
                print("\n🎉 多窗口启动成功！")
                print("💡 您现在应该能看到多个浏览器窗口同时打开")
                print("📱 每个窗口都是独立的Twitter抓取实例")
                
                # 保持窗口运行一段时间
                print("\n⏳ 窗口将保持运行30秒，您可以观察窗口状态...")
                for i in range(30):
                    print(f"\r⏱️  剩余时间: {30-i} 秒", end="", flush=True)
                    await asyncio.sleep(1)
                
                print("\n\n🧹 开始清理窗口...")
                # 清理所有窗口
                for window in successful_windows:
                    try:
                        await window['parser'].close()
                        window['launcher'].stop_browser(window['user_id'])
                        print(f"✅ 窗口 {window['window_id']} 清理完成")
                    except Exception as e:
                        print(f"⚠️ 窗口 {window['window_id']} 清理失败: {e}")
            else:
                print("\n❌ 没有窗口启动成功")
                
        except KeyboardInterrupt:
            print("\n⏹️ 用户中断操作")
        except Exception as e:
            print(f"\n💥 演示过程中出现错误: {e}")
        
        print("\n" + "="*60)
        print("🏁 多窗口演示结束")
        print(f"📅 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)

async def main():
    """
    主函数
    """
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 简化版多窗口演示启动")
    print("💡 这个演示将测试多个AdsPower浏览器窗口的启动")
    print("📱 您将看到多个浏览器窗口同时打开")
    
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
        
        # 确认开始
        input(f"\n🎯 按 Enter 键开始 {num_windows} 窗口演示 (Ctrl+C 取消)...")
        
        # 运行演示
        demo = SimpleWindowDemo(num_windows)
        await demo.run_demo()
        
    except KeyboardInterrupt:
        print("\n👋 用户取消操作")
    except Exception as e:
        print(f"\n💥 程序启动失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())