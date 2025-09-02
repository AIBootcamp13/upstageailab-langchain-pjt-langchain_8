"""Small helpers around chainlit session access to centralize session keys and safe access.
This keeps direct `cl.user_session` usage in one place and reduces import churn.
"""
import chainlit as cl
from src.ui.enums import SessionKey


def get_processed_documents():
    return cl.user_session.get("processed_documents")


def set_processed_documents(docs):
    cl.user_session.set("processed_documents", docs)


def get_retriever():
    return cl.user_session.get(SessionKey.RETRIEVER)


def set_retriever(retriever):
    cl.user_session.set(SessionKey.RETRIEVER, retriever)


def get_session_id():
    sid = cl.user_session.get(SessionKey.SESSION_ID)
    if not sid:
        import uuid
        sid = str(uuid.uuid4())
        cl.user_session.set(SessionKey.SESSION_ID, sid)
    return sid


def set_agent(agent):
    cl.user_session.set(SessionKey.BLOG_CREATOR_AGENT, agent)


def get_agent():
    return cl.user_session.get(SessionKey.BLOG_CREATOR_AGENT)
