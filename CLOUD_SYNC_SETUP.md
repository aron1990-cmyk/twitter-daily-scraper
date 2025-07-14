# 云端同步设置指南

本指南将帮助您设置Google Sheets和飞书文档的API集成，实现Twitter数据的自动同步。

## 🚀 功能概述

- ✅ 自动同步Twitter数据到Google Sheets
- ✅ 自动同步Twitter数据到飞书表格
- ✅ 支持自定义表格格式和工作表
- ✅ 实时同步状态反馈
- ✅ 错误处理和重试机制

## 📋 前置要求

1. 安装额外依赖包：
```bash
pip install gspread google-auth google-auth-oauthlib google-auth-httplib2
```

2. 创建凭证目录：
```bash
mkdir -p credentials
```

## 🔧 Google Sheets 设置

### 步骤1：创建Google Cloud项目

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建新项目或选择现有项目
3. 启用以下API：
   - Google Sheets API
   - Google Drive API

### 步骤2：创建服务账号

1. 在Google Cloud Console中，转到「IAM和管理」>「服务账号」
2. 点击「创建服务账号」
3. 填写服务账号详细信息
4. 授予以下角色：
   - Editor（编辑者）
5. 创建并下载JSON密钥文件
6. 将密钥文件重命名为 `google-credentials.json` 并放入 `credentials/` 目录

### 步骤3：创建Google表格

1. 在Google Sheets中创建新表格
2. 从URL中复制表格ID（例如：`1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms`）
3. 与服务账号邮箱共享表格（编辑权限）

### 步骤4：配置config.py

```python
CLOUD_SYNC_CONFIG = {
    'google_sheets': {
        'enabled': True,  # 启用Google Sheets同步
        'credentials_file': './credentials/google-credentials.json',
        'spreadsheet_id': '你的表格ID',  # 从URL中获取
        'worksheet_name': 'Twitter数据',  # 工作表名称
    },
    # ...
}
```

## 🔧 飞书文档设置

### 步骤1：创建飞书应用

1. 访问 [飞书开放平台](https://open.feishu.cn/)
2. 创建企业自建应用
3. 记录应用的 App ID 和 App Secret

### 步骤2：配置应用权限

在应用管理页面，添加以下权限：
- `sheets:spreadsheet` - 查看、编辑、创建和删除电子表格
- `drive:drive` - 查看、编辑、创建和删除云文档

### 步骤3：创建飞书表格

1. 在飞书中创建新的表格文档
2. 从URL中获取表格token（例如：`shtcnmBA*****UIVUrkqPx`）
3. 确保应用有访问该表格的权限

### 步骤4：配置config.py

```python
CLOUD_SYNC_CONFIG = {
    # ...
    'feishu': {
        'enabled': True,  # 启用飞书同步
        'app_id': '你的应用ID',
        'app_secret': '你的应用密钥',
        'spreadsheet_token': '你的表格token',  # 从URL中获取
        'sheet_id': '',  # 可选，留空使用第一个工作表
    }
}
```

## 📊 数据格式说明

同步到云端的数据将包含以下列：

| 列名 | 说明 |
|------|------|
| 序号 | 数据行号 |
| 用户名 | Twitter用户名 |
| 推文内容 | 推文文本内容 |
| 发布时间 | 推文发布时间 |
| 点赞数 | 推文点赞数量 |
| 评论数 | 推文评论数量 |
| 转发数 | 推文转发数量 |
| 链接 | 推文链接 |
| 标签 | 相关标签 |
| 筛选状态 | 是否通过筛选 |

## 🔍 使用方法

### 1. 配置完成后运行

```bash
python3 main.py
```

### 2. 检查同步状态

程序运行时会显示同步状态：
```
开始同步数据到云端平台...
✅ google_sheets 同步成功
✅ feishu 同步成功
云端同步结果: {'google_sheets': True, 'feishu': True}
```

### 3. 查看同步结果

- Google Sheets：打开您的表格查看数据
- 飞书表格：打开您的飞书表格查看数据

## 🛠️ 故障排除

### Google Sheets常见问题

1. **权限错误**
   - 确保服务账号有表格的编辑权限
   - 检查API是否已启用

2. **凭证文件错误**
   - 确保JSON文件路径正确
   - 检查文件格式是否有效

3. **表格ID错误**
   - 从完整URL中复制正确的表格ID
   - 确保表格存在且可访问

### 飞书常见问题

1. **应用权限不足**
   - 检查应用是否有必要的API权限
   - 确保应用已发布并激活

2. **Token错误**
   - 检查App ID和App Secret是否正确
   - 确保表格token有效

3. **网络连接问题**
   - 检查网络连接
   - 确认飞书API服务可访问

## 📝 高级配置

### 自定义同步频率

可以通过修改主程序中的同步逻辑来实现不同的同步策略：

```python
# 仅在有新数据时同步
if passed_tweets:
    sync_results = await self.cloud_sync.sync_all_platforms(passed_tweets, CLOUD_SYNC_CONFIG)
```

### 选择性同步

可以根据需要启用或禁用特定平台：

```python
# 仅启用Google Sheets
CLOUD_SYNC_CONFIG['google_sheets']['enabled'] = True
CLOUD_SYNC_CONFIG['feishu']['enabled'] = False
```

### 数据过滤

可以在同步前对数据进行额外过滤：

```python
# 仅同步高质量推文
high_quality_tweets = [tweet for tweet in passed_tweets if tweet.get('likes', 0) > 1000]
sync_results = await self.cloud_sync.sync_all_platforms(high_quality_tweets, CLOUD_SYNC_CONFIG)
```

## 🔒 安全注意事项

1. **保护凭证文件**
   - 不要将凭证文件提交到版本控制系统
   - 设置适当的文件权限

2. **API密钥安全**
   - 定期轮换API密钥
   - 使用环境变量存储敏感信息

3. **访问权限控制**
   - 仅授予必要的最小权限
   - 定期审查访问权限

## 📞 技术支持

如果您在设置过程中遇到问题，请：

1. 检查日志文件中的详细错误信息
2. 确认所有配置参数正确
3. 验证网络连接和API服务状态
4. 参考官方API文档获取最新信息

---

**注意**：首次设置可能需要一些时间来配置API权限和测试连接。建议先在测试环境中验证配置，然后再应用到生产环境。