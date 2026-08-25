from dataclasses import dataclass, field
from typing import Any


@dataclass
class Message:
    role: str
    content: str


@dataclass
class Session:
    session_id: str
    messages: list[Message] = field(default_factory=list)

    # Relevant state that can be carried across turns.
    current_order_id: str | None = None
    current_topic: str | None = None

    def add_message(
        self,
        role: str,
        content: str,
    ) -> None:
        self.messages.append(
            Message(
                role=role,
                content=content,
            )
        )

    def set_order_id(
        self,
        order_id: str,
    ) -> None:
        self.current_order_id = order_id

    def set_topic(
        self,
        topic: str,
    ) -> None:
        self.current_topic = topic

    def recent_messages(
        self,
        limit: int = 6,
    ) -> list[Message]:
        """
        Return only recent conversation history.

        We don't need to send an unlimited conversation
        to the model.
        """

        return self.messages[-limit:]


class SessionManager:

    def __init__(self):
        self.sessions: dict[str, Session] = {}

    def get_or_create(
        self,
        session_id: str,
    ) -> Session:

        if session_id not in self.sessions:

            self.sessions[session_id] = Session(
                session_id=session_id,
            )

        return self.sessions[session_id]

    def delete(
        self,
        session_id: str,
    ) -> None:

        self.sessions.pop(
            session_id,
            None,
        )