#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书数据验证器
用于在数据同步后，获取飞书中的数据并与本地数据进行比对验证
确保数据同步的准确性和完整性
"""

import os
import sys
import json
import requests
from datetime import datetime
from typing import List, Dict, Any, Tuple
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_app import app, db, TweetData, FEISHU_CONFIG
from cloud_sync import CloudSyncManager

class FeishuDataValidator:
    """
    飞书数据验证器
    负责获取飞书数据并与本地数据进行比对
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.feishu_config = FEISHU_CONFIG
        # 构建正确的配置格式，确保包含所有必需字段
        feishu_config_with_base_url = dict(self.feishu_config)
        if 'base_url' not in feishu_config_with_base_url:
            feishu_config_with_base_url['base_url'] = 'https://open.feishu.cn/open-apis'
        
        config = {
            'feishu': feishu_config_with_base_url
        }
        self.sync_manager = CloudSyncManager(config)
        
    def get_feishu_access_token(self) -> str:
        """
        获取飞书访问令牌
        
        Returns:
            访问令牌字符串，失败返回None
        """
        return self.sync_manager.get_feishu_access_token()
    
    def get_feishu_table_fields(self, access_token: str) -> Dict[str, Any]:
        """
        获取飞书表格字段信息
        
        Args:
            access_token: 飞书访问令牌
            
        Returns:
            字段信息字典，包含字段名到ID的映射和字段类型
        """
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.feishu_config['spreadsheet_token']}/tables/{self.feishu_config['table_id']}/fields"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            result = response.json()
            
            if result.get('code') == 0:
                fields_data = result.get('data', {}).get('items', [])
                
                field_name_to_id = {}
                field_types = {}
                field_id_to_name = {}
                
                for field in fields_data:
                    field_name = field.get('field_name', '')
                    field_id = field.get('field_id', '')
                    field_type = field.get('type', 1)
                    
                    field_name_to_id[field_name] = field_id
                    field_types[field_name] = field_type
                    field_id_to_name[field_id] = field_name
                
                return {
                    'field_name_to_id': field_name_to_id,
                    'field_types': field_types,
                    'field_id_to_name': field_id_to_name,
                    'fields_data': fields_data
                }
            else:
                self.logger.error(f"获取飞书表格字段失败: {result}")
                return {}
        except Exception as e:
            self.logger.error(f"获取飞书表格字段异常: {e}")
            return {}
    
    def get_feishu_table_records(self, access_token: str, page_size: int = 100) -> List[Dict[str, Any]]:
        """
        获取飞书表格记录
        
        Args:
            access_token: 飞书访问令牌
            page_size: 每页记录数
            
        Returns:
            记录列表
        """
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.feishu_config['spreadsheet_token']}/tables/{self.feishu_config['table_id']}/records"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        all_records = []
        page_token = None
        
        try:
            while True:
                params = {"page_size": page_size}
                if page_token:
                    params["page_token"] = page_token
                
                response = requests.get(url, headers=headers, params=params, timeout=30)
                result = response.json()
                
                if result.get('code') == 0:
                    data = result.get('data', {})
                    records = data.get('items', [])
                    all_records.extend(records)
                    
                    # 检查是否有下一页
                    page_token = data.get('page_token')
                    if not page_token:
                        break
                else:
                    self.logger.error(f"获取飞书表格记录失败: {result}")
                    break
                    
        except Exception as e:
            self.logger.error(f"获取飞书表格记录异常: {e}")
            
        return all_records
    
    def parse_feishu_records(self, records: List[Dict[str, Any]], field_mapping: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        解析飞书记录数据
        
        Args:
            records: 飞书原始记录列表
            field_mapping: 字段ID到字段名的映射（可能不需要，因为字段可能已经是名称）
            
        Returns:
            解析后的记录列表
        """
        parsed_records = []
        
        for record in records:
            record_id = record.get('record_id', '')
            created_time = record.get('created_time', 0)
            fields_data = record.get('fields', {})
            
            parsed_record = {
                'record_id': record_id,
                'created_time': created_time,
                'fields': {}
            }
            
            # 解析字段数据
            for field_key, field_value in fields_data.items():
                # 检查字段键是否已经是字段名（中文）还是字段ID
                if field_key in field_mapping.values():  # 如果是字段名
                    field_name = field_key
                elif field_key in field_mapping:  # 如果是字段ID
                    field_name = field_mapping[field_key]
                else:
                    field_name = field_key  # 直接使用原始键名
                
                parsed_record['fields'][field_name] = field_value
            
            parsed_records.append(parsed_record)
        
        return parsed_records
    
    def get_local_sync_data(self, task_id: int = None) -> List[Dict[str, Any]]:
        """
        获取本地同步的数据
        
        Args:
            task_id: 任务ID，如果为None则获取所有数据
            
        Returns:
            本地数据列表
        """
        try:
            with app.app_context():
                if task_id:
                    tweets = TweetData.query.filter_by(task_id=task_id).all()
                else:
                    tweets = TweetData.query.all()
                
                local_data = []
                for tweet in tweets:
                    # 构建与飞书同步格式一致的数据
                    tweet_data = {
                        'id': tweet.id,
                        'task_id': tweet.task_id,
                        '推文原文内容': tweet.content or '',
                        '作者（账号）': tweet.username or '',
                        '推文链接': tweet.link or '',
                        '话题标签（Hashtag）': tweet.hashtags or '',
                        '类型标签': tweet.content_type or '',
                        '评论': tweet.comments or 0,
                        '点赞': tweet.likes or 0,
                        '转发': tweet.retweets or 0,
                        '发布时间': int(tweet.scraped_at.timestamp() * 1000) if tweet.scraped_at else 0
                    }
                    local_data.append(tweet_data)
                
                return local_data
        except Exception as e:
            self.logger.error(f"获取本地数据异常: {e}")
            return []
    
    def compare_data(self, local_data: List[Dict[str, Any]], feishu_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        比对本地数据和飞书数据
        
        Args:
            local_data: 本地数据列表
            feishu_data: 飞书数据列表
            
        Returns:
            比对结果字典
        """
        comparison_result = {
            'local_count': len(local_data),
            'feishu_count': len(feishu_data),
            'matched_records': [],
            'missing_in_feishu': [],
            'extra_in_feishu': [],
            'field_mismatches': [],
            'summary': {}
        }
        
        # 创建本地数据的内容索引（用推文原文内容作为唯一标识）
        local_content_map = {}
        for local_record in local_data:
            content = local_record.get('推文原文内容', '').strip()
            if content:
                local_content_map[content] = local_record
        
        # 创建飞书数据的内容索引
        feishu_content_map = {}
        for feishu_record in feishu_data:
            content = feishu_record.get('fields', {}).get('推文原文内容', '').strip()
            if content:
                feishu_content_map[content] = feishu_record
        
        # 查找匹配的记录
        for content, local_record in local_content_map.items():
            if content in feishu_content_map:
                feishu_record = feishu_content_map[content]
                
                # 比对字段值
                field_matches = self._compare_record_fields(local_record, feishu_record)
                
                comparison_result['matched_records'].append({
                    'content': content[:100] + '...' if len(content) > 100 else content,
                    'local_record': local_record,
                    'feishu_record': feishu_record,
                    'field_matches': field_matches
                })
                
                # 记录字段不匹配的情况
                if not field_matches['all_match']:
                    comparison_result['field_mismatches'].append({
                        'content': content[:100] + '...' if len(content) > 100 else content,
                        'mismatched_fields': field_matches['mismatched_fields']
                    })
            else:
                # 本地有但飞书没有的记录
                comparison_result['missing_in_feishu'].append({
                    'content': content[:100] + '...' if len(content) > 100 else content,
                    'local_record': local_record
                })
        
        # 查找飞书中多出的记录
        for content, feishu_record in feishu_content_map.items():
            if content not in local_content_map:
                comparison_result['extra_in_feishu'].append({
                    'content': content[:100] + '...' if len(content) > 100 else content,
                    'feishu_record': feishu_record
                })
        
        # 生成摘要
        comparison_result['summary'] = {
            'total_local': len(local_data),
            'total_feishu': len(feishu_data),
            'matched_count': len(comparison_result['matched_records']),
            'missing_in_feishu_count': len(comparison_result['missing_in_feishu']),
            'extra_in_feishu_count': len(comparison_result['extra_in_feishu']),
            'field_mismatch_count': len(comparison_result['field_mismatches']),
            'sync_accuracy': len(comparison_result['matched_records']) / len(local_data) * 100 if local_data else 0
        }
        
        return comparison_result
    
    def _compare_record_fields(self, local_record: Dict[str, Any], feishu_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        比对单条记录的字段值
        
        Args:
            local_record: 本地记录
            feishu_record: 飞书记录
            
        Returns:
            字段比对结果
        """
        feishu_fields = feishu_record.get('fields', {})
        
        # 需要比对的字段
        compare_fields = [
            '推文原文内容', '作者（账号）', '推文链接', '话题标签（Hashtag）',
            '类型标签', '评论', '点赞', '转发'
        ]
        
        matched_fields = []
        mismatched_fields = []
        
        for field_name in compare_fields:
            local_value = local_record.get(field_name, '')
            feishu_value = feishu_fields.get(field_name, '')
            
            # 数值字段特殊处理
            if field_name in ['评论', '点赞', '转发']:
                local_value = int(local_value) if local_value else 0
                feishu_value = int(feishu_value) if feishu_value else 0
            else:
                local_value = str(local_value).strip()
                feishu_value = str(feishu_value).strip()
            
            if local_value == feishu_value:
                matched_fields.append(field_name)
            else:
                mismatched_fields.append({
                    'field': field_name,
                    'local_value': local_value,
                    'feishu_value': feishu_value
                })
        
        return {
            'all_match': len(mismatched_fields) == 0,
            'matched_fields': matched_fields,
            'mismatched_fields': mismatched_fields
        }
    
    def validate_sync_data(self, task_id: int = None) -> Dict[str, Any]:
        """
        验证同步数据的完整性和准确性
        
        Args:
            task_id: 任务ID，如果为None则验证所有数据
            
        Returns:
            验证结果字典
        """
        print(f"\n{'='*80}")
        print(f"🔍 开始飞书数据验证流程")
        print(f"📋 验证参数:")
        print(f"   - 任务ID: {task_id if task_id else '全部任务'}")
        print(f"   - 验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}")
        
        self.logger.info(f"🔍 开始飞书数据验证流程，任务ID: {task_id}")
        
        try:
            # 0. 检查飞书配置完整性
            print(f"\n🔧 步骤0: 检查飞书配置")
            required_fields = ['app_id', 'app_secret', 'spreadsheet_token', 'table_id']
            missing_fields = [field for field in required_fields if not self.feishu_config.get(field)]
            
            if missing_fields:
                error_msg = f"飞书配置不完整，缺少字段: {', '.join(missing_fields)}"
                print(f"❌ {error_msg}")
                self.logger.error(error_msg)
                return {'success': False, 'error': error_msg}
            
            if not self.feishu_config.get('enabled', False):
                error_msg = "飞书同步功能未启用，请在系统配置中启用飞书同步"
                print(f"❌ {error_msg}")
                self.logger.error(error_msg)
                return {'success': False, 'error': error_msg}
            
            print(f"✅ 飞书配置检查通过")
            print(f"   - App ID: {self.feishu_config['app_id'][:10]}...")
            print(f"   - 表格Token: {self.feishu_config['spreadsheet_token'][:10]}...")
            print(f"   - 表格ID: {self.feishu_config['table_id']}")
            print(f"   - 启用状态: {self.feishu_config.get('enabled', False)}")
            
            # 1. 获取飞书访问令牌
            print(f"\n🔑 步骤1: 获取飞书访问令牌")
            access_token = self.get_feishu_access_token()
            if not access_token:
                error_msg = "无法获取飞书访问令牌"
                print(f"❌ {error_msg}")
                self.logger.error(error_msg)
                return {'success': False, 'error': error_msg}
            print(f"✅ 访问令牌获取成功")
            
            # 2. 获取飞书表格字段信息
            print(f"\n📋 步骤2: 获取飞书表格字段信息")
            field_info = self.get_feishu_table_fields(access_token)
            if not field_info:
                error_msg = "无法获取飞书表格字段信息"
                print(f"❌ {error_msg}")
                self.logger.error(error_msg)
                return {'success': False, 'error': error_msg}
            
            field_id_to_name = field_info['field_id_to_name']
            print(f"✅ 获取到 {len(field_id_to_name)} 个字段")
            
            # 3. 获取飞书表格记录
            print(f"\n📊 步骤3: 获取飞书表格记录")
            feishu_records = self.get_feishu_table_records(access_token)
            print(f"✅ 获取到 {len(feishu_records)} 条飞书记录")
            
            # 4. 解析飞书记录
            print(f"\n🔄 步骤4: 解析飞书记录")
            parsed_feishu_data = self.parse_feishu_records(feishu_records, field_id_to_name)
            print(f"✅ 解析完成 {len(parsed_feishu_data)} 条记录")
            
            # 5. 获取本地数据
            print(f"\n💾 步骤5: 获取本地数据")
            local_data = self.get_local_sync_data(task_id)
            print(f"✅ 获取到 {len(local_data)} 条本地记录")
            
            # 6. 数据比对
            print(f"\n🔍 步骤6: 数据比对分析")
            comparison_result = self.compare_data(local_data, parsed_feishu_data)
            
            # 7. 输出比对结果
            self._print_comparison_result(comparison_result)
            
            return {
                'success': True,
                'comparison_result': comparison_result,
                'field_info': field_info,
                'validation_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"数据验证过程中发生异常: {e}"
            print(f"❌ {error_msg}")
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg}
    
    def _print_comparison_result(self, result: Dict[str, Any]):
        """
        打印比对结果
        
        Args:
            result: 比对结果字典
        """
        summary = result['summary']
        
        print(f"\n📊 数据比对结果摘要:")
        print(f"   - 本地记录数: {summary['total_local']}")
        print(f"   - 飞书记录数: {summary['total_feishu']}")
        print(f"   - 匹配记录数: {summary['matched_count']}")
        print(f"   - 飞书缺失记录数: {summary['missing_in_feishu_count']}")
        print(f"   - 飞书多余记录数: {summary['extra_in_feishu_count']}")
        print(f"   - 字段不匹配记录数: {summary['field_mismatch_count']}")
        print(f"   - 同步准确率: {summary['sync_accuracy']:.2f}%")
        
        # 显示详细的不匹配信息
        if result['missing_in_feishu']:
            print(f"\n❌ 飞书中缺失的记录 ({len(result['missing_in_feishu'])} 条):")
            for i, missing in enumerate(result['missing_in_feishu'][:5]):
                print(f"   {i+1}. {missing['content']}")
            if len(result['missing_in_feishu']) > 5:
                print(f"   ... 还有 {len(result['missing_in_feishu']) - 5} 条")
        
        if result['extra_in_feishu']:
            print(f"\n⚠️ 飞书中多余的记录 ({len(result['extra_in_feishu'])} 条):")
            for i, extra in enumerate(result['extra_in_feishu'][:5]):
                print(f"   {i+1}. {extra['content']}")
            if len(result['extra_in_feishu']) > 5:
                print(f"   ... 还有 {len(result['extra_in_feishu']) - 5} 条")
        
        if result['field_mismatches']:
            print(f"\n🔄 字段值不匹配的记录 ({len(result['field_mismatches'])} 条):")
            for i, mismatch in enumerate(result['field_mismatches'][:3]):
                print(f"   {i+1}. {mismatch['content']}")
                for field_mismatch in mismatch['mismatched_fields'][:3]:
                    print(f"      - {field_mismatch['field']}: 本地='{field_mismatch['local_value']}' vs 飞书='{field_mismatch['feishu_value']}'")
            if len(result['field_mismatches']) > 3:
                print(f"   ... 还有 {len(result['field_mismatches']) - 3} 条")
        
        # 总体评估
        if summary['sync_accuracy'] >= 95:
            print(f"\n✅ 数据同步质量: 优秀 (准确率 {summary['sync_accuracy']:.2f}%)")
        elif summary['sync_accuracy'] >= 85:
            print(f"\n⚠️ 数据同步质量: 良好 (准确率 {summary['sync_accuracy']:.2f}%)")
        else:
            print(f"\n❌ 数据同步质量: 需要改进 (准确率 {summary['sync_accuracy']:.2f}%)")

def main():
    """
    主函数 - 执行数据验证
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='飞书数据验证器')
    parser.add_argument('--task-id', type=int, help='指定任务ID进行验证')
    parser.add_argument('--verbose', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建验证器并执行验证
    validator = FeishuDataValidator()
    result = validator.validate_sync_data(task_id=args.task_id)
    
    if result['success']:
        print(f"\n🎉 数据验证完成")
    else:
        print(f"\n❌ 数据验证失败: {result.get('error', '未知错误')}")
        sys.exit(1)

if __name__ == "__main__":
    main()