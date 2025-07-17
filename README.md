# Twitter 日报采集系统

基于 AdsPower 虚拟浏览器的自动化 Twitter 信息采集系统，用于构建"日报矩阵"项目。

## 功能特性

### 核心功能
- 🚀 **AdsPower 集成**: 使用 AdsPower 虚拟浏览器环境，避免账号风险
- 🎯 **多目标采集**: 支持指定博主主页和关键词搜索两种采集方式
- 🔍 **智能筛选**: 根据互动数（点赞/评论/转发）和关键词自动筛选优质推文
- 📊 **Excel 报表**: 自动生成包含统计信息的 Excel 日报
- ☁️ **云端同步**: 支持自动同步数据到 Google Sheets 和飞书文档
- 🛡️ **反检测**: 模拟真实用户行为，降低被检测风险
- 📝 **详细日志**: 完整的操作日志记录，便于调试和监控

### 增强功能 🆕
- 🤖 **AI内容分析**: 智能评估推文质量、情感倾向和趋势相关性
- 👥 **多账户管理**: 自动轮换AdsPower账户，提高采集效率和安全性
- ⏰ **任务调度**: 支持定时任务和自动化采集
- 📈 **系统监控**: 实时监控系统资源和性能指标
- 🎛️ **统一管理**: 提供命令行管理控制台，集中管理所有功能
- ⚙️ **配置管理**: 集中化配置管理，支持备份和恢复
- ⚡ **性能优化**: 批处理、缓存和并发优化

### 技术特性
- 🔧 **配置灵活**: 支持多种配置方式，适应不同采集需求
- 🛠️ **错误处理**: 完善的异常处理和自动恢复机制
- 🔌 **扩展性强**: 模块化设计，易于扩展和定制

## 系统要求

- Python 3.7+
- AdsPower 浏览器客户端
- macOS / Windows / Linux

## 安装步骤

1. **克隆或下载项目**
   ```bash
   # 如果使用 git
   git clone <repository-url>
   cd twitter-daily-scraper
   
   # 或直接下载并解压到目标目录
   ```

2. **安装依赖包**
   ```bash
   # 如果遇到SSL证书问题，使用以下命令
   pip3 install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt
   
   # 安装 Playwright 浏览器
   python3 -m playwright install
   ```
   
   或者运行自动安装脚本：
   ```bash
   python3 setup.py
   ```

3. **验证配置**
   ```bash
   # 验证配置文件
   python3 validate_config.py
   ```

4. **配置系统**
   - 编辑 `config.py` 文件
   - 设置 AdsPower 配置
   - 配置采集目标和筛选条件

### 5. 配置 AdsPower

1. 启动 AdsPower 客户端
2. 创建或选择一个浏览器配置文件
3. 记录配置文件的用户ID
4. 确保 Local API 服务已启用（默认端口 50325）

## 配置说明

### 主要配置文件：`config.py`

#### AdsPower 配置

```python
ADS_POWER_CONFIG = {
    'local_api_url': 'http://local.adspower.net:50325',  # AdsPower API 地址
    'user_id': 'YOUR_USER_ID',  # 替换为你的 AdsPower 用户ID
    'group_id': '',  # 分组ID（可选）
}
```

#### 采集目标配置

```python
TWITTER_TARGETS = {
    # 目标账号列表（不包含@符号）
    'accounts': [
        'elonmusk',
        'OpenAI',
        'sama',
    ],
    
    # 搜索关键词列表
    'keywords': [
        'AI',
        '副业',
        'daily',
        '人工智能',
        'ChatGPT',
    ]
}
```

#### 筛选条件配置

```python
FILTER_CONFIG = {
    'min_likes': 100,      # 最小点赞数
    'min_comments': 30,    # 最小评论数
    'min_retweets': 50,    # 最小转发数
    
    # 特定关键词筛选（包含任一关键词即通过）
    'keywords_filter': ['AI', '副业', 'daily', '人工智能', 'ChatGPT'],
    
    # 最大抓取数量
    'max_tweets_per_target': 10,
}
```

#### 云端同步配置

