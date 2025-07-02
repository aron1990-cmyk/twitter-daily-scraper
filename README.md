# Twitter 日报采集系统

基于 AdsPower 虚拟浏览器的自动化 Twitter 信息采集系统，用于构建"日报矩阵"项目。

## 功能特性

- 🚀 **AdsPower 集成**: 使用 AdsPower 虚拟浏览器环境，避免账号风险
- 🎯 **多目标采集**: 支持指定博主主页和关键词搜索两种采集方式
- 🔍 **智能筛选**: 根据互动数（点赞/评论/转发）和关键词自动筛选优质推文
- 📊 **Excel 报表**: 自动生成包含统计信息的 Excel 日报
- 🛡️ **反检测**: 模拟真实用户行为，降低被检测风险
- 📝 **详细日志**: 完整的操作日志记录，便于调试和监控

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

## 使用方法

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

### 高级用法

#### 1. 基本使用

```bash
python main.py
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
├── main.py                 # 主程序入口
├── run.py                  # 快速启动脚本（推荐）
├── validate_config.py      # 配置验证工具
├── setup.py               # 自动安装脚本
├── config.py              # 配置文件
├── ads_browser_launcher.py # AdsPower 浏览器启动器
├── twitter_parser.py      # Twitter 页面解析器
├── tweet_filter.py        # 推文筛选器
├── excel_writer.py        # Excel 报表生成器
├── requirements.txt       # 依赖包列表
├── README.md             # 项目说明
├── data/                 # 输出数据目录
└── logs/                 # 日志文件目录
```

## 模块说明

### 核心模块

#### 1. main.py
主程序入口，协调各个模块的工作流程。

#### 2. config.py
系统配置文件，包含所有可配置参数。

#### 3. ads_browser_launcher.py (AdsPower 浏览器启动器)

- 启动和停止 AdsPower 浏览器
- 获取浏览器调试端口
- 监控浏览器状态

#### 4. twitter_parser.py (Twitter 解析器)

- 连接到 AdsPower 浏览器
- 导航到 Twitter 页面
- 解析推文数据
- 处理用户主页和关键词搜索

#### 5. tweet_filter.py (推文筛选器)

- 根据互动数筛选推文
- 关键词匹配筛选
- 生成筛选统计信息

#### 6. excel_writer.py (Excel 输出器)

- 生成格式化的 Excel 报表
- 创建汇总统计表
- 自动调整列宽和样式

### 辅助工具

#### 7. run.py
快速启动脚本，提供友好的命令行界面：
- 配置检查和验证
- AdsPower 连接状态检查
- 一键启动采集任务
- 调试模式支持

#### 8. validate_config.py
配置验证工具，帮助用户检查配置文件：
- 验证 AdsPower 连接
- 检查配置参数有效性
- 提供修复建议
- 测试系统就绪状态

#### 9. setup.py
自动安装脚本，简化环境配置：
- 自动安装依赖包
- 处理 SSL 证书问题
- 安装 Playwright 浏览器
- 创建必要目录结构

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
0 9 * * * cd /path/to/twitter-daily-scraper && python main.py
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

### v1.0.0 (2024-01-01)
- 初始版本发布
- 支持 AdsPower 浏览器集成
- 实现用户主页和关键词搜索
- 添加智能筛选功能
- 生成 Excel 报表