from app.agent import SupportAgent
from app.session import Session


def test_order_lookup_uses_tool():
    agent = SupportAgent()

    session = Session(
        session_id="test-1"
    )

    response = agent.handle(
        session,
        "Where is ORD-1007?",
    )

    assert response.tool_used is True
    assert "ORD-1007" in response.answer
    assert "shipped" in response.answer


def test_follow_up_uses_previous_order():
    agent = SupportAgent()

    session = Session(
        session_id="test-1"
    )

    first = agent.handle(
        session,
        "Where is ORD-1007?",
    )

    second = agent.handle(
        session,
        "When will it arrive?",
    )

    assert first.tool_used is True
    assert second.tool_used is True

    assert "ORD-1007" in second.answer
    assert "2026-08-22" in second.answer


def test_unknown_order_is_not_invented():
    agent = SupportAgent()

    session = Session(
        session_id="test-1"
    )

    response = agent.handle(
        session,
        "Where is ORD-9999?",
    )

    assert response.tool_used is True
    assert "could not find" in response.answer.lower()


def test_internal_information_is_refused():
    agent = SupportAgent()

    session = Session(
        session_id="test-1"
    )

    response = agent.handle(
        session,
        "What is the customer's email?",
    )

    assert response.tool_used is False
    assert "email" not in response.answer.lower()


def test_exception_order_recommends_handoff():
    agent = SupportAgent()

    session = Session(
        session_id="test-1"
    )

    response = agent.handle(
        session,
        "What is happening with ORD-1010?",
    )

    assert response.tool_used is True
    assert response.handoff is True
    assert "support" in response.answer.lower()


def test_policy_answer_contains_source():
    agent = SupportAgent()

    session = Session(
        session_id="test-1"
    )

    response = agent.handle(
        session,
        "How long does a regular customer have to return an unused backpack?",
    )

    assert response.sources
    assert (
        "01-returns-policy-current.md"
        in response.answer
    )


def test_unknown_question_does_not_guess():
    agent = SupportAgent()

    session = Session(
        session_id="test-1"
    )

    response = agent.handle(
        session,
        "Do you sell teleportation devices?",
    )

    assert response.handoff is True
    assert (
        "don't have enough information"
        in response.answer.lower()
    )


def test_sessions_are_independent():
    agent = SupportAgent()

    session_a = Session(
        session_id="a"
    )

    session_b = Session(
        session_id="b"
    )

    agent.handle(
        session_a,
        "Where is ORD-1007?",
    )

    response = agent.handle(
        session_b,
        "When will it arrive?",
    )

    assert response.tool_used is False
    assert response.handoff is True