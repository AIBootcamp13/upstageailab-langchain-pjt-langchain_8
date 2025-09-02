# Headless test: simulate upload + instruction flow and capture graph stream events
import traceback

from src.agent import BlogContentAgent

try:
    try:
        from langchain_core.documents import Document
    except Exception:
        class Document:
            def __init__(self, page_content=''):
                self.page_content = page_content

    # Build a bare agent instance (without constructing LLMs)
    agent = BlogContentAgent.__new__(BlogContentAgent)
    # Simulate processed/uploaded documents
    agent.documents = [Document(page_content='Uploaded document content A.'), Document(page_content='Uploaded document content B.')]
    agent.session_histories = {}
    # minimal llm stub to satisfy token estimation calls
    agent.llm = type('L', (), {'model': 'test-model'})()

    # Minimal history implementation used by agent
    class Hist:
        def __init__(self):
            self.messages = []
        def add_user_message(self, m):
            self.messages.append({'user': m})
        def add_ai_message(self, m):
            self.messages.append({'ai': m})

    agent.get_session_history = lambda sid: Hist()

    # FakeGraph: emits a draft chunk then a longer response in several chunks
    class FakeGraph:
        def stream(self, initial_state):
            # emit a draft preview (first 60 chars)
            yield {'node0': {'draft': initial_state['draft'][:60]}}
            # emit a response in two chunks
            yield {'node1': {'response': 'This is the first part of the response. ' * 20}}
            yield {'node2': {'response': 'This is the second part of the response. ' * 20}}

    agent.graph = FakeGraph()

    # Run get_response with an instruction that references uploaded docs
    user_request = 'Please summarize the uploaded documents in 100 words.'
    print('Running headless get_response...')
    gen = agent.get_response(user_request, '', 'headless-session')

    events = []
    for ev in gen:
        print('EVENT:', ev)
        events.append(ev)

    print('\nCaptured events:', len(events))
    if events:
        print('Last event type:', events[-1].get('type'))
        print('Last event snippet:', events[-1].get('content')[:200])

    print('Headless test completed successfully')
except Exception:
    traceback.print_exc()
    raise
