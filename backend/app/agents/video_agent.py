"""The video question-answering agent, built with LangChain's `create_agent`."""

from collections.abc import Sequence

from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware, ToolCallLimitMiddleware
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.types import Checkpointer

from app.agents.context import VideoContext
from app.agents.middleware import VideoMiddleware
from app.agents.prompts import skill_prompt
from app.core.config import get_settings


def build_video_agent(
    tools: Sequence[BaseTool],
    model: BaseChatModel | None = None,
    checkpointer: Checkpointer | None = None,
):
    """Compile the agent. The Agent Server attaches its own checkpointer; pass one only in tests."""
    settings = get_settings()
    return create_agent(
        model=model or ChatGoogleGenerativeAI(model=settings.gemini_model, temperature=0),
        tools=list(tools),
        middleware=[
            VideoMiddleware(),
            skill_prompt,
            ToolCallLimitMiddleware(run_limit=settings.max_tool_calls, exit_behavior="continue"),
            ModelCallLimitMiddleware(run_limit=settings.max_model_calls, exit_behavior="end"),
        ],
        context_schema=VideoContext,
        checkpointer=checkpointer,
        name="video_assistant",
    )
