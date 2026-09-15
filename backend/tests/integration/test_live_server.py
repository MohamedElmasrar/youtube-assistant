"""Smoke tests against a running `langgraph dev` (network required). Opt in with:

    RUN_INTEGRATION=1 uv run pytest tests/integration

They ingest a real video, then drive the agent with a scripted model so that no Gemini
credentials are needed, while the MCP tools, Qdrant index and run context are all real.
"""

import os

import httpx
import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from app.agents.context import VideoContext
from app.agents.video_agent import build_video_agent
from app.tools.mcp_tools import load_youtube_tools

BASE = os.environ.get("LANGGRAPH_API_URL", "http://localhost:2024")
VIDEO = "dQw4w9WgXcQ"

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_INTEGRATION") != "1", reason="set RUN_INTEGRATION=1 with a running server"
)


class ScriptedModel(GenericFakeChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


@pytest.fixture(scope="module")
def ingested():
    response = httpx.post(f"{BASE}/api/videos", json={"url": VIDEO}, timeout=600)
    assert response.status_code == 200 and response.json()["status"] == "ready"
    return response.json()


def test_transcript_endpoint_returns_timestamps(ingested):
    body = httpx.get(f"{BASE}/api/videos/{VIDEO}/transcript", timeout=30).json()
    assert body["segments"] and {"start", "duration", "text"} <= body["segments"][0].keys()


async def test_agent_uses_real_mcp_search_and_cites_real_timestamps(ingested):
    tools = await load_youtube_tools()
    model = ScriptedModel(
        messages=iter(
            [
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "search_video_transcript",
                            # A model-supplied video_id must be ignored.
                            "args": {"query": "never gonna give you up", "video_id": "bbbbbbbbbbb"},
                            "id": "1",
                        }
                    ],
                ),
                AIMessage(content=f"The chorus repeats [[{VIDEO}_0]] and [[{VIDEO}_999]]."),
            ]
        )
    )
    agent = build_video_agent(tools, model=model, checkpointer=InMemorySaver())
    result = await agent.ainvoke(
        {"messages": [HumanMessage("What is the chorus?")]},
        config={"configurable": {"thread_id": "live"}},
        context=VideoContext(video_id=VIDEO),
    )
    tool_message = next(m for m in result["messages"] if m.type == "tool")
    assert tool_message.status != "error"
    chunks = tool_message.artifact["structured_content"]["chunks"]
    assert {c["video_id"] for c in chunks} == {VIDEO}
    citations = result["messages"][-1].additional_kwargs["citations"]
    assert [c["chunk_id"] for c in citations] == [f"{VIDEO}_0"]
    assert citations[0]["start_time"] == pytest.approx(1.36)
