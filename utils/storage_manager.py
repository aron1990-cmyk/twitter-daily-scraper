#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
存储管理模块 - 负责推文数据的持久化存储
支持JSON、CSV、Excel等多种格式
"""

import os
import json
import csv
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import pandas as pd


class StorageManager:
    """存储管理器 - 处理推文数据的持久化存储"""
    
    def __init__(self, base_dir: str = "./data"):
        self.base_dir = Path(base_dir)
        self.logger = logging.getLogger(__name__)
        
        # 创建必要的目录结构
        self._create_directory_structure()
    
    def _create_directory_structure(self):
        """创建目录结构"""
        directories = [
            self.base_dir / "tweets",
            self.base_dir / "accounts", 
            self.base_dir / "exports",
            self.base_dir / "logs"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"确保目录存在: {directory}")
    
    def get_date_directory(self, date: datetime = None) -> Path:
        """获取按日期分组的目录"""
        if date is None:
            date = datetime.now()
        
        date_str = date.strftime("%Y-%m-%d")
        date_dir = self.base_dir / "tweets" / date_str
        date_dir.mkdir(parents=True, exist_ok=True)
        
        return date_dir
    
    async def save_user_tweets(self, username: str, tweets: List[Dict[str, Any]], 
                              metadata: Dict[str, Any] = None) -> str:
        """
        保存单个用户的推文数据
        
        Args:
            username: 用户名
            tweets: 推文数据列表
            metadata: 元数据信息
            
        Returns:
            保存的文件路径
        """
        try:
            # 获取日期目录
            date_dir = self.get_date_directory()
            
            # 构建文件名
            filename = f"{username}_tweets.json"
            filepath = date_dir / filename
            
            # 准备保存的数据
            save_data = {
                "metadata": {
                    "username": username,
                    "scraped_at": datetime.now().isoformat(),
                    "total_tweets": len(tweets),
                    "scraping_duration": metadata.get("duration", 0) if metadata else 0,
                    "status": "success"
                },
                "tweets": tweets
            }
            
            # 如果有额外的元数据，合并进去
            if metadata:
                save_data["metadata"].update(metadata)
            
            # 保存JSON文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"用户 @{username} 的推文数据已保存到: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"保存用户 @{username} 的推文数据失败: {e}")
            raise
    
    async def save_batch_summary(self, scraping_result, usernames: List[str]) -> str:
        """
        保存批次抓取摘要
        
        Args:
            scraping_result: 抓取结果对象
            usernames: 用户名列表
            
        Returns:
            保存的文件路径
        """
        try:
            # 获取日期目录
            date_dir = self.get_date_directory()
            
            # 构建摘要数据
            summary_data = {
                "batch_info": {
                    "batch_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
                    "start_time": scraping_result.start_time.isoformat(),
                    "end_time": scraping_result.end_time.isoformat() if scraping_result.end_time else None,
                    "duration_seconds": scraping_result.duration,
                    "target_usernames": usernames
                },
                "statistics": {
                    "total_users": scraping_result.total_users,
                    "successful_users": scraping_result.successful_users,
                    "failed_users": scraping_result.failed_users,
                    "success_rate": scraping_result.success_rate,
                    "total_tweets": scraping_result.total_tweets,
                    "average_tweets_per_user": scraping_result.total_tweets / scraping_result.successful_users if scraping_result.successful_users > 0 else 0
                },
                "success_details": scraping_result.success_details,
                "errors": scraping_result.errors
            }
            
            # 保存摘要文件
            filename = "batch_summary.json"
            filepath = date_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"批次抓取摘要已保存到: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"保存批次摘要失败: {e}")
            raise
    
    async def save_account_states(self, account_states: Dict[str, Any]) -> str:
        """
        保存账号状态信息
        
        Args:
            account_states: 账号状态字典
            
        Returns:
            保存的文件路径
        """
        try:
            accounts_dir = self.base_dir / "accounts"
            filepath = accounts_dir / "account_states.json"
            
            # 转换账号状态为可序列化的格式
            serializable_states = {}
            for username, state in account_states.items():
                serializable_states[username] = {
                    "username": state.username,
                    "last_fetched_id": state.last_fetched_id,
                    "last_fetched_time": state.last_fetched_time.isoformat() if state.last_fetched_time else None,
                    "status": state.status,
                    "total_tweets_fetched": state.total_tweets_fetched,
                    "last_error": state.last_error,
                    "retry_count": state.retry_count,
                    "next_retry_time": state.next_retry_time.isoformat() if state.next_retry_time else None
                }
            
            # 保存状态文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    "updated_at": datetime.now().isoformat(),
                    "account_states": serializable_states
                }, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"账号状态已保存到: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"保存账号状态失败: {e}")
            raise
    
    async def export_to_csv(self, date: datetime = None) -> str:
        """
        导出指定日期的推文数据为CSV格式
        
        Args:
            date: 目标日期，默认为今天
            
        Returns:
            导出的CSV文件路径
        """
        try:
            if date is None:
                date = datetime.now()
            
            date_str = date.strftime("%Y-%m-%d")
            date_dir = self.base_dir / "tweets" / date_str
            
            if not date_dir.exists():
                raise FileNotFoundError(f"日期目录不存在: {date_dir}")
            
            # 收集所有推文数据
            all_tweets = []
            
            for json_file in date_dir.glob("*_tweets.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        tweets = data.get("tweets", [])
                        
                        # 为每条推文添加来源信息
                        username = data.get("metadata", {}).get("username", "unknown")
                        for tweet in tweets:
                            tweet["source_username"] = username
                            all_tweets.append(tweet)
                            
                except Exception as e:
                    self.logger.warning(f"读取文件 {json_file} 失败: {e}")
                    continue
            
            if not all_tweets:
                self.logger.warning(f"日期 {date_str} 没有找到推文数据")
                return ""
            
            # 导出为CSV
            exports_dir = self.base_dir / "exports"
            csv_filename = f"twitter_daily_{date_str}.csv"
            csv_filepath = exports_dir / csv_filename
            
            # 使用pandas处理CSV导出
            df = pd.DataFrame(all_tweets)
            df.to_csv(csv_filepath, index=False, encoding='utf-8-sig')
            
            self.logger.info(f"推文数据已导出为CSV: {csv_filepath}")
            return str(csv_filepath)
            
        except Exception as e:
            self.logger.error(f"导出CSV失败: {e}")
            raise
    
    async def export_to_excel(self, date: datetime = None) -> str:
        """
        导出指定日期的推文数据为Excel格式
        
        Args:
            date: 目标日期，默认为今天
            
        Returns:
            导出的Excel文件路径
        """
        try:
            if date is None:
                date = datetime.now()
            
            date_str = date.strftime("%Y-%m-%d")
            date_dir = self.base_dir / "tweets" / date_str
            
            if not date_dir.exists():
                raise FileNotFoundError(f"日期目录不存在: {date_dir}")
            
            # 收集所有推文数据
            all_tweets = []
            user_summaries = []
            
            for json_file in date_dir.glob("*_tweets.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        tweets = data.get("tweets", [])
                        metadata = data.get("metadata", {})
                        
                        # 收集推文数据
                        username = metadata.get("username", "unknown")
                        for tweet in tweets:
                            tweet["source_username"] = username
                            all_tweets.append(tweet)
                        
                        # 收集用户摘要
                        user_summaries.append({
                            "username": username,
                            "total_tweets": metadata.get("total_tweets", 0),
                            "scraped_at": metadata.get("scraped_at", ""),
                            "status": metadata.get("status", "unknown")
                        })
                        
                except Exception as e:
                    self.logger.warning(f"读取文件 {json_file} 失败: {e}")
                    continue
            
            if not all_tweets:
                self.logger.warning(f"日期 {date_str} 没有找到推文数据")
                return ""
            
            # 导出为Excel
            exports_dir = self.base_dir / "exports"
            excel_filename = f"twitter_daily_{date_str}.xlsx"
            excel_filepath = exports_dir / excel_filename
            
            with pd.ExcelWriter(excel_filepath, engine='openpyxl') as writer:
                # 推文数据工作表
                tweets_df = pd.DataFrame(all_tweets)
                tweets_df.to_excel(writer, sheet_name='推文数据', index=False)
                
                # 用户摘要工作表
                summary_df = pd.DataFrame(user_summaries)
                summary_df.to_excel(writer, sheet_name='用户摘要', index=False)
            
            self.logger.info(f"推文数据已导出为Excel: {excel_filepath}")
            return str(excel_filepath)
            
        except Exception as e:
            self.logger.error(f"导出Excel失败: {e}")
            raise
    
    def load_account_states(self) -> Dict[str, Any]:
        """
        加载账号状态信息
        
        Returns:
            账号状态字典
        """
        try:
            accounts_dir = self.base_dir / "accounts"
            filepath = accounts_dir / "account_states.json"
            
            if not filepath.exists():
                self.logger.info("账号状态文件不存在，返回空状态")
                return {}
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("account_states", {})
                
        except Exception as e:
            self.logger.error(f"加载账号状态失败: {e}")
            return {}
    
    def get_storage_statistics(self) -> Dict[str, Any]:
        """
        获取存储统计信息
        
        Returns:
            存储统计信息
        """
        try:
            stats = {
                "total_dates": 0,
                "total_users": 0,
                "total_tweets": 0,
                "total_files": 0,
                "storage_size_mb": 0,
                "date_details": []
            }
            
            tweets_dir = self.base_dir / "tweets"
            
            if not tweets_dir.exists():
                return stats
            
            # 遍历日期目录
            for date_dir in tweets_dir.iterdir():
                if not date_dir.is_dir():
                    continue
                
                date_stats = {
                    "date": date_dir.name,
                    "users": 0,
                    "tweets": 0,
                    "files": 0
                }
                
                # 统计该日期的文件
                for json_file in date_dir.glob("*_tweets.json"):
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            tweets_count = len(data.get("tweets", []))
                            
                            date_stats["users"] += 1
                            date_stats["tweets"] += tweets_count
                            date_stats["files"] += 1
                            
                            # 计算文件大小
                            stats["storage_size_mb"] += json_file.stat().st_size / (1024 * 1024)
                            
                    except Exception as e:
                        self.logger.warning(f"统计文件 {json_file} 失败: {e}")
                        continue
                
                if date_stats["files"] > 0:
                    stats["date_details"].append(date_stats)
                    stats["total_dates"] += 1
                    stats["total_users"] += date_stats["users"]
                    stats["total_tweets"] += date_stats["tweets"]
                    stats["total_files"] += date_stats["files"]
            
            return stats
            
        except Exception as e:
            self.logger.error(f"获取存储统计信息失败: {e}")
            return {}
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """
        清理旧数据
        
        Args:
            days_to_keep: 保留的天数
        """
        try:
            from datetime import timedelta
            
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            tweets_dir = self.base_dir / "tweets"
            
            if not tweets_dir.exists():
                return
            
            deleted_count = 0
            
            for date_dir in tweets_dir.iterdir():
                if not date_dir.is_dir():
                    continue
                
                try:
                    # 解析日期
                    dir_date = datetime.strptime(date_dir.name, "%Y-%m-%d")
                    
                    if dir_date < cutoff_date:
                        # 删除整个日期目录
                        import shutil
                        shutil.rmtree(date_dir)
                        deleted_count += 1
                        self.logger.info(f"删除过期数据目录: {date_dir}")
                        
                except ValueError:
                    # 日期格式不正确，跳过
                    continue
                except Exception as e:
                    self.logger.error(f"删除目录 {date_dir} 失败: {e}")
                    continue
            
            self.logger.info(f"清理完成，删除了 {deleted_count} 个过期数据目录")
            
        except Exception as e:
            self.logger.error(f"清理旧数据失败: {e}")