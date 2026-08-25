import os

from openai import OpenAI


EMBEDDING_MODEL = "text-embedding-3-small"


def get_client():
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return None

    return OpenAI(api_key=api_key)


def create_embedding(text: str) -> list[float]:
    """
    Create an OpenAI embedding.

    This function is only called when real semantic
    retrieval is enabled.
    """

    client = get_client()

    if client is None:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured."
        )

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
    )

    return response.data[0].embedding