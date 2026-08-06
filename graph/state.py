from typing import Annotated, Any
from pydantic import BaseModel
import operator


class AgentFeedback(BaseModel):
    agent_name: str
    findings: list[str]
    severity: str  # "low", "medium", "high"
    passed: bool


class CodeReviewState(BaseModel):
    # Input
    code: str
    language: str = "python"
    filename: str = "unnamed.py"

    # Planner output
    agents_to_run: list[str] = []

    # Each specialist agent writes its feedback here
    feedbacks: Annotated[list[AgentFeedback], operator.add] = []

    # Critic decision
    needs_retry: bool = False
    retry_count: int = 0
    retry_notes: str = ""

    # Final output
    final_report: dict[str, Any] = {}