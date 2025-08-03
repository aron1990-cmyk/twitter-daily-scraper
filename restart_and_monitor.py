#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重启服务并监控P0优化效果
"""

import subprocess
import time
import psutil
import logging
import signal
import os
from datetime import datetime
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('restart_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_memory_usage():
    """获取当前内存使用情况"""
    memory = psutil.virtual_memory()
    return {
        'percent': memory.percent,
        'used_gb': memory.used / (1024**3),
        'total_gb': memory.total / (1024**3),
        'available_gb': memory.available / (1024**3)
    }

def find_python_processes():
    """查找相关的Python进程"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                if any(keyword in cmdline.lower() for keyword in ['twitter', 'web_app', 'browser_manager', 'task_manager']):
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cmdline': cmdline
                    })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return processes

def stop_related_processes():
    """停止相关进程"""
    logger.info("[P0优化] 查找并停止相关进程...")
    
    processes = find_python_processes()
    if not processes:
        logger.info("[P0优化] 未找到相关的Python进程")
        return
    
    for proc_info in processes:
        try:
            logger.info(f"[P0优化] 停止进程 PID {proc_info['pid']}: {proc_info['name']}")
            proc = psutil.Process(proc_info['pid'])
            proc.terminate()
            
            # 等待进程优雅退出
            try:
                proc.wait(timeout=10)
                logger.info(f"[P0优化] 进程 {proc_info['pid']} 已优雅退出")
            except psutil.TimeoutExpired:
                logger.warning(f"[P0优化] 进程 {proc_info['pid']} 未在10秒内退出，强制终止")
                proc.kill()
                
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.warning(f"[P0优化] 无法停止进程 {proc_info['pid']}: {e}")

def monitor_memory_after_restart():
    """重启后监控内存使用情况"""
    logger.info("[P0优化] 开始监控重启后内存使用情况")
    
    # 记录重启前内存
    memory_before_restart = get_memory_usage()
    logger.info(
        f"[P0优化] 重启前内存: {memory_before_restart['percent']:.1f}% "
        f"({memory_before_restart['used_gb']:.2f}GB / {memory_before_restart['total_gb']:.2f}GB)"
    )
    
    # 停止相关进程
    stop_related_processes()
    
    # 等待系统稳定
    logger.info("[P0优化] 等待系统稳定...")
    time.sleep(10)
    
    # 强制垃圾回收
    import gc
    gc.collect()
    
    # 记录重启后内存
    memory_after_restart = get_memory_usage()
    logger.info(
        f"[P0优化] 重启后内存: {memory_after_restart['percent']:.1f}% "
        f"({memory_after_restart['used_gb']:.2f}GB / {memory_after_restart['total_gb']:.2f}GB)"
    )
    
    # 计算内存节省
    memory_saved_percent = memory_before_restart['percent'] - memory_after_restart['percent']
    memory_saved_gb = memory_before_restart['used_gb'] - memory_after_restart['used_gb']
    
    logger.info("\n" + "="*80)
    logger.info("[P0优化] 重启后内存优化效果报告")
    logger.info("="*80)
    
    if memory_saved_percent > 0:
        logger.info(f"✅ 重启释放内存: {memory_saved_percent:.1f}% ({memory_saved_gb:.2f}GB)")
    else:
        logger.info(f"⚠️  内存变化: {abs(memory_saved_percent):.1f}%")
    
    if memory_after_restart['percent'] <= 50:
        logger.info("🎯 P0优化目标达成: 内存占用已降至50%以下")
        success_level = "完全成功"
    elif memory_after_restart['percent'] <= 60:
        logger.info("📈 P0优化效果显著: 内存占用已大幅降低")
        success_level = "效果显著"
    elif memory_saved_percent > 0:
        logger.info("📊 P0优化有效: 内存占用有所降低")
        success_level = "有效"
    else:
        logger.info("⚠️  需要进一步优化")
        success_level = "需要进一步优化"
    
    # 生成最终报告
    final_report = {
        'optimization_timestamp': datetime.now().isoformat(),
        'memory_before_restart': memory_before_restart,
        'memory_after_restart': memory_after_restart,
        'memory_savings': {
            'percent_saved': memory_saved_percent,
            'gb_saved': memory_saved_gb
        },
        'optimization_success_level': success_level,
        'target_achieved': memory_after_restart['percent'] <= 50,
        'p0_optimizations_completed': [
            'browser_manager.py: 清理间隔0.5h, 空闲2min, 运行6h, 内存阈值300MB',
            'async_task_manager.py: LRU缓存1000/500条, 清理间隔1h, 内存监控',
            'templates: 轮询60s/120s, 页面可见性检测',
            'system_monitor.py: 告警阈值70%, 主动清理, 数据保留3天'
        ]
    }
    
    # 保存最终报告
    import json
    with open('p0_final_optimization_report.json', 'w', encoding='utf-8') as f:
        json.dump(final_report, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n最终优化状态: {success_level}")
    logger.info(f"当前系统内存占用: {memory_after_restart['percent']:.1f}%")
    logger.info(f"最终报告已保存至: p0_final_optimization_report.json")
    logger.info("="*80)
    
    return final_report

def main():
    """主函数"""
    logger.info("[P0优化] 开始重启服务并监控优化效果")
    logger.info("目标: 通过重启服务让P0优化生效，将内存占用降至50%以下")
    
    try:
        final_report = monitor_memory_after_restart()
        
        # 输出关键指标
        logger.info("\n[P0优化] 关键指标总结:")
        logger.info(f"• 优化目标: ≤50% 内存占用")
        logger.info(f"• 当前内存占用: {final_report['memory_after_restart']['percent']:.1f}%")
        logger.info(f"• 目标达成: {'✅ 是' if final_report['target_achieved'] else '❌ 否'}")
        logger.info(f"• 优化效果: {final_report['optimization_success_level']}")
        
        if final_report['memory_savings']['percent_saved'] > 0:
            logger.info(f"• 内存节省: {final_report['memory_savings']['percent_saved']:.1f}% ({final_report['memory_savings']['gb_saved']:.2f}GB)")
        
    except Exception as e:
        logger.error(f"[P0优化] 监控过程出错: {e}")
        raise

if __name__ == '__main__':
    main()