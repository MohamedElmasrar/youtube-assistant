import pytest

from app.rag.chunking import chunk_transcript
from tests.conftest import make_segments


def test_chunks_have_exact_timestamps_and_metadata():
    segments = make_segments(40)
    docs = chunk_transcript("vid", segments, "en", chunk_tokens=60, overlap_tokens=15)
    assert len(docs) > 3
    by_start = {s.start: s for s in segments}
    for i, doc in enumerate(docs):
        meta = doc.metadata
        assert meta["chunk_id"] == f"vid_{i}" and meta["video_id"] == "vid"
        assert meta["language"] == "en" and meta["start_time"] in by_start
        covered = [s for s in segments if meta["start_time"] <= s.start < meta["end_time"]]
        assert doc.page_content == " ".join(s.text for s in covered)
        assert meta["end_time"] == covered[-1].end


def test_chunks_cover_whole_transcript_with_overlap():
    segments = make_segments(40)
    docs = chunk_transcript("vid", segments, "en", chunk_tokens=60, overlap_tokens=15)
    assert docs[0].metadata["start_time"] == segments[0].start
    assert docs[-1].metadata["end_time"] == segments[-1].end
    for before, after in zip(docs, docs[1:], strict=False):
        assert after.metadata["start_time"] < before.metadata["end_time"]  # overlap
        assert after.metadata["start_time"] > before.metadata["start_time"]  # progress


def test_oversized_single_segment_still_becomes_a_chunk():
    segments = make_segments(1, words="word " * 400)
    docs = chunk_transcript("vid", segments, "en", chunk_tokens=50, overlap_tokens=10)
    assert len(docs) == 1


def test_empty_and_invalid_arguments():
    assert chunk_transcript("vid", [], "en", 50, 10) == []
    with pytest.raises(ValueError):
        chunk_transcript("vid", make_segments(3), "en", 50, 50)
