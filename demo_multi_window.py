#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多窗口并行抓取演示脚本
展示如何使用多个浏览器窗口同时进行Twitter数据抓取
"""

import asyncio
import sys
import os
from multi_window_scraper import MultiWindowScraper
from config import ADS_POWER_CONFIG, TWITTER_TARGETS, OUTPUT_CONFIG

def print_banner():
    """
    打印欢迎横幅
    """
    print("\n" + "="*80)
    print("🚀 Twitter 多窗口并行抓取器 - 演示版本")
    print("="*80)
    print("📱 功能特点:")
    print("   • 多个浏览器窗口同时运行")
    print("   • 实时显示抓取进度")
    print("   • 智能任务分配")
    print("   • 可视化操作过程")
    print("\n💡 使用说明:")
    print("   • 确保 AdsPower 客户端已启动")
    print("   • 程序将自动打开多个浏览器窗口")
    print("   • 每个窗口会显示不同的抓取任务")
    print("   • 您可以观察到窗口同步移动、点击、滚动")
    print("="*80)

def check_prerequisites():
    """
    检查运行前提条件
    """
    print("\n🔍 检查运行环境...")
    
    # 检查Python版本
    if sys.version_info < (3, 7):
        print("❌ 错误: 需要 Python 3.7 或更高版本")
        return False
    print("✅ Python 版本检查通过")
    
    # 检查配置
    if not ADS_POWER_CONFIG.get('user_id'):
        print("❌ 错误: AdsPower 用户ID未配置")
        return False
    print("✅ AdsPower 配置检查通过")
    
    # 检查目标配置
    if not TWITTER_TARGETS['accounts'] and not TWITTER_TARGETS['keywords']:
        print("❌ 错误: 未配置任何抓取目标")
        return False
    print("✅ 抓取目标配置检查通过")
    
    # 检查多用户ID配置
    multi_user_ids = ADS_POWER_CONFIG.get('multi_user_ids', [])
    if not multi_user_ids:
        print("⚠️ 警告: 未配置多个用户ID，将使用单一用户ID")
    else:
        print(f"✅ 发现 {len(multi_user_ids)} 个用户ID配置")
    
    return True

def show_target_distribution(num_windows: int):
    """
    显示目标分配情况
    """
    accounts = TWITTER_TARGETS['accounts']
    keywords = TWITTER_TARGETS['keywords']
    multi_user_ids = ADS_POWER_CONFIG.get('multi_user_ids', [ADS_POWER_CONFIG['user_id']])
    
    actual_windows = min(num_windows, len(multi_user_ids))
    accounts_per_window = len(accounts) // actual_windows
    keywords_per_window = len(keywords) // actual_windows
    
    print(f"\n📊 任务分配预览 ({actual_windows} 个窗口):")
    print("-" * 60)
    
    for i in range(actual_windows):
        start_acc = i * accounts_per_window
        end_acc = start_acc + accounts_per_window if i < actual_windows - 1 else len(accounts)
        window_accounts = accounts[start_acc:end_acc]
        
        start_kw = i * keywords_per_window
        end_kw = start_kw + keywords_per_window if i < actual_windows - 1 else len(keywords)
        window_keywords = keywords[start_kw:end_kw]
        
        print(f"🪟 窗口 {i+1} (用户ID: {multi_user_ids[i][:8]}...):")
        if window_accounts:
            print(f"   📱 账号 ({len(window_accounts)}): {', '.join(window_accounts[:3])}{'...' if len(window_accounts) > 3 else ''}")
        if window_keywords:
            print(f"   🔍 关键词 ({len(window_keywords)}): {', '.join(window_keywords[:3])}{'...' if len(window_keywords) > 3 else ''}")
        print()

async def run_demo(num_windows: int = 4):
    """
    运行多窗口抓取演示
    """
    scraper = None
    try:
        print(f"\n🚀 启动 {num_windows} 个窗口的并行抓取任务...")
        print("⏳ 正在初始化，请稍等...")
        
        # 创建多窗口抓取器
        scraper = MultiWindowScraper(num_windows=num_windows)
        
        # 执行并行抓取
        output_file = await scraper.run_parallel_scraping()
        
        if output_file:
            print("\n" + "="*80)
            print("🎉 多窗口抓取任务完成！")
            print("="*80)
            print(f"📊 Excel 报表: {output_file}")
            print(f"📁 数据目录: {OUTPUT_CONFIG['data_dir']}")
            print("\n💡 您可以打开Excel文件查看抓取结果")
            print("📈 文件包含详细的推文数据和统计信息")
        else:
            print("\n❌ 抓取任务失败，请查看日志了解详情")
            
    except KeyboardInterrupt:
        print("\n⏹️ 任务被用户中断")
        print("🧹 正在清理资源...")
    except Exception as e:
        print(f"\n❌ 任务执行失败: {e}")
        print("💡 请检查:")
        print("   • AdsPower 客户端是否正常运行")
        print("   • 网络连接是否正常")
        print("   • 配置文件是否正确")
    finally:
        if scraper:
            await scraper.cleanup_all_windows()
        print("\n✅ 资源清理完成")

def main():
    """
    主函数
    """
    # 打印欢迎信息
    print_banner()
    
    # 检查运行环境
    if not check_prerequisites():
        print("\n❌ 环境检查失败，程序退出")
        sys.exit(1)
    
    # 获取窗口数量
    try:
        if len(sys.argv) > 1:
            num_windows = int(sys.argv[1])
        else:
            num_windows = 4  # 默认4个窗口
        
        if num_windows < 1 or num_windows > 8:
            print("⚠️ 窗口数量应在 1-8 之间，使用默认值 4")
            num_windows = 4
            
    except ValueError:
        print("⚠️ 无效的窗口数量参数，使用默认值 4")
        num_windows = 4
    
    # 显示任务分配
    show_target_distribution(num_windows)
    
    # 确认开始
    try:
        input(f"\n🎯 按 Enter 键开始 {num_windows} 窗口并行抓取 (Ctrl+C 取消)...")
    except KeyboardInterrupt:
        print("\n👋 用户取消操作")
        sys.exit(0)
    
    # 运行演示
    try:
        asyncio.run(run_demo(num_windows))
    except Exception as e:
        print(f"\n💥 程序启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()