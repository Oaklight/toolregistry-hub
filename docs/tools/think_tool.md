---
title: Cognitive Tools
summary: Modular cognitive operations for structured reasoning
description: Cognitive tools separate knowledge recall from logical reasoning, inspired by cognitive psychology research and designed for AI integration.
keywords: cognitive tools, reasoning, memory, recall, think tool, AI tools
author: Oaklight
---

# Cognitive Tools

Cognitive tools provide modular operations for structured reasoning, separating **knowledge/memory/facts** from **reasoning/logic**. Design inspired by [Anthropic's Claude Think Tool](https://www.anthropic.com/engineering/claude-think-tool) and the cognitive psychology paper ["Eliciting Reasoning in Language Models with Cognitive Tools"](https://arxiv.org/html/2506.12115).

## 🎯 Design Philosophy

### Why Do We Need Cognitive Tools?

When interacting with AI models, we found that the model's "thinking" process is often a black box. The core goal of cognitive tools is: **transform the model's thinking process from "black box" to "white box"**, making its reasoning visible, traceable, and correctable.

Research shows that **knowledge and reasoning are separate cognitive processes**:

- **Knowledge/Memory/Facts**: Content about the world, observations, context
- **Reasoning/Logic**: Mathematical/logical operations independent of specific world knowledge

Our tools reflect this separation for clearer, more structured thinking.

### Design Evolution

#### Generation 1: Single `think()` Tool

The initial design, inspired by [Anthropic's Claude Think Tool](https://www.anthropic.com/engineering/claude-think-tool), had only one `think()` method, allowing models to freely record thinking content like a scratchpad. This design was simple and direct, but we discovered problems in practice:

- **Lack of structure**: Model's thinking content was mixed, hard to distinguish between recalling facts and performing reasoning
- **Difficult to trace**: Users couldn't quickly locate problem types when reviewing
- **Low efficiency**: Models didn't know when to use which thinking approach

#### Generation 2: Three-Tool Separation (`recall` + `reason` + `think`)

Inspired by Brown et al.'s paper ["Eliciting Reasoning in Language Models with Cognitive Tools"](https://arxiv.org/html/2506.12115), we subdivided the cognitive process into three independent tools:

- **`recall()`**: Specifically for memory retrieval and fact statements
- **`reason()`**: For goal-directed logical reasoning with explicit reasoning stage markers
- **`think()`**: For free exploratory thinking without structural constraints

This design was theoretically perfect, but in actual use we found:

- **Model selection difficulty**: Models either only used `think` or only used `reason`, rarely mixing them
- **Blurred boundaries**: The distinction between `reason` and `think` wasn't intuitive enough for models
- **Cognitive burden**: Three tools increased the model's selection cost

#### Generation 3: Current Design (`recall` + `think`)

Based on actual usage feedback, we made a key simplification: **merge `reason` and `think` into a unified `think` tool**.

**Core improvements:**

1. **Simplified selection**: Models no longer need to struggle between `think` and `reason`
2. **Clear contrast**: `recall` (static knowledge) vs `think` (dynamic thinking)
3. **Preserved flexibility**: Support all thinking modes through `thinking_mode` parameter
4. **Encourage detail**: Parameter naming (`thought_process`) hints at writing lengthy content

**Design philosophy:**

- **Tools as recorders**: These tools don't execute operations, they record thinking processes
- **Parameters as hints**: Guide model behavior through parameter naming (`thought_process` instead of `content`)
- **Modes as guidance**: Predefined modes provide direction but don't limit creativity

## 🚀 Quick Start

```python
from toolregistry_hub import ThinkTool

# Recall facts and knowledge (memory)
ThinkTool.recall(
    knowledge_content="FastAPI uses dependency injection. Project has blocking DB calls "
                      "that need to be converted to async for proper performance.",
    topic_tag="Python async patterns"
)

# Record thinking process (includes structured reasoning and free exploration)
ThinkTool.think(
    thought_process="Blocking calls in async context cause performance issues. "
                    "Need to use asyncpg for async PostgreSQL. "
                    "Solution: Replace sync DB calls with async equivalents.",
    thinking_mode="analysis",
    focus_area="Database performance optimization"
)
```

## 🔧 API Reference

### `recall(knowledge_content: str, topic_tag: Optional[str] = None)`

Retrieve and record factual knowledge (what you know). Use this to dump your raw memory/knowledge about a subject into the context.

**Parameters:**

- `knowledge_content` (str): The detailed facts and information you are recalling. Can be long.
- `topic_tag` (str, optional): A short label for this memory block.

### `think(thought_process: str, thinking_mode: Optional[str] = None, focus_area: Optional[str] = None)`

Record your thinking process - both structured reasoning and free exploration.

This unified tool handles all forms of active thinking:

- Structured problem-solving (analysis, planning, verification, etc.)
- Creative exploration (brainstorming, mental simulation, etc.)
- Intuitive insights and gut feelings

**Parameters:**

- `thought_process` (str): Your detailed stream of thoughts. Can be long and messy.
- `thinking_mode` (str, optional): The type of thinking you're doing. Common modes:
    - Structured: `"analysis"`, `"hypothesis"`, `"planning"`, `"verification"`, `"correction"`
    - Exploratory: `"brainstorming"`, `"mental_simulation"`, `"perspective_taking"`, `"intuition"`
    - Or use any custom string that describes your thinking mode
- `focus_area` (str, optional): What specific problem or topic you're thinking about.

**Thinking Mode Descriptions:**

| Mode | Purpose | Example Scenario |
|------|---------|------------------|
| `analysis` | Systematically analyze problems | Examine error patterns, understand root causes |
| `hypothesis` | Form theories about causes | Infer possible causes based on symptoms |
| `planning` | Develop solution plans | Design implementation steps and strategies |
| `verification` | Check if something works | Test fixes, confirm results |
| `correction` | Fix mistakes in thinking | Correct previous wrong assumptions |
| `brainstorming` | Generate ideas freely | Explore multiple possibilities without judgment |
| `mental_simulation` | Imagine how something plays out | Simulate user interaction flows |
| `perspective_taking` | Consider other viewpoints | Think from different role perspectives |
| `intuition` | Follow gut feelings | Instinctive judgments based on experience |

## 🎯 Usage Guide

### When to Use `recall()`

- Before reasoning, to gather relevant background
- To explicitly state what you know/remember
- To separate factual recall from logical inference
- Treat this as a scratchpad for your memory

### When to Use `think()`

- Analyze problems
- Form hypotheses
- Plan solutions
- Verify results
- Correct mistakes
- Brainstorm
- Explore possibilities
- Follow intuition

### Best Practices

**1. Separate Memory from Logic**

```python
# First recall facts
ThinkTool.recall(
    knowledge_content="Python 3.9 introduced dict merge operator |. "
                      "Project requires Python 3.9+.",
    topic_tag="Python 3.9 features"
)

# Then reason about them
ThinkTool.think(
    thought_process="We currently use dict(**a, **b) for merging configs. "
                    "The | operator is cleaner and more readable. "
                    "Since we require 3.9+, we can safely use this.",
    thinking_mode="planning"
)
```

**2. Don't Summarize - Show the Full Process**

```python
# Good practice
ThinkTool.think(
    thought_process="First checking error logs... found timeout errors. "
                    "Timeout occurs in database queries. Looking at the query, missing index. "
                    "Adding index should solve it. But need to verify in test environment first...",
    thinking_mode="analysis"
)

# Avoid
ThinkTool.think(
    thought_process="Found it's an index issue",  # Too brief, lost the thinking process
    thinking_mode="analysis"
)
```

**3. Use Appropriate Thinking Modes**

Choose the mode that best describes your current thinking type, but don't overthink it - modes are guidance, not restrictions.

## 🚨 Important Notes

### What These Tools Do

- **recall()**: Retrieve and record factual knowledge from memory
- **think()**: Record various forms of active thinking processes

### What These Tools Do NOT Do

- Access external information or APIs
- Make changes to code or data
- Execute code or run tests
- Access file systems or databases
- Perform actual computations

These tools are **recorders of thinking processes**, not executors. Their value lies in making thinking processes visible, traceable, and improvable.

## 📚 References

- Anthropic, ["Claude Think Tool"](https://www.anthropic.com/engineering/claude-think-tool) - Inspiration for the early single-tool design
- Brown et al., ["Eliciting Reasoning in Language Models with Cognitive Tools"](https://arxiv.org/html/2506.12115) - Theoretical foundation for the three-tool separation design
- Cognitive psychology research on knowledge vs. reasoning separation
- Anderson's ACT-R cognitive architecture

## 🔗 Related Tools

- [Calculator](calculator.md) - For actual mathematical computations
- [Todo List](todo_list.md) - For task tracking and planning
- [File Operations](file_ops.md) - For reading/writing files