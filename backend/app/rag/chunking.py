"""Timestamp-aware chunking.

Caption segments are short and already carry exact timestamps, so a general text splitter
would lose the segment-to-time mapping. Instead, whole segments are grouped greedily into
chunks of roughly `chunk_tokens`, with the trailing segments repeated as overlap.
"""

from langchain_core.documents import Document

from app.core.models import TranscriptSegment

_CHARS_PER_TOKEN = 4  # rough estimate; chunk size is approximate by design


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // _CHARS_PER_TOKEN)


def chunk_transcript(
    video_id: str,
    segments: list[TranscriptSegment],
    language: str,
    chunk_tokens: int,
    overlap_tokens: int,
) -> list[Document]:
    if overlap_tokens >= chunk_tokens:
        raise ValueError("overlap_tokens must be smaller than chunk_tokens")

    documents: list[Document] = []
    window: list[TranscriptSegment] = []
    window_tokens = 0
    # Number of segments at the front of `window` that were carried over as overlap.
    carried = 0

    def flush() -> None:
        nonlocal window, window_tokens, carried
        documents.append(
            Document(
                page_content=" ".join(s.text for s in window),
                metadata={
                    "video_id": video_id,
                    "chunk_id": f"{video_id}_{len(documents)}",
                    "start_time": window[0].start,
                    "end_time": max(s.end for s in window),
                    "language": language,
                },
            )
        )
        keep: list[TranscriptSegment] = []
        kept_tokens = 0
        for seg in reversed(window):
            tokens = estimate_tokens(seg.text)
            if kept_tokens + tokens > overlap_tokens:
                break
            keep.insert(0, seg)
            kept_tokens += tokens
        window, window_tokens, carried = keep, kept_tokens, len(keep)

    for segment in segments:
        tokens = estimate_tokens(segment.text)
        if window and len(window) > carried and window_tokens + tokens > chunk_tokens:
            flush()
        window.append(segment)
        window_tokens += tokens

    if window and len(window) > carried:
        flush()
    return documents
