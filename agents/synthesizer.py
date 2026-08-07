from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import CodeReviewState
from schemas.report import FinalReport
from dotenv import load_dotenv
import os
import json

load_dotenv()

llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0
)


def synthesizer_node(state: CodeReviewState) -> dict:
    # Build a summary of all agent feedback to synthesize
    feedback_summary = []
    for fb in state.feedbacks:
        feedback_summary.append(
            f"Agent: {fb.agent_name}\n"
            f"Severity: {fb.severity}\n"
            f"Passed: {fb.passed}\n"
            f"Findings: {'; '.join(fb.findings) if fb.findings else 'None'}"
        )
    feedback_text = "\n\n".join(feedback_summary) if feedback_summary else "No feedback received from any agent."

    system_prompt = """You are a synthesizer that combines multiple specialist code review reports 
into one final, coherent report for a human developer to read.

Your job:
- Combine all findings into a clear summary
- Give an overall verdict on code quality
- Rank findings by real-world impact, not just by which agent found them
- Write in plain, direct language a developer can act on immediately

Respond ONLY with a valid JSON object in this exact format:
{
    "overall_verdict": "one or two sentence summary of code quality",
    "overall_severity": "low" or "medium" or "high",
    "approved": true or false,
    "summary_by_category": {
        "security": ["finding 1", "finding 2"],
        "performance": ["finding 1"],
        "style": ["finding 1"],
        "test_coverage": ["finding 1"]
    },
    "top_priority_fixes": ["most important fix 1", "most important fix 2"]
}

- approved is true only if overall_severity is low and no high-severity findings exist anywhere
- top_priority_fixes should contain at most 3 items, the most critical ones across all categories
- summary_by_category should only include categories that were actually reviewed
Do not include any text outside the JSON object."""

    human_prompt = f"""
Filename: {state.filename}
Language: {state.language}
Agents that ran: {', '.join(state.agents_to_run)}
Retry attempts: {state.retry_count}

All agent feedback:
{feedback_text}
"""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt)
    ])

    # Hallucination handling with Pydantic validation as final safety net
    try:
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        parsed = json.loads(raw.strip())

        # Validate against Pydantic schema — this is the strictest layer.
        # If the LLM's JSON doesn't match FinalReport's structure, this raises
        # and we fall into the except block below.
        validated_report = FinalReport(**parsed)
        final_report_dict = validated_report.model_dump()

    except Exception:
        # Build a safe fallback report directly from raw agent feedback,
        # bypassing the LLM entirely. This guarantees the user always gets
        # a usable report even if synthesis fails.
        by_category = {}
        highest_severity = "low"
        severity_rank = {"low": 0, "medium": 1, "high": 2}

        for fb in state.feedbacks:
            by_category[fb.agent_name] = fb.findings
            if severity_rank.get(fb.severity, 0) > severity_rank.get(highest_severity, 0):
                highest_severity = fb.severity

        approved = highest_severity == "low" and all(fb.passed for fb in state.feedbacks)

        final_report_dict = {
            "overall_verdict": "Automated synthesis failed — showing raw agent findings instead.",
            "overall_severity": highest_severity,
            "approved": approved,
            "summary_by_category": by_category,
            "top_priority_fixes": [
                f.findings[0] for f in state.feedbacks if f.findings
            ][:3]
        }

    return {"final_report": final_report_dict}