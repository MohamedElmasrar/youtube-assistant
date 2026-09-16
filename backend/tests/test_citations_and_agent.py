"""Citation validation and a full agent run with a fake model (no network, no API key)."""

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import StructuredTool
from langgraph.checkpoint.memory import InMemorySaver

from app.agents.citations import attach_citations, collect_evidence, rewrite_markers
from app.agents.context import VideoContext
from app.agents.video_agent import build_video_agent

VID = "aaaaaaaaaaa"
OTHER = "bbbbbbbbbbb"
CHUNK = {
    "chunk_id": f"{VID}_5",
    "video_id": VID,
    "start_time": 120.5,
    "end_time": 154.8,
    "text": "Attention weighs tokens.",
}


def search_message(chunks, name="search_video_transcript"):
    return ToolMessage(
        content="...",
        name=name,
        tool_call_id="t1",
        artifact={"structured_content": {"chunks": chunks}},
    )


def test_collect_evidence_only_trusts_search_results_for_the_active_video():
    foreign = {**CHUNK, "video_id": OTHER, "chunk_id": f"{OTHER}_1"}
    messages = [
        search_message([CHUNK, foreign]),
        search_message([{**CHUNK, "chunk_id": "x"}], "other"),
    ]
    assert list(collect_evidence(messages, VID)) == [f"{VID}_5"]


def test_rewrite_markers_drops_unknown_ids_and_splits_lists():
    evidence = {"a_1": {}, "a_2": {}}
    text, cited = rewrite_markers("One [[a_1]] two [[a_2, fake_9]] three [[fake_1]].", evidence)
    assert text == "One [[a_1]] two [[a_2]] three ."
    assert cited == ["a_1", "a_2"]


def test_rewrite_markers_repairs_nested_and_single_bracket_forms():
    evidence = {"a_2": {}, "a_3": {}}
    text, cited = rewrite_markers(
        "X [[a_2], [a_3]]. Y [a_3]. Z [[a_2], [fake_9]]. W [1].", evidence
    )
    assert text == "X [[a_2]][[a_3]]. Y [[a_3]]. Z [[a_2]]. W [1]."
    assert cited == ["a_2", "a_3"]


def test_attach_citations_uses_retrieved_timestamps_not_model_text():
    message = AIMessage(content=f"It starts at 99:99 [[{VID}_5]] and [[{VID}_404]].", id="m1")
    result = attach_citations(message, {f"{VID}_5": CHUNK})
    assert result.id == "m1"
    (citation,) = result.additional_kwargs["citations"]
    assert citation == CHUNK
    assert f"{VID}_404" not in result.content


def test_attach_citations_handles_block_content():
    message = AIMessage(content=[{"type": "text", "text": f"Yes [[{VID}_5]] [[bad_1]]"}])
    result = attach_citations(message, {f"{VID}_5": CHUNK})
    assert result.content[0]["text"] == f"Yes [[{VID}_5]]"


class ToolCapableFakeModel(GenericFakeChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


def make_agent(replies, *, chunks=(CHUNK,)):
    seen_args = []

    def search(query: str):
        seen_args.append(query)
        return "evidence", {"structured_content": {"chunks": list(chunks)}}

    tool = StructuredTool.from_function(
        search,
        name="search_video_transcript",
        description="search",
        response_format="content_and_artifact",
    )
    model = ToolCapableFakeModel(messages=iter(replies))
    return build_video_agent([tool], model=model, checkpointer=InMemorySaver()), seen_args


def tool_call_reply():
    return AIMessage(
        content="",
        tool_calls=[
            {"name": "search_video_transcript", "args": {"query": "attention"}, "id": "c1"}
        ],
    )


async def ask(agent, question, video_id=VID, thread="t", context=None):
    return await agent.ainvoke(
        {"messages": [HumanMessage(question)]},
        config={"configurable": {"thread_id": thread}},
        context=context if context is not None else VideoContext(video_id=video_id),
    )


async def test_agent_retrieves_answers_and_validates_citations():
    reply = AIMessage(content=f"Attention weighs tokens [[{VID}_5]]. Also [[{VID}_77]].")
    agent, searched = make_agent([tool_call_reply(), reply])
    result = await ask(agent, "What is attention?")
    final = result["messages"][-1]
    assert searched == ["attention"] and result["video_id"] == VID
    assert [c["chunk_id"] for c in final.additional_kwargs["citations"]] == [f"{VID}_5"]
    assert f"{VID}_77" not in final.content


async def test_follow_up_reuses_thread_state():
    agent, _ = make_agent(
        [tool_call_reply(), AIMessage(content="first"), AIMessage(content="second")]
    )
    await ask(agent, "one")
    result = await ask(agent, "two")
    assert [m.type for m in result["messages"]].count("human") == 2


async def test_thread_cannot_switch_to_another_video():
    agent, _ = make_agent([AIMessage(content="ok"), AIMessage(content="never")])
    await ask(agent, "hello", video_id=VID)
    with pytest.raises(ValueError, match="different video"):
        await ask(agent, "hello again", video_id=OTHER)


async def test_run_without_valid_video_context_is_rejected():
    agent, _ = make_agent([AIMessage(content="never")])
    with pytest.raises(ValueError, match="video_id"):
        await ask(agent, "hi", video_id="../../etc")


async def test_missing_context_gives_a_clear_error_not_a_type_error():
    agent, _ = make_agent([AIMessage(content="never")])
    with pytest.raises(ValueError, match="No video selected"):
        await ask(agent, "hi", context=VideoContext())


def test_video_id_is_not_part_of_the_input_schema():
    agent, _ = make_agent([])
    assert "video_id" not in agent.get_input_jsonschema()["properties"]
    assert "video_id" in agent.get_output_jsonschema()["properties"]


async def test_citations_from_another_threads_video_are_not_accepted():
    foreign = {**CHUNK, "video_id": OTHER, "chunk_id": f"{OTHER}_5"}
    reply = AIMessage(content=f"Claim [[{OTHER}_5]].")
    agent, _ = make_agent([tool_call_reply(), reply], chunks=(foreign,))
    result = await ask(agent, "q")
    assert result["messages"][-1].additional_kwargs["citations"] == []


async def test_failed_llm_call_surfaces_as_an_error():
    class Exploding(ToolCapableFakeModel):
        def _generate(self, *args, **kwargs):
            raise RuntimeError("llm down")

    agent = build_video_agent([], model=Exploding(messages=iter([])), checkpointer=InMemorySaver())
    with pytest.raises(RuntimeError, match="llm down"):
        await ask(agent, "hi")
