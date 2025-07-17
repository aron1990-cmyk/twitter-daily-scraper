#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter抓取系统数据完整性和备份测试脚本
测试数据存储、备份恢复、数据一致性等功能
"""

import os
import sys
import json
import time
import sqlite3
import shutil
import hashlib
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

class DataIntegrityTester:
    def __init__(self, base_url="http://localhost:8084"):
        self.base_url = base_url
        self.test_results = []
        self.project_root = Path(__file__).parent
        self.data_dir = self.project_root / "data"
        self.backup_dir = self.project_root / "backup_test"
        
        # 确保测试目录存在
        self.backup_dir.mkdir(exist_ok=True)
        
    def log_test_result(self, test_name, success, details="", severity="INFO"):
        """记录测试结果"""
        result = {
            'test_name': test_name,
            'success': success,
            'details': details,
            'severity': severity,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        severity_emoji = {"INFO": "ℹ️", "WARNING": "⚠️", "ERROR": "🚨"}.get(severity, "ℹ️")
        print(f"   {status} {severity_emoji} {test_name}: {details}")
    
    def test_database_integrity(self):
        """测试数据库完整性"""
        print("🗄️ 测试数据库完整性...")
        
        # 查找数据库文件
        db_files = list(self.data_dir.glob("*.db")) + list(self.project_root.glob("*.db"))
        
        if not db_files:
            self.log_test_result(
                "数据库文件检查",
                False,
                "未找到数据库文件",
                "WARNING"
            )
            return False
        
        integrity_passed = 0
        total_dbs = len(db_files)
        
        for db_file in db_files:
            try:
                # 检查数据库文件完整性
                conn = sqlite3.connect(str(db_file))
                cursor = conn.cursor()
                
                # 执行PRAGMA integrity_check
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchone()
                
                if result and result[0] == 'ok':
                    integrity_passed += 1
                    self.log_test_result(
                        f"数据库完整性 - {db_file.name}",
                        True,
                        "完整性检查通过"
                    )
                else:
                    self.log_test_result(
                        f"数据库完整性 - {db_file.name}",
                        False,
                        f"完整性检查失败: {result}",
                        "ERROR"
                    )
                
                # 检查表结构
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                if tables:
                    self.log_test_result(
                        f"数据库表结构 - {db_file.name}",
                        True,
                        f"包含 {len(tables)} 个表"
                    )
                else:
                    self.log_test_result(
                        f"数据库表结构 - {db_file.name}",
                        False,
                        "数据库为空或无表",
                        "WARNING"
                    )
                
                conn.close()
                
            except Exception as e:
                self.log_test_result(
                    f"数据库访问 - {db_file.name}",
                    False,
                    f"无法访问数据库: {str(e)}",
                    "ERROR"
                )
        
        success_rate = integrity_passed / total_dbs if total_dbs > 0 else 0
        
        self.log_test_result(
            "数据库完整性总体",
            success_rate >= 0.8,
            f"完整性通过率: {success_rate:.1%} ({integrity_passed}/{total_dbs})",
            "ERROR" if success_rate < 0.5 else "WARNING" if success_rate < 0.8 else "INFO"
        )
        
        return success_rate >= 0.8
    
    def test_data_backup_restore(self):
        """测试数据备份和恢复"""
        print("\n💾 测试数据备份和恢复...")
        
        # 创建测试数据
        test_db = self.backup_dir / "test_backup.db"
        
        try:
            # 创建测试数据库
            conn = sqlite3.connect(str(test_db))
            cursor = conn.cursor()
            
            # 创建测试表
            cursor.execute("""
                CREATE TABLE test_tweets (
                    id INTEGER PRIMARY KEY,
                    content TEXT,
                    created_at TIMESTAMP,
                    user_id TEXT
                )
            """)
            
            # 插入测试数据
            test_data = [
                (1, "Test tweet 1", datetime.now(), "user1"),
                (2, "Test tweet 2", datetime.now(), "user2"),
                (3, "Test tweet 3", datetime.now(), "user3")
            ]
            
            cursor.executemany(
                "INSERT INTO test_tweets (id, content, created_at, user_id) VALUES (?, ?, ?, ?)",
                test_data
            )
            
            conn.commit()
            conn.close()
            
            # 计算原始文件哈希
            original_hash = self.calculate_file_hash(test_db)
            
            self.log_test_result(
                "测试数据创建",
                True,
                f"创建了包含 {len(test_data)} 条记录的测试数据库"
            )
            
            # 测试备份
            backup_file = self.backup_dir / "test_backup_copy.db"
            shutil.copy2(test_db, backup_file)
            
            backup_hash = self.calculate_file_hash(backup_file)
            
            if original_hash == backup_hash:
                self.log_test_result(
                    "数据备份",
                    True,
                    "备份文件哈希值匹配"
                )
            else:
                self.log_test_result(
                    "数据备份",
                    False,
                    "备份文件哈希值不匹配",
                    "ERROR"
                )
                return False
            
            # 测试数据恢复
            # 删除原文件
            test_db.unlink()
            
            # 从备份恢复
            shutil.copy2(backup_file, test_db)
            
            # 验证恢复的数据
            conn = sqlite3.connect(str(test_db))
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM test_tweets")
            count = cursor.fetchone()[0]
            
            if count == len(test_data):
                self.log_test_result(
                    "数据恢复",
                    True,
                    f"成功恢复 {count} 条记录"
                )
            else:
                self.log_test_result(
                    "数据恢复",
                    False,
                    f"恢复记录数不匹配: 期望 {len(test_data)}, 实际 {count}",
                    "ERROR"
                )
                conn.close()
                return False
            
            # 验证数据内容
            cursor.execute("SELECT * FROM test_tweets ORDER BY id")
            restored_data = cursor.fetchall()
            
            data_match = True
            for i, (original, restored) in enumerate(zip(test_data, restored_data)):
                if original[0] != restored[0] or original[1] != restored[1] or original[3] != restored[3]:
                    data_match = False
                    break
            
            if data_match:
                self.log_test_result(
                    "数据内容验证",
                    True,
                    "恢复的数据内容完全匹配"
                )
            else:
                self.log_test_result(
                    "数据内容验证",
                    False,
                    "恢复的数据内容不匹配",
                    "ERROR"
                )
            
            conn.close()
            
            # 清理测试文件
            try:
                test_db.unlink()
            except FileNotFoundError:
                pass
            try:
                backup_file.unlink()
            except FileNotFoundError:
                pass
            
            return data_match
            
        except Exception as e:
            self.log_test_result(
                "备份恢复测试",
                False,
                f"测试异常: {str(e)}",
                "ERROR"
            )
            return False
    
    def test_data_consistency(self):
        """测试数据一致性"""
        print("\n🔄 测试数据一致性...")
        
        # 查找现有数据库
        db_files = list(self.data_dir.glob("*.db")) + list(self.project_root.glob("*.db"))
        
        if not db_files:
            self.log_test_result(
                "数据一致性检查",
                False,
                "未找到数据库文件进行一致性检查",
                "WARNING"
            )
            return True  # 没有数据库也算通过
        
        consistency_issues = 0
        
        for db_file in db_files:
            try:
                conn = sqlite3.connect(str(db_file))
                cursor = conn.cursor()
                
                # 检查外键约束
                cursor.execute("PRAGMA foreign_key_check")
                fk_violations = cursor.fetchall()
                
                if fk_violations:
                    consistency_issues += 1
                    self.log_test_result(
                        f"外键约束 - {db_file.name}",
                        False,
                        f"发现 {len(fk_violations)} 个外键约束违反",
                        "ERROR"
                    )
                else:
                    self.log_test_result(
                        f"外键约束 - {db_file.name}",
                        True,
                        "外键约束检查通过"
                    )
                
                # 检查数据类型一致性
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                for table in tables:
                    table_name = table[0]
                    
                    # 获取表结构
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()
                    
                    # 检查每列的数据类型一致性
                    for column in columns:
                        col_name = column[1]
                        col_type = column[2]
                        
                        if col_type.upper() in ['INTEGER', 'INT']:
                            # 检查整数列是否包含非整数值
                            cursor.execute(f"""
                                SELECT COUNT(*) FROM {table_name} 
                                WHERE {col_name} IS NOT NULL 
                                AND TYPEOF({col_name}) != 'integer'
                            """)
                            
                            invalid_count = cursor.fetchone()[0]
                            if invalid_count > 0:
                                consistency_issues += 1
                                self.log_test_result(
                                    f"数据类型一致性 - {table_name}.{col_name}",
                                    False,
                                    f"发现 {invalid_count} 个非整数值",
                                    "WARNING"
                                )
                
                conn.close()
                
            except Exception as e:
                consistency_issues += 1
                self.log_test_result(
                    f"一致性检查 - {db_file.name}",
                    False,
                    f"检查异常: {str(e)}",
                    "ERROR"
                )
        
        self.log_test_result(
            "数据一致性总体",
            consistency_issues == 0,
            f"发现 {consistency_issues} 个一致性问题",
            "ERROR" if consistency_issues > 0 else "INFO"
        )
        
        return consistency_issues == 0
    
    def test_concurrent_data_access(self):
        """测试并发数据访问"""
        print("\n🔀 测试并发数据访问...")
        
        # 创建测试数据库
        test_db = self.backup_dir / "concurrent_test.db"
        
        try:
            # 初始化数据库
            conn = sqlite3.connect(str(test_db))
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE concurrent_test (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    thread_id INTEGER,
                    operation TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            
            # 并发写入测试
            def write_worker(thread_id, operations_count=10):
                """并发写入工作线程"""
                try:
                    conn = sqlite3.connect(str(test_db), timeout=30)
                    cursor = conn.cursor()
                    
                    for i in range(operations_count):
                        cursor.execute(
                            "INSERT INTO concurrent_test (thread_id, operation) VALUES (?, ?)",
                            (thread_id, f"write_{i}")
                        )
                        conn.commit()
                        time.sleep(0.01)  # 小延迟模拟真实操作
                    
                    conn.close()
                    return True
                    
                except Exception as e:
                    return False
            
            # 启动多个并发线程
            thread_count = 5
            operations_per_thread = 10
            
            with ThreadPoolExecutor(max_workers=thread_count) as executor:
                futures = [executor.submit(write_worker, i, operations_per_thread) 
                          for i in range(thread_count)]
                
                successful_threads = sum(1 for future in as_completed(futures) if future.result())
            
            # 验证并发写入结果
            conn = sqlite3.connect(str(test_db))
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM concurrent_test")
            total_records = cursor.fetchone()[0]
            
            expected_records = thread_count * operations_per_thread
            
            if total_records == expected_records:
                self.log_test_result(
                    "并发写入测试",
                    True,
                    f"成功写入 {total_records} 条记录 (期望: {expected_records})"
                )
            else:
                self.log_test_result(
                    "并发写入测试",
                    False,
                    f"记录数不匹配: 实际 {total_records}, 期望 {expected_records}",
                    "ERROR"
                )
            
            # 检查数据完整性
            cursor.execute("SELECT thread_id, COUNT(*) FROM concurrent_test GROUP BY thread_id")
            thread_counts = cursor.fetchall()
            
            integrity_ok = all(count == operations_per_thread for _, count in thread_counts)
            
            if integrity_ok:
                self.log_test_result(
                    "并发数据完整性",
                    True,
                    "所有线程的数据都完整写入"
                )
            else:
                self.log_test_result(
                    "并发数据完整性",
                    False,
                    "部分线程的数据丢失",
                    "ERROR"
                )
            
            conn.close()
            
            # 清理测试文件
            try:
                test_db.unlink()
            except FileNotFoundError:
                pass
            
            return total_records == expected_records and integrity_ok
            
        except Exception as e:
            self.log_test_result(
                "并发访问测试",
                False,
                f"测试异常: {str(e)}",
                "ERROR"
            )
            return False
    
    def test_data_export_import(self):
        """测试数据导出导入"""
        print("\n📤 测试数据导出导入...")
        
        # 查找现有数据库
        db_files = list(self.data_dir.glob("*.db")) + list(self.project_root.glob("*.db"))
        
        if not db_files:
            # 创建测试数据库
            test_db = self.backup_dir / "export_test.db"
            
            conn = sqlite3.connect(str(test_db))
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE export_test (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    value INTEGER,
                    created_at TIMESTAMP
                )
            """)
            
            # 插入测试数据
            test_data = [
                (1, "Item 1", 100, datetime.now()),
                (2, "Item 2", 200, datetime.now()),
                (3, "Item 3", 300, datetime.now())
            ]
            
            cursor.executemany(
                "INSERT INTO export_test VALUES (?, ?, ?, ?)",
                test_data
            )
            
            conn.commit()
            conn.close()
            
            db_files = [test_db]
        
        export_success = 0
        total_exports = 0
        
        for db_file in db_files[:2]:  # 限制测试数量
            try:
                conn = sqlite3.connect(str(db_file))
                
                # 获取所有表
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                for table in tables[:2]:  # 限制表数量
                    table_name = table[0]
                    total_exports += 1
                    
                    # 导出为CSV
                    export_file = self.backup_dir / f"{db_file.stem}_{table_name}.csv"
                    
                    try:
                        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                        df.to_csv(export_file, index=False)
                        
                        # 验证导出文件
                        if export_file.exists() and export_file.stat().st_size > 0:
                            export_success += 1
                            
                            # 测试重新导入
                            imported_df = pd.read_csv(export_file)
                            
                            if len(imported_df) == len(df):
                                self.log_test_result(
                                    f"数据导出导入 - {table_name}",
                                    True,
                                    f"成功导出导入 {len(df)} 行数据"
                                )
                            else:
                                self.log_test_result(
                                    f"数据导出导入 - {table_name}",
                                    False,
                                    f"导入数据行数不匹配: 原始 {len(df)}, 导入 {len(imported_df)}",
                                    "ERROR"
                                )
                                export_success -= 1
                        else:
                            self.log_test_result(
                                f"数据导出 - {table_name}",
                                False,
                                "导出文件为空或不存在",
                                "ERROR"
                            )
                        
                        # 清理导出文件
                        try:
                            export_file.unlink()
                        except FileNotFoundError:
                            pass
                        
                    except Exception as e:
                        self.log_test_result(
                            f"数据导出 - {table_name}",
                            False,
                            f"导出异常: {str(e)}",
                            "ERROR"
                        )
                
                conn.close()
                
            except Exception as e:
                self.log_test_result(
                    f"数据库访问 - {db_file.name}",
                    False,
                    f"无法访问数据库: {str(e)}",
                    "ERROR"
                )
        
        success_rate = export_success / total_exports if total_exports > 0 else 1
        
        self.log_test_result(
            "数据导出导入总体",
            success_rate >= 0.8,
            f"成功率: {success_rate:.1%} ({export_success}/{total_exports})",
            "ERROR" if success_rate < 0.5 else "WARNING" if success_rate < 0.8 else "INFO"
        )
        
        # 清理测试文件
        test_db = self.backup_dir / "export_test.db"
        try:
            test_db.unlink()
        except FileNotFoundError:
            pass
        
        return success_rate >= 0.8
    
    def test_storage_space_monitoring(self):
        """测试存储空间监控"""
        print("\n💽 测试存储空间监控...")
        
        try:
            # 检查数据目录空间使用
            if self.data_dir.exists():
                total_size = sum(f.stat().st_size for f in self.data_dir.rglob('*') if f.is_file())
                
                self.log_test_result(
                    "数据目录大小",
                    True,
                    f"数据目录总大小: {self.format_size(total_size)}"
                )
                
                # 检查大文件
                large_files = []
                for f in self.data_dir.rglob('*'):
                    if f.is_file() and f.stat().st_size > 100 * 1024 * 1024:  # 100MB
                        large_files.append((f, f.stat().st_size))
                
                if large_files:
                    self.log_test_result(
                        "大文件检查",
                        True,
                        f"发现 {len(large_files)} 个大文件 (>100MB)",
                        "WARNING"
                    )
                else:
                    self.log_test_result(
                        "大文件检查",
                        True,
                        "未发现异常大文件"
                    )
            
            # 检查磁盘空间
            disk_usage = shutil.disk_usage(self.project_root)
            free_space_gb = disk_usage.free / (1024**3)
            
            if free_space_gb > 1:  # 至少1GB可用空间
                self.log_test_result(
                    "磁盘空间检查",
                    True,
                    f"可用空间: {free_space_gb:.1f} GB"
                )
            else:
                self.log_test_result(
                    "磁盘空间检查",
                    False,
                    f"磁盘空间不足: {free_space_gb:.1f} GB",
                    "ERROR"
                )
                return False
            
            return True
            
        except Exception as e:
            self.log_test_result(
                "存储空间监控",
                False,
                f"监控异常: {str(e)}",
                "ERROR"
            )
            return False
    
    def calculate_file_hash(self, file_path):
        """计算文件哈希值"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def format_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def run_comprehensive_test(self):
        """运行综合数据完整性测试"""
        print("💾 Twitter抓取系统数据完整性测试")
        print("=" * 60)
        
        # 数据完整性测试套件
        test_suites = [
            ('数据库完整性', self.test_database_integrity),
            ('数据备份恢复', self.test_data_backup_restore),
            ('数据一致性', self.test_data_consistency),
            ('并发数据访问', self.test_concurrent_data_access),
            ('数据导出导入', self.test_data_export_import),
            ('存储空间监控', self.test_storage_space_monitoring)
        ]
        
        passed_tests = 0
        total_tests = len(test_suites)
        
        for test_name, test_func in test_suites:
            try:
                if test_func():
                    passed_tests += 1
                    print(f"✅ {test_name}: 通过\n")
                else:
                    print(f"❌ {test_name}: 失败\n")
            except Exception as e:
                print(f"❌ {test_name}: 异常 - {str(e)}\n")
        
        # 生成数据完整性报告
        self.generate_integrity_report(passed_tests, total_tests)
        
        return passed_tests == total_tests
    
    def generate_integrity_report(self, passed_tests, total_tests):
        """生成数据完整性测试报告"""
        print("=" * 60)
        print("💾 数据完整性测试总结")
        print("=" * 60)
        print(f"总测试套件: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {total_tests - passed_tests} ❌")
        print(f"成功率: {(passed_tests/total_tests*100):.1f}%")
        
        # 严重性评估
        error_count = sum(1 for result in self.test_results if result.get('severity') == 'ERROR' and not result['success'])
        warning_count = sum(1 for result in self.test_results if result.get('severity') == 'WARNING' and not result['success'])
        info_count = sum(1 for result in self.test_results if result.get('severity') == 'INFO' and not result['success'])
        
        print(f"\n🚨 问题严重性分析:")
        print(f"严重错误: {error_count} 🔴")
        print(f"警告: {warning_count} 🟡")
        print(f"信息: {info_count} 🟢")
        
        # 详细结果统计
        success_count = sum(1 for result in self.test_results if result['success'])
        total_count = len(self.test_results)
        
        print(f"\n详细测试项: {total_count}")
        print(f"成功: {success_count}")
        print(f"失败: {total_count - success_count}")
        print(f"详细成功率: {(success_count/total_count*100):.1f}%")
        
        # 保存详细报告
        report_file = self.project_root / "data_integrity_test_report.json"
        report_data = {
            'test_summary': {
                'total_suites': total_tests,
                'passed_suites': passed_tests,
                'suite_success_rate': passed_tests/total_tests,
                'total_tests': total_count,
                'passed_tests': success_count,
                'test_success_rate': success_count/total_count,
                'timestamp': datetime.now().isoformat()
            },
            'severity_analysis': {
                'error_issues': error_count,
                'warning_issues': warning_count,
                'info_issues': info_count
            },
            'detailed_results': self.test_results
        }
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            print(f"\n📄 详细报告已保存: {report_file}")
        except Exception as e:
            print(f"\n⚠️ 无法保存报告: {str(e)}")
        
        # 数据完整性评估
        print("\n" + "=" * 60)
        print("💾 数据完整性评估")
        print("=" * 60)
        
        if error_count == 0 and warning_count <= 1:
            print("🎉 数据状态: 优秀 - 数据完整性良好")
        elif error_count == 0 and warning_count <= 3:
            print("✅ 数据状态: 良好 - 存在少量警告")
        elif error_count <= 1:
            print("⚠️ 数据状态: 一般 - 需要关注数据问题")
        else:
            print("❌ 数据状态: 需要修复 - 存在严重数据问题")
        
        print("\n💾 数据管理建议:")
        print("1. 定期进行数据库完整性检查")
        print("2. 建立自动化备份机制")
        print("3. 实施数据一致性验证")
        print("4. 监控存储空间使用情况")
        print("5. 测试数据恢复流程")
        print("6. 实施并发访问控制")
        print("7. 定期清理和归档旧数据")
        
        # 清理测试目录
        try:
            if self.backup_dir.exists():
                shutil.rmtree(self.backup_dir)
        except:
            pass

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Twitter抓取系统数据完整性测试')
    parser.add_argument('--url', default='http://localhost:8084', 
                       help='Web服务器地址 (默认: http://localhost:8084)')
    
    args = parser.parse_args()
    
    tester = DataIntegrityTester(args.url)
    tester.run_comprehensive_test()

if __name__ == '__main__':
    main()