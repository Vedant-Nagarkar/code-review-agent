from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import CodeReviewState, AgentFeedback
from tools.bandit_runner import run_bandit
from core.llm_client import get_llm
from core.logging_config import log_node
import json

llm = get_llm()

@log_node("security")
def security_node(state: CodeReviewState) -> dict:
    # Skip if planner didn't select this agent
    if "security" not in state.agents_to_run:
        return {"feedbacks": []}

    # Run static analysis tool first
    bandit_output = run_bandit(state.code, state.language)

    system_prompt = """You are a security code reviewer. Your job is to identify security vulnerabilities in code.

You will be given:
1. The code to review
2. Output from Bandit (a static security analysis tool)

Focus on:
- SQL injection, XSS, command injection risks
- Hardcoded secrets, API keys, passwords
- Insecure use of eval(), exec(), pickle
- Missing input validation
- Insecure random number generation
- Path traversal vulnerabilities

Respond ONLY with a valid JSON object in this exact format:
{
    "findings": ["finding 1", "finding 2"],
    "severity": "low" or "medium" or "high",
    "passed": true or false
}

- passed is true only if there are zero security issues
- severity is the highest severity level found
- findings is a list of specific issues found, empty list if none
Do not include any text outside the JSON object."""

    human_prompt = f"""
Language: {state.language}
Filename: {state.filename}

Bandit Static Analysis Output:
{bandit_output}

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

        import json
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
        findings = ["Security analysis failed to parse — manual review recommended"]
        severity = "medium"
        passed = False

    feedback = AgentFeedback(
        agent_name="security",
        findings=findings,
        severity=severity,
        passed=passed,
        round=state.retry_count

    )


    return {"feedbacks": [feedback]}