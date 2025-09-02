import chainlit as cl
from chainlit.element import Text
from typing import Optional
from datetime import datetime
from src.ui.enums import SessionKey


def _append_telemetry(entry: dict):
    try:
        lst = cl.user_session.get(SessionKey.MESSAGE_LIST, []) or []
    except Exception:
        # If chainlit context isn't available, skip telemetry silently
        return

    lst.append(entry)
    try:
        cl.user_session.set(SessionKey.MESSAGE_LIST, lst)
    except Exception:
        # best-effort
        pass


def get_message_telemetry():
    try:
        return cl.user_session.get(SessionKey.MESSAGE_LIST, []) or []
    except Exception:
        return []


async def send_preview_message(draft: str):
    """Create and send a preview message containing markdown text and return the Message object.

    This function records a telemetry entry with message id, time and a short content snippet.
    """
    msg = await cl.Message(
        content="📄 Live Preview",
        elements=[Text(content=draft, language="markdown", name="markdown_preview")],
    ).send()

    try:
        _append_telemetry({
            "action": "send_preview",
            "id": getattr(msg, "id", None),
            "time": datetime.utcnow().isoformat(),
            "snippet": (draft[:200] + "...") if draft and len(draft) > 200 else draft,
        })
    except Exception:
        pass

    return msg


async def update_preview_message(message_id: str, new_content: str):
    """Update an existing preview message's content and record telemetry."""
    await cl.Message(id=message_id).update(
        content="📄 Live Preview",
        elements=[Text(content=new_content, language="markdown", name="markdown_preview")],
    )

    try:
        _append_telemetry({
            "action": "update_preview",
            "id": message_id,
            "time": datetime.utcnow().isoformat(),
            "snippet": (new_content[:200] + "...") if new_content and len(new_content) > 200 else new_content,
        })
    except Exception:
        pass


async def send_status(content: str, parent_id: Optional[str] = None):
    msg = cl.Message(content=content, parent_id=parent_id)
    await msg.send()

    try:
        _append_telemetry({
            "action": "status",
            "id": getattr(msg, "id", None),
            "time": datetime.utcnow().isoformat(),
            "content": content,
            "parent_id": parent_id,
        })
    except Exception:
        pass

    return msg
