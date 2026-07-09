from pathlib import Path


def test_default_prompt_buttons_call_send_handler():
    source = (Path(__file__).parents[2] / "src/pages/CommandCenterPage.tsx").read_text()
    assert "onClick={()=>onPrompt(prompt)}" in source
    assert "<EmptyCommandCenter onPrompt={send}/>" in source


def test_default_prompt_copy_matches_real_chat_prompts():
    source = (Path(__file__).parents[2] / "src/pages/CommandCenterPage.tsx").read_text()
    assert "'Show customers'" in source
    assert "'Show sales invoices'" in source
    assert "'Show stock balance'" in source
