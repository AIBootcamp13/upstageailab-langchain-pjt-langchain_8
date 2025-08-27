Project Update: Conversational Memory & Tool Integration Plan
Date: August 27, 2025

Phase 1: Implementing Conversational Memory
This phase focuses on enhancing the BlogContentAgent with short-term memory to enable more natural, stateful interactions during the blog editing process in the Streamlit UI.

1.1. Goal:
The agent must remember the history of a single editing conversation. If a user makes a request to change the tone and then follows up with a request to add a new section, the agent should apply the second request to the already tone-adjusted text, not the original draft.

1.2. Chosen Strategy: ConversationSummaryBufferMemory
For this project, especially when using a powerful local model like gpt-oss:20b, the ConversationSummaryBufferMemory is the optimal choice.

Why? It strikes a balance between performance and context preservation. It keeps recent exchanges in full detail for immediate context while summarizing older messages to prevent the overall context from exceeding the model's token limit during long editing sessions.

1.3. Implementation Steps & Checklist:

Step 1: Update Dependencies

[ ] pyproject.toml: Ensure langchain is up to date, as memory components are part of the core library. No new packages are strictly required for this step.

Step 2: Refactor src/agent.py

[ ] Import necessary modules: Add from langchain.chains import ConversationChain and from langchain.memory import ConversationSummaryBufferMemory.

[ ] Update BlogContentAgent.__init__: Modify the constructor to accept a memory object.

[ ] Replace update_blog_post logic: The current update_blog_post method uses a simple chain. This will be replaced by a ConversationChain. The new chain will be initialized with the LLM, the memory object, and a new, more conversational prompt template.

[ ] Create a new prompt: The update_prompt in prompts.yaml needs to be adapted for a conversational chain, including placeholders for history and input.

Step 3: Refactor src/ui/components/contents_editor.py

[ ] Import memory module: Add from langchain.memory import ConversationSummaryBufferMemory.

[ ] Instantiate Memory: In the render method, when the BlogContentAgent is first created, also create an instance of ConversationSummaryBufferMemory and save it to st.session_state.

[ ] Pass Memory to Agent: Pass the newly created memory object to the BlogContentAgent during its initialization. This ensures that the memory persists for the entire user session but is cleared when a new blog is started.

Phase 2: Integrating Tavily Web Search as an Agent Tool
This phase focuses on giving the BlogContentAgent a new capability: the ability to perform real-time web searches to enrich or verify content during the editing process.

2.1. Goal:
During a conversation, a user should be able to ask the agent to find and incorporate new information. For example: "Can you find the latest statistics on RAG adoption and add them to the second paragraph?"

2.2. Implementation Strategy:
We will transform the BlogContentAgent from a simple ConversationChain into a more powerful LangChain Agent that can use tools. The TavilySearchResults tool will be its primary new tool.

2.3. Implementation Steps & Checklist:

Step 1: Update Configuration

[ ] .env file: Ensure the TAVILY_API_KEY is present and loaded by src/config.py.

[ ] pyproject.toml: Add the tavily-python dependency.

Step 2: Refactor src/agent.py

[ ] Import agent modules: Add imports for AgentExecutor, create_react_agent (or a similar agent constructor), and TavilySearchResults.

[ ] Define Tools: Create a tools list that includes an instance of TavilySearchResults.

[ ] Re-implement the Agent: The BlogContentAgent will now be built around an AgentExecutor. It will be initialized with the LLM, the tools list, and a new agent-specific prompt that instructs it on how to use its tools. The conversational memory from Phase 1 will be integrated directly into this new agent executor.

Step 3: Update UI and Prompts

[ ] prompts.yaml: Create a new, more sophisticated prompt template suitable for a ReAct agent, instructing it on how to handle editing tasks and when to use the web search tool.

[ ] src/ui/components/contents_editor.py: The UI logic will remain largely the same, but the user instructions or placeholder text in the chat input could be updated to hint 