# Archive Directory

这个目录用于存放项目中的非核心文件，保持主目录的整洁。

## 目录结构

### `/tests/`
存放所有测试文件 (`test_*.py`)
- 包含各种功能测试、集成测试和调试测试

### `/scripts/`
存放工具脚本和辅助文件
- `check_*.py` - 检查和验证脚本
- `debug_*.py` - 调试脚本
- `fix_*.py` - 修复脚本
- `monitor_*.py` - 监控脚本
- `verify_*.py` - 验证脚本
- 其他辅助工具脚本

### `/task_results/`
存放任务执行结果文件
- `task_result_*.json` - 任务执行结果
- `task_error_*.json` - 任务错误记录

### `/databases/`
存放数据库文件
- `*.db` - SQLite数据库文件
- 包含主数据库和备份数据库

### `/logs/`
存放日志文件
- `*.log` - 各种系统和任务日志

### `/backups/`
存放备份文件
- `web_app_backup_*.py` - Web应用备份文件
- `web_app_original.py` - 原始Web应用文件

## 使用说明

如果需要使用这些文件，可以直接从对应的子目录中找到。所有文件都按照功能和类型进行了分类，便于管理和查找。