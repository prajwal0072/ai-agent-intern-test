from app.session import SessionManager


def test_session_is_created():
    manager = SessionManager()

    session = manager.get_or_create("session-1")

    assert session.session_id == "session-1"


def test_same_session_is_reused():
    manager = SessionManager()

    first = manager.get_or_create("session-1")
    second = manager.get_or_create("session-1")

    assert first is second


def test_different_sessions_are_isolated():
    manager = SessionManager()

    first = manager.get_or_create("session-1")
    second = manager.get_or_create("session-2")

    first.set_order_id("ORD-1007")

    assert first.current_order_id == "ORD-1007"
    assert second.current_order_id is None


def test_session_remembers_order():
    manager = SessionManager()

    session = manager.get_or_create("session-1")

    session.set_order_id("ORD-1007")

    assert session.current_order_id == "ORD-1007"


def test_session_remembers_topic():
    manager = SessionManager()

    session = manager.get_or_create("session-1")

    session.set_topic(
        "international_shipping"
    )

    assert (
        session.current_topic
        == "international_shipping"
    )


def test_recent_messages_are_limited():
    manager = SessionManager()

    session = manager.get_or_create("session-1")

    for i in range(10):
        session.add_message(
            "user",
            f"message {i}",
        )

    messages = session.recent_messages(
        limit=6
    )

    assert len(messages) == 6
    assert messages[0].content == "message 4"
    assert messages[-1].content == "message 9"


def test_delete_session():
    manager = SessionManager()

    manager.get_or_create("session-1")

    manager.delete("session-1")

    assert "session-1" not in manager.sessions