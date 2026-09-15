"""Transcript search over the active video, using the LangChain retriever."""

from app.core.exceptions import VideoNotIndexed
from app.core.models import TranscriptChunk
from app.rag.vector_store import get_video_retriever
from app.services.ingestion import get_index_marker


def search_transcript(video_id: str, query: str) -> list[TranscriptChunk]:
    """Return the most relevant chunks of `video_id`, de-duplicated and in video order."""
    if get_index_marker(video_id) is None:
        raise VideoNotIndexed("This video has not been indexed yet. Load it first.")
    documents = get_video_retriever(video_id).invoke(query)

    chunks: dict[str, TranscriptChunk] = {}
    for doc in documents:
        meta = doc.metadata
        # Defence in depth: the retriever filter already restricts results to this video.
        if meta.get("video_id") != video_id or meta["chunk_id"] in chunks:
            continue
        chunks[meta["chunk_id"]] = TranscriptChunk(
            chunk_id=meta["chunk_id"],
            video_id=video_id,
            start_time=meta["start_time"],
            end_time=meta["end_time"],
            text=doc.page_content,
        )
    return sorted(chunks.values(), key=lambda c: c.start_time)
