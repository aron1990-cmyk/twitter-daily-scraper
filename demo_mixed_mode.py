#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter 混合模式采集演示
结合博主采集和关键词搜索的最佳实践
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from typing import List, Dict, Any

# 添加当前目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import (
    ADS_POWER_CONFIG, TWITTER_TARGETS, FILTER_CONFIG, 
    OUTPUT_CONFIG, BROWSER_CONFIG, LOG_CONFIG
)
from ads_browser_launcher import AdsPowerLauncher
from account_manager import AccountManager

class MixedModeDemo:
    def __init__(self):
        self.launcher = AdsPowerLauncher()
        # 简化演示，不使用账户管理器
        # self.account_manager = AccountManager()
        self.logger = self.setup_logging()
        
    def setup_logging(self) -> logging.Logger:
        """设置日志配置"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def display_config_summary(self):
        """显示混合模式配置摘要"""
        print("\n🎯 Twitter 混合模式采集配置")
        print("=" * 50)
        
        # 显示博主列表
        accounts = TWITTER_TARGETS['accounts']
        print(f"\n👥 目标博主列表 ({len(accounts)} 个):")
        for i, account in enumerate(accounts[:10], 1):  # 显示前10个
            print(f"  {i:2d}. @{account}")
        if len(accounts) > 10:
            print(f"     ... 还有 {len(accounts) - 10} 个博主")
        
        # 显示关键词列表
        keywords = TWITTER_TARGETS['keywords']
        print(f"\n🔍 搜索关键词 ({len(keywords)} 个):")
        for i, keyword in enumerate(keywords[:10], 1):  # 显示前10个
            print(f"  {i:2d}. {keyword}")
        if len(keywords) > 10:
            print(f"     ... 还有 {len(keywords) - 10} 个关键词")
        
        # 显示筛选条件
        print(f"\n⚙️ 筛选条件:")
        print(f"  📊 最小点赞数: {FILTER_CONFIG['min_likes']}")
        print(f"  💬 最小评论数: {FILTER_CONFIG['min_comments']}")
        print(f"  🔄 最小转发数: {FILTER_CONFIG['min_retweets']}")
        print(f"  📝 内容长度: {FILTER_CONFIG['min_content_length']}-{FILTER_CONFIG['max_content_length']} 字符")
        print(f"  ⏰ 时间范围: 最近 {FILTER_CONFIG['max_age_hours']} 小时")
        print(f"  📈 每目标最大采集: {FILTER_CONFIG['max_tweets_per_target']} 条")
        print(f"  🎯 总最大采集: {FILTER_CONFIG['max_total_tweets']} 条")
        
        # 显示关键词过滤器
        keywords_filter = FILTER_CONFIG['keywords_filter']
        print(f"\n🎯 内容关键词过滤器 ({len(keywords_filter)} 个):")
        categories = {
            'AI相关': ['AI', '人工智能', 'ChatGPT', 'GPT', 'Claude', 'Midjourney', '机器学习', '深度学习', '大模型', 'LLM'],
            '创业商业': ['副业', '创业', '商业', '产品', '增长', '营销', '思维', '认知', '方法论', '模式'],
            '技术开发': ['编程', '开发', '技术', '工具', '自动化', '效率', '生产力', 'productivity'],
            '学习成长': ['学习', '成长', '思考', '洞察', '经验', '方法', '技巧', '策略', '框架']
        }
        
        for category, words in categories.items():
            matching_words = [w for w in words if w in keywords_filter]
            if matching_words:
                print(f"  📂 {category}: {', '.join(matching_words[:5])}{'...' if len(matching_words) > 5 else ''}")
    
    def display_strategy_explanation(self):
        """显示混合模式策略说明"""
        print("\n💡 混合模式策略说明")
        print("=" * 50)
        
        print("\n🎯 采集策略:")
        print("  1. 📱 博主采集: 从精选KOL获取高质量内容")
        print("     • 科技创新领域: Elon Musk, OpenAI, Sam Altman 等")
        print("     • AI技术专家: 吴恩达, Yann LeCun, Andrej Karpathy 等")
        print("     • 商业创业: Naval, Paul Graham, Marc Andreessen 等")
        print("     • 中文博主: 宝玉, 歸藏, 倪爽 等")
        
        print("\n  2. 🔍 关键词搜索: 追踪热点话题和趋势")
        print("     • AI工具应用: ChatGPT应用, AI工具, Midjourney")
        print("     • 创业商业: 副业赚钱, 商业模式, 产品思维")
        print("     • 技术趋势: 编程技巧, 开发工具, 自动化")
        print("     • 个人成长: 学习方法, 时间管理, 认知升级")
        
        print("\n✨ 优势特点:")
        print("  • 🎯 内容质量: KOL博主保证内容权威性")
        print("  • 📈 热点追踪: 关键词搜索捕获最新趋势")
        print("  • 🔍 智能筛选: 多维度过滤确保内容价值")
        print("  • ⚖️ 平衡覆盖: 既有深度又有广度")
        
        print("\n🚀 预期效果:")
        print("  • 每日可获得 100-200 条高质量推文")
        print("  • 涵盖 AI、创业、技术、成长 等多个领域")
        print("  • 内容新鲜度: 72小时内的最新内容")
        print("  • 互动质量: 平均点赞数 50+, 评论数 10+")
    
    async def test_browser_connection(self):
        """测试浏览器连接"""
        print("\n🔧 测试浏览器连接")
        print("=" * 50)
        
        try:
            # 获取系统健康报告
            print("📊 检查系统状态...")
            health_report = self.launcher.get_health_report()
            
            resources = health_report['system_resources']
            print(f"  💻 CPU: {resources['cpu_percent']:.1f}% {'✅' if resources['cpu_healthy'] else '⚠️'}")
            print(f"  🧠 内存: {resources['memory_percent']:.1f}% {'✅' if resources['memory_healthy'] else '⚠️'}")
            print(f"  💾 可用内存: {resources['memory_available_gb']:.1f}GB")
            
            # 检查AdsPower状态
            processes = health_report['adspower_processes']
            print(f"  🔧 AdsPower: {'✅ 运行中' if processes['adspower_running'] else '❌ 未运行'}")
            
            if not processes['adspower_running']:
                print("\n⚠️ AdsPower 未运行，请先启动 AdsPower 客户端")
                return False
            
            # 测试浏览器启动
            print("\n🚀 测试浏览器启动...")
            user_id = ADS_POWER_CONFIG['user_id']
            print(f"  📱 使用用户ID: {user_id}")
            
            browser_info = self.launcher.start_browser(user_id)
            
            if browser_info:
                print("  ✅ 浏览器启动成功")
                debug_port = self.launcher.get_debug_port()
                print(f"  📡 调试端口: {debug_port}")
                
                # 测试浏览器状态
                print("\n⏳ 测试浏览器稳定性（3秒）...")
                await asyncio.sleep(3)
                
                try:
                    status = self.launcher.get_browser_status(user_id)
                    if status.get('code') == 0:
                        print("  ✅ 浏览器运行稳定")
                    else:
                        print("  ⚠️ 浏览器状态异常")
                except:
                    print("  ⚠️ 无法获取浏览器状态")
                
                # 停止浏览器
                print("\n🛑 停止浏览器...")
                if self.launcher.stop_browser(user_id):
                    print("  ✅ 浏览器停止成功")
                else:
                    print("  ❌ 浏览器停止失败")
                
                return True
            else:
                print("  ❌ 浏览器启动失败")
                return False
                
        except Exception as e:
            print(f"  ❌ 连接测试失败: {e}")
            return False
    
    def display_usage_guide(self):
        """显示使用指南"""
        print("\n📖 使用指南")
        print("=" * 50)
        
        print("\n🚀 快速启动:")
        print("  1. 确保 AdsPower 客户端正在运行")
        print("  2. 运行采集命令:")
        print("     python3 run.py                    # 基础版本")
        print("     python3 run_enhanced.py           # 增强版本（推荐）")
        print("     python3 demo_enhanced.py scraping # 演示模式")
        
        print("\n⚙️ 配置调整:")
        print("  • 修改博主列表: 编辑 config.py 中的 TWITTER_TARGETS['accounts']")
        print("  • 调整关键词: 编辑 config.py 中的 TWITTER_TARGETS['keywords']")
        print("  • 筛选条件: 修改 FILTER_CONFIG 中的各项参数")
        print("  • 采集数量: 调整 max_tweets_per_target 和 max_total_tweets")
        
        print("\n📊 输出文件:")
        print(f"  • Excel文件: {OUTPUT_CONFIG['data_dir']}/twitter_daily_{{date}}.xlsx")
        print(f"  • 日志文件: {LOG_CONFIG['filename']}")
        print("  • 健康报告: health_report.json")
        
        print("\n🔧 高级功能:")
        print("  • AI内容分析: 自动评估推文质量和情感倾向")
        print("  • 多账户管理: 自动轮换AdsPower账户")
        print("  • 云端同步: 支持Google Sheets和飞书文档")
        print("  • 定时任务: 支持cron定时采集")
        print("  • 系统监控: 实时监控资源使用情况")
        
        print("\n💡 最佳实践:")
        print("  1. 🕘 建议每日定时采集，避免信息过载")
        print("  2. 📊 定期查看健康报告，优化系统性能")
        print("  3. 🎯 根据需求调整筛选条件，平衡质量与数量")
        print("  4. 🔄 定期更新博主列表和关键词，保持内容新鲜")
        print("  5. 💾 启用云端同步，便于多设备访问")
    
    async def run_demo(self):
        """运行混合模式演示"""
        print("🎯 Twitter 混合模式采集系统")
        print("=" * 60)
        print("\n这是一个结合博主采集和关键词搜索的智能采集方案")
        print("旨在为您提供高质量、多维度的Twitter内容")
        
        try:
            # 1. 显示配置摘要
            self.display_config_summary()
            
            # 2. 显示策略说明
            self.display_strategy_explanation()
            
            # 3. 测试浏览器连接
            connection_success = await self.test_browser_connection()
            
            # 4. 显示使用指南
            self.display_usage_guide()
            
            # 5. 总结
            print("\n🎉 混合模式配置完成！")
            print("\n📋 系统状态:")
            print(f"  🔧 AdsPower配置: {'✅ 已配置' if ADS_POWER_CONFIG['user_id'] else '❌ 需要配置'}")
            print(f"  🌐 浏览器连接: {'✅ 正常' if connection_success else '⚠️ 需要检查'}")
            print(f"  👥 博主数量: {len(TWITTER_TARGETS['accounts'])} 个")
            print(f"  🔍 关键词数量: {len(TWITTER_TARGETS['keywords'])} 个")
            print(f"  🎯 预期采集量: {FILTER_CONFIG['max_total_tweets']} 条/次")
            
            if connection_success:
                print("\n✨ 系统已就绪，可以开始采集！")
                print("\n🚀 推荐命令:")
                print("   python3 run_enhanced.py    # 启动增强版采集")
            else:
                print("\n⚠️ 请检查AdsPower状态后重试")
                
        except KeyboardInterrupt:
            print("\n⏹️ 演示被用户中断")
        except Exception as e:
            print(f"\n❌ 演示过程中发生错误: {e}")
            self.logger.exception("演示异常")

def main():
    """主函数"""
    demo = MixedModeDemo()
    asyncio.run(demo.run_demo())

if __name__ == "__main__":
    main()