# Twitter抓取管理系统 - 项目结构说明

## 📁 目录结构

```
twitter-daily-scraper/
├── 📁 core/                    # 核心业务模块
│   ├── async_feishu_sync.py    # 飞书异步同步
│   ├── enhanced_tweet_scraper.py # 增强推文抓取器
│   ├── enhanced_twitter_parser.py # 增强推文解析器
│   ├── refactored_task_manager.py # 重构任务管理器
│   ├── twitter_parser.py       # 推文解析器
│   └── twitter_scraping_engine.py # 推文抓取引擎
│
├── 📁 utils/                   # 工具类模块
│   ├── account_manager.py      # 账户管理
│   ├── account_state_tracker.py # 账户状态跟踪
│   ├── ads_browser_launcher.py # AdsPower浏览器启动器
│   ├── ai_analyzer.py          # AI分析器
│   ├── background_task_runner.py # 后台任务运行器
│   ├── browser_manager.py      # 浏览器管理
│   ├── cloud_sync.py           # 云同步
│   ├── config_manager.py       # 配置管理
│   ├── data_extractor.py       # 数据提取器
│   ├── excel_writer.py         # Excel写入器
│   ├── exception_handler.py    # 异常处理器
│   ├── exceptions.py           # 自定义异常
│   ├── feishu_data_validator.py # 飞书数据验证器
│   ├── human_behavior_simulator.py # 人类行为模拟器
│   ├── management_console.py   # 管理控制台
│   ├── monitoring.py           # 监控模块
│   ├── multi_blogger_task_system.py # 多博主任务系统
│   ├── retry_utils.py          # 重试工具
│   ├── storage_manager.py      # 存储管理器
│   ├── system_monitor.py       # 系统监控
│   └── tweet_filter.py         # 推文过滤器
│
├── 📁 templates/               # HTML模板
│   ├── base.html              # 基础模板
│   ├── index.html             # 首页
│   ├── tasks.html             # 任务管理页面
│   ├── data.html              # 数据查看页面
│   ├── config.html            # 配置页面
│   ├── scheduler.html         # 定时任务页面
│   └── ...
│
├── 📁 static/                  # 静态资源
│   └── js/                    # JavaScript文件
│
├── 📁 config/                  # 配置文件
│   ├── batch_config.yaml      # 批量配置
│   └── feishu_config.json     # 飞书配置
│
├── 📁 data/                    # 数据目录
│   ├── accounts/              # 账户数据
│   ├── batch_results/         # 批量结果
│   ├── exports/               # 导出文件
│   ├── logs/                  # 日志文件
│   └── tweets/                # 推文数据
│
├── 📁 instance/                # 实例数据
│   └── twitter_scraper.db     # 主数据库
│
├── 📁 accounts/                # 账户配置
│   └── accounts.json          # 账户信息
│
├── 📁 scripts/                 # 脚本文件
│   └── prd.txt                # 产品需求文档
│
├── 📁 logs/                    # 系统日志
│   ├── background_task.log    # 后台任务日志
│   ├── batch_scraper.log      # 批量抓取日志
│   └── feishu_rate_limit_test.log # 飞书限流测试日志
│
├── 📁 exports/                 # 导出文件（已整理）
│   ├── test_export.xlsx       # 测试导出
│   ├── tweets_*.xlsx          # 推文导出文件
│   └── twitter_daily_*.xlsx   # 每日推文导出
│
├── 📁 task_results/            # 任务结果（已整理）
│   └── task_result_*.json     # 任务结果JSON文件
│
├── 📁 tests/                   # 测试文件（已整理）
│   ├── test_*.py              # 各种测试脚本
│   └── __init__.py            # Python包初始化
│
├── 📁 debug_scripts/           # 调试脚本（已整理）
│   ├── check_*.py             # 检查脚本
│   ├── debug_*.py             # 调试脚本
│   ├── fix_*.py               # 修复脚本
│   ├── verify_*.py            # 验证脚本
│   └── sync_*.py              # 同步脚本
│
├── 📁 archive/                 # 归档文件
│   ├── auto_sync_fix_report.md # 自动同步修复报告
│   ├── task5_full.html        # 任务5完整页面
│   ├── databases/             # 数据库备份
│   ├── backups/               # 备份文件
│   └── ...
│
├── 📄 web_app.py               # Flask Web应用主文件
├── 📄 main.py                  # 主程序入口
├── 📄 run.py                   # 运行脚本
├── 📄 scheduler.py             # 调度器
├── 📄 models.py                # 数据模型
├── 📄 config.py                # 配置文件
├── 📄 requirements.txt         # Python依赖
├── 📄 package.json             # Node.js依赖
├── 📄 README.md                # 项目说明
├── 📄 .gitignore               # Git忽略文件
└── 📄 PROJECT_STRUCTURE.md     # 项目结构说明（本文件）
```

## 🎯 模块分类说明

### 核心业务模块 (core/)
- **twitter_scraping_engine.py**: 推文抓取的核心引擎
- **enhanced_tweet_scraper.py**: 增强版推文抓取器，支持更多功能
- **refactored_task_manager.py**: 重构后的任务管理器，负责任务调度和管理
- **async_feishu_sync.py**: 飞书异步同步模块，处理数据同步到飞书
- **twitter_parser.py**: 推文解析器，解析推文内容和元数据

### 工具类模块 (utils/)
- **账户管理**: account_manager.py, account_state_tracker.py
- **浏览器管理**: browser_manager.py, ads_browser_launcher.py
- **数据处理**: data_extractor.py, excel_writer.py, tweet_filter.py
- **系统监控**: system_monitor.py, monitoring.py
- **配置管理**: config_manager.py
- **异常处理**: exception_handler.py, exceptions.py, retry_utils.py

### 已整理的目录
- **tests/**: 所有测试文件，包含单元测试和集成测试
- **debug_scripts/**: 调试和诊断脚本，用于问题排查
- **exports/**: 导出的Excel文件，按时间和任务ID组织
- **task_results/**: 任务执行结果的JSON文件
- **archive/**: 归档的旧文件和备份

## 🚀 快速开始

1. **安装依赖**:
   ```bash
   pip install -r requirements.txt
   ```

2. **启动Web应用**:
   ```bash
   python3 web_app_optimized.py  # 推荐使用优化版本
# python web_app.py  # 已注释掉，不再使用
   ```

3. **访问管理界面**:
   - 浏览器打开: http://localhost:8090
   - 功能包括: 任务管理、数据查看、系统配置、定时任务等

## 📝 维护说明

- **日志文件**: 定期清理 `logs/` 目录下的日志文件
- **导出文件**: `exports/` 目录下的Excel文件可定期归档
- **任务结果**: `task_results/` 目录下的JSON文件可定期清理
- **测试文件**: `tests/` 目录下的测试脚本需要根据代码变更及时更新
- **调试脚本**: `debug_scripts/` 目录下的脚本在问题解决后可以归档

## 🔧 配置文件

- **config/feishu_config.json**: 飞书API配置
- **config/batch_config.yaml**: 批量处理配置
- **accounts/accounts.json**: 账户信息配置

## 📊 数据库

- **instance/twitter_scraper.db**: 主数据库，存储任务、推文、用户等数据
- **archive/databases/**: 数据库备份文件

---

*最后更新: 2025-01-28*
*版本: v2.0 - 重构整理版*