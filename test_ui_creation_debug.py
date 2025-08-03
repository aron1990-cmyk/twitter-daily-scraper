#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select

def test_ui_task_creation():
    """测试UI任务创建的完整流程"""
    print("🔍 开始UI任务创建调试测试")
    
    # 配置Chrome选项
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 10)
        
        # 访问任务页面
        print("📄 访问任务页面...")
        driver.get("http://localhost:8091/tasks")
        time.sleep(2)
        
        # 获取创建前的任务列表
        print("📋 获取创建前的任务列表...")
        response = requests.get("http://localhost:8091/api/tasks")
        if response.status_code == 200:
            before_tasks = response.json().get('tasks', [])
            print(f"创建前任务数量: {len(before_tasks)}")
            for task in before_tasks[-3:]:
                print(f"  - ID: {task['id']}, 名称: '{task['name']}', 状态: {task.get('status', 'unknown')}")
        else:
            print(f"获取任务列表失败: {response.status_code}")
            return
        
        # 查找并点击创建任务按钮
        print("🔘 查找创建任务按钮...")
        create_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-bs-toggle='modal'][data-bs-target='#createTaskModal']"))
        )
        print(f"找到创建按钮: {create_button.text}")
        create_button.click()
        
        # 等待模态框显示
        print("⏳ 等待模态框显示...")
        modal = wait.until(
            EC.visibility_of_element_located((By.ID, "createTaskModal"))
        )
        print("模态框已显示")
        
        # 填写任务名称
        task_name = f"调试任务_UI创建_{int(time.time())}"
        print(f"📝 填写任务名称: {task_name}")
        name_input = driver.find_element(By.ID, "modal_task_name")
        name_input.clear()
        name_input.send_keys(task_name)
        
        # 填写关键词
        print("🔑 填写关键词...")
        keywords_input = driver.find_element(By.ID, "modal_keywords")
        keywords_input.clear()
        keywords_input.send_keys("调试测试")
        
        # 填写目标账号
        print("👤 填写目标账号...")
        target_input = driver.find_element(By.ID, "modal_target_accounts")
        target_input.clear()
        target_input.send_keys("elonmusk")  # 使用一个示例账号
        
        # 设置为不自动启动
        print("⚙️ 设置不自动启动...")
        auto_start_checkbox = driver.find_element(By.ID, "modal_auto_start")
        if auto_start_checkbox.is_selected():
            auto_start_checkbox.click()
        
        # 点击创建按钮
        print("✅ 点击创建按钮...")
        submit_button = driver.find_element(By.CSS_SELECTOR, "#createTaskModal .btn-primary")
        submit_button.click()
        
        # 等待并处理成功提示弹窗
        print("⏳ 等待成功提示弹窗...")
        try:
            wait.until(EC.alert_is_present())
            alert = driver.switch_to.alert
            alert_text = alert.text
            print(f"收到提示: {alert_text}")
            alert.accept()  # 点击确定
        except Exception as e:
            print(f"处理弹窗时出错: {str(e)}")
        
        # 等待模态框关闭
        print("⏳ 等待模态框关闭...")
        try:
            wait.until(EC.invisibility_of_element_located((By.ID, "createTaskModal")))
            print("模态框已关闭")
        except Exception as e:
            print(f"等待模态框关闭时出错: {str(e)}")
        
        # 等待一段时间让任务创建完成
        print("⏳ 等待任务创建完成...")
        time.sleep(3)
        
        # 获取创建后的任务列表
        print("📋 获取创建后的任务列表...")
        response = requests.get("http://localhost:8091/api/tasks")
        if response.status_code == 200:
            after_tasks = response.json().get('tasks', [])
            print(f"创建后任务数量: {len(after_tasks)}")
            
            # 查找新创建的任务
            new_tasks = [task for task in after_tasks if task['id'] not in [t['id'] for t in before_tasks]]
            print(f"新创建的任务数量: {len(new_tasks)}")
            
            for task in new_tasks:
                print(f"  新任务 - ID: {task['id']}, 名称: '{task['name']}', 状态: {task.get('status', 'unknown')}")
            
            # 查找匹配的任务
            matching_tasks = []
            for task in after_tasks:
                if (task['name'] == task_name or 
                    task['name'].startswith(task_name + " (主任务)") or
                    task_name in task['name']):
                    matching_tasks.append(task)
            
            print(f"匹配的任务数量: {len(matching_tasks)}")
            for task in matching_tasks:
                print(f"  匹配任务 - ID: {task['id']}, 名称: '{task['name']}', 状态: {task.get('status', 'unknown')}")
            
            # 显示最后几个任务
            print("最后5个任务:")
            for task in after_tasks[-5:]:
                print(f"  - ID: {task['id']}, 名称: '{task['name']}', 状态: {task.get('status', 'unknown')}")
                
            if matching_tasks:
                print(f"✅ 成功找到创建的任务: {matching_tasks[0]['name']}")
                return matching_tasks[0]['id']
            else:
                print(f"❌ 未找到匹配的任务: {task_name}")
                return None
        else:
            print(f"获取任务列表失败: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    task_id = test_ui_task_creation()
    if task_id:
        print(f"\n🎉 任务创建成功，ID: {task_id}")
        
        # 清理创建的任务
        print("🧹 清理测试任务...")
        try:
            response = requests.delete(f"http://localhost:8091/api/tasks/{task_id}")
            if response.status_code == 200:
                print("✅ 测试任务已清理")
            else:
                print(f"⚠️ 清理任务失败: {response.status_code}")
        except Exception as e:
            print(f"⚠️ 清理任务时发生错误: {str(e)}")
    else:
        print("\n❌ 任务创建失败")