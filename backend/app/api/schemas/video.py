from typing import Literal

from pydantic import BaseModel, Field

from app.core.models import Transcript, VideoMetadata


class IngestRequest(BaseModel):
    url: str = Field(min_length=1, max_length=500, description="YouTube URL or video ID")


class IngestionError(BaseModel):
    code: str
    message: str
    stage: str | None = None


class VideoResponse(BaseModel):
    video_id: str
    status: Literal["ready", "failed"]
    cached: bool = False
    language: str | None = None
    chunk_count: int = 0
    metadata: VideoMetadata
    error: IngestionError | None = None


class TranscriptResponse(Transcript):
    pass


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
