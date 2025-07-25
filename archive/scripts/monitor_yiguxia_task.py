#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
监控yiguxia任务的完整执行流程
从AdsPower启动到数据保存的每个环节
"""

import requests
import time
import json
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('yiguxia_task_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class YiguxiaTaskMonitor:
    def __init__(self):
        self.base_url = "http://localhost:8088"
        self.task_id = None
        self.start_time = None
        
    def create_task(self):
        """创建yiguxia任务"""
        logger.info("🚀 步骤1: 创建yiguxia任务")
        
        task_data = {
            'name': 'yiguxia监控任务',
            'target_accounts': json.dumps(['yiguxia']),
            'target_keywords': json.dumps([]),
            'max_tweets': 100,
            'min_likes': 0,
            'min_comments': 0,
            'min_retweets': 0
        }
        
        logger.info(f"📤 发送创建任务请求: {task_data}")
        
        try:
            response = requests.post(f"{self.base_url}/api/tasks", json=task_data, timeout=30)
            logger.info(f"📥 创建任务响应: 状态码={response.status_code}, 内容={response.text}")
            
            if response.status_code in [200, 201]:
                try:
                    result = response.json()
                    logger.info(f"📋 解析响应数据: {result}")
                    if result.get('success'):
                        self.task_id = result['task_id']
                        logger.info(f"✅ 任务创建成功，任务ID: {self.task_id}")
                        return True
                    else:
                        logger.error(f"❌ 任务创建失败: {result.get('message', 'Unknown error')}")
                        return False
                except Exception as e:
                    logger.error(f"❌ 解析响应失败: {e}")
                    return False
            else:
                logger.error(f"❌ 任务创建失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ 任务创建异常: {e}")
            return False
    
    def start_task(self):
        """启动任务"""
        if not self.task_id:
            logger.error("❌ 无法启动任务：任务ID为空")
            return False
            
        logger.info(f"🚀 步骤2: 启动任务 {self.task_id}")
        self.start_time = datetime.now()
        
        try:
            response = requests.post(f"{self.base_url}/api/tasks/{self.task_id}/start")
            if response.status_code == 200:
                logger.info("✅ 任务启动成功")
                return True
            else:
                logger.error(f"❌ 任务启动失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ 任务启动异常: {e}")
            return False
    
    def monitor_task_progress(self):
        """监控任务进度"""
        logger.info("🔍 步骤3: 开始监控任务进度")
        
        check_count = 0
        last_status = None
        last_result_count = 0
        
        while True:
            check_count += 1
            elapsed_time = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
            
            try:
                # 获取任务状态
                response = requests.get(f"{self.base_url}/api/tasks/{self.task_id}")
                if response.status_code != 200:
                    logger.error(f"❌ 获取任务状态失败: {response.status_code}")
                    time.sleep(5)
                    continue
                
                task_info = response.json()
                current_status = task_info.get('status', 'unknown')
                result_count = task_info.get('result_count', 0)
                
                # 状态变化时记录
                if current_status != last_status:
                    logger.info(f"📊 任务状态变化: {last_status} -> {current_status}")
                    logger.info(f"   - 检查次数: {check_count}")
                    logger.info(f"   - 运行时间: {elapsed_time:.1f}秒")
                    logger.info(f"   - 当前结果数: {result_count}")
                    last_status = current_status
                
                # 结果数量变化时记录
                if result_count != last_result_count:
                    logger.info(f"📈 抓取进度更新: {last_result_count} -> {result_count} 条推文")
                    last_result_count = result_count
                
                # 详细状态信息
                if check_count % 10 == 0:  # 每10次检查输出一次详细信息
                    logger.info(f"📋 详细状态报告 (第{check_count}次检查):")
                    logger.info(f"   - 任务ID: {self.task_id}")
                    logger.info(f"   - 任务名称: {task_info.get('name', 'N/A')}")
                    logger.info(f"   - 当前状态: {current_status}")
                    logger.info(f"   - 目标账号: {task_info.get('target_accounts', 'N/A')}")
                    logger.info(f"   - 最大推文数: {task_info.get('max_tweets', 'N/A')}")
                    logger.info(f"   - 已收集推文: {result_count}")
                    logger.info(f"   - 创建时间: {task_info.get('created_at', 'N/A')}")
                    logger.info(f"   - 开始时间: {task_info.get('started_at', 'N/A')}")
                    logger.info(f"   - 运行时长: {elapsed_time:.1f}秒")
                
                # 检查任务是否完成
                if current_status in ['completed', 'failed']:
                    logger.info(f"🏁 任务执行完成，最终状态: {current_status}")
                    logger.info(f"   - 总运行时间: {elapsed_time:.1f}秒")
                    logger.info(f"   - 最终结果数: {result_count}")
                    logger.info(f"   - 总检查次数: {check_count}")
                    
                    if current_status == 'completed':
                        self.analyze_results()
                    else:
                        self.analyze_failure()
                    break
                
                # 超时检查
                if elapsed_time > 600:  # 10分钟超时
                    logger.warning(f"⚠️ 任务执行超时 ({elapsed_time:.1f}秒)，停止监控")
                    break
                
                time.sleep(3)  # 每3秒检查一次
                
            except Exception as e:
                logger.error(f"❌ 监控过程中发生异常: {e}")
                time.sleep(5)
                continue
    
    def analyze_results(self):
        """分析任务结果"""
        logger.info("📊 步骤4: 分析任务执行结果")
        
        try:
            # 获取任务详细信息
            response = requests.get(f"{self.base_url}/api/tasks/{self.task_id}")
            if response.status_code == 200:
                task_info = response.json()
                logger.info("✅ 任务执行成功分析:")
                logger.info(f"   - 任务名称: {task_info.get('name')}")
                logger.info(f"   - 目标账号: {task_info.get('target_accounts')}")
                logger.info(f"   - 抓取推文数: {task_info.get('result_count', 0)}")
                logger.info(f"   - 完成时间: {task_info.get('completed_at')}")
                
                # 检查数据库中的推文数据
                self.check_database_data()
                
                # 检查Excel文件
                self.check_excel_export()
                
                # 检查飞书同步
                self.check_feishu_sync()
                
            else:
                logger.error(f"❌ 获取任务结果失败: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ 结果分析异常: {e}")
    
    def analyze_failure(self):
        """分析任务失败原因"""
        logger.info("🔍 步骤4: 分析任务失败原因")
        
        try:
            # 检查任务错误日志
            error_file = f"task_error_{self.task_id}.json"
            try:
                with open(error_file, 'r', encoding='utf-8') as f:
                    error_data = json.load(f)
                    logger.error(f"❌ 任务失败详情:")
                    logger.error(f"   - 错误类型: {error_data.get('error_type', 'Unknown')}")
                    logger.error(f"   - 错误消息: {error_data.get('error_message', 'No message')}")
                    logger.error(f"   - 错误时间: {error_data.get('error_time', 'Unknown')}")
            except FileNotFoundError:
                logger.warning("⚠️ 未找到错误日志文件")
            
            # 检查AdsPower状态
            self.check_adspower_status()
            
            # 检查浏览器连接
            self.check_browser_connection()
            
        except Exception as e:
            logger.error(f"❌ 失败分析异常: {e}")
    
    def check_database_data(self):
        """检查数据库中的数据"""
        logger.info("💾 检查数据库数据...")
        
        try:
            response = requests.get(f"{self.base_url}/api/tasks/{self.task_id}/data")
            if response.status_code == 200:
                data = response.json()
                tweet_count = len(data.get('tweets', []))
                logger.info(f"✅ 数据库检查结果:")
                logger.info(f"   - 推文数量: {tweet_count}")
                
                if tweet_count > 0:
                    sample_tweet = data['tweets'][0]
                    logger.info(f"   - 示例推文用户: {sample_tweet.get('username', 'N/A')}")
                    logger.info(f"   - 示例推文内容: {sample_tweet.get('content', 'N/A')[:50]}...")
                    logger.info(f"   - 示例推文点赞: {sample_tweet.get('likes', 0)}")
            else:
                logger.warning(f"⚠️ 无法获取数据库数据: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ 数据库检查异常: {e}")
    
    def check_excel_export(self):
        """检查Excel导出"""
        logger.info("📊 检查Excel导出...")
        
        try:
            import os
            data_dir = "data"
            if os.path.exists(data_dir):
                excel_files = [f for f in os.listdir(data_dir) if f.startswith(f'tweets_{self.task_id}') and f.endswith('.xlsx')]
                if excel_files:
                    latest_file = max(excel_files, key=lambda x: os.path.getctime(os.path.join(data_dir, x)))
                    file_path = os.path.join(data_dir, latest_file)
                    file_size = os.path.getsize(file_path)
                    logger.info(f"✅ Excel文件检查结果:")
                    logger.info(f"   - 文件名: {latest_file}")
                    logger.info(f"   - 文件大小: {file_size} 字节")
                    logger.info(f"   - 文件路径: {file_path}")
                else:
                    logger.warning("⚠️ 未找到对应的Excel文件")
            else:
                logger.warning("⚠️ data目录不存在")
                
        except Exception as e:
            logger.error(f"❌ Excel检查异常: {e}")
    
    def check_feishu_sync(self):
        """检查飞书同步状态"""
        logger.info("☁️ 检查飞书同步状态...")
        
        try:
            # 检查飞书配置
            try:
                with open('feishu_config.json', 'r', encoding='utf-8') as f:
                    feishu_config = json.load(f)
                    enabled = feishu_config.get('enabled', False)
                    logger.info(f"📋 飞书配置状态:")
                    logger.info(f"   - 同步启用: {enabled}")
                    
                    if enabled:
                        logger.info(f"   - App ID: {feishu_config.get('app_id', 'N/A')[:10]}...")
                        logger.info(f"   - 表格ID: {feishu_config.get('spreadsheet_id', 'N/A')[:10]}...")
                    else:
                        logger.info("   - 飞书同步未启用，跳过同步检查")
                        
            except FileNotFoundError:
                logger.warning("⚠️ 未找到飞书配置文件")
                
        except Exception as e:
            logger.error(f"❌ 飞书同步检查异常: {e}")
    
    def check_adspower_status(self):
        """检查AdsPower状态"""
        logger.info("🌐 检查AdsPower状态...")
        
        try:
            # 检查AdsPower API
            adspower_url = "http://local.adspower.net:50325/api/v1/user/list"
            response = requests.get(adspower_url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    users = data.get('data', {}).get('list', [])
                    logger.info(f"✅ AdsPower状态正常:")
                    logger.info(f"   - 用户配置数量: {len(users)}")
                    
                    # 查找yiguxia相关配置
                    target_users = [u for u in users if 'yiguxia' in u.get('name', '').lower() or u.get('user_id') == 'k11p9ypc']
                    if target_users:
                        user = target_users[0]
                        logger.info(f"   - 目标用户: {user.get('name', 'N/A')}")
                        logger.info(f"   - 用户ID: {user.get('user_id', 'N/A')}")
                        logger.info(f"   - 状态: {user.get('status', 'N/A')}")
                    else:
                        logger.warning("⚠️ 未找到yiguxia相关用户配置")
                else:
                    logger.error(f"❌ AdsPower API返回错误: {data.get('msg', 'Unknown')}")
            else:
                logger.error(f"❌ AdsPower API请求失败: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ AdsPower状态检查异常: {e}")
    
    def check_browser_connection(self):
        """检查浏览器连接状态"""
        logger.info("🔗 检查浏览器连接状态...")
        
        try:
            # 这里可以添加更多的浏览器连接检查逻辑
            logger.info("📋 浏览器连接检查:")
            logger.info("   - 检查项目: 调试端口连接")
            logger.info("   - 检查项目: Playwright连接")
            logger.info("   - 检查项目: Twitter页面访问")
            logger.info("   - 注意: 详细检查需要在任务执行过程中进行")
            
        except Exception as e:
            logger.error(f"❌ 浏览器连接检查异常: {e}")
    
    def run_full_monitor(self):
        """运行完整监控流程"""
        logger.info("🚀 开始yiguxia任务完整监控流程")
        logger.info("="*60)
        
        try:
            # 步骤1: 创建任务
            if not self.create_task():
                logger.error("❌ 任务创建失败，停止监控")
                return False
            
            # 步骤2: 启动任务
            if not self.start_task():
                logger.error("❌ 任务启动失败，停止监控")
                return False
            
            # 步骤3: 监控进度
            self.monitor_task_progress()
            
            logger.info("🏁 监控流程完成")
            logger.info("="*60)
            return True
            
        except KeyboardInterrupt:
            logger.info("⚠️ 用户中断监控")
            return False
        except Exception as e:
            logger.error(f"❌ 监控流程异常: {e}")
            return False

if __name__ == "__main__":
    monitor = YiguxiaTaskMonitor()
    monitor.run_full_monitor()