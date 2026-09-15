"""Loads the YouTube MCP tools for the agent and pins them to the active video."""

import copy

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.interceptors import MCPToolCallRequest

from app.core.config import get_settings
from app.services.youtube import is_valid_video_id

_VIDEO_ID_ARG = "video_id"


async def bind_active_video(request: MCPToolCallRequest, handler):
    """Overwrite `video_id` with the trusted run context, whatever the model supplied."""
    context = getattr(request.runtime, "context", None)
    video_id = getattr(context, "video_id", None)
    if not isinstance(video_id, str) or not is_valid_video_id(video_id):
        raise ValueError("No valid active video in the run context.")
    return await handler(request.override(args={**request.args, _VIDEO_ID_ARG: video_id}))


def _hide_video_id(tool: BaseTool) -> BaseTool:
    """Remove `video_id` from the schema the model sees; the interceptor supplies it."""
    schema = copy.deepcopy(tool.args_schema)
    if isinstance(schema, dict):
        schema.get("properties", {}).pop(_VIDEO_ID_ARG, None)
        schema["required"] = [r for r in schema.get("required", []) if r != _VIDEO_ID_ARG]
        tool.args_schema = schema
    return tool


async def load_youtube_tools() -> list[BaseTool]:
    client = MultiServerMCPClient(
        {"youtube": {"transport": "streamable_http", "url": get_settings().mcp_url}},
        tool_interceptors=[bind_active_video],
    )
    return [_hide_video_id(tool) for tool in await client.get_tools()]
