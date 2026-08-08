# Multi-Agent Code Review System

A multi-agent code review pipeline built with LangGraph, where specialized AI agents analyze code in parallel for security, performance, style, and test coverage — coordinated by a planner, evaluated by a critic, and combined into a single structured report by a synthesizer.

## How it works

1. **Planner** — decides which specialist agents should review the submitted code.
2. **Specialist agents** (run in parallel) — each combines a static analysis tool with an LLM review:
   - **Security** — Bandit static analysis + LLM review for vulnerabilities, hardcoded secrets, injection risks
   - **Performance** — Radon complexity analysis + LLM review for inefficiencies and bottlenecks
   - **Style** — AST-based structural analysis + LLM review for readability and naming
   - **Test Coverage** — LLM reasoning over missing edge cases and untested code paths
3. **Critic** — evaluates whether the specialist agents did a thorough enough job, and can trigger a retry round with more targeted focus if not (capped to prevent infinite loops).
4. **Synthesizer** — combines all findings into one final report with an overall verdict, severity rating, and prioritized fixes. Falls back to a raw-findings summary if structured synthesis fails, so a usable report is always returned.

## Tech stack

- **Orchestration:** LangGraph
- **LLM:** OpenAI (`gpt-4o-mini`)
- **Backend:** FastAPI
- **Frontend:** Streamlit
- **Static analysis:** Bandit (security), Radon (complexity), Python `ast` (structure)
- **Validation:** Pydantic
- **Containerization:** Docker, Docker Compose

## Project structure


code-review-agent/
├── agents/
│   ├── __init__.py
│   ├── critic.py
│   ├── performance.py
│   ├── planner.py
│   ├── security.py
│   ├── style.py
│   ├── synthesizer.py
│   └── test_coverage.py
├── api/
│   └── main.py
├── core/
│   ├── __init__.py
│   ├── config.py
│   ├── llm_client.py
│   └── logging_config.py
├── eval/
│   ├── __init__.py
│   ├── golden_dataset.py
│   └── run_eval.py
├── graph/
│   ├── __init__.py
│   ├── graph.py
│   └── state.py
├── sandbox/
│   ├── __init__.py
│   ├── Dockerfile
│   ├── main.py
│   └── runner.py
├── schemas/
│   ├── __init__.py
│   └── report.py
├── tools/
│   ├── __init__.py
│   ├── api_client.py
│   ├── ast_parser.py
│   ├── bandit_runner.py
│   ├── radon_runner.py
│   └── sandbox_client.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── unit/
│       ├── __init__.py
│       ├── test_ast_parser.py
│       ├── test_schemas.py
│       └── test_state.py
├── ui/
│   ├── __init__.py
│   ├── app.py
│   └── utils/
│       └── __init__.py
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile.api
├── Dockerfile.ui
├── LICENSE
├── README.md
└── requirements.txt


## Getting started

### Prerequisites
- Python 3.11+
- An OpenAI API key
- Docker & Docker Compose (optional, for containerized setup)

### Local setup

```bash
python -m venv venv
source venv/Scripts/activate  # or venv/bin/activate on macOS/Linux
pip install -r requirements.txt
cp .env.example .env  # then add your OPENAI_API_KEY
```

### Running the API

```bash
uvicorn api.main:app --reload --port 8080
```

```bash
curl -X POST http://localhost:8080/review \
  -H "Content-Type: application/json" \
  -d '{"code": "def add(a, b):\n    return a + b"}'
```

### Running the UI

```bash
streamlit run ui/app.py
```

### Running with Docker Compose

```bash
docker compose up --build
```

Starts the API, UI, and sandbox services together.

## Testing

```bash
pytest tests/ -v
```

Unit tests cover state management, report schema validation, and the AST analysis tool.

## Evaluation

```bash
python -m eval.run_eval
```

Runs the full pipeline against a small golden dataset of known code samples (SQL injection, hardcoded secrets, performance issues, missing documentation, and clean code) and checks whether each specialist agent correctly identifies the expected issues.

## Current scope and roadmap

- Supports Python code review end to end; static analysis tools (Bandit, Radon, AST parsing) are Python-specific, so non-Python input relies on LLM judgment alone.
- The `sandbox/` service can safely execute submitted code but is not yet connected to the review pipeline.
- Test and evaluation coverage currently focuses on deterministic logic and end-to-end agent accuracy; direct unit tests for individual agent functions are a planned addition.

## License

See [LICENSE](./LICENSE).