# 测试文档

本目录包含了 toolregistry-hub 项目的完整测试套件。

## 测试结构

```
tests/
├── __init__.py                    # 测试包初始化
├── test_calculator.py             # Calculator 工具测试
├── test_file_ops.py              # FileOps 工具测试
├── test_filesystem.py            # FileSystem 工具测试
├── test_unit_converter.py        # UnitConverter 工具测试
├── test_utils.py                 # Utils 工具测试
├── websearch/                    # WebSearch 模块测试
│   ├── __init__.py
│   ├── test_websearch.py         # WebSearch 基类测试
│   ├── test_websearch_google.py  # Google 搜索测试
│   ├── test_websearch_bing.py    # Bing 搜索测试
│   └── test_websearch_searxng.py # SearXNG 搜索测试
└── README.md                     # 本文档
```

## 运行测试

### 使用测试运行脚本（推荐）

项目根目录提供了 `run_tests.py` 脚本，可以方便地运行各种测试：

```bash
# 运行所有测试
python run_tests.py

# 运行特定模块的测试
python run_tests.py --module calculator
python run_tests.py --module websearch

# 运行测试并生成覆盖率报告
python run_tests.py --coverage

# 运行快速测试（排除慢速测试）
python run_tests.py --fast

# 详细模式运行测试
python run_tests.py --verbose

# 代码格式化和检查
python run_tests.py --lint
python run_tests.py --format

# 安装测试依赖
python run_tests.py --install-deps
```

### 直接使用 pytest

```bash
# 运行所有测试
pytest

# 运行特定文件的测试
pytest tests/test_calculator.py

# 运行特定目录的测试
pytest tests/websearch/

# 运行特定测试函数
pytest tests/test_calculator.py::TestCalculator::test_evaluate_basic_arithmetic

# 运行测试并显示覆盖率
pytest --cov=src/toolregistry --cov-report=html

# 运行测试并显示详细输出
pytest -v

# 运行快速测试（排除标记为 slow 的测试）
pytest -m "not slow"
```

## 测试分类

测试使用 pytest 标记进行分类：

- `@pytest.mark.unit` - 单元测试
- `@pytest.mark.integration` - 集成测试
- `@pytest.mark.slow` - 慢速测试
- `@pytest.mark.websearch` - WebSearch 相关测试
- `@pytest.mark.calculator` - Calculator 相关测试
- `@pytest.mark.filesystem` - 文件系统相关测试

## 测试覆盖的功能

### Calculator 测试 (`test_calculator.py`)
- 基本算术运算（加减乘除）
- 数学函数（三角函数、对数、指数）
- 统计函数（平均值、中位数、标准差）
- 表达式求值
- 错误处理

### FileOps 测试 (`test_file_ops.py`)
- 文件读写操作
- 原子写入操作
- 文件搜索功能
- Diff 和 Git 冲突格式处理
- 路径验证

### FileSystem 测试 (`test_filesystem.py`)
- 文件和目录存在性检查
- 文件和目录创建、复制、移动、删除
- 目录列表功能
- 文件大小和修改时间获取
- 路径操作

### UnitConverter 测试 (`test_unit_converter.py`)
- 温度转换
- 长度转换
- 重量转换
- 时间转换
- 容量转换
- 面积转换
- 速度转换
- 数据存储转换
- 压力、功率、能量转换
- 往返转换验证

### Utils 测试 (`test_utils.py`)
- 静态方法检测
- 命名空间确定
- 静态方法列表获取
- 包含/排除列表处理

### WebSearch 测试 (`websearch/`)
- 搜索引擎抽象基类测试
- Google 搜索实现测试
- Bing 搜索实现测试
- SearXNG 搜索实现测试
- HTML 解析测试
- 错误处理测试
- 网络请求模拟

## 测试最佳实践

### 1. 测试隔离
每个测试都应该是独立的，不依赖于其他测试的执行结果。

### 2. 使用临时文件
文件系统相关的测试使用 `tempfile` 模块创建临时文件和目录。

### 3. Mock 外部依赖
网络请求和外部服务调用使用 `unittest.mock` 进行模拟。

### 4. 测试边界条件
测试包括正常情况、边界条件和错误情况。

### 5. 清晰的测试名称
测试函数名称清楚地描述了测试的内容。

## 添加新测试

### 为新工具添加测试

1. 在 `tests/` 目录下创建 `test_<tool_name>.py` 文件
2. 导入要测试的模块
3. 创建测试类，继承自适当的基类
4. 编写测试方法，使用 `test_` 前缀
5. 添加适当的 pytest 标记

示例：
```python
import pytest
from toolregistry_hub.new_tool import NewTool

class TestNewTool:
    """Test cases for NewTool class."""
    
    def test_basic_functionality(self):
        """Test basic functionality."""
        tool = NewTool()
        result = tool.do_something()
        assert result == expected_value
    
    def test_error_handling(self):
        """Test error handling."""
        tool = NewTool()
        with pytest.raises(ValueError):
            tool.do_something_invalid()
```

### 测试数据

如果需要测试数据文件，可以在 `tests/` 目录下创建 `data/` 子目录存放。

## 持续集成

测试可以集成到 CI/CD 流水线中：

```yaml
# GitHub Actions 示例
- name: Run tests
  run: |
    python run_tests.py --coverage
    
- name: Upload coverage
  uses: codecov/codecov-action@v1
```

## 故障排除

### 常见问题

1. **导入错误**: 确保项目根目录在 Python 路径中
2. **文件权限错误**: 确保测试有权限创建临时文件
3. **网络相关测试失败**: 检查是否正确使用了 mock

### 调试测试

```bash
# 运行单个测试并显示详细输出
pytest tests/test_calculator.py::TestCalculator::test_add -v -s

# 在测试失败时进入调试器
pytest --pdb

# 显示测试执行时间
pytest --durations=10
```

## 性能测试

对于性能敏感的功能，可以添加性能测试：

```python
import time
import pytest

@pytest.mark.slow
def test_performance():
    """Test performance of expensive operation."""
    start_time = time.time()
    # 执行操作
    end_time = time.time()
    assert end_time - start_time < 1.0  # 应该在1秒内完成
```

## 贡献指南

在提交代码前，请确保：

1. 所有测试都通过
2. 代码覆盖率不降低
3. 新功能有相应的测试
4. 代码符合项目的格式标准

```bash
# 运行完整的检查
python run_tests.py --coverage
python run_tests.py --lint