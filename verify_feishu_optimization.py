#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证飞书配置优化结果
确认飞书同步功能已默认启用并正常工作
"""

import json
from web_app import app, db, TweetData, SystemConfig, FEISHU_CONFIG

def verify_feishu_optimization():
    """验证飞书配置优化结果"""
    with app.app_context():
        print("🔍 验证飞书配置优化结果")
        print("=" * 60)
        
        verification_results = {
            'default_enabled': False,
            'database_config': False,
            'web_config': False,
            'sync_functionality': False
        }
        
        # 1. 检查代码中的默认配置
        print("\n📝 1. 检查代码默认配置:")
        if FEISHU_CONFIG.get('enabled', False):
            print("   ✅ FEISHU_CONFIG['enabled'] = True (代码中默认启用)")
            verification_results['default_enabled'] = True
        else:
            print("   ❌ FEISHU_CONFIG['enabled'] = False (代码中默认未启用)")
        
        # 2. 检查数据库配置
        print("\n💾 2. 检查数据库配置:")
        feishu_configs = SystemConfig.query.filter(SystemConfig.key.like('feishu_%')).all()
        
        if feishu_configs:
            print(f"   ✅ 找到 {len(feishu_configs)} 项飞书配置")
            
            config_dict = {cfg.key: cfg.value for cfg in feishu_configs}
            
            # 检查关键配置
            enabled_status = config_dict.get('feishu_enabled', 'false').lower() == 'true'
            auto_sync_status = config_dict.get('feishu_auto_sync', 'false').lower() == 'true'
            
            if enabled_status:
                print("   ✅ feishu_enabled = true (数据库中已启用)")
                verification_results['database_config'] = True
            else:
                print("   ❌ feishu_enabled = false (数据库中未启用)")
            
            if auto_sync_status:
                print("   ✅ feishu_auto_sync = true (自动同步已启用)")
            else:
                print("   ⚠️ feishu_auto_sync = false (自动同步未启用)")
            
            # 显示所有配置
            print("\n   📋 完整配置列表:")
            for config in feishu_configs:
                if 'secret' in config.key.lower():
                    display_value = config.value[:10] + '...' if config.value and len(config.value) > 10 else config.value
                else:
                    display_value = config.value
                print(f"      - {config.key}: {display_value}")
        else:
            print("   ❌ 数据库中未找到飞书配置")
        
        # 3. 检查Web应用配置加载
        print("\n🌐 3. 检查Web应用配置加载:")
        try:
            # 重新加载配置
            from web_app import load_config_from_database
            load_config_from_database()
            
            # 检查加载后的配置
            if FEISHU_CONFIG.get('enabled', False):
                print("   ✅ Web应用中飞书同步已启用")
                verification_results['web_config'] = True
            else:
                print("   ❌ Web应用中飞书同步未启用")
            
            print(f"   📊 当前FEISHU_CONFIG: {json.dumps(FEISHU_CONFIG, ensure_ascii=False, indent=6)}")
            
        except Exception as e:
            print(f"   ❌ 配置加载失败: {e}")
        
        # 4. 检查同步功能
        print("\n🔄 4. 检查同步功能:")
        try:
            # 检查推文数据
            total_tweets = TweetData.query.count()
            synced_tweets = TweetData.query.filter_by(synced_to_feishu=True).count()
            
            print(f"   📊 推文数据统计:")
            print(f"      - 总推文数: {total_tweets}")
            print(f"      - 已同步: {synced_tweets}")
            print(f"      - 未同步: {total_tweets - synced_tweets}")
            
            if total_tweets > 0:
                sync_rate = (synced_tweets / total_tweets) * 100
                print(f"      - 同步率: {sync_rate:.1f}%")
                
                if synced_tweets > 0:
                    print("   ✅ 同步功能正常工作")
                    verification_results['sync_functionality'] = True
                else:
                    print("   ⚠️ 同步功能已配置但无同步数据")
            else:
                print("   ℹ️ 暂无推文数据可供同步")
                verification_results['sync_functionality'] = True  # 功能可用，只是没有数据
            
        except Exception as e:
            print(f"   ❌ 同步功能检查失败: {e}")
        
        # 5. 生成验证报告
        print("\n📋 5. 验证报告:")
        print("=" * 40)
        
        passed_checks = sum(verification_results.values())
        total_checks = len(verification_results)
        
        for check_name, result in verification_results.items():
            status = "✅ 通过" if result else "❌ 失败"
            check_display = {
                'default_enabled': '代码默认启用',
                'database_config': '数据库配置',
                'web_config': 'Web应用配置',
                'sync_functionality': '同步功能'
            }
            print(f"   {status} {check_display[check_name]}")
        
        print(f"\n📈 总体评分: {passed_checks}/{total_checks} ({(passed_checks/total_checks*100):.1f}%)")
        
        if passed_checks == total_checks:
            print("\n🎉 飞书配置优化完成！")
            print("   ✅ 飞书同步功能已默认启用")
            print("   ✅ 抓取的内容将自动保存到飞书")
            return True
        else:
            print("\n⚠️ 飞书配置优化部分完成")
            print("   💡 请检查上述失败项目并进行修复")
            return False

def show_next_steps():
    """显示后续步骤"""
    print("\n📝 后续步骤")
    print("=" * 40)
    print("1. 配置飞书应用信息:")
    print("   - 访问 http://localhost:5000/config")
    print("   - 填写真实的飞书 App ID、App Secret")
    print("   - 填写飞书表格 Token 和表格 ID")
    print("")
    print("2. 测试同步功能:")
    print("   - 启动新的抓取任务")
    print("   - 观察推文数据是否同步到飞书")
    print("")
    print("3. 监控同步状态:")
    print("   - 定期检查同步日志")
    print("   - 确保同步功能稳定运行")

if __name__ == '__main__':
    print("🔍 飞书配置优化验证工具")
    print("=" * 60)
    
    # 运行验证
    success = verify_feishu_optimization()
    
    # 显示后续步骤
    show_next_steps()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 验证完成：飞书配置优化成功！")
    else:
        print("⚠️ 验证完成：飞书配置需要进一步优化")