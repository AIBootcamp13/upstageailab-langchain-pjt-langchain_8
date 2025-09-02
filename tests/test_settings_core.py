import asyncio
import chainlit as cl


class DummySession(dict):
    def get(self, k, d=None):
        return super().get(k, d)

    def set(self, k, v):
        self[k] = v


def test_setup_settings_creates_chatsettings(monkeypatch):
    sent = {}

    class DummyChatSettings:
        def __init__(self, items):
            self.items = items

        async def send(self):
            sent['called'] = True

    # Inject a dummy user_session so Chainlit context isn't required
    monkeypatch.setattr(cl, 'user_session', DummySession())
    monkeypatch.setattr(cl, 'ChatSettings', DummyChatSettings)

    from src.ui.chainlit import settings_core

    # Run the async setup in an event loop
    asyncio.run(settings_core.setup_settings())
    assert sent.get('called', False) is True
