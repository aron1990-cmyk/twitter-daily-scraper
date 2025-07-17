#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云端同步模块 - 支持Google Sheets和飞书文档API同步
"""

import requests
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import asyncio

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    gspread = None
    Credentials = None

try:
    import requests
except ImportError:
    requests = None

class CloudSyncManager:
    """
    云端同步管理器
    支持Google Sheets和飞书文档的数据同步
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger('CloudSync')
        self.google_client = None
        self.feishu_config = self.config.get('feishu', {})
        
    def setup_google_sheets(self, credentials_file: str, scopes: List[str] = None) -> bool:
        """
        设置Google Sheets连接
        
        Args:
            credentials_file: Google服务账号凭证文件路径
            scopes: API权限范围
            
        Returns:
            是否设置成功
        """
        if not gspread or not Credentials:
            self.logger.error("Google Sheets依赖未安装，请运行: pip install gspread google-auth")
            return False
            
        try:
            if scopes is None:
                scopes = [
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive'
                ]
            
            credentials = Credentials.from_service_account_file(
                credentials_file, scopes=scopes
            )
            self.google_client = gspread.authorize(credentials)
            self.logger.info("Google Sheets连接设置成功")
            return True
            
        except Exception as e:
            self.logger.error(f"Google Sheets设置失败: {e}")
            return False
    
    def sync_to_google_sheets(self, data: List[Dict[str, Any]], 
                             spreadsheet_id: str, 
                             worksheet_name: str = None) -> bool:
        """
        同步数据到Google Sheets
        
        Args:
            data: 要同步的数据
            spreadsheet_id: Google表格ID
            worksheet_name: 工作表名称
            
        Returns:
            是否同步成功
        """
        if not self.google_client:
            self.logger.error("Google Sheets未初始化")
            return False
            
        try:
            # 打开表格
            spreadsheet = self.google_client.open_by_key(spreadsheet_id)
            
            # 获取或创建工作表
            if worksheet_name:
                try:
                    worksheet = spreadsheet.worksheet(worksheet_name)
                except:
                    worksheet = spreadsheet.add_worksheet(
                        title=worksheet_name, rows=1000, cols=20
                    )
            else:
                worksheet = spreadsheet.sheet1
            
            # 清空现有数据
            worksheet.clear()
            
            if not data:
                self.logger.warning("没有数据需要同步")
                return True
            
            # 准备表头
            headers = [
                '序号', '用户名', '推文内容', '发布时间', '点赞数', 
                '评论数', '转发数', '链接', '标签', '筛选状态'
            ]
            
            # 准备数据行
            rows = [headers]
            for i, tweet in enumerate(data, 1):
                row = [
                    i,
                    tweet.get('username', ''),
                    tweet.get('content', ''),
                    tweet.get('timestamp', ''),
                    tweet.get('likes', 0),
                    tweet.get('comments', 0),
                    tweet.get('retweets', 0),
                    tweet.get('link', ''),
                    ', '.join(tweet.get('tags', [])),
                    tweet.get('filter_status', '')
                ]
                rows.append(row)
            
            # 批量更新数据
            worksheet.update('A1', rows)
            
            # 添加同步时间戳
            timestamp_cell = f"A{len(rows) + 2}"
            worksheet.update(timestamp_cell, f"最后同步时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            self.logger.info(f"成功同步 {len(data)} 条数据到Google Sheets")
            return True
            
        except Exception as e:
            self.logger.error(f"Google Sheets同步失败: {e}")
            return False
    
    def setup_feishu(self, app_id: str, app_secret: str) -> bool:
        """
        设置飞书应用配置
        
        Args:
            app_id: 飞书应用ID
            app_secret: 飞书应用密钥
            
        Returns:
            是否设置成功
        """
        if not requests:
            self.logger.error("requests依赖未安装，请运行: pip install requests")
            return False
            
        self.feishu_config = {
            'app_id': app_id,
            'app_secret': app_secret,
            'base_url': 'https://open.feishu.cn/open-apis'
        }
        self.logger.info("飞书配置设置成功")
        return True
    
    def get_feishu_access_token(self) -> Optional[str]:
        """
        获取飞书访问令牌
        
        Returns:
            访问令牌或None
        """
        if not self.feishu_config.get('app_id'):
            self.logger.error("飞书配置未设置")
            return None
            
        try:
            url = f"{self.feishu_config['base_url']}/auth/v3/tenant_access_token/internal"
            payload = {
                'app_id': self.feishu_config['app_id'],
                'app_secret': self.feishu_config['app_secret']
            }
            
            response = requests.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            if result.get('code') == 0:
                return result.get('tenant_access_token')
            else:
                self.logger.error(f"获取飞书令牌失败: {result.get('msg')}")
                return None
                
        except Exception as e:
            self.logger.error(f"获取飞书令牌异常: {e}")
            return None
    
    def sync_to_feishu(self, data: List[Dict[str, Any]], 
                      spreadsheet_token: str, 
                      table_id: str = None) -> bool:
        """
        同步数据到飞书多维表格
        
        Args:
            data: 要同步的数据
            spreadsheet_token: 飞书表格token
            table_id: 多维表格ID
            
        Returns:
            是否同步成功
        """
        access_token = self.get_feishu_access_token()
        if not access_token:
            return False
            
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # 获取表格字段信息以确定字段类型
            fields_url = f"{self.feishu_config['base_url']}/bitable/v1/apps/{spreadsheet_token}/tables/{table_id}/fields"
            fields_response = requests.get(fields_url, headers=headers)
            field_types = {}
            if fields_response.status_code == 200:
                fields_result = fields_response.json()
                if fields_result.get('code') == 0:
                    fields_data = fields_result.get('data', {}).get('items', [])
                    field_types = {field.get('field_name'): field.get('type') for field in fields_data}
            
            # 准备数据记录
            records = []
            for tweet in data:
                # 处理时间字段 - 根据字段类型决定格式
                publish_time = tweet.get('发布时间', '')
                create_time = tweet.get('创建时间', '')
                
                # 获取时间字段的类型（5=时间戳，1=文本）
                publish_time_type = field_types.get('发布时间', 5)  # 默认为时间戳类型
                create_time_type = field_types.get('创建时间', 1)   # 默认为文本类型
                
                # 处理发布时间
                if publish_time_type == 5:  # 时间戳类型
                    if isinstance(publish_time, str) and publish_time:
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(publish_time.replace('Z', '+00:00'))
                            publish_time = int(dt.timestamp() * 1000)
                        except:
                            publish_time = int(time.time() * 1000)
                    elif isinstance(publish_time, (int, float)):
                        if publish_time < 10000000000:  # 如果是秒时间戳，转换为毫秒
                            publish_time = int(publish_time * 1000)
                        else:
                            publish_time = int(publish_time)
                    else:
                        publish_time = int(time.time() * 1000)
                else:  # 文本类型
                    if isinstance(publish_time, str):
                        publish_time = publish_time
                    elif isinstance(publish_time, (int, float)):
                        from datetime import datetime
                        if publish_time > 10000000000:  # 毫秒时间戳
                            publish_time = datetime.fromtimestamp(publish_time / 1000).strftime('%Y-%m-%d %H:%M:%S')
                        else:  # 秒时间戳
                            publish_time = datetime.fromtimestamp(publish_time).strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        from datetime import datetime
                        publish_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # 处理创建时间 - 统一转换为字符串格式
                if isinstance(create_time, str) and create_time:
                    # 如果已经是字符串，保持原样
                    create_time = create_time
                elif isinstance(create_time, (int, float)):
                    # 如果是数字时间戳，转换为字符串格式
                    from datetime import datetime
                    if create_time > 10000000000:  # 毫秒时间戳
                        create_time = datetime.fromtimestamp(create_time / 1000).strftime('%Y-%m-%d %H:%M:%S')
                    else:  # 秒时间戳
                        create_time = datetime.fromtimestamp(create_time).strftime('%Y-%m-%d %H:%M:%S')
                else:
                    # 默认使用当前时间的字符串格式
                    from datetime import datetime
                    create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # 处理数值字段 - 确保数值字段为有效数字
                def safe_int(value, default=0):
                    """安全转换为整数"""
                    try:
                        if value is None or value == '':
                            return default
                        return int(float(str(value)))
                    except (ValueError, TypeError):
                        return default
                
                # 构建记录数据，只包含飞书表格中存在的字段
                record_fields = {
                    '推文原文内容': str(tweet.get('推文原文内容', '')),
                    '作者（账号）': str(tweet.get('作者（账号）', '')),
                    '推文链接': str(tweet.get('推文链接', '')),
                    '话题标签（Hashtag）': str(tweet.get('话题标签（Hashtag）', '')),
                    '类型标签': str(tweet.get('类型标签', '')),
                    '评论数': safe_int(tweet.get('评论数')),
                    '转发数': safe_int(tweet.get('转发数')),
                    '点赞数': safe_int(tweet.get('点赞数')),
                    '发布时间': publish_time
                }
                
                # 只有当创建时间字段在飞书表格中存在时才添加
                if '创建时间' in field_types:
                    record_fields['创建时间'] = create_time
                
                record = {'fields': record_fields}
                    
                records.append(record)
            
            # 批量创建记录
            url = f"{self.feishu_config['base_url']}/bitable/v1/apps/{spreadsheet_token}/tables/{table_id}/records/batch_create"
            payload = {
                'records': records
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            if result.get('code') == 0:
                self.logger.info(f"成功同步 {len(data)} 条数据到飞书多维表格")
                return True
            else:
                self.logger.error(f"飞书同步失败: {result.get('msg')}")
                return False
                
        except Exception as e:
            self.logger.error(f"飞书同步异常: {e}")
            return False
    
    def sync_to_feishu_sheet(self, data: List[Dict[str, Any]], 
                            spreadsheet_token: str, 
                            sheet_id: str = None) -> bool:
        """
        同步数据到飞书表格
        
        Args:
            data: 要同步的数据
            spreadsheet_token: 飞书表格token
            sheet_id: 工作表ID
            
        Returns:
            是否同步成功
        """
        access_token = self.get_feishu_access_token()
        if not access_token:
            return False
            
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # 如果没有指定sheet_id，获取第一个工作表
            if not sheet_id:
                url = f"{self.feishu_config['base_url']}/sheets/v3/spreadsheets/{spreadsheet_token}/sheets/query"
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                
                result = response.json()
                if result.get('code') == 0 and result.get('data', {}).get('sheets'):
                    sheet_id = result['data']['sheets'][0]['sheet_id']
                else:
                    self.logger.error("无法获取飞书工作表信息")
                    return False
            
            # 清空现有数据
            clear_url = f"{self.feishu_config['base_url']}/sheets/v2/spreadsheets/{spreadsheet_token}/values_batch_clear"
            clear_payload = {
                'ranges': [f'{sheet_id}!A:Z']
            }
            requests.post(clear_url, headers=headers, json=clear_payload)
            
            if not data:
                self.logger.warning("没有数据需要同步")
                return True
            
            # 准备数据
            values = [[
                '序号', '用户名', '推文内容', '发布时间', '评论数', 
                '转发数', '点赞数', '链接', '标签', '筛选状态'
            ]]
            
            for i, tweet in enumerate(data, 1):
                row = [
                    str(i),
                    tweet.get('username', ''),
                    tweet.get('content', ''),
                    tweet.get('timestamp', ''),
                    str(tweet.get('comments', 0)),
                    str(tweet.get('retweets', 0)),
                    str(tweet.get('likes', 0)),
                    tweet.get('link', ''),
                    ', '.join(tweet.get('tags', [])),
                    tweet.get('filter_status', '')
                ]
                values.append(row)
            
            # 批量更新数据
            update_url = f"{self.feishu_config['base_url']}/sheets/v2/spreadsheets/{spreadsheet_token}/values_batch_update"
            update_payload = {
                'value_ranges': [{
                    'range': f'{sheet_id}!A1:J{len(values)}',
                    'values': values
                }]
            }
            
            response = requests.post(update_url, headers=headers, json=update_payload)
            response.raise_for_status()
            
            result = response.json()
            if result.get('code') == 0:
                self.logger.info(f"成功同步 {len(data)} 条数据到飞书表格")
                return True
            else:
                self.logger.error(f"飞书同步失败: {result.get('msg')}")
                return False
                
        except Exception as e:
            self.logger.error(f"飞书同步异常: {e}")
            return False
    
    async def sync_all_platforms(self, data: List[Dict[str, Any]], 
                                sync_config: Dict[str, Any]) -> Dict[str, bool]:
        """
        同步到所有配置的平台
        
        Args:
            data: 要同步的数据
            sync_config: 同步配置
            
        Returns:
            各平台同步结果
        """
        results = {}
        
        # Google Sheets同步
        google_config = sync_config.get('google_sheets', {})
        if google_config.get('enabled', False):
            if self.setup_google_sheets(google_config.get('credentials_file')):
                results['google_sheets'] = self.sync_to_google_sheets(
                    data, 
                    google_config.get('spreadsheet_id'),
                    google_config.get('worksheet_name')
                )
            else:
                results['google_sheets'] = False
        
        # 飞书同步
        feishu_config = sync_config.get('feishu', {})
        if feishu_config.get('enabled', False):
            if self.setup_feishu(
                feishu_config.get('app_id'),
                feishu_config.get('app_secret')
            ):
                results['feishu'] = self.sync_to_feishu_sheet(
                    data,
                    feishu_config.get('spreadsheet_token'),
                    feishu_config.get('sheet_id')
                )
            else:
                results['feishu'] = False
        
        return results

# 使用示例
if __name__ == "__main__":
    # 示例配置
    sync_config = {
        'google_sheets': {
            'enabled': True,
            'credentials_file': 'path/to/google-credentials.json',
            'spreadsheet_id': 'your-google-spreadsheet-id',
            'worksheet_name': 'Twitter数据'
        },
        'feishu': {
            'enabled': True,
            'app_id': 'your-feishu-app-id',
            'app_secret': 'your-feishu-app-secret',
            'spreadsheet_token': 'your-feishu-spreadsheet-token',
            'sheet_id': 'your-sheet-id'  # 可选
        }
    }
    
    # 示例数据
    sample_data = [
        {
            'username': 'elonmusk',
            'content': 'Sample tweet content',
            'timestamp': '2024-01-01 12:00:00',
            'likes': 1000,
            'comments': 100,
            'retweets': 500,
            'link': 'https://twitter.com/elonmusk/status/123',
            'tags': ['AI', 'Technology'],
            'filter_status': 'passed'
        }
    ]
    
    # 创建同步管理器并执行同步
    sync_manager = CloudSyncManager()
    
    async def main():
        results = await sync_manager.sync_all_platforms(sample_data, sync_config)
        print(f"同步结果: {results}")
    
    asyncio.run(main())