"""
think_tool.py - Unified Cognitive Tool for Structured Reasoning

Single tool design: think (handles all cognitive operations including memory recall)
Inspired by "Eliciting Reasoning in Language Models with Cognitive Tools"
(https://arxiv.org/html/2506.12115).
"""

from typing import Literal, Optional, Union


class ThinkTool:
    """Unified cognitive tool for all thinking operations.

    Core insight: One flexible tool is better than multiple specialized ones.
    The thinking_mode parameter guides the type of cognitive operation.
    """

    @staticmethod
    def think(
        thinking_mode: Optional[
            Union[
                Literal[
                    # Core modes (most commonly used)
                    "reasoning",  # Logical analysis and deduction
                    "planning",  # Breaking down tasks, creating strategies
                    "reflection",  # Reviewing, verifying, self-correction
                    # Memory mode (replaces recall tool)
                    "recalling",  # Dumping knowledge/facts from memory
                    # Creative modes
                    "brainstorming",  # Generating ideas freely
                    "exploring",  # Mental simulation, what-if scenarios
                ],
                str,  # Allow custom modes
            ]
        ] = None,
        focus_area: Optional[str] = None,
        thought_process: str = "",
    ) -> None:
        """Record your cognitive process - thinking, reasoning, planning, or recalling.

        USAGE GUIDE:
        1. First, decide your thinking_mode based on what you need to do
        2. Then, specify the focus_area to narrow your scope
        3. Finally, write out your thought_process in detail

        WHEN TO USE EACH MODE:
        - "reasoning": When analyzing a problem, making logical deductions, or evaluating options
        - "planning": When breaking down a task into steps or creating a strategy
        - "reflection": When reviewing your work, checking for errors, or self-correcting
        - "recalling": When you need to dump facts/knowledge from memory into context
        - "brainstorming": When generating creative ideas without judgment
        - "exploring": When doing mental simulations or considering hypotheticals

        Args:
            thinking_mode: The type of cognitive operation. Choose this FIRST to guide your thinking.
                Core modes: "reasoning", "planning", "reflection"
                Memory mode: "recalling" (use this to dump knowledge/facts)
                Creative modes: "brainstorming", "exploring"
                Or use any custom string that describes your thinking mode.
            focus_area: What specific problem or topic you're thinking about. Set this SECOND.
            thought_process: Your detailed stream of thoughts. Write this LAST.
                Can be long and messy. Don't summarize - show your actual thought process.
        """
        return
