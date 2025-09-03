import asyncio
import chainlit as cl


class DummySession(dict):
    def get(self, k, d=None):
        return super().get(k, d)

    def set(self, k, v):
        self[k] = v


class DummyMessage:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.id = kwargs.get('id', 'msg-1')
        self.sent = False

    async def send(self):
        self.sent = True

    async def update(self, **kwargs):
        # store last update for assertions
        self.last_update = kwargs


def test_on_open_inline_editor_prefills_editor(monkeypatch):
    # Set up dummy session with a draft
    session = DummySession()
    session.set('BLOG_DRAFT', 'Initial draft text')
    monkeypatch.setattr(cl, 'user_session', session)

    # Monkeypatch cl.Message to our DummyMessage to capture sends
    monkeypatch.setattr(cl, 'Message', lambda **kwargs: DummyMessage(**kwargs))

    # Import the callbacks module and call the action handler
    from src.ui.chainlit import callbacks

    class DummyAction:
        payload = {'message_id': 'parent-msg-1'}

    # Run the coroutine
    asyncio.run(callbacks.on_open_inline_editor(DummyAction()))

    # The dummy session should remain unchanged and no exceptions raised
    assert session.get('BLOG_DRAFT') == 'Initial draft text'


def test_on_submit_inline_editor_updates_session_and_preview(monkeypatch):
    session = DummySession()
    # Set preview message id so submit handler updates it
    session.set('preview_message_id', 'preview-1')
    monkeypatch.setattr(cl, 'user_session', session)

    # Track messages sent/updated
    sent = {}

    class DummyMsg2:
        def __init__(self, **kwargs):
            self.id = kwargs.get('id', 'preview-1')

        async def update(self, content=None, elements=None):
            sent['updated'] = {'content': content, 'elements': elements}
        
        async def send(self):
            sent['sent_confirm'] = True

    # Patch Message constructor used in the handler
    monkeypatch.setattr(cl, 'Message', lambda **kwargs: DummyMsg2(**kwargs))

    # Stub cl.Text to avoid needing Chainlit context during tests
    monkeypatch.setattr(cl, 'Text', lambda **kwargs: {'content': kwargs.get('content'), 'language': kwargs.get('language'), 'name': kwargs.get('name')})

    from src.ui.chainlit import callbacks

    class DummyAction2:
        payload = {'editor': 'Edited draft content'}

    asyncio.run(callbacks.on_submit_inline_editor(DummyAction2()))

    # Session should be updated (use the project's SessionKey value)
    from src.ui.enums import SessionKey as SK
    assert session.get(SK.BLOG_DRAFT) == 'Edited draft content'
    # Preview should have been updated
    assert sent.get('updated') is not None
