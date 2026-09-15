from dataclasses import dataclass


@dataclass
class VideoContext:
    """Trusted per-run context supplied by the client application, never by the model."""

    video_id: str
