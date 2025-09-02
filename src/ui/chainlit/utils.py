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
from src.ui.chainlit.settings_core import setup_settings
from src.ui.chainlit.session_helpers import (
    get_processed_documents,
    set_processed_documents,
    get_retriever,
    set_retriever,
)
from src.ui.chainlit.agent_factory import create_and_store_agent


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

    set_processed_documents(all_documents)
    msg.content = f"✅ Files processed: **{len(all_documents)}** chunks created."
    await msg.update()

    # Create and store the vector store and retriever
    vector_store = VectorStore()
    vector_store.add_documents(all_documents)
    cl.user_session.set(SessionKey.VECTOR_STORE, vector_store)

    retriever = RetrieverFactory.create(vector_store)
    set_retriever(retriever)

    # Update the original processing message to indicate the retriever is ready
    msg.content = "✅ Retriever is ready! You can now set up the agent."
    await msg.update()
    return True


async def setup_agent(
    llm_provider: str, llm_model: str, agent_profile: str = "draft"
) -> BlogContentAgent | None:
    """
    Sets up the agent using the retriever from the user session.
    """
    retriever = get_retriever()
    processed_docs = get_processed_documents()

    if not retriever or not processed_docs:
        # This function should only be called after ingestion is complete.
        return None

    agent = create_and_store_agent(
        retriever=retriever,
        documents=processed_docs,
        llm_provider=llm_provider,
        llm_model=llm_model,
        agent_profile=agent_profile,
    )
    return agent


async def rebuild_agent_with_new_model(llm_provider: str, llm_model: str, agent_profile: str = "draft") -> None:
    """
    Rebuild or update the BlogContentAgent in the user session when the model/profile changes.
    This will recreate the agent using the existing retriever and processed documents.
    """
    retriever = get_retriever()
    processed_docs = get_processed_documents()

    if not retriever or not processed_docs:
        await cl.Message(content="Please upload a document before changing the model.").send()
        return

    # Mark loading in session so UI can show inline loading indicators (icons/spinner)
    cl.user_session.set("loading_model", True)
    # Refresh the settings panel to show the loading state in the model label
    await setup_settings(forced_provider=llm_provider)

    # Notify user that model update is in progress using a single message to
    # avoid multiple messages causing the input box to jump while the model
    # is being recreated.
    status_msg = cl.Message(content=f"⏳ Updating model to `{llm_model}` ({llm_provider})...")
    await status_msg.send()

    agent = BlogContentAgent(
        retriever=retriever,
        documents=processed_docs,
        llm_provider=llm_provider,
        llm_model=llm_model,
        agent_profile=agent_profile,
    )
    cl.user_session.set(SessionKey.BLOG_CREATOR_AGENT, agent)

    # Update the same message to indicate completion – this minimizes UI
    # reflows because the message element is updated instead of creating
    # a new one.
    # Clear loading flag and refresh settings so icons and model label return to normal
    cl.user_session.set("loading_model", False)
    # Refresh settings panel
    await setup_settings()

    status_msg.content = f"✅ Model updated to `{llm_model}` ({llm_provider}). You can regenerate the draft if needed."
    status_msg.actions = [
        cl.Action(name="regenerate_draft", payload={"value": "regenerate"}, label="🔁 Regenerate Draft"),
    ]
    await status_msg.update()