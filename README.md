# Twitter 日报采集系统

一个基于 AdsPower 虚拟浏览器的自动化 Twitter 信息采集系统，提供 Web 管理界面进行任务管理和数据查看。

## 🚀 项目特性

- **自动化采集**: 基于 AdsPower 虚拟浏览器，模拟真实用户行为
- **Web 管理界面**: 提供直观的 Web 界面进行任务配置和管理
- **多账号支持**: 支持多个 Twitter 账号轮换使用
- **智能过滤**: 根据点赞数、转发数等指标过滤高质量内容
- **数据导出**: 支持 Excel 格式导出，便于数据分析
- **云端同步**: 支持飞书多维表格同步
- **任务队列**: 支持任务排队和并发控制
- **实时监控**: 提供系统状态监控和任务进度跟踪

## 📋 系统要求

- Python 3.8+
- AdsPower 浏览器客户端
- 操作系统: Windows/macOS/Linux
- 内存: 建议 4GB 以上
- 存储: 建议 2GB 以上可用空间

## 🛠️ 安装指南

### 1. 克隆项目

```bash
git clone https://github.com/your-username/twitter-daily-scraper.git
cd twitter-daily-scraper
```

### 2. 创建虚拟环境

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 安装 Playwright 浏览器

```bash
playwright install
```

## ⚙️ 配置说明

### AdsPower 配置

