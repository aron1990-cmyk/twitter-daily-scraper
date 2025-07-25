#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试飞书字段映射
验证字段映射是否正确
"""

import json
from datetime import datetime

def test_field_mapping():
    """测试字段映射逻辑"""
    print("🧪 测试飞书字段映射")
    print("=" * 50)
    
    # 模拟推文数据（基于web_app.py中的数据结构）
    mock_tweet_data = {
        '推文原文内容': '这是一条测试推文内容，包含一些有趣的话题 #AI #技术',
        '发布时间': '2025-07-25 16:30:00',
        '作者（账号）': '@test_user',
        '推文链接': 'https://twitter.com/test_user/status/123456789',
        '话题标签（Hashtag）': '#AI, #技术',
        '类型标签': '技术分享',
        '评论数': 15,
        '点赞数': 128,
        '转发数': 42,
        '创建时间': '2025-07-25 16:32:00'
    }
    
    print("📊 原始推文数据:")
    for key, value in mock_tweet_data.items():
        print(f"   - {key}: {value}")
    
    # 模拟cloud_sync.py中的字段映射逻辑
    def safe_int(value, default=0):
        """安全转换为整数"""
        try:
            if value is None or value == '':
                return default
            return int(float(str(value)))
        except (ValueError, TypeError):
            return default
    
    # 应用字段映射（基于修改后的逻辑）
    all_possible_fields = {
        # 推文内容字段 - 直接使用"推文原文内容"
        '推文原文内容': str(mock_tweet_data.get('推文原文内容', '') or mock_tweet_data.get('推文原 文内容', '')),
        
        # 作者信息
        '作者（账号）': str(mock_tweet_data.get('作者（账号）', '')),
        
        # 链接信息
        '推文链接': str(mock_tweet_data.get('推文链接', '')),
        
        # 标签信息
        '话题标签（Hashtag）': str(mock_tweet_data.get('话题标签（Hashtag）', '')),
        '类型标签': str(mock_tweet_data.get('类型标签', '')),
        
        # 数值字段 - 直接使用字段名称
        '评论': safe_int(mock_tweet_data.get('评论数', 0) or mock_tweet_data.get('评论', 0)),
        '转发': safe_int(mock_tweet_data.get('转发数', 0) or mock_tweet_data.get('转发', 0)),
        '点赞': safe_int(mock_tweet_data.get('点赞数', 0) or mock_tweet_data.get('点赞', 0)),
        
        # 时间字段
        '创建时间': str(mock_tweet_data.get('创建时间', '')),
        '发布时间': str(mock_tweet_data.get('发布时间', ''))
    }
    
    print("\n🔄 字段映射结果:")
    for key, value in all_possible_fields.items():
        print(f"   - {key}: {value} ({type(value).__name__})")
    
    # 模拟飞书表格的可用字段（基于用户截图）
    # 从截图可以看到的字段：推文原文内容、数字式、评论、转发、点赞、创建时间
    available_fields = [
        '推文原文内容',
        '数字式',  # 这个字段在截图中可见，但不确定用途
        '评论',
        '转发', 
        '点赞',
        '创建时间'
    ]
    
    print(f"\n📋 飞书表格可用字段 (基于截图): {available_fields}")
    
    # 检查字段匹配情况
    record_fields = {}
    matched_fields = []
    skipped_fields = []
    
    for field_name, field_value in all_possible_fields.items():
        if field_name in available_fields:
            record_fields[field_name] = field_value
            matched_fields.append(field_name)
        else:
            skipped_fields.append(field_name)
    
    print("\n📊 字段匹配分析:")
    print(f"   - 匹配字段 ({len(matched_fields)}): {matched_fields}")
    print(f"   - 跳过字段 ({len(skipped_fields)}): {skipped_fields}")
    print(f"   - 匹配率: {len(matched_fields)/len(all_possible_fields)*100:.1f}%")
    
    print("\n✅ 最终发送到飞书的记录:")
    record = {'fields': record_fields}
    print(json.dumps(record, ensure_ascii=False, indent=2))
    
    # 检查是否有有效数据
    if record_fields:
        print(f"\n🎉 字段映射成功！将发送 {len(record_fields)} 个字段到飞书")
        return True
    else:
        print("\n❌ 没有匹配的字段，无法同步")
        return False

def suggest_field_improvements():
    """建议字段改进"""
    print("\n💡 字段映射改进建议:")
    print("=" * 30)
    
    suggestions = [
        "1. 确认飞书表格中是否有'作者（账号）'字段，如果没有可以添加",
        "2. 确认飞书表格中是否有'推文链接'字段，如果没有可以添加", 
        "3. 确认飞书表格中是否有'话题标签（Hashtag）'字段，如果没有可以添加",
        "4. 确认飞书表格中是否有'类型标签'字段，如果没有可以添加",
        "5. 确认飞书表格中是否有'发布时间'字段，如果没有可以添加",
        "6. '数字式'字段的用途需要确认，可能需要映射到某个数据字段"
    ]
    
    for suggestion in suggestions:
        print(f"   {suggestion}")
    
    print("\n📝 如果无法修改飞书表格字段，需要：")
    print("   - 获取飞书表格的完整字段列表")
    print("   - 根据实际字段名称调整程序中的映射逻辑")
    print("   - 确保字段名称完全匹配（包括标点符号和空格）")

if __name__ == '__main__':
    success = test_field_mapping()
    suggest_field_improvements()
    
    if success:
        print("\n🎯 测试结果: 字段映射基本正确")
    else:
        print("\n⚠️ 测试结果: 字段映射需要调整")