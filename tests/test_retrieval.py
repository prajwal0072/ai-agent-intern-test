from app.retrieval import Retriever


def test_current_returns_policy_beats_legacy_policy():
    retriever = Retriever()

    results = retriever.search(
        "How long can I return an unused backpack?"
    )

    assert results

    filenames = [
        result.chunk.filename
        for result in results
    ]

    assert "01-returns-policy-current.md" in filenames


def test_return_window_retrieves_correct_heading():
    retriever = Retriever()

    results = retriever.search(
        "What is the standard return window?"
    )

    assert results

    top = results[0].chunk

    assert top.filename == "01-returns-policy-current.md"
    assert top.heading == "Standard return window"


def test_superseded_policy_has_lower_priority():
    retriever = Retriever()

    results = retriever.search(
        "return window 45 days",
        top_k=len(retriever.chunks),
    )

    current_results = [
        result
        for result in results
        if result.chunk.filename
        == "01-returns-policy-current.md"
    ]

    legacy_results = [
        result
        for result in results
        if result.chunk.filename
        == "02-returns-policy-legacy.md"
    ]

    assert legacy_results

    if current_results:
        assert (
            current_results[0].score
            > legacy_results[0].score
        )


def test_conflict_detection_returns_multiple_sources():
    retriever = Retriever()

    response = retriever.search_with_conflict_detection(
        "What is the return window?"
    )

    assert response.results

    filenames = {
        result.chunk.filename
        for result in response.results
    }

    assert "01-returns-policy-current.md" in filenames


def test_retrieval_preserves_document_metadata():
    retriever = Retriever()

    results = retriever.search(
        "return policy"
    )

    assert results

    chunk = results[0].chunk

    assert chunk.filename
    assert chunk.document_id
    assert chunk.heading
    assert chunk.metadata