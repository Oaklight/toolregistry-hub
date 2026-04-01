---
title: 待办事项工具
summary: 为AI驱动工作流设计的任务管理和进度跟踪
description: Todo List工具为AI助手提供结构化的任务管理和进度跟踪功能，用于组织、跟踪和管理复杂的多步骤工作流和项目任务。
keywords: todo list, 任务管理, 工作流跟踪, AI工具, 进度监控
author: Oaklight
---

# 待办事项工具

待办事项工具为 AI 驱动的工作流提供结构化的任务管理和进度跟踪功能。该工具使 AI 助手能够组织、跟踪和管理复杂的多步骤任务、项目工作流和长时间运行的操作，并提供清晰的状态可见性。

???+ note "更新日志"
    0.5.1 初始版本，支持 planned、pending、done 和 cancelled 状态

## 概述

TodoList 类提供了以下功能：

- **工作流管理**: 跟踪多步骤 AI 任务和操作
- **进度监控**: 监控任务完成情况和工作流进度
- **状态跟踪**: 在复杂工作流中保持清晰的任务状态可见性
- **任务组织**: 结构化和组织相关任务
- **执行规划**: 规划和记录 AI 任务执行序列
- **输出格式化**: 为不同上下文生成格式化报告

## 快速开始

```python
from toolregistry_hub.todo_list import TodoList

# 创建工作流任务列表
workflow_tasks = [
    "[analyze-requirements] 分析用户需求和约束 (planned)",
    "[design-solution] 设计解决方案架构 (planned)",
    "[implement-core] 实现核心功能 (planned)",
    "[test-integration] 测试系统集成 (planned)",
    "[deploy-production] 部署到生产环境 (planned)"
]

# 更新工作流状态
TodoList.update(workflow_tasks)
print("工作流已初始化")

# 获取格式化的进度报告
progress_report = TodoList.update(workflow_tasks, format="markdown")
print(progress_report)
```

## API 参考

### `TodoList.update(todos, format="simple")`

更新或创建待办事项列表，支持可选的格式化输出用于工作流跟踪。

**参数:**

- `todos` (List[str]): 任务条目列表，格式为 `[id] description (status)`
- `format` (str, 可选): 输出格式 - `"simple"`、`"markdown"` 或 `"ascii"`。默认为 `"simple"`

**返回值:**

- `Optional[str]`: 格式化的任务列表输出（simple 格式返回 None）

**状态值:**

- `planned` - 任务已计划但尚未开始
- `pending` - 任务正在执行中
- `done` - 任务已成功完成
- `cancelled` - 任务已取消或放弃

## AI 工作流用例

### 多步骤任务执行

```python
from toolregistry_hub.todo_list import TodoList

# AI 助手管理复杂的分析任务
analysis_workflow = [
    "[data-collection] 收集和验证输入数据 (done)",
    "[preprocessing] 清理和规范化数据 (pending)",
    "[feature-extraction] 提取相关特征 (planned)",
    "[model-training] 训练预测模型 (planned)",
    "[evaluation] 评估模型性能 (planned)",
    "[reporting] 生成分析报告 (planned)"
]

# 跟踪工作流进度
TodoList.update(analysis_workflow)

# 生成状态报告
status = TodoList.update(analysis_workflow, format="markdown")
print("分析工作流状态:")
print(status)
```

### 迭代问题求解

```python
from toolregistry_hub.todo_list import TodoList

def solve_problem_iteratively(problem_description, max_iterations=3):
    """AI 助手通过迭代细化来解决问题。"""

    iteration_tasks = [
        f"[iteration-1] 初始分析和方法设计 (pending)",
        f"[iteration-2] 基于约束条件细化解决方案 (planned)",
        f"[iteration-3] 优化和验证解决方案 (planned)",
        f"[finalization] 记录最终解决方案 (planned)"
    ]

    # 跟踪迭代进度
    TodoList.update(iteration_tasks)

    # 生成迭代报告
    report = TodoList.update(iteration_tasks, format="markdown")
    return report

# 在 AI 工作流中使用
problem = "为高流量 API 设计高效的缓存策略"
result = solve_problem_iteratively(problem)
print(result)
```

### 代码生成和审查工作流

```python
from toolregistry_hub.todo_list import TodoList

# AI 助手管理代码生成和审查
code_workflow = [
    "[understand-spec] 理解需求和规范 (done)",
    "[design-architecture] 设计代码架构 (done)",
    "[generate-code] 生成实现代码 (pending)",
    "[add-tests] 生成单元测试 (planned)",
    "[code-review] 执行代码审查和优化 (planned)",
    "[documentation] 生成文档 (planned)",
    "[final-validation] 根据需求验证 (planned)"
]

# 跟踪代码生成工作流
TodoList.update(code_workflow)

# 获取详细进度
progress = TodoList.update(code_workflow, format="ascii")
print("代码生成进度:")
print(progress)
```

