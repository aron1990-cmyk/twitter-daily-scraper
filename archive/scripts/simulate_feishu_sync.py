#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟飞书同步功能
演示抓取的推文数据如何同步到飞书
"""

import json
from datetime import datetime
from web_app import app, db, TweetData, SystemConfig

def simulate_feishu_sync():
    """模拟飞书同步功能"""
    with app.app_context():
        print("🚀 模拟飞书同步功能")
        print("=" * 50)
        
        # 1. 检查飞书配置状态
        print("\n📋 检查飞书配置状态:")
        feishu_enabled_config = SystemConfig.query.filter_by(key='feishu_enabled').first()
        
        if feishu_enabled_config and feishu_enabled_config.value.lower() == 'true':
            print("   ✅ 飞书同步已启用")
        else:
            print("   ❌ 飞书同步未启用")
            return False
        
        # 2. 获取推文数据
        print("\n📊 获取推文数据:")
        tweets = TweetData.query.filter_by(synced_to_feishu=False).limit(3).all()
        
        if not tweets:
            print("   ℹ️ 没有需要同步的推文数据")
            # 获取所有推文查看状态
            all_tweets = TweetData.query.limit(5).all()
            if all_tweets:
                print(f"   📈 数据库中共有 {len(all_tweets)} 条推文")
                synced_count = sum(1 for t in all_tweets if hasattr(t, 'synced_to_feishu') and t.synced_to_feishu)
                print(f"   📤 已同步: {synced_count} 条")
                print(f"   📥 未同步: {len(all_tweets) - synced_count} 条")
            return True
        
        print(f"   ✅ 找到 {len(tweets)} 条待同步推文")
        
        # 3. 模拟同步过程
        print("\n🔄 模拟同步过程:")
        
        for i, tweet in enumerate(tweets, 1):
            print(f"\n   📝 同步推文 {i}/{len(tweets)}:")
            print(f"      - ID: {tweet.id}")
            print(f"      - 用户: {tweet.username}")
            print(f"      - 内容: {tweet.content[:50]}...")
            print(f"      - 点赞: {tweet.likes}")
            print(f"      - 转发: {tweet.retweets}")
            print(f"      - 评论: {tweet.comments}")
            
            # 模拟飞书API调用
            feishu_data = {
                "推文ID": str(tweet.id),
                "用户名": tweet.username,
                "内容": tweet.content,
                "点赞数": tweet.likes,
                "转发数": tweet.retweets,
                "评论数": tweet.comments,
                "发布时间": tweet.publish_time or '',
                "链接": getattr(tweet, 'link', '') or getattr(tweet, 'url', ''),
                "内容类型": tweet.content_type or '未分类',
                "抓取时间": tweet.scraped_at.strftime('%Y-%m-%d %H:%M:%S') if tweet.scraped_at else '',
                "同步时间": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            print(f"      📤 飞书数据: {json.dumps(feishu_data, ensure_ascii=False, indent=8)}")
            
            # 模拟成功同步，更新数据库状态
            try:
                tweet.synced_to_feishu = True
                db.session.commit()
                print(f"      ✅ 推文 {tweet.id} 同步成功")
            except Exception as e:
                print(f"      ❌ 推文 {tweet.id} 同步失败: {e}")
                db.session.rollback()
        
        # 4. 显示同步结果
        print("\n📈 同步结果统计:")
        total_tweets = TweetData.query.count()
        synced_tweets = TweetData.query.filter_by(synced_to_feishu=True).count()
        unsynced_tweets = total_tweets - synced_tweets
        
        print(f"   - 总推文数: {total_tweets}")
        print(f"   - 已同步: {synced_tweets}")
        print(f"   - 未同步: {unsynced_tweets}")
        print(f"   - 同步率: {(synced_tweets/total_tweets*100):.1f}%" if total_tweets > 0 else "   - 同步率: 0%")
        
        return True

def reset_sync_status():
    """重置同步状态（用于测试）"""
    with app.app_context():
        print("\n🔄 重置同步状态:")
        tweets = TweetData.query.all()
        
        for tweet in tweets:
            tweet.synced_to_feishu = False
        
        try:
            db.session.commit()
            print(f"   ✅ 已重置 {len(tweets)} 条推文的同步状态")
        except Exception as e:
            print(f"   ❌ 重置失败: {e}")
            db.session.rollback()

def show_sync_summary():
    """显示同步摘要"""
    with app.app_context():
        print("\n📊 飞书同步摘要")
        print("=" * 50)
        
        # 飞书配置状态
        feishu_configs = SystemConfig.query.filter(SystemConfig.key.like('feishu_%')).all()
        config_dict = {cfg.key: cfg.value for cfg in feishu_configs}
        
        print("\n🔧 配置状态:")
        print(f"   - 飞书同步: {'✅ 已启用' if config_dict.get('feishu_enabled', 'false').lower() == 'true' else '❌ 未启用'}")
        print(f"   - 自动同步: {'✅ 已启用' if config_dict.get('feishu_auto_sync', 'false').lower() == 'true' else '❌ 未启用'}")
        
        # 配置完整性
        required_configs = ['feishu_app_id', 'feishu_app_secret', 'feishu_spreadsheet_token', 'feishu_table_id']
        missing_configs = []
        
        for config_key in required_configs:
            value = config_dict.get(config_key, '')
            if not value or value.startswith('your_'):
                missing_configs.append(config_key)
        
        if missing_configs:
            print(f"   ⚠️ 缺少配置: {', '.join(missing_configs)}")
        else:
            print("   ✅ 配置完整")
        
        # 数据统计
        total_tweets = TweetData.query.count()
        synced_tweets = TweetData.query.filter_by(synced_to_feishu=True).count()
        
        print("\n📈 数据统计:")
        print(f"   - 总推文数: {total_tweets}")
        print(f"   - 已同步: {synced_tweets}")
        print(f"   - 未同步: {total_tweets - synced_tweets}")
        
        if total_tweets > 0:
            sync_rate = (synced_tweets / total_tweets) * 100
            print(f"   - 同步率: {sync_rate:.1f}%")
        
        print("\n💡 提示:")
        if missing_configs:
            print("   - 请在Web界面 (http://localhost:5000/config) 中配置飞书信息")
        else:
            print("   - 飞书配置已完成，推文数据将自动同步")

if __name__ == '__main__':
    print("🧪 飞书同步模拟器")
    print("=" * 50)
    
    # 显示同步摘要
    show_sync_summary()
    
    # 运行模拟同步
    print("\n" + "=" * 50)
    success = simulate_feishu_sync()
    
    if success:
        print("\n🎉 飞书同步模拟完成！")
        print("\n💡 说明:")
        print("   - 这是模拟演示，实际同步需要配置真实的飞书应用信息")
        print("   - 推文数据的 synced_to_feishu 字段已更新为 True")
        print("   - 在实际环境中，数据会同步到飞书多维表格")
    else:
        print("\n❌ 飞书同步模拟失败")
    
    print("\n" + "=" * 50)
    print("🔗 相关链接:")
    print("   - Web界面: http://localhost:5000")
    print("   - 配置页面: http://localhost:5000/config")
    print("   - 飞书开放平台: https://open.feishu.cn/")