"""
think_tool.py - Cognitive Tools for Structured Reasoning

Simplified design: recall (memory) + think (reasoning/exploration)
Inspired by "Eliciting Reasoning in Language Models with Cognitive Tools"
(https://arxiv.org/html/2506.12115).
"""

from typing import Literal, Optional, Union


class ThinkTool:
    """Modular cognitive operations for structured reasoning.

    Core insight: Separate memory recall from active thinking.
    """

    @staticmethod
    def recall(knowledge_content: str, topic_tag: Optional[str] = None) -> None:
        """Retrieve and record factual knowledge (what you know).

        Use this to dump your raw memory/knowledge about a subject into the context.
        This can be internal knowledge or information gathered from the current context.
        Don't just list the topic; write out the actual facts, details, and observations you remember.
        Treat this as a scratchpad for your memory.

        Args:
            knowledge_content: The detailed facts and information you are recalling. Can be long.
            topic_tag: A short label for this memory block.
        """
        return

    @staticmethod
    def think(
        thought_process: str,
        thinking_mode: Optional[
            Union[
                Literal[
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
                ],
                str,  # Allow custom modes
            ]
        ] = None,
        focus_area: Optional[str] = None,
    ) -> None:
        """Record your thinking process - both structured reasoning and free exploration.

        This unified tool handles all forms of active thinking:
        - Structured problem-solving (analysis, planning, verification, etc.)
        - Creative exploration (brainstorming, mental simulation, etc.)
        - Intuitive insights and gut feelings

        Use this whenever you're actively processing information, solving problems,
        or exploring possibilities. Don't summarize - show your actual thought process.

        Args:
            thought_process: Your detailed stream of thoughts. Can be long and messy.
            thinking_mode: (Optional) The type of thinking you're doing. Common modes:
                - Structured: "analysis", "hypothesis", "planning", "verification", "correction"
                - Exploratory: "brainstorming", "mental_simulation", "perspective_taking", "intuition"
                - Or use any custom string that describes your thinking mode
            focus_area: (Optional) What specific problem or topic you're thinking about.
        """
        return