### 研究和分析任务

```python
from toolregistry_hub.todo_list import TodoList

# AI 助手进行研究
research_workflow = [
    "[literature-review] 审查相关研究论文 (pending)",
    "[data-analysis] 分析收集的数据 (planned)",
    "[pattern-identification] 识别关键模式和趋势 (planned)",
    "[hypothesis-formation] 形成研究假设 (planned)",
    "[validation] 根据标准验证发现 (planned)",
    "[synthesis] 综合结论 (planned)"
]

# 跟踪研究进度
TodoList.update(research_workflow)

# 生成研究状态
status = TodoList.update(research_workflow, format="markdown")
print("研究进度:")
print(status)
```

### 决策制定过程

```python
from toolregistry_hub.todo_list import TodoList

# AI 助手管理决策制定工作流
decision_workflow = [
    "[gather-options] 收集和记录所有选项 (done)",
    "[analyze-criteria] 定义评估标准 (done)",
    "[evaluate-options] 根据标准评估每个选项 (pending)",
    "[risk-assessment] 评估每个选项的风险 (planned)",
    "[recommendation] 生成建议 (planned)",
    "[justification] 记录决策理由 (planned)"
]

# 跟踪决策过程
TodoList.update(decision_workflow)

# 获取决策报告
report = TodoList.update(decision_workflow, format="markdown")
print("决策分析报告:")
print(report)
```

## 输出格式

### 简单格式（默认）

```python
# 无输出，仅更新内部状态
TodoList.update(tasks)  # 返回 None
```

适合内部工作流跟踪，无需生成输出。

### Markdown 表格格式

```python
tasks = [
    "[step-1] 完成初始分析 (done)",
    "[step-2] 设计解决方案 (pending)",
    "[step-3] 实现解决方案 (planned)"
]

report = TodoList.update(tasks, format="markdown")
print(report)
```

输出:

```markdown
| id     | task         | status  |
| ------ | ------------ | ------- |
| step-1 | 完成初始分析 | done    |
| step-2 | 设计解决方案 | pending |
| step-3 | 实现解决方案 | planned |
```

### ASCII 表格格式

```python
report = TodoList.update(tasks, format="ascii")
print(report)
```

输出:

```
+--------+---------------------------+---------+
| ID     | TASK                      | STATUS  |
+--------+---------------------------+---------+
| step-1 | 完成初始分析              | done    |
| step-2 | 设计解决方案              | pending |
| step-3 | 实现解决方案              | planned |
+--------+---------------------------+---------+
```

## AI 工作流最佳实践

### 结构化任务分解

```python
from toolregistry_hub.todo_list import TodoList

def decompose_complex_task(main_task, subtasks):
    """将复杂的 AI 任务分解为可管理的子任务。"""
    task_list = [
        f"[analyze] 分析 {main_task} (pending)",
    ]

    for i, subtask in enumerate(subtasks, 1):
        task_list.append(f"[subtask-{i}] {subtask} (planned)")

    task_list.append(f"[integrate] 集成所有子任务结果 (planned)")
    task_list.append(f"[validate] 验证最终输出 (planned)")

    TodoList.update(task_list)
    return TodoList.update(task_list, format="markdown")

# 示例：AI 助手分解复杂分析
subtasks = [
    "收集和验证数据源",
    "执行统计分析",
    "识别关键见解",
    "生成可视化"
]

result = decompose_complex_task("市场趋势分析", subtasks)
print(result)
```

### 工作流状态管理

```python
from toolregistry_hub.todo_list import TodoList

def update_workflow_state(tasks, completed_task_id, next_task_id):
    """随着任务进展更新工作流状态。"""
    updated_tasks = []

    for task in tasks:
        if f"[{completed_task_id}]" in task:
            # 标记为完成
            parts = task.split('] ')
            content = parts[1].split(' (')[0]
            updated_tasks.append(f"[{completed_task_id}] {content} (done)")
        elif f"[{next_task_id}]" in task:
            # 标记为进行中
            parts = task.split('] ')
            content = parts[1].split(' (')[0]
            updated_tasks.append(f"[{next_task_id}] {content} (pending)")
        else:
            updated_tasks.append(task)

    TodoList.update(updated_tasks)
    return updated_tasks

# 跟踪工作流进度
workflow = [
    "[step-1] 初始分析 (done)",
    "[step-2] 设计阶段 (pending)",
    "[step-3] 实现 (planned)",
    "[step-4] 测试 (planned)"
]

# 移至下一步
workflow = update_workflow_state(workflow, "step-2", "step-3")
```

