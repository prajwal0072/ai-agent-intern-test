from app.llm import CHAT_MODEL, SYSTEM_PROMPT


def test_chat_model_is_configured():
    assert CHAT_MODEL


def test_system_prompt_contains_safety_rules():
    assert "untrusted" in SYSTEM_PROMPT
    assert "Never invent" in SYSTEM_PROMPT
    assert "system prompts" in SYSTEM_PROMPT
    assert "internal notes" in SYSTEM_PROMPT