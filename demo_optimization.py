#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AdsPower 优化功能演示
展示程序内部的优化和监控功能
"""

import logging
import time
from ads_browser_launcher import AdsPowerLauncher

def demo_health_monitoring():
    """演示健康监控功能"""
    print("\n=== 🔍 系统健康监控演示 ===")
    
    launcher = AdsPowerLauncher()
    
    # 获取健康报告
    print("📊 正在获取系统健康报告...")
    health_report = launcher.get_health_report()
    
    # 显示系统资源
    resources = health_report['system_resources']
    print(f"\n💻 系统资源状态:")
    print(f"  🔥 CPU使用率: {resources['cpu_percent']:.1f}% {'✅' if resources['cpu_healthy'] else '⚠️'}")
    print(f"  🧠 内存使用率: {resources['memory_percent']:.1f}% {'✅' if resources['memory_healthy'] else '⚠️'}")
    print(f"  💾 可用内存: {resources['memory_available_gb']:.1f}GB")
    print(f"  💿 磁盘空间: {resources['disk_free_gb']:.1f}GB {'✅' if resources['disk_healthy'] else '⚠️'}")
    
    # 显示AdsPower进程状态
    processes = health_report['adspower_processes']
    print(f"\n🔧 AdsPower进程状态:")
    print(f"  📱 AdsPower运行: {'✅ 正常' if processes['adspower_running'] else '❌ 未运行'}")
    print(f"  📊 总进程数: {processes['total_processes']}")
    print(f"  🤖 RPA进程数: {len(processes['rpa_processes'])}")
    
    if processes['rpa_processes']:
        print(f"  📋 RPA进程详情:")
        for rpa in processes['rpa_processes']:
            status = "⚠️ 高负载" if rpa['cpu_percent'] > 50 else "✅ 正常"
            print(f"    {status} PID {rpa['pid']}: CPU {rpa['cpu_percent']:.1f}%, 内存 {rpa['memory_percent']:.1f}%")
    
    if processes['high_cpu_processes']:
        print(f"  🚨 发现 {len(processes['high_cpu_processes'])} 个高CPU进程")
    
    # 显示建议
    print(f"\n💡 系统建议:")
    for i, recommendation in enumerate(health_report['recommendations'], 1):
        print(f"  {i}. {recommendation}")
    
    return health_report

def demo_process_management():
    """演示进程管理功能"""
    print("\n=== ⚙️ 进程管理演示 ===")
    
    launcher = AdsPowerLauncher()
    
    # 检查AdsPower进程
    print("🔍 检查AdsPower进程状态...")
    process_info = launcher.check_adspower_processes()
    
    if process_info['adspower_running']:
        print("✅ AdsPower正在运行")
        
        # 检查是否有异常进程
        if process_info['high_cpu_processes']:
            print(f"🚨 发现 {len(process_info['high_cpu_processes'])} 个高CPU使用率进程")
            print("🔧 正在终止异常进程...")
            
            if launcher.terminate_high_cpu_rpa_processes():
                print("✅ 异常进程已成功终止")
            else:
                print("❌ 终止异常进程失败")
        else:
            print("✅ 所有进程运行正常")
    else:
        print("❌ AdsPower未运行")
        print("🔄 尝试启动AdsPower...")
        
        if launcher.restart_adspower_if_needed():
            print("✅ AdsPower启动成功")
        else:
            print("❌ AdsPower启动失败")

def demo_system_optimization():
    """演示系统优化功能"""
    print("\n=== 🚀 系统优化演示 ===")
    
    launcher = AdsPowerLauncher()
    
    # 获取优化前状态
    print("📊 优化前系统状态:")
    before_report = launcher.get_health_report()
    before_resources = before_report['system_resources']
    print(f"  CPU: {before_resources['cpu_percent']:.1f}%")
    print(f"  内存: {before_resources['memory_percent']:.1f}%")
    print(f"  可用内存: {before_resources['memory_available_gb']:.1f}GB")
    
    # 执行系统优化
    print("\n🔧 正在执行系统优化...")
    print("  🧹 清理异常RPA进程")
    print("  🗑️ 清理系统缓存")
    print("  📁 清理AdsPower缓存")
    print("  ⏳ 等待系统稳定")
    
    optimization_success = launcher.auto_optimize_system()
    
    if optimization_success:
        print("✅ 系统优化完成")
        
        # 获取优化后状态
        print("\n📊 优化后系统状态:")
        after_report = launcher.get_health_report()
        after_resources = after_report['system_resources']
        print(f"  CPU: {after_resources['cpu_percent']:.1f}%")
        print(f"  内存: {after_resources['memory_percent']:.1f}%")
        print(f"  可用内存: {after_resources['memory_available_gb']:.1f}GB")
        
        # 计算改善情况
        cpu_improvement = before_resources['cpu_percent'] - after_resources['cpu_percent']
        memory_improvement = before_resources['memory_percent'] - after_resources['memory_percent']
        memory_freed = after_resources['memory_available_gb'] - before_resources['memory_available_gb']
        
        print("\n📈 优化效果:")
        print(f"  🔥 CPU改善: {cpu_improvement:+.1f}%")
        print(f"  🧠 内存改善: {memory_improvement:+.1f}%")
        print(f"  💾 释放内存: {memory_freed:+.1f}GB")
        
        if cpu_improvement > 0 or memory_improvement > 0:
            print("🎉 优化效果显著！")
        else:
            print("ℹ️ 系统本身状态良好，优化效果有限")
    else:
        print("❌ 系统优化失败")

def demo_safe_browser_launch():
    """演示安全浏览器启动"""
    print("\n=== 🛡️ 安全启动演示 ===")
    
    launcher = AdsPowerLauncher()
    
    # 使用已知的用户ID
    user_id = "k11p9ypc"
    
    try:
        print(f"🚀 尝试安全启动浏览器 (用户ID: {user_id})...")
        print("  🔍 执行启动前健康检查")
        print("  📊 检查系统资源")
        print("  🔧 检查AdsPower进程")
        print("  ⏳ 等待系统稳定")
        
        browser_info = launcher.start_browser(user_id)
        
        if browser_info:
            print("✅ 浏览器启动成功")
            debug_port = launcher.get_debug_port()
            print(f"📡 调试端口: {debug_port}")
            
            # 等待几秒钟测试稳定性
            print("⏳ 测试浏览器稳定性（5秒）...")
            time.sleep(5)
            
            # 检查浏览器状态
            try:
                status = launcher.get_browser_status(user_id)
                if status.get('code') == 0:
                    print("✅ 浏览器运行稳定")
                else:
                    print("⚠️ 浏览器状态异常")
            except:
                print("⚠️ 无法获取浏览器状态")
            
            # 停止浏览器
            print("🛑 停止浏览器...")
            if launcher.stop_browser(user_id):
                print("✅ 浏览器停止成功")
            else:
                print("❌ 浏览器停止失败")
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        
        # 尝试自动修复
        print("🔄 尝试自动修复...")
        if launcher.auto_optimize_system():
            print("✅ 自动修复成功，建议重试启动")
        else:
            print("❌ 自动修复失败，请检查AdsPower状态")

def main():
    """主演示函数"""
    # 配置日志（减少输出）
    logging.basicConfig(
        level=logging.WARNING,  # 只显示警告和错误
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("🔧 AdsPower 程序内优化功能演示")
    print("=" * 50)
    print("\n这些功能可以解决浏览器窗口自动关闭的问题：")
    print("• 🔍 实时系统资源监控")
    print("• ⚙️ 自动进程管理和修复")
    print("• 🚀 智能系统优化")
    print("• 🛡️ 启动前健康检查")
    print("• 👁️ 持续运行监控")
    
    try:
        # 1. 健康监控演示
        health_report = demo_health_monitoring()
        
        # 2. 进程管理演示
        demo_process_management()
        
        # 3. 系统优化演示
        demo_system_optimization()
        
        # 4. 安全启动演示
        demo_safe_browser_launch()
        
        print("\n🎉 演示完成！")
        print("\n📋 使用建议:")
        print("1. 在启动浏览器前调用 launcher.start_browser() （已包含健康检查）")
        print("2. 定期调用 launcher.get_health_report() 监控系统状态")
        print("3. 出现问题时调用 launcher.auto_optimize_system() 自动修复")
        print("4. 长时间运行时使用 launcher.start_browser_with_monitoring() 持续监控")
        
        # 显示当前系统状态
        current_resources = health_report['system_resources']
        print(f"\n📊 当前系统状态:")
        print(f"  CPU: {current_resources['cpu_percent']:.1f}% {'✅' if current_resources['cpu_healthy'] else '⚠️'}")
        print(f"  内存: {current_resources['memory_percent']:.1f}% {'✅' if current_resources['memory_healthy'] else '⚠️'}")
        print(f"  磁盘: {current_resources['disk_free_gb']:.1f}GB {'✅' if current_resources['disk_healthy'] else '⚠️'}")
        
    except KeyboardInterrupt:
        print("\n⏹️ 演示被用户中断")
    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")
        logging.exception("演示异常")

if __name__ == "__main__":
    main()