from app.ingestion import load_documents, create_chunks


def test_loads_all_knowledge_base_documents():
    documents = load_documents()

    assert len(documents) == 14


def test_current_returns_policy_metadata():
    documents = load_documents()

    current = next(
        doc
        for doc in documents
        if doc.filename == "01-returns-policy-current.md"
    )

    assert current.document_id == "RET-2026-01"
    assert current.status == "active"
    assert current.policy_authority == "official"


def test_legacy_returns_policy_is_superseded():
    documents = load_documents()

    legacy = next(
        doc
        for doc in documents
        if doc.filename == "02-returns-policy-legacy.md"
    )

    assert legacy.document_id == "RET-2024-01"
    assert legacy.status == "superseded"


def test_returns_policy_sections_are_preserved():
    chunks = create_chunks()

    current = [
        chunk
        for chunk in chunks
        if chunk.filename == "01-returns-policy-current.md"
    ]

    headings = {chunk.heading for chunk in current}

    assert "Standard return window" in headings
    assert "Item condition" in headings
    assert "Return shipping and refunds" in headings
    assert "Exclusions and exceptions" in headings