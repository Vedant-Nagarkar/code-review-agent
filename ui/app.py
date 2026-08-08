from core.config import settings
import streamlit as st
import sys
import os

# Allow imports from project root when running via streamlit
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.api_client import run_review

st.set_page_config(page_title="Code Review Agent", layout="wide")

st.title("Multi-Agent Code Review System")
st.caption("Security, Performance, Style, and Test Coverage analysis powered by LangGraph")

with st.sidebar:
    st.header("Input")
    filename = st.text_input("Filename", value="example.py")
    language = st.selectbox("Language", ["python"], index=0)
    st.caption("Currently Python-only — see README for scope notes.")

code_input = st.text_area(
    "Paste your code here",
    height=300,
    placeholder="def add(a, b):\n    return a + b"
)


run_button = st.button("Run Review", type="primary")

if run_button:
    if not code_input.strip():
        st.error("Please paste some code before running the review.")
    elif len(code_input) > settings.max_code_length:
        st.error(f"Code exceeds maximum length of {settings.max_code_length} characters.")
    else:
        with st.spinner("Running multi-agent review..."):
                try:
                    result = run_review(code_input, language, filename)
                    if "error" in result:
                        st.error(result["error"])
                        st.stop()
                except Exception as e:
                    st.error(f"Review failed: {str(e)}")
                st.stop()

        report = result.get("final_report", {})

        if not report:
            st.error("No report was generated. Check logs for details.")
            st.stop()

        # Overall verdict section
        st.divider()
        col1, col2 = st.columns([3, 1])

        with col1:
            st.subheader("Verdict")
            st.write(report.get("overall_verdict", "No verdict available."))

        with col2:
            approved = report.get("approved", False)
            severity = report.get("overall_severity", "unknown")

            if approved:
                st.success(f"APPROVED\nSeverity: {severity}")
            else:
                st.error(f"CHANGES NEEDED\nSeverity: {severity}")

        # Top priority fixes
        top_fixes = report.get("top_priority_fixes", [])
        if top_fixes:
            st.subheader("Top Priority Fixes")
            for i, fix in enumerate(top_fixes, 1):
                st.write(f"{i}. {fix}")

        # Category breakdown
        st.divider()
        st.subheader("Detailed Findings by Category")

        summary = report.get("summary_by_category", {})
        category_labels = {
            "security": "Security",
            "performance": "Performance",
            "style": "Style",
            "test_coverage": "Test Coverage"
        }

        cols = st.columns(len(summary)) if summary else []
        for idx, (category, findings) in enumerate(summary.items()):
            with cols[idx]:
                st.markdown(f"**{category_labels.get(category, category)}**")
                if findings:
                    for finding in findings:
                        st.write(f"- {finding}")
                else:
                    st.write("No issues found.")

        # Debug info — retry transparency
        with st.expander("Debug: Agent Execution Details"):
            st.write(f"Retry attempts: {result.get('retry_count', 0)}")
            st.write(f"Agents run: {', '.join(result.get('agents_to_run', []))}")
            st.json(report)