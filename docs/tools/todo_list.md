---
title: Todo List Tool
summary: Task management and progress tracking for AI-driven workflows
description: Todo List tool provides structured task management with status tracking, designed for AI assistants to organize, track, and manage complex multi-step workflows and project tasks.
keywords: todo list, task management, workflow tracking, AI tools, progress monitoring
author: Oaklight
---

# Todo List Tool

The Todo List tool provides structured task management and progress tracking functionality for AI-driven workflows. This tool enables AI assistants to organize, track, and manage complex multi-step tasks, project workflows, and long-running operations with clear status visibility.

???+ note "Changelog"
    0.5.1 Initial release with support for planned, pending, done, and cancelled statuses

## 🎯 Overview

The TodoList class offers a dedicated space for:

- **Workflow Management**: Track multi-step AI tasks and operations
- **Progress Monitoring**: Monitor task completion and workflow progress
- **Status Tracking**: Maintain clear visibility of task states across complex workflows
- **Task Organization**: Structure and organize related tasks hierarchically
- **Execution Planning**: Plan and document AI task execution sequences
- **Output Formatting**: Generate formatted reports for different contexts

## 🚀 Quick Start

```python
from toolregistry_hub.todo_list import TodoList

# Create a workflow task list
workflow_tasks = [
    "[analyze-requirements] Analyze user requirements and constraints (planned)",
    "[design-solution] Design solution architecture (planned)",
    "[implement-core] Implement core functionality (planned)",
    "[test-integration] Test system integration (planned)",
    "[deploy-production] Deploy to production (planned)"
]

# Update workflow status
TodoList.update(workflow_tasks)
print("Workflow initialized")

# Get formatted progress report
progress_report = TodoList.update(workflow_tasks, format="markdown")
print(progress_report)
```

## 🔧 API Reference

### `TodoList.update(todos, format="simple")`

Update or create a todo list with optional formatting output for workflow tracking.

**Parameters:**

- `todos` (List[str]): List of task entries in format `[id] description (status)`
- `format` (str, optional): Output format - `"simple"`, `"markdown"`, or `"ascii"`. Defaults to `"simple"`

**Returns:**

- `Optional[str]`: Formatted task list output (None for 'simple' format)

**Status Values:**

- `planned` - Task is scheduled but not yet started
- `pending` - Task is currently being executed
- `done` - Task has been completed successfully
- `cancelled` - Task has been cancelled or abandoned

## 🛠️ Use Cases for AI Workflows

### Multi-Step Task Execution

```python
from toolregistry_hub.todo_list import TodoList

# AI assistant managing a complex analysis task
analysis_workflow = [
    "[data-collection] Gather and validate input data (done)",
    "[preprocessing] Clean and normalize data (pending)",
    "[feature-extraction] Extract relevant features (planned)",
    "[model-training] Train predictive model (planned)",
    "[evaluation] Evaluate model performance (planned)",
    "[reporting] Generate analysis report (planned)"
]

# Track workflow progress
TodoList.update(analysis_workflow)

# Generate status report
status = TodoList.update(analysis_workflow, format="markdown")
print("Analysis Workflow Status:")
print(status)
```

### Iterative Problem Solving

```python
from toolregistry_hub.todo_list import TodoList

def solve_problem_iteratively(problem_description, max_iterations=3):
    """AI assistant solving a problem through iterative refinement."""

    iteration_tasks = [
        f"[iteration-1] Initial analysis and approach design (pending)",
        f"[iteration-2] Refine solution based on constraints (planned)",
        f"[iteration-3] Optimize and validate solution (planned)",
        f"[finalization] Document final solution (planned)"
    ]

    # Track iteration progress
    TodoList.update(iteration_tasks)

    # Generate iteration report
    report = TodoList.update(iteration_tasks, format="markdown")
    return report

# Use in AI workflow
problem = "Design an efficient caching strategy for high-traffic API"
result = solve_problem_iteratively(problem)
print(result)
```

### Code Generation and Review Workflow

