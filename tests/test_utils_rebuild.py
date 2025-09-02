import pytest
import asyncio

import chainlit as cl


class DummySession(dict):
    def get(self, k, d=None):
        return super().get(k, d)

    def set(self, k, v):
        self[k] = v


class DummyMessage:
    def __init__(self, content=""):
        self.content = content
        self.actions = []

    async def send(self):
        pass

    async def update(self):
        pass


def test_rebuild_agent_with_new_model(monkeypatch):
    # Monkeypatch chainlit user_session and Message
    dummy_session = DummySession()
    monkeypatch.setattr(cl, 'user_session', dummy_session)

    # Provide a fake retriever and documents
    dummy_retriever = object()
    dummy_docs = ["doc1", "doc2"]
    dummy_session['processed_documents'] = dummy_docs
    dummy_session["RETRIEVER"] = dummy_retriever

    # Monkeypatch Message to avoid real sends
    monkeypatch.setattr(cl, 'Message', lambda content="": DummyMessage(content))

    from src.ui.chainlit import utils

    # Call rebuild; should not raise
    import asyncio
    asyncio.run(utils.rebuild_agent_with_new_model('openai', 'gpt-test', 'draft'))
