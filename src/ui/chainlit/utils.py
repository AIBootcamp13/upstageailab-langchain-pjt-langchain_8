# src/ui/chainlit/utils.py

from pathlib import Path
from typing import List
import chainlit as cl
# from chainlit.types import File

from src.agent import BlogContentAgent
from src.document_preprocessor import DocumentPreprocessor
from src.retriever import RetrieverFactory
from src.ui.enums import SessionKey
from src.vector_store import VectorStore


async def ingest_documents(files: List[cl.File]) -> bool:
    """
    Processes uploaded files, creates a vector store, and sets up a retriever.
    """
    if not files:
        return False

    file_names = [file.name for file in files]
    msg = cl.Message(content=f"Processing files: `{'`, `'.join(file_names)}`...")
    await msg.send()

    all_documents = []
    for file in files:
        file_path = Path(file.path)
        try:
            # Each file is processed and documents are accumulated
            preprocessor = DocumentPreprocessor(file_path)
            documents = preprocessor.process()
            all_documents.extend(documents)
        except Exception as e:
            await cl.Message(content=f"Error processing file `{file.name}`: {e}").send()
            return False

    if not all_documents:
        await cl.Message(content="Could not extract any content from the uploaded files.").send()
        return False

    cl.user_session.set("processed_documents", all_documents)
    msg.content = f"✅ Files processed: **{len(all_documents)}** chunks created."
    await msg.update()

    # Create and store the vector store and retriever
    vector_store = VectorStore()
    vector_store.add_documents(all_documents)
    cl.user_session.set(SessionKey.VECTOR_STORE, vector_store)

    retriever = RetrieverFactory.create(vector_store)
    cl.user_session.set(SessionKey.RETRIEVER, retriever)

    await cl.Message(content="✅ Retriever is ready! Setting up the agent...").send()
    return True


async def setup_agent(
    llm_provider: str, llm_model: str
) -> BlogContentAgent | None:
    """
    Sets up the agent using the retriever from the user session.
    """
    retriever = cl.user_session.get(SessionKey.RETRIEVER)
    processed_docs = cl.user_session.get("processed_documents")

    if not retriever or not processed_docs:
        # This function should only be called after ingestion is complete.
        return None

    agent = BlogContentAgent(
        retriever=retriever,
        documents=processed_docs,
        llm_provider=llm_provider,
        llm_model=llm_model,
    )
    cl.user_session.set(SessionKey.BLOG_CREATOR_AGENT, agent)
    return agent


async def rebuild_agent_with_new_model(llm_provider: str, llm_model: str) -> None:
    """
    Rebuild or update the BlogContentAgent in the user session when the model/profile changes.
    This will recreate the agent using the existing retriever and processed documents.
    """
    retriever = cl.user_session.get(SessionKey.RETRIEVER)
    processed_docs = cl.user_session.get("processed_documents")

    if not retriever or not processed_docs:
        await cl.Message(content="Please upload a document before changing the model.").send()
        return

    agent = BlogContentAgent(
        retriever=retriever,
        documents=processed_docs,
        llm_provider=llm_provider,
        llm_model=llm_model,
    )
    cl.user_session.set(SessionKey.BLOG_CREATOR_AGENT, agent)
    await cl.Message(content=f"✅ Model updated to `{llm_model}` (provider: {llm_provider}). Regenerating draft...").send()

    session_id = cl.user_session.get(SessionKey.SESSION_ID)
    if session_id:
        draft = await cl.make_async(agent.generate_draft)(session_id=session_id)
        cl.user_session.set(SessionKey.BLOG_DRAFT, draft)

        draft_msg = cl.Message(content="", author="BlogGenerator")
        await draft_msg.send()
        chunk_size = 10
        for i in range(0, len(draft), chunk_size):
            part = draft[i : i + chunk_size]
            await draft_msg.stream_token(part)
        await draft_msg.update()
        
        # Add actions to the new draft message
        await cl.Message(
            content="Draft regenerated with the new model. How would you like to proceed?",
            parent_id=draft_msg.id, # This makes it a reply/follow-up
            actions=[
                cl.Action(name="edit_draft", payload={"value": "edit"}, label="📝 Edit Draft"),
                cl.Action(name="save_draft", payload={"value": "save"}, label="💾 Save Draft"),
                cl.Action(name="toggle_tokens", payload={"value": "toggle"}, label="📊 Show Tokens"),
            ],
        ).send()