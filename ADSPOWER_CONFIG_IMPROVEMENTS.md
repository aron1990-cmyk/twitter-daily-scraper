# AdsPower API配置功能改进

## 概述

本次更新对AdsPower API配置功能进行了重大改进，将原来的单一API地址配置拆分为主机地址和端口的独立配置，并新增了多项高级配置选项，提升了系统的灵活性和用户体验。

## 主要改进

### 1. API地址配置分离

**之前：**
- 只有一个"API地址"字段，用户需要输入完整的URL（如：`http://local.adspower.net:50325`）

**现在：**
- **API主机地址**：独立配置主机名（如：`local.adspower.net`）
- **API端口**：独立配置端口号（如：`50325`）
- **完整API地址预览**：实时显示组合后的完整URL

**优势：**
- 更直观的配置方式
- 减少用户输入错误
- 支持端口验证（1-65535范围）
- 实时预览功能，所见即所得

### 2. 新增高级配置选项

#### 请求频率控制
- **请求间隔时间**：控制API请求之间的间隔（默认2.0秒）
- **用户切换间隔**：控制用户ID轮询的间隔（默认30秒）
- **启用用户轮询**：开启/关闭智能用户轮询机制

#### 浏览器配置优化
- **浏览器启动延迟**：支持小数点精度（步长0.1秒）
- 更精确的时间控制

### 3. 向后兼容性

系统完全兼容旧的配置格式：
- 自动解析旧的完整API地址
- 智能拆分为主机和端口
- 无缝迁移现有配置

## 技术实现

### 前端改进

1. **实时预览功能**
   ```javascript
   function updateAdsPowerApiUrl() {
       const host = document.getElementById('adspower_api_host').value || 'local.adspower.net';
       const port = document.getElementById('adspower_api_port').value || '50325';
       const fullUrl = `http://${host}:${port}`;
       document.getElementById('adspower_api_url_display').value = fullUrl;
   }
   ```

2. **输入验证**
   - 端口号范围验证（1-65535）
   - 实时输入监听
   - 自动格式化

### 后端改进

1. **配置处理逻辑**
   ```python
   # 支持新的主机和端口字段
   api_host = request.form.get('adspower_api_host', 'local.adspower.net')
   api_port = request.form.get('adspower_api_port', '50325')
   api_url = f'http://{api_host}:{api_port}'
   ```

2. **向后兼容处理**
   ```python
   # 处理AdsPower API地址的向后兼容性
   if 'adspower_api_url' in config_data and ('adspower_api_host' not in config_data or 'adspower_api_port' not in config_data):
       # 从完整URL中解析主机和端口
       api_url = config_data['adspower_api_url']
       if api_url.startswith('http://'):
           url_parts = api_url.replace('http://', '').split(':')
           if len(url_parts) == 2:
               config_data['adspower_api_host'] = url_parts[0]
               config_data['adspower_api_port'] = url_parts[1]
   ```

3. **API接口更新**
   - 支持新的主机和端口参数
   - 保持API地址参数的兼容性
   - 增强错误处理

## 配置字段说明

| 字段名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| adspower_api_host | 文本 | local.adspower.net | AdsPower API主机地址 |
| adspower_api_port | 数字 | 50325 | AdsPower API端口号（1-65535） |
| request_interval | 数字 | 2.0 | API请求间隔时间（秒） |
| user_switch_interval | 数字 | 30 | 用户切换间隔时间（秒） |
| user_rotation_enabled | 布尔 | true | 是否启用用户轮询 |
| browser_startup_delay | 数字 | 2.0 | 浏览器启动延迟（秒，支持小数） |

## 使用指南

### 基础配置

1. **设置API地址**
   - 在"API主机地址"中输入AdsPower的主机名
   - 在"API端口"中输入端口号
   - 查看"完整API地址预览"确认配置正确

2. **配置用户ID**
   - 在"主要用户ID"中输入主要的用户配置ID
   - 在"多窗口用户ID列表"中每行输入一个用户ID

### 高级配置

1. **频率控制**
   - 根据AdsPower的限制调整"请求间隔时间"
   - 设置合适的"用户切换间隔"避免频繁切换
   - 启用"用户轮询"实现负载均衡

2. **性能优化**
   - 调整"浏览器启动延迟"适应系统性能
   - 设置合适的"最大并发任务数"

## 测试验证

系统包含完整的测试套件（`test_api_config.py`），验证以下功能：

- ✅ 配置页面加载
- ✅ API配置更新
- ✅ 安装检测API
- ✅ 连接测试API
- ✅ 配置持久化

所有测试均通过，确保功能稳定可靠。

## 问题解决

### 常见问题

1. **端口被占用**
   - 系统会自动检测并提示
   - 可以修改端口号解决

2. **API连接失败**
   - 检查AdsPower是否正在运行
   - 验证主机地址和端口配置
   - 使用"测试连接"功能诊断

3. **频率限制错误**
   - 增加"请求间隔时间"
   - 启用"用户轮询"分散请求
   - 减少并发任务数

### 调试工具

- 使用配置页面的"测试连接"功能
- 查看系统日志获取详细错误信息
- 运行测试脚本验证配置

## 未来改进方向

1. **HTTPS支持**：支持安全连接
2. **自动发现**：自动检测AdsPower端口
3. **配置模板**：预设常用配置模板
4. **监控面板**：实时显示API状态和性能指标
5. **批量配置**：支持批量导入/导出配置

## 总结

本次更新显著提升了AdsPower配置的用户体验和系统稳定性：

- 🎯 **用户友好**：直观的分离式配置界面
- 🔧 **功能强大**：丰富的高级配置选项
- 🔄 **向后兼容**：无缝升级现有配置
- 🛡️ **稳定可靠**：完整的测试覆盖
- 📈 **性能优化**：智能频率控制和负载均衡

这些改进为用户提供了更灵活、更稳定的AdsPower集成体验，同时为系统的进一步扩展奠定了坚实基础。