```python
CLOUD_SYNC_CONFIG = {
    'google_sheets': {
        'enabled': False,  # 启用 Google Sheets 同步
        'credentials_file': 'path/to/service-account-key.json',
        'spreadsheet_id': 'your_spreadsheet_id',
        'worksheet_name': 'Twitter数据'
    },
    'feishu': {
        'enabled': False,  # 启用飞书文档同步
        'app_id': 'your_app_id',
        'app_secret': 'your_app_secret',
        'spreadsheet_token': 'your_spreadsheet_token',
        'sheet_id': 'your_sheet_id'
    }
}
```

## 使用方法

### 快速开始（增强版）🆕

1. **一键设置**
   ```bash
   python3 setup_enhanced.py
   ```

2. **配置账户和目标**
   - 编辑 `config_enhanced.py` 中的配置
   - 编辑 `accounts/accounts.json` 中的账户信息

3. **运行采集任务**
   ```bash
   # 快速启动（包含AI分析）
   ./quick_start.sh
   
   # 或使用Python命令
   python3 run_enhanced.py --mode scrape --ai-analysis
   ```

4. **启动管理控制台**
   ```bash
   ./start_console.sh
   # 或
   python3 run_enhanced.py --mode console
   ```

5. **启动任务调度器**
   ```bash
   ./start_scheduler.sh
   # 或
   python3 run_enhanced.py --mode schedule
   ```

### 快速启动（推荐）

```bash
# 快速启动采集任务
python3 run.py

# 查看配置摘要
python3 run.py --check-config

# 检查 AdsPower 连接
python3 run.py --check-adspower

# 强制运行（忽略连接检查）
python3 run.py --force

# 调试模式
python3 run.py --debug

# 测试云端同步配置
python3 test_cloud_sync.py
```

### 传统方式

1. **启动 AdsPower 客户端**

2. **验证配置**
   ```bash
   python3 validate_config.py
   ```

3. **运行采集程序**
   ```bash
   python3 main.py
   ```

4. **查看结果**
   - 程序会在 `data/` 目录下生成 Excel 报表
   - 日志文件保存在 `logs/` 目录下

## 增强功能详解 🆕

### AI内容分析

AI分析器提供智能内容评估功能：

```python
# AI分析配置
AI_ANALYZER_CONFIG = {
    'quality_weights': {
        'content_length': 0.15,     # 内容长度权重
        'structure_score': 0.20,    # 结构评分权重
        'richness_score': 0.25,     # 丰富度权重
        'language_quality': 0.20,   # 语言质量权重
        'professionalism': 0.20     # 专业度权重
    },
    'sentiment_keywords': {
        'positive': ['好', '棒', '优秀', 'great', 'excellent'],
        'negative': ['差', '糟糕', '失败', 'bad', 'terrible']
    },
    'trending_keywords': ['AI', '人工智能', 'ChatGPT', '机器学习']
}
```

**AI分析功能包括：**
- 推文质量评分（0-100分）
- 情感分析（正面/中性/负面）
- 参与度预测
- 趋势相关性分析
- 作者影响力评估

### 多账户管理

自动管理和轮换AdsPower账户：

```json
// accounts/accounts.json
{
  "accounts": [
    {
      "user_id": "ads_user_1",
      "name": "主账户",
      "priority": 1,
      "daily_limit": 15,
      "hourly_limit": 3,
      "tags": ["primary", "high_quality"]
    }
  ]
}
```

**账户管理功能：**
- 智能轮换策略（轮询/优先级/随机）
- 使用限制和冷却时间
- 健康状态监控
- 自动故障恢复

### 任务调度

支持定时和自动化任务：

```python
# 调度器配置
SCHEDULER_CONFIG = {
    'scheduled_tasks': [
        {
            'id': 'daily_scraping',
            'name': '每日Twitter采集',
            'trigger': 'cron',
            'hour': 9,
            'minute': 0,
            'enabled': True
        }
    ]
}
```

**调度功能：**
- 定时任务（cron表达式）
- 间隔任务（固定间隔）
- 任务重试和超时控制
- 任务状态监控

### 系统监控

实时监控系统性能和资源使用：

```python
# 监控配置
SYSTEM_MONITOR_CONFIG = {
    'alert_rules': [
        {
            'name': 'high_cpu_usage',
            'metric': 'cpu_percent',
            'threshold': 80.0,
            'severity': 'warning'
        }
    ]
}
```

