# src/ui/chainlit/handlers.py

import uuid

import chainlit as cl

from src.agent import BlogContentAgent
from src.config import CONFIG
from src.tokens import format_usage_summary
from chainlit.element import Text
from chainlit.sidebar import ElementSidebar
from src.ui.chainlit.utils import setup_agent
from src.ui.enums import SessionKey

# 사용자 친화적인 레이블을 정의합니다.
PROFILE_LABELS = {
    "default_cpu": "Default (CPU)",
    "high_gpu": "High Performance (GPU)",
}

@cl.on_chat_start
async def on_chat_start():
    """채팅 세션이 시작될 때 호출됩니다."""
    session_id = str(uuid.uuid4())
    cl.user_session.set(SessionKey.SESSION_ID, session_id)
    # Ensure settings widget is registered in the UI for this chat/thread
    try:
        from src.ui.chainlit.settings import setup_settings

        await setup_settings()
    except Exception:
        pass

    # UX change: don't present profile options as a chat response.
    # Instead, guide the user to use the settings panel (top-right) to pick a model profile.
    await cl.Message(content="시작하려면 오른쪽 상단의 설정(⚙️)에서 모델 프로필을 선택하세요. 기본 프로필이 자동으로 적용됩니다.").send()

    # Load provider/model from session (set by settings or fallback to config default)
    llm_provider = cl.user_session.get("llm_provider") or CONFIG["profiles"]["default_cpu"]["llm_provider"]
    llm_model = cl.user_session.get("llm_model") or CONFIG["profiles"]["default_cpu"]["llm_model"]

    cl.user_session.set("llm_provider", llm_provider)
    cl.user_session.set("llm_model", llm_model)
    agent = await setup_agent(llm_provider, llm_model)

    if agent is None:
        await cl.Message(content="파일이 업로드되지 않았습니다. 페이지를 새로고침하여 다시 시도해주세요.").send()
        return

    # 초기 초안 생성 및 스트리밍 출력 (문자 단위 혹은 작은 청크)
    draft = await cl.make_async(agent.generate_draft)(session_id=session_id)
    cl.user_session.set(SessionKey.BLOG_DRAFT, draft)

    draft_msg = cl.Message(content="", author="BlogGenerator")
    await draft_msg.send()
    # Stream in small character chunks for a 'typing' effect
    chunk_size = 8
    for i in range(0, len(draft), chunk_size):
        part = draft[i : i + chunk_size]
        await draft_msg.stream_token(part)
    await draft_msg.update()
    await cl.Message(
        content="이제 초안을 어떻게 수정하고 싶으신가요? 자유롭게 요청해주세요.",
        actions=[cl.Action(name="toggle_tokens", payload={"value": "toggle"}, label="📊 토큰 보기")],
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """사용자로부터 메시지를 받았을 때 호출됩니다."""
    session_id = cl.user_session.get(SessionKey.SESSION_ID)
    agent: BlogContentAgent = cl.user_session.get(SessionKey.BLOG_CREATOR_AGENT)
    draft = cl.user_session.get(SessionKey.BLOG_DRAFT, "")

    if not agent:
        await cl.Message(content="에이전트가 초기화되지 않았습니다.").send()
        return

    draft_msg = cl.Message(content="", author="Draft")
    chat_msg = cl.Message(content="", author="BlogGenerator")

    stream = agent.get_response(message.content, draft, session_id)

    draft_updated = False
    chat_started = False

    for chunk in stream:
        chunk_type = chunk.get("type")
        content = chunk.get("content", "")

        if chunk_type == "draft":
            if not draft_updated:
                await draft_msg.send()
                draft_updated = True
            await draft_msg.stream_token(content)
        elif chunk_type == "chat":
            if not chat_started:
                await chat_msg.send()
                chat_started = True
            await chat_msg.stream_token(content)

    if draft_updated:
        cl.user_session.set(SessionKey.BLOG_DRAFT, draft_msg.content)
        await draft_msg.update()
        await cl.Message(
            content="✅ 초안이 수정되었습니다.",
            actions=[
                cl.Action(name="save_draft", payload={"value": "save"}, label="💾 초안 저장"),
                cl.Action(name="toggle_tokens", payload={"value": "toggle"}, label="📊 토큰 보기"),
            ],
        ).send()

    if chat_started:
        await chat_msg.update()

    # Update token summary in the sidebar instead of sending it in the chat
    token_summary = format_usage_summary(session_id)
    sidebar_text = Text(content=f"📊 **세션 토큰 사용량**\n\n---\n\n{token_summary}")
    await ElementSidebar.set_title("Session Tokens")
    await ElementSidebar.set_elements([sidebar_text])