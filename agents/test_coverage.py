from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import CodeReviewState, AgentFeedback
from dotenv import load_dotenv
import os
import json

load_dotenv()

llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0
)


def test_coverage_node(state: CodeReviewState) -> dict:
    # Skip if planner didn't select this agent
    if "test_coverage" not in state.agents_to_run:
        return {"feedbacks": []}

    # No external tool here — this agent has no runnable test suite to analyze,
    # since the input is a single code snippet, not a project with existing tests.
    # The LLM reasons purely from reading the code and imagining what could break.

    system_prompt = """You are a test coverage reviewer. Your job is to identify what test cases 
are missing for the given code, based on reading the code alone (no existing test suite is provided).

Focus on:
- Edge cases not handled (empty input, None, zero, negative numbers)
- Error conditions that aren't tested (invalid types, missing keys, exceptions)
- Boundary conditions (off-by-one risks, first/last element handling)
- Missing tests for each distinct code path (if/else branches, loops)
- Untested external dependencies (API calls, file I/O, database calls)

Respond ONLY with a valid JSON object in this exact format:
{
    "findings": ["finding 1", "finding 2"],
    "severity": "low" or "medium" or "high",
    "passed": true or false
}

- passed is true only if the code has no significant untested risk areas
- severity is the highest severity level found
- findings is a list of specific missing test cases, empty list if none
Do not include any text outside the JSON object."""

    human_prompt = f"""
Language: {state.language}
Filename: {state.filename}

Code to review:
```{state.language}
{state.code}
```

Note: no existing test file was provided. Base your analysis on what tests SHOULD exist for this code.
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
        findings = ["Test coverage analysis failed to parse — manual review recommended"]
        severity = "low"
        passed = False

    feedback = AgentFeedback(
        agent_name="test_coverage",
        findings=findings,
        severity=severity,
        passed=passed
    )

    return {"feedbacks": [feedback]}