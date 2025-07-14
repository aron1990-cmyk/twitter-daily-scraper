#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器
统一管理所有配置文件和设置
"""

import json
import os
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
import shutil
from pathlib import Path

@dataclass
class ConfigBackup:
    """配置备份信息"""
    backup_time: str
    config_name: str
    backup_path: str
    file_size: int
    description: str = ""

class ConfigManager:
    """
    配置管理器
    提供配置文件的统一管理、备份、恢复、验证等功能
    """
    
    def __init__(self, config_dir: str = "configs"):
        self.logger = logging.getLogger('ConfigManager')
        self.config_dir = Path(config_dir)
        self.backup_dir = self.config_dir / "backups"
        
        # 创建配置目录
        self.config_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)
        
        # 配置文件映射
        self.config_files = {
            'main': 'config.py',
            'scheduler': 'scheduler_config.json',
            'ai_analyzer': 'ai_analyzer_config.json',
            'account_manager': 'account_manager_config.json',
            'cloud_sync': 'cloud_sync_config.json',
            'filters': 'filter_config.json',
            'targets': 'target_config.json'
        }
        
        # 默认配置模板
        self.default_configs = {
            'scheduler': {
                'default_timeout_minutes': 60,
                'max_concurrent_tasks': 3,
                'retry_delay_minutes': 5,
                'log_retention_days': 30,
                'enable_email_notifications': False,
                'email_settings': {
                    'smtp_server': '',
                    'smtp_port': 587,
                    'username': '',
                    'password': '',
                    'recipients': []
                }
            },
            'ai_analyzer': {
                'enable_sentiment_analysis': True,
                'enable_trend_analysis': True,
                'enable_quality_scoring': True,
                'sentiment_threshold': 0.1,
                'quality_threshold': 0.6,
                'trend_keywords_update_interval_hours': 24,
                'batch_size': 100,
                'cache_results': True,
                'cache_expiry_hours': 24
            },
            'account_manager': {
                'rotation_strategy': 'round_robin',
                'cooldown_minutes': 30,
                'max_daily_usage_per_account': 50,
                'error_threshold': 5,
                'auto_disable_failed_accounts': True,
                'health_check_interval_minutes': 15,
                'priority_boost_factor': 1.5
            },
            'cloud_sync': {
                'sync_interval_minutes': 60,
                'retry_attempts': 3,
                'batch_upload_size': 1000,
                'compress_data': True,
                'backup_before_sync': True,
                'sync_timeout_minutes': 30
            },
            'filters': {
                'enable_duplicate_detection': True,
                'enable_spam_filtering': True,
                'enable_language_filtering': True,
                'min_tweet_length': 10,
                'max_tweet_length': 2000,
                'allowed_languages': ['zh', 'en'],
                'spam_keywords': ['spam', 'bot', 'fake'],
                'quality_filters': {
                    'min_likes': 0,
                    'min_retweets': 0,
                    'min_comments': 0,
                    'verified_users_only': False
                }
            },
            'targets': {
                'max_tweets_per_user': 100,
                'max_tweets_per_keyword': 200,
                'search_time_range_hours': 24,
                'include_replies': False,
                'include_retweets': True,
                'sort_by': 'latest',
                'user_verification_required': False
            }
        }
        
        self.logger.info("配置管理器初始化完成")
    
    def load_config(self, config_name: str) -> Optional[Dict[str, Any]]:
        """
        加载配置文件
        
        Args:
            config_name: 配置名称
            
        Returns:
            配置内容，如果文件不存在返回None
        """
        if config_name not in self.config_files:
            self.logger.error(f"未知的配置名称: {config_name}")
            return None
        
        config_file = self.config_files[config_name]
        config_path = Path(config_file)
        
        # 如果是Python文件，从当前目录加载
        if config_file.endswith('.py'):
            if not config_path.exists():
                self.logger.warning(f"配置文件不存在: {config_file}")
                return None
            
            try:
                # 动态导入配置模块
                import importlib.util
                spec = importlib.util.spec_from_file_location("config", config_path)
                config_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(config_module)
                
                # 提取配置变量
                config_dict = {}
                for attr_name in dir(config_module):
                    if not attr_name.startswith('_'):
                        attr_value = getattr(config_module, attr_name)
                        if not callable(attr_value):
                            config_dict[attr_name] = attr_value
                
                self.logger.info(f"已加载Python配置: {config_file}")
                return config_dict
                
            except Exception as e:
                self.logger.error(f"加载Python配置失败: {e}")
                return None
        
        # JSON配置文件
        else:
            json_path = self.config_dir / config_file
            
            if not json_path.exists():
                # 创建默认配置
                if config_name in self.default_configs:
                    default_config = self.default_configs[config_name]
                    self.save_config(config_name, default_config)
                    self.logger.info(f"已创建默认配置: {config_file}")
                    return default_config
                else:
                    self.logger.warning(f"配置文件不存在且无默认配置: {config_file}")
                    return None
            
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.logger.info(f"已加载JSON配置: {config_file}")
                    return config
            except Exception as e:
                self.logger.error(f"加载JSON配置失败: {e}")
                return None
    
    def save_config(self, config_name: str, config_data: Dict[str, Any], 
                   backup: bool = True) -> bool:
        """
        保存配置文件
        
        Args:
            config_name: 配置名称
            config_data: 配置数据
            backup: 是否备份原配置
            
        Returns:
            是否保存成功
        """
        if config_name not in self.config_files:
            self.logger.error(f"未知的配置名称: {config_name}")
            return False
        
        config_file = self.config_files[config_name]
        
        # Python配置文件不支持直接保存
        if config_file.endswith('.py'):
            self.logger.warning(f"Python配置文件需要手动编辑: {config_file}")
            return False
        
        json_path = self.config_dir / config_file
        
        try:
            # 备份原配置
            if backup and json_path.exists():
                self.backup_config(config_name)
            
            # 保存新配置
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"配置已保存: {config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
            return False
    
    def backup_config(self, config_name: str, description: str = "") -> Optional[str]:
        """
        备份配置文件
        
        Args:
            config_name: 配置名称
            description: 备份描述
            
        Returns:
            备份文件路径，失败返回None
        """
        if config_name not in self.config_files:
            self.logger.error(f"未知的配置名称: {config_name}")
            return None
        
        config_file = self.config_files[config_name]
        source_path = Path(config_file) if config_file.endswith('.py') else self.config_dir / config_file
        
        if not source_path.exists():
            self.logger.warning(f"配置文件不存在，无法备份: {config_file}")
            return None
        
        try:
            # 生成备份文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{config_name}_{timestamp}.backup"
            backup_path = self.backup_dir / backup_filename
            
            # 复制文件
            shutil.copy2(source_path, backup_path)
            
            # 记录备份信息
            backup_info = ConfigBackup(
                backup_time=datetime.now().isoformat(),
                config_name=config_name,
                backup_path=str(backup_path),
                file_size=backup_path.stat().st_size,
                description=description
            )
            
            # 保存备份记录
            self._save_backup_record(backup_info)
            
            self.logger.info(f"配置已备份: {backup_filename}")
            return str(backup_path)
            
        except Exception as e:
            self.logger.error(f"备份配置失败: {e}")
            return None
    
    def restore_config(self, config_name: str, backup_time: str) -> bool:
        """
        恢复配置文件
        
        Args:
            config_name: 配置名称
            backup_time: 备份时间（用于查找备份文件）
            
        Returns:
            是否恢复成功
        """
        backup_records = self.list_backups(config_name)
        
        # 查找匹配的备份
        target_backup = None
        for backup in backup_records:
            if backup.backup_time.startswith(backup_time.replace('-', '').replace(':', '').replace(' ', '_')):
                target_backup = backup
                break
        
        if not target_backup:
            self.logger.error(f"未找到匹配的备份: {config_name} @ {backup_time}")
            return False
        
        backup_path = Path(target_backup.backup_path)
        if not backup_path.exists():
            self.logger.error(f"备份文件不存在: {backup_path}")
            return False
        
        try:
            # 先备份当前配置
            self.backup_config(config_name, f"恢复前自动备份")
            
            # 恢复配置
            config_file = self.config_files[config_name]
            target_path = Path(config_file) if config_file.endswith('.py') else self.config_dir / config_file
            
            shutil.copy2(backup_path, target_path)
            
            self.logger.info(f"配置已恢复: {config_name} from {backup_time}")
            return True
            
        except Exception as e:
            self.logger.error(f"恢复配置失败: {e}")
            return False
    
    def list_backups(self, config_name: Optional[str] = None) -> List[ConfigBackup]:
        """
        列出备份记录
        
        Args:
            config_name: 配置名称，None表示列出所有备份
            
        Returns:
            备份记录列表
        """
        backup_record_file = self.backup_dir / "backup_records.json"
        
        if not backup_record_file.exists():
            return []
        
        try:
            with open(backup_record_file, 'r', encoding='utf-8') as f:
                records_data = json.load(f)
            
            backups = [ConfigBackup(**record) for record in records_data]
            
            if config_name:
                backups = [backup for backup in backups if backup.config_name == config_name]
            
            # 按时间倒序排列
            backups.sort(key=lambda x: x.backup_time, reverse=True)
            
            return backups
            
        except Exception as e:
            self.logger.error(f"读取备份记录失败: {e}")
            return []
    
    def _save_backup_record(self, backup_info: ConfigBackup):
        """
        保存备份记录
        
        Args:
            backup_info: 备份信息
        """
        backup_record_file = self.backup_dir / "backup_records.json"
        
        try:
            # 读取现有记录
            if backup_record_file.exists():
                with open(backup_record_file, 'r', encoding='utf-8') as f:
                    records = json.load(f)
            else:
                records = []
            
            # 添加新记录
            records.append(asdict(backup_info))
            
            # 保持最近100条记录
            if len(records) > 100:
                records = records[-100:]
            
            # 保存记录
            with open(backup_record_file, 'w', encoding='utf-8') as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"保存备份记录失败: {e}")
    
    def validate_config(self, config_name: str, config_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        验证配置文件
        
        Args:
            config_name: 配置名称
            config_data: 配置数据，None表示加载文件验证
            
        Returns:
            验证结果
        """
        if config_data is None:
            config_data = self.load_config(config_name)
        
        if config_data is None:
            return {
                'valid': False,
                'errors': ['配置文件不存在或加载失败'],
                'warnings': [],
                'suggestions': []
            }
        
        errors = []
        warnings = []
        suggestions = []
        
        # 根据配置类型进行验证
        if config_name == 'scheduler':
            errors.extend(self._validate_scheduler_config(config_data))
        elif config_name == 'ai_analyzer':
            errors.extend(self._validate_ai_analyzer_config(config_data))
        elif config_name == 'account_manager':
            errors.extend(self._validate_account_manager_config(config_data))
        elif config_name == 'cloud_sync':
            errors.extend(self._validate_cloud_sync_config(config_data))
        elif config_name == 'filters':
            errors.extend(self._validate_filters_config(config_data))
        elif config_name == 'targets':
            errors.extend(self._validate_targets_config(config_data))
        
        # 检查缺失的默认配置项
        if config_name in self.default_configs:
            default_config = self.default_configs[config_name]
            missing_keys = set(default_config.keys()) - set(config_data.keys())
            if missing_keys:
                warnings.append(f"缺失配置项: {', '.join(missing_keys)}")
                suggestions.append("建议添加缺失的配置项以使用默认值")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'suggestions': suggestions
        }
    
    def _validate_scheduler_config(self, config: Dict[str, Any]) -> List[str]:
        """验证调度器配置"""
        errors = []
        
        if 'default_timeout_minutes' in config:
            if not isinstance(config['default_timeout_minutes'], int) or config['default_timeout_minutes'] <= 0:
                errors.append("default_timeout_minutes必须是正整数")
        
        if 'max_concurrent_tasks' in config:
            if not isinstance(config['max_concurrent_tasks'], int) or config['max_concurrent_tasks'] <= 0:
                errors.append("max_concurrent_tasks必须是正整数")
        
        return errors
    
    def _validate_ai_analyzer_config(self, config: Dict[str, Any]) -> List[str]:
        """验证AI分析器配置"""
        errors = []
        
        if 'sentiment_threshold' in config:
            threshold = config['sentiment_threshold']
            if not isinstance(threshold, (int, float)) or not -1 <= threshold <= 1:
                errors.append("sentiment_threshold必须是-1到1之间的数值")
        
        if 'quality_threshold' in config:
            threshold = config['quality_threshold']
            if not isinstance(threshold, (int, float)) or not 0 <= threshold <= 1:
                errors.append("quality_threshold必须是0到1之间的数值")
        
        return errors
    
    def _validate_account_manager_config(self, config: Dict[str, Any]) -> List[str]:
        """验证账户管理器配置"""
        errors = []
        
        if 'rotation_strategy' in config:
            valid_strategies = ['round_robin', 'priority', 'random']
            if config['rotation_strategy'] not in valid_strategies:
                errors.append(f"rotation_strategy必须是以下之一: {', '.join(valid_strategies)}")
        
        if 'cooldown_minutes' in config:
            if not isinstance(config['cooldown_minutes'], int) or config['cooldown_minutes'] < 0:
                errors.append("cooldown_minutes必须是非负整数")
        
        return errors
    
    def _validate_cloud_sync_config(self, config: Dict[str, Any]) -> List[str]:
        """验证云同步配置"""
        errors = []
        
        if 'sync_interval_minutes' in config:
            if not isinstance(config['sync_interval_minutes'], int) or config['sync_interval_minutes'] <= 0:
                errors.append("sync_interval_minutes必须是正整数")
        
        if 'batch_upload_size' in config:
            if not isinstance(config['batch_upload_size'], int) or config['batch_upload_size'] <= 0:
                errors.append("batch_upload_size必须是正整数")
        
        return errors
    
    def _validate_filters_config(self, config: Dict[str, Any]) -> List[str]:
        """验证过滤器配置"""
        errors = []
        
        if 'min_tweet_length' in config:
            if not isinstance(config['min_tweet_length'], int) or config['min_tweet_length'] < 0:
                errors.append("min_tweet_length必须是非负整数")
        
        if 'max_tweet_length' in config:
            if not isinstance(config['max_tweet_length'], int) or config['max_tweet_length'] <= 0:
                errors.append("max_tweet_length必须是正整数")
        
        if 'allowed_languages' in config:
            if not isinstance(config['allowed_languages'], list):
                errors.append("allowed_languages必须是列表")
        
        return errors
    
    def _validate_targets_config(self, config: Dict[str, Any]) -> List[str]:
        """验证目标配置"""
        errors = []
        
        if 'max_tweets_per_user' in config:
            if not isinstance(config['max_tweets_per_user'], int) or config['max_tweets_per_user'] <= 0:
                errors.append("max_tweets_per_user必须是正整数")
        
        if 'search_time_range_hours' in config:
            if not isinstance(config['search_time_range_hours'], int) or config['search_time_range_hours'] <= 0:
                errors.append("search_time_range_hours必须是正整数")
        
        return errors
    
    def get_config_summary(self) -> Dict[str, Any]:
        """
        获取配置摘要
        
        Returns:
            配置摘要信息
        """
        summary = {
            'config_files': {},
            'backup_count': 0,
            'total_size': 0,
            'last_modified': None
        }
        
        latest_time = None
        
        for config_name, config_file in self.config_files.items():
            file_path = Path(config_file) if config_file.endswith('.py') else self.config_dir / config_file
            
            if file_path.exists():
                stat = file_path.stat()
                modified_time = datetime.fromtimestamp(stat.st_mtime)
                
                summary['config_files'][config_name] = {
                    'exists': True,
                    'size': stat.st_size,
                    'modified': modified_time.isoformat(),
                    'path': str(file_path)
                }
                
                summary['total_size'] += stat.st_size
                
                if latest_time is None or modified_time > latest_time:
                    latest_time = modified_time
            else:
                summary['config_files'][config_name] = {
                    'exists': False,
                    'size': 0,
                    'modified': None,
                    'path': str(file_path)
                }
        
        summary['backup_count'] = len(self.list_backups())
        summary['last_modified'] = latest_time.isoformat() if latest_time else None
        
        return summary
    
    def cleanup_old_backups(self, days: int = 30) -> int:
        """
        清理旧备份文件
        
        Args:
            days: 保留天数
            
        Returns:
            清理的文件数量
        """
        cutoff_time = datetime.now() - timedelta(days=days)
        backups = self.list_backups()
        
        cleaned_count = 0
        remaining_backups = []
        
        for backup in backups:
            backup_time = datetime.fromisoformat(backup.backup_time)
            
            if backup_time < cutoff_time:
                # 删除旧备份文件
                backup_path = Path(backup.backup_path)
                if backup_path.exists():
                    try:
                        backup_path.unlink()
                        cleaned_count += 1
                        self.logger.info(f"已删除旧备份: {backup_path.name}")
                    except Exception as e:
                        self.logger.error(f"删除备份文件失败: {e}")
                        remaining_backups.append(backup)
                else:
                    cleaned_count += 1  # 文件已不存在，计入清理数量
            else:
                remaining_backups.append(backup)
        
        # 更新备份记录
        if cleaned_count > 0:
            backup_record_file = self.backup_dir / "backup_records.json"
            try:
                with open(backup_record_file, 'w', encoding='utf-8') as f:
                    json.dump([asdict(backup) for backup in remaining_backups], 
                             f, ensure_ascii=False, indent=2)
            except Exception as e:
                self.logger.error(f"更新备份记录失败: {e}")
        
        self.logger.info(f"清理完成，删除了 {cleaned_count} 个旧备份文件")
        return cleaned_count
    
    def export_all_configs(self, export_path: str) -> bool:
        """
        导出所有配置到指定目录
        
        Args:
            export_path: 导出目录路径
            
        Returns:
            是否导出成功
        """
        export_dir = Path(export_path)
        export_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            exported_count = 0
            
            for config_name, config_file in self.config_files.items():
                source_path = Path(config_file) if config_file.endswith('.py') else self.config_dir / config_file
                
                if source_path.exists():
                    target_path = export_dir / config_file
                    shutil.copy2(source_path, target_path)
                    exported_count += 1
                    self.logger.info(f"已导出配置: {config_file}")
            
            # 创建导出信息文件
            export_info = {
                'export_time': datetime.now().isoformat(),
                'exported_configs': exported_count,
                'config_summary': self.get_config_summary()
            }
            
            with open(export_dir / 'export_info.json', 'w', encoding='utf-8') as f:
                json.dump(export_info, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"配置导出完成，共导出 {exported_count} 个文件到 {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出配置失败: {e}")
            return False
    
    def import_configs(self, import_path: str, backup_existing: bool = True) -> bool:
        """
        从指定目录导入配置
        
        Args:
            import_path: 导入目录路径
            backup_existing: 是否备份现有配置
            
        Returns:
            是否导入成功
        """
        import_dir = Path(import_path)
        
        if not import_dir.exists():
            self.logger.error(f"导入目录不存在: {import_path}")
            return False
        
        try:
            imported_count = 0
            
            # 备份现有配置
            if backup_existing:
                for config_name in self.config_files.keys():
                    self.backup_config(config_name, "导入前自动备份")
            
            # 导入配置文件
            for config_name, config_file in self.config_files.items():
                source_path = import_dir / config_file
                
                if source_path.exists():
                    target_path = Path(config_file) if config_file.endswith('.py') else self.config_dir / config_file
                    shutil.copy2(source_path, target_path)
                    imported_count += 1
                    self.logger.info(f"已导入配置: {config_file}")
            
            self.logger.info(f"配置导入完成，共导入 {imported_count} 个文件")
            return True
            
        except Exception as e:
            self.logger.error(f"导入配置失败: {e}")
            return False