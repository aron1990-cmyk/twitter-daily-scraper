# 🤖 Twitter自动互动引擎

一个功能完整、安全可靠的Twitter自动互动模块，支持多账号管理、智能行为控制和防封号机制。

## 🌟 核心特性

- ✅ **多账号支持**: 独立管理多个Twitter账号的互动行为
- ✅ **智能评分**: 基于关键词和热度的推文质量评估
- ✅ **行为随机化**: 模拟真实用户的不规律互动模式
- ✅ **每日限额**: 防止过度操作的安全保护机制
- ✅ **详细日志**: 完整记录所有互动行为和结果
- ✅ **重试机制**: 自动处理网络异常和页面加载问题
- ✅ **人性化操作**: 集成人类行为模拟器

## 📦 模块结构

```
core/
└── interaction_engine.py     # 核心互动引擎

config/
└── interaction_config.yaml   # 配置文件

docs/
└── interaction_engine_guide.md  # 详细使用指南

logs/
└── interaction_example.log   # 日志示例

test_interaction.py          # 测试脚本
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install playwright pyyaml
```

### 2. 配置文件

编辑 `config/interaction_config.yaml`:

```yaml
daily_limit:
  like: 30
  retweet: 10
  comment: 5
  dm: 3

delay_range:
  min: 2
  max: 6

random_behavior:
  like_probability: 0.7
  retweet_probability: 0.4
  comment_probability: 0.2
  dm_probability: 0.1
```

### 3. 基本使用

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

asyncio.run(main())
```

### 4. 运行测试

```bash
python test_interaction.py
```

## 🎯 功能详解

### 自动点赞 (Like)
- 智能识别高质量推文
- 避免重复点赞
- 支持每日限额控制

### 自动转发 (Retweet)
- 基于评分系统选择转发内容
- 确认转发操作
- 记录转发历史

### 自动评论 (Comment)
- 从语料池随机选择评论内容
- 支持自定义评论文本
- 模拟人类打字速度

### 自动私信 (DM)
- 向高价值用户发送私信
- 支持模板化消息
- 智能用户筛选

### 推文评分系统
- 关键词匹配评分
- 热度指标评估
- 综合质量判断

## 🔒 安全机制

### 防封号策略
1. **操作频率控制**: 严格限制每日操作次数
2. **随机延迟**: 模拟人类操作的自然间隔
3. **行为随机化**: 避免机械化的固定模式
4. **异常检测**: 自动识别并处理异常情况
5. **渐进式增长**: 新账号从低频操作开始

### 建议配置

**新账号 (保守模式)**:
```yaml
daily_limit:
  like: 15
  retweet: 3
  comment: 2
  dm: 1

delay_range:
  min: 3
  max: 8
```

**老账号 (正常模式)**:
```yaml
daily_limit:
  like: 30
  retweet: 10
  comment: 5
  dm: 3

delay_range:
  min: 2
  max: 6
```

## 📊 监控和日志

### 日志格式
每个操作都会生成详细的JSON格式日志:

```json
{
  "timestamp": "2024-01-15T10:30:22.789Z",
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

### 统计信息
```python
# 获取每日统计
stats = engine.get_daily_stats()
print(f"今日剩余操作: {stats['remaining']}")
print(f"已使用额度: {stats['used']}")
```

## 🔧 高级配置

### 自定义评分规则
```yaml
scoring:
  keywords_positive:
    - "AI"
    - "机器学习"
    - "技术创新"
  keywords_negative:
    - "广告"
    - "推广"
    - "spam"
  min_likes: 10
  min_retweets: 5
```

### 评论语料池
```yaml
comment_pool:
  - "This is exactly what I needed! 👍"
  - "Great point! Thanks for sharing 🙏"
  - "Very insightful, learned something new today"
  - "Couldn't agree more! 💯"
```

### 私信模板
```yaml
dm_templates:
  - "Hi! I really enjoyed your recent tweet about {topic}."
  - "Hello! Your insights on {topic} are fascinating."
```

## 🔄 集成指南

### 与任务管理器集成
```python
# 在refactored_task_manager.py中
from core.interaction_engine import InteractionEngine

class TaskManager:
    async def run_interaction_task(self, profile_id, tweets):
        engine = InteractionEngine(profile_id, "config/interaction_config.yaml")
        return await engine.run(tweets)
```

### 定时任务设置
```python
import schedule

def daily_interaction():
    tweets = get_daily_tweets()
    for profile_id in get_active_profiles():
        asyncio.run(run_interaction(profile_id, tweets))

schedule.every().day.at("10:00").do(daily_interaction)
```

## 🛠️ 故障排除

### 常见问题

1. **浏览器启动失败**
   - 检查AdsPower客户端状态
   - 验证profile_id正确性
   - 确认浏览器配置存在

2. **元素定位失败**
   - Twitter页面可能已更新
   - 增加页面等待时间
   - 检查网络连接

3. **操作被拒绝**
   - 可能触发安全机制
   - 降低操作频率
   - 检查账号状态

### 调试模式
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 单步调试
result = await engine.like(tweet_url)
print(f"操作结果: {result}")
```

## 📈 性能优化

- **批量处理**: 一次处理多条推文
- **缓存机制**: 避免重复操作
- **并发控制**: 合理安排任务队列
- **资源管理**: 及时释放浏览器资源

## 📋 API参考

### InteractionEngine类

```python
class InteractionEngine:
    def __init__(self, profile_id: str, config_path: str)
    async def run(self, tweet_list: List[Dict]) -> Dict
    async def like(self, tweet_url: str) -> bool
    async def retweet(self, tweet_url: str) -> bool
    async def comment(self, tweet_url: str, text: str = None) -> bool
    async def send_dm(self, user_url: str, message: str) -> bool
    def get_daily_stats(self) -> Dict
```

### 配置参数

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| daily_limit.like | int | 每日点赞上限 | 30 |
| daily_limit.retweet | int | 每日转发上限 | 10 |
| daily_limit.comment | int | 每日评论上限 | 5 |
| daily_limit.dm | int | 每日私信上限 | 3 |
| delay_range.min | int | 最小延迟(秒) | 2 |
| delay_range.max | int | 最大延迟(秒) | 6 |

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目仅供学习和研究使用。请遵守Twitter服务条款和相关法律法规。

## ⚠️ 免责声明

- 本模块仅供学习和研究目的
- 使用者需遵守Twitter服务条款
- 作者不对使用后果承担责任
- 请合理使用，避免滥用

---

**📞 技术支持**: 如有问题，请查看 `docs/interaction_engine_guide.md` 获取详细文档。