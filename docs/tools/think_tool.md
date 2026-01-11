---
title: 认知工具
summary: 用于结构化推理的模块化认知操作
description: 认知工具将知识回忆与逻辑推理分离，受认知心理学研究启发，专为 AI 集成设计。
keywords: 认知工具, 推理, 记忆, 回忆, 思考工具, AI 工具
author: Oaklight
---

# 认知工具

认知工具提供模块化操作用于结构化推理，将**知识/记忆/事实**与**推理/逻辑**分离。灵感来自认知心理学和论文["Eliciting Reasoning in Language Models with Cognitive Tools"](https://arxiv.org/html/2506.12115)。

???+ note "更新日志"
    **0.6.0** - 重大重新设计：分离为 `recall()`（记忆）和 `reason()`（逻辑），并提供 `cognitive_operation()` 用于扩展性

    0.5.0 - 不再以 json 格式返回思考内容

## 🎯 核心概念

研究表明**知识和推理是独立的认知过程**：

- **知识/记忆/事实**：关于世界的内容、观察、上下文
- **推理/逻辑**：独立于特定世界知识的数学/逻辑操作

我们的工具反映了这种分离，以实现更清晰、更结构化的思考。

## 🚀 快速开始

```python
from toolregistry_hub import ThinkTool

# 回忆事实和知识（记忆）
ThinkTool.recall(
    topic="Python 异步模式",
    context="项目使用 FastAPI，存在阻塞式数据库调用"
)

# 执行逻辑推理
ThinkTool.reason(
    content="异步上下文中的阻塞调用会导致性能问题。"
            "需要使用 asyncpg 进行异步 PostgreSQL 操作。"
            "解决方案：将同步数据库调用替换为异步等效调用。",
    reasoning_type="causal"
)

# 自定义认知操作用于新颖模式
ThinkTool.cognitive_operation(
    operation_type="hypothesis_generation",
    content="H1: 数据库查询问题（高可能性）\n"
            "H2: 内存泄漏（中等）\n"
            "H3: 网络延迟（低）",
    metadata="单一原因调试失败，尝试多个假设"
)
```

## 🔧 API 参考

### `recall(topic: str, context: Optional[str] = None)`

回忆事实、知识和观察。这是用于**记忆**，而非推理。

**何时使用：**

- 在推理之前，收集相关背景
- 明确说明你知道/记得什么
- 将事实回忆与逻辑推理分离

**参数：**

- `topic` (str): 要回忆信息的主题
- `context` (str, 可选): 当前情况下观察到的事实

**示例：**

```python
# 回忆一般知识
ThinkTool.recall(
    topic="FastAPI 依赖注入模式"
)

# 带当前上下文的回忆
ThinkTool.recall(
    topic="auth.py 第 45 行的 bug",
    context="v2.0 之后开始，影响 5% 用户，用户类型无规律"
)
```

### `reason(content: str, reasoning_type: Optional[str] = None)`

执行逻辑推理和分析。

**何时使用：**

- 问题分析
- 评估选项和权衡
- 得出结论
- 规划解决方案
- 理解问题
- 检查解决方案

**参数：**

- `content` (str): 你的推理过程和结论
- `reasoning_type` (str, 可选): 推理类型 - `"deductive"`、`"inductive"`、`"abductive"`、`"analogical"` 或 `"causal"`

**推理类型：**

- **deductive**（演绎）: 从一般原则到具体结论
- **inductive**（归纳）: 从具体观察到一般模式
- **abductive**（溯因）: 推断最佳解释
- **analogical**（类比）: 通过类比/相似性推理
- **causal**（因果）: 因果关系推理

**示例：**

```python
# 问题分析
ThinkTool.reason(
    content="v2.0 之后认证失败。新代码有共享缓存但没有锁。"
            "间歇性失败表明是竞态条件。修复：添加同步机制。",
    reasoning_type="causal"
)

# 解决方案评估
ThinkTool.reason(
    content="选项 A：互斥锁 - 简单但可能降低吞吐量。"
            "选项 B：线程安全缓存 - 性能更好但更复杂。"
            "选择 B 以实现长期可维护性。"
)
```

### `cognitive_operation(operation_type: str, content: str, metadata: Optional[str] = None)`

用于 recall/reason 未涵盖的模式的自定义认知操作。

**何时使用：**

- 你的思考不适合 recall 或 reason
- 新颖的推理模式
- 特定领域的认知操作

**参数：**

- `operation_type` (str): 操作名称
- `content` (str): 正在执行的认知工作
- `metadata` (str, 可选): 关于为何/如何使用此操作的上下文

**常见操作类型：**

- `hypothesis_generation`: 创建多个假设进行测试
- `mental_simulation`: 在脑海中模拟执行/结果
- `constraint_satisfaction`: 系统地处理约束
- `pattern_matching`: 识别数据/代码中的模式
- `metacognitive_monitoring`: 反思你的推理过程

**示例：**

```python
# 假设生成
ThinkTool.cognitive_operation(
    operation_type="hypothesis_generation",
    content="H1: 数据库查询效率低（高可能性，测试：添加查询日志）\n"
            "H2: 缓存中的内存泄漏（中等，测试：监控内存）\n"
            "H3: 网络延迟（低，测试：检查网络指标）",
    metadata="单一原因调试失败"
)

# 心理模拟
ThinkTool.cognitive_operation(
    operation_type="mental_simulation",
    content="1. 用户点击 → onClick 处理器\n"
            "2. 处理器调用 API → 异步请求\n"
            "3. UI 显示加载状态（缺失！）\n"
            "4. API 返回 → 状态更新\n"
            "问题：未显示加载状态",
    metadata="模拟以发现 UX 问题"
)
```

## 🛠️ 使用模式

### 完整的问题解决工作流

```python
from toolregistry_hub import ThinkTool

# 步骤 1：回忆相关知识
ThinkTool.recall(
    topic="认证系统和竞态条件",
    context="v2.0 重构了令牌验证，5% 用户出现间歇性失败"
)

# 步骤 2：对问题进行推理
ThinkTool.reason(
    content="时间相关性：失败始于 v2.0 部署。"
            "间歇性特征表明是竞态条件，而非逻辑错误。"
            "v2.0 引入了没有适当锁定的共享缓存。"
            "结论：缓存访问中的竞态条件。",
    reasoning_type="causal"
)

# 步骤 3：生成解决方案假设
ThinkTool.cognitive_operation(
    operation_type="hypothesis_generation",
    content="解决方案 1：添加互斥锁（简单，可能降低吞吐量）\n"
            "解决方案 2：使用线程安全缓存（性能更好）\n"
            "解决方案 3：移除缓存（最安全，性能最差）"
)

# 步骤 4：评估解决方案
ThinkTool.reason(
    content="解决方案 1 有效但在负载下影响性能。"
            "解决方案 2 长期最佳：性能更好且可维护性强。"
            "解决方案 3 过于激进。"
            "决策：实施线程安全缓存（解决方案 2）。"
)
```

### 调试策略

```python
# 回忆观察结果
ThinkTool.recall(
    topic="内存泄漏症状",
    context="内存使用量随时间线性增长，"
            "与用户会话相关，"
            "添加 WebSocket 支持后开始"
)

# 分析原因
ThinkTool.reason(
    content="线性增长 + 会话相关性表明每会话泄漏。"
            "WebSocket 时间点可疑。"
            "可能原因：WebSocket 事件监听器未被移除。"
            "需要检查会话终止时的清理。",
    reasoning_type="abductive"
)
```

### 设计决策

```python
# 回忆约束
ThinkTool.recall(
    topic="项目技术栈和需求",
    context="FastAPI 后端，15 个相似端点，团队偏好 DRY 原则"
)

# 对方法进行推理
ThinkTool.reason(
    content="15 个相似端点 → 高重复风险。"
            "可以使用基类，但 FastAPI 更适合依赖注入。"
            "工厂函数模式更 Pythonic，与 FastAPI 配合良好。"
            "决策：使用工厂函数而非继承。",
    reasoning_type="analogical"
)
```

## 🎯 最佳实践

### 1. 将记忆与逻辑分离

**好的做法：**

```python
# 首先回忆事实
ThinkTool.recall(
    topic="Python 3.9 特性",
    context="项目要求 Python 3.9+"
)

# 然后对其进行推理
ThinkTool.reason(
    content="Python 3.9 引入了字典合并运算符 |。"
            "这简化了我们的配置合并代码。"
            "可以用 a | b 替换 dict(**a, **b)。"
)
```

**避免：**

```python
# 不要混合记忆和推理
ThinkTool.reason(
    content="Python 3.9 有字典合并（这是记忆，不是推理）。"
            "我们可以用它简化代码（这是推理）。"
)
```

### 2. 使用适当的推理类型

```python
# 因果推理用于因果关系
ThinkTool.reason(
    content="变更 X 导致效果 Y，因为...",
    reasoning_type="causal"
)

# 溯因推理用于最佳解释
ThinkTool.reason(
    content="给定症状 A、B、C，最可能的原因是...",
    reasoning_type="abductive"
)

# 归纳推理用于模式
ThinkTool.reason(
    content="这 5 个 bug 都涉及空值检查。"
            "模式：需要在整个系统中更好地处理空值。",
    reasoning_type="inductive"
)
```

### 3. 对新颖模式使用 cognitive_operation

```python
# 当标准工具不适用时
ThinkTool.cognitive_operation(
    operation_type="constraint_satisfaction",
    content="✓ 必须使用 Python 3.9+（满足）\n"
            "✓ 必须是异步的（满足）\n"
            "✗ 不能添加新依赖（违反：需要 aiohttp）\n"
            "→ 决策：使用 stdlib urllib 配合 asyncio",
    metadata="系统性约束检查"
)
```

## 🚨 重要说明

### 这些工具的功能

- **recall()**：明确说明事实、知识、观察
- **reason()**：执行逻辑分析、评估、规划
- **cognitive_operation()**：用于新颖模式的自定义操作

### 这些工具不做的事

- 访问外部信息或 API
- 对代码或数据进行更改
- 执行代码或运行测试
- 访问文件系统或数据库
- 执行实际计算

### 旧版 `think()` 方法

原始的 `think(reasoning, facts)` 方法仍可用于向后兼容，但已弃用。请使用 `recall()` 和 `reason()` 以更清晰地分离关注点。

```python
# 旧版（已弃用）
ThinkTool.think(
    reasoning="一些推理...",
    facts="一些事实..."
)

# 新方法（推荐）
ThinkTool.recall(topic="...", context="...")
ThinkTool.reason(content="...")
```

## 📚 参考文献

- Brown et al., ["Eliciting Reasoning in Language Models with Cognitive Tools"](https://arxiv.org/html/2506.12115)
- 关于知识与推理分离的认知心理学研究
- Anderson 的 ACT-R 认知架构

## 🔗 相关工具

- [计算器](calculator.md) - 用于实际数学计算
- [待办事项列表](todo_list.md) - 用于任务跟踪和规划
- [文件操作](file_ops.md) - 用于读写文件