**监控功能：**
- CPU、内存、磁盘使用率
- 进程性能指标
- 自定义告警规则
- 历史数据记录

### 管理控制台

统一的命令行管理界面：

```bash
# 启动控制台
python3 run_enhanced.py --mode console

# 控制台命令示例
> status              # 查看系统状态
> scrape start        # 开始采集
> accounts list       # 查看账户列表
> schedule list       # 查看调度任务
> ai analyze          # 运行AI分析
> config backup       # 备份配置
```

### 高级用法

#### 1. 基本使用

```bash
python3 main.py
```

#### 2. 指定 AdsPower 用户ID

```python
# 在 main.py 中修改
output_file = await scraper.run_scraping_task(user_id="your_user_id")
```

#### 3. 自定义配置

```python
# 动态修改筛选条件
scraper.filter_engine.update_filter_config(
    min_likes=200,
    min_comments=50,
    keywords_filter=['新关键词']
)
```

#### 4. 自定义过滤条件

可以通过修改 `config.py` 中的 `FILTER_CONFIG` 来自定义过滤条件：

```python
FILTER_CONFIG = {
    'min_likes': 50,        # 最少点赞数
    'min_retweets': 10,     # 最少转发数
    'min_comments': 5,      # 最少评论数
    'exclude_keywords': ['广告', 'spam'],  # 排除关键词
    'include_keywords': ['技术', '创新'],   # 包含关键词
    'min_content_length': 20,              # 最短内容长度
    'max_content_length': 500,             # 最长内容长度
    'language_filter': ['zh', 'en'],       # 语言过滤
    'time_range': {
        'start_hours_ago': 24,  # 开始时间（小时前）
        'end_hours_ago': 0      # 结束时间（小时前）
    }
}
```

#### 5. 批量处理多个目标

```python
TWITTER_TARGETS = {
    'users': [
        {'username': 'user1', 'max_tweets': 100},
        {'username': 'user2', 'max_tweets': 50},
        # 添加更多用户...
    ],
    'keywords': [
        {'keyword': '关键词1', 'max_tweets': 200},
        {'keyword': '关键词2', 'max_tweets': 150},
        # 添加更多关键词...
    ]
}
```

## 输出说明

### Excel 报表结构

生成的 Excel 文件包含两个工作表：

#### 1. Twitter数据表

| 列名 | 说明 |
|------|------|
| 序号 | 推文序号 |
| 账号 | 推文作者 |
| 推文内容 | 推文文本内容 |
| 发布时间 | 推文发布时间 |
| 点赞数 | 点赞数量 |
| 评论数 | 评论数量 |
| 转发数 | 转发数量 |
| 推文链接 | 推文URL |
| 来源 | 采集来源（用户名或关键词） |
| 来源类型 | 采集类型（user_profile/keyword_search） |
| 筛选原因 | 通过筛选的原因 |

#### 2. 汇总统计表

- 总推文数
- 通过筛选推文数
- 筛选通过率
- 互动数据统计
- 筛选原因统计

### 文件命名规则

```
data/twitter_daily_YYYYMMDD.xlsx
```

例如：`data/twitter_daily_20240101.xlsx`

## 项目结构

