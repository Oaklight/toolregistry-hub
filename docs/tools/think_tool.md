---
title: Cognitive Tools
summary: Modular cognitive operations for structured reasoning
description: Cognitive tools separate knowledge recall from logical reasoning, inspired by cognitive psychology research and designed for AI integration.
keywords: cognitive tools, reasoning, memory, recall, think tool, AI tools
author: Oaklight
---

# Cognitive Tools

Cognitive tools provide modular operations for structured reasoning, separating **knowledge/memory/facts** from **reasoning/logic**. Inspired by cognitive psychology and the paper ["Eliciting Reasoning in Language Models with Cognitive Tools"](https://arxiv.org/html/2506.12115).

???+ note "Changelog"
    **0.6.0** - Major redesign: Separated into `recall()` (memory) and `reason()` (logic) with `cognitive_operation()` for extensibility

    0.5.0 - No longer return thoughts as json

## 🎯 Core Concept

Research shows that **knowledge and reasoning are separate cognitive processes**:

- **Knowledge/Memory/Facts**: Content about the world, observations, context
- **Reasoning/Logic**: Mathematical/logical operations independent of specific world knowledge

Our tools reflect this separation for clearer, more structured thinking.

## 🚀 Quick Start

```python
from toolregistry_hub import ThinkTool

# Recall facts and knowledge (memory)
ThinkTool.recall(
    topic="Python async patterns",
    context="Project uses FastAPI, has blocking DB calls"
)

# Perform logical reasoning
ThinkTool.reason(
    content="Blocking calls in async context cause performance issues. "
            "Need to use asyncpg for async PostgreSQL. "
            "Solution: Replace sync DB calls with async equivalents.",
    reasoning_type="causal"
)

# Custom cognitive operation for novel patterns
ThinkTool.cognitive_operation(
    operation_type="hypothesis_generation",
    content="H1: DB query issue (high likelihood)\n"
            "H2: Memory leak (medium)\n"
            "H3: Network latency (low)",
    metadata="Single-cause debugging failed, trying multiple hypotheses"
)
```

## 🔧 API Reference

### `recall(topic: str, context: Optional[str] = None)`

Recall facts, knowledge, and observations. This is for **memory**, not reasoning.

**When to use:**

- Before reasoning, to gather relevant background
- To explicitly state what you know/remember
- To separate factual recall from logical inference

**Parameters:**

- `topic` (str): What to recall information about
- `context` (str, optional): Observed facts from current situation

**Examples:**

```python
# Recall general knowledge
ThinkTool.recall(
    topic="FastAPI dependency injection patterns"
)

# Recall with current context
ThinkTool.recall(
    topic="Bug in auth.py line 45",
    context="Started after v2.0, affects 5% of users, no pattern in user types"
)
```

### `reason(content: str, reasoning_type: Optional[str] = None)`

Perform logical reasoning and analysis.

**When to use:**

- Problem analysis
- Evaluating options and trade-offs
- Drawing conclusions
- Planning solutions
- Understanding problems
- Examining solutions

**Parameters:**

- `content` (str): Your reasoning process and conclusions
- `reasoning_type` (str, optional): Type of reasoning - `"deductive"`, `"inductive"`, `"abductive"`, `"analogical"`, or `"causal"`

**Reasoning Types:**

- **deductive**: From general principles to specific conclusion
- **inductive**: From specific observations to general pattern
- **abductive**: Inference to best explanation
- **analogical**: Reasoning by analogy/similarity
- **causal**: Cause-and-effect reasoning

**Examples:**

```python
# Problem analysis
ThinkTool.reason(
    content="Auth fails after v2.0. New code has shared cache without locks. "
            "Intermittent failures suggest race condition. Fix: add synchronization.",
    reasoning_type="causal"
)

# Solution evaluation
ThinkTool.reason(
    content="Option A: Mutex lock - simple but may reduce throughput. "
            "Option B: Thread-safe cache - better performance but more complex. "
            "Choose B for long-term maintainability."
)
```

### `cognitive_operation(operation_type: str, content: str, metadata: Optional[str] = None)`

Custom cognitive operation for patterns not covered by recall/reason.

**When to use:**

- Your thinking doesn't fit recall or reason
- Novel reasoning patterns
- Domain-specific cognitive operations

**Parameters:**

- `operation_type` (str): Name of operation
- `content` (str): The cognitive work being performed
- `metadata` (str, optional): Context about why/how this operation is used

**Common Operation Types:**

- `hypothesis_generation`: Create multiple hypotheses to test
- `mental_simulation`: Simulate execution/outcomes mentally
- `constraint_satisfaction`: Work through constraints systematically
- `pattern_matching`: Identify patterns in data/code
- `metacognitive_monitoring`: Reflect on your reasoning process

**Examples:**

```python
# Hypothesis generation
ThinkTool.cognitive_operation(
    operation_type="hypothesis_generation",
    content="H1: DB query inefficiency (high likelihood, test: add query logging)\n"
            "H2: Memory leak in cache (medium, test: monitor memory)\n"
            "H3: Network latency (low, test: check network metrics)",
    metadata="Single-cause debugging failed"
)

# Mental simulation
ThinkTool.cognitive_operation(
    operation_type="mental_simulation",
    content="1. User clicks → onClick handler\n"
            "2. Handler calls API → async request\n"
            "3. UI shows loading (MISSING!)\n"
            "4. API returns → state update\n"
            "Problem: No loading state shown",
    metadata="Simulating to find UX issue"
)
```

## 🛠️ Usage Patterns

### Complete Problem-Solving Workflow

```python
from toolregistry_hub import ThinkTool

# Step 1: Recall relevant knowledge
ThinkTool.recall(
    topic="Authentication systems and race conditions",
    context="v2.0 refactored token validation, intermittent failures for 5% users"
)

# Step 2: Reason about the problem
ThinkTool.reason(
    content="Timing correlation: failures started with v2.0 deployment. "
            "Intermittent nature suggests race condition, not logic error. "
            "v2.0 introduced shared cache without proper locking. "
            "Conclusion: Race condition in cache access.",
    reasoning_type="causal"
)

# Step 3: Generate solution hypotheses
ThinkTool.cognitive_operation(
    operation_type="hypothesis_generation",
    content="Solution 1: Add mutex lock (simple, may reduce throughput)\n"
            "Solution 2: Use thread-safe cache (better performance)\n"
            "Solution 3: Remove caching (safest, worst performance)"
)

# Step 4: Evaluate solutions
ThinkTool.reason(
    content="Solution 1 works but impacts performance under load. "
            "Solution 2 is best long-term: better performance and maintainability. "
            "Solution 3 is too drastic. "
            "Decision: Implement thread-safe cache (Solution 2)."
)
```

### Debugging Strategy

```python
# Recall observations
ThinkTool.recall(
    topic="Memory leak symptoms",
    context="Memory usage increases linearly over time, "
            "correlates with user sessions, "
            "started after adding WebSocket support"
)

# Analyze cause
ThinkTool.reason(
    content="Linear growth + session correlation suggests per-session leak. "
            "WebSocket timing is suspicious. "
            "Likely cause: WebSocket event listeners not being removed. "
            "Need to check cleanup in session termination.",
    reasoning_type="abductive"
)
```

### Design Decision

```python
# Recall constraints
ThinkTool.recall(
    topic="Project tech stack and requirements",
    context="FastAPI backend, 15 similar endpoints, team prefers DRY principles"
)

# Reason about approach
ThinkTool.reason(
    content="15 similar endpoints → high duplication risk. "
            "Could use base class, but FastAPI works better with dependency injection. "
            "Factory function pattern is more Pythonic and plays well with FastAPI. "
            "Decision: Use factory functions instead of inheritance.",
    reasoning_type="analogical"
)
```

## 🎯 Best Practices

### 1. Separate Memory from Logic

**Good:**

```python
# First recall facts
ThinkTool.recall(
    topic="Python 3.9 features",
    context="Project requires Python 3.9+"
)

# Then reason about them
ThinkTool.reason(
    content="Python 3.9 introduced dict merge operator |. "
            "This simplifies our config merging code. "
            "Can replace dict(**a, **b) with a | b."
)
```

**Avoid:**

```python
# Don't mix memory and reasoning
ThinkTool.reason(
    content="Python 3.9 has dict merge (this is memory, not reasoning). "
            "We can use it to simplify code (this is reasoning)."
)
```

### 2. Use Appropriate Reasoning Types

```python
# Causal reasoning for cause-effect
ThinkTool.reason(
    content="Change X caused effect Y because...",
    reasoning_type="causal"
)

# Abductive reasoning for best explanation
ThinkTool.reason(
    content="Given symptoms A, B, C, most likely cause is...",
    reasoning_type="abductive"
)

# Inductive reasoning for patterns
ThinkTool.reason(
    content="These 5 bugs all involve null checks. "
            "Pattern: need better null handling throughout.",
    reasoning_type="inductive"
)
```

### 3. Use cognitive_operation for Novel Patterns

```python
# When standard tools don't fit
ThinkTool.cognitive_operation(
    operation_type="constraint_satisfaction",
    content="✓ Must use Python 3.9+ (satisfied)\n"
            "✓ Must be async (satisfied)\n"
            "✗ No new dependencies (violated: need aiohttp)\n"
            "→ Decision: Use stdlib urllib with asyncio",
    metadata="Systematic constraint checking"
)
```

## 🚨 Important Notes

### What These Tools Do

- **recall()**: Explicitly state facts, knowledge, observations
- **reason()**: Perform logical analysis, evaluation, planning
- **cognitive_operation()**: Custom operations for novel patterns

### What These Tools Do NOT Do

- Access external information or APIs
- Make changes to code or data
- Execute code or run tests
- Access file systems or databases
- Perform actual computations

### Legacy `think()` Method

The original `think(reasoning, facts)` method is still available for backward compatibility but is deprecated. Use `recall()` and `reason()` instead for clearer separation of concerns.

```python
# Legacy (deprecated)
ThinkTool.think(
    reasoning="Some reasoning...",
    facts="Some facts..."
)

# New approach (recommended)
ThinkTool.recall(topic="...", context="...")
ThinkTool.reason(content="...")
```

## 📚 References

- Brown et al., ["Eliciting Reasoning in Language Models with Cognitive Tools"](https://arxiv.org/html/2506.12115)
- Cognitive psychology research on knowledge vs. reasoning separation
- Anderson's ACT-R cognitive architecture

## 🔗 Related Tools

- [Calculator](calculator.md) - For actual mathematical computations
- [Todo List](todo_list.md) - For task tracking and planning
- [File Operations](file_ops.md) - For reading/writing files
