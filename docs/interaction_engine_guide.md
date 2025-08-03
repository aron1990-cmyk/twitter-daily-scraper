# Twitter自动互动引擎使用指南

## 📖 模块介绍

`InteractionEngine` 是一个功能完整的Twitter自动互动模块，支持多账号管理、每日限额控制、行为随机化等功能，旨在模拟真实用户的互动行为，同时最大化降低封号风险。

### 🎯 核心功能

- **自动点赞 (Like)**: 智能识别并点赞符合条件的推文
- **自动转发 (Retweet)**: 转发高质量内容到自己的时间线
- **自动评论 (Comment)**: 使用语料池生成自然的评论内容
- **自动私信 (DM)**: 向高价值用户发送个性化私信
- **推文评分**: 基于关键词和热度的智能评分系统
- **每日限额**: 防止过度操作的安全机制
- **行为随机化**: 模拟真实用户的不规律行为
- **详细日志**: 完整记录所有互动行为

### 🏗️ 架构设计

```
InteractionEngine
├── TweetScorer          # 推文评分模块
├── InteractionLogger    # 日志记录模块
├── DailyLimitTracker   # 每日限额跟踪
└── Core Engine         # 核心互动逻辑
```

## ⚙️ 配置说明

### 配置文件结构 (`interaction_config.yaml`)

```yaml
# 每日互动限额配置
daily_limit:
  like: 30        # 每日点赞上限
  retweet: 10     # 每日转发上限
  comment: 5      # 每日评论上限
  dm: 3           # 每日私信上限

# 行为延迟配置（秒）
delay_range:
  min: 2          # 最小延迟
  max: 6          # 最大延迟

# 随机行为概率配置（0-1之间）
random_behavior:
  like_probability: 0.7     # 点赞概率
  retweet_probability: 0.4  # 转发概率
  comment_probability: 0.2  # 评论概率
  dm_probability: 0.1       # 私信概率

# 推文评分配置
scoring:
  keywords_positive:        # 正面关键词
    - "AI"
    - "机器学习"
    - "技术"
  keywords_negative:        # 负面关键词
    - "广告"
    - "spam"
  min_likes: 10            # 最小点赞数阈值
  min_retweets: 5          # 最小转发数阈值

# 评论语料池
comment_pool:
  - "This is exactly what I needed! 👍"
  - "Great point! Thanks for sharing 🙏"
  # ... 更多评论模板

# 私信模板
dm_templates:
  - "Hi! I really enjoyed your recent tweet about {topic}."
  # ... 更多私信模板

# 安全配置
safety:
  max_actions_per_hour: 15           # 每小时最大操作数
  pause_after_failures: 30           # 失败后暂停时间（分钟）
  max_consecutive_failures: 5        # 最大连续失败次数
  enable_random_breaks: true          # 启用随机暂停
  random_break_range:
    min: 10
    max: 30
```

### 配置参数详解

#### 1. 每日限额 (daily_limit)
- **目的**: 防止单日操作过多导致账号异常
- **建议值**: 
  - 新账号: like≤20, retweet≤5, comment≤3, dm≤2
  - 老账号: like≤50, retweet≤15, comment≤8, dm≤5

#### 2. 延迟范围 (delay_range)
- **目的**: 模拟人类操作的自然间隔
- **建议值**: min=2-5秒, max=5-10秒
- **注意**: 延迟过短可能被识别为机器人

#### 3. 行为概率 (random_behavior)
- **目的**: 避免对每条推文都执行相同操作
- **建议值**: 
  - like_probability: 0.6-0.8 (点赞最常见)
  - retweet_probability: 0.2-0.4 (转发较谨慎)
  - comment_probability: 0.1-0.3 (评论需要思考)
  - dm_probability: 0.05-0.15 (私信最谨慎)

#### 4. 推文评分 (scoring)
- **正面关键词**: 提高互动概率的词汇
- **负面关键词**: 降低互动概率的词汇
- **热度阈值**: 基于点赞/转发数的质量判断

## 🚀 使用方法

### 基本使用

```python
import asyncio
from core.interaction_engine import InteractionEngine

async def main():
    # 初始化引擎
    engine = InteractionEngine(
        profile_id="your_adspower_profile_id",
        config_path="config/interaction_config.yaml"
    )
    
    # 准备推文数据
    tweets = [
        {
            'url': 'https://twitter.com/user/status/123456',
            'content': 'Amazing AI breakthrough!',
            'likes': 25,
            'retweets': 8,
            'user_url': 'https://twitter.com/user'
        }
    ]
    
    # 执行互动
    results = await engine.run(tweets)
    print(f"互动结果: {results}")

# 运行
asyncio.run(main())
```

