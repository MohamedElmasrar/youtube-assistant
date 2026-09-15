"""Thin HTTP adapters over the video services. Chat, threads and runs live in LangGraph."""

from fastapi import APIRouter, Query

from app.api.schemas.video import (
    HealthResponse,
    IngestionError,
    IngestRequest,
    TranscriptResponse,
    VideoResponse,
)
from app.core.exceptions import InvalidVideoUrl, VideoNotIndexed
from app.core.models import VideoId, VideoMetadata
from app.graphs.ingestion import get_ingestion_graph
from app.services.ingestion import get_index_marker
from app.services.transcripts import get_transcript
from app.services.youtube import get_video_metadata

router = APIRouter(prefix="/api")


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@router.post("/videos", response_model=VideoResponse)
async def ingest_video(request: IngestRequest) -> VideoResponse:
    """Validate, fetch and index a video. Re-posting an indexed video is a cheap no-op."""
    state = await get_ingestion_graph().ainvoke({"url": request.url})
    error = state.get("error")
    if error and error["code"] == InvalidVideoUrl.code:
        raise InvalidVideoUrl(error["message"])
    return VideoResponse(
        video_id=state["video_id"],
        status=state["status"],
        cached=state.get("cached", False),
        language=state.get("language"),
        chunk_count=state.get("chunk_count", 0),
        metadata=VideoMetadata.model_validate(state["metadata"]),
        error=IngestionError(code=error["code"], message=error["message"], stage=state.get("stage"))
        if error
        else None,
    )


@router.get("/videos/{video_id}", response_model=VideoResponse)
def get_video(video_id: VideoId) -> VideoResponse:
    marker = get_index_marker(video_id)
    return VideoResponse(
        video_id=video_id,
        status="ready" if marker else "failed",
        cached=marker is not None,
        language=marker.language if marker else None,
        chunk_count=marker.chunk_count if marker else 0,
        metadata=get_video_metadata(video_id),
        error=None
        if marker
        else IngestionError(code=VideoNotIndexed.code, message="Video is not indexed yet."),
    )


@router.get("/videos/{video_id}/transcript", response_model=TranscriptResponse)
def get_video_transcript(
    video_id: VideoId, language: str | None = Query(default=None, max_length=12)
) -> TranscriptResponse:
    return TranscriptResponse(**get_transcript(video_id, language).model_dump())
