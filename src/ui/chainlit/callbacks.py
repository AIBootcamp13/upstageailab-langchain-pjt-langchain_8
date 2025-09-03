# src/ui/chainlit/callbacks.py

import chainlit as cl
import chainlit.input_widget as iw
import uuid
from src.ui.components.publisher import Publisher
from github import Github, GithubException
from datetime import datetime
from datetime import timedelta
import html
from src.ui.enums import SessionKey
from src.artifacts import save_artifact, list_artifacts
import json
import _uuid
from enum import Enum


@cl.action_callback("toggle_markdown_format")
async def on_toggle_markdown_format(action: cl.Action):
    """Toggle the format of a previously sent markdown display message."""
    # For stability across different Chainlit versions we enforce markdown-only views.
    await cl.Message(content="ℹ️ Markdown-only view is enforced — plain-text toggle disabled.").send()


@cl.action_callback("copy_instructions")
async def on_copy_instructions(action: cl.Action):
    """Provide detailed instructions for copying the markdown content."""
    await cl.Message(
        content="📋 **​How to Copy the Markdown Content:​**\n\n" +
                "**​Desktop/Laptop:​**\n" +
                "1. Click inside the gray text block above\n" +
                "2. Press `Ctrl+A` (Windows/Linux) or `Cmd+A` (Mac) to select all\n" +
                "3. Press `Ctrl+C` (Windows/Linux) or `Cmd+C` (Mac) to copy\n\n" +
                "**​Mobile:​**\n" +
                "1. Long press on the text block above\n" +
                "2. Tap 'Select All' from the menu\n" +
                "3. Tap 'Copy' from the menu\n\n" +
                "**​Alternative:​**\n" +
                "• You can also manually select text by clicking and dragging\n" +
                "• The content is now in your clipboard and ready to paste!"
    ).send()


@cl.action_callback("copy_to_clipboard")
async def on_copy_to_clipboard(action: cl.Action):
    """Legacy callback - redirect to copy instructions."""
    await on_copy_instructions(action)


@cl.action_callback("hide_markdown")
async def on_hide_markdown(action: cl.Action):
    """Legacy callback - no longer needed since we can't actually hide messages."""
    await cl.Message(content=" The markdown content will remain visible above for easy copying. You can continue with other actions.").send()


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
        )
        for a in artifacts
    ]
    await cl.Message(content="**​List of Generated Artifacts:​**", elements=elements).send()


@cl.action_callback("submit_inline_editor")
async def on_submit_inline_editor(action: cl.Action):
    """Handle submit from the inline TextInput editor."""
    payload = getattr(action, "payload", {}) or {}

    # Directly extract the editor content (most reliable path)
    new_draft = payload.get("editor")

    if isinstance(new_draft, str) and new_draft.strip():
        cl.user_session.set(SessionKey.BLOG_DRAFT, new_draft.strip())
        # Update preview on submit as well
        preview_msg_id = cl.user_session.get("preview_message_id")
        if preview_msg_id:
            # Some Chainlit Message constructors require a content argument;
            # pass an empty content when referencing by id so .update() works.
            msg = cl.Message(id=preview_msg_id)
            msg.content = "📄 Live Preview"
            msg.elements = [cl.Text(content=new_draft.strip(), language="markdown", name="markdown_preview")]
            await msg.update()
        await cl.Message(
            content="✅ Draft updated successfully from the inline editor.",
            actions=[
                cl.Action(name="save_draft", payload={"value": "save"}, label="💾 Save Updated Draft"),
                cl.Action(name="view_markdown", payload={"value": "view"}, label="📋 View Markdown"),
                cl.Action(name="toggle_tokens", payload={"value": "toggle"}, label="📊 Show Tokens"),
            ],
        ).send()
    else:
        # Fallback for unexpected cases
        await cl.Message(content="No content received. Please try editing again.").send()


@cl.action_callback("view_markdown")
async def on_view_markdown(action: cl.Action):
    """Show the current draft as a markdown page with helper actions."""
    draft = cl.user_session.get(SessionKey.BLOG_DRAFT, "")
    if not draft:
        await cl.Message(content="No draft available to view. Generate a draft first.").send()
        return

    # Send the draft as a markdown-display Text element
    msg = cl.Message(content="📋 Blog Draft (Markdown)", elements=[cl.Text(content=draft, language="markdown", name="draft.md")])
    await msg.send()

    # Provide helper actions that operate on the displayed message
    await cl.Message(
        content="Actions for the markdown view:",
        parent_id=msg.id,
        actions=[
            cl.Action(name="copy_instructions", payload={}, label="📋 How to Copy"),
            cl.Action(name="save_draft", payload={"value": "save"}, label="💾 Save Draft"),
            # Inline edit: open a small editor pre-filled with the draft. The
            # `submit_inline_editor` callback will receive the widget payload
            # (key: `editor`) and persist the change.
            cl.Action(name="open_inline_editor", payload={"message_id": msg.id}, label="✏️ Edit"),
            # cl.Action(name="publish_post", payload={"value": "publish"}, label="🚀 Publish Post"),
        ],
    ).send()



