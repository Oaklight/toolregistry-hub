import pytest

from toolregistry_hub.think_tool import ThinkTool


def test_recall_structure():
    """Test the recall method with parameter structure."""
    # This should not raise any errors
    ThinkTool.recall(
        knowledge_content="Python 3.11 introduced TaskGroups for better async error handling.",
        topic_tag="Python Async",
    )


def test_recall_without_topic_tag():
    """Test recall without optional topic_tag."""
    ThinkTool.recall(
        knowledge_content="FastAPI uses Pydantic for data validation and serialization."
    )


def test_think_structured_analysis():
    """Test think with 'analysis' mode (structured reasoning)."""
    ThinkTool.think(
        thought_process="Breaking down the user requirement into three main components.",
        thinking_mode="analysis",
        focus_area="Requirement Gathering",
    )


def test_think_structured_hypothesis():
    """Test think with 'hypothesis' mode (structured reasoning)."""
    ThinkTool.think(
        thought_process="The error might be caused by a race condition in the DB pool.",
        thinking_mode="hypothesis",
        focus_area="Debugging",
    )


def test_think_structured_planning():
    """Test think with 'planning' mode (structured reasoning)."""
    ThinkTool.think(
        thought_process="1. Fix the bug. 2. Add tests. 3. Deploy.",
        thinking_mode="planning",
        focus_area="Release Cycle",
    )


def test_think_structured_verification():
    """Test think with 'verification' mode (structured reasoning)."""
    ThinkTool.think(
        thought_process="Double checking the logic against edge cases.",
        thinking_mode="verification",
        focus_area="Code Review",
    )


def test_think_structured_correction():
    """Test think with 'correction' mode (structured reasoning)."""
    ThinkTool.think(
        thought_process="Actually, the previous assumption was wrong. It's a network timeout.",
        thinking_mode="correction",
        focus_area="Debugging",
    )


def test_think_exploratory_brainstorming():
    """Test think with 'brainstorming' mode (exploratory thinking)."""
    ThinkTool.think(
        thought_process="Idea 1, Idea 2, Idea 3",
        thinking_mode="brainstorming",
        focus_area="Feature Ideation",
    )


def test_think_exploratory_mental_simulation():
    """Test think with 'mental_simulation' mode (exploratory thinking)."""
    ThinkTool.think(
        thought_process="If we implement this feature, users would first see X, then interact with Y...",
        thinking_mode="mental_simulation",
        focus_area="UX Design",
    )


def test_think_exploratory_perspective_taking():
    """Test think with 'perspective_taking' mode (exploratory thinking)."""
    ThinkTool.think(
        thought_process="From the user's perspective, this might be confusing because...",
        thinking_mode="perspective_taking",
        focus_area="User Experience",
    )


def test_think_exploratory_intuition():
    """Test think with 'intuition' mode (exploratory thinking)."""
    ThinkTool.think(
        thought_process="I feel like this is the right direction.",
        thinking_mode="intuition",
        focus_area="Decision Making",
    )


def test_think_custom_mode():
    """Test think with a custom thinking mode."""
    ThinkTool.think(
        thought_process="Considering the trade-offs between performance and maintainability...",
        thinking_mode="trade_off_analysis",
        focus_area="Architecture Decision",
    )


def test_think_without_optional_params():
    """Test think without optional parameters."""
    ThinkTool.think(
        thought_process="Analyzing the problem step by step to find the root cause."
    )


def test_think_without_focus_area():
    """Test think without optional focus_area."""
    ThinkTool.think(
        thought_process="What if we try a completely different approach?",
        thinking_mode="brainstorming",
    )


def test_think_with_all_modes():
    """Test think with all predefined thinking modes."""
    all_modes = [
        # Structured reasoning modes
        "analysis",
        "hypothesis",
        "planning",
        "verification",
        "correction",
        # Exploratory thinking modes
        "brainstorming",
        "mental_simulation",
        "perspective_taking",
        "intuition",
    ]
    for mode in all_modes:
        ThinkTool.think(
            thought_process=f"Testing {mode} mode with detailed thought process.",
            thinking_mode=mode,
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
        thought_process=long_process,
        thinking_mode="analysis",
        focus_area="Complex Problem Solving",
    )
