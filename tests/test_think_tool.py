from toolregistry_hub.think_tool import ThinkTool


def test_think_reasoning_mode():
    """Test think with 'reasoning' mode (core mode)."""
    ThinkTool.think(
        thinking_mode="reasoning",
        focus_area="Requirement Gathering",
        thought_process="Breaking down the user requirement into three main components.",
    )


def test_think_planning_mode():
    """Test think with 'planning' mode (core mode)."""
    ThinkTool.think(
        thinking_mode="planning",
        focus_area="Release Cycle",
        thought_process="1. Fix the bug. 2. Add tests. 3. Deploy.",
    )


def test_think_reflection_mode():
    """Test think with 'reflection' mode (core mode)."""
    ThinkTool.think(
        thinking_mode="reflection",
        focus_area="Code Review",
        thought_process="Double checking the logic against edge cases. The previous assumption was wrong.",
    )


def test_think_recalling_mode():
    """Test think with 'recalling' mode (memory mode - replaces old recall tool)."""
    ThinkTool.think(
        thinking_mode="recalling",
        focus_area="Python Async",
        thought_process="Python 3.11 introduced TaskGroups for better async error handling.",
    )


def test_think_brainstorming_mode():
    """Test think with 'brainstorming' mode (creative mode)."""
    ThinkTool.think(
        thinking_mode="brainstorming",
        focus_area="Feature Ideation",
        thought_process="Idea 1, Idea 2, Idea 3",
    )


def test_think_exploring_mode():
    """Test think with 'exploring' mode (creative mode)."""
    ThinkTool.think(
        thinking_mode="exploring",
        focus_area="UX Design",
        thought_process="If we implement this feature, users would first see X, then interact with Y...",
    )


def test_think_custom_mode():
    """Test think with a custom thinking mode."""
    ThinkTool.think(
        thinking_mode="trade_off_analysis",
        focus_area="Architecture Decision",
        thought_process="Considering the trade-offs between performance and maintainability...",
    )


def test_think_without_optional_params():
    """Test think without optional parameters."""
    ThinkTool.think(
        thought_process="Analyzing the problem step by step to find the root cause."
    )


def test_think_without_focus_area():
    """Test think without optional focus_area."""
    ThinkTool.think(
        thinking_mode="brainstorming",
        thought_process="What if we try a completely different approach?",
    )


def test_think_with_all_modes():
    """Test think with all predefined thinking modes."""
    all_modes = [
        # Core modes
        "reasoning",
        "planning",
        "reflection",
        # Memory mode
        "recalling",
        # Creative modes
        "brainstorming",
        "exploring",
    ]
    for mode in all_modes:
        ThinkTool.think(
            thinking_mode=mode,
            thought_process=f"Testing {mode} mode with detailed thought process.",
        )


def test_think_long_thought_process():
    """Test think with a long, detailed thought process."""
    long_process = """
    First, I need to understand the problem domain.
    The user is asking about X, which relates to Y.
    Let me break this down:
    1. Component A does this
    2. Component B does that
    3. They interact through Z
    
    Now, considering the constraints:
    - Time is limited
    - Resources are constrained
    - Quality must be maintained
    
    My conclusion is that we should proceed with approach C because...
    """
    ThinkTool.think(
        thinking_mode="reasoning",
        focus_area="Complex Problem Solving",
        thought_process=long_process,
    )
