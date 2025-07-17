#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub文档同步更新工具
自动同步本地文档到GitHub，确保文档版本一致性
"""

import os
import subprocess
import json
from datetime import datetime
from pathlib import Path

class GitHubDocSync:
    def __init__(self, repo_path="."):
        self.repo_path = Path(repo_path)
        self.docs_files = [
            "README.md",
            "README_BATCH_SYSTEM.md", 
            "FIXES_SUMMARY.md",
            "COMPLETE_ARCHITECTURE.md",
            "COMPLETE_USER_GUIDE.md",
            "PERFORMANCE_OPTIMIZATION.md",
            "TECHNICAL_IMPLEMENTATION.md",
            "TESTING_FRAMEWORK_SUMMARY.md",
            "tests/README.md"
        ]
        
    def check_git_status(self):
        """检查Git状态"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            return result.stdout.strip()
        except Exception as e:
            print(f"检查Git状态失败: {e}")
            return None
            
    def get_doc_changes(self):
        """获取文档变更"""
        status = self.check_git_status()
        if not status:
            return []
            
        changed_docs = []
        for line in status.split('\n'):
            if line.strip():
                status_code = line[:2]
                file_path = line[3:].strip()
                
                # 检查是否为文档文件
                if any(doc in file_path for doc in self.docs_files):
                    changed_docs.append({
                        'status': status_code,
                        'file': file_path
                    })
                    
        return changed_docs
        
    def sync_docs(self, commit_message=None):
        """同步文档到GitHub"""
        print("🔄 开始同步GitHub文档...")
        
        # 检查文档变更
        changes = self.get_doc_changes()
        if not changes:
            print("✅ 没有文档需要同步")
            return True
            
        print(f"📝 发现 {len(changes)} 个文档变更:")
        for change in changes:
            print(f"  {change['status']} {change['file']}")
            
        # 添加文档文件
        try:
            for doc_file in self.docs_files:
                doc_path = self.repo_path / doc_file
                if doc_path.exists():
                    subprocess.run(
                        ["git", "add", str(doc_file)],
                        cwd=self.repo_path,
                        check=True
                    )
                    
            # 提交变更
            if not commit_message:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                commit_message = f"📚 文档同步更新 - {timestamp}"
                
            subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=self.repo_path,
                check=True
            )
            
            # 推送到GitHub
            subprocess.run(
                ["git", "push", "origin", "main"],
                cwd=self.repo_path,
                check=True
            )
            
            print("✅ 文档同步完成")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ 文档同步失败: {e}")
            return False
            
    def generate_sync_report(self):
        """生成同步报告"""
        report = {
            "sync_time": datetime.now().isoformat(),
            "docs_status": {},
            "total_docs": len(self.docs_files),
            "synced_docs": 0
        }
        
        for doc_file in self.docs_files:
            doc_path = self.repo_path / doc_file
            if doc_path.exists():
                stat = doc_path.stat()
                report["docs_status"][doc_file] = {
                    "exists": True,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                }
                report["synced_docs"] += 1
            else:
                report["docs_status"][doc_file] = {
                    "exists": False
                }
                
        return report
        
    def auto_sync_watch(self, interval=300):
        """自动监控并同步文档"""
        import time
        
        print(f"🔍 开始监控文档变更 (每{interval}秒检查一次)")
        
        while True:
            try:
                changes = self.get_doc_changes()
                if changes:
                    print(f"📝 检测到文档变更，开始同步...")
                    self.sync_docs()
                    
                time.sleep(interval)
                
            except KeyboardInterrupt:
                print("\n⏹️ 停止监控")
                break
            except Exception as e:
                print(f"❌ 监控过程中出错: {e}")
                time.sleep(interval)

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="GitHub文档同步工具")
    parser.add_argument("--sync", action="store_true", help="立即同步文档")
    parser.add_argument("--watch", action="store_true", help="监控模式")
    parser.add_argument("--report", action="store_true", help="生成同步报告")
    parser.add_argument("--message", "-m", help="自定义提交信息")
    parser.add_argument("--interval", type=int, default=300, help="监控间隔(秒)")
    
    args = parser.parse_args()
    
    sync_tool = GitHubDocSync()
    
    if args.sync:
        sync_tool.sync_docs(args.message)
    elif args.watch:
        sync_tool.auto_sync_watch(args.interval)
    elif args.report:
        report = sync_tool.generate_sync_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        # 默认执行同步
        sync_tool.sync_docs(args.message)

if __name__ == "__main__":
    main()