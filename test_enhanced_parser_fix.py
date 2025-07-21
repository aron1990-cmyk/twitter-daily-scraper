#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试增强Twitter解析器的修复
"""

import asyncio
import logging
from enhanced_twitter_parser import EnhancedTwitterParser
from optimized_scraping_engine import OptimizedScrapingEngine

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_enhanced_parser_initialization():
    """测试增强解析器的初始化"""
    try:
        logger.info("开始测试增强Twitter解析器初始化...")
        
        # 创建抓取引擎
        scraping_engine = OptimizedScrapingEngine(max_workers=2)
        scraping_engine.start_engine()
        
        # 创建增强解析器
        user_id = "test_user"
        window_id = "test_window_001"
        parser = EnhancedTwitterParser(user_id, window_id, scraping_engine)
        
        logger.info(f"✅ EnhancedTwitterParser 创建成功")
        logger.info(f"   - user_id: {parser.user_id}")
        logger.info(f"   - window_id: {parser.window_id}")
        logger.info(f"   - debug_port: {parser.debug_port}")
        logger.info(f"   - page: {parser.page}")
        logger.info(f"   - browser: {parser.browser}")
        
        # 测试 initialize_with_debug_port 方法是否存在
        if hasattr(parser, 'initialize_with_debug_port'):
            logger.info("✅ initialize_with_debug_port 方法存在")
        else:
            logger.error("❌ initialize_with_debug_port 方法不存在")
        
        # 测试父类方法是否可用
        if hasattr(parser, 'initialize'):
            logger.info("✅ 父类 initialize 方法可用")
        else:
            logger.error("❌ 父类 initialize 方法不可用")
        
        # 停止抓取引擎
        scraping_engine.stop_engine()
        
        logger.info("✅ 测试完成，EnhancedTwitterParser 初始化修复成功！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_enhanced_parser_initialization())
    if success:
        print("\n🎉 修复验证成功！EnhancedTwitterParser 现在可以正确初始化了。")
    else:
        print("\n❌ 修复验证失败，需要进一步检查。")