@cl.action_callback("open_inline_editor")
async def on_open_inline_editor(action: cl.Action):
    """Open an inline TextInput editor prefilled with the current draft.

    The existing `submit_inline_editor` callback expects the submitted
    payload to contain the key `editor`. We create a TextInput with id
    `editor` so the submitted payload matches that shape.
    """
    payload = getattr(action, "payload", {}) or {}
    parent_message_id = payload.get("message_id")

    # Fetch current draft (fallback to empty string)
    draft = cl.user_session.get(SessionKey.BLOG_DRAFT, "")

    # Create a TextInput widget. TextInput/TextArea are available on
    # chainlit.input_widget; we imported it as `iw` at the top of this file.
    try:
        editor = iw.TextInput(id="editor", label="Edit Draft", initial_value=draft)
    except Exception:
        # Some Chainlit versions may only provide TextArea - try fallback
        try:
            editor = iw.TextArea(id="editor", label="Edit Draft", initial_value=draft)
        except Exception:
            # As a last resort, do not show a noisy message announcing lack of
            # inline editor support; we prefer the manual-edit action below.
            # await cl.Message(content="Inline editor is not supported by the running Chainlit version.").send()
            return

    # Some Chainlit/input_widget versions expose widget objects that do not
    # implement the `send` coroutine used by Message.send() internals. Avoid
    # passing such objects to `Message(elements=...)` to prevent
    # AttributeError and un-awaited coroutine warnings. If the widget doesn't
    # support `.send`, fall back to a friendly instruction message.
    send_method = getattr(editor, "send", None)
    if callable(send_method):
        await cl.Message(
            content="✏️ Edit the draft below and click Save:",
            parent_id=parent_message_id,
            elements=[editor],
            actions=[cl.Action(name="submit_inline_editor", payload={}, label="💾 Save Updated Draft")],
        ).send()
    else:
        # Offer a manual edit fallback: user can send the edited draft as their
        # next message. We intentionally suppress the explanatory text to keep
        # the UI minimal; the action button below will start the manual edit flow.
        await cl.Message(
            content="",
            parent_id=parent_message_id,
            actions=[cl.Action(name="start_manual_edit", payload={}, label="✏️ Edit by sending message")],
        ).send()


@cl.action_callback("start_manual_edit")
async def on_start_manual_edit(action: cl.Action):
    """Begin a manual edit flow: the next user message will replace the draft.

    This flow is a robust fallback when input widgets are not supported by the
    running Chainlit version.
    """
    cl.user_session.set("expect_manual_edit", True)
    await cl.Message(content="Send your edited draft as a new chat message; it will replace the current draft.").send()


@cl.action_callback("edit_draft")
async def on_edit_draft_alias(action: cl.Action):
    """Alias for `open_inline_editor` so the `edit_draft` action can be used in handlers.

    This keeps the handlers small: both `open_inline_editor` and `edit_draft` now open the
    same inline editor.
    """
    # Reuse the existing open_inline_editor logic
    await on_open_inline_editor(action)


@cl.action_callback("regenerate_draft")
async def on_regenerate_draft(action: cl.Action):
    """Regenerate the draft by invoking the agent's generate_draft and stream the result."""
    session_id = cl.user_session.get(SessionKey.SESSION_ID)
    agent = cl.user_session.get(SessionKey.BLOG_CREATOR_AGENT)
    if not agent:
        await cl.Message(content="No agent available to regenerate the draft. Start a session first.").send()
        return

    # Generate draft (may be async or sync)
    try:
        draft = await cl.make_async(agent.generate_draft)(session_id=session_id)
    except Exception as e:
        await cl.Message(content=f"Failed to regenerate draft: {e!s}").send()
        return

    cl.user_session.set(SessionKey.BLOG_DRAFT, draft)

    draft_msg = cl.Message(content="", author="📝 Draft")
    await draft_msg.send()
    # Stream the regenerated draft
    chunk_size = 10
    for i in range(0, len(draft), chunk_size):
        part = draft[i : i + chunk_size]
        await draft_msg.stream_token(part)
    await draft_msg.update()

    # Send follow-up with actions
    await cl.Message(
        content="Draft regenerated. How would you like to proceed?",
        parent_id=draft_msg.id,
        actions=[
            cl.Action(name="save_draft", payload={"value": "save"}, label="💾 Save Draft"),
            cl.Action(name="view_markdown", payload={"value": "view"}, label="📋 View Markdown"),
            cl.Action(name="toggle_tokens", payload={"value": "toggle"}, label="📊 Show Tokens"),
            cl.Action(name="list_artifacts", payload={"value": "list"}, label="📄 List Artifacts"),
            # cl.Action(name="publish_post", payload={"value": "publish"}, label="🚀 Publish Post"),
        ],
    ).send()



@cl.action_callback("export_telemetry")
async def on_export_telemetry(action: cl.Action):
    """Export recorded message telemetry (SessionKey.MESSAGE_LIST) as a JSON artifact."""
    telemetry = cl.user_session.get(SessionKey.MESSAGE_LIST, []) or []
    if not telemetry:
        await cl.Message(content="ℹ️ No telemetry entries to export.").send()
        return

    # Serialize telemetry to JSON
    try:
        payload = json.dumps(telemetry, ensure_ascii=False, indent=2)
    except Exception:
        payload = json.dumps(telemetry, ensure_ascii=True, indent=2)

    # Ensure session id
    session_id = cl.user_session.get(SessionKey.SESSION_ID)
    if not session_id:
        session_id = str(_uuid.uuid4())
        cl.user_session.set(SessionKey.SESSION_ID, session_id)

    artifact = save_artifact(session_id, "message-telemetry", payload, kind="telemetry", ext="json")
    await cl.Message(content=f"✅ Telemetry exported as artifact:\n`{artifact.file_path}`").send()

