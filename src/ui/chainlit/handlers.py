# src/ui/chainlit/handlers.py

import uuid
from typing import List
import chainlit as cl

from src.ui.chainlit.settings import setup_settings, PROVIDER_LABELS
from src.ui.chainlit.icons import PROVIDER_ICONS
from src.agent import BlogContentAgent
from src.config import CONFIG, DEFAULT_PROFILE
from src.ui.chainlit.utils import setup_agent, ingest_documents
from src.ui.enums import SessionKey

@cl.on_chat_start
async def on_chat_start():
    """Called when a new chat session starts."""
    session_id = str(uuid.uuid4())
    cl.user_session.set(SessionKey.SESSION_ID, session_id)

    # Get the selected chat profile and extract provider info
    selected_profile = cl.user_session.get("chat_profile")
    
    # Safely handle profile selection
    if selected_profile:
        # Parse the profile name to extract provider
        # Format: "emoji ProviderName" (e.g., "🤖 OpenAI", "🐏 Ollama", "🚀 Upstage")
        provider_key = None
        for key, display in PROVIDER_LABELS.items():
            if display in selected_profile:
                provider_key = key
                break
        
        if provider_key:
            # Get the first available model for this provider
            providers = CONFIG.get("llm_providers", {})
            models = providers.get(provider_key, [])
            default_model = models[0] if models else ""
            
            cl.user_session.set("llm_provider", provider_key)
            cl.user_session.set("llm_model", default_model)
            cl.user_session.set("agent_profile", "draft")  # Default to draft agent
        
        cl.user_session.set("last_profile", selected_profile)

    # The settings panel will be set up once after initializing session values
    await setup_settings()

async def process_initial_draft(agent: BlogContentAgent, session_id: str):
    """Generates and streams the initial draft to the UI."""
    draft = await cl.make_async(agent.generate_draft)(session_id=session_id)
    cl.user_session.set(SessionKey.BLOG_DRAFT, draft)

    draft_msg = cl.Message(content="", author="🤖 BlogGenerator")
    await draft_msg.send()
    # Remember the preview message id so inline editor submissions can update it
    cl.user_session.set("preview_message_id", draft_msg.id)
    
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
            cl.Action(name="save_draft", payload={"value": "save"}, label="💾 Save Draft"),
            cl.Action(name="view_markdown", payload={"value": "view"}, label="📋 View Markdown"),
            cl.Action(name="open_inline_editor", payload={"message_id": draft_msg.id}, label="✏️ Edit"),
            cl.Action(name="toggle_tokens", payload={"value": "toggle"}, label="📊 Show Tokens"),
            cl.Action(name="list_artifacts", payload={"value": "list"}, label="📄 List Artifacts"),
            # cl.Action(name="publish_post", payload={"value": "publish"}, label="🚀 Publish Post"),
        ],
    ).send()

@cl.on_message
async def on_message(message: cl.Message):
    """Called when a user sends a message or uploads a file."""
    # Check if profile changed
    current_profile = cl.user_session.get("chat_profile")
    last_profile = cl.user_session.get("last_profile")
    if current_profile and current_profile != last_profile:
        # Profile changed
        cl.user_session.set("last_profile", current_profile)
        # Parse provider
        provider_key = None
        for key, display in PROVIDER_LABELS.items():
            if display in current_profile:
                provider_key = key
                break
        if provider_key:
            providers = CONFIG.get("llm_providers", {})
            models = providers.get(provider_key, [])
            default_model = models[0] if models else ""
            cl.user_session.set("llm_provider", provider_key)
            cl.user_session.set("llm_model", default_model)
            await setup_settings()
            # Provider changed - settings updated automatically
    
    session_id = cl.user_session.get(SessionKey.SESSION_ID)
    agent: BlogContentAgent = cl.user_session.get(SessionKey.BLOG_CREATOR_AGENT)
    # Manual edit fallback: if user clicked "Edit by sending message" the next
    # user message should be treated as the edited draft and not routed to the agent.
    expect_manual = cl.user_session.get("expect_manual_edit", False)
    if expect_manual:
        # Reset the flag first to avoid re-entrancy
        cl.user_session.set("expect_manual_edit", False)
        # Extract text content from the message
        edited_text = getattr(message, "content", "") or ""
        if not isinstance(edited_text, str) or not edited_text.strip():
            await cl.Message(content="No text received. Please send the edited draft as a chat message.").send()
            return
        # Persist edited draft in session
        cl.user_session.set(SessionKey.BLOG_DRAFT, edited_text.strip())
        # Update preview if available
        preview_msg_id = cl.user_session.get("preview_message_id")
        if preview_msg_id:
            msg = cl.Message(id=preview_msg_id)
            # Set fields on the Message object and call update() without kwargs
            msg.content = "📄 Live Preview"
            msg.elements = [cl.Text(content=edited_text.strip(), language="markdown", name="markdown_preview")]
            await msg.update()
        # Show a confirmation with helpful follow-up actions attached to the preview
        await cl.Message(
            content="✅ Draft updated from your message.",
            parent_id=preview_msg_id,
            actions=[
                cl.Action(name="save_draft", payload={"value": "save"}, label="💾 Save Draft"),
                cl.Action(name="view_markdown", payload={"value": "view"}, label="📋 View Markdown"),
                cl.Action(name="open_inline_editor", payload={"message_id": preview_msg_id}, label="✏️ Edit"),
            ],
        ).send()
        return
    
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
        agent = await setup_agent(llm_provider, llm_model, cl.user_session.get("agent_profile", "draft"))

        if not agent:
            await cl.Message(content="Failed to initialize the agent. Please try again.").send()
            return
            
        # 3. Generate and stream the initial draft
        await process_initial_draft(agent, session_id)
        return

    # If agent exists, process the user's text message to update the draft
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
        # Keep track of the preview message for inline edits
        cl.user_session.set("preview_message_id", draft_msg.id)
        await draft_msg.update()
        await cl.Message(
            content="✅ Draft has been updated.",
            actions=[
                cl.Action(name="save_draft", payload={"value": "save"}, label="💾 Save Draft"),
                cl.Action(name="view_markdown", payload={"value": "view"}, label="📋 View Markdown"),
                cl.Action(name="open_inline_editor", payload={"message_id": draft_msg.id}, label="✏️ Edit"),
                cl.Action(name="toggle_tokens", payload={"value": "toggle"}, label="📊 Show Tokens"),
                # cl.Action(name="publish_post", payload={"value": "publish"}, label="🚀 Publish Post"),
            ],
        ).send()

    if chat_started:
        await chat_msg.update()