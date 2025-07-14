#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证代码质量改进功能
"""

import sys
import os
from pathlib import Path

def test_imports():
    """测试新模块导入"""
    print("🔍 测试模块导入...")
    
    modules_to_test = [
        'exceptions',
        'models', 
        'retry_utils',
        'monitoring',
        'performance_optimizer'
    ]
    
    success_count = 0
    
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✅ {module} 导入成功")
            success_count += 1
        except ImportError as e:
            print(f"❌ {module} 导入失败: {e}")
        except Exception as e:
            print(f"⚠️ {module} 导入异常: {e}")
    
    return success_count, len(modules_to_test)

def test_exception_classes():
    """测试异常类"""
    print("\n🚨 测试异常处理...")
    
    try:
        from exceptions import (
            TwitterScrapingError,
            ConfigurationError,
            BrowserError,
            DataValidationError,
            RetryExhaustedError
        )
        
        # 测试异常创建
        error = TwitterScrapingError("测试错误", "TEST_001")
        print(f"✅ 异常类创建成功: {error}")
        
        return True
    except Exception as e:
        print(f"❌ 异常类测试失败: {e}")
        return False

def test_data_models():
    """测试数据模型"""
    print("\n📊 测试数据模型...")
    
    try:
        from models import TweetData, UserData, ScrapingConfig
        
        # 测试模型创建
        tweet = TweetData(
            username="test_user",
            content="测试推文",
            likes=10,
            retweets=5,
            comments=2
        )
        
        print(f"✅ 数据模型创建成功: {tweet.content}")
        return True
    except Exception as e:
        print(f"❌ 数据模型测试失败: {e}")
        return False

def test_retry_utils():
    """测试重试工具"""
    print("\n🔄 测试重试机制...")
    
    try:
        from retry_utils import RetryConfig, exponential_backoff
        
        # 测试重试配置
        config = RetryConfig(max_attempts=3, base_delay=1.0)
        print(f"✅ 重试配置创建成功: {config.max_attempts} 次尝试")
        
        # 测试退避算法
        delay = exponential_backoff(1, 2.0, 1.0)
        print(f"✅ 退避算法计算成功: {delay}s")
        
        return True
    except Exception as e:
        print(f"❌ 重试工具测试失败: {e}")
        return False

def test_monitoring():
    """测试监控系统"""
    print("\n📊 测试监控系统...")
    
    try:
        from monitoring import MonitoringSystem
        
        # 测试监控系统
        monitoring = MonitoringSystem()
        monitoring.start()
        print("✅ 监控系统创建成功")
        
        # 测试状态获取
        status = monitoring.get_status()
        print("✅ 状态获取成功")
        
        return True
    except Exception as e:
        print(f"❌ 监控系统测试失败: {e}")
        return False

def test_performance_optimizer():
    """测试性能优化器"""
    print("\n⚡ 测试性能优化器...")
    
    try:
        from performance_optimizer import (
            AsyncBatchProcessor,
            MemoryOptimizer,
            PerformanceProfiler
        )
        
        # 测试批处理器
        processor = AsyncBatchProcessor(batch_size=10)
        print("✅ 批处理器创建成功")
        
        # 测试内存优化器
        optimizer = MemoryOptimizer(max_memory_mb=512)
        print("✅ 内存优化器创建成功")
        
        # 测试性能分析器
        profiler = PerformanceProfiler()
        print("✅ 性能分析器创建成功")
        
        return True
    except Exception as e:
        print(f"❌ 性能优化器测试失败: {e}")
        return False

def check_file_structure():
    """检查文件结构"""
    print("\n📁 检查文件结构...")
    
    required_files = [
        'exceptions.py',
        'models.py',
        'retry_utils.py', 
        'monitoring.py',
        'performance_optimizer.py',
        'quality_check.py',
        'pyproject.toml',
        '.flake8',
        '.pre-commit-config.yaml',
        'tests/conftest.py',
        'tests/test_models.py'
    ]
    
    existing_files = []
    missing_files = []
    
    for file_path in required_files:
        if Path(file_path).exists():
            existing_files.append(file_path)
            print(f"✅ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"❌ {file_path} (缺失)")
    
    return len(existing_files), len(required_files)

def main():
    """主函数"""
    print("🚀 开始验证代码质量改进功能...\n")
    
    # 测试结果统计
    total_tests = 0
    passed_tests = 0
    
    # 检查文件结构
    existing, total_files = check_file_structure()
    print(f"\n📊 文件结构: {existing}/{total_files} 文件存在")
    
    # 测试模块导入
    import_success, import_total = test_imports()
    total_tests += import_total
    passed_tests += import_success
    
    # 测试各个功能模块
    test_functions = [
        test_exception_classes,
        test_data_models,
        test_retry_utils,
        test_monitoring,
        test_performance_optimizer
    ]
    
    for test_func in test_functions:
        total_tests += 1
        if test_func():
            passed_tests += 1
    
    # 输出总结
    print(f"\n📊 测试总结:")
    print(f"✅ 通过: {passed_tests}/{total_tests} 项测试")
    print(f"📁 文件: {existing}/{total_files} 个文件存在")
    
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    print(f"🎯 成功率: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("\n🎉 代码质量改进功能验证成功！")
        return 0
    else:
        print("\n⚠️ 部分功能需要进一步完善")
        return 1

if __name__ == "__main__":
    sys.exit(main())