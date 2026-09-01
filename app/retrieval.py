import re
from dataclasses import dataclass

from app.ingestion import create_chunks
from app.models import Chunk


@dataclass
class RetrievalResult:
    chunk: Chunk
    score: float


@dataclass
class RetrievalResponse:
    results: list[RetrievalResult]
    conflict_detected: bool


STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "be",
    "can",
    "do",
    "does",
    "for",
    "how",
    "i",
    "in",
    "is",
    "it",
    "me",
    "of",
    "on",
    "the",
    "to",
    "what",
    "when",
    "where",
    "with",
}


def tokenize(text: str) -> list[str]:
    """
    Normalize text into searchable tokens.
    """

    tokens = re.findall(r"[a-z0-9]+", text.lower())

    return [
        token
        for token in tokens
        if token not in STOP_WORDS
    ]


def document_priority(chunk: Chunk) -> float:
    """
    Assign authority based on document metadata.

    Higher score = more trustworthy for customer-facing answers.
    """

    metadata = chunk.metadata

    status = str(
        metadata.get("status", "")
    ).lower()

    authority = str(
        metadata.get("policy_authority", "")
    ).lower()

    audience = str(
        metadata.get("audience", "")
    ).lower()

    score = 0.0

    # Document lifecycle
    if status == "active":
        score += 5.0

    elif status == "superseded":
        score -= 5.0

    elif status == "draft":
        score -= 3.0

    # Authority
    if authority == "official":
        score += 3.0

    elif authority == "none":
        score -= 3.0

    # Audience
    if audience == "customer":
        score += 1.0

    elif audience == "internal":
        score -= 3.0

    return score


def lexical_score(
    query: str,
    chunk: Chunk,
) -> float:
    """
    Calculate basic lexical relevance.

    Heading matches receive extra weight because headings
    are strong indicators of what a section discusses.
    """

    query_tokens = set(
        tokenize(query)
    )

    if not query_tokens:
        return 0.0

    text_tokens = set(
        tokenize(chunk.text)
    )

    heading_tokens = set(
        tokenize(chunk.heading)
    )

    title_tokens = set(
        tokenize(chunk.title)
    )

    text_matches = len(
        query_tokens & text_tokens
    )

    heading_matches = len(
        query_tokens & heading_tokens
    )

    title_matches = len(
        query_tokens & title_tokens
    )

    return (
        text_matches
        + heading_matches * 3.0
        + title_matches * 1.5
    )


def score_chunk(
    query: str,
    chunk: Chunk,
) -> float:

    relevance = lexical_score(
        query,
        chunk,
    )

    authority = document_priority(
        chunk
    )

    return relevance + authority


class Retriever:

    def __init__(self):
        self.chunks = create_chunks()

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[RetrievalResult]:

        results = []

        for chunk in self.chunks:

            score = score_chunk(
                query,
                chunk,
            )

            if score > 0:

                results.append(
                    RetrievalResult(
                        chunk=chunk,
                        score=score,
                    )
                )

        results.sort(
            key=lambda result: result.score,
            reverse=True,
        )

        return results[:top_k]

    def search_with_conflict_detection(
        self,
        query: str,
        top_k: int = 8,
    ) -> RetrievalResponse:

        """
        Retrieve relevant chunks and determine whether
        multiple documents discuss the same topic.

        We deliberately keep superseded documents available
        so they can be detected during retrieval, rather
        than deleting them from the knowledge base.
        """

        results = self.search(
            query,
            top_k=top_k,
        )

        document_ids = {
            result.chunk.document_id
            for result in results
        }

        conflict_detected = (
            len(document_ids) > 1
        )

        return RetrievalResponse(
            results=results,
            conflict_detected=conflict_detected,
        )