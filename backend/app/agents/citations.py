"""Citation validation. The model may only reference chunk IDs; timestamps and text always
come from retrieval results, never from the model's output."""

import re
from collections.abc import Iterable
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, ToolMessage

SEARCH_TOOL_NAME = "search_video_transcript"
# Models sometimes nest or merge brackets: [[a_1]], [[a_1, a_2]], [[a_1], [a_2]], [a_1].
# A marker is a bracketed run made only of chunk-ID-shaped tokens and separators.
_ID = r"[A-Za-z0-9_-]*_\d+"
_MARKER_RE = re.compile(rf"\[+\s*{_ID}(?:[\s,;\[\]]+{_ID})*\s*\]+|\[\[[^\[\]]*\]\]")
_TOKEN_RE = re.compile(r"[A-Za-z0-9_-]+")


def collect_evidence(messages: Iterable[BaseMessage], video_id: str) -> dict[str, dict[str, Any]]:
    """Chunks actually returned by the retrieval tool in this thread, for the active video."""
    evidence: dict[str, dict[str, Any]] = {}
    for message in messages:
        if not isinstance(message, ToolMessage) or message.name != SEARCH_TOOL_NAME:
            continue
        artifact = message.artifact if isinstance(message.artifact, dict) else {}
        chunks = artifact.get("structured_content", {}).get("chunks", [])
        for chunk in chunks:
            if chunk.get("video_id") == video_id and chunk.get("chunk_id"):
                evidence[chunk["chunk_id"]] = chunk
    return evidence


def rewrite_markers(text: str, evidence: dict[str, Any]) -> tuple[str, list[str]]:
    """Drop markers that reference unknown chunks; return cleaned text and cited IDs in order."""
    cited: list[str] = []

    def replace(match: re.Match[str]) -> str:
        ids = _TOKEN_RE.findall(match.group(0))
        valid = [i for i in ids if i in evidence]
        cited.extend(i for i in valid if i not in cited)
        return "".join(f"[[{i}]]" for i in valid)

    return _MARKER_RE.sub(replace, text), cited


def attach_citations(message: AIMessage, evidence: dict[str, dict[str, Any]]) -> AIMessage:
    """Return a copy of `message` with validated citations in `additional_kwargs`."""
    cited: list[str] = []

    def clean(text: str) -> str:
        cleaned, ids = rewrite_markers(text, evidence)
        cited.extend(i for i in ids if i not in cited)
        return cleaned

    content = message.content
    if isinstance(content, str):
        content = clean(content)
    else:
        content = [
            {**block, "text": clean(block["text"])}
            if isinstance(block, dict) and block.get("type") == "text" and "text" in block
            else block
            for block in content
        ]

    citations = [
        {
            key: evidence[i][key]
            for key in ("chunk_id", "video_id", "start_time", "end_time", "text")
        }
        for i in cited
    ]
    return message.model_copy(
        update={
            "content": content,
            "additional_kwargs": {**message.additional_kwargs, "citations": citations},
        }
    )
