"""Run-level guards: pin the thread to one video and validate citations on the final answer."""

from typing import Annotated, Any, NotRequired

from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware
from langchain.agents.middleware.types import OmitFromInput
from langchain_core.messages import AIMessage
from langgraph.runtime import Runtime

from app.agents.citations import attach_citations, collect_evidence
from app.agents.context import VideoContext
from app.services.youtube import is_valid_video_id

MISSING_VIDEO_MESSAGE = (
    "No video selected: pass a valid 11-character video_id in the run context "
    "(in LangGraph Studio, set it in the assistant's context/configuration, not the input)."
)


class VideoState(AgentState):
    # The video this thread is bound to. Set by the middleware from the trusted run context;
    # hidden from the input schema so clients cannot (and Studio does not invite them to) set it.
    video_id: Annotated[NotRequired[str], OmitFromInput]


class VideoMiddleware(AgentMiddleware[VideoState, VideoContext]):
    state_schema = VideoState

    def before_agent(
        self, state: VideoState, runtime: Runtime[VideoContext]
    ) -> dict[str, Any] | None:
        context = runtime.context
        video_id = getattr(context, "video_id", None)
        if not isinstance(video_id, str) or not is_valid_video_id(video_id):
            raise ValueError(MISSING_VIDEO_MESSAGE)
        bound = state.get("video_id")
        if bound and bound != video_id:
            raise ValueError("This conversation belongs to a different video. Start a new one.")
        return None if bound else {"video_id": video_id}

    def after_agent(
        self, state: VideoState, runtime: Runtime[VideoContext]
    ) -> dict[str, Any] | None:
        messages = state["messages"]
        last = messages[-1] if messages else None
        if not isinstance(last, AIMessage) or last.tool_calls or runtime.context is None:
            return None
        evidence = collect_evidence(messages, runtime.context.video_id)
        return {"messages": [attach_citations(last, evidence)]}
