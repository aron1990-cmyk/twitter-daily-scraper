#!/usr/bin/env python3
import requests
import time
import json

def test_start_task27():
    """测试启动任务27"""
    
    print("=== 测试启动任务27 ===")
    
    # API地址
    api_url = "http://127.0.0.1:8088/api/tasks/27/start"
    
    try:
        print(f"\n🚀 发送启动请求到: {api_url}")
        
        # 发送POST请求启动任务
        response = requests.post(api_url, timeout=30)
        
        print(f"\n响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"\n✅ 响应JSON:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                
                if result.get('success'):
                    print(f"\n✅ 任务启动成功!")
                    print(f"消息: {result.get('message', '')}")
                    
                    # 等待一段时间后检查状态
                    print(f"\n⏳ 等待15秒后检查任务状态...")
                    time.sleep(15)
                    
                    # 检查任务状态
                    status_url = "http://127.0.0.1:8088/api/tasks/27"
                    status_response = requests.get(status_url)
                    
                    if status_response.status_code == 200:
                        status_result = status_response.json()
                        print(f"\n📊 任务状态更新:")
                        task_data = status_result.get('data', {})
                        print(f"  状态: {task_data.get('status', 'N/A')}")
                        print(f"  开始时间: {task_data.get('started_at', 'N/A')}")
                        print(f"  结果数量: {task_data.get('result_count', 'N/A')}")
                        print(f"  错误信息: {task_data.get('error_message', '无')}")
                    else:
                        print(f"❌ 获取任务状态失败: {status_response.status_code}")
                        
                else:
                    print(f"\n❌ 任务启动失败!")
                    print(f"错误: {result.get('error', 'Unknown error')}")
                    
            except json.JSONDecodeError:
                print(f"\n❌ 响应不是有效的JSON:")
                print(f"响应内容: {response.text[:500]}...")
                
        else:
            print(f"\n❌ HTTP请求失败")
            print(f"响应内容: {response.text[:500]}...")
            
    except requests.exceptions.Timeout:
        print(f"\n❌ 请求超时")
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 连接失败，请确保Web服务器正在运行")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")

if __name__ == "__main__":
    test_start_task27()