1. **安装 AdsPower 客户端**
   - 下载并安装 [AdsPower](https://www.adspower.net/) 客户端
   - 启动 AdsPower 并确保 API 服务运行在 `http://local.adspower.net:50325`

2. **创建浏览器配置文件**
   - 在 AdsPower 中创建新的浏览器配置文件
   - 记录配置文件的 User ID

3. **配置系统参数**
   - 启动 Web 应用后，在设置页面配置 AdsPower 参数
   - 填入正确的 User ID 和 API 地址

### 飞书配置（可选）

如需使用飞书多维表格同步功能：

1. 创建飞书应用并获取 App ID 和 App Secret
2. 创建多维表格并获取 Spreadsheet Token 和 Table ID
3. 在 Web 界面的设置页面配置飞书参数

## 🚀 部署运行

### 开发环境运行

```bash
# 启动 Web 应用
python web_app.py
```

应用将在 `http://localhost:5000` 启动。

### 生产环境部署

#### 使用 Gunicorn (推荐)

```bash
# 安装 Gunicorn
pip install gunicorn

# 启动应用
gunicorn -w 4 -b 0.0.0.0:5000 web_app:app
```

#### 使用 Docker

```bash
# 构建镜像
docker build -t twitter-scraper .

# 运行容器
docker run -d -p 5000:5000 -v $(pwd)/data:/app/data twitter-scraper
```

#### 使用 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## 📖 使用教程

### 1. 首次启动

1. 启动 AdsPower 客户端
2. 运行 `python web_app.py`
3. 访问 `http://localhost:5000`
4. 进入设置页面配置 AdsPower 参数

### 2. 创建采集任务

1. 在首页点击「快速创建任务」
2. 填写任务名称
3. 输入目标用户名（如：elonmusk）
4. 设置关键词（可选）
5. 配置过滤条件：
   - 最小点赞数
   - 最小转发数
   - 最大推文数量
6. 点击「创建并启动任务」

### 3. 任务管理

- **查看任务状态**: 在首页查看当前运行的任务
- **任务队列**: 查看排队中的任务
- **任务历史**: 在任务管理页面查看历史任务
- **停止任务**: 点击停止按钮终止运行中的任务

### 4. 数据查看与导出

1. **在线查看**: 点击任务的「查看数据」按钮
2. **导出 Excel**: 在数据页面点击「导出 Excel」
3. **飞书同步**: 配置飞书后可自动同步到多维表格

### 5. 系统监控

- **系统状态**: 首页显示系统运行状态
- **资源使用**: 查看内存、CPU 使用情况
- **任务统计**: 查看任务成功率和数据统计

## 🔧 高级配置

### 过滤配置

在 `config.py` 中可以调整过滤参数：

```python
FILTER_CONFIG = {
    'min_likes': 50,        # 最小点赞数
    'min_comments': 10,     # 最小评论数
    'min_retweets': 20,     # 最小转发数
    'max_tweets_per_target': 8,  # 每个目标最大推文数
    'max_total_tweets': 200,     # 总最大推文数
    'min_content_length': 20,    # 最小内容长度
    'max_content_length': 1000,  # 最大内容长度
    'max_age_hours': 72,         # 最大推文年龄（小时）
}
```

### 浏览器配置

```python
BROWSER_CONFIG = {
    'headless': False,           # 是否无头模式
    'timeout': 8000,            # 超时时间（毫秒）
    'wait_time': 0.3,           # 等待时间
    'scroll_pause_time': 0.3,   # 滚动暂停时间
    'fast_mode': True,          # 快速模式
    'skip_images': True,        # 跳过图片加载
}
```

### 并发配置

```python
ADS_POWER_CONFIG = {
    'max_concurrent_tasks': 2,   # 最大并发任务数
    'task_timeout': 900,         # 任务超时时间（秒）
    'browser_startup_delay': 2,  # 浏览器启动延迟
}
```

## 📁 项目结构

```
twitter-daily-scraper/
├── web_app.py              # Web 应用主文件
├── main.py                 # 命令行主程序
├── config.py               # 配置文件
├── requirements.txt        # Python 依赖
├── models.py              # 数据模型
├── ads_browser_launcher.py # AdsPower 浏览器启动器
├── twitter_parser.py       # Twitter 解析器
├── refactored_task_manager.py # 任务管理器
├── cloud_sync.py          # 云端同步
├── excel_writer.py        # Excel 导出
├── templates/             # HTML 模板
│   ├── index.html
│   ├── tasks.html
│   └── settings.html
├── static/               # 静态资源
│   └── js/
├── data/                 # 数据目录
│   ├── exports/         # 导出文件
│   └── tweets/          # 推文数据
├── archive/             # 归档文件
│   ├── tests/          # 测试文件
│   ├── scripts/        # 工具脚本
│   └── backups/        # 备份文件
└── instance/            # 实例数据
    └── twitter_scraper.db # SQLite 数据库
```

## 🐛 故障排除

### 常见问题

1. **AdsPower 连接失败**
   - 确保 AdsPower 客户端正在运行
   - 检查 API 地址是否正确（默认：`http://local.adspower.net:50325`）
   - 验证 User ID 是否存在

2. **任务执行失败**
   - 检查网络连接
   - 确认目标用户名是否正确
   - 查看日志文件获取详细错误信息

3. **数据导出问题**
   - 确保有足够的磁盘空间
   - 检查文件权限
   - 验证导出目录是否存在

4. **飞书同步失败**
   - 检查 App ID 和 App Secret 是否正确
   - 确认多维表格权限设置
   - 验证网络连接

### 日志查看

```bash
# 查看应用日志
tail -f twitter_scraper.log

# 查看任务日志
tail -f data/logs/task_*.log
```

### 数据库维护

```bash
# 备份数据库
cp instance/twitter_scraper.db instance/twitter_scraper_backup.db

# 清理旧数据（保留最近30天）
python -c "from web_app import cleanup_old_data; cleanup_old_data(30)"
```

## 🔒 安全注意事项

1. **API 密钥保护**
   - 不要在代码中硬编码 API 密钥
   - 使用环境变量或配置文件存储敏感信息
   - 定期更换 API 密钥

2. **网络安全**
   - 在生产环境中使用 HTTPS
   - 配置防火墙限制访问
   - 使用强密码保护管理界面

3. **数据保护**
   - 定期备份数据库
   - 加密存储敏感数据
   - 遵守数据保护法规

4. **使用限制**
   - 遵守 Twitter 使用条款
   - 控制请求频率避免被限制
   - 尊重用户隐私

## 📊 性能优化

### 系统优化

1. **内存优化**
   - 定期清理缓存数据
   - 限制并发任务数量
   - 使用数据库分页查询

2. **网络优化**
   - 配置合适的超时时间
   - 使用连接池
   - 启用数据压缩

3. **存储优化**
   - 定期清理旧数据
   - 压缩导出文件
   - 使用 SSD 存储

### 监控指标

- CPU 使用率
- 内存使用率
- 磁盘空间
- 网络延迟
- 任务成功率
- 数据采集速度

## 🔄 更新日志

### v2.0.0 (2025-01-25)
- 重构项目目录结构
- 优化 Web 界面，简化首页功能
- 改进任务管理系统
- 增强错误处理和日志记录
- 添加系统监控功能

### v1.5.0 (2024-12-15)
- 添加飞书多维表格同步
- 支持多账号轮换
- 优化数据过滤算法
- 改进用户界面

### v1.0.0 (2024-10-01)
- 初始版本发布
- 基础采集功能
- Web 管理界面
- Excel 导出功能

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 支持与反馈

- 问题反馈：[GitHub Issues](https://github.com/your-username/twitter-daily-scraper/issues)
- 功能建议：[GitHub Discussions](https://github.com/your-username/twitter-daily-scraper/discussions)
- 邮件联系：your-email@example.com

## 🙏 致谢

感谢以下开源项目的支持：

- [Flask](https://flask.palletsprojects.com/) - Web 框架
- [Playwright](https://playwright.dev/) - 浏览器自动化
- [SQLAlchemy](https://www.sqlalchemy.org/) - 数据库 ORM
- [AdsPower](https://www.adspower.net/) - 虚拟浏览器平台

---

**注意**: 请确保在使用本系统时遵守相关法律法规和平台使用条款。本项目仅供学习和研究使用。