"""Small factory to create and register BlogContentAgent instances.
This isolates direct references to BlogContentAgent and `cl.user_session`.
"""
from src.agent import BlogContentAgent
from src.ui.enums import SessionKey
import chainlit as cl


def create_and_store_agent(retriever, documents, llm_provider, llm_model, agent_profile="draft"):
    agent = BlogContentAgent(
        retriever=retriever,
        documents=documents,
        llm_provider=llm_provider,
        llm_model=llm_model,
        agent_profile=agent_profile,
    )
    cl.user_session.set(SessionKey.BLOG_CREATOR_AGENT, agent)
    return agent
