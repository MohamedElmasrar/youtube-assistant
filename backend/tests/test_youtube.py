import httpx
import pytest

from app.core.exceptions import InvalidVideoUrl
from app.services import youtube
from app.services.youtube import metadata_from_item, parse_iso8601_duration, parse_video_id

VID = "dQw4w9WgXcQ"


@pytest.mark.parametrize(
    "value",
    [
        f"https://www.youtube.com/watch?v={VID}",
        f"https://www.youtube.com/watch?v={VID}&t=42s&list=abc",
        f"youtube.com/watch?v={VID}",
        f"https://m.youtube.com/watch?v={VID}",
        f"https://youtu.be/{VID}?si=xyz",
        f"https://www.youtube.com/shorts/{VID}",
        f"https://www.youtube.com/live/{VID}?feature=share",
        f"https://www.youtube.com/embed/{VID}",
        f"https://www.youtube-nocookie.com/embed/{VID}",
        f"  {VID}  ",
    ],
)
def test_parse_video_id_accepts_supported_formats(value):
    assert parse_video_id(value) == VID


@pytest.mark.parametrize(
    "value",
    [
        "",
        "https://example.com/watch?v=" + VID,
        "https://youtube.com.evil.com/watch?v=" + VID,
        "https://www.youtube.com/watch?v=short",
        "https://www.youtube.com/channel/UCabcdefghijklmnop",
        "not a url",
        "javascript:alert(1)",
    ],
)
def test_parse_video_id_rejects_everything_else(value):
    with pytest.raises(InvalidVideoUrl):
        parse_video_id(value)


def test_parse_duration():
    assert parse_iso8601_duration("PT1H2M3S") == 3723
    assert parse_iso8601_duration("PT45S") == 45
    assert parse_iso8601_duration("P1DT1S") == 86401
    assert parse_iso8601_duration("garbage") is None
    assert parse_iso8601_duration(None) is None


def test_metadata_from_item_maps_fields():
    meta = metadata_from_item(
        VID,
        {
            "snippet": {
                "title": "T",
                "channelTitle": "C",
                "publishedAt": "2020-01-02T03:04:05Z",
                "thumbnails": {"default": {"url": "d"}, "high": {"url": "h"}},
            },
            "contentDetails": {"duration": "PT3M"},
            "statistics": {"viewCount": "10"},
            "status": {"embeddable": False},
        },
    )
    assert (meta.title, meta.channel_title, meta.duration_seconds) == ("T", "C", 180)
    assert meta.thumbnail_url == "h" and meta.view_count == 10 and meta.embeddable is False
    assert meta.like_count is None


def test_metadata_without_api_key_is_a_graceful_fallback():
    meta = youtube.get_video_metadata(VID)
    assert meta.available is False and meta.video_id == VID


def test_metadata_http_failure_is_a_graceful_fallback(monkeypatch):
    monkeypatch.setenv("YOUTUBE_API_KEY", "k")
    from app.core.config import get_settings

    get_settings.cache_clear()

    def boom(*args, **kwargs):
        raise httpx.ConnectError("down")

    monkeypatch.setattr(youtube.httpx, "get", boom)
    assert youtube.get_video_metadata(VID).available is False


def test_metadata_sends_key_in_header_not_url(monkeypatch):
    monkeypatch.setenv("YOUTUBE_API_KEY", "secret")
    from app.core.config import get_settings

    get_settings.cache_clear()
    seen = {}

    def fake_get(url, params, headers, timeout):
        seen.update(url=url, params=params, headers=headers)
        request = httpx.Request("GET", url)
        return httpx.Response(200, json={"items": [{"snippet": {"title": "Hi"}}]}, request=request)

    monkeypatch.setattr(youtube.httpx, "get", fake_get)
    meta = youtube.get_video_metadata(VID)
    assert meta.title == "Hi"
    assert "secret" not in str(seen["params"]) and seen["headers"]["x-goog-api-key"] == "secret"
