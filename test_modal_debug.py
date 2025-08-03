#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模态框调试测试脚本
专门测试创建任务模态框的显示和交互功能
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def setup_driver():
    """设置Chrome驱动"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 无头模式
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    return driver

def test_modal_functionality():
    """测试模态框功能"""
    driver = setup_driver()
    
    try:
        print("🚀 开始测试模态框功能")
        
        # 访问任务页面
        print("📱 访问任务页面...")
        driver.get("http://localhost:8091/tasks")
        
        # 等待页面加载
        print("⏳ 等待页面加载...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # 检查页面标题
        print(f"📄 页面标题: {driver.title}")
        
        # 查找创建任务按钮
        print("🔍 查找创建任务按钮...")
        try:
            create_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-bs-toggle="modal"][data-bs-target="#createTaskModal"]'))
            )
            print("✅ 找到创建任务按钮")
            print(f"   按钮文本: {create_btn.text}")
            print(f"   按钮可见: {create_btn.is_displayed()}")
            print(f"   按钮启用: {create_btn.is_enabled()}")
        except TimeoutException:
            print("❌ 未找到创建任务按钮")
            # 尝试查找所有可能的按钮
            buttons = driver.find_elements(By.TAG_NAME, "button")
            print(f"📋 页面上的所有按钮 ({len(buttons)}个):")
            for i, btn in enumerate(buttons[:10]):  # 只显示前10个
                print(f"   {i+1}. 文本: '{btn.text}', 类名: '{btn.get_attribute('class')}'")
            return False
        
        # 检查模态框是否存在
        print("🔍 检查模态框是否存在...")
        try:
            modal = driver.find_element(By.ID, "createTaskModal")
            print("✅ 找到模态框")
            print(f"   模态框可见: {modal.is_displayed()}")
        except NoSuchElementException:
            print("❌ 未找到模态框")
            return False
        
        # 点击创建任务按钮
        print("🖱️ 点击创建任务按钮...")
        driver.execute_script("arguments[0].scrollIntoView(true);", create_btn)
        time.sleep(0.5)
        create_btn.click()
        
        # 等待模态框显示
        print("⏳ 等待模态框显示...")
        try:
            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.ID, "createTaskModal"))
            )
            print("✅ 模态框已显示")
            
            # 检查模态框内容
            modal_title = driver.find_element(By.CSS_SELECTOR, "#createTaskModal .modal-title")
            print(f"   模态框标题: {modal_title.text}")
            
            # 检查表单字段
            form_fields = [
                ("modal_task_name", "任务名称"),
                ("modal_keywords", "关键词"),
                ("modal_target_accounts", "目标账号"),
                ("modal_max_tweets", "最大推文数"),
                ("modal_min_likes", "最小点赞数"),
                ("modal_min_retweets", "最小转发数"),
                ("modal_auto_start", "自动启动")
            ]
            
            print("📝 检查表单字段:")
            for field_id, field_name in form_fields:
                try:
                    field = driver.find_element(By.ID, field_id)
                    print(f"   ✅ {field_name}: 存在, 可见: {field.is_displayed()}, 启用: {field.is_enabled()}")
                except NoSuchElementException:
                    print(f"   ❌ {field_name}: 不存在")
            
            # 测试填写表单
            print("📝 测试填写表单...")
            task_name_input = driver.find_element(By.ID, "modal_task_name")
            task_name_input.clear()
            task_name_input.send_keys("测试任务_模态框调试")
            print(f"   任务名称已填写: {task_name_input.get_attribute('value')}")
            
            keywords_input = driver.find_element(By.ID, "modal_keywords")
            keywords_input.clear()
            keywords_input.send_keys("测试关键词")
            print(f"   关键词已填写: {keywords_input.get_attribute('value')}")
            
            # 检查创建按钮
            submit_btn = driver.find_element(By.CSS_SELECTOR, "#createTaskModal .btn-primary")
            print(f"   创建按钮: 可见: {submit_btn.is_displayed()}, 启用: {submit_btn.is_enabled()}")
            print(f"   创建按钮文本: {submit_btn.text}")
            
            print("🎉 模态框功能测试成功!")
            return True
            
        except TimeoutException:
            print("❌ 模态框未能显示")
            
            # 检查JavaScript错误
            try:
                logs = driver.get_log('browser')
                if logs:
                    print("🐛 浏览器控制台错误:")
                    for log in logs:
                        if log['level'] in ['SEVERE', 'ERROR']:
                            print(f"   - {log['level']}: {log['message']}")
            except:
                print("🐛 无法获取浏览器日志")
            
            return False
    
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False
    
    finally:
        driver.quit()

if __name__ == "__main__":
    success = test_modal_functionality()
    if success:
        print("\n✅ 模态框功能正常")
    else:
        print("\n❌ 模态框功能异常")
    exit(0 if success else 1)