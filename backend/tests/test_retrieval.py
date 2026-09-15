"""Indexing + retrieval against a real local Qdrant, using fake embeddings."""

import pytest

from app.core.exceptions import VideoNotIndexed
from app.rag.vector_store import count_video_chunks, get_video_retriever
from app.services import ingestion, retrieval
from tests.conftest import make_segments

A, B = "aaaaaaaaaaa", "bbbbbbbbbbb"


@pytest.fixture
def two_videos(monkeypatch):
    from app.core.models import Transcript

    def fake_get_transcript(video_id, language=None):
        words = "apples oranges" if video_id == A else "rockets planets"
        return Transcript(video_id=video_id, language="en", segments=make_segments(30, words))

    monkeypatch.setattr(ingestion, "get_transcript", fake_get_transcript)
    return ingestion.index_video(A), ingestion.index_video(B)


def test_retriever_only_returns_the_active_video(two_videos):
    for video_id in (A, B):
        docs = get_video_retriever(video_id).invoke("anything at all")
        assert docs and {d.metadata["video_id"] for d in docs} == {video_id}


def test_search_returns_citable_chunks_in_video_order(two_videos):
    chunks = retrieval.search_transcript(A, "apples")
    assert 0 < len(chunks) <= 5
    assert all(c.video_id == A and c.chunk_id.startswith(A) for c in chunks)
    assert [c.start_time for c in chunks] == sorted(c.start_time for c in chunks)
    assert all(c.end_time > c.start_time and c.text for c in chunks)


def test_search_unindexed_video_fails_closed(two_videos):
    with pytest.raises(VideoNotIndexed):
        retrieval.search_transcript("ccccccccccc", "x")


def test_indexing_is_idempotent(two_videos):
    marker = two_videos[0]
    assert count_video_chunks(A) == marker.chunk_count
    again = ingestion.index_video(A)
    assert again.chunk_count == marker.chunk_count == count_video_chunks(A)
    assert ingestion.get_index_marker(A) is not None


def test_changed_chunk_settings_invalidate_the_marker(two_videos, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setenv("CHUNK_TOKENS", "999")
    get_settings.cache_clear()
    assert ingestion.get_index_marker(A) is None


def test_missing_vectors_invalidate_the_marker(two_videos):
    from app.core.config import get_settings
    from app.rag.vector_store import get_client, video_filter

    get_client().delete(get_settings().qdrant_collection, points_selector=video_filter(A))
    assert ingestion.get_index_marker(A) is None  # incomplete index is not "ready"
    assert ingestion.get_index_marker(B) is not None
