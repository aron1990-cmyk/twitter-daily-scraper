#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Excel导出功能
"""

import requests
import os
from datetime import datetime

def test_excel_export():
    """测试Excel导出功能"""
    print("🧪 开始测试Excel导出功能...")
    
    # 测试URL
    base_url = "http://127.0.0.1:8090"
    export_url = f"{base_url}/api/data/export"
    
    try:
        # 发送导出请求
        print(f"📤 发送导出请求到: {export_url}")
        response = requests.get(export_url, timeout=30)
        
        print(f"📊 响应状态码: {response.status_code}")
        print(f"📄 响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            # 检查响应类型
            content_type = response.headers.get('content-type', '')
            print(f"📋 内容类型: {content_type}")
            
            if 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in content_type:
                # 保存Excel文件
                filename = f"test_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                with open(filename, 'wb') as f:
                    f.write(response.content)
                
                file_size = os.path.getsize(filename)
                print(f"✅ Excel文件导出成功!")
                print(f"📁 文件名: {filename}")
                print(f"📏 文件大小: {file_size} 字节")
                
                # 验证文件内容
                try:
                    import pandas as pd
                    df = pd.read_excel(filename)
                    print(f"📊 数据行数: {len(df)}")
                    print(f"📋 列名: {list(df.columns)}")
                    
                    if len(df) > 0:
                        print("\n📝 前3行数据预览:")
                        for i, row in df.head(3).iterrows():
                            print(f"  行 {i+1}:")
                            for col in df.columns:
                                value = row[col]
                                if pd.isna(value):
                                    value = "(空)"
                                elif isinstance(value, str) and len(value) > 50:
                                    value = value[:50] + "..."
                                print(f"    {col}: {value}")
                            print()
                    
                    print("✅ Excel文件格式验证通过!")
                    
                except Exception as e:
                    print(f"❌ Excel文件验证失败: {e}")
                    
            elif 'application/json' in content_type:
                # 如果返回JSON，可能是错误信息
                try:
                    error_data = response.json()
                    print(f"❌ 导出失败: {error_data.get('error', '未知错误')}")
                except:
                    print(f"❌ 导出失败，无法解析错误信息")
            else:
                print(f"❌ 意外的响应类型: {content_type}")
                print(f"📄 响应内容: {response.text[:500]}")
                
        else:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            try:
                error_data = response.json()
                print(f"❌ 错误信息: {error_data.get('error', '未知错误')}")
            except:
                print(f"📄 响应内容: {response.text[:500]}")
                
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求失败: {e}")
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

def test_with_filters():
    """测试带筛选条件的导出"""
    print("\n🧪 测试带筛选条件的Excel导出...")
    
    base_url = "http://127.0.0.1:8090"
    
    # 测试不同的筛选条件
    test_cases = [
        {"name": "按任务ID筛选", "params": {"task_id": 1}},
        {"name": "按最小点赞数筛选", "params": {"min_likes": 1}},
        {"name": "按搜索关键词筛选", "params": {"search": "test"}},
    ]
    
    for test_case in test_cases:
        print(f"\n📋 测试: {test_case['name']}")
        export_url = f"{base_url}/api/data/export"
        
        try:
            response = requests.get(export_url, params=test_case['params'], timeout=30)
            print(f"📊 状态码: {response.status_code}")
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in content_type:
                    print(f"✅ {test_case['name']} - 导出成功")
                    print(f"📏 文件大小: {len(response.content)} 字节")
                else:
                    print(f"❌ {test_case['name']} - 响应类型错误: {content_type}")
            elif response.status_code == 400:
                try:
                    error_data = response.json()
                    if error_data.get('error') == '没有数据可导出':
                        print(f"ℹ️ {test_case['name']} - 没有匹配的数据")
                    else:
                        print(f"❌ {test_case['name']} - 错误: {error_data.get('error')}")
                except:
                    print(f"❌ {test_case['name']} - 请求失败")
            else:
                print(f"❌ {test_case['name']} - 状态码: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {test_case['name']} - 异常: {e}")

if __name__ == "__main__":
    print("🚀 Excel导出功能测试开始")
    print("=" * 50)
    
    # 基本导出测试
    test_excel_export()
    
    # 筛选条件测试
    test_with_filters()
    
    print("\n" + "=" * 50)
    print("🏁 Excel导出功能测试完成")