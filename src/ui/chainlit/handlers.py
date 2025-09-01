# src/ui/chainlit/handlers.py

import uuid
from typing import List
import chainlit as cl
# from chainlit.types import File

from src.agent import BlogContentAgent
from src.config import CONFIG, DEFAULT_PROFILE
from src.ui.chainlit.utils import setup_agent, ingest_documents
from src.ui.enums import SessionKey

@cl.on_chat_start
async def on_chat_start():
    """Called when a new chat session starts."""
    session_id = str(uuid.uuid4())
    cl.user_session.set(SessionKey.SESSION_ID, session_id)

    try:
        from src.ui.chainlit.settings import setup_settings
        await setup_settings()
    except Exception:
        pass # Settings setup is optional

    # Guide the user on how to start
    await cl.Message(
        content="Welcome to the Blog Post Generator! Please upload a PDF, Markdown, or Python file to begin."
    ).send()

async def process_initial_draft(agent: BlogContentAgent, session_id: str):
    """Generates and streams the initial draft to the UI."""
    draft = await cl.make_async(agent.generate_draft)(session_id=session_id)
    cl.user_session.set(SessionKey.BLOG_DRAFT, draft)

    draft_msg = cl.Message(content="", author="BlogGenerator")
    await draft_msg.send()
    
    # Stream the draft content
    chunk_size = 10
    for i in range(0, len(draft), chunk_size):
        part = draft[i : i + chunk_size]
        await draft_msg.stream_token(part)
    await draft_msg.update()

    # Send a follow-up message with actions
    await cl.Message(
        content="Initial draft generated! How would you like to refine it?",
        parent_id=draft_msg.id,
        actions=[
            cl.Action(name="edit_draft", payload={"value": "edit"}, label="📝 Edit Draft"),
            cl.Action(name="save_draft", payload={"value": "save"}, label="💾 Save Draft"),
            cl.Action(name="toggle_tokens", payload={"value": "toggle"}, label="📊 Show Tokens"),
            cl.Action(name="list_artifacts", payload={"value": "list"}, label="📄 List Artifacts"),
        ],
    ).send()

@cl.on_message
async def on_message(message: cl.Message):
    """Called when a user sends a message or uploads a file."""
    session_id = cl.user_session.get(SessionKey.SESSION_ID)
    agent: BlogContentAgent = cl.user_session.get(SessionKey.BLOG_CREATOR_AGENT)
    
    # Check for file uploads if the agent has not been initialized yet
    if not agent:
        # --- OLD CODE (PDF ONLY) ---
        # pdf_files = [file for file in message.elements if "pdf" in file.mime]
        # if not pdf_files:
        #     await cl.Message(content="Please upload a PDF file to start.").send()
        #     return

        uploaded_files = [
            file for file in message.elements if isinstance(file, cl.File)
        ]
        if not uploaded_files:
            await cl.Message(content="To begin, please upload a document (PDF, MD, PY, etc.).").send()
            return

        ingestion_successful = await ingest_documents(uploaded_files)            
        # 1. Ingest documents from the uploaded file(s)
        # ingestion_successful = await ingest_documents(pdf_files)
        if not ingestion_successful:
            return # Ingestion failed, user was notified.

        # 2. Setup the agent with the default model
        # Use the configured DEFAULT_PROFILE from configs/config.yaml to avoid
        # unintentionally falling back to an external API provider.
        default_profile_cfg = CONFIG.get("profiles", {}).get(DEFAULT_PROFILE, {})
        llm_provider = cl.user_session.get("llm_provider") or default_profile_cfg.get("llm_provider")
        llm_model = cl.user_session.get("llm_model") or default_profile_cfg.get("llm_model")
        agent = await setup_agent(llm_provider, llm_model)

        if not agent:
            await cl.Message(content="Failed to initialize the agent. Please try again.").send()
            return
            
        # 3. Generate and stream the initial draft
        await process_initial_draft(agent, session_id)
        return

    # If agent exists, process the user's text message to update the draft
    draft = cl.user_session.get(SessionKey.BLOG_DRAFT, "")
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
            content="✅ Draft has been updated.",
            actions=[
                cl.Action(name="edit_draft", payload={"value": "edit"}, label="📝 Edit Draft"),
                cl.Action(name="save_draft", payload={"value": "save"}, label="💾 Save Draft"),
                cl.Action(name="toggle_tokens", payload={"value": "toggle"}, label="📊 Show Tokens"),
            ],
        ).send()

    if chat_started:
        await chat_msg.update()