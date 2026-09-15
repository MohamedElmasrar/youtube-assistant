"""Indexing of cached transcripts into Qdrant, with an on-disk completion marker.

A video counts as indexed only when its marker file exists, the marker matches the current
chunking/embedding settings, and Qdrant holds every chunk the marker promises. A crash
mid-indexing therefore leaves no marker, and the next attempt simply re-upserts the same
deterministic point IDs.
"""

import json
import logging
import os
from pathlib import Path

from pydantic import BaseModel

from app.core.config import get_settings
from app.core.exceptions import UpstreamError
from app.rag.chunking import chunk_transcript
from app.rag.vector_store import chunk_point_id, count_video_chunks, get_vector_store
from app.services.transcripts import get_transcript

logger = logging.getLogger(__name__)

_BATCH_SIZE = 64


class IndexMarker(BaseModel):
    video_id: str
    language: str
    chunk_count: int
    embedding_model: str
    chunk_tokens: int
    chunk_overlap_tokens: int


def _marker_path(video_id: str) -> Path:
    settings = get_settings()
    return settings.resolve(settings.transcript_cache_dir) / "index" / f"{video_id}.json"


def _expected(marker: IndexMarker) -> bool:
    settings = get_settings()
    return (
        marker.embedding_model == settings.embedding_model
        and marker.chunk_tokens == settings.chunk_tokens
        and marker.chunk_overlap_tokens == settings.chunk_overlap_tokens
    )


def get_index_marker(video_id: str) -> IndexMarker | None:
    """Return the marker if the video is fully and currently indexed, else None."""
    try:
        marker = IndexMarker.model_validate_json(_marker_path(video_id).read_text("utf-8"))
    except (OSError, ValueError):
        return None
    if not _expected(marker) or count_video_chunks(video_id) < marker.chunk_count:
        return None
    return marker


def index_video(video_id: str) -> IndexMarker:
    """Chunk the cached transcript, embed it in batches and upsert it into Qdrant."""
    settings = get_settings()
    transcript = get_transcript(video_id)
    documents = chunk_transcript(
        video_id,
        transcript.segments,
        transcript.language,
        settings.chunk_tokens,
        settings.chunk_overlap_tokens,
    )
    store = get_vector_store()
    try:
        for i in range(0, len(documents), _BATCH_SIZE):
            batch = documents[i : i + _BATCH_SIZE]
            store.add_documents(batch, ids=[chunk_point_id(d.metadata["chunk_id"]) for d in batch])
    except Exception as exc:  # qdrant/torch raise many unrelated types; surface one clean error
        logger.exception("Indexing failed for %s", video_id)
        raise UpstreamError("Indexing the transcript failed.") from exc

    marker = IndexMarker(
        video_id=video_id,
        language=transcript.language,
        chunk_count=len(documents),
        embedding_model=settings.embedding_model,
        chunk_tokens=settings.chunk_tokens,
        chunk_overlap_tokens=settings.chunk_overlap_tokens,
    )
    path = _marker_path(video_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(marker.model_dump()), encoding="utf-8")
    os.replace(tmp, path)
    return marker
