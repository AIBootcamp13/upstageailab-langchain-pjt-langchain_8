import chainlit as cl
from chainlit.element import Text
from chainlit.sidebar import ElementSidebar


@cl.action_callback("toggle_tokens")
async def toggle_tokens(action: cl.Action):
    """Toggle the token usage sidebar: open if closed, close if open.

    We persist a boolean flag in `cl.user_session['token_panel_open']` so the handler
    can close the panel when it's already open.
    """
    session_id = cl.user_session.get("session_id")
    if not session_id:
        # Nothing we can do without a session id
        return

    # Read current open flag (default False)
    open_flag = cl.user_session.get("token_panel_open") or False

    try:
        from src.tokens import format_usage_summary

        if open_flag:
            # Close by clearing elements
            await ElementSidebar.set_title("Session Tokens")
            await ElementSidebar.set_elements([])
            # Opening the sidebar with empty elements will effectively hide content
            await ElementSidebar.open()
            cl.user_session.set("token_panel_open", False)
            return

        # Otherwise open and populate
        token_summary = format_usage_summary(session_id)
        sidebar_text = Text(content=f"📊 **세션 토큰 사용량**\n\n---\n\n{token_summary}")
        await ElementSidebar.set_title("Session Tokens")
        await ElementSidebar.set_elements([sidebar_text])
        await ElementSidebar.open()
        cl.user_session.set("token_panel_open", True)

    except Exception:
        # If anything fails, send a small notification in chat
        await cl.Message(content="토큰 패널을 열 수 없습니다.").send()



@cl.action_callback("show_telemetry_button")
async def show_telemetry_button(action: cl.Action):
    """Place a button in the sidebar that triggers telemetry export."""
    try:
        # The chainlit public API exposes action buttons via cl.Action in chat messages.
        # Sidebar elements accept visual elements (Text, etc.) but not action Buttons directly
        # so we place an instructional text in the sidebar and send an in-chat Action button
        sidebar_text = Text(content="📦 Telemetry\n\nClick the 'Export Telemetry' button in chat to save session telemetry.")
        await ElementSidebar.set_title("Telemetry")
        await ElementSidebar.set_elements([sidebar_text])
        await ElementSidebar.open()

        actions = [cl.Action(name="export_telemetry", payload={}, label="Export Telemetry")]
        await cl.Message(content="Export telemetry for this session:", actions=actions).send()
    except Exception:
        await cl.Message(content="Could not place telemetry button in the sidebar.").send()
