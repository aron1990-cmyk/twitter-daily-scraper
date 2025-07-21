#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的推文抓取测试
"""

import asyncio
import logging
import sqlite3
from ads_browser_launcher import AdsPowerLauncher
from twitter_parser import TwitterParser

def load_adspower_config_from_db():
    """从数据库加载AdsPower配置"""
    try:
        conn = sqlite3.connect('instance/twitter_scraper.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT key, value FROM system_config WHERE key LIKE '%adspower%'")
        configs = cursor.fetchall()
        
        config_dict = {}
        api_host = 'local.adspower.net'
        api_port = '50325'
        
        for key, value in configs:
            if key == 'adspower_api_host':
                api_host = value
            elif key == 'adspower_api_port':
                api_port = value
            elif key == 'adspower_user_id':
                config_dict['user_id'] = value
            elif key == 'adspower_group_id':
                config_dict['group_id'] = value
        
        config_dict['local_api_url'] = f"http://{api_host}:{api_port}"
        
        if 'user_id' not in config_dict or not config_dict['user_id']:
            config_dict['user_id'] = 'k11p9ypc'
        
        conn.close()
        print(f"AdsPower配置: {config_dict}")
        return config_dict
        
    except Exception as e:
        print(f"加载配置失败: {e}")
        return {
            'local_api_url': 'http://local.adspower.net:50325',
            'user_id': 'k11p9ypc',
            'group_id': ''
        }

async def test_scrape():
    """测试抓取功能"""
    print("开始测试推文抓取...")
    
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        # 加载配置
        config = load_adspower_config_from_db()
        
        # 初始化AdsPower启动器
        launcher = AdsPowerLauncher(config)
        
        # 启动浏览器
        print("启动AdsPower浏览器...")
        browser_info = launcher.start_browser()
        print(f"浏览器信息: {browser_info}")
        
        # 等待浏览器准备就绪
        if not launcher.wait_for_browser_ready():
            raise Exception("浏览器启动超时")
        
        # 获取调试端口
        debug_port = launcher.get_debug_port()
        print(f"调试端口: {debug_port}")
        
        # 创建Twitter解析器
        parser = TwitterParser(debug_port)
        await parser.connect_browser()
        
        # 导航到Twitter
        await parser.navigate_to_twitter()
        
        # 抓取Musk的推文
        print("开始抓取@elonmusk的推文...")
        tweets = await parser.scrape_user_tweets('elonmusk', 100, enable_enhanced=True)
        
        print(f"成功抓取 {len(tweets)} 条推文")
        
        # 保存到数据库
        if tweets:
            print("保存推文到数据库...")
            from web_app import app, Tweet
            with app.app_context():
                saved_count = 0
                for tweet_data in tweets:
                    try:
                        # 检查是否已存在
                        existing = Tweet.query.filter_by(tweet_id=tweet_data.get('id')).first()
                        if not existing:
                            tweet = Tweet(
                                tweet_id=tweet_data.get('id'),
                                username=tweet_data.get('username', 'elonmusk'),
                                content=tweet_data.get('content', ''),
                                likes=tweet_data.get('likes', 0),
                                retweets=tweet_data.get('retweets', 0),
                                comments=tweet_data.get('comments', 0),
                                timestamp=tweet_data.get('timestamp'),
                                url=tweet_data.get('url', ''),
                                raw_data=str(tweet_data)
                            )
                            from web_app import db
                            db.session.add(tweet)
                            saved_count += 1
                    except Exception as e:
                        print(f"保存推文失败: {e}")
                
                if saved_count > 0:
                    db.session.commit()
                    print(f"成功保存 {saved_count} 条新推文到数据库")
                else:
                    print("没有新推文需要保存")
        
        # 同步到飞书
        print("同步到飞书...")
        from cloud_sync import CloudSyncManager
        cloud_sync = CloudSyncManager({})
        
        # 检查飞书配置
        conn = sqlite3.connect('instance/twitter_scraper.db')
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM system_config WHERE key LIKE '%feishu%'")
        feishu_configs = cursor.fetchall()
        feishu_config = {key.replace('feishu_', ''): value for key, value in feishu_configs}
        conn.close()
        
        if feishu_config.get('enabled') == 'true':
            try:
                sync_result = await cloud_sync.sync_to_feishu(tweets, feishu_config)
                if sync_result:
                    print("✅ 飞书同步成功")
                else:
                    print("❌ 飞书同步失败")
            except Exception as e:
                print(f"飞书同步错误: {e}")
        else:
            print("飞书同步未启用")
        
        # 清理
        await parser.close()
        launcher.stop_browser()
        
        print("测试完成！")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_scrape())