```
twitter-daily-scraper/
├── 核心模块
│   ├── main.py                    # 主程序入口
│   ├── config.py                  # 基础配置文件
│   ├── ads_browser_launcher.py    # AdsPower浏览器启动器
│   ├── twitter_parser.py          # Twitter页面解析器
│   ├── tweet_filter.py            # 推文过滤器
│   ├── excel_writer.py            # Excel导出器
│   └── cloud_sync.py              # 云同步管理器
│
├── 增强功能模块 🆕
│   ├── ai_analyzer.py             # AI内容分析器
│   ├── account_manager.py         # 多账户管理器
│   ├── scheduler.py               # 任务调度器
│   ├── system_monitor.py          # 系统监控器
│   ├── config_manager.py          # 配置管理器
│   └── management_console.py      # 管理控制台
│
├── 启动脚本
│   ├── run.py                     # 传统启动脚本
│   ├── run_enhanced.py            # 增强版启动脚本 🆕
│   ├── quick_start.sh             # 快速启动脚本 🆕
│   ├── start_console.sh           # 控制台启动脚本 🆕
│   └── start_scheduler.sh         # 调度器启动脚本 🆕
│
├── 配置和设置
│   ├── config_enhanced.py         # 增强版配置文件 🆕
│   ├── config_enhanced_example.py # 配置示例文件 🆕
│   ├── setup.py                   # 基础环境设置
│   ├── setup_enhanced.py          # 增强版设置脚本 🆕
│   └── requirements.txt           # 依赖包列表
│
├── 工具脚本
│   ├── validate_config.py         # 配置验证工具
│   └── test_cloud_sync.py         # 云同步测试工具
│
├── 数据目录 🆕
│   ├── configs/                   # 配置文件目录
│   ├── accounts/                  # 账户配置目录
│   ├── logs/                      # 日志文件目录
│   ├── data/                      # 数据文件目录
│   ├── exports/                   # 导出文件目录
│   ├── cache/                     # 缓存文件目录
│   └── reports/                   # 报告文件目录
│
└── 文档
    ├── README.md                  # 项目说明文档
    └── CLOUD_SYNC_SETUP.md        # 云同步设置指南
```

## 模块说明

### 核心模块

#### 1. main.py
主程序入口，协调各个模块的工作流程：
- 处理异常和错误恢复
- 生成执行报告
- 集成AI分析和增强功能 🆕

#### 2. config.py
基础系统配置文件，包含所有可配置参数：
- 支持环境变量覆盖
- 配置验证和默认值设置

#### 3. ads_browser_launcher.py (AdsPower 浏览器启动器)

- 启动和停止 AdsPower 浏览器
- 获取浏览器调试端口
- 监控浏览器状态
- 自动重试和错误处理

#### 4. twitter_parser.py (Twitter 解析器)

- 连接到 AdsPower 浏览器
- 导航到 Twitter 页面
- 解析推文数据
- 处理用户主页和关键词搜索
- 反爬虫机制应对

#### 5. tweet_filter.py (推文筛选器)

- 根据互动数筛选推文
- 关键词匹配筛选
- 生成筛选统计信息
- 多维度过滤条件
- 智能去重算法

#### 6. excel_writer.py (Excel 输出器)

- 生成格式化的 Excel 报表
- 创建汇总统计表
- 自动调整列宽和样式
- 支持AI分析结果导出 🆕
- 图表和统计生成

#### 7. cloud_sync.py (云端同步管理器)

- 支持 Google Sheets API 集成
- 支持飞书文档 API 集成
- 自动同步 Excel 数据到云端平台
- 统一的同步接口和错误处理

### 增强功能模块 🆕

#### 8. ai_analyzer.py (AI内容分析器)

- 推文质量评估和评分
- 情感分析和趋势识别
- 参与度预测和作者影响力分析
- 批量处理和洞察报告生成

#### 9. account_manager.py (多账户管理器)

- AdsPower账户轮换和负载均衡
- 使用限制和冷却时间管理
- 健康状态监控和自动恢复
- 账户优先级和标签管理

#### 10. scheduler.py (任务调度器)

- 定时任务和间隔任务调度
- 任务重试和超时控制
- 任务状态监控和报告
- 预定义任务模板

#### 11. system_monitor.py (系统监控器)

- 实时系统资源监控
- 自定义告警规则和通知
- 历史数据记录和分析
- 性能指标统计和报告

#### 12. config_manager.py (配置管理器)

- 集中化配置文件管理
- 配置备份和恢复
- 配置验证和版本控制
- 多格式配置支持

#### 13. management_console.py (管理控制台)

- 统一的命令行管理界面
- 交互式操作和状态查看
- 批量操作和脚本支持
- 实时监控和控制

### 启动脚本

#### 14. run.py (传统启动脚本)
快速启动脚本，提供友好的命令行界面：
- 配置检查和验证
- AdsPower 连接状态检查
- 一键启动采集任务
- 调试模式支持

#### 15. run_enhanced.py (增强版启动脚本) 🆕

- 多模式运行支持（采集/调度/控制台/监控）
- 命令行参数解析和配置
- 增强功能集成和管理
- 调试和试运行模式

