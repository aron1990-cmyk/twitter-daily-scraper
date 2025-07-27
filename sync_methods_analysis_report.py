#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书同步方式差异分析报告
详细分析任务完成后自动同步和API手动同步的差异
"""

import json
from datetime import datetime

def analyze_sync_differences():
    """
    分析两种飞书同步方式的关键差异
    """
    print("\n" + "="*80)
    print("🔍 飞书同步方式差异分析报告")
    print("="*80)
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n📋 问题描述:")
    print("   - 任务28完成后的自动同步有问题")
    print("   - 单独用脚本测试的同步没问题")
    print("   - 用户询问是否使用同一段代码")
    
    print("\n🔍 分析结果:")
    print("   ❌ 两种同步方式使用的是不同的代码路径和初始化方式")
    
    print("\n" + "-"*60)
    print("📊 详细差异对比")
    print("-"*60)
    
    # 1. 代码路径差异
    print("\n1️⃣ 代码路径差异:")
    print("   🤖 任务完成后自动同步:")
    print("      - 文件: web_app.py")
    print("      - 方法: _check_auto_sync_feishu()")
    print("      - 触发: 任务完成后自动调用")
    print("      - 位置: 第3050-3120行左右")
    
    print("\n   🌐 API手动同步:")
    print("      - 文件: web_app.py")
    print("      - 路由: /api/data/sync_feishu/<int:task_id>")
    print("      - 触发: 手动调用API")
    print("      - 位置: 第2192-2280行左右")
    
    # 2. 初始化方式差异
    print("\n2️⃣ CloudSyncManager初始化方式差异:")
    print("   🤖 任务完成后自动同步:")
    print("      - 步骤1: 创建基础配置 (只包含app_id, app_secret, base_url)")
    print("      - 步骤2: CloudSyncManager(sync_config)")
    print("      - 步骤3: 调用 sync_manager.setup_feishu(app_id, app_secret)")
    print("      - 特点: 分两步初始化，先创建对象再设置配置")
    
    print("\n   🌐 API手动同步:")
    print("      - 步骤1: 创建完整配置 (包含所有字段)")
    print("      - 步骤2: CloudSyncManager(sync_config)")
    print("      - 步骤3: 无需额外设置")
    print("      - 特点: 一步初始化，配置完整传入")
    
    # 3. 配置内容差异
    print("\n3️⃣ 配置内容差异:")
    print("   🤖 任务完成后自动同步配置:")
    auto_config = {
        'feishu': {
            'enabled': True,
            'app_id': 'xxx',
            'app_secret': 'xxx',
            'base_url': 'https://open.feishu.cn/open-apis'
        }
    }
    print(f"      {json.dumps(auto_config, indent=6, ensure_ascii=False)}")
    
    print("\n   🌐 API手动同步配置:")
    api_config = {
        'feishu': {
            'enabled': True,
            'app_id': 'xxx',
            'app_secret': 'xxx',
            'spreadsheet_token': 'xxx',
            'table_id': 'xxx',
            'base_url': 'https://open.feishu.cn/open-apis'
        }
    }
    print(f"      {json.dumps(api_config, indent=6, ensure_ascii=False)}")
    
    # 4. setup_feishu方法的影响
    print("\n4️⃣ setup_feishu()方法的关键影响:")
    print("   🔧 setup_feishu()方法的作用:")
    print("      - 重新设置 self.feishu_config")
    print("      - 只保留 app_id, app_secret, base_url")
    print("      - 丢失 spreadsheet_token 和 table_id")
    
    print("\n   ⚠️ 潜在问题:")
    print("      - 自动同步调用setup_feishu()后，配置被覆盖")
    print("      - 缺少spreadsheet_token和table_id可能导致同步失败")
    print("      - API同步不调用setup_feishu()，保持完整配置")
    
    # 5. 数据处理差异
    print("\n5️⃣ 数据处理方式:")
    print("   📊 两种方式的数据处理基本一致:")
    print("      - 都使用相同的字段映射")
    print("      - 都调用CloudSyncManager.sync_to_feishu()")
    print("      - 都更新数据库中的同步状态")
    
    # 6. 问题根源
    print("\n" + "-"*60)
    print("🎯 问题根源分析")
    print("-"*60)
    
    print("\n❌ 核心问题:")
    print("   1. setup_feishu()方法会覆盖原有配置")
    print("   2. 覆盖后的配置缺少关键字段")
    print("   3. 导致后续同步操作失败")
    
    print("\n🔍 具体分析:")
    print("   - 自动同步: 初始配置 → setup_feishu() → 配置被覆盖 → 同步失败")
    print("   - API同步: 完整配置 → 无setup_feishu() → 配置完整 → 同步成功")
    
    # 7. 解决方案
    print("\n" + "-"*60)
    print("💡 解决方案建议")
    print("-"*60)
    
    print("\n🔧 方案1: 修改setup_feishu()方法")
    print("   - 保留原有配置中的spreadsheet_token和table_id")
    print("   - 只更新app_id和app_secret")
    print("   - 确保配置完整性")
    
    print("\n🔧 方案2: 统一初始化方式")
    print("   - 自动同步也使用完整配置初始化")
    print("   - 移除setup_feishu()调用")
    print("   - 保持两种方式的一致性")
    
    print("\n🔧 方案3: 改进setup_feishu()逻辑")
    print("   - 检查是否已有完整配置")
    print("   - 如果有，则不覆盖")
    print("   - 如果没有，则设置基础配置")
    
    print("\n" + "="*80)
    print("📝 总结")
    print("="*80)
    
    print("\n✅ 确认:")
    print("   - 两种同步方式确实使用了不同的代码路径")
    print("   - 关键差异在于CloudSyncManager的初始化方式")
    print("   - setup_feishu()方法是导致问题的根本原因")
    
    print("\n🎯 建议:")
    print("   - 优先采用方案2，统一初始化方式")
    print("   - 确保两种同步方式使用相同的配置和逻辑")
    print("   - 测试修改后的同步功能")
    
    print("\n" + "="*80)
    print("🏁 分析完成")
    print("="*80)

if __name__ == '__main__':
    analyze_sync_differences()