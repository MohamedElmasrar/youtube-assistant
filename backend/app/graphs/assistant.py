"""Graph registered with the Agent Server as the `assistant` graph.

The Agent Server provides threads, runs, streaming and checkpointing; this module only
supplies the compiled agent. MCP tools are loaded lazily on first use because the MCP server
is mounted in the same server process and is not reachable at import time.
"""

import asyncio

from langgraph.graph.state import CompiledStateGraph

from app.agents.video_agent import build_video_agent
from app.tools.mcp_tools import load_youtube_tools

_lock = asyncio.Lock()
_agent: CompiledStateGraph | None = None


async def make_graph() -> CompiledStateGraph:
    global _agent
    async with _lock:
        if _agent is None:
            _agent = build_video_agent(await load_youtube_tools())
        return _agent
