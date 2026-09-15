import pytest
from fastapi.testclient import TestClient

from app.api.routes import videos
from app.core.exceptions import TranscriptUnavailable
from app.core.models import Transcript
from app.main import app
from tests.conftest import make_segments

VID = "dQw4w9WgXcQ"


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_invalid_url_is_a_400_with_error_envelope(client):
    response = client.post("/api/videos", json={"url": "https://example.com/x"})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_video_url"


def test_invalid_body_is_a_422(client):
    assert client.post("/api/videos", json={}).status_code == 422


def test_ingest_failure_returns_200_with_status_failed_and_metadata(client, monkeypatch):
    from app.graphs import ingestion as graph_module

    def unavailable(video_id):
        raise TranscriptUnavailable("No captions are available for this video.")

    monkeypatch.setattr(graph_module, "get_transcript", unavailable)
    monkeypatch.setattr(graph_module, "get_index_marker", lambda v: None)
    response = client.post("/api/videos", json={"url": f"https://youtu.be/{VID}"})
    body = response.json()
    assert response.status_code == 200 and body["status"] == "failed"
    assert body["error"] == {
        "code": "transcript_unavailable",
        "message": "No captions are available for this video.",
        "stage": "fetch_transcript",
    }
    assert body["metadata"]["video_id"] == VID and body["metadata"]["available"] is False


def test_transcript_endpoint(client, monkeypatch):
    transcript = Transcript(video_id=VID, language="en", segments=make_segments(3))
    monkeypatch.setattr(videos, "get_transcript", lambda v, lang: transcript)
    body = client.get(f"/api/videos/{VID}/transcript").json()
    assert body["language"] == "en" and len(body["segments"]) == 3


def test_transcript_unavailable_is_a_404_and_hides_internals(client, monkeypatch):
    def boom(v, lang):
        raise TranscriptUnavailable("No captions are available for this video.")

    monkeypatch.setattr(videos, "get_transcript", boom)
    response = client.get(f"/api/videos/{VID}/transcript")
    assert response.status_code == 404 and "Traceback" not in response.text


def test_unexpected_errors_do_not_leak_details(client, monkeypatch):
    def boom(v, lang):
        raise RuntimeError("secret internal detail")

    monkeypatch.setattr(videos, "get_transcript", boom)
    response = client.get(f"/api/videos/{VID}/transcript")
    assert response.status_code == 500 and "secret" not in response.text


def test_malformed_video_id_path_is_rejected(client):
    assert client.get("/api/videos/not-an-id/transcript").status_code == 422
