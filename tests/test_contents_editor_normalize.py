import json

from src.ui.components.contents_editor import ContentsEditor


def test_normalize_plain_markdown():
    editor = ContentsEditor()
    raw = "# Title\n\nSome content"
    assert editor._normalize_markdown(raw) == raw


def test_normalize_json_string():
    editor = ContentsEditor()
    inner = "# Title\n\nSome content"
    raw = json.dumps(inner)
    assert editor._normalize_markdown(raw) == inner


def test_normalize_json_object_with_content():
    editor = ContentsEditor()
    payload = {"content": "# Title\n\nSome content", "type": "draft"}
    raw = json.dumps(payload)
    assert editor._normalize_markdown(raw) == payload["content"]


def test_normalize_wrapped_quotes():
    editor = ContentsEditor()
    raw = '"# Title\\n\\nSome content"'
    assert editor._normalize_markdown(raw) == "# Title\n\nSome content"
