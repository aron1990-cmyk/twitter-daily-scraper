#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书数据验证功能测试脚本
测试新增的数据验证功能是否正常工作
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_app import app, FEISHU_CONFIG, ScrapingTask, TweetData, db
from feishu_data_validator import FeishuDataValidator
from datetime import datetime
import json

def test_feishu_validation():
    """测试飞书数据验证功能"""
    with app.app_context():
        print("🧪 测试飞书数据验证功能")
        print("=" * 60)
        
        # 1. 检查飞书配置
        print("\n🔧 检查飞书配置:")
        print(f"   - 飞书启用: {FEISHU_CONFIG.get('enabled', False)}")
        print(f"   - 自动同步: {FEISHU_CONFIG.get('auto_sync', False)}")
        print(f"   - App ID: {'已配置' if FEISHU_CONFIG.get('app_id') else '未配置'}")
        print(f"   - App Secret: {'已配置' if FEISHU_CONFIG.get('app_secret') else '未配置'}")
        print(f"   - 表格Token: {'已配置' if FEISHU_CONFIG.get('spreadsheet_token') else '未配置'}")
        print(f"   - 表格ID: {'已配置' if FEISHU_CONFIG.get('table_id') else '未配置'}")
        
        # 检查配置完整性
        required_fields = ['app_id', 'app_secret', 'spreadsheet_token', 'table_id']
        missing_fields = [field for field in required_fields if not FEISHU_CONFIG.get(field)]
        
        if missing_fields:
            print(f"   ❌ 配置不完整，缺少字段: {', '.join(missing_fields)}")
            print("\n💡 请先完成飞书配置后再测试验证功能")
            return False
        
        if not FEISHU_CONFIG.get('enabled'):
            print("   ❌ 飞书同步未启用")
            print("\n💡 请先启用飞书同步后再测试验证功能")
            return False
        
        print("   ✅ 飞书配置完整且已启用")
        
        # 2. 查找有数据的任务
        print("\n📋 查找可用任务:")
        tasks_with_data = db.session.query(ScrapingTask).join(TweetData).filter(
            TweetData.task_id == ScrapingTask.id
        ).distinct().all()
        
        if not tasks_with_data:
            print("   ❌ 没有找到包含推文数据的任务")
            print("\n💡 请先运行抓取任务获取一些推文数据")
            return False
        
        print(f"   ✅ 找到 {len(tasks_with_data)} 个包含数据的任务")
        
        # 选择最新的任务进行测试
        test_task = max(tasks_with_data, key=lambda t: t.id)
        tweet_count = TweetData.query.filter_by(task_id=test_task.id).count()
        synced_count = TweetData.query.filter_by(task_id=test_task.id, synced_to_feishu=True).count()
        
        print(f"   - 选择任务: {test_task.name} (ID: {test_task.id})")
        print(f"   - 推文总数: {tweet_count}")
        print(f"   - 已同步数: {synced_count}")
        print(f"   - 同步率: {synced_count/tweet_count*100:.1f}%" if tweet_count > 0 else "   - 同步率: 0%")
        
        if synced_count == 0:
            print("   ⚠️ 该任务尚未同步任何数据到飞书")
            print("\n💡 建议先同步一些数据到飞书后再测试验证功能")
            # 注意：即使没有同步数据，验证器功能本身仍可能正常工作
            # 这里不直接返回False，而是继续测试验证器功能
        
        # 3. 测试数据验证器
        print("\n🔍 测试数据验证器:")
        try:
            validator = FeishuDataValidator()
            print("   ✅ 验证器初始化成功")
            
            # 执行验证
            print(f"\n🚀 开始验证任务 {test_task.id} 的数据...")
            validation_result = validator.validate_sync_data(task_id=test_task.id)
            
            if validation_result.get('success'):
                print("   ✅ 验证执行成功")
                
                # 显示验证结果
                comparison = validation_result.get('comparison_result', {})
                summary = comparison.get('summary', {})
                
                print("\n📊 验证结果摘要:")
                print(f"   - 本地记录数: {summary.get('total_local', 0)}")
                print(f"   - 飞书记录数: {summary.get('total_feishu', 0)}")
                print(f"   - 匹配记录数: {summary.get('matched_count', 0)}")
                print(f"   - 同步准确率: {summary.get('sync_accuracy', 0):.2f}%")
                
                print("\n📋 详细统计:")
                print(f"   - 完全匹配: {len(comparison.get('matched_records', []))} 条")
                print(f"   - 飞书缺失: {len(comparison.get('missing_in_feishu', []))} 条")
                print(f"   - 飞书多余: {len(comparison.get('extra_in_feishu', []))} 条")
                print(f"   - 字段不匹配: {len(comparison.get('field_mismatches', []))} 条")
                
                # 质量评估
                sync_accuracy = summary.get('sync_accuracy', 0)
                if sync_accuracy >= 95:
                    print("\n🎉 数据同步质量: 优秀")
                elif sync_accuracy >= 85:
                    print("\n⚠️ 数据同步质量: 良好")
                else:
                    print(f"\n❌ 数据同步质量: 需要改进 (准确率 {sync_accuracy:.2f}%)")
                
                # 显示问题样例（如果有）
                missing_in_feishu = comparison.get('missing_in_feishu', [])
                if missing_in_feishu:
                    print(f"\n❌ 飞书中缺失的记录 ({len(missing_in_feishu)} 条):")
                    for i, missing in enumerate(missing_in_feishu[:3]):
                        content = missing.get('content', missing.get('推文原文内容', ''))[:50]
                        print(f"   {i+1}. {content}...")
                    if len(missing_in_feishu) > 3:
                        print(f"   ... 还有 {len(missing_in_feishu) - 3} 条")
                
                extra_in_feishu = comparison.get('extra_in_feishu', [])
                if extra_in_feishu:
                    print(f"\n⚠️ 飞书中多余的记录 ({len(extra_in_feishu)} 条):")
                    for i, extra in enumerate(extra_in_feishu[:3]):
                        content = extra.get('推文原文内容', '')[:50]
                        print(f"   {i+1}. {content}...")
                    if len(extra_in_feishu) > 3:
                        print(f"   ... 还有 {len(extra_in_feishu) - 3} 条")
                
                field_mismatches = comparison.get('field_mismatches', [])
                if field_mismatches:
                    print(f"\n🔄 字段值不匹配的记录 ({len(field_mismatches)} 条):")
                    for i, mismatch in enumerate(field_mismatches[:3]):
                        content = mismatch.get('content', 'No content available')
                        mismatched_fields = mismatch.get('mismatched_fields', [])
                        print(f"   {i+1}. {content}")
                        for field_info in mismatched_fields[:3]:  # 只显示前3个不匹配字段
                            field_name = field_info.get('field', '')
                            local_value = field_info.get('local_value', '')
                            feishu_value = field_info.get('feishu_value', '')
                            print(f"      - {field_name}: 本地='{local_value}' vs 飞书='{feishu_value}'")
                
                print(f"\n✅ [FEISHU_VALIDATE] 验证完成")
                print(f"📊 [FEISHU_VALIDATE] 同步准确率: {sync_accuracy:.2f}%")
                
                # 验证器功能测试成功的标准是能够正常执行验证，而不是数据质量
                print("\n🎉 验证器功能测试成功！验证器能够正常执行并返回结果")
                return True
                
            else:
                error_msg = validation_result.get('error', '未知错误')
                print(f"   ❌ 验证执行失败: {error_msg}")
                return False
                
        except Exception as e:
            print(f"   ❌ 验证器测试失败: {e}")
            import traceback
            print(f"   📋 错误详情: {traceback.format_exc()}")
            return False

