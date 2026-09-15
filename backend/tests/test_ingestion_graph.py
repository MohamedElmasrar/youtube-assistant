import pytest

from app.core.exceptions import TranscriptUnavailable, UpstreamError
from app.core.models import VideoMetadata
from app.graphs import ingestion as graph_module

VID = "dQw4w9WgXcQ"


@pytest.fixture
def stubs(monkeypatch):
    calls = {"transcript": 0, "index": 0}
    state = {"indexed": False}

    monkeypatch.setattr(
        graph_module, "get_video_metadata", lambda v: VideoMetadata(video_id=v, title="Title")
    )

    def get_marker(video_id):
        if not state["indexed"]:
            return None
        return type("M", (), {"language": "en", "chunk_count": 3})()

    def fetch(video_id):
        calls["transcript"] += 1
        return type("T", (), {"language": "en"})()

    def index(video_id):
        calls["index"] += 1
        state["indexed"] = True
        return type("M", (), {"language": "en", "chunk_count": 3})()

    monkeypatch.setattr(graph_module, "get_index_marker", get_marker)
    monkeypatch.setattr(graph_module, "get_transcript", fetch)
    monkeypatch.setattr(graph_module, "index_video", index)
    return calls


async def run(url):
    return await graph_module.build_ingestion_graph().ainvoke({"url": url})


async def test_happy_path_then_skips_reprocessing(stubs):
    first = await run(f"https://youtu.be/{VID}")
    assert first["status"] == "ready" and first["chunk_count"] == 3 and not first["cached"]
    assert first["metadata"]["title"] == "Title"
    second = await run(VID)
    assert second["status"] == "ready" and second["cached"] is True
    assert stubs == {"transcript": 1, "index": 1}


async def test_invalid_url_fails_at_validation(stubs):
    result = await run("https://example.com")
    assert result["status"] == "failed" and result["stage"] == "validate"
    assert result["error"]["code"] == "invalid_video_url" and stubs["transcript"] == 0


async def test_missing_transcript_reports_stage_and_keeps_metadata(stubs, monkeypatch):
    def unavailable(video_id):
        raise TranscriptUnavailable("No captions are available for this video.")

    monkeypatch.setattr(graph_module, "get_transcript", unavailable)
    result = await run(VID)
    assert result["status"] == "failed" and result["stage"] == "fetch_transcript"
    assert result["error"]["code"] == "transcript_unavailable"
    assert result["metadata"]["title"] == "Title"  # the UI can still show the video


async def test_indexing_failure_is_reported(stubs, monkeypatch):
    def broken(video_id):
        raise UpstreamError("Indexing the transcript failed.")

    monkeypatch.setattr(graph_module, "index_video", broken)
    result = await run(VID)
    assert result["status"] == "failed" and result["stage"] == "index"
