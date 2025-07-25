#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书连接调试脚本
用于测试飞书API连接并输出详细的错误信息
"""

import requests
import json
import logging
from datetime import datetime

# 设置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_feishu_connection(app_id, app_secret, spreadsheet_token, table_id):
    """
    测试飞书连接
    """
    base_url = 'https://open.feishu.cn/open-apis'
    
    logger.info("=== 开始飞书连接测试 ===")
    logger.info(f"App ID: {app_id}")
    logger.info(f"App Secret: {app_secret[:10]}...")
    logger.info(f"Spreadsheet Token: {spreadsheet_token}")
    logger.info(f"Table ID: {table_id}")
    
    try:
        # 步骤1: 获取访问令牌
        logger.info("\n步骤1: 获取访问令牌")
        token_url = f"{base_url}/auth/v3/tenant_access_token/internal"
        token_payload = {
            'app_id': app_id,
            'app_secret': app_secret
        }
        
        logger.info(f"请求URL: {token_url}")
        logger.info(f"请求数据: {token_payload}")
        
        token_response = requests.post(token_url, json=token_payload, timeout=30)
        logger.info(f"响应状态码: {token_response.status_code}")
        logger.info(f"响应头: {dict(token_response.headers)}")
        logger.info(f"响应内容: {token_response.text}")
        
        if token_response.status_code != 200:
            logger.error(f"获取令牌失败: HTTP {token_response.status_code}")
            return False
            
        token_result = token_response.json()
        if token_result.get('code') != 0:
            logger.error(f"获取令牌失败: {token_result.get('msg')}")
            logger.error(f"错误代码: {token_result.get('code')}")
            return False
            
        access_token = token_result.get('tenant_access_token')
        logger.info(f"✅ 访问令牌获取成功: {access_token[:20]}...")
        
        # 步骤2: 获取表格字段信息
        logger.info("\n步骤2: 获取表格字段信息")
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        fields_url = f"{base_url}/bitable/v1/apps/{spreadsheet_token}/tables/{table_id}/fields"
        logger.info(f"请求URL: {fields_url}")
        logger.info(f"请求头: {headers}")
        
        fields_response = requests.get(fields_url, headers=headers, timeout=30)
        logger.info(f"响应状态码: {fields_response.status_code}")
        logger.info(f"响应内容: {fields_response.text}")
        
        if fields_response.status_code != 200:
            logger.error(f"获取字段信息失败: HTTP {fields_response.status_code}")
            return False
            
        fields_result = fields_response.json()
        if fields_result.get('code') != 0:
            logger.error(f"获取字段信息失败: {fields_result.get('msg')}")
            logger.error(f"错误代码: {fields_result.get('code')}")
            return False
            
        fields_data = fields_result.get('data', {}).get('items', [])
        logger.info(f"✅ 字段信息获取成功，共 {len(fields_data)} 个字段")
        
        for field in fields_data:
            logger.info(f"  - {field.get('field_name')}: {field.get('type')}")
        
        # 步骤3: 发送测试数据
        logger.info("\n步骤3: 发送测试数据")
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        test_record = {
            'fields': {
                '推文原文内容': '测试连接 - ' + current_time,
                '发布时间': current_time,
                '作者（账号）': 'test_user',
                '推文链接': 'https://twitter.com/test',
                '话题标签（Hashtag）': '#测试',
                '类型标签': '测试',
                '评论': 0,
                '转发': 0,
                '点赞': 0,
                '创建时间': current_time
            }
        }
        
        records_url = f"{base_url}/bitable/v1/apps/{spreadsheet_token}/tables/{table_id}/records"
        records_payload = {
            'records': [test_record]
        }
        
        logger.info(f"请求URL: {records_url}")
        logger.info(f"请求数据: {json.dumps(records_payload, ensure_ascii=False, indent=2)}")
        
        records_response = requests.post(records_url, headers=headers, json=records_payload, timeout=30)
        logger.info(f"响应状态码: {records_response.status_code}")
        logger.info(f"响应内容: {records_response.text}")
        
        if records_response.status_code != 200:
            logger.error(f"发送测试数据失败: HTTP {records_response.status_code}")
            return False
            
        records_result = records_response.json()
        if records_result.get('code') != 0:
            logger.error(f"发送测试数据失败: {records_result.get('msg')}")
            logger.error(f"错误代码: {records_result.get('code')}")
            return False
            
        logger.info("✅ 测试数据发送成功")
        logger.info("=== 飞书连接测试完成 ===")
        return True
        
    except requests.exceptions.Timeout:
        logger.error("❌ 请求超时")
        return False
    except requests.exceptions.ConnectionError:
        logger.error("❌ 连接错误")
        return False
    except Exception as e:
        logger.error(f"❌ 测试过程中发生异常: {e}")
        logger.exception("详细错误信息:")
        return False

if __name__ == '__main__':
    # 使用真实配置数据
    app_id = 'cli_a8f94354c178900b'
    app_secret = 'HGQGTQyvr2QsWVmPMdY8Oe7A67J3ihVV'
    spreadsheet_token = 'V862biEswatwnRsGalochUI6n6d'
    table_id = 'tblicDZl35dn2vZ9'
    
    success = test_feishu_connection(app_id, app_secret, spreadsheet_token, table_id)
    
    if success:
        print("\n🎉 飞书连接测试成功！")
    else:
        print("\n❌ 飞书连接测试失败！")