from dataclasses import dataclass


@dataclass
class VideoContext:
    """Trusted per-run context supplied by the client application, never by the model.

    Optional at construction so a run without it fails with a clear error from
    `VideoMiddleware` instead of a TypeError. In LangGraph Studio, set it in the assistant's
    context/configuration panel, not in the input form.
    """

    video_id: str | None = None
