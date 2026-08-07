from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import CodeReviewState
from dotenv import load_dotenv
import os
import json

load_dotenv()

llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0
)

MAX_RETRIES = 2


def critic_node(state: CodeReviewState) -> dict:
    # Build a summary of all agent feedback for the critic to evaluate
    feedback_summary = []
    for fb in state.feedbacks:
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

Flag for retry ONLY if:
- An agent's findings list is suspiciously empty for clearly complex or risky code
- An agent's findings are too vague to be actionable (e.g. "code has issues" with no specifics)
- There's a contradiction between agents (e.g. security says passed=true but findings list is non-empty)
- Multiple agents failed to parse (findings mention "failed to parse")

Do NOT flag for retry just because issues were found — finding issues is the system working correctly.

Respond ONLY with a valid JSON object in this exact format:
{
    "needs_retry": true or false,
    "retry_notes": "specific instructions for what agents should focus on if retrying, empty string if no retry"
}

Do not include any text outside the JSON object."""

    human_prompt = f"""
Current retry count: {state.retry_count}
Max retries allowed: {MAX_RETRIES}

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

    return {
        "needs_retry": needs_retry,
        "retry_notes": retry_notes,
        "retry_count": state.retry_count + 1 if needs_retry else state.retry_count
    }


def should_retry(state: CodeReviewState) -> str:
    """Conditional edge function — determines next node after critic."""
    if state.needs_retry:
        return "retry"
    return "done"