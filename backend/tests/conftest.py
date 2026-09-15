import pytest
from langchain_core.embeddings import DeterministicFakeEmbedding

from app.core.config import get_settings
from app.core.models import TranscriptSegment
from app.rag import vector_store


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path, monkeypatch):
    """Each test gets its own Qdrant directory, transcript cache and fake embeddings."""
    monkeypatch.setenv("QDRANT_PATH", str(tmp_path / "qdrant"))
    monkeypatch.setenv("TRANSCRIPT_CACHE_DIR", str(tmp_path / "transcripts"))
    monkeypatch.setenv("YOUTUBE_API_KEY", "")
    get_settings.cache_clear()
    vector_store.get_client.cache_clear()
    vector_store.get_vector_store.cache_clear()
    monkeypatch.setattr(vector_store, "get_embeddings", lambda: DeterministicFakeEmbedding(size=16))
    yield
    vector_store.get_vector_store.cache_clear()
    vector_store.get_client.cache_clear()
    get_settings.cache_clear()


def make_segments(count: int = 40, words: str = "alpha beta gamma delta epsilon zeta eta") -> list:
    return [
        TranscriptSegment(start=i * 4.0, duration=4.0, text=f"{words} {i}") for i in range(count)
    ]