### 高级使用

```python
# 检查每日限额
stats = engine.get_daily_stats()
print(f"今日剩余操作: {stats['remaining']}")

# 单独执行操作
if await engine.like("https://twitter.com/user/status/123456"):
    print("点赞成功")

# 自定义评论
if await engine.comment("https://twitter.com/user/status/123456", "Great post!"):
    print("评论成功")
```

## 🔒 安全建议

### 1. 账号安全

- **渐进式增加**: 新账号应从低频操作开始，逐步增加活跃度
- **多样化行为**: 不要只进行互动，也要发布原创内容
- **时间分散**: 避免在固定时间段集中操作
- **IP轮换**: 使用代理或VPN避免IP关联

### 2. 操作频率

```yaml
# 保守配置（推荐新账号）
daily_limit:
  like: 15
  retweet: 3
  comment: 2
  dm: 1

# 激进配置（仅限老账号）
daily_limit:
  like: 50
  retweet: 20
  comment: 10
  dm: 5
```

### 3. 内容质量

- **关键词过滤**: 避免与敏感话题互动
- **用户筛选**: 优先与活跃、正常的用户互动
- **内容审核**: 定期检查互动内容的质量

### 4. 技术防护

- **User-Agent轮换**: 使用不同的浏览器标识
- **行为模拟**: 包含鼠标移动、滚动等人类行为
- **异常处理**: 遇到验证码或限制时及时停止
- **日志监控**: 密切关注错误率和成功率

### 5. 风险指标

⚠️ **立即停止使用的情况**:
- 连续失败率 > 50%
- 出现验证码或安全检查
- 账号功能被限制
- 收到官方警告邮件

## 📊 日志格式

### 互动日志示例

```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "profile_id": "profile_001",
  "action": "like",
  "tweet_url": "https://twitter.com/user/status/123456",
  "success": true,
  "details": {
    "tweet_score": 0.75,
    "execution_time": 2.3
  }
}
```

### 每日统计示例

```json
{
  "date": "2024-01-15",
  "profile_id": "profile_001",
  "total_actions": 25,
  "success_rate": 0.92,
  "actions": {
    "like": {"attempted": 15, "successful": 14},
    "retweet": {"attempted": 5, "successful": 5},
    "comment": {"attempted": 3, "successful": 2},
    "dm": {"attempted": 2, "successful": 2}
  }
}
```

## 🔧 故障排除

### 常见问题

1. **浏览器启动失败**
   - 检查AdsPower客户端是否运行
   - 验证profile_id是否正确
   - 确认浏览器配置是否存在

2. **元素定位失败**
   - Twitter页面结构可能已更新
   - 检查网络连接和页面加载
   - 增加等待时间

3. **操作被拒绝**
   - 可能触发了Twitter的安全机制
   - 降低操作频率
   - 检查账号状态

4. **配置文件错误**
   - 验证YAML语法
   - 检查文件路径
   - 确认所有必需字段存在

### 调试模式

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 单步调试
engine = InteractionEngine(profile_id, config_path)
result = await engine.like(tweet_url)
print(f"操作结果: {result}")
```

## 📈 性能优化

### 1. 批量处理
- 一次处理多条推文，减少浏览器启动次数
- 合理安排任务队列

### 2. 缓存机制
- 缓存已处理的推文URL
- 避免重复操作

### 3. 并发控制
- 单账号串行处理
- 多账号可并行处理

## 🔄 集成指南

### 与现有系统集成

```python
# 在refactored_task_manager.py中调用
from core.interaction_engine import InteractionEngine

class TaskManager:
    async def run_interaction_task(self, profile_id, tweets):
        engine = InteractionEngine(profile_id, "config/interaction_config.yaml")
        return await engine.run(tweets)
```

### 定时任务

```python
# 使用scheduler.py设置定时任务
import schedule

def daily_interaction():
    # 获取今日推文
    tweets = get_daily_tweets()
    
    # 执行互动
    for profile_id in get_active_profiles():
        asyncio.run(run_interaction(profile_id, tweets))

schedule.every().day.at("10:00").do(daily_interaction)
```

## 📝 更新日志

### v1.0.0 (2024-01-15)
- 初始版本发布
- 支持基本的点赞、转发、评论、私信功能
- 实现每日限额和行为随机化
- 添加推文评分系统
- 完整的日志记录功能

---

**⚠️ 免责声明**: 本模块仅供学习和研究使用。使用者需要遵守Twitter的服务条款和相关法律法规。作者不对因使用本模块而导致的任何后果承担责任。