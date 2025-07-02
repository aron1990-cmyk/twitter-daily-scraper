#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置验证脚本 - Twitter 日报采集系统

这个脚本帮助用户验证配置文件的正确性，并提供修复建议。
"""

import sys
import os
import json
import requests
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from config import (
        ADS_POWER_CONFIG, TWITTER_TARGETS, FILTER_CONFIG, 
        OUTPUT_CONFIG, BROWSER_CONFIG, LOG_CONFIG
    )
except ImportError as e:
    print(f"❌ 无法导入配置文件: {e}")
    print("请确保 config.py 文件存在且语法正确")
    sys.exit(1)

class ConfigValidator:
    """配置验证器"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.suggestions = []
    
    def add_error(self, message: str):
        """添加错误信息"""
        self.errors.append(f"❌ {message}")
    
    def add_warning(self, message: str):
        """添加警告信息"""
        self.warnings.append(f"⚠️  {message}")
    
    def add_suggestion(self, message: str):
        """添加建议信息"""
        self.suggestions.append(f"💡 {message}")
    
    def validate_adspower_config(self) -> bool:
        """验证 AdsPower 配置"""
        print("\n🔍 验证 AdsPower 配置...")
        
        # 检查必需字段
        required_fields = ['local_api_url', 'user_id']
        for field in required_fields:
            if field not in ADS_POWER_CONFIG:
                self.add_error(f"AdsPower 配置缺少必需字段: {field}")
                return False
        
        # 检查API URL
        api_url = ADS_POWER_CONFIG.get('local_api_url')
        if not api_url or not isinstance(api_url, str) or not api_url.startswith('http'):
            self.add_error(f"AdsPower API URL 无效: {api_url}")
        
        # 检查用户 ID
        user_id = ADS_POWER_CONFIG.get('user_id')
        if not user_id or not isinstance(user_id, str):
            self.add_warning("AdsPower 用户 ID 未配置，请在实际使用前填入")
        
        # 测试 AdsPower 连接
        try:
            url = f"{api_url}/api/v1/browser/list"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    browsers = data.get('data', {}).get('list', [])
                    print(f"✅ AdsPower 连接成功，发现 {len(browsers)} 个浏览器配置")
                    
                    # 检查指定的用户 ID 是否存在
                    if user_id:
                        browser_ids = [b.get('user_id') for b in browsers]
                        if user_id not in browser_ids:
                            self.add_warning(f"指定的用户 ID '{user_id}' 未在可用列表中找到")
                            self.add_suggestion(f"可用的用户 ID: {', '.join(browser_ids)}")
                        else:
                            print(f"✅ 用户 ID '{user_id}' 验证通过")
                else:
                    self.add_error(f"AdsPower API 返回错误: {data.get('msg', '未知错误')}")
            else:
                self.add_error(f"AdsPower API 响应状态码: {response.status_code}")
        except requests.exceptions.ConnectionError:
            self.add_error("无法连接到 AdsPower，请确保客户端已启动")
        except Exception as e:
            self.add_error(f"AdsPower 连接测试失败: {e}")
        
        return len(self.errors) == 0
    
    def validate_twitter_targets(self) -> bool:
        """验证 Twitter 目标配置"""
        print("\n🔍 验证 Twitter 目标配置...")
        
        # 检查目标账号
        target_accounts = TWITTER_TARGETS.get('accounts', [])
        if not isinstance(target_accounts, list):
            self.add_error("accounts 必须是列表类型")
        elif len(target_accounts) == 0:
            self.add_warning("未配置目标账号，将跳过用户推文采集")
        else:
            print(f"✅ 配置了 {len(target_accounts)} 个目标账号")
            for account in target_accounts:
                if not isinstance(account, str) or not account.strip():
                    self.add_error(f"无效的账号名: {account}")
        
        # 检查关键词
        keywords = TWITTER_TARGETS.get('keywords', [])
        if not isinstance(keywords, list):
            self.add_error("keywords 必须是列表类型")
        elif len(keywords) == 0:
            self.add_warning("未配置关键词，将跳过关键词搜索")
        else:
            print(f"✅ 配置了 {len(keywords)} 个关键词")
        
        # 检查是否至少有一种采集方式
        if len(target_accounts) == 0 and len(keywords) == 0:
            self.add_error("必须至少配置目标账号或关键词中的一种")
        
        return len(self.errors) == 0
    
    def validate_tweet_filters(self) -> bool:
        """验证推文筛选配置"""
        print("\n🔍 验证推文筛选配置...")
        
        # 检查数值类型的筛选条件
        numeric_filters = {
            'min_likes': '最小点赞数',
            'min_comments': '最小评论数', 
            'min_retweets': '最小转发数',
            'max_tweets_per_target': '最大采集数'
        }
        
        for key, desc in numeric_filters.items():
            value = FILTER_CONFIG.get(key)
            if value is not None and (not isinstance(value, int) or value < 0):
                self.add_error(f"{desc} 必须是非负整数: {value}")
        
        # 检查筛选关键词
        filter_keywords = FILTER_CONFIG.get('keywords_filter', [])
        if not isinstance(filter_keywords, list):
            self.add_error("keywords_filter 必须是列表类型")
        
        print("✅ 推文筛选配置验证通过")
        return len(self.errors) == 0
    
    def validate_output_config(self) -> bool:
        """验证输出配置"""
        print("\n🔍 验证输出配置...")
        
        # 检查输出目录
        output_dir = OUTPUT_CONFIG.get('data_dir')
        if not output_dir:
            self.add_error("输出目录不能为空")
        else:
            output_path = Path(output_dir)
            try:
                output_path.mkdir(parents=True, exist_ok=True)
                print(f"✅ 输出目录可用: {output_path.absolute()}")
            except Exception as e:
                self.add_error(f"无法创建输出目录 {output_dir}: {e}")
        
        # 检查文件名格式
        filename_format = OUTPUT_CONFIG.get('excel_filename_format')
        if not filename_format or not isinstance(filename_format, str):
            self.add_warning("建议设置有意义的文件名格式")
        
        return len(self.errors) == 0
    
    def validate_browser_config(self) -> bool:
        """验证浏览器配置"""
        print("\n🔍 验证浏览器配置...")
        
        # 检查超时设置
        timeouts = {
            'timeout': '页面加载超时',
            'wait_time': '页面操作间隔时间',
            'scroll_pause_time': '滚动间隔时间'
        }
        
        for key, desc in timeouts.items():
            value = BROWSER_CONFIG.get(key)
            if value is not None and (not isinstance(value, (int, float)) or value <= 0):
                self.add_error(f"{desc} 必须是正数: {value}")
        
        # 检查headless设置
        headless = BROWSER_CONFIG.get('headless')
        if headless is not None and not isinstance(headless, bool):
            self.add_error("headless 必须是布尔值")
        
        print("✅ 浏览器配置验证通过")
        return len(self.errors) == 0
    
    def validate_log_config(self) -> bool:
        """验证日志配置"""
        print("\n🔍 验证日志配置...")
        
        # 检查日志文件名
        log_filename = LOG_CONFIG.get('filename')
        if not log_filename or not isinstance(log_filename, str):
            self.add_warning("建议设置日志文件名")
        
        # 检查日志级别
        log_level = LOG_CONFIG.get('level')
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if log_level and log_level not in valid_levels:
            self.add_error(f"无效的日志级别: {log_level}，有效值: {', '.join(valid_levels)}")
        
        # 检查日志格式
        log_format = LOG_CONFIG.get('format')
        if not log_format or not isinstance(log_format, str):
            self.add_warning("建议设置日志格式")
        
        print("✅ 日志配置验证通过")
        return len(self.errors) == 0
    
    def run_validation(self) -> bool:
        """运行完整验证"""
        print("🔍 开始配置验证...")
        print("="*50)
        
        # 运行各项验证
        validations = [
            self.validate_adspower_config,
            self.validate_twitter_targets,
            self.validate_tweet_filters,
            self.validate_output_config,
            self.validate_browser_config,
            self.validate_log_config
        ]
        
        all_passed = True
        for validation in validations:
            try:
                if not validation():
                    all_passed = False
            except Exception as e:
                self.add_error(f"验证过程中出现异常: {e}")
                all_passed = False
        
        # 输出结果
        print("\n" + "="*50)
        print("📋 验证结果汇总")
        print("="*50)
        
        if self.errors:
            print("\n❌ 发现错误:")
            for error in self.errors:
                print(f"   {error}")
        
        if self.warnings:
            print("\n⚠️  警告信息:")
            for warning in self.warnings:
                print(f"   {warning}")
        
        if self.suggestions:
            print("\n💡 建议:")
            for suggestion in self.suggestions:
                print(f"   {suggestion}")
        
        if all_passed and not self.errors:
            print("\n✅ 所有配置验证通过！系统已准备就绪。")
        else:
            print("\n❌ 配置验证失败，请修复上述问题后重试。")
        
        return all_passed and len(self.errors) == 0

def main():
    """主函数"""
    print("🔧 Twitter 日报采集系统 - 配置验证工具")
    print("="*60)
    
    validator = ConfigValidator()
    success = validator.run_validation()
    
    if success:
        print("\n🚀 配置验证完成，可以开始使用系统！")
        print("\n使用方法:")
        print("   python3 run.py              # 快速启动")
        print("   python3 main.py             # 直接运行主程序")
    else:
        print("\n🔧 请修复配置问题后重新验证。")
        sys.exit(1)

if __name__ == "__main__":
    main()