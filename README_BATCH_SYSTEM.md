# 推特博主推文批量抓取系统

一个专业的、可扩展的推特博主推文批量抓取系统，支持并发抓取、智能重试、状态管理和多种输出格式。

## 🚀 系统特性

### 核心功能
- **批量抓取**: 支持同时抓取多个推特博主的推文
- **并发处理**: 可配置的并发抓取，提高效率
- **智能过滤**: 多维度推文过滤（时间、互动数、关键词等）
- **增量更新**: 支持增量抓取，避免重复数据
- **状态管理**: 完整的账号状态跟踪和恢复机制

### 技术特性
- **异步架构**: 基于asyncio的高性能异步处理
- **模块化设计**: 清晰的模块划分，易于维护和扩展
- **异常处理**: 完善的异常处理和重试机制
- **多格式输出**: 支持JSON、CSV、Excel等多种输出格式
- **实时监控**: 进度监控和性能统计

### 企业级特性
- **配置管理**: 灵活的YAML/JSON配置文件
- **日志系统**: 完整的日志记录和轮转
- **命令行界面**: 友好的CLI工具
- **Web API**: 可选的REST API接口
- **云存储**: 支持多种云存储服务

## 📋 系统架构

```
推特批量抓取系统
├── 批量抓取协调器 (BatchScraper)
│   ├── 任务调度和并发控制
│   ├── 进度监控和状态管理
│   └── 结果汇总和报告生成
│
├── 抓取引擎 (TwitterScrapingEngine)
│   ├── 单用户推文抓取
│   ├── 数据提取和清洗
│   └── 错误处理和重试
│
├── 浏览器管理器 (BrowserManager)
│   ├── 浏览器实例池管理
│   ├── 会话保持和复用
│   └── 性能监控和自动重启
│
├── 数据提取器 (DataExtractor)
│   ├── 推文内容提取
│   ├── 用户信息提取
│   └── 数据验证和过滤
│
├── 存储管理器 (StorageManager)
│   ├── 多格式数据存储
│   ├── 文件组织和管理
│   └── 数据导出和备份
│
├── 状态跟踪器 (AccountStateTracker)
│   ├── 账号状态管理
│   ├── 增量抓取支持
│   └── 历史记录维护
│
└── 异常处理器 (ExceptionHandler)
    ├── 错误分类和处理
    ├── 重试策略管理
    └── 熔断器模式
```

## 🛠️ 安装和配置

### 环境要求
- Python 3.8+
- Chrome/Chromium 浏览器
- 8GB+ 内存（推荐）

### 依赖安装
```bash
# 安装Python依赖
pip install -r requirements.txt

# 安装Playwright浏览器
playwright install chromium
```

### 配置文件
复制并编辑配置文件：
```bash
cp config/batch_config.yaml config/my_config.yaml
```

主要配置项：
```yaml
# 目标账号
target_accounts:
  - "elonmusk"
  - "openai"
  - "github"

# 抓取参数
max_tweets_per_account: 50
max_concurrent_accounts: 3

# 过滤条件
filters:
  min_likes: 10
  exclude_retweets: true
  max_age_days: 7

# 输出格式
output_formats: ["json", "csv", "excel"]
```

## 🚀 快速开始

### 命令行使用

#### 1. 基本抓取
```bash
# 使用默认配置开始抓取
python3 main_batch_scraper.py start

# 使用自定义配置
python3 main_batch_scraper.py start --config config/my_config.yaml
```

#### 2. 自定义参数抓取
```bash
# 指定账号和推文数量
python3 main_batch_scraper.py start \
  --accounts elonmusk openai github \
  --max-tweets 30 \
  --concurrent 2 \
  --formats json csv
```

#### 3. 查看状态
```bash
# 查看当前抓取状态
python3 main_batch_scraper.py status

# 查看特定批次状态
python3 main_batch_scraper.py status --batch-id batch_1234567890
```

#### 4. 控制抓取过程
```bash
# 暂停当前抓取
python3 main_batch_scraper.py control pause

# 恢复抓取
python3 main_batch_scraper.py control resume

# 取消抓取
python3 main_batch_scraper.py control cancel
```

