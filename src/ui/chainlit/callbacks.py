# src/ui/chainlit/callbacks.py

import chainlit as cl
import chainlit.input_widget as iw

from src.artifacts import list_artifacts, save_artifact
from src.ui.enums import SessionKey


@cl.action_callback("edit_draft")
async def on_edit_draft(action: cl.Action):
    """'Edit Draft' action: open the editor in the Settings panel (reliable in 2.x)."""
    # Switch settings panel to Editing mode and re-render it so DraftEditor appears.
    cl.user_session.set("OperationMode", "edit")
    try:
        from src.ui.chainlit.settings import setup_settings
        await setup_settings()
        await cl.Message(
            content=(
                "Opened the editor in the Settings panel (top). Edit your draft in '📝 Draft Editor'."
            )
        ).send()
    except Exception as e:
        print(f"edit_draft: failed to open settings editor: {e}")
        # Fallback: ask the user to paste the updated markdown
        ask = cl.AskUserMessage(
            content=(
                "Your environment doesn't support the inline editor. Please paste your updated markdown below and send."
            ),
            timeout=300,
        )
        await ask.send()


@cl.action_callback("save_draft")
async def on_save_draft(action: cl.Action):
    """'Save Draft' action callback."""
    session_id = cl.user_session.get(SessionKey.SESSION_ID)
    draft = cl.user_session.get(SessionKey.BLOG_DRAFT, "")
    if not draft:
        await cl.Message(content="There is no draft to save.").send()
        return
    artifact = save_artifact(session_id, "blog-draft", draft, kind="draft", ext="md")
    await cl.Message(content=f"✅ Draft saved as an artifact:\n`{artifact.file_path}`").send()


@cl.action_callback("list_artifacts")
async def on_list_artifacts(action: cl.Action):
    """'List Artifacts' action callback."""
    session_id = cl.user_session.get(SessionKey.SESSION_ID)
    artifacts = list_artifacts(session_id)
    if not artifacts:
        await cl.Message(content="No artifacts have been saved yet.").send()
        return
    elements = [
        cl.Text(
            name=a.file_path.name,
            content=f"Type: {a.kind}, Size: {a.size} bytes\nCreated: {a.created_at}",
            # The display="inline" parameter has been removed for compatibility
        )
        for a in artifacts
    ]
    await cl.Message(content="**List of Generated Artifacts:**", elements=elements).send()


@cl.action_callback("submit_inline_editor")
async def on_submit_inline_editor(action: cl.Action):
    """Handle submit from the inline TextInput editor."""
    payload = getattr(action, "payload", {}) or {}
    new_draft = None

    # Try common payload shapes
    # 1) direct key
    if "editor" in payload and isinstance(payload["editor"], str):
        new_draft = payload["editor"]

    # 2) provided editor_id points to a value in payload
    if new_draft is None:
        editor_id = payload.get("editor_id")
        if editor_id and isinstance(editor_id, str):
            v = payload.get(editor_id)
            if isinstance(v, str) and v.strip():
                new_draft = v

    # 3) nested dicts
    if new_draft is None:
        for v in payload.values():
            if isinstance(v, str) and v.strip():
                new_draft = v
                break
            if isinstance(v, dict):
                for vv in v.values():
                    if isinstance(vv, str) and vv.strip():
                        new_draft = vv
                        break
                if new_draft:
                    break

    # 4) fallback 'value'
    if new_draft is None:
        v = payload.get("value")
        if isinstance(v, str) and v.strip():
            new_draft = v

    if new_draft:
        cl.user_session.set(SessionKey.BLOG_DRAFT, new_draft)
        await cl.Message(
            content="✅ Draft updated successfully from the inline editor.",
            actions=[
                cl.Action(name="save_draft", payload={"value": "save"}, label="💾 Save Updated Draft")
            ],
        ).send()
    else:
        # Fallback to paste-based AskUserMessage for environments not sending payloads.
        ask = cl.AskUserMessage(
            content=(
                "Couldn't read the inline editor submission. Please paste your updated markdown here and send."
            ),
            timeout=300,
        )
        resp = await ask.send()
        content = None
        if isinstance(resp, dict):
            content = resp.get("content")
        if not content:
            content = getattr(resp, "content", None)

        if isinstance(content, str) and content.strip():
            cl.user_session.set(SessionKey.BLOG_DRAFT, content)
            await cl.Message(
                content="✅ Draft updated from pasted content.",
                actions=[
                    cl.Action(name="save_draft", payload={"value": "save"}, label="💾 Save Updated Draft")
                ],
            ).send()
        else:
            await cl.Message(content="No content received. Please try editing again.").send()