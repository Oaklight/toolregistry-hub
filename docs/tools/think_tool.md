---
title: 认知工具
summary: 用于结构化推理的模块化认知操作
description: 认知工具将知识回忆与逻辑推理分离,受认知心理学研究启发,专为 AI 集成设计。
keywords: 认知工具, 推理, 记忆, 回忆, 思考工具, AI 工具
author: Oaklight
---

# 认知工具

认知工具提供模块化操作用于结构化推理,将**知识/记忆/事实**与**推理/逻辑**分离。设计灵感来自 [Anthropic 的 Claude Think Tool](https://www.anthropic.com/engineering/claude-think-tool) 和认知心理学论文 ["Eliciting Reasoning in Language Models with Cognitive Tools"](https://arxiv.org/html/2506.12115)。

## 🎯 设计理念

### 为什么需要认知工具?

在与 AI 模型交互时,我们发现模型的"思考"过程往往是黑盒的。认知工具的核心目标是:**让模型的思考过程从"黑盒"变成"白盒"**,使其推理过程可见、可追踪、可纠错。

研究表明**知识和推理是独立的认知过程**:

- **知识/记忆/事实**: 关于世界的内容、观察、上下文
- **推理/逻辑**: 独立于特定世界知识的数学/逻辑操作

我们的工具反映了这种分离,以实现更清晰、更结构化的思考。

### 设计演进历程

#### 第一代: 单一 `think()` 工具

最初的设计受 [Anthropic 的 Claude Think Tool](https://www.anthropic.com/engineering/claude-think-tool) 启发,只有一个 `think()` 方法,允许模型自由记录思考内容,就像一个草稿本。这种设计简单直接,但在实践中发现了问题:

- **缺乏结构**: 模型的思考内容混杂,难以区分是在回忆事实还是进行推理
- **难以追踪**: 用户回看时无法快速定位问题类型
- **效率低下**: 模型不知道何时该用何种思考方式

#### 第二代: 三工具分离 (`recall` + `reason` + `think`)

受 Brown 等人的论文 ["Eliciting Reasoning in Language Models with Cognitive Tools"](https://arxiv.org/html/2506.12115) 启发,我们将认知过程细分为三个独立工具:

- **`recall()`**: 专门用于记忆提取和事实陈述
- **`reason()`**: 用于目标导向的逻辑推理,带有明确的推理阶段标记
- **`think()`**: 用于自由探索式思考,不受结构约束

这个设计在理论上很完美,但实际使用中发现:

- **模型选择困难**: 模型要么只用 `think`,要么只用 `reason`,很少混用
- **边界模糊**: `reason` 和 `think` 的区分对模型来说不够直观
- **认知负担**: 三个工具增加了模型的选择成本

#### 第三代: 当前设计 (`recall` + `think`)

基于实际使用反馈,我们进行了关键性简化:**将 `reason` 和 `think` 合并为统一的 `think` 工具**。

**核心改进:**

1. **简化选择**: 模型不再需要在 `think` 和 `reason` 之间纠结
2. **清晰对比**: `recall`(静态知识) vs `think`(动态思考)
3. **保留灵活性**: 通过 `thinking_mode` 参数支持所有思考模式
4. **鼓励详细**: 参数命名(`thought_process`)暗示可以写长篇内容

**设计哲学:**

- **工具即记录器**: 这些工具不执行操作,而是记录思考过程
- **参数即暗示**: 通过参数命名引导模型行为(`thought_process` 而非 `content`)
- **模式即指引**: 预定义模式提供方向,但不限制创造性

## 🚀 快速开始

```python
from toolregistry_hub import ThinkTool

# 回忆事实和知识(记忆)
ThinkTool.recall(
    knowledge_content="FastAPI 使用依赖注入。项目有阻塞式数据库调用,"
                      "需要转换为异步以获得正确的性能。",
    topic_tag="Python 异步模式"
)

# 记录思考过程(包含结构化推理和自由探索)
ThinkTool.think(
    thought_process="异步上下文中的阻塞调用会导致性能问题。"
                    "需要使用 asyncpg 进行异步 PostgreSQL 操作。"
                    "解决方案:将同步数据库调用替换为异步等效调用。",
    thinking_mode="analysis",
    focus_area="数据库性能优化"
)
```

## 🔧 API 参考

### `recall(knowledge_content: str, topic_tag: Optional[str] = None)`

检索和记录事实知识(你知道的内容)。用于将你关于某个主题的原始记忆/知识导入到上下文中。

**参数:**

- `knowledge_content` (str): 你正在回忆的详细事实和信息。可以很长。
- `topic_tag` (str, 可选): 此记忆块的简短标签。

### `think(thought_process: str, thinking_mode: Optional[str] = None, focus_area: Optional[str] = None)`

记录你的思考过程 - 包括结构化推理和自由探索。

这个统一工具处理所有形式的主动思考:

- 结构化问题解决(分析、规划、验证等)
- 创造性探索(头脑风暴、心理模拟等)
- 直觉洞察和本能感受

**参数:**

- `thought_process` (str): 你详细的思考流。可以很长且杂乱。
- `thinking_mode` (str, 可选): 你正在进行的思考类型。常见模式:
    - 结构化: `"analysis"`, `"hypothesis"`, `"planning"`, `"verification"`, `"correction"`
    - 探索性: `"brainstorming"`, `"mental_simulation"`, `"perspective_taking"`, `"intuition"`
    - 或使用任何描述你思考模式的自定义字符串
- `focus_area` (str, 可选): 你正在思考的具体问题或主题。

**思考模式说明:**

| 模式 | 用途 | 示例场景 |
|------|------|----------|
| `analysis` | 系统地分析问题 | 检查错误模式,理解问题根源 |
| `hypothesis` | 形成关于原因的理论 | 基于症状推测可能的原因 |
| `planning` | 制定解决方案计划 | 设计实施步骤和策略 |
| `verification` | 检查某事是否有效 | 测试修复,确认结果 |
| `correction` | 修复思考中的错误 | 纠正之前的错误假设 |
| `brainstorming` | 自由生成想法 | 不加评判地探索多种可能性 |
| `mental_simulation` | 想象某事如何发展 | 模拟用户交互流程 |
| `perspective_taking` | 考虑其他角度 | 从不同角色视角思考 |
| `intuition` | 跟随直觉 | 基于经验的本能判断 |

## 🎯 使用指南

### 何时使用 `recall()`

- 在推理之前,收集相关背景
- 明确说明你知道/记得什么
- 将事实回忆与逻辑推理分离
- 将其视为你记忆的草稿本

### 何时使用 `think()`

- 分析问题
- 形成假设
- 规划解决方案
- 验证结果
- 纠正错误
- 头脑风暴
- 探索可能性
- 跟随直觉

### 最佳实践

**1. 将记忆与逻辑分离**

```python
# 首先回忆事实
ThinkTool.recall(
    knowledge_content="Python 3.9 引入了字典合并运算符 |。"
                      "项目要求 Python 3.9+。",
    topic_tag="Python 3.9 特性"
)

# 然后对其进行推理
ThinkTool.think(
    thought_process="我们目前使用 dict(**a, **b) 合并配置。"
                    "| 运算符更简洁、更易读。"
                    "由于我们要求 3.9+,可以安全使用此功能。",
    thinking_mode="planning"
)
```

**2. 不要总结 - 展示完整过程**

```python
# 好的做法
ThinkTool.think(
    thought_process="首先检查错误日志... 发现超时错误。"
                    "超时发生在数据库查询。查看查询,发现缺少索引。"
                    "添加索引应该能解决问题。但需要先在测试环境验证...",
    thinking_mode="analysis"
)

# 避免
ThinkTool.think(
    thought_process="发现是索引问题",  # 太简短,丢失了思考过程
    thinking_mode="analysis"
)
```

**3. 使用合适的思考模式**

选择最能描述你当前思考类型的模式,但不必过度纠结 - 模式是指引而非限制。

## 🚨 重要说明

### 这些工具的功能

- **recall()**: 从记忆中检索和记录事实知识
- **think()**: 记录各种形式的主动思考过程

### 这些工具不做的事

- 访问外部信息或 API
- 对代码或数据进行更改
- 执行代码或运行测试
- 访问文件系统或数据库
- 执行实际计算

这些工具是**思考过程的记录器**,不是执行器。它们的价值在于让思考过程可见、可追踪、可改进。

## 📚 参考文献

- Anthropic, ["Claude Think Tool"](https://www.anthropic.com/engineering/claude-think-tool) - 早期单一工具设计的灵感来源
- Brown et al., ["Eliciting Reasoning in Language Models with Cognitive Tools"](https://arxiv.org/html/2506.12115) - 三工具分离设计的理论基础
- 关于知识与推理分离的认知心理学研究
- Anderson 的 ACT-R 认知架构

## 🔗 相关工具

- [计算器](calculator.md) - 用于实际数学计算
- [待办事项列表](todo_list.md) - 用于任务跟踪和规划
- [文件操作](file_ops.md) - 用于读写文件