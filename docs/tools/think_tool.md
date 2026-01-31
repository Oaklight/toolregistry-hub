---
title: 认知工具
summary: 用于结构化推理的统一认知工具
description: 单一 think 工具处理所有认知操作，包括记忆回忆、推理和探索。
keywords: 认知工具, 推理, 记忆, 思考工具, AI 工具
author: Oaklight
---

# 认知工具

用于结构化推理的统一认知工具，将**知识回忆**、**逻辑推理**和**创造性探索**整合到单一灵活的接口中。设计灵感来自 [Anthropic 的 Claude Think Tool](https://www.anthropic.com/engineering/claude-think-tool) 和认知心理学论文 ["Eliciting Reasoning in Language Models with Cognitive Tools"](https://arxiv.org/html/2506.12115)。

## 🎯 设计理念

### 为什么使用统一工具？

在与 AI 模型交互时，我们发现模型的"思考"过程往往是黑盒的。认知工具的核心目标是：**让模型的思考过程从"黑盒"变成"白盒"**，使其推理过程可见、可追踪、可纠错。

### 设计演进历程

#### 第 1-3 代：从复杂到简单

我们经历了多次迭代：

1. **单一 `think()` 工具** - 简单但缺乏结构
2. **三个工具 (`recall` + `reason` + `think`)** - 理论上完美但模型难以选择
3. **两个工具 (`recall` + `think`)** - 更好，但 `recall` 在实践中很少被使用

#### 第 4 代：当前设计（统一 `think`）

基于实际使用反馈，我们得出关键洞察：**模型几乎从不单独使用 `recall`**。它们更倾向于把所有内容都放入 `think`。因此我们：

1. **将 `recall` 合并到 `think`** - 添加 `"recalling"` 作为思考模式
2. **重新排序参数** - `thinking_mode` → `focus_area` → `thought_process`（先决定如何思考，再决定思考什么）
3. **简化模式** - 从 9 个减少到 6 个核心模式，每个都有明确的使用场景

**设计哲学：**

- **一个工具，多种模式**：为 AI 提供更简单的心智模型
- **参数顺序很重要**：引导模型先决定思考方式
- **模式即指引**：预定义模式提供方向，但不限制创造性

## 🚀 快速开始

```python
from toolregistry_hub import ThinkTool

# 回忆事实和知识（使用 "recalling" 模式）
ThinkTool.think(
    thinking_mode="recalling",
    focus_area="Python 异步模式",
    thought_process="FastAPI 使用依赖注入。项目有阻塞式数据库调用，"
                    "需要转换为异步以获得正确的性能。"
)

# 分析问题
ThinkTool.think(
    thinking_mode="reasoning",
    focus_area="数据库性能优化",
    thought_process="异步上下文中的阻塞调用会导致性能问题。"
                    "需要使用 asyncpg 进行异步 PostgreSQL 操作。"
                    "解决方案：将同步数据库调用替换为异步等效调用。"
)

# 规划实施步骤
ThinkTool.think(
    thinking_mode="planning",
    focus_area="迁移策略",
    thought_process="1. 识别所有同步数据库调用。2. 安装 asyncpg。"
                    "3. 创建异步连接池。4. 逐个端点迁移。"
)
```

## 🔧 API 参考

### `think(thinking_mode, focus_area, thought_process)`

记录你的认知过程 - 思考、推理、规划或回忆。

**参数（按推荐顺序）：**

1. `thinking_mode` (str, 可选)：认知操作的类型。**首先选择这个**来引导你的思考。
    - 核心模式：`"reasoning"`、`"planning"`、`"reflection"`
    - 记忆模式：`"recalling"`（用于导出知识/事实）
    - 创意模式：`"brainstorming"`、`"exploring"`
    - 或使用任何自定义字符串

2. `focus_area` (str, 可选)：你正在思考的具体问题或主题。**第二个设置这个**。

3. `thought_process` (str)：你详细的思考流。**最后写这个**。可以很长且杂乱。

**思考模式说明：**

| 模式 | 用途 | 何时使用 |
|------|------|----------|
| `reasoning` | 逻辑分析和推演 | 分析问题、评估选项、进行逻辑推理 |
| `planning` | 分解任务、制定策略 | 设计实施步骤、创建行动计划 |
| `reflection` | 审查、验证、自我纠正 | 检查工作、发现错误、纠正假设 |
| `recalling` | 从记忆中导出知识/事实 | 收集背景信息、陈述你知道的内容 |
| `brainstorming` | 自由生成想法 | 不加评判地探索可能性 |
| `exploring` | 心理模拟、假设场景 | 想象事情如何发展、考虑假设情况 |

## 🎯 使用指南

### 参数顺序很重要

参数顺序是有意设计的：`thinking_mode` → `focus_area` → `thought_process`

这引导模型：
1. **首先**决定如何思考（模式）
2. **然后**缩小范围（焦点）
3. **最后**写出实际的想法

```python
# 好的做法：先模式，再焦点，最后内容
ThinkTool.think(
    thinking_mode="planning",           # 1. 决定方法
    focus_area="API 重构",              # 2. 缩小范围
    thought_process="步骤 1: ..."       # 3. 写出想法
)
```

### 何时使用每种模式

**`reasoning`** - 用于逻辑分析：
```python
ThinkTool.think(
    thinking_mode="reasoning",
    focus_area="错误诊断",
    thought_process="错误发生在数据库调用之后。"
                    "查看堆栈跟踪，是连接超时。"
                    "这表明连接池已耗尽..."
)
```

**`planning`** - 用于任务分解：
```python
ThinkTool.think(
    thinking_mode="planning",
    focus_area="功能实现",
    thought_process="1. 创建数据模型。2. 添加 API 端点。"
                    "3. 编写测试。4. 更新文档。"
)
```

**`reflection`** - 用于自我纠正：
```python
ThinkTool.think(
    thinking_mode="reflection",
    focus_area="之前的假设",
    thought_process="等等，我假设错误在数据库层，"
                    "但仔细看，实际上是网络问题..."
)
```

**`recalling`** - 用于知识导出：
```python
ThinkTool.think(
    thinking_mode="recalling",
    focus_area="Python 3.9 特性",
    thought_process="Python 3.9 引入了字典合并运算符 |。"
                    "还添加了 removeprefix() 和 removesuffix() 字符串方法。"
                    "类型提示通过内置泛型变得更灵活。"
)
```

**`brainstorming`** - 用于想法生成：
```python
ThinkTool.think(
    thinking_mode="brainstorming",
    focus_area="性能优化",
    thought_process="可以使用缓存。也许 Redis？或者内存 LRU？"
                    "懒加载怎么样？或者预计算结果？"
                    "数据库索引可能也有帮助..."
)
```

**`exploring`** - 用于假设场景：
```python
ThinkTool.think(
    thinking_mode="exploring",
    focus_area="架构决策",
    thought_process="如果我们使用微服务，需要服务发现。"
                    "这增加了复杂性但提高了可扩展性。"
                    "如果我们先用单体架构，以后再拆分呢？"
)
```

### 最佳实践

**1. 不要总结 - 展示完整过程**

```python
# 好的做法：详细的思考
ThinkTool.think(
    thinking_mode="reasoning",
    focus_area="Bug 调查",
    thought_process="首先检查错误日志... 发现超时错误。"
                    "超时发生在数据库查询。查看查询，发现缺少索引。"
                    "添加索引应该能解决问题。但需要先在测试环境验证..."
)

# 避免：太简短
ThinkTool.think(
    thinking_mode="reasoning",
    focus_area="Bug 调查",
    thought_process="发现是索引问题"  # 丢失了思考过程
)
```

**2. 适当使用模式**

选择最能描述你当前思考类型的模式，但不必过度纠结 - 模式是指引而非限制。

## 🚨 重要说明

### 这个工具的功能

- 记录各种形式的认知过程
- 使思考可见和可追踪
- 通过模式引导结构化推理

### 这个工具不做的事

- 访问外部信息或 API
- 对代码或数据进行更改
- 执行代码或运行测试
- 执行实际计算

这个工具是**思考过程的记录器**，不是执行器。它的价值在于让思考过程可见、可追踪、可改进。

## 📚 参考文献

- Anthropic, ["Claude Think Tool"](https://www.anthropic.com/engineering/claude-think-tool) - 最初的灵感来源
- Brown et al., ["Eliciting Reasoning in Language Models with Cognitive Tools"](https://arxiv.org/html/2506.12115) - 理论基础
- 关于知识与推理分离的认知心理学研究

## 🔗 相关工具

- [计算器](calculator.md) - 用于实际数学计算
- [待办事项列表](todo_list.md) - 用于任务跟踪和规划
- [文件操作](file_ops.md) - 用于读写文件
