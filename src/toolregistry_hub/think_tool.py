"""
think_tool.py - Simple Claude Think Tool implementation

A simple implementation of the "think" tool as described by Anthropic.
This tool provides a space for Claude to think and reason without obtaining
new information or making changes.
"""


class ThinkTool:
    """Simple Claude Think Tool for reasoning and brainstorming.

    This tool allows Claude to think about problems, brainstorm solutions,
    and reason through complex scenarios without making any external changes.
    """

    @staticmethod
    def think(thought: str) -> None:
        """Use the tool to think about something. It will not obtain new information or make any changes to the repository, but just log the thought. Use it when complex reasoning or brainstorming is needed. For example, if you explore the repo and discover the source of a bug, call this tool to brainstorm several unique ways of fixing the bug, and assess which change(s) are likely to be simplest and most effective. Alternatively, if you receive some test results, call this tool to brainstorm ways to fix the failing tests."""
        return
