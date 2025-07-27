#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试飞书同步修复
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cloud_sync import CloudSyncManager
from datetime import datetime
import json

def test_feishu_sync():
    """测试飞书同步功能"""
    print("🧪 开始测试飞书同步功能")
    
    # 模拟从数据库获取的数据格式（修复后的格式）
    test_data = [
        {
            '推文原文内容': '这是一条测试推文内容，用于验证飞书同步功能是否正常工作。',
            '发布时间': int(datetime.now().timestamp()),  # Unix时间戳（秒级）
            '作者（账号）': 'test_user',
            '推文链接': 'https://twitter.com/test_user/status/123456789',
            '话题标签（Hashtag）': '#测试, #飞书同步',
            '类型标签': '测试类型',
            '评论': 10,
            '点赞': 100,
            '转发': 50,
            '创建时间': int(datetime.now().timestamp())  # Unix时间戳（秒级）
        },
        {
            '推文原文内容': '第二条测试推文，验证批量同步功能。',
            '发布时间': int(datetime.now().timestamp()),
            '作者（账号）': 'test_user2',
            '推文链接': 'https://twitter.com/test_user2/status/987654321',
            '话题标签（Hashtag）': '#批量测试',
            '类型标签': '功能测试',
            '评论': 5,
            '点赞': 25,
            '转发': 12,
            '创建时间': int(datetime.now().timestamp())
        }
    ]
    
    print(f"📋 测试数据准备完成，共 {len(test_data)} 条记录")
    print(f"📋 数据字段: {list(test_data[0].keys())}")
    
    # 飞书配置（需要用户提供真实配置）
    feishu_config = {
        'feishu': {
            'enabled': True,
            'app_id': 'your_app_id',  # 需要替换为真实的app_id
            'app_secret': 'your_app_secret',  # 需要替换为真实的app_secret
            'spreadsheet_token': 'your_spreadsheet_token',  # 需要替换为真实的token
            'table_id': 'your_table_id',  # 需要替换为真实的table_id
            'base_url': 'https://open.feishu.cn/open-apis'
        }
    }
    
    print("⚠️ 注意：请在运行此测试前，在代码中填入真实的飞书配置信息")
    print("📝 需要配置的字段：")
    print("   - app_id: 飞书应用ID")
    print("   - app_secret: 飞书应用密钥")
    print("   - spreadsheet_token: 飞书多维表格Token")
    print("   - table_id: 飞书表格ID")
    
    # 创建同步管理器
    sync_manager = CloudSyncManager(feishu_config)
    
    # 测试飞书配置
    print("\n🔧 测试飞书配置...")
    if not sync_manager.setup_feishu(
        feishu_config['feishu']['app_id'],
        feishu_config['feishu']['app_secret']
    ):
        print("❌ 飞书配置设置失败")
        return False
    
    # 测试获取访问令牌
    print("\n🔑 测试获取飞书访问令牌...")
    access_token = sync_manager.get_feishu_access_token()
    if not access_token:
        print("❌ 获取飞书访问令牌失败")
        print("💡 请检查：")
        print("   1. app_id 和 app_secret 是否正确")
        print("   2. 网络连接是否正常")
        print("   3. 飞书应用是否已启用")
        return False
    
    print(f"✅ 成功获取访问令牌: {access_token[:10]}...")
    
    # 测试同步数据
    print("\n📤 测试同步数据到飞书...")
    success = sync_manager.sync_to_feishu(
        test_data,
        feishu_config['feishu']['spreadsheet_token'],
        feishu_config['feishu']['table_id']
    )
    
    if success:
        print("✅ 飞书同步测试成功！")
        print("📊 数据已成功同步到飞书多维表格")
        return True
    else:
        print("❌ 飞书同步测试失败")
        print("💡 请检查：")
        print("   1. spreadsheet_token 是否正确")
        print("   2. table_id 是否正确")
        print("   3. 飞书表格字段是否与代码中的字段名称匹配")
        print("   4. 应用是否有表格的写入权限")
        return False

if __name__ == "__main__":
    print("🚀 飞书同步功能测试")
    print("=" * 50)
    
    result = test_feishu_sync()
    
    print("\n" + "=" * 50)
    if result:
        print("🎉 测试完成：飞书同步功能正常")
    else:
        print("⚠️ 测试完成：飞书同步功能需要进一步检查")
    
    print("\n📝 修复说明：")
    print("1. 修复了数据字段映射问题")
    print("2. 确保字段名称与飞书表格完全匹配")
    print("3. 修复了时间戳格式问题")
    print("4. 添加了详细的调试日志")
    print("5. 改进了错误处理机制")