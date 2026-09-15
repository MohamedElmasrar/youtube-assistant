"""YouTube URL parsing and public metadata lookup (YouTube Data API v3)."""

import logging
import re
from urllib.parse import parse_qs, urlparse

import httpx

from app.core.config import get_settings
from app.core.exceptions import InvalidVideoUrl, UpstreamError
from app.core.models import VIDEO_ID_PATTERN, VideoMetadata

logger = logging.getLogger(__name__)

VIDEOS_ENDPOINT = "https://www.googleapis.com/youtube/v3/videos"
_ID_RE = re.compile(VIDEO_ID_PATTERN)
_YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"}
_NOCOOKIE_HOSTS = {"youtube-nocookie.com", "www.youtube-nocookie.com"}
_PATH_PREFIXES = ("shorts", "live", "embed", "v")
_DURATION_RE = re.compile(r"^P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$")


def is_valid_video_id(value: str) -> bool:
    return bool(_ID_RE.match(value))


def parse_video_id(url_or_id: str) -> str:
    """Return the video ID for a supported YouTube URL or a bare video ID.

    Only the ID is extracted; the URL itself is never requested.
    """
    value = url_or_id.strip()
    if is_valid_video_id(value):
        return value

    parsed = urlparse(value if "://" in value else f"https://{value}")
    host = (parsed.hostname or "").lower()
    segments = [s for s in parsed.path.split("/") if s]
    candidate: str | None = None

    if host == "youtu.be":
        candidate = segments[0] if segments else None
    elif host in _YOUTUBE_HOSTS | _NOCOOKIE_HOSTS:
        if segments[:1] == ["watch"]:
            candidate = (parse_qs(parsed.query).get("v") or [None])[0]
        elif len(segments) >= 2 and segments[0] in _PATH_PREFIXES:
            candidate = segments[1]

    if candidate and is_valid_video_id(candidate):
        return candidate
    raise InvalidVideoUrl("Enter a valid YouTube video URL or video ID.")


def parse_iso8601_duration(value: str | None) -> int | None:
    if not value:
        return None
    match = _DURATION_RE.match(value)
    if not match:
        return None
    days, hours, minutes, seconds = (int(g or 0) for g in match.groups())
    return days * 86400 + hours * 3600 + minutes * 60 + seconds


def _to_int(value: str | None) -> int | None:
    return int(value) if value and value.isdigit() else None


def _best_thumbnail(thumbnails: dict) -> str | None:
    for key in ("maxres", "standard", "high", "medium", "default"):
        if key in thumbnails:
            return thumbnails[key].get("url")
    return None


def metadata_from_item(video_id: str, item: dict) -> VideoMetadata:
    snippet = item.get("snippet", {})
    stats = item.get("statistics", {})
    return VideoMetadata(
        video_id=video_id,
        title=snippet.get("title"),
        description=snippet.get("description"),
        channel_title=snippet.get("channelTitle"),
        channel_id=snippet.get("channelId"),
        thumbnail_url=_best_thumbnail(snippet.get("thumbnails", {})),
        published_at=snippet.get("publishedAt"),
        duration_seconds=parse_iso8601_duration(item.get("contentDetails", {}).get("duration")),
        view_count=_to_int(stats.get("viewCount")),
        like_count=_to_int(stats.get("likeCount")),
        tags=snippet.get("tags", []),
        embeddable=item.get("status", {}).get("embeddable"),
    )


def get_video_metadata(video_id: str) -> VideoMetadata:
    """Fetch public metadata. Returns `available=False` when it cannot be obtained."""
    settings = get_settings()
    if not settings.youtube_api_key:
        logger.info("YOUTUBE_API_KEY not set; metadata unavailable for %s", video_id)
        return VideoMetadata(video_id=video_id, available=False)
    try:
        response = httpx.get(
            VIDEOS_ENDPOINT,
            params={"part": "snippet,contentDetails,statistics,status", "id": video_id},
            headers={"x-goog-api-key": settings.youtube_api_key},
            timeout=settings.http_timeout_seconds,
        )
        response.raise_for_status()
        items = response.json().get("items", [])
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("YouTube Data API request failed for %s: %s", video_id, type(exc).__name__)
        return VideoMetadata(video_id=video_id, available=False)
    if not items:
        return VideoMetadata(video_id=video_id, available=False)
    return metadata_from_item(video_id, items[0])


def require_video_metadata(video_id: str) -> VideoMetadata:
    """Like `get_video_metadata` but raises when metadata is unavailable (for MCP tools)."""
    metadata = get_video_metadata(video_id)
    if not metadata.available:
        raise UpstreamError(
            "Video metadata is unavailable (check YOUTUBE_API_KEY and the video ID)."
        )
    return metadata
