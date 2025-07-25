#!/usr/bin/env python3
import requests
import json
from web_app import app, db, SystemConfig

def test_adspower_connection():
    """测试AdsPower连接并获取可用的Profile列表"""
    
    with app.app_context():
        # 获取配置
        configs = SystemConfig.query.all()
        config_dict = {cfg.key: cfg.value for cfg in configs}
        
        api_host = config_dict.get('adspower_api_host', 'localhost')
        api_port = config_dict.get('adspower_api_port', '50325')
        api_url = f"http://{api_host}:{api_port}"
        
        print(f"AdsPower API URL: {api_url}")
        
        try:
            # 测试连接
            response = requests.get(f"{api_url}/api/v1/user/list", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n✅ AdsPower连接成功!")
                print(f"响应状态: {data.get('code', 'N/A')}")
                print(f"响应消息: {data.get('msg', 'N/A')}")
                
                if 'data' in data and 'list' in data['data']:
                    profiles = data['data']['list']
                    print(f"\n📋 可用的Profile列表 (共{len(profiles)}个):")
                    
                    for i, profile in enumerate(profiles, 1):
                        user_id = profile.get('user_id', 'N/A')
                        name = profile.get('name', 'N/A')
                        status = profile.get('status', 'N/A')
                        print(f"  {i}. ID: {user_id} | 名称: {name} | 状态: {status}")
                    
                    # 检查默认用户ID是否存在
                    default_user_id = 'k11p9ypc'
                    found_default = any(p.get('user_id') == default_user_id for p in profiles)
                    
                    print(f"\n🔍 默认用户ID '{default_user_id}' 检查结果:")
                    if found_default:
                        print(f"  ✅ 找到默认用户ID")
                    else:
                        print(f"  ❌ 未找到默认用户ID")
                        if profiles:
                            first_profile = profiles[0]
                            print(f"  💡 建议使用第一个可用的Profile: {first_profile.get('user_id')}")
                else:
                    print("\n⚠️ 未找到Profile列表")
            else:
                print(f"\n❌ AdsPower连接失败!")
                print(f"状态码: {response.status_code}")
                print(f"响应内容: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"\n❌ 无法连接到AdsPower API")
            print(f"请确保:")
            print(f"  1. AdsPower客户端已启动")
            print(f"  2. API服务运行在 {api_url}")
            print(f"  3. 防火墙允许连接")
        except Exception as e:
            print(f"\n❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    test_adspower_connection()