#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AdsPower连接诊断工具
用于诊断AdsPower连接问题并提供解决方案
"""

import requests
import time
import subprocess
import psutil
import sys
import os

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 从数据库获取配置
def get_adspower_config():
    """从数据库获取AdsPower配置"""
    try:
        from web_app import app, SystemConfig
        with app.app_context():
            configs = SystemConfig.query.all()
            config_dict = {cfg.key: cfg.value for cfg in configs}
            
            # 构建AdsPower配置
            api_host = config_dict.get('adspower_api_host', 'local.adspower.net')
            api_port = config_dict.get('adspower_api_port', '50325')
            api_url = config_dict.get('adspower_api_url', f'http://{api_host}:{api_port}')
            
            return {
                'local_api_url': api_url,
                'user_id': config_dict.get('adspower_user_id', ''),
                'group_id': config_dict.get('adspower_group_id', '')
            }
    except Exception as e:
        print(f"⚠️ 无法从数据库获取配置，使用默认配置: {e}")
        return {
            'local_api_url': 'http://local.adspower.net:50325',
            'user_id': '',
            'group_id': ''
        }

ADS_POWER_CONFIG = get_adspower_config()

def check_adspower_process():
    """检查AdsPower进程是否运行"""
    print("\n🔍 检查AdsPower进程状态...")
    
    adspower_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            name = proc.info['name'] or ''
            cmdline = proc.info['cmdline'] or []
            
            if 'adspower' in name.lower() or \
               any('adspower' in arg.lower() for arg in cmdline if arg):
                adspower_processes.append({
                    'pid': proc.info['pid'],
                    'name': name,
                    'cmdline': ' '.join(cmdline[:3])  # 只显示前3个参数
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied, TypeError):
            continue
    
    if adspower_processes:
        print("✅ 发现AdsPower进程:")
        for proc in adspower_processes:
            print(f"   PID: {proc['pid']}, 名称: {proc['name']}")
        return True
    else:
        print("❌ 未发现AdsPower进程")
        return False

def test_api_connection():
    """测试AdsPower API连接"""
    print("\n🔍 测试AdsPower API连接...")
    
    api_url = ADS_POWER_CONFIG['local_api_url']
    test_endpoints = [
        '/api/v1/user/list',
        '/api/v1/browser/list',
        '/api/v1/status'
    ]
    
    for endpoint in test_endpoints:
        try:
            url = f"{api_url}{endpoint}"
            print(f"   测试: {url}")
            
            response = requests.get(url, timeout=5)
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   响应: {data}")
                    return True
                except:
                    print(f"   响应: {response.text[:100]}...")
            else:
                print(f"   错误: HTTP {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ 连接失败: 无法连接到 {url}")
        except requests.exceptions.Timeout:
            print(f"   ❌ 连接超时: {url}")
        except Exception as e:
            print(f"   ❌ 其他错误: {e}")
    
    return False

def test_browser_start():
    """测试浏览器启动"""
    print("\n🔍 测试浏览器启动...")
    
    api_url = ADS_POWER_CONFIG['local_api_url']
    user_id = ADS_POWER_CONFIG['user_id']
    
    try:
        url = f"{api_url}/api/v1/browser/start"
        params = {'user_id': user_id}
        
        print(f"   请求URL: {url}")
        print(f"   用户ID: {user_id}")
        
        response = requests.get(url, params=params, timeout=30)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   响应: {data}")
                
                if data.get('code') == 0:
                    print("   ✅ 浏览器启动成功!")
                    browser_info = data.get('data', {})
                    debug_port = browser_info.get('ws', {}).get('puppeteer')
                    if debug_port:
                        print(f"   调试端口: {debug_port}")
                    return True
                else:
                    print(f"   ❌ 浏览器启动失败: {data.get('msg', '未知错误')}")
            except:
                print(f"   响应内容: {response.text}")
        else:
            print(f"   ❌ HTTP错误: {response.status_code}")
            print(f"   响应内容: {response.text}")
            
    except Exception as e:
        print(f"   ❌ 启动测试失败: {e}")
    
    return False

def provide_solutions():
    """提供解决方案"""
    print("\n💡 解决方案建议:")
    print("\n1. 确保AdsPower应用程序正在运行:")
    print("   - 打开AdsPower应用程序")
    print("   - 确保应用程序完全启动（不是最小化状态）")
    
    print("\n2. 检查AdsPower本地API设置:")
    print("   - 在AdsPower中打开 '设置' -> 'Local API'")
    print("   - 确保本地API已启用")
    print("   - 检查端口号是否为50325")
    print("   - 如果端口不同，请更新config.py中的local_api_url")
    
    print("\n3. 检查用户ID配置:")
    print(f"   - 当前配置的用户ID: {ADS_POWER_CONFIG['user_id']}")
    print("   - 在AdsPower中确认此用户ID存在")
    print("   - 如果用户ID不正确，请更新config.py")
    
    print("\n4. 重启AdsPower:")
    print("   - 完全退出AdsPower应用程序")
    print("   - 等待几秒钟")
    print("   - 重新启动AdsPower")
    print("   - 等待应用程序完全加载")
    
    print("\n5. 检查防火墙设置:")
    print("   - 确保防火墙没有阻止AdsPower的本地API端口")
    print("   - 如果使用企业网络，可能需要联系IT部门")
    
    print("\n6. 如果问题仍然存在:")
    print("   - 尝试重启计算机")
    print("   - 重新安装AdsPower")
    print("   - 联系AdsPower技术支持")

def main():
    """主函数"""
    print("🔧 AdsPower连接诊断工具")
    print("=" * 50)
    
    # 检查进程
    process_running = check_adspower_process()
    
    # 测试API连接
    api_working = test_api_connection()
    
    # 测试浏览器启动
    browser_working = False
    if api_working:
        browser_working = test_browser_start()
    
    # 总结
    print("\n📊 诊断结果:")
    print(f"   AdsPower进程: {'✅ 运行中' if process_running else '❌ 未运行'}")
    print(f"   API连接: {'✅ 正常' if api_working else '❌ 失败'}")
    print(f"   浏览器启动: {'✅ 正常' if browser_working else '❌ 失败'}")
    
    if not (process_running and api_working and browser_working):
        provide_solutions()
    else:
        print("\n🎉 AdsPower连接正常！任务启动问题可能在其他地方。")

if __name__ == '__main__':
    main()