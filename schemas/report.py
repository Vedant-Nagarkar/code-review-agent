from pydantic import BaseModel, Field


class FinalReport(BaseModel):
    overall_verdict: str
    overall_severity: str = Field(pattern="^(low|medium|high)$")
    approved: bool
    summary_by_category: dict[str, list[str]] = {}
    top_priority_fixes: list[str] = Field(default=[], max_length=3)