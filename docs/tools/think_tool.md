---
title: Cognitive Tools
summary: Unified cognitive tool for structured reasoning
description: A single think tool that handles all cognitive operations including memory recall, reasoning, and exploration.
keywords: cognitive tools, reasoning, memory, think tool, AI tools
author: Oaklight
---

# Cognitive Tools

A unified cognitive tool for structured reasoning, combining **knowledge recall**, **logical reasoning**, and **creative exploration** into a single flexible interface. Design inspired by [Anthropic's Claude Think Tool](https://www.anthropic.com/engineering/claude-think-tool) and the cognitive psychology paper ["Eliciting Reasoning in Language Models with Cognitive Tools"](https://arxiv.org/html/2506.12115).

## 🎯 Design Philosophy

### Why a Unified Tool?

When interacting with AI models, we found that the model's "thinking" process is often a black box. The core goal of cognitive tools is: **transform the model's thinking process from "black box" to "white box"**, making its reasoning visible, traceable, and correctable.

### Design Evolution

#### Generation 1-3: From Complexity to Simplicity

We went through several iterations:

1. **Single `think()` tool** - Simple but lacked structure
2. **Three tools (`recall` + `reason` + `think`)** - Theoretically perfect but models struggled to choose
3. **Two tools (`recall` + `think`)** - Better, but `recall` was rarely used in practice

#### Generation 4: Current Design (Unified `think`)

Based on real-world usage feedback, we made a key insight: **models almost never used `recall` separately**. They preferred to dump everything into `think`. So we:

1. **Merged `recall` into `think`** - Added `"recalling"` as a thinking mode
2. **Reordered parameters** - `thinking_mode` → `focus_area` → `thought_process` (decide HOW to think before WHAT to think)
3. **Simplified modes** - Reduced from 9 to 6 core modes with clear use cases

**Design philosophy:**

- **One tool, many modes**: Simpler mental model for the AI
- **Parameter order matters**: Guide the model to decide thinking approach first
- **Modes as guidance**: Predefined modes provide direction but don't limit creativity

## 🚀 Quick Start

```python
from toolregistry_hub import ThinkTool

# Recall facts and knowledge (using "recalling" mode)
ThinkTool.think(
    thinking_mode="recalling",
    focus_area="Python async patterns",
    thought_process="FastAPI uses dependency injection. Project has blocking DB calls "
                    "that need to be converted to async for proper performance."
)

# Analyze a problem
ThinkTool.think(
    thinking_mode="reasoning",
    focus_area="Database performance optimization",
    thought_process="Blocking calls in async context cause performance issues. "
                    "Need to use asyncpg for async PostgreSQL. "
                    "Solution: Replace sync DB calls with async equivalents."
)

# Plan implementation steps
ThinkTool.think(
    thinking_mode="planning",
    focus_area="Migration strategy",
    thought_process="1. Identify all sync DB calls. 2. Install asyncpg. "
                    "3. Create async connection pool. 4. Migrate one endpoint at a time."
)
```

## 🔧 API Reference

### `think(thinking_mode, focus_area, thought_process)`

Record your cognitive process - thinking, reasoning, planning, or recalling.

**Parameters (in recommended order):**

1. `thinking_mode` (str, optional): The type of cognitive operation. **Choose this FIRST** to guide your thinking.
    - Core modes: `"reasoning"`, `"planning"`, `"reflection"`
    - Memory mode: `"recalling"` (use this to dump knowledge/facts)
    - Creative modes: `"brainstorming"`, `"exploring"`
    - Or use any custom string

2. `focus_area` (str, optional): What specific problem or topic you're thinking about. **Set this SECOND**.

3. `thought_process` (str): Your detailed stream of thoughts. **Write this LAST**. Can be long and messy.

**Thinking Mode Descriptions:**

| Mode | Purpose | When to Use |
|------|---------|-------------|
| `reasoning` | Logical analysis and deduction | Analyzing problems, evaluating options, making logical deductions |
| `planning` | Breaking down tasks, creating strategies | Designing implementation steps, creating action plans |
| `reflection` | Reviewing, verifying, self-correction | Checking your work, finding errors, correcting assumptions |
| `recalling` | Dumping knowledge/facts from memory | Gathering background info, stating what you know |
| `brainstorming` | Generating ideas freely | Exploring possibilities without judgment |
| `exploring` | Mental simulation, what-if scenarios | Imagining how things play out, considering hypotheticals |

## 🎯 Usage Guide

### Parameter Order Matters

The parameter order is intentional: `thinking_mode` → `focus_area` → `thought_process`

This guides the model to:
1. **First** decide HOW to think (mode)
2. **Then** narrow the scope (focus)
3. **Finally** write the actual thoughts

```python
# Good: Mode first, then focus, then content
ThinkTool.think(
    thinking_mode="planning",           # 1. Decide approach
    focus_area="API refactoring",       # 2. Narrow scope
    thought_process="Step 1: ..."       # 3. Write thoughts
)
```

### When to Use Each Mode

**`reasoning`** - For logical analysis:
```python
ThinkTool.think(
    thinking_mode="reasoning",
    focus_area="Error diagnosis",
    thought_process="The error occurs after the database call. "
                    "Looking at the stack trace, it's a connection timeout. "
                    "This suggests the connection pool is exhausted..."
)
```

**`planning`** - For task breakdown:
```python
ThinkTool.think(
    thinking_mode="planning",
    focus_area="Feature implementation",
    thought_process="1. Create the data model. 2. Add API endpoint. "
                    "3. Write tests. 4. Update documentation."
)
```

**`reflection`** - For self-correction:
```python
ThinkTool.think(
    thinking_mode="reflection",
    focus_area="Previous assumption",
    thought_process="Wait, I assumed the error was in the database layer, "
                    "but looking more carefully, it's actually a network issue..."
)
```

**`recalling`** - For knowledge dump:
```python
ThinkTool.think(
    thinking_mode="recalling",
    focus_area="Python 3.9 features",
    thought_process="Python 3.9 introduced dict merge operator |. "
                    "Also added removeprefix() and removesuffix() to strings. "
                    "Type hints got more flexible with built-in generics."
)
```

**`brainstorming`** - For idea generation:
```python
ThinkTool.think(
    thinking_mode="brainstorming",
    focus_area="Performance optimization",
    thought_process="Could use caching. Maybe Redis? Or in-memory LRU? "
                    "What about lazy loading? Or precomputing results? "
                    "Database indexing might help too..."
)
```

**`exploring`** - For what-if scenarios:
```python
ThinkTool.think(
    thinking_mode="exploring",
    focus_area="Architecture decision",
    thought_process="If we use microservices, we'd need service discovery. "
                    "That adds complexity but improves scalability. "
                    "What if we start monolithic and split later?"
)
```

### Best Practices

**1. Don't Summarize - Show the Full Process**

```python
# Good: Detailed thinking
ThinkTool.think(
    thinking_mode="reasoning",
    focus_area="Bug investigation",
    thought_process="First checking error logs... found timeout errors. "
                    "Timeout occurs in database queries. Looking at the query, missing index. "
                    "Adding index should solve it. But need to verify in test environment first..."
)

# Avoid: Too brief
ThinkTool.think(
    thinking_mode="reasoning",
    focus_area="Bug investigation",
    thought_process="Found it's an index issue"  # Lost the thinking process
)
```

**2. Use Modes Appropriately**

Choose the mode that best describes your current thinking type, but don't overthink it - modes are guidance, not restrictions.

## 🚨 Important Notes

### What This Tool Does

- Records various forms of cognitive processes
- Makes thinking visible and traceable
- Guides structured reasoning through modes

### What This Tool Does NOT Do

- Access external information or APIs
- Make changes to code or data
- Execute code or run tests
- Perform actual computations

This tool is a **recorder of thinking processes**, not an executor. Its value lies in making thinking visible, traceable, and improvable.

## 📚 References

- Anthropic, ["Claude Think Tool"](https://www.anthropic.com/engineering/claude-think-tool) - Original inspiration
- Brown et al., ["Eliciting Reasoning in Language Models with Cognitive Tools"](https://arxiv.org/html/2506.12115) - Theoretical foundation
- Cognitive psychology research on knowledge vs. reasoning separation

## 🔗 Related Tools

- [Calculator](calculator.md) - For actual mathematical computations
- [Todo List](todo_list.md) - For task tracking and planning
- [File Operations](file_ops.md) - For reading/writing files