def test_api_endpoint():
    """测试API端点"""
    print("\n🌐 测试API端点功能")
    print("=" * 40)
    
    with app.app_context():
        # 查找有数据的任务
        tasks_with_data = db.session.query(ScrapingTask).join(TweetData).filter(
            TweetData.task_id == ScrapingTask.id,
            TweetData.synced_to_feishu == True
        ).distinct().all()
        
        if not tasks_with_data:
            print("   ❌ 没有找到已同步的任务数据")
            return False
        
        test_task = tasks_with_data[0]
        print(f"   - 测试任务: {test_task.name} (ID: {test_task.id})")
        
        # 模拟API调用
        with app.test_client() as client:
            print(f"   - 调用API: POST /api/data/validate_feishu/{test_task.id}")
            
            response = client.post(f'/api/data/validate_feishu/{test_task.id}')
            
            print(f"   - 响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                # 先获取原始响应文本
                response_text = response.get_data(as_text=True)
                print(f"   - 响应内容类型: {response.content_type}")
                
                try:
                    # 尝试解析JSON
                    data = json.loads(response_text)
                    
                    if data.get('success'):
                        report = data.get('validation_report', {})
                        summary = report.get('summary', {})
                        print(f"   ✅ API调用成功，准确率: {summary.get('sync_accuracy', 0):.2f}%")
                        print(f"   - 匹配记录: {summary.get('matched_count', 0)}")
                        print(f"   - 本地记录: {summary.get('total_local', 0)}")
                        print(f"   - 飞书记录: {summary.get('total_feishu', 0)}")
                        return True
                    else:
                        print(f"   ❌ API返回失败: {data.get('error')}")
                        return False
                except json.JSONDecodeError as je:
                    print(f"   ❌ JSON解析失败: {je}")
                    print(f"   - 响应内容: {response_text[:500]}...")  # 只显示前500字符
                    return False
            else:
                print(f"   ❌ API调用失败: {response.status_code}")
                response_text = response.get_data(as_text=True)
                print(f"   - 响应内容: {response_text[:500]}...")  # 只显示前500字符
                return False

if __name__ == '__main__':
    print("🧪 飞书数据验证功能完整测试")
    print("=" * 60)
    
    # 测试验证器功能
    validator_success = test_feishu_validation()
    
    # 测试API端点
    api_success = test_api_endpoint()
    
    print("\n📋 测试结果总结:")
    print("=" * 40)
    print(f"   - 验证器功能: {'✅ 通过' if validator_success else '❌ 失败'}")
    print(f"   - API端点功能: {'✅ 通过' if api_success else '❌ 失败'}")
    
    if validator_success and api_success:
        print("\n🎉 所有测试通过！飞书数据验证功能已就绪")
        print("\n💡 使用方法:")
        print("   1. 在数据查看页面选择任务")
        print("   2. 点击'验证数据'按钮")
        print("   3. 查看验证结果和准确率")
    else:
        print("\n❌ 部分测试失败，请检查配置和数据")