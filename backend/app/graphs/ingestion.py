"""Video ingestion workflow: validate -> metadata -> (skip if indexed) -> transcript -> index.

State stays small on purpose: the transcript is cached on disk and re-read by the indexing
node rather than passed through (and checkpointed in) graph state.
"""

import logging
from collections.abc import Callable
from functools import lru_cache
from typing import Any, Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from app.core.exceptions import AppError
from app.services.ingestion import get_index_marker, index_video
from app.services.transcripts import get_transcript
from app.services.youtube import get_video_metadata, parse_video_id

logger = logging.getLogger(__name__)

Status = Literal["pending", "ready", "failed"]


class IngestionInput(TypedDict):
    url: str


class IngestionState(IngestionInput, total=False):
    video_id: str
    status: Status
    stage: str
    cached: bool
    language: str | None
    chunk_count: int
    metadata: dict[str, Any]
    error: dict[str, Any] | None


def _guarded(stage: str, fn: Callable[[IngestionState], dict[str, Any]]):
    """Turn expected application errors into a `failed` state naming the failing stage."""

    def node(state: IngestionState) -> dict[str, Any]:
        try:
            return {"stage": stage, **fn(state)}
        except AppError as exc:
            logger.info("Ingestion failed at %s: %s", stage, exc.code)
            return {
                "stage": stage,
                "status": "failed",
                "error": {"code": exc.code, "message": exc.message, "status_code": exc.status_code},
            }

    node.__name__ = stage
    return node


def _validate(state: IngestionState) -> dict[str, Any]:
    return {"video_id": parse_video_id(state["url"]), "status": "pending", "error": None}


def _fetch_metadata(state: IngestionState) -> dict[str, Any]:
    # Metadata is best-effort: an unavailable result must not block transcript-based chat.
    return {"metadata": get_video_metadata(state["video_id"]).model_dump(mode="json")}


def _check_index(state: IngestionState) -> dict[str, Any]:
    marker = get_index_marker(state["video_id"])
    if marker is None:
        return {"cached": False}
    return {
        "cached": True,
        "status": "ready",
        "language": marker.language,
        "chunk_count": marker.chunk_count,
    }


def _fetch_transcript(state: IngestionState) -> dict[str, Any]:
    transcript = get_transcript(state["video_id"])  # caches to disk
    return {"language": transcript.language}


def _index(state: IngestionState) -> dict[str, Any]:
    marker = index_video(state["video_id"])
    return {"status": "ready", "chunk_count": marker.chunk_count, "language": marker.language}


def _continue_unless_failed(next_node: str):
    def route(state: IngestionState) -> str:
        return END if state.get("status") == "failed" else next_node

    return route


def _after_check(state: IngestionState) -> str:
    return END if state.get("status") in ("ready", "failed") else "fetch_transcript"


def build_ingestion_graph():
    builder = StateGraph(IngestionState, input_schema=IngestionInput)
    for name, fn in [
        ("validate", _validate),
        ("fetch_metadata", _fetch_metadata),
        ("check_index", _check_index),
        ("fetch_transcript", _fetch_transcript),
        ("index", _index),
    ]:
        builder.add_node(name, _guarded(name, fn))
    builder.add_edge(START, "validate")
    builder.add_conditional_edges("validate", _continue_unless_failed("fetch_metadata"))
    builder.add_edge("fetch_metadata", "check_index")
    builder.add_conditional_edges("check_index", _after_check)
    builder.add_conditional_edges("fetch_transcript", _continue_unless_failed("index"))
    builder.add_edge("index", END)
    return builder.compile(name="ingestion")


@lru_cache
def get_ingestion_graph():
    """Instance used by the REST route. Separate from the module-level `graph` that the
    Agent Server loads (and attaches its own checkpointer to)."""
    return build_ingestion_graph()


graph = build_ingestion_graph()
