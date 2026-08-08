import pytest
from pydantic import ValidationError
from schemas.report import FinalReport


def test_valid_report_passes():
    report = FinalReport(
        overall_verdict="Code is clean, no significant issues.",
        overall_severity="low",
        approved=True,
        summary_by_category={"style": []},
        top_priority_fixes=[]
    )
    assert report.approved is True
    assert report.overall_severity == "low"


def test_invalid_severity_string_rejected():
    with pytest.raises(ValidationError):
        FinalReport(
            overall_verdict="Something",
            overall_severity="critical",  # not one of low/medium/high
            approved=False,
            summary_by_category={},
            top_priority_fixes=[]
        )


def test_more_than_three_top_priority_fixes_rejected():
    with pytest.raises(ValidationError):
        FinalReport(
            overall_verdict="Something",
            overall_severity="high",
            approved=False,
            summary_by_category={},
            top_priority_fixes=["fix1", "fix2", "fix3", "fix4"]  # 4 items, max is 3
        )


def test_summary_by_category_defaults_to_empty_dict():
    report = FinalReport(
        overall_verdict="Nothing to report",
        overall_severity="low",
        approved=True
    )
    assert report.summary_by_category == {}
    assert report.top_priority_fixes == []