# AdsPower 测试套件

这个测试套件提供了全面的 AdsPower 配置和连接功能测试，帮助您验证 AdsPower 集成是否正常工作。

## 📁 文件结构

```
test/
├── __init__.py                    # 测试模块初始化
├── test_adspower_config.py        # 配置测试
├── test_adspower_connection.py    # 连接测试
├── test_adspower_web_api.py       # Web API 测试
├── test_adspower_all.py           # 综合测试
├── run_tests.py                   # 测试运行脚本
└── README.md                      # 说明文档（本文件）
```

## 🧪 测试模块说明

### 1. 配置测试 (`test_adspower_config.py`)

测试 AdsPower 配置相关功能：
- 默认配置值验证
- API URL 生成
- 用户ID 获取
- 配置数据类功能
- AdsPowerManager 初始化

**特点：**
- 不需要 AdsPower 运行
- 纯配置逻辑测试
- 快速执行

### 2. 连接测试 (`test_adspower_connection.py`)

测试 AdsPower API 连接功能：
- API 连通性检查
- 用户列表获取
- 用户ID 验证
- 浏览器启动 API 测试
- 管理器可用性检查

**特点：**
- 需要 AdsPower 运行
- 实际网络连接测试
- 提供详细的诊断信息

### 3. Web API 测试 (`test_adspower_web_api.py`)

测试 Flask Web 应用中的 AdsPower API 接口：
- 服务器可用性检查
- 配置页面加载
- AdsPower 连接 API
- 安装检查 API
- 浏览器测试 API
- 超时处理测试

**特点：**
- 需要 Web 服务器运行
- 测试前端后端集成
- HTTP 接口测试

### 4. 综合测试 (`test_adspower_all.py`)

整合所有测试模块：
- 统一的测试入口
- 详细的测试报告
- HTML 报告生成
- 灵活的测试选项

### 5. 测试运行脚本 (`run_tests.py`)

提供简单的命令行接口：
- 依赖检查
- 快速检查
- 分类测试执行
- 用户友好的输出

## 🚀 快速开始

### 1. 环境检查

首先检查测试环境是否准备就绪：

```bash
# 检查依赖和测试文件
python test/run_tests.py check

# 快速检查 AdsPower 状态
python test/run_tests.py quick
```

### 2. 运行单个测试

```bash
# 配置测试（不需要 AdsPower 运行）
python test/run_tests.py config

# 连接测试（需要 AdsPower 运行）
python test/run_tests.py connection

# Web API 测试（需要 Web 服务器运行）
python test/run_tests.py web-api
```

### 3. 运行所有测试

```bash
# 运行所有测试
python test/run_tests.py all

# 跳过 Web API 测试
python test/run_tests.py all --skip-web-api

# 生成 HTML 报告
python test/run_tests.py all --report
```

### 4. 直接运行测试文件

```bash
# 直接运行配置测试
python test/test_adspower_config.py

# 直接运行连接测试
python test/test_adspower_connection.py

# 直接运行 Web API 测试
python test/test_adspower_web_api.py

# 直接运行综合测试
python test/test_adspower_all.py
```

## 📋 测试前准备

### 1. AdsPower 配置

确保以下配置正确：

```python
# config/adspower_config.py
ADSPOWER_CONFIG = {
    'api_host': '127.0.0.1',
    'api_port': 50325,
    'api_key': 'your_api_key',
    'user_ids': ['user_id_1', 'user_id_2'],
    # ... 其他配置
}
```

### 2. AdsPower 启动

运行连接测试前：
1. 启动 AdsPower 应用
2. 登录您的账户
3. 在设置中启用本地 API 服务
4. 确保端口 50325 未被占用

### 3. Web 服务器启动

运行 Web API 测试前：
```bash
# 启动优化版服务器
python web_app_optimized.py

# 或启动标准版服务器
python web_app.py
```

## 🔍 测试结果解读

### 成功标识
- ✅ 测试通过
- 🎉 所有测试完成

### 警告标识
- ⚠️ 部分测试失败
- 📝 注意事项

### 错误标识
- ❌ 测试失败
- 🚫 严重错误

### 常见错误及解决方案

#### 1. 连接被拒绝
```
❌ AdsPower API 连接失败 - 连接被拒绝
```
**解决方案：**
- 确保 AdsPower 已启动
- 检查本地 API 服务是否开启
- 验证端口配置是否正确

#### 2. API Key 验证失败
```
❌ API Key 验证失败
```
**解决方案：**
- 检查 API Key 是否正确
- 确认 AdsPower 中的 API 设置

#### 3. 用户ID 不存在
```
❌ 用户ID xxx 不存在
```
**解决方案：**
- 检查配置的用户ID 是否正确
- 在 AdsPower 中创建对应的用户配置

#### 4. Web 服务器连接失败
```
❌ 无法连接到 Web 服务器
```
**解决方案：**
- 启动 Web 服务器
- 检查端口是否正确
- 确认防火墙设置

## 📊 测试报告

### HTML 报告生成

```bash
# 生成详细的 HTML 测试报告
python test/run_tests.py all --report
```

报告将包含：
- 测试执行时间
- 详细的测试统计
- 成功率分析
- 分类测试结果

### 报告文件位置

默认报告文件：`test/adspower_test_report.html`

## 🛠️ 自定义测试

### 添加新的测试用例

1. 在相应的测试文件中添加新的测试方法
2. 使用 `unittest.TestCase` 基类
3. 方法名以 `test_` 开头

示例：
```python
def test_custom_feature(self):
    """测试自定义功能"""
    # 测试逻辑
    self.assertTrue(some_condition)
```

### 修改测试配置

编辑测试文件中的 `setUp` 方法来修改测试配置：

```python
def setUp(self):
    """测试前准备"""
    self.custom_config = {
        'api_host': 'custom_host',
        'api_port': 'custom_port',
        # ... 其他配置
    }
```

## 🔧 故障排除

### 1. 导入错误

如果遇到模块导入错误：
```bash
# 确保在项目根目录运行
cd /path/to/twitter-daily-scraper
python test/run_tests.py check
```

### 2. 权限问题

如果遇到权限问题：
```bash
# 给测试脚本执行权限
chmod +x test/run_tests.py
chmod +x test/test_adspower_all.py
```

### 3. 依赖缺失

如果缺少依赖：
```bash
# 安装项目依赖
pip install -r requirements.txt

# 或手动安装测试依赖
pip install requests unittest2
```

## 📝 最佳实践

1. **定期运行测试**：在修改 AdsPower 相关代码后运行测试
2. **分步测试**：先运行配置测试，再运行连接测试
3. **保存报告**：定期生成 HTML 报告用于记录
4. **环境隔离**：在不同环境中运行测试验证兼容性
5. **日志记录**：关注测试输出中的详细信息

## 🤝 贡献

如果您发现测试中的问题或有改进建议：

1. 检查现有的测试用例
2. 添加新的测试场景
3. 改进错误处理和诊断信息
4. 优化测试性能和可靠性

## 📞 支持

如果您在使用测试套件时遇到问题：

1. 首先运行 `python test/run_tests.py check` 检查环境
2. 查看测试输出中的详细错误信息
3. 参考本文档的故障排除部分
4. 检查 AdsPower 和 Web 服务器的运行状态

---

**注意：** 这些测试脚本设计用于开发和调试环境，请不要在生产环境中运行可能影响系统稳定性的测试。