#### 5. 账号管理
```bash
# 查看账号状态
python3 main_batch_scraper.py accounts list

# 重置账号状态
python3 main_batch_scraper.py accounts reset --username elonmusk
```

#### 6. 导出结果
```bash
# 导出批次结果
python3 main_batch_scraper.py export batch_1234567890 --format json

# 查看历史记录
python3 main_batch_scraper.py history --limit 5
```

### 编程接口使用

```python
import asyncio
from batch_scraper import BatchScraper, BatchConfig

async def main():
    # 创建配置
    config = BatchConfig(
        target_accounts=["elonmusk", "openai", "github"],
        max_tweets_per_account=30,
        max_concurrent_accounts=2,
        output_formats=["json", "csv"],
        filters={
            "min_likes": 10,
            "exclude_retweets": True,
            "max_age_days": 7
        }
    )
    
    # 创建抓取器
    scraper = BatchScraper(config)
    
    # 设置回调函数
    def on_progress(progress):
        print(f"进度: {progress.overall_progress:.1f}%")
    
    scraper.set_progress_callback(on_progress)
    
    # 开始抓取
    try:
        summary = await scraper.start_batch_scraping()
        print(f"抓取完成: {summary['results']['total_tweets']} 条推文")
    except Exception as e:
        print(f"抓取失败: {e}")

# 运行
asyncio.run(main())
```

## 📊 数据结构

### 推文数据模型
```python
@dataclass
class TweetData:
    tweet_id: str              # 推文ID
    user_id: str               # 用户ID
    username: str              # 用户名
    display_name: str          # 显示名称
    content: str               # 推文内容
    created_at: datetime       # 发布时间
    likes: int                 # 点赞数
    retweets: int             # 转发数
    replies: int              # 回复数
    views: Optional[int]       # 浏览数
    is_retweet: bool          # 是否为转发
    is_reply: bool            # 是否为回复
    media_urls: List[str]     # 媒体链接
    hashtags: List[str]       # 话题标签
    mentions: List[str]       # 提及用户
    urls: List[str]           # 外部链接
    lang: Optional[str]       # 语言
    scraped_at: datetime      # 抓取时间
```

### 用户数据模型
```python
@dataclass
class UserData:
    user_id: str              # 用户ID
    username: str             # 用户名
    display_name: str         # 显示名称
    bio: Optional[str]        # 个人简介
    location: Optional[str]   # 位置
    website: Optional[str]    # 网站
    followers_count: int      # 粉丝数
    following_count: int      # 关注数
    tweets_count: int         # 推文数
    verified: bool            # 是否认证
    created_at: Optional[datetime]  # 账号创建时间
    avatar_url: Optional[str] # 头像链接
    banner_url: Optional[str] # 横幅链接
```

## 📁 输出文件结构

```
data/batch_results/
├── batch_1234567890/
│   ├── users/
│   │   ├── elonmusk_tweets.json
│   │   ├── openai_tweets.json
│   │   └── github_tweets.json
│   ├── profiles/
│   │   ├── elonmusk_profile.json
│   │   ├── openai_profile.json
│   │   └── github_profile.json
│   ├── exports/
│   │   ├── batch_1234567890_all_tweets.json
│   │   ├── batch_1234567890_all_tweets.csv
│   │   └── batch_1234567890_all_tweets.xlsx
│   ├── batch_1234567890_summary.json
│   └── batch_1234567890_progress.json
└── account_states.json
```

## ⚙️ 高级配置

### 过滤器配置
```yaml
filters:
  # 互动数过滤
  min_likes: 10
  min_retweets: 5
  min_replies: 0
  
  # 内容过滤
  exclude_retweets: true
  exclude_replies: true
  exclude_quotes: false
  
  # 时间过滤
  max_age_days: 7
  
  # 关键词过滤
  keywords: ["AI", "技术", "开发"]
  exclude_keywords: ["广告", "推广"]
  
  # 内容长度过滤
  min_content_length: 10
  max_content_length: 2000
```

