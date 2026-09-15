from types import SimpleNamespace

import pytest
from youtube_transcript_api import NoTranscriptFound, TranscriptsDisabled

from app.core.exceptions import InvalidVideoUrl, TranscriptUnavailable
from app.services import transcripts
from app.services.transcripts import get_transcript, normalize_segments

VID = "dQw4w9WgXcQ"


def test_normalize_cleans_sorts_and_dedupes():
    segments = normalize_segments(
        [
            (5.0, 2.0, "second &amp; last"),
            (1.0, 2.0, "  first\n line "),
            (1.0, 2.0, "first line"),
            (3.0, 1.0, "   "),
            (-1.0, 1.0, "negative"),
        ]
    )
    assert [(s.start, s.text) for s in segments] == [(1.0, "first line"), (5.0, "second & last")]


class _Fetched(list):
    language_code = "en"
    is_generated = True


class FakeTranscript:
    def fetch(self):
        return _Fetched(
            [
                SimpleNamespace(start=0.0, duration=2.0, text="hello"),
                SimpleNamespace(start=2.0, duration=2.0, text="world"),
            ]
        )


class FakeList:
    def find_transcript(self, languages):
        return FakeTranscript()

    def __iter__(self):
        return iter([FakeTranscript()])


def patch_api(monkeypatch, *, listing=None, error=None):
    calls = []

    class FakeApi:
        def list(self, video_id):
            calls.append(video_id)
            if error:
                raise error
            return listing or FakeList()

    monkeypatch.setattr(transcripts, "YouTubeTranscriptApi", FakeApi)
    return calls


def test_get_transcript_fetches_then_reuses_cache(monkeypatch):
    calls = patch_api(monkeypatch)
    first = get_transcript(VID)
    second = get_transcript(VID)
    assert first == second and first.language == "en" and first.is_generated
    assert [s.text for s in first.segments] == ["hello", "world"]
    assert len(calls) == 1  # second call served from the local cache


@pytest.mark.parametrize(
    "error", [TranscriptsDisabled(VID), NoTranscriptFound(VID, ["en"], FakeList())]
)
def test_unavailable_transcripts_raise_clean_error(monkeypatch, error):
    patch_api(monkeypatch, error=error)
    with pytest.raises(TranscriptUnavailable):
        get_transcript(VID)


def test_cache_paths_reject_traversal():
    with pytest.raises(InvalidVideoUrl):
        get_transcript("../../etc/passwd")
    with pytest.raises(InvalidVideoUrl):
        get_transcript(VID, "../x")
