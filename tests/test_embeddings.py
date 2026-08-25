from app.embeddings import EMBEDDING_MODEL


def test_embedding_model_is_configured():
    assert EMBEDDING_MODEL == "text-embedding-3-small"