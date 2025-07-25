#!/usr/bin/env python3
from web_app import app, db, SystemConfig
import requests
import json

def check_adspower_user_profiles():
    """检查AdsPower中的用户Profile"""
    
    with app.app_context():
        # 手动加载配置
        from web_app import load_config_from_database
        load_config_from_database()
        
        # 获取配置
        configs = SystemConfig.query.all()
        config_dict = {cfg.key: cfg.value for cfg in configs}
        
        print("=== AdsPower用户Profile检查 ===")
        
        # 获取API配置
        api_url = config_dict.get('adspower_api_url', 'http://127.0.0.1:50325')
        
        print(f"\n1. API地址: {api_url}")
        
        # 检查所有配置的用户ID
        user_ids_to_check = ['k11p9ypc', 'k11p9y6f']
        
        for user_id in user_ids_to_check:
            print(f"\n2. 检查用户ID: {user_id}")
            
            try:
                # 获取用户Profile信息
                response = requests.get(f"{api_url}/api/v1/user/list")
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('code') == 0:
                        profiles = data.get('data', {}).get('list', [])
                        
                        # 查找指定的用户ID
                        found_profile = None
                        for profile in profiles:
                            if profile.get('user_id') == user_id:
                                found_profile = profile
                                break
                        
                        if found_profile:
                            print(f"   ✅ 用户ID {user_id} 存在")
                            print(f"   名称: {found_profile.get('name', 'N/A')}")
                            print(f"   状态: {found_profile.get('remark', 'N/A')}")
                            print(f"   分组: {found_profile.get('group_name', 'N/A')}")
                            
                            # 测试启动浏览器
                            print(f"   测试启动浏览器...")
                            start_response = requests.get(f"{api_url}/api/v1/browser/start?user_id={user_id}")
                            
                            if start_response.status_code == 200:
                                start_data = start_response.json()
                                if start_data.get('code') == 0:
                                    print(f"   ✅ 浏览器启动成功")
                                    
                                    # 关闭浏览器
                                    close_response = requests.get(f"{api_url}/api/v1/browser/stop?user_id={user_id}")
                                    if close_response.status_code == 200:
                                        print(f"   ✅ 浏览器关闭成功")
                                else:
                                    print(f"   ❌ 浏览器启动失败: {start_data.get('msg', 'Unknown error')}")
                            else:
                                print(f"   ❌ 浏览器启动请求失败: {start_response.status_code}")
                        else:
                            print(f"   ❌ 用户ID {user_id} 不存在")
                    else:
                        print(f"   ❌ API返回错误: {data.get('msg', 'Unknown error')}")
                else:
                    print(f"   ❌ API请求失败: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ 检查用户ID {user_id} 时发生错误: {e}")
        
        print(f"\n3. 检查完成")

if __name__ == "__main__":
    check_adspower_user_profiles()