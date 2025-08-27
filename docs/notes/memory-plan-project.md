For your project, the most useful type of "memory" is **short-term conversational memory**. Its purpose is to allow the `BlogContentAgent` to remember the back-and-forth conversation during a single editing session, ensuring that each new edit builds upon the last one.

This prevents the agent from forgetting previous instructions. For example, after you ask it to change the tone, you can then ask it to add a new section, and it will remember to apply the new section to the professional-toned version, not the original draft.

For your specific use case with a local `gpt-oss:20b` model, the best implementation is LangChain's **`ConversationSummaryBufferMemory`**. It's efficient because it keeps the most recent messages in full detail while summarizing older parts of the conversation. This prevents the context sent to your local model from getting too long and exceeding its token limit during a lengthy editing session.

---
### Where to Implement Memory

You can implement this memory in two key areas of your existing codebase:

#### 1. **The Agent (`src/agent.py`)**
This is the "brain" where the memory will be used. The `BlogContentAgent` needs to be modified to be "memory-aware."

* **What to do**: You'll update the `BlogContentAgent` to be initialized with a memory object. The chain inside the `update_blog_post` method will be changed from a simple LLM call to a `ConversationChain`, which automatically reads from and saves to the memory object with each new request.

#### 2. **The UI Component (`src/ui/components/contents_editor.py`)**
This is the "control center" where the memory will be created and managed for each user session.

* **What to do**: You will modify the `render` method in the `ContentsEditor` class. When a new editing session begins (i.e., when the `BlogContentAgent` is first created), you will also create a new `ConversationSummaryBufferMemory` instance and store it in Streamlit's `session_state`. This memory object will then be passed to the `BlogContentAgent` upon its creation. This ensures each new blog editing session starts with a fresh, clean memory.