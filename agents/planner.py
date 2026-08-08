from graph.state import CodeReviewState
from langchain_core.messages import SystemMessage, HumanMessage
from core.llm_client import get_llm
from core.logging_config import log_node
import json

llm = get_llm()


@log_node("planner")
def planner_node(state: CodeReviewState) -> dict:
    # If this is a retry, use critic's notes to guide replanning
    retry_context = ""
    if state.retry_count > 0:
        retry_context = f"""
This is retry attempt {state.retry_count}.
Critic feedback from previous attempt: {state.retry_notes}
Focus the agents on addressing the critic's concerns.
"""

    system_prompt = """You are a code review planner. Your job is to decide which specialist agents 
should review the given code. 

Available agents:
- security: checks for vulnerabilities, injection risks, hardcoded secrets
- performance: checks for complexity, inefficient patterns, bottlenecks  
- style: checks for formatting, naming conventions, code clarity
- test_coverage: checks for missing tests, untested edge cases

Respond ONLY with a valid JSON object in this exact format:
{
    "agents_to_run": ["security", "performance", "style", "test_coverage"],
    "reasoning": "brief explanation of why these agents were selected"
}

Always include all 4 agents unless the code is trivially simple.
Do not include any text outside the JSON object."""

    human_prompt = f"""
Language: {state.language}
Filename: {state.filename}
{retry_context}

Code to review:
```{state.language}
{state.code}
```
"""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt)
    ])

    # Hallucination handling — validate the response is proper JSON
    try:
        raw = response.content.strip()
        # Strip markdown code fences if model adds them
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = json.loads(raw.strip())

        # Validate agents_to_run only contains known agents
        valid_agents = {"security", "performance", "style", "test_coverage"}
        agents = [a for a in parsed.get("agents_to_run", []) if a in valid_agents]

        # Fallback: if model returns empty list, run all agents
        if not agents:
            agents = list(valid_agents)

    except (json.JSONDecodeError, KeyError):
        # If parsing fails entirely, default to all agents
        agents = ["security", "performance", "style", "test_coverage"]


    return {
        "agents_to_run": agents,
    }