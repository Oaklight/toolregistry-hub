import pytest

from toolregistry_hub.think_tool import ThinkTool


def test_recall_structure():
    """Test the recall method with new parameter structure."""
    # This should not raise any errors
    ThinkTool.recall(
        knowledge_content="Python 3.11 introduced TaskGroups for better async error handling.",
        topic_tag="Python Async",
    )


def test_reason_structure_analysis():
    """Test reason with 'analysis' type."""
    ThinkTool.reason(
        thought_process="Breaking down the user requirement into three main components.",
        reasoning_type="analysis",
        focus_area="Requirement Gathering",
    )


def test_reason_structure_hypothesis():
    """Test reason with 'hypothesis' type."""
    ThinkTool.reason(
        thought_process="The error might be caused by a race condition in the DB pool.",
        reasoning_type="hypothesis",
        focus_area="Debugging",
    )


def test_reason_structure_planning():
    """Test reason with 'planning' type."""
    ThinkTool.reason(
        thought_process="1. Fix the bug. 2. Add tests. 3. Deploy.",
        reasoning_type="planning",
        focus_area="Release Cycle",
    )


def test_reason_structure_verification():
    """Test reason with 'verification' type."""
    ThinkTool.reason(
        thought_process="Double checking the logic against edge cases.",
        reasoning_type="verification",
        focus_area="Code Review",
    )


def test_reason_structure_correction():
    """Test reason with 'correction' type."""
    ThinkTool.reason(
        thought_process="Actually, the previous assumption was wrong. It's a network timeout.",
        reasoning_type="correction",
        focus_area="Debugging",
    )


def test_think_structure_brainstorming():
    """Test think with 'brainstorming' type."""
    ThinkTool.think(
        thought="Idea 1, Idea 2, Idea 3",
        thinking_type="brainstorming",
        focus_area="Feature Ideation",
    )


def test_think_structure_custom():
    """Test think with a custom thinking type."""
    ThinkTool.think(
        thought="I feel like this is the right direction.",
        thinking_type="gut_feeling",
        focus_area="Decision Making",
    )