```python
from toolregistry_hub.todo_list import TodoList

# AI assistant managing code generation and review
code_workflow = [
    "[understand-spec] Understand requirements and specifications (done)",
    "[design-architecture] Design code architecture (done)",
    "[generate-code] Generate implementation code (pending)",
    "[add-tests] Generate unit tests (planned)",
    "[code-review] Perform code review and optimization (planned)",
    "[documentation] Generate documentation (planned)",
    "[final-validation] Validate against requirements (planned)"
]

# Track code generation workflow
TodoList.update(code_workflow)

# Get detailed progress
progress = TodoList.update(code_workflow, format="ascii")
print("Code Generation Progress:")
print(progress)
```

### Research and Analysis Tasks

```python
from toolregistry_hub.todo_list import TodoList

# AI assistant conducting research
research_workflow = [
    "[literature-review] Review relevant research papers (pending)",
    "[data-analysis] Analyze collected data (planned)",
    "[pattern-identification] Identify key patterns and trends (planned)",
    "[hypothesis-formation] Formulate research hypotheses (planned)",
    "[validation] Validate findings against criteria (planned)",
    "[synthesis] Synthesize conclusions (planned)"
]

# Track research progress
TodoList.update(research_workflow)

# Generate research status
status = TodoList.update(research_workflow, format="markdown")
print("Research Progress:")
print(status)
```

### Decision-Making Process

```python
from toolregistry_hub.todo_list import TodoList

# AI assistant managing decision-making workflow
decision_workflow = [
    "[gather-options] Gather and document all options (done)",
    "[analyze-criteria] Define evaluation criteria (done)",
    "[evaluate-options] Evaluate each option against criteria (pending)",
    "[risk-assessment] Assess risks for each option (planned)",
    "[recommendation] Generate recommendation (planned)",
    "[justification] Document decision justification (planned)"
]

# Track decision process
TodoList.update(decision_workflow)

# Get decision report
report = TodoList.update(decision_workflow, format="markdown")
print("Decision Analysis Report:")
print(report)
```

## 📊 Output Formats

### Simple Format (Default)

```python
# No output, just updates internal state
TodoList.update(tasks)  # Returns None
```

Ideal for internal workflow tracking without output generation.

### Markdown Table Format

```python
tasks = [
    "[step-1] Complete initial analysis (done)",
    "[step-2] Design solution (pending)",
    "[step-3] Implement solution (planned)"
]

report = TodoList.update(tasks, format="markdown")
print(report)
```

Output:

```markdown
| id     | task                      | status  |
| ------ | ------------------------- | ------- |
| step-1 | Complete initial analysis | done    |
| step-2 | Design solution           | pending |
| step-3 | Implement solution        | planned |
```

### ASCII Table Format

```python
report = TodoList.update(tasks, format="ascii")
print(report)
```

Output:

```
+--------+---------------------------+---------+
| ID     | TASK                      | STATUS  |
+--------+---------------------------+---------+
| step-1 | Complete initial analysis | done    |
| step-2 | Design solution           | pending |
| step-3 | Implement solution        | planned |
+--------+---------------------------+---------+
```

## 🎯 Best Practices for AI Workflows

### Structured Task Decomposition

```python
from toolregistry_hub.todo_list import TodoList

def decompose_complex_task(main_task, subtasks):
    """Decompose complex AI tasks into manageable subtasks."""
    task_list = [
        f"[analyze] Analyze {main_task} (pending)",
    ]

    for i, subtask in enumerate(subtasks, 1):
        task_list.append(f"[subtask-{i}] {subtask} (planned)")

    task_list.append(f"[integrate] Integrate all subtask results (planned)")
    task_list.append(f"[validate] Validate final output (planned)")

    TodoList.update(task_list)
    return TodoList.update(task_list, format="markdown")

# Example: AI assistant decomposing a complex analysis
subtasks = [
    "Gather and validate data sources",
    "Perform statistical analysis",
    "Identify key insights",
    "Generate visualizations"
]

result = decompose_complex_task("Market trend analysis", subtasks)
print(result)
```

### Workflow State Management

```python
from toolregistry_hub.todo_list import TodoList

def update_workflow_state(tasks, completed_task_id, next_task_id):
    """Update workflow state as tasks progress."""
    updated_tasks = []

    for task in tasks:
        if f"[{completed_task_id}]" in task:
            # Mark as done
            parts = task.split('] ')
            content = parts[1].split(' (')[0]
            updated_tasks.append(f"[{completed_task_id}] {content} (done)")
        elif f"[{next_task_id}]" in task:
            # Mark as pending
            parts = task.split('] ')
            content = parts[1].split(' (')[0]
            updated_tasks.append(f"[{next_task_id}] {content} (pending)")
        else:
            updated_tasks.append(task)

    TodoList.update(updated_tasks)
    return updated_tasks

# Track workflow progression
workflow = [
    "[step-1] Initial analysis (done)",
    "[step-2] Design phase (pending)",
    "[step-3] Implementation (planned)",
    "[step-4] Testing (planned)"
]

# Move to next step
workflow = update_workflow_state(workflow, "step-2", "step-3")
```