### 辅助工具

#### 16. validate_config.py (配置验证)
配置验证工具，帮助用户检查配置文件：
- 验证 AdsPower 连接
- 检查配置参数有效性
- 提供修复建议
- 测试系统就绪状态

#### 17. setup.py (基础环境设置)
自动安装脚本，简化环境配置：
- 自动安装依赖包
- 处理 SSL 证书问题
- 安装 Playwright 浏览器
- 创建必要目录结构

#### 18. setup_enhanced.py (增强版设置脚本) 🆕

- 一键完整环境设置
- 配置文件生成和初始化
- 目录结构创建和权限设置
- 功能模块测试和验证

#### 19. test_cloud_sync.py (云同步测试)
云端同步测试工具：
- 测试 Google Sheets 连接和权限
- 测试飞书文档 API 配置
- 验证数据同步功能
- 提供详细的测试报告

## 常见问题

### Q: SSL 证书验证失败
A: 这是常见的网络问题，解决方案：
```bash
# 使用可信主机安装依赖
pip3 install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt
```

### Q: python 命令未找到
A: 在 macOS 上使用 `python3` 替代 `python`：
```bash
python3 run.py
python3 main.py
```

### Q1: AdsPower 连接失败

**解决方案：**
1. 确保 AdsPower 客户端正在运行
2. 检查 Local API 是否启用
3. 验证用户ID是否正确
4. 确认防火墙没有阻止连接
5. 运行配置验证：`python3 validate_config.py`

### Q2: 推文抓取失败

**解决方案：**
1. 检查网络连接
2. 确认 Twitter 账号是否需要登录
3. 调整 `BROWSER_CONFIG` 中的超时时间
4. 检查目标用户是否存在或账号是否公开
5. 使用调试模式查看详细错误：`python3 run.py --debug`

### Q3: 没有推文通过筛选

**解决方案：**
1. 降低筛选阈值（`FILTER_CONFIG`）
2. 增加关键词列表
3. 检查目标账号的推文质量
4. 调整抓取数量

### Q4: Excel 文件生成失败

**解决方案：**
1. 确保 `data` 目录存在且有写入权限
2. 检查磁盘空间是否充足
3. 确认没有其他程序占用同名文件
4. 运行配置验证确保输出目录可写

### Q: 配置文件错误
A: 使用配置验证工具：
```bash
python3 validate_config.py
```
该工具会检查所有配置项并提供修复建议。

### Q5: 云端同步失败

**解决方案：**
1. 检查网络连接是否正常
2. 验证 API 凭据是否正确配置
3. 确认 Google Sheets 或飞书文档的权限设置
4. 运行同步测试：`python3 test_cloud_sync.py`
5. 查看详细的同步配置指南：`CLOUD_SYNC_SETUP.md`
6. 检查目标文档是否存在且可访问

### Q6: Google Sheets API 认证失败

**解决方案：**
1. 确保服务账号 JSON 文件路径正确
2. 验证服务账号是否有目标表格的编辑权限
3. 检查 Google Sheets API 是否已启用
4. 确认 spreadsheet_id 是否正确

### Q7: 飞书文档同步权限不足

**解决方案：**
1. 确认应用的 app_id 和 app_secret 是否正确
2. 检查应用是否有表格的读写权限
3. 验证 spreadsheet_token 和 sheet_id 是否正确
4. 确保应用已获得必要的 API 权限范围

### 增强功能相关问题 🆕

### Q8: AI分析功能不工作怎么办？

**解决方案：**
1. 确认AI分析器配置正确
2. 检查推文数据格式是否完整
3. 查看AI分析日志获取详细错误信息
4. 确认系统资源充足（内存、CPU）

### Q9: 账户管理器无法轮换账户

**解决方案：**
1. 检查accounts.json文件格式和内容
2. 确认AdsPower账户状态正常
3. 验证账户使用限制和冷却时间设置
4. 查看账户管理器日志

### Q10: 任务调度器不执行任务

**解决方案：**
1. 检查调度器配置文件
2. 确认任务时间设置正确
3. 验证任务函数是否存在
4. 查看调度器运行日志

### Q11: 系统监控告警过于频繁

