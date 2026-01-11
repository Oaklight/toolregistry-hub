"""
think_tool.py - Cognitive Tools for Structured Reasoning

Inspired by "Eliciting Reasoning in Language Models with Cognitive Tools"
(https://arxiv.org/html/2506.12115). Separates memory recall from logical reasoning.
"""

from typing import Literal, Optional


class ThinkTool:
    """Modular cognitive operations for structured reasoning.

    Core insight: Complex reasoning = orchestrated execution of specific cognitive operations.
    Reference: Brown et al., "Eliciting Reasoning in Language Models with Cognitive Tools"
    """

    @staticmethod
    def recall(topic: str, context: Optional[str] = None) -> None:
        """Recall facts, knowledge, and observations (memory, not reasoning).

        Use to explicitly state what you know/remember before reasoning about it.
        Separates factual recall from logical inference.

        Args:
            topic: What to recall information about
            context: Optional observed facts from current situation

        Examples:
            topic="Python async patterns", context="Project uses FastAPI, has blocking DB calls"
            topic="Bug in auth.py line 45", context="Started after v2.0, affects 5% of users"
        """
        return

    @staticmethod
    def reason(
        content: str,
        reasoning_type: Optional[
            Literal["deductive", "inductive", "abductive", "analogical", "causal"]
        ] = None,
    ) -> None:
        """Perform logical reasoning and analysis.

        Use for: problem analysis, evaluating options, drawing conclusions, planning.
        Can include: understanding problems, examining solutions, making decisions.

        Args:
            content: Your reasoning process and conclusions
            reasoning_type: Optional type (deductive/inductive/abductive/analogical/causal)

        Examples:
            content="Auth fails after v2.0. New code has shared cache without locks.
                    Intermittent failures suggest race condition. Fix: add synchronization."
            reasoning_type="causal"
        """
        return

    @staticmethod
    def cognitive_operation(
        operation_type: str, content: str, metadata: Optional[str] = None
    ) -> None:
        """Custom cognitive operation for patterns not covered by recall/reason.

        Use when your thinking doesn't fit recall or reason. Provides extensibility
        for novel reasoning patterns while maintaining structure.

        Args:
            operation_type: Name of operation (e.g., "hypothesis_generation", "mental_simulation")
            content: The cognitive work being performed
            metadata: Optional context about why/how this operation is used

        Common operation types:
            - hypothesis_generation: Create multiple hypotheses to test
            - mental_simulation: Simulate execution/outcomes mentally
            - constraint_satisfaction: Work through constraints systematically
            - pattern_matching: Identify patterns in data/code
            - metacognitive_monitoring: Reflect on your reasoning process

        Example:
            operation_type="hypothesis_generation"
            content="H1: DB query issue (high likelihood), H2: Memory leak (medium), H3: Network (low)"
            metadata="Single-cause debugging failed, trying multiple hypotheses"
        """
        return

    @staticmethod
    def think(reasoning: str, facts: Optional[str] = None) -> None:
        """Legacy method (backward compatibility). Use recall() and reason() instead.

        Args:
            reasoning: Logical reasoning process
            facts: Optional factual information
        """
        return
