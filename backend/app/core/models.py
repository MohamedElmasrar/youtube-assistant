"""Domain models shared by services, the API, the MCP server and the agent."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

VIDEO_ID_PATTERN = r"^[A-Za-z0-9_-]{11}$"
VideoId = Annotated[str, Field(pattern=VIDEO_ID_PATTERN, description="11-character YouTube ID")]


class VideoMetadata(BaseModel):
    video_id: VideoId
    available: bool = True
    title: str | None = None
    description: str | None = None
    channel_title: str | None = None
    channel_id: str | None = None
    thumbnail_url: str | None = None
    published_at: datetime | None = None
    duration_seconds: int | None = None
    view_count: int | None = None
    like_count: int | None = None
    tags: list[str] = Field(default_factory=list)
    embeddable: bool | None = None


class TranscriptSegment(BaseModel):
    start: float
    duration: float
    text: str

    @property
    def end(self) -> float:
        return self.start + self.duration


class Transcript(BaseModel):
    video_id: VideoId
    language: str
    is_generated: bool = False
    segments: list[TranscriptSegment]


class TranscriptChunk(BaseModel):
    """A retrieved, citable piece of the transcript."""

    chunk_id: str
    video_id: VideoId
    start_time: float
    end_time: float
    text: str
