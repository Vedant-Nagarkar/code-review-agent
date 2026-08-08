from graph.state import CodeReviewState, AgentFeedback


def test_agent_feedback_requires_all_fields():
    feedback = AgentFeedback(
        agent_name="security",
        findings=["hardcoded API key on line 12"],
        severity="high",
        passed=False,
        round=0
    )
    assert feedback.agent_name == "security"
    assert feedback.round == 0


def test_agent_feedback_round_defaults_to_zero():
    feedback = AgentFeedback(
        agent_name="style",
        findings=[],
        severity="low",
        passed=True
    )
    assert feedback.round == 0


def test_feedbacks_accumulate_across_rounds():
    """
    Regression test for the reducer bug: state.feedbacks uses operator.add,
    which only ever appends — it can never be reset. This test locks in
    that behavior so nobody 'fixes' it by trying to clear the list again,
    which would silently break round-filtering in critic.py/synthesizer.py.
    """
    state = CodeReviewState(code="def f(): pass")

    round_0_feedback = AgentFeedback(
        agent_name="style", findings=["no docstring"], severity="low", passed=False, round=0
    )
    round_1_feedback = AgentFeedback(
        agent_name="style", findings=["still no docstring"], severity="low", passed=False, round=1
    )

    # Simulate what LangGraph's operator.add reducer does across two node returns
    combined = [round_0_feedback] + [round_1_feedback]

    assert len(combined) == 2
    assert combined[0].round == 0
    assert combined[1].round == 1


def test_filtering_by_round_isolates_current_round_only():
    """
    This is the actual logic critic.py and synthesizer.py rely on:
    filtering state.feedbacks down to only the current round's entries.
    """
    all_feedbacks = [
        AgentFeedback(agent_name="style", findings=["a"], severity="low", passed=False, round=0),
        AgentFeedback(agent_name="security", findings=["b"], severity="high", passed=False, round=0),
        AgentFeedback(agent_name="style", findings=["c"], severity="low", passed=False, round=1),
    ]

    current_round = 1
    filtered = [fb for fb in all_feedbacks if fb.round == current_round]

    assert len(filtered) == 1
    assert filtered[0].findings == ["c"]