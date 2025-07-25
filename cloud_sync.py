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
        print(f"🔑 [CloudSync] 开始获取飞书访问令牌")
        
        if not self.feishu_config.get('app_id'):
            print(f"❌ [CloudSync] 飞书配置未设置")
            self.logger.error("飞书配置未设置")
            return None
        
        print(f"   - App ID: {self.feishu_config['app_id']}")
        print(f"   - App Secret: {self.feishu_config['app_secret'][:10]}...")
        print(f"   - Base URL: {self.feishu_config['base_url']}")
            
        try:
            url = f"{self.feishu_config['base_url']}/auth/v3/tenant_access_token/internal"
            payload = {
                'app_id': self.feishu_config['app_id'],
                'app_secret': self.feishu_config['app_secret']
            }
            
            print(f"🌐 [CloudSync] 发送令牌请求")
            print(f"   - 请求URL: {url}")
            print(f"   - 请求载荷: {{'app_id': '{payload['app_id']}', 'app_secret': '***'}}")
            
            response = requests.post(url, json=payload, timeout=30)
            print(f"📊 [CloudSync] 令牌请求响应状态码: {response.status_code}")
            
            response.raise_for_status()
            
            result = response.json()
            print(f"📊 [CloudSync] 令牌响应解析: code={result.get('code')}, msg={result.get('msg', 'N/A')}")
            
            if result.get('code') == 0:
                token = result.get('tenant_access_token')
                print(f"✅ [CloudSync] 成功获取飞书访问令牌: {token[:10]}...")
                return token
            else:
                error_msg = f"获取飞书令牌失败: {result.get('msg')}"
                print(f"❌ [CloudSync] {error_msg}")
                self.logger.error(error_msg)
                return None
                
        except Exception as e:
            error_msg = f"获取飞书令牌异常: {e}"
            print(f"❌ [CloudSync] {error_msg}")
            self.logger.error(error_msg)
            import traceback
            print(f"   - 异常详情: {traceback.format_exc()}")
            return None
    
    def sync_to_feishu(self, data: List[Dict[str, Any]], 
                      spreadsheet_token: str, 
                      table_id: str = None,
                      max_retries: int = 3,
                      continue_on_failure: bool = True) -> bool:
        """
        同步数据到飞书多维表格
        
        Args:
            data: 要同步的数据
            spreadsheet_token: 飞书表格token
            table_id: 多维表格ID
            max_retries: 最大重试次数
            continue_on_failure: 失败时是否继续（不抛出异常）
            
        Returns:
            是否同步成功
        """
        self.logger.info(f"🚀 [CloudSync] 开始飞书同步流程")
        self.logger.info(f"   - 数据条数: {len(data)}")
        self.logger.info(f"   - 表格Token: {spreadsheet_token[:10]}...")
        self.logger.info(f"   - 表格ID: {table_id}")
        self.logger.info(f"   - 最大重试次数: {max_retries}")
        self.logger.info(f"   - 失败时继续执行: {continue_on_failure}")
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"🔑 [CloudSync] 尝试获取飞书访问令牌 (第{attempt + 1}次)")
                access_token = self.get_feishu_access_token()
                if not access_token:
                    if attempt < max_retries - 1:
                        self.logger.warning(f"⚠️ [CloudSync] 获取飞书令牌失败，{5}秒后重试 (尝试 {attempt + 1}/{max_retries})")
                        time.sleep(5)
                        continue
                    else:
                        if continue_on_failure:
                            self.logger.error("❌ [CloudSync] 飞书令牌获取失败，但继续执行任务")
                            return False
                        else:
                            self.logger.error("❌ [CloudSync] 飞书令牌获取失败，抛出异常")
                            raise Exception("无法获取飞书访问令牌")
                
                self.logger.info(f"✅ [CloudSync] 飞书访问令牌获取成功")
                result = self._execute_feishu_sync(data, spreadsheet_token, table_id, access_token)
                self.logger.info(f"📊 [CloudSync] 同步执行结果: {result}")
                return result
                
            except Exception as e:
                self.logger.error(f"❌ [CloudSync] 飞书同步失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                
                if attempt < max_retries - 1:
                    wait_time = 10 * (attempt + 1)  # 递增等待时间
                    self.logger.info(f"⏳ [CloudSync] {wait_time}秒后重试飞书同步")
                    time.sleep(wait_time)
                else:
                    if continue_on_failure:
                        self.logger.error("❌ [CloudSync] 飞书同步最终失败，但继续执行任务")
                        return False
                    else:
                        self.logger.error("❌ [CloudSync] 飞书同步最终失败，抛出异常")
                        raise e
        
        self.logger.error("❌ [CloudSync] 所有重试尝试都已用尽")
        return False
    
    def _execute_feishu_sync(self, data: List[Dict[str, Any]], 
                           spreadsheet_token: str, 
                           table_id: str,
                           access_token: str) -> bool:
        """
        执行飞书同步的核心逻辑
        
        Args:
            data: 要同步的数据
            spreadsheet_token: 飞书表格token
            table_id: 多维表格ID
            access_token: 访问令牌
            
        Returns:
            是否同步成功
        """
        try:
             self.logger.info(f"🔧 [CloudSync] 开始执行飞书同步核心逻辑")
             self.logger.info(f"   - 数据条数: {len(data)}")
             self.logger.info(f"   - 表格Token: {spreadsheet_token[:10]}...")
             self.logger.info(f"   - 表格ID: {table_id}")
             
             # 设置请求头
             headers = {
                 'Authorization': f'Bearer {access_token}',
                 'Content-Type': 'application/json'
             }
             self.logger.info(f"🔑 [CloudSync] 请求头设置完成")
             
             # 获取表格字段信息以确定字段类型
             self.logger.info(f"📋 [CloudSync] 开始获取飞书表格字段信息")
             fields_url = f"{self.feishu_config['base_url']}/bitable/v1/apps/{spreadsheet_token}/tables/{table_id}/fields"
             self.logger.info(f"   - 字段查询URL: {fields_url}")
             
             self.logger.info(f"🌐 发送字段查询请求...")
             fields_response = requests.get(fields_url, headers=headers, timeout=30)
             self.logger.info(f"   - 字段查询响应状态: {fields_response.status_code}")
             
             field_types = {}
             available_fields = []
             
             if fields_response.status_code == 200:
                 fields_result = fields_response.json()
                 self.logger.info(f"   - 字段查询响应解析: code={fields_result.get('code')}, msg={fields_result.get('msg', 'N/A')}")
                 
                 if fields_result.get('code') == 0:
                     fields_data = fields_result.get('data', {}).get('items', [])
                     field_types = {field.get('field_name'): field.get('type') for field in fields_data}
                     available_fields = [field.get('field_name') for field in fields_data]
                     self.logger.info(f"✅ 飞书表格字段信息获取成功:")
                     self.logger.info(f"   - 可用字段数量: {len(available_fields)}")
                     self.logger.info(f"   - 可用字段列表: {available_fields}")
                     self.logger.info(f"   - 字段类型映射: {field_types}")
                 else:
                     self.logger.error(f"❌ 获取字段信息失败: {fields_result.get('msg')}")
             else:
                 self.logger.error(f"❌ 获取字段信息请求失败: HTTP {fields_response.status_code}")
                 self.logger.error(f"   - 响应内容: {fields_response.text[:200]}...")
             
             # 准备数据记录
             self.logger.info(f"🔄 开始准备数据记录")
             self.logger.info(f"   - 待处理数据条数: {len(data)}")
             
             records = []
             skipped_fields = set()
             processed_fields = set()
             
             for idx, tweet in enumerate(data):
                 self.logger.info(f"   - 处理第 {idx + 1}/{len(data)} 条数据")
                 self.logger.debug(f"     - 原始数据字段: {list(tweet.keys())}")
                 
                 # 处理时间字段 - 根据字段类型决定格式
                 publish_time = tweet.get('发布时间', '')
                 create_time = tweet.get('创建时间', '')
                 
                 # 获取时间字段的类型（5=时间戳，1=文本）
                 publish_time_type = field_types.get('发布时间', 5)  # 默认为时间戳类型
                 create_time_type = field_types.get('创建时间', 1)   # 默认为文本类型
                 
                 # 处理发布时间 - 转换为Unix时间戳（飞书要求）
                 if isinstance(publish_time, str) and publish_time:
                     # 如果是字符串，尝试解析并转换为时间戳
                     try:
                         from datetime import datetime
                         if 'T' in publish_time:  # ISO格式
                             dt = datetime.fromisoformat(publish_time.replace('Z', '+00:00'))
                             publish_time = int(dt.timestamp())
                         else:
                             # 尝试解析常见格式
                             try:
                                 dt = datetime.strptime(publish_time, '%Y-%m-%d %H:%M:%S')
                                 publish_time = int(dt.timestamp())
                             except:
                                 # 如果解析失败，使用当前时间
                                 publish_time = int(datetime.now().timestamp())
                     except:
                         # 如果解析失败，使用当前时间
                         from datetime import datetime
                         publish_time = int(datetime.now().timestamp())
                 elif isinstance(publish_time, (int, float)) and publish_time > 0:
                     # 如果已经是数字，确保是秒级时间戳
                     if publish_time > 10000000000:  # 毫秒时间戳
                         publish_time = int(publish_time / 1000)
                     else:  # 秒时间戳
                         publish_time = int(publish_time)
                 else:
                     # 默认使用当前时间戳
                     from datetime import datetime
                     publish_time = int(datetime.now().timestamp())
                 
                 # 处理创建时间 - 转换为Unix时间戳（飞书要求）
                 if isinstance(create_time, str) and create_time:
                     # 如果是字符串，尝试解析并转换为时间戳
                     try:
                         from datetime import datetime
                         if 'T' in create_time:  # ISO格式
                             dt = datetime.fromisoformat(create_time.replace('Z', '+00:00'))
                             create_time = int(dt.timestamp())
                         else:
                             # 尝试解析常见格式
                             try:
                                 dt = datetime.strptime(create_time, '%Y-%m-%d %H:%M:%S')
                                 create_time = int(dt.timestamp())
                             except:
                                 # 如果解析失败，使用当前时间
                                 create_time = int(datetime.now().timestamp())
                     except:
                         # 如果解析失败，使用当前时间
                         from datetime import datetime
                         create_time = int(datetime.now().timestamp())
                 elif isinstance(create_time, (int, float)) and create_time > 0:
                     # 如果已经是数字，确保是秒级时间戳
                     if create_time > 10000000000:  # 毫秒时间戳
                         create_time = int(create_time / 1000)
                     else:  # 秒时间戳
                         create_time = int(create_time)
                 else:
                     # 默认使用当前时间戳
                     from datetime import datetime
                     create_time = int(datetime.now().timestamp())
                 
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
                 # 直接使用飞书表格中的实际字段名称进行映射
                 
                 # 根据飞书表格的实际字段名称进行映射
                 # 基于用户提供的飞书表格截图，字段包括：推文原文内容、数字式、评论、转发、点赞、创建时间等
                 all_possible_fields = {
                     # 推文内容字段 - 直接使用"推文原文内容"
                     '推文原文内容': str(tweet.get('推文原文内容', '') or tweet.get('推文原 文内容', '')),
                     
                     # 作者信息
                     '作者（账号）': str(tweet.get('作者（账号）', '')),
                     
                     # 链接信息
                     '推文链接': str(tweet.get('推文链接', '')),
                     
                     # 标签信息
                     '话题标签（Hashtag）': str(tweet.get('话题标签（Hashtag）', '')),
                     '类型标签': str(tweet.get('类型标签', '')),
                     
                     # 数值字段 - 直接使用字段名称
                     '评论': safe_int(tweet.get('评论数', 0) or tweet.get('评论', 0)),
                     '转发': safe_int(tweet.get('转发数', 0) or tweet.get('转发', 0)),
                     '点赞': safe_int(tweet.get('点赞数', 0) or tweet.get('点赞', 0)),
                     
                     # 时间字段 - 都使用Unix时间戳格式
                     '创建时间': create_time,  # Unix时间戳格式
                     '发布时间': publish_time  # Unix时间戳格式
                 }
                 
                 # 只保留飞书表格中实际存在的字段
                 record_fields = {}
                 for field_name, field_value in all_possible_fields.items():
                     if field_name in available_fields:
                         record_fields[field_name] = field_value
                         processed_fields.add(field_name)
                         self.logger.debug(f"     - 字段 {field_name}: {str(field_value)[:50]}...")
                     else:
                         skipped_fields.add(field_name)
                         self.logger.debug(f"     - 跳过字段 '{field_name}' (不存在于飞书表格)")
                 
                 self.logger.info(f"     - 第 {idx + 1} 条记录使用字段数: {len(record_fields)}")
                 self.logger.debug(f"     - 使用字段: {list(record_fields.keys())}")
                 
                 if record_fields:
                     record = {'fields': record_fields}
                     records.append(record)
                 else:
                     self.logger.warning(f"⚠️ 第 {idx + 1} 条数据没有匹配的字段，跳过")
             
             self.logger.info(f"✅ 数据记录准备完成:")
             self.logger.info(f"   - 原始数据条数: {len(data)}")
             self.logger.info(f"   - 有效记录数: {len(records)}")
             self.logger.info(f"   - 成功处理率: {len(records)/len(data)*100:.1f}%")
             self.logger.info(f"   - 处理的字段: {list(processed_fields)}")
             if skipped_fields:
                 self.logger.warning(f"⚠️ 跳过的字段 (不存在于飞书表格): {list(skipped_fields)}")
             
             # 检查是否有有效记录
             if not records:
                 self.logger.warning(f"⚠️ 没有有效的数据记录可以同步")
                 return False
             
             # 批量创建记录
             self.logger.info(f"📤 [CloudSync] 开始批量创建飞书记录")
             url = f"{self.feishu_config['base_url']}/bitable/v1/apps/{spreadsheet_token}/tables/{table_id}/records/batch_create"
             self.logger.info(f"   - 创建URL: {url}")
             
             payload = {
                 'records': records
             }
             self.logger.info(f"   - 记录数量: {len(records)}")
             self.logger.info(f"   - 载荷大小: {len(str(payload))} 字符")
             self.logger.info(f"   - 载荷示例: {str(payload)[:200]}...")
             
             self.logger.info(f"🌐 [CloudSync] 发送飞书API请求...")
             response = requests.post(url, headers=headers, json=payload, timeout=60)
             self.logger.info(f"📊 [CloudSync] 飞书API响应状态码: {response.status_code}")
             
             response.raise_for_status()
             
             result = response.json()
             self.logger.info(f"📊 [CloudSync] 飞书API响应解析: code={result.get('code')}, msg={result.get('msg', 'N/A')}")
             
             if result.get('code') == 0:
                 created_records = result.get('data', {}).get('records', [])
                 self.logger.info(f"✅ [CloudSync] 成功同步到飞书多维表格:")
                 self.logger.info(f"   - 原始数据条数: {len(data)}")
                 self.logger.info(f"   - 有效记录数: {len(records)}")
                 self.logger.info(f"   - 创建成功数: {len(created_records)}")
                 return True
             else:
                 self.logger.error(f"❌ [CloudSync] 飞书同步失败: {result.get('msg')}")
                 self.logger.error(f"   - 错误详情: {result}")
                 return False
                 
        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ 飞书同步网络请求异常:")
            self.logger.error(f"   - 异常类型: {type(e).__name__}")
            self.logger.error(f"   - 异常详情: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                self.logger.error(f"   - 响应状态码: {e.response.status_code}")
                self.logger.error(f"   - 响应内容: {e.response.text[:500]}...")
            raise e  # 重新抛出异常，让上层处理重试逻辑
        except Exception as e:
            self.logger.error(f"❌ 飞书同步过程中发生未知错误:")
            self.logger.error(f"   - 异常类型: {type(e).__name__}")
            self.logger.error(f"   - 异常详情: {str(e)}")
            import traceback
            self.logger.error(f"   - 异常堆栈: {traceback.format_exc()}")
            raise e  # 重新抛出异常，让上层处理重试逻辑
    
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
        self.logger.info(f"📊 开始飞书表格同步流程")
        self.logger.info(f"   - 表格Token: {spreadsheet_token[:10]}...")
        self.logger.info(f"   - 工作表ID: {sheet_id}")
        self.logger.info(f"   - 数据条数: {len(data)}")
        
        self.logger.info(f"🔑 获取飞书访问令牌")
        access_token = self.get_feishu_access_token()
        if not access_token:
            self.logger.error(f"❌ 飞书访问令牌获取失败")
            return False
        self.logger.info(f"✅ 飞书访问令牌获取成功")
            
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            self.logger.info(f"✅ 请求头设置完成")
            
            # 如果没有指定sheet_id，获取第一个工作表
            if not sheet_id:
                self.logger.info(f"🔍 未指定工作表ID，获取第一个工作表")
                url = f"{self.feishu_config['base_url']}/sheets/v3/spreadsheets/{spreadsheet_token}/sheets/query"
                self.logger.info(f"   - 查询URL: {url}")
                
                response = requests.get(url, headers=headers)
                self.logger.info(f"   - 响应状态码: {response.status_code}")
                response.raise_for_status()
                
                result = response.json()
                self.logger.info(f"   - 响应结果: code={result.get('code')}")
                
                if result.get('code') == 0 and result.get('data', {}).get('sheets'):
                    sheet_id = result['data']['sheets'][0]['sheet_id']
                    self.logger.info(f"✅ 获取到工作表ID: {sheet_id}")
                else:
                    self.logger.error(f"❌ 无法获取飞书工作表信息: {result.get('msg')}")
                    return False
            else:
                self.logger.info(f"ℹ️ 使用指定的工作表ID: {sheet_id}")
            
            # 清空现有数据
            self.logger.info(f"🧹 清空现有数据")
            clear_url = f"{self.feishu_config['base_url']}/sheets/v2/spreadsheets/{spreadsheet_token}/values_batch_clear"
            clear_payload = {
                'ranges': [f'{sheet_id}!A:Z']
            }
            self.logger.info(f"   - 清空URL: {clear_url}")
            self.logger.info(f"   - 清空范围: {clear_payload['ranges']}")
            
            clear_response = requests.post(clear_url, headers=headers, json=clear_payload)
            self.logger.info(f"   - 清空响应状态码: {clear_response.status_code}")
            
            if not data:
                self.logger.warning(f"⚠️ 没有数据需要同步")
                return True
            
            # 准备数据
            self.logger.info(f"🔄 开始准备表格数据")
            values = [[
                '序号', '用户名', '推文内容', '发布时间', '评论数', 
                '转发数', '点赞数', '链接', '标签', '筛选状态'
            ]]
            self.logger.info(f"   - 表头设置完成: {values[0]}")
            
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
                if i <= 3:  # 只记录前3行的详细信息
                    self.logger.debug(f"   - 第 {i} 行数据: {row[:3]}...")  # 只显示前3个字段
            
            self.logger.info(f"✅ 表格数据准备完成:")
            self.logger.info(f"   - 总行数: {len(values)} (包含表头)")
            self.logger.info(f"   - 数据行数: {len(values) - 1}")
            
            # 批量更新数据
            self.logger.info(f"📤 开始批量更新表格数据")
            update_url = f"{self.feishu_config['base_url']}/sheets/v2/spreadsheets/{spreadsheet_token}/values_batch_update"
            update_payload = {
                'value_ranges': [{
                    'range': f'{sheet_id}!A1:J{len(values)}',
                    'values': values
                }]
            }
            
            self.logger.info(f"   - 更新URL: {update_url}")
            self.logger.info(f"   - 更新范围: {update_payload['value_ranges'][0]['range']}")
            self.logger.info(f"   - 载荷大小: {len(values)} 行数据")
            
            self.logger.info(f"🌐 发送表格更新请求...")
            response = requests.post(update_url, headers=headers, json=update_payload)
            self.logger.info(f"   - 响应状态码: {response.status_code}")
            response.raise_for_status()
            
            result = response.json()
            self.logger.info(f"   - 响应结果: code={result.get('code')}, msg={result.get('msg', 'N/A')}")
            
            if result.get('code') == 0:
                self.logger.info(f"✅ 成功同步 {len(data)} 条数据到飞书表格")
                return True
            else:
                self.logger.error(f"❌ 飞书表格同步失败: {result.get('msg')}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ 飞书表格同步网络请求异常:")
            self.logger.error(f"   - 异常类型: {type(e).__name__}")
            self.logger.error(f"   - 异常详情: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                self.logger.error(f"   - 响应状态码: {e.response.status_code}")
                self.logger.error(f"   - 响应内容: {e.response.text[:500]}...")
            return False
        except Exception as e:
            self.logger.error(f"❌ 飞书表格同步过程中发生未知错误:")
            self.logger.error(f"   - 异常类型: {type(e).__name__}")
            self.logger.error(f"   - 异常详情: {str(e)}")
            import traceback
            self.logger.error(f"   - 异常堆栈: {traceback.format_exc()}")
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