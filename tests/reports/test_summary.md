# Twitter采集系统测试报告

**生成时间**: 2025-07-17 20:45:45

## 测试模块

| 模块 | 文件 | 描述 |
|------|------|------|
| 推文抓取 | test_scraper.py | 测试Twitter抓取功能 |
| 数据导出 | test_export.py | 测试数据保存和导出 |
| 去重处理 | test_deduplication.py | 测试去重算法 |
| 价值分析 | test_value_analysis.py | 测试推文价值评估 |
| 集成测试 | test_integration.py | 测试完整工作流程 |
| 修复测试 | test_fixes.py | 测试系统修复和改进 |

## 测试报告文件

- **HTML报告**: `reports/report.html`
- **覆盖率报告**: `htmlcov/index.html`
- **JUnit XML**: `reports/junit.xml`
- **覆盖率XML**: `reports/coverage.xml`

## 测试标记

- `unit`: 单元测试
- `integration`: 集成测试
- `performance`: 性能测试
- `slow`: 慢速测试
- `network`: 需要网络的测试
- `browser`: 需要浏览器的测试

## 运行命令示例

```bash
# 运行所有测试
python3 tests/run_tests.py --all

# 运行单元测试
python3 tests/run_tests.py --unit

# 运行特定模块
python3 tests/run_tests.py --module scraper

# 快速测试（排除慢速）
python3 tests/run_tests.py --quick
```