**解决方案：**
1. 适当提高告警阈值
2. 增加告警持续时间要求
3. 调整监控间隔
4. 优化系统性能

### Q12: 管理控制台命令无响应

**解决方案：**
1. 检查控制台是否正确启动
2. 确认命令语法正确
3. 查看控制台错误输出
4. 重启控制台服务

### Q13: 配置文件备份失败

**解决方案：**
1. 确认备份目录存在且有写权限
2. 检查磁盘空间是否充足
3. 验证配置文件格式正确
4. 查看配置管理器日志

## 注意事项

1. **合规使用**: 请遵守 Twitter 的使用条款和相关法律法规
2. **频率控制**: 避免过于频繁的请求，建议设置合理的延迟时间
3. **账号安全**: 使用 AdsPower 虚拟环境可以降低主账号风险
4. **数据备份**: 定期备份生成的 Excel 文件
5. **监控日志**: 关注日志文件中的错误信息

## 扩展功能

### 1. 定时任务

可以结合 cron（Linux/macOS）或任务计划程序（Windows）实现定时采集：

```bash
# 每天上午 9 点执行
0 9 * * * cd /path/to/twitter-daily-scraper && python3 main.py
```

### 2. 多账号轮换

```python
# 配置多个 AdsPower 用户ID
user_ids = ['user_id_1', 'user_id_2', 'user_id_3']
for user_id in user_ids:
    await scraper.run_scraping_task(user_id=user_id)
```

### 3. 数据库存储

可以扩展 `excel_writer.py` 支持数据库存储：

```python
# 添加数据库写入功能
def write_to_database(self, tweets, statistics):
    # 实现数据库写入逻辑
    pass
```

## 技术支持

如果遇到问题，请：

1. 查看日志文件 `twitter_scraper.log`
2. 检查配置文件是否正确
3. 确认所有依赖包已正确安装
4. 验证 AdsPower 环境是否正常

## 许可证

本项目仅供学习和研究使用，请遵守相关法律法规和平台使用条款。

## 更新日志

### v2.0.0 (2024-01-XX) - 增强版发布 🆕
- 🤖 **新增AI内容分析功能**
  - 推文质量评估和评分
  - 情感分析和趋势识别
  - 参与度预测和作者影响力分析
  - 智能洞察报告生成

- 👥 **新增多账户管理系统**
  - 自动账户轮换和负载均衡
  - 使用限制和冷却时间管理
  - 健康状态监控和自动恢复
  - 账户优先级和标签管理

- ⏰ **新增任务调度功能**
  - 定时任务和间隔任务调度
  - 任务重试和超时控制
  - 任务状态监控和报告
  - 预定义任务模板

- 📈 **新增系统监控功能**
  - 实时系统资源监控
  - 自定义告警规则和通知
  - 历史数据记录和分析
  - 性能指标统计和报告

- 🎛️ **新增管理控制台**
  - 统一的命令行管理界面
  - 交互式操作和状态查看
  - 批量操作和脚本支持
  - 实时监控和控制

- ⚙️ **新增配置管理系统**
  - 集中化配置文件管理
  - 配置备份和恢复
  - 配置验证和版本控制
  - 多格式配置支持

- 🚀 **新增增强版启动脚本**
  - 多模式运行支持
  - 一键设置和初始化
  - 调试和试运行模式
  - 完善的错误处理

- ⚡ **性能优化**
  - 批处理和并发优化
  - 缓存机制实现
  - 资源使用优化
  - 内存管理改进

### v1.2.0 (2024-01-XX)
- ✨ 新增云端同步功能
- 🔧 支持Google Sheets自动同步
- 🔧 支持飞书文档自动同步
- 📝 完善配置验证和错误处理
- 📚 新增云同步配置指南

### v1.1.0 (2024-01-XX)
- 🎯 优化推文过滤算法
- 📊 增强Excel报告功能
- 🐛 修复AdsPower连接稳定性问题
- 📝 改进日志记录和错误提示

### v1.0.0 (2024-01-01)
- 初始版本发布
- 支持 AdsPower 浏览器集成
- 实现用户主页和关键词搜索
- 添加智能筛选功能
- 生成 Excel 报表