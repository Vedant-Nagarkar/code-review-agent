from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import CodeReviewState, AgentFeedback
from tools.radon_runner import run_radon
from core.llm_client import get_llm
from core.logging_config import log_node
import json

llm = get_llm()

@log_node("performance")
def performance_node(state: CodeReviewState) -> dict:
    # Skip if planner didn't select this agent
    if "performance" not in state.agents_to_run:
        return {"feedbacks": []}

    # Run complexity analysis tool first
    radon_output = run_radon(state.code, state.language)

    system_prompt = """You are a performance code reviewer. Your job is to identify performance issues in code.

You will be given:
1. The code to review
2. Output from Radon (a code complexity analysis tool)

Focus on:
- High cyclomatic complexity functions
- Nested loops with high time complexity
- Repeated database or API calls inside loops
- Unnecessary recomputation inside loops
- Memory inefficiencies (loading entire files, huge lists)
- Missing caching where beneficial
- Inefficient data structures for the use case

Respond ONLY with a valid JSON object in this exact format:
{
    "findings": ["finding 1", "finding 2"],
    "severity": "low" or "medium" or "high",
    "passed": true or false
}

- passed is true only if there are zero performance issues
- severity is the highest severity level found
- findings is a list of specific issues found, empty list if none
Do not include any text outside the JSON object."""

    human_prompt = f"""
Language: {state.language}
Filename: {state.filename}

Radon Complexity Analysis Output:
{radon_output}

Code to review:
```{state.language}
{state.code}
```
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

        valid_severities = {"low", "medium", "high"}
        severity = parsed.get("severity", "low")
        if severity not in valid_severities:
            severity = "low"

        findings = parsed.get("findings", [])
        if not isinstance(findings, list):
            findings = [str(findings)]

        passed = parsed.get("passed", len(findings) == 0)
        if not isinstance(passed, bool):
            passed = len(findings) == 0

    except Exception:
        findings = ["Performance analysis failed to parse — manual review recommended"]
        severity = "medium"
        passed = False

    feedback = AgentFeedback(
        agent_name="performance",
        findings=findings,
        severity=severity,
        passed=passed,
        round=state.retry_count

    )


    return {"feedbacks": [feedback]}