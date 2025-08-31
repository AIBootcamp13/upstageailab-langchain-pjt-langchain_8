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