### Progress Monitoring

```python
from toolregistry_hub.todo_list import TodoList

def calculate_workflow_progress(tasks):
    """Calculate and report workflow progress."""
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

# Monitor workflow
tasks = [
    "[task-1] Complete (done)",
    "[task-2] In progress (pending)",
    "[task-3] Planned (planned)",
    "[task-4] Planned (planned)"
]

progress = calculate_workflow_progress(tasks)
print(f"Workflow Progress: {progress['progress_percentage']:.1f}%")
print(f"Completed: {progress['completed']}/{progress['total']}")
```

## 🚨 Important Notes

### Format Requirements

Task entries must follow the exact format: `[id] description (status)`

```python
# ✅ Correct format
correct_tasks = [
    "[analyze-data] Analyze input dataset (pending)",
    "[train-model] Train machine learning model (planned)",
    "[evaluate] Evaluate model performance (planned)"
]

# ❌ Incorrect formats (will raise errors)
incorrect_tasks = [
    "analyze-data Analyze input dataset pending",  # Missing brackets and parentheses
    "[analyze-data] Analyze input dataset",        # Missing status
    "[analyze-data] Analyze input dataset (invalid)"  # Invalid status
]
```

### Status Validation

Only four status values are supported:

- `planned` - Task scheduled but not started
- `pending` - Task currently being executed
- `done` - Task completed successfully
- `cancelled` - Task cancelled or abandoned

### Error Handling

```python
from toolregistry_hub.todo_list import TodoList

try:
    # Invalid status will raise ValueError
    invalid_tasks = ["[task] Description (invalid_status)"]
    TodoList.update(invalid_tasks)
except ValueError as e:
    print(f"Status validation error: {e}")

try:
    # Malformed format will raise ValueError
    malformed_tasks = ["task without proper format"]
    TodoList.update(malformed_tasks)
except ValueError as e:
    print(f"Format validation error: {e}")
```

## 🔗 Integration with AI Workflows

### Workflow Orchestration

```python
from toolregistry_hub.todo_list import TodoList

def orchestrate_ai_workflow(user_request):
    """Orchestrate complex AI workflow with task tracking."""

    # Define workflow tasks
    workflow = [
        "[parse-request] Parse and understand user request (pending)",
        "[gather-context] Gather relevant context and information (planned)",
        "[analyze-problem] Analyze problem and identify approach (planned)",
        "[execute-solution] Execute solution approach (planned)",
        "[validate-output] Validate output quality (planned)",
        "[generate-report] Generate final report (planned)"
    ]

    # Initialize workflow
    TodoList.update(workflow)

    # Get initial status
    status = TodoList.update(workflow, format="markdown")
    print("Workflow Status:")
    print(status)

    return workflow

# Use in AI assistant
request = "Analyze customer feedback and identify improvement areas"
workflow = orchestrate_ai_workflow(request)
```

### Task Dependency Tracking

```python
from toolregistry_hub.todo_list import TodoList

def track_task_dependencies(tasks_with_deps):
    """Track tasks with dependencies for sequential execution."""

    task_list = []
    for task_id, description, dependencies, status in tasks_with_deps:
        dep_info = f" (depends on: {', '.join(dependencies)})" if dependencies else ""
        task_list.append(f"[{task_id}] {description}{dep_info} ({status})")

    TodoList.update(task_list)
    return TodoList.update(task_list, format="markdown")

# Example: Tasks with dependencies
tasks = [
    ("data-prep", "Prepare and validate data", [], "done"),
    ("feature-eng", "Engineer features", ["data-prep"], "pending"),
    ("model-train", "Train model", ["feature-eng"], "planned"),
    ("evaluation", "Evaluate results", ["model-train"], "planned")
]

report = track_task_dependencies(tasks)
print("Task Dependency Report:")
print(report)
```
