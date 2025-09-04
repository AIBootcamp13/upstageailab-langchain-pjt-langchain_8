# In src/ui/chainlit/handlers.py

@cl.on_message
async def on_message(message: cl.Message):
    """
    사용자 메시지 또는 파일 업로드 시 호출됩니다.
    이제 파일 업로드를 항상 최우선으로 처리합니다.
    """
    session_id = cl.user_session.get(SessionKey.SESSION_ID)
    
    # 1. 메시지에 파일이 포함되어 있는지 먼저 확인합니다.
    uploaded_files = [
        file for file in message.elements if isinstance(file, cl.File)
    ]

    if uploaded_files:
        # 파일이 있는 경우, 항상 새로 문서를 처리하고 에이전트를 설정합니다.
        # 이것은 세션 중간에 새로운 소스 파일로 작업을 다시 시작할 수 있게 합니다.
        ingestion_successful = await ingest_documents(uploaded_files)
        if not ingestion_successful:
            return  # Ingestion failed, user was notified.

        # 현재 UI 설정에 따라 에이전트를 설정합니다.
        default_profile_cfg = CONFIG.get("profiles", {}).get(DEFAULT_PROFILE, {})
        llm_provider = cl.user_session.get("llm_provider") or default_profile_cfg.get("llm_provider")
        llm_model = cl.user_session.get("llm_model") or default_profile_cfg.get("llm_model")
        agent = await setup_agent(llm_provider, llm_model, cl.user_session.get("agent_profile", "draft"))

        if not agent:
            await cl.Message(content="Failed to initialize the agent. Please try again.").send()
            return
            
        # 새로운 문서로부터 초기 초안을 생성하고 스트리밍합니다.
        await process_initial_draft(agent, session_id)
        return

    # 2. 파일이 없는 경우, 기존의 텍스트 메시지 처리 로직을 실행합니다.
    agent: BlogContentAgent = cl.user_session.get(SessionKey.BLOG_CREATOR_AGENT)
    if not agent:
        # 에이전트가 없고 텍스트 메시지만 있는 경우 사용자에게 파일을 먼저 업로드하도록 안내합니다.
        await cl.Message(content="To begin, please upload a source document (e.g., PDF, .png, .mp3).").send()
        return

    # 기존 에이전트가 있는 경우, 텍스트 메시지를 사용하여 초안을 업데이트합니다.
    draft = cl.user_session.get(SessionKey.BLOG_DRAFT, "")
    draft_msg = cl.Message(content="", author="📝 Draft")
    chat_msg = cl.Message(content="", author="🤖 BlogGenerator")
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
        cl.user_session.set("preview_message_id", draft_msg.id)
        await draft_msg.update()
        await cl.Message(
            content="✅ Draft has been updated.",
            actions=[
                cl.Action(name="save_draft", payload={"value": "save"}, label="💾 Save Draft"),
                cl.Action(name="view_markdown", payload={"value": "view"}, label="📋 View Markdown"),
                cl.Action(name="open_inline_editor", payload={"message_id": draft_msg.id}, label="✏️ Edit"),
                cl.Action(name="toggle_tokens", payload={"value": "toggle"}, label="📊 Show Tokens"),
            ],
        ).send()

    if chat_started:
        await chat_msg.update()
        if not draft_updated:
            await cl.Message(
                content="✅ Draft presented. How would you like to proceed?",
                parent_id=chat_msg.id,
                actions=[
                    cl.Action(name="save_draft", payload={"value": "save"}, label="💾 Save Draft"),
                    cl.Action(name="view_markdown", payload={"value": "view"}, label="📋 View Markdown"),
                    cl.Action(name="open_inline_editor", payload={"message_id": chat_msg.id}, label="✏️ Edit"),
                    cl.Action(name="toggle_tokens", payload={"value": "toggle"}, label="📊 Show Tokens"),
                ],
            ).send()