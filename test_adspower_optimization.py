#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AdsPower 优化功能测试脚本
演示新增的系统监控、进程管理和自动修复功能
"""

import logging
import time
import json
from ads_browser_launcher import AdsPowerLauncher

def test_health_monitoring():
    """测试健康监控功能"""
    print("\n=== 🔍 健康监控测试 ===")
    
    launcher = AdsPowerLauncher()
    
    # 获取健康报告
    health_report = launcher.get_health_report()
    
    print("📊 系统资源状态:")
    resources = health_report['system_resources']
    print(f"  CPU: {resources['cpu_percent']:.1f}% {'✅' if resources['cpu_healthy'] else '⚠️'}")
    print(f"  内存: {resources['memory_percent']:.1f}% {'✅' if resources['memory_healthy'] else '⚠️'}")
    print(f"  磁盘: {resources['disk_free_gb']:.1f}GB {'✅' if resources['disk_healthy'] else '⚠️'}")
    
    print("\n🔧 AdsPower进程状态:")
    processes = health_report['adspower_processes']
    print(f"  AdsPower运行: {'✅' if processes['adspower_running'] else '❌'}")
    print(f"  总进程数: {processes['total_processes']}")
    print(f"  RPA进程数: {len(processes['rpa_processes'])}")
    print(f"  异常进程数: {len(processes['high_cpu_processes'])}")
    
    print("\n💡 系统建议:")
    for i, recommendation in enumerate(health_report['recommendations'], 1):
        print(f"  {i}. {recommendation}")
    
    return health_report

def test_process_management():
    """测试进程管理功能"""
    print("\n=== ⚙️ 进程管理测试 ===")
    
    launcher = AdsPowerLauncher()
    
    # 检查AdsPower进程
    print("🔍 检查AdsPower进程...")
    process_info = launcher.check_adspower_processes()
    
    if process_info['adspower_running']:
        print("✅ AdsPower正在运行")
        
        if process_info['rpa_processes']:
            print(f"📋 发现 {len(process_info['rpa_processes'])} 个RPA进程:")
            for rpa in process_info['rpa_processes']:
                status = "⚠️" if rpa['cpu_percent'] > 50 else "✅"
                print(f"  {status} PID {rpa['pid']}: {rpa['name']} (CPU: {rpa['cpu_percent']:.1f}%)")
        
        # 测试异常进程终止
        if process_info['high_cpu_processes']:
            print(f"\n🚨 发现 {len(process_info['high_cpu_processes'])} 个高CPU进程")
            print("🔧 测试异常进程终止功能...")
            if launcher.terminate_high_cpu_rpa_processes():
                print("✅ 异常进程终止成功")
            else:
                print("❌ 异常进程终止失败")
    else:
        print("❌ AdsPower未运行")
        print("🔄 测试AdsPower重启功能...")
        if launcher.restart_adspower_if_needed():
            print("✅ AdsPower重启成功")
        else:
            print("❌ AdsPower重启失败")

def test_system_optimization():
    """测试系统优化功能"""
    print("\n=== 🚀 系统优化测试 ===")
    
    launcher = AdsPowerLauncher()
    
    # 获取优化前状态
    print("📊 优化前系统状态:")
    before_report = launcher.get_health_report()
    before_resources = before_report['system_resources']
    print(f"  CPU: {before_resources['cpu_percent']:.1f}%")
    print(f"  内存: {before_resources['memory_percent']:.1f}%")
    
    # 执行系统优化
    print("\n🔧 执行系统优化...")
    optimization_success = launcher.auto_optimize_system()
    
    if optimization_success:
        print("✅ 系统优化完成")
        
        # 获取优化后状态
        print("\n📊 优化后系统状态:")
        after_report = launcher.get_health_report()
        after_resources = after_report['system_resources']
        print(f"  CPU: {after_resources['cpu_percent']:.1f}%")
        print(f"  内存: {after_resources['memory_percent']:.1f}%")
        
        # 计算改善情况
        cpu_improvement = before_resources['cpu_percent'] - after_resources['cpu_percent']
        memory_improvement = before_resources['memory_percent'] - after_resources['memory_percent']
        
        print("\n📈 优化效果:")
        print(f"  CPU改善: {cpu_improvement:+.1f}%")
        print(f"  内存改善: {memory_improvement:+.1f}%")
    else:
        print("❌ 系统优化失败")

def test_safe_browser_launch():
    """测试安全浏览器启动"""
    print("\n=== 🛡️ 安全启动测试 ===")
    
    launcher = AdsPowerLauncher()
    
    try:
        print("🚀 尝试安全启动浏览器...")
        browser_info = launcher.start_browser()
        
        if browser_info:
            print("✅ 浏览器启动成功")
            print(f"📡 调试端口: {launcher.get_debug_port()}")
            
            # 等待几秒钟
            print("⏳ 等待5秒钟测试稳定性...")
            time.sleep(5)
            
            # 检查浏览器状态
            status = launcher.get_browser_status()
            if status.get('code') == 0:
                print("✅ 浏览器运行稳定")
            else:
                print("⚠️ 浏览器状态异常")
            
            # 停止浏览器
            print("🛑 停止浏览器...")
            if launcher.stop_browser():
                print("✅ 浏览器停止成功")
            else:
                print("❌ 浏览器停止失败")
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        
        # 尝试自动修复
        print("🔄 尝试自动修复...")
        if launcher.auto_optimize_system():
            print("✅ 自动修复成功，可以重试启动")
        else:
            print("❌ 自动修复失败")

def test_monitoring_mode():
    """测试监控模式"""
    print("\n=== 👁️ 监控模式测试 ===")
    
    launcher = AdsPowerLauncher()
    
    try:
        print("🚀 启动浏览器并开启监控模式...")
        browser_info = launcher.start_browser_with_monitoring(monitor_duration=20)
        
        if browser_info:
            print("✅ 监控模式测试完成")
            
            # 停止浏览器
            launcher.stop_browser()
        
    except Exception as e:
        print(f"❌ 监控模式测试失败: {e}")

def main():
    """主测试函数"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🔧 AdsPower 优化功能测试")
    print("=" * 50)
    
    try:
        # 1. 健康监控测试
        health_report = test_health_monitoring()
        
        # 2. 进程管理测试
        test_process_management()
        
        # 3. 系统优化测试
        test_system_optimization()
        
        # 4. 安全启动测试
        test_safe_browser_launch()
        
        # 5. 监控模式测试（可选）
        if input("\n是否测试监控模式？(y/n): ").lower() == 'y':
            test_monitoring_mode()
        
        print("\n🎉 所有测试完成！")
        
        # 保存健康报告
        with open('health_report.json', 'w', encoding='utf-8') as f:
            json.dump(health_report, f, indent=2, ensure_ascii=False)
        print("📄 健康报告已保存到 health_report.json")
        
    except KeyboardInterrupt:
        print("\n⏹️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        logging.exception("测试异常")

if __name__ == "__main__":
    main()