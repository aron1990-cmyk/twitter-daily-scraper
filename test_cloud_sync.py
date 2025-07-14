#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云端同步测试脚本
用于验证Google Sheets和飞书API配置是否正确
"""

import asyncio
import sys
import os
from datetime import datetime

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import CLOUD_SYNC_CONFIG
from cloud_sync import CloudSyncManager

def print_banner():
    """打印测试横幅"""
    print("\n" + "="*60)
    print("🧪 云端同步配置测试")
    print("="*60)
    print("📊 测试Google Sheets和飞书API连接")
    print("🔧 验证配置参数和权限设置")
    print("="*60 + "\n")

def create_test_data():
    """创建测试数据"""
    return [
        {
            'username': 'test_user',
            'content': '这是一条测试推文，用于验证云端同步功能。',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'likes': 100,
            'comments': 20,
            'retweets': 50,
            'link': 'https://twitter.com/test_user/status/123456789',
            'tags': ['测试', '同步'],
            'filter_status': 'passed'
        },
        {
            'username': 'another_user',
            'content': '第二条测试推文，包含更多数据字段。',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'likes': 250,
            'comments': 45,
            'retweets': 80,
            'link': 'https://twitter.com/another_user/status/987654321',
            'tags': ['API', '测试', '自动化'],
            'filter_status': 'passed'
        }
    ]

def check_config():
    """检查配置文件"""
    print("📋 检查配置文件...")
    
    # 检查Google Sheets配置
    google_config = CLOUD_SYNC_CONFIG.get('google_sheets', {})
    if google_config.get('enabled', False):
        print("✅ Google Sheets 已启用")
        print(f"   📁 凭证文件: {google_config.get('credentials_file')}")
        print(f"   📊 表格ID: {google_config.get('spreadsheet_id')[:20]}...")
        print(f"   📄 工作表: {google_config.get('worksheet_name')}")
        
        # 检查凭证文件是否存在
        cred_file = google_config.get('credentials_file')
        if cred_file and os.path.exists(cred_file):
            print("   ✅ 凭证文件存在")
        else:
            print("   ❌ 凭证文件不存在")
    else:
        print("⚪ Google Sheets 未启用")
    
    print()
    
    # 检查飞书配置
    feishu_config = CLOUD_SYNC_CONFIG.get('feishu', {})
    if feishu_config.get('enabled', False):
        print("✅ 飞书 已启用")
        print(f"   🔑 应用ID: {feishu_config.get('app_id')[:10]}...")
        print(f"   🔐 应用密钥: {'*' * 10}")
        print(f"   📊 表格Token: {feishu_config.get('spreadsheet_token')[:20]}...")
        if feishu_config.get('sheet_id'):
            print(f"   📄 工作表ID: {feishu_config.get('sheet_id')}")
        else:
            print("   📄 工作表ID: 使用默认（第一个工作表）")
    else:
        print("⚪ 飞书 未启用")
    
    print()

async def test_google_sheets(sync_manager, test_data):
    """测试Google Sheets连接"""
    google_config = CLOUD_SYNC_CONFIG.get('google_sheets', {})
    if not google_config.get('enabled', False):
        print("⚪ 跳过Google Sheets测试（未启用）")
        return False
    
    print("🧪 测试Google Sheets连接...")
    
    try:
        # 设置Google Sheets
        success = sync_manager.setup_google_sheets(
            google_config.get('credentials_file')
        )
        
        if not success:
            print("❌ Google Sheets设置失败")
            return False
        
        print("✅ Google Sheets连接成功")
        
        # 测试数据同步
        print("📤 测试数据同步...")
        sync_success = sync_manager.sync_to_google_sheets(
            test_data,
            google_config.get('spreadsheet_id'),
            google_config.get('worksheet_name')
        )
        
        if sync_success:
            print("✅ Google Sheets数据同步成功")
            print(f"📊 已同步 {len(test_data)} 条测试数据")
            return True
        else:
            print("❌ Google Sheets数据同步失败")
            return False
            
    except Exception as e:
        print(f"❌ Google Sheets测试异常: {e}")
        return False

async def test_feishu(sync_manager, test_data):
    """测试飞书连接"""
    feishu_config = CLOUD_SYNC_CONFIG.get('feishu', {})
    if not feishu_config.get('enabled', False):
        print("⚪ 跳过飞书测试（未启用）")
        return False
    
    print("🧪 测试飞书连接...")
    
    try:
        # 设置飞书
        success = sync_manager.setup_feishu(
            feishu_config.get('app_id'),
            feishu_config.get('app_secret')
        )
        
        if not success:
            print("❌ 飞书设置失败")
            return False
        
        print("✅ 飞书连接成功")
        
        # 测试获取访问令牌
        print("🔑 测试访问令牌获取...")
        token = sync_manager.get_feishu_access_token()
        
        if not token:
            print("❌ 无法获取飞书访问令牌")
            return False
        
        print("✅ 飞书访问令牌获取成功")
        
        # 测试数据同步
        print("📤 测试数据同步...")
        sync_success = sync_manager.sync_to_feishu_sheet(
            test_data,
            feishu_config.get('spreadsheet_token'),
            feishu_config.get('sheet_id')
        )
        
        if sync_success:
            print("✅ 飞书数据同步成功")
            print(f"📊 已同步 {len(test_data)} 条测试数据")
            return True
        else:
            print("❌ 飞书数据同步失败")
            return False
            
    except Exception as e:
        print(f"❌ 飞书测试异常: {e}")
        return False

async def main():
    """主测试函数"""
    print_banner()
    
    # 检查配置
    check_config()
    
    # 检查是否有启用的平台
    enabled_platforms = []
    if CLOUD_SYNC_CONFIG.get('google_sheets', {}).get('enabled', False):
        enabled_platforms.append('Google Sheets')
    if CLOUD_SYNC_CONFIG.get('feishu', {}).get('enabled', False):
        enabled_platforms.append('飞书')
    
    if not enabled_platforms:
        print("⚠️  没有启用任何云端同步平台")
        print("💡 请在config.py中启用至少一个平台进行测试")
        return
    
    print(f"🎯 将测试以下平台: {', '.join(enabled_platforms)}")
    print()
    
    # 创建测试数据
    test_data = create_test_data()
    print(f"📝 创建了 {len(test_data)} 条测试数据")
    print()
    
    # 创建同步管理器
    sync_manager = CloudSyncManager(CLOUD_SYNC_CONFIG)
    
    # 测试结果
    results = {}
    
    # 测试Google Sheets
    if 'Google Sheets' in enabled_platforms:
        results['google_sheets'] = await test_google_sheets(sync_manager, test_data)
        print()
    
    # 测试飞书
    if '飞书' in enabled_platforms:
        results['feishu'] = await test_feishu(sync_manager, test_data)
        print()
    
    # 显示测试结果
    print("="*60)
    print("📊 测试结果汇总")
    print("="*60)
    
    all_success = True
    for platform, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        print(f"   {platform}: {status}")
        if not success:
            all_success = False
    
    print()
    if all_success and results:
        print("🎉 所有测试通过！云端同步配置正确。")
        print("💡 现在可以运行主程序进行实际数据同步。")
    elif results:
        print("⚠️  部分测试失败，请检查配置和网络连接。")
        print("📖 参考 CLOUD_SYNC_SETUP.md 获取详细设置指南。")
    else:
        print("ℹ️  没有进行任何测试，请启用至少一个平台。")
    
    print("="*60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()