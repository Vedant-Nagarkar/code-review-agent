from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import CodeReviewState, AgentFeedback
from tools.ast_parser import run_ast_parser
from dotenv import load_dotenv
import os
import json

load_dotenv()

llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0
)


def style_node(state: CodeReviewState) -> dict:
    # Skip if planner didn't select this agent
    if "style" not in state.agents_to_run:
        return {"feedbacks": []}

    # Run AST parser to get code structure metrics
    ast_output = run_ast_parser(state.code, state.language)

    system_prompt = """You are a code style reviewer. Your job is to identify style and readability issues in code.

You will be given:
1. The code to review
2. Output from an AST parser showing code structure metrics

Focus on:
- Unclear or misleading variable and function names
- Functions that are too long or do too many things
- Missing or inadequate docstrings and comments
- Inconsistent naming conventions (mixing camelCase and snake_case)
- Deep nesting that hurts readability
- Magic numbers and hardcoded values without explanation
- Dead code or unused variables
- Poor separation of concerns

Respond ONLY with a valid JSON object in this exact format:
{
    "findings": ["finding 1", "finding 2"],
    "severity": "low" or "medium" or "high",
    "passed": true or false
}

- passed is true only if there are zero style issues
- severity is the highest severity level found
- findings is a list of specific issues found, empty list if none
Do not include any text outside the JSON object."""

    human_prompt = f"""
Language: {state.language}
Filename: {state.filename}

AST Parser Output:
{ast_output}

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
        findings = ["Style analysis failed to parse — manual review recommended"]
        severity = "low"
        passed = False

    feedback = AgentFeedback(
        agent_name="style",
        findings=findings,
        severity=severity,
        passed=passed
    )

    return {"feedbacks": [feedback]}