### 性能优化配置
```yaml
advanced:
  performance:
    enable_images: false      # 禁用图片加载
    enable_javascript: true   # 启用JavaScript
    enable_css: true          # 启用CSS
  
  stealth:
    random_delays: true       # 随机延迟
    human_like_scrolling: true # 人类化滚动
    random_mouse_movements: true # 随机鼠标移动
```

### 通知配置
```yaml
notifications:
  enabled: true
  
  email:
    enabled: true
    smtp_server: "smtp.gmail.com"
    username: "your_email@gmail.com"
    to_addresses: ["admin@example.com"]
  
  webhook:
    enabled: true
    url: "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
```

## 🔧 故障排除

### 常见问题

#### 1. 浏览器启动失败
```bash
# 重新安装浏览器
playwright install chromium

# 检查系统依赖
sudo apt-get install -y libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxss1 libasound2
```

#### 2. 内存不足
```yaml
# 减少并发数
max_concurrent_accounts: 1
max_browser_instances: 1

# 启用无头模式
headless: true

# 禁用图片加载
advanced:
  performance:
    enable_images: false
```

#### 3. 抓取速度慢
```yaml
# 增加并发数
max_concurrent_accounts: 5

# 减少延迟
delay_between_accounts: 2.0

# 优化浏览器设置
advanced:
  performance:
    enable_images: false
    enable_css: false
```

#### 4. 频繁被限流
```yaml
# 增加延迟
delay_between_accounts: 10.0

# 启用反检测
advanced:
  stealth:
    random_delays: true
    human_like_scrolling: true

# 减少并发
max_concurrent_accounts: 1
```

### 日志分析
```bash
# 查看错误日志
grep "ERROR" logs/batch_scraper.log

# 查看限流日志
grep "rate.limit" logs/batch_scraper.log

# 实时监控日志
tail -f logs/batch_scraper.log
```

## 📈 性能监控

### 系统指标
- **抓取速度**: 推文/分钟
- **成功率**: 成功账号/总账号
- **错误率**: 错误次数/总请求
- **内存使用**: 峰值内存占用
- **CPU使用**: 平均CPU占用率

### 监控命令
```bash
# 查看实时状态
watch -n 5 "python3 main_batch_scraper.py status"

# 查看系统资源
top -p $(pgrep -f main_batch_scraper)

# 查看网络连接
netstat -an | grep :443
```

## 🔒 安全和合规

### 使用建议
1. **遵守Twitter服务条款**
2. **合理设置抓取频率**
3. **尊重用户隐私**
4. **仅用于合法目的**
5. **定期更新系统**

### 数据保护
```yaml
# 启用数据加密
advanced:
  storage:
    encrypt_data: true
    encryption_key: "your-encryption-key"

# 自动清理旧数据
advanced:
  storage:
    cleanup_old_files: true
    max_file_age_days: 30
```

## 🤝 贡献指南

### 开发环境设置
```bash
# 克隆项目
git clone <repository-url>
cd twitter-batch-scraper

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
pytest tests/

# 代码格式化
black .
flake8 .
```

### 提交规范
- 使用清晰的提交信息
- 添加适当的测试
- 更新相关文档
- 遵循代码风格

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 支持和反馈

- **问题报告**: [GitHub Issues](https://github.com/your-repo/issues)
- **功能请求**: [GitHub Discussions](https://github.com/your-repo/discussions)
- **邮件支持**: support@example.com

## 🗺️ 路线图

### v2.0 计划功能
- [ ] 图形用户界面 (GUI)
- [ ] 实时数据分析
- [ ] 机器学习推文分类
- [ ] 多平台支持 (Instagram, LinkedIn)
- [ ] 分布式抓取
- [ ] 数据可视化仪表板

### v1.1 计划功能
- [ ] Docker 容器化
- [ ] Kubernetes 部署
- [ ] 更多云存储支持
- [ ] 高级过滤器
- [ ] 性能优化

---

**注意**: 本系统仅供学习和研究使用，请遵守相关法律法规和平台服务条款。