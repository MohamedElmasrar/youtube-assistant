"""Transcript retrieval, normalization and local caching."""

import html
import logging
import os
import re
from pathlib import Path

from youtube_transcript_api import YouTubeTranscriptApi, YouTubeTranscriptApiException

from app.core.config import get_settings
from app.core.exceptions import InvalidVideoUrl, TranscriptUnavailable
from app.core.models import Transcript, TranscriptSegment
from app.services.youtube import is_valid_video_id

logger = logging.getLogger(__name__)

_WHITESPACE_RE = re.compile(r"\s+")
_LANGUAGE_RE = re.compile(r"^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$")
_PREFERRED_LANGUAGES = ["en"]


def normalize_segments(raw: list[tuple[float, float, str]]) -> list[TranscriptSegment]:
    """Decode HTML entities, collapse whitespace, drop empty/duplicate entries, sort by start."""
    segments: list[TranscriptSegment] = []
    for start, duration, text in sorted(raw, key=lambda item: item[0]):
        clean = _WHITESPACE_RE.sub(" ", html.unescape(text)).strip()
        if not clean or start < 0:
            continue
        if segments and segments[-1].text == clean and abs(segments[-1].start - start) < 0.01:
            continue
        segments.append(
            TranscriptSegment(
                start=round(start, 2), duration=round(max(duration, 0), 2), text=clean
            )
        )
    return segments


def _cache_dir() -> Path:
    return get_settings().resolve(get_settings().transcript_cache_dir)


def _cache_path(video_id: str, language: str) -> Path:
    if not is_valid_video_id(video_id) or not _LANGUAGE_RE.match(language):
        raise InvalidVideoUrl("Invalid video ID or language code.")
    return _cache_dir() / f"{video_id}.{language}.json"


def _read_cache(path: Path) -> Transcript | None:
    try:
        return Transcript.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        logger.warning("Ignoring unreadable transcript cache file %s", path.name)
        return None


def load_cached_transcript(video_id: str, language: str | None = None) -> Transcript | None:
    if language:
        path = _cache_path(video_id, language)
        return _read_cache(path) if path.exists() else None
    if not is_valid_video_id(video_id):
        raise InvalidVideoUrl("Invalid video ID.")
    candidates = sorted(_cache_dir().glob(f"{video_id}.*.json")) if _cache_dir().exists() else []
    candidates.sort(key=lambda p: p.name.split(".")[1] not in _PREFERRED_LANGUAGES)
    for path in candidates:
        if (cached := _read_cache(path)) is not None:
            return cached
    return None


def _save_cache(transcript: Transcript) -> None:
    path = _cache_path(transcript.video_id, transcript.language)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(transcript.model_dump_json(), encoding="utf-8")
    os.replace(tmp, path)


def fetch_transcript(video_id: str, language: str | None = None) -> Transcript:
    """Fetch captions (manual or auto-generated) from YouTube and normalize them."""
    api = YouTubeTranscriptApi()
    languages = [language] if language else _PREFERRED_LANGUAGES
    try:
        available = api.list(video_id)
        try:
            chosen = available.find_transcript(languages)
        except YouTubeTranscriptApiException:
            if language:
                raise
            chosen = next(iter(available))  # no preferred language: take whatever exists
        fetched = chosen.fetch()
    except (YouTubeTranscriptApiException, StopIteration) as exc:
        logger.info("Transcript unavailable for %s: %s", video_id, type(exc).__name__)
        raise TranscriptUnavailable(
            "No captions are available for this video"
            + (f" in language '{language}'." if language else ".")
        ) from exc

    segments = normalize_segments([(s.start, s.duration, s.text) for s in fetched])
    if not segments:
        raise TranscriptUnavailable("The video's captions are empty.")
    return Transcript(
        video_id=video_id,
        language=fetched.language_code,
        is_generated=fetched.is_generated,
        segments=segments,
    )


def get_transcript(video_id: str, language: str | None = None) -> Transcript:
    """Return the cached transcript, fetching and caching it on first use."""
    if (cached := load_cached_transcript(video_id, language)) is not None:
        return cached
    transcript = fetch_transcript(video_id, language)
    _save_cache(transcript)
    return transcript
