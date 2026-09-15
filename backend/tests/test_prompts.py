import pytest

from app.agents.prompts import SKILLS, build_system_prompt, select_skills


@pytest.mark.parametrize(
    "question", ["Summarize this video", "give me a tl;dr", "What are the key takeaways?"]
)
def test_summary_requests_load_the_summarization_skill(question):
    assert select_skills(question) == ["grounding", "summarization"]
    assert SKILLS["summarization"] in build_system_prompt(question)


def test_other_questions_load_only_grounding():
    prompt = build_system_prompt("Where does he explain attention?")
    assert SKILLS["grounding"] in prompt and SKILLS["summarization"] not in prompt
    assert "untrusted" in prompt
