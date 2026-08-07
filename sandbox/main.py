from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from runner import run_code

app = FastAPI(title="Code Review Sandbox", version="1.0")


class ExecuteRequest(BaseModel):
    code: str
    language: str = "python"


class ExecuteResponse(BaseModel):
    success: bool
    stdout: str
    stderr: str
    timed_out: bool


@app.get("/health")
def health_check():
    """Used by Railway to verify the sandbox container is alive."""
    return {"status": "ok"}


@app.post("/run", response_model=ExecuteResponse)
def execute_code(request: ExecuteRequest):
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty.")

    if len(request.code) > 20000:
        raise HTTPException(status_code=400, detail="Code exceeds maximum length of 20000 characters.")

    result = run_code(request.code, request.language)
    return result