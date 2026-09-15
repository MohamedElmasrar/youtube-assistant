"""Qdrant (local persistent mode) vector store and the per-video retriever."""

import uuid
from functools import lru_cache

from langchain_core.vectorstores import VectorStoreRetriever
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient, models

from app.core.config import get_settings
from app.rag.embeddings import get_embeddings

_CHUNK_NAMESPACE = uuid.UUID("5a1f6a3e-6f0e-4d3b-9a77-0c0d2f9f6b11")
_VIDEO_ID_KEY = "metadata.video_id"  # langchain-qdrant stores document metadata under "metadata"


def chunk_point_id(chunk_id: str) -> str:
    """Deterministic point ID so re-indexing a chunk overwrites instead of duplicating."""
    return str(uuid.uuid5(_CHUNK_NAMESPACE, chunk_id))


def video_filter(video_id: str) -> models.Filter:
    return models.Filter(
        must=[models.FieldCondition(key=_VIDEO_ID_KEY, match=models.MatchValue(value=video_id))]
    )


@lru_cache
def get_client() -> QdrantClient:
    settings = get_settings()
    path = settings.resolve(settings.qdrant_path)
    path.mkdir(parents=True, exist_ok=True)
    return QdrantClient(path=str(path))


@lru_cache
def get_vector_store() -> QdrantVectorStore:
    settings = get_settings()
    client = get_client()
    embeddings = get_embeddings()
    if not client.collection_exists(settings.qdrant_collection):
        dimension = len(embeddings.embed_query("dimension probe"))
        client.create_collection(
            settings.qdrant_collection,
            vectors_config=models.VectorParams(size=dimension, distance=models.Distance.COSINE),
        )
    return QdrantVectorStore(
        client=client, collection_name=settings.qdrant_collection, embedding=embeddings
    )


def count_video_chunks(video_id: str) -> int:
    settings = get_settings()
    client = get_client()
    if not client.collection_exists(settings.qdrant_collection):
        return 0
    return client.count(
        settings.qdrant_collection, count_filter=video_filter(video_id), exact=True
    ).count


def get_video_retriever(video_id: str) -> VectorStoreRetriever:
    """Retriever restricted to one video. The filter is applied server-side, not by the LLM."""
    return get_vector_store().as_retriever(
        search_type="similarity",
        search_kwargs={"k": get_settings().top_k, "filter": video_filter(video_id)},
    )
