import json

import pytest
from mcp.server.fastmcp.exceptions import ToolError
from mcp.shared.memory import create_connected_server_and_client_session

from app.core.models import Transcript, TranscriptSegment, VideoMetadata
from app.mcp import youtube_server
from app.tools.mcp_tools import _hide_video_id, bind_active_video

VID = "aaaaaaaaaaa"


async def test_server_exposes_exactly_the_three_tools():
    tools = await youtube_server.mcp.list_tools()
    assert {t.name for t in tools} == {
        "get_video_info",
        "get_video_transcript",
        "search_video_transcript",
    }


async def test_get_video_info_delegates_to_service(monkeypatch):
    monkeypatch.setattr(
        youtube_server, "require_video_metadata", lambda v: VideoMetadata(video_id=v, title="T")
    )
    _, structured = await youtube_server.mcp.call_tool("get_video_info", {"video_id": VID})
    assert structured["title"] == "T"


async def test_transcript_window_and_pagination(monkeypatch):
    segments = [TranscriptSegment(start=i, duration=1, text=f"s{i}") for i in range(500)]
    monkeypatch.setattr(
        youtube_server,
        "get_transcript",
        lambda v, lang: Transcript(video_id=v, language="en", segments=segments),
    )
    _, page = await youtube_server.mcp.call_tool("get_video_transcript", {"video_id": VID})
    assert len(page["segments"]) == 400 and page["truncated"] and page["next_start_time"] == 400
    _, rest = await youtube_server.mcp.call_tool(
        "get_video_transcript", {"video_id": VID, "start_time": 400}
    )
    assert len(rest["segments"]) == 100 and not rest["truncated"]
    _, window = await youtube_server.mcp.call_tool(
        "get_video_transcript", {"video_id": VID, "start_time": 10, "end_time": 12}
    )
    assert [s["text"] for s in window["segments"]] == ["s10", "s11"]


@pytest.mark.parametrize("bad_id", ["short", "../../etc/passwd", "a" * 12])
async def test_tool_arguments_are_validated(bad_id):
    with pytest.raises(ToolError):
        await youtube_server.mcp.call_tool("get_video_info", {"video_id": bad_id})
    with pytest.raises(ToolError):
        await youtube_server.mcp.call_tool(
            "search_video_transcript", {"query": "x", "video_id": bad_id}
        )


async def test_search_tool_over_a_real_mcp_session(monkeypatch):
    from app.core.models import TranscriptChunk

    chunk = TranscriptChunk(chunk_id=f"{VID}_0", video_id=VID, start_time=1, end_time=2, text="t")
    monkeypatch.setattr(youtube_server, "search_transcript", lambda v, q: [chunk])
    async with create_connected_server_and_client_session(
        youtube_server.mcp._mcp_server
    ) as session:
        result = await session.call_tool("search_video_transcript", {"query": "q", "video_id": VID})
    payload = json.loads(result.content[0].text)
    assert payload["chunks"][0]["chunk_id"] == f"{VID}_0" and "untrusted" in payload["notice"]
    assert result.structuredContent["chunks"][0]["start_time"] == 1


async def test_interceptor_overrides_model_supplied_video_id():
    class Runtime:
        context = type("C", (), {"video_id": VID})()

    from langchain_mcp_adapters.interceptors import MCPToolCallRequest

    request = MCPToolCallRequest(
        name="search_video_transcript",
        args={"query": "q", "video_id": "bbbbbbbbbbb"},
        server_name="youtube",
        runtime=Runtime(),
    )

    async def handler(req):
        return req.args

    assert (await bind_active_video(request, handler))["video_id"] == VID
    no_context = MCPToolCallRequest(name="x", args={}, server_name="youtube", runtime=None)
    with pytest.raises(ValueError):
        await bind_active_video(no_context, handler)


def test_video_id_is_hidden_from_the_model_schema():
    from langchain_core.tools import StructuredTool

    schema = {
        "type": "object",
        "properties": {"query": {"type": "string"}, "video_id": {"type": "string"}},
        "required": ["query", "video_id"],
    }
    tool = StructuredTool(name="t", description="d", args_schema=schema, coroutine=lambda **kw: "x")
    hidden = _hide_video_id(tool)
    assert list(hidden.args_schema["properties"]) == ["query"]
    assert hidden.args_schema["required"] == ["query"]
