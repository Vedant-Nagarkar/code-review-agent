from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import CodeReviewState
from core.llm_client import get_llm
from core.logging_config import log_node
import json


llm = get_llm()

MAX_RETRIES = 2


@log_node("critic")
def critic_node(state: CodeReviewState) -> dict:
    current_round_feedbacks = [fb for fb in state.feedbacks if fb.round == state.retry_count]

    # Build a summary of all agent feedback for the critic to evaluate
    feedback_summary = []
    for fb in current_round_feedbacks:
        feedback_summary.append(
            f"Agent: {fb.agent_name}\n"
            f"Severity: {fb.severity}\n"
            f"Passed: {fb.passed}\n"
            f"Findings: {'; '.join(fb.findings) if fb.findings else 'None'}"
        )
    feedback_text = "\n\n".join(feedback_summary) if feedback_summary else "No feedback received from any agent."

    system_prompt = """You are a critic reviewing the output quality of a multi-agent code review system.

Your job is NOT to review the code itself. Your job is to judge whether the AGENTS did a 
thorough enough job reviewing it.

Each agent only reviews its own domain. Empty findings from one agent are NEVER a problem 
caused by another agent having findings. Example:

Security: 2 findings, high severity
Performance: 0 findings, low severity
Style: 3 findings, high severity

This is CORRECT and should NOT trigger a retry. A short function with no loops or complexity 
simply has no performance issues to find — that's a valid result, not a failure. Do not 
reference one agent's findings when judging whether another agent's findings are sufficient.

Flag for retry ONLY if, within a SINGLE agent's own output:
- That agent's findings list is vague or unactionable (e.g. "code has issues" with no specifics)
- That agent's passed=true but its own findings list is non-empty (internal contradiction)
- That agent's findings mention "failed to parse"

Do NOT flag for retry just because issues were found — finding issues is the system working correctly.
Do NOT compare agents against each other. Judge each agent only against its own output.
Do NOT flag for retry if a previous round already covered the same ground and 
findings are substantively unchanged — retrying will not improve output that 
depends only on the code itself, not on agent effort. If the code hasn't 
changed between rounds, additional retries cannot surface new information.

Respond ONLY with a valid JSON object in this exact format:
{
    "needs_retry": true or false,
    "retry_notes": "specific instructions for what agents should focus on if retrying, empty string if no retry"
}

Do not include any text outside the JSON object."""
    previous_round_feedbacks = [fb for fb in state.feedbacks if fb.round == state.retry_count - 1]
    previous_round_summary = "\n".join(
        f"{fb.agent_name}: {len(fb.findings)} findings" for fb in previous_round_feedbacks
) if previous_round_feedbacks else "N/A (this is the first round)"
    human_prompt = f"""
Current retry count: {state.retry_count}
Max retries allowed: {MAX_RETRIES}
    
Previous round's findings summary (for comparison):
{previous_round_summary}

Agent feedback to evaluate:
{feedback_text}
"""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt)
    ])

    # Hallucination handling
    try:
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        parsed = json.loads(raw.strip())

        needs_retry = parsed.get("needs_retry", False)
        if not isinstance(needs_retry, bool):
            needs_retry = False

        retry_notes = parsed.get("retry_notes", "")
        if not isinstance(retry_notes, str):
            retry_notes = ""

    except Exception:
        # If critic itself fails to parse, default to NOT retrying
        # (fail-safe: don't loop forever on a broken critic)
        needs_retry = False
        retry_notes = ""

    # Hard cap — never allow infinite retry loops regardless of what LLM says
    if state.retry_count >= MAX_RETRIES:
        needs_retry = False

    forced_retry = state.retry_count == 0

    return {
        "needs_retry":  needs_retry ,
        "retry_notes": retry_notes,
        "retry_count": state.retry_count + 1 if needs_retry else state.retry_count
    }


def should_retry(state: CodeReviewState) -> str:
    """Conditional edge function — determines next node after critic."""
    if state.needs_retry:
        return "retry"
    return "done"