### 进度监控

```python
from toolregistry_hub.todo_list import TodoList

def calculate_workflow_progress(tasks):
    """计算和报告工作流进度。"""
    total = len(tasks)
    completed = sum(1 for t in tasks if "(done)" in t)
    in_progress = sum(1 for t in tasks if "(pending)" in t)
    planned = sum(1 for t in tasks if "(planned)" in t)

    progress_pct = (completed / total * 100) if total > 0 else 0

    return {
        "total": total,
        "completed": completed,
        "in_progress": in_progress,
        "planned": planned,
        "progress_percentage": progress_pct
    }

# 监控工作流
tasks = [
    "[task-1] 完成 (done)",
    "[task-2] 进行中 (pending)",
    "[task-3] 计划中 (planned)",
    "[task-4] 计划中 (planned)"
]

progress = calculate_workflow_progress(tasks)
print(f"工作流进度: {progress['progress_percentage']:.1f}%")
print(f"已完成: {progress['completed']}/{progress['total']}")
```

## 重要说明

### 格式要求

任务条目必须遵循确切的格式：`[id] description (status)`

```python
# 正确的格式
correct_tasks = [
    "[analyze-data] 分析输入数据集 (pending)",
    "[train-model] 训练机器学习模型 (planned)",
    "[evaluate] 评估模型性能 (planned)"
]

# 错误的格式（会抛出错误）
incorrect_tasks = [
    "analyze-data Analyze input dataset pending",  # 缺少括号和括号
    "[analyze-data] Analyze input dataset",        # 缺少状态
    "[analyze-data] Analyze input dataset (invalid)"  # 无效状态
]
```

### 状态验证

仅支持四个状态值：

- `planned` - 任务已计划但未开始
- `pending` - 任务正在执行
- `done` - 任务已成功完成
- `cancelled` - 任务已取消或放弃

### 错误处理

```python
from toolregistry_hub.todo_list import TodoList

try:
    # 无效的状态会抛出 ValueError
    invalid_tasks = ["[task] 描述 (invalid_status)"]
    TodoList.update(invalid_tasks)
except ValueError as e:
    print(f"状态验证错误: {e}")

try:
    # 格式错误会抛出 ValueError
    malformed_tasks = ["task without proper format"]
    TodoList.update(malformed_tasks)
except ValueError as e:
    print(f"格式验证错误: {e}")
```

## 与 AI 工作流集成

### 工作流编排

```python
from toolregistry_hub.todo_list import TodoList

def orchestrate_ai_workflow(user_request):
    """使用任务跟踪编排复杂的 AI 工作流。"""

    # 定义工作流任务
    workflow = [
        "[parse-request] 解析和理解用户请求 (pending)",
        "[gather-context] 收集相关上下文和信息 (planned)",
        "[analyze-problem] 分析问题并确定方法 (planned)",
        "[execute-solution] 执行解决方案方法 (planned)",
        "[validate-output] 验证输出质量 (planned)",
        "[generate-report] 生成最终报告 (planned)"
    ]

    # 初始化工作流
    TodoList.update(workflow)

    # 获取初始状态
    status = TodoList.update(workflow, format="markdown")
    print("工作流状态:")
    print(status)

    return workflow

# 在 AI 助手中使用
request = "分析客户反馈并识别改进领域"
workflow = orchestrate_ai_workflow(request)
```

### 任务依赖跟踪

```python
from toolregistry_hub.todo_list import TodoList

def track_task_dependencies(tasks_with_deps):
    """跟踪具有依赖关系的任务以进行顺序执行。"""

    task_list = []
    for task_id, description, dependencies, status in tasks_with_deps:
        dep_info = f" (depends on: {', '.join(dependencies)})" if dependencies else ""
        task_list.append(f"[{task_id}] {description}{dep_info} ({status})")

    TodoList.update(task_list)
    return TodoList.update(task_list, format="markdown")

# 示例：具有依赖关系的任务
tasks = [
    ("data-prep", "准备和验证数据", [], "done"),
    ("feature-eng", "工程特征", ["data-prep"], "pending"),
    ("model-train", "训练模型", ["feature-eng"], "planned"),
    ("evaluation", "评估结果", ["model-train"], "planned")
]

report = track_task_dependencies(tasks)
print("任务依赖报告:")
print(report)
```
