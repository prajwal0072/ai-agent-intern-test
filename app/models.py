from dataclasses import dataclass, field
from typing import Any


@dataclass
class Document:
    document_id: str
    title: str
    status: str
    effective_date: str | None
    last_reviewed: str | None
    audience: str | None
    policy_authority: str | None
    filename: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Chunk:
    text: str
    filename: str
    document_id: str
    title: str
    heading: str
    metadata: dict[str, Any] = field(default_factory=dict)