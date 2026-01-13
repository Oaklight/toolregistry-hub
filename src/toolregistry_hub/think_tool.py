"""
think_tool.py - Cognitive Tools for Structured Reasoning

Inspired by "Eliciting Reasoning in Language Models with Cognitive Tools"
(https://arxiv.org/html/2506.12115). Separates memory recall from logical reasoning.
"""

from typing import Literal, Optional, Union


class ThinkTool:
    """Modular cognitive operations for structured reasoning.

    Core insight: Complex reasoning = orchestrated execution of specific cognitive operations.
    Reference: Brown et al., "Eliciting Reasoning in Language Models with Cognitive Tools"
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
    def reason(
        thought_process: str,
        reasoning_type: Optional[
            Literal["analysis", "hypothesis", "planning", "verification", "correction"]
        ] = None,
        focus_area: Optional[str] = None,
    ) -> None:
        """Perform step-by-step logical reasoning (how you solve problems).

        Use this for structured problem-solving: analyzing situations, forming hypotheses, planning solutions, verifying results, or correcting mistakes.

        Args:
            thought_process: Your detailed stream of thoughts. Don't summarize; show the work.
            reasoning_type: The stage of the problem-solving lifecycle.
            focus_area: What specific problem are you trying to solve here?
        """
        return

    @staticmethod
    def think(
        thought: str,
        thinking_type: Union[
            Literal[
                "brainstorming", "mental_simulation", "perspective_taking", "intuition"
            ],
            str,
        ],
        focus_area: Optional[str] = None,
    ) -> None:
        """Free-form exploratory thinking without a predetermined path.

        Use this when you need to explore possibilities without committing to a specific reasoning structure. Unlike 'recall' (which retrieves facts) or 'reason' (which follows a goal-directed path), this is for open-ended exploration, gut feelings, or trying out ideas.

        Args:
            thought: The content of your exploratory thinking.
            thinking_type: The specific mode of thinking. Recommended: "brainstorming", "mental_simulation", "perspective_taking", "intuition", or any custom string.
            focus_area: The context or problem you are thinking about.
        """
        return
