from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from graph.graph import review_graph
from core.config import settings
from core.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger("api")

app = FastAPI(title="Code Review Agent", version="1.0")


class ReviewRequest(BaseModel):
    code: str
    language: str = "python"
    filename: str = "unnamed.py"


class ReviewResponse(BaseModel):
    final_report: dict
    retry_count: int
    agents_run: list[str]


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/review", response_model=ReviewResponse)
def run_review(request: ReviewRequest):
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty.")

    if len(request.code) > settings.max_code_length:
        raise HTTPException(
            status_code=400,
            detail=f"Code exceeds maximum length of {settings.max_code_length} characters."
        )

    try:
        result = review_graph.invoke({
            "code": request.code,
            "language": request.language,
            "filename": request.filename
        })
    except Exception as e:
        logger.exception("review_graph invocation failed")
        raise HTTPException(status_code=500, detail="Review failed — check server logs.")

    return {
        "final_report": result.get("final_report", {}),
        "retry_count": result.get("retry_count", 0),
        "agents_run": result.get("agents_to_run", [])
    }