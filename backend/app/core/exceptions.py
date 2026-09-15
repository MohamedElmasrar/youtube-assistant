"""Application errors. Each carries an HTTP status and a stable machine-readable code."""


class AppError(Exception):
    status_code = 500
    code = "internal_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class InvalidVideoUrl(AppError):
    status_code = 400
    code = "invalid_video_url"


class TranscriptUnavailable(AppError):
    status_code = 404
    code = "transcript_unavailable"


class VideoNotIndexed(AppError):
    status_code = 409
    code = "video_not_indexed"


class UpstreamError(AppError):
    status_code = 502
    code = "upstream_error"
