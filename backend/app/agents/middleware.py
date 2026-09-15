"""Run-level guards: pin the thread to one video and validate citations on the final answer."""

from typing import Any, NotRequired

from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import AIMessage
from langgraph.runtime import Runtime

from app.agents.citations import attach_citations, collect_evidence
from app.agents.context import VideoContext
from app.services.youtube import is_valid_video_id


class VideoState(AgentState):
    video_id: NotRequired[str]


class VideoMiddleware(AgentMiddleware[VideoState, VideoContext]):
    state_schema = VideoState

    def before_agent(
        self, state: VideoState, runtime: Runtime[VideoContext]
    ) -> dict[str, Any] | None:
        context = runtime.context
        if context is None or not is_valid_video_id(context.video_id):
            raise ValueError("A valid video_id is required in the run context.")
        bound = state.get("video_id")
        if bound and bound != context.video_id:
            raise ValueError("This conversation belongs to a different video. Start a new one.")
        return None if bound else {"video_id": context.video_id}

    def after_agent(
        self, state: VideoState, runtime: Runtime[VideoContext]
    ) -> dict[str, Any] | None:
        messages = state["messages"]
        last = messages[-1] if messages else None
        if not isinstance(last, AIMessage) or last.tool_calls or runtime.context is None:
            return None
        evidence = collect_evidence(messages, runtime.context.video_id)
        return {"messages": [attach_citations(last, evidence)]}
