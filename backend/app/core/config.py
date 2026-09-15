"""Application settings, loaded once from environment variables and `backend/.env`."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    google_api_key: str | None = None
    youtube_api_key: str | None = None

    gemini_model: str = "gemini-flash-lite-latest"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    qdrant_path: Path = Path("./data/qdrant")
    qdrant_collection: str = "video_transcripts"
    transcript_cache_dir: Path = Path("./data/transcripts")

    top_k: int = Field(default=5, ge=1, le=20)
    # all-MiniLM-L6-v2 truncates input at 256 word pieces, so chunks are sized to fit.
    chunk_tokens: int = Field(default=240, ge=50)
    chunk_overlap_tokens: int = Field(default=40, ge=0)

    max_tool_calls: int = Field(default=6, ge=1)
    max_model_calls: int = Field(default=8, ge=2)

    # Where the agent reaches the MCP server mounted on this same Agent Server.
    langgraph_api_url: str = "http://localhost:2024"
    mcp_mount_path: str = "/api/mcp"

    http_timeout_seconds: float = 10.0

    @property
    def mcp_url(self) -> str:
        return f"{self.langgraph_api_url.rstrip('/')}{self.mcp_mount_path}/"

    def resolve(self, path: Path) -> Path:
        return path if path.is_absolute() else (BACKEND_DIR / path).resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()
