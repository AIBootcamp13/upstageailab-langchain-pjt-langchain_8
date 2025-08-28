# src/agent.py
import json
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools.retriever import create_retriever_tool
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_tavily import TavilySearch

from src.config import (
    LLM_PROVIDER,
    LLM_MODEL,
    DRAFT_PROMPT_TEMPLATE,
    UPDATE_PROMPT_TEMPLATE,
    TAVILY_API_KEY,
)


class BlogContentAgent:
    """
    웹 검색 및 문서 검색 도구를 사용하여 블로그 초안을 생성하고 수정하는 Tool-Calling 에이전트.
    """
    def __init__(self, retriever, processed_docs: list[Document]):
        self.retriever = retriever
        self.processed_docs = processed_docs
        self.chat_history_store = {}

        if LLM_PROVIDER == "openai":
            self.llm = ChatOpenAI(model=LLM_MODEL, temperature=0)
        elif LLM_PROVIDER == "ollama":
            self.llm = ChatOllama(model=LLM_MODEL, temperature=0)
        else:
            raise ValueError(f"Unsupported LLM provider: {LLM_PROVIDER}")

        self.draft_prompt_template = ChatPromptTemplate.from_template(DRAFT_PROMPT_TEMPLATE)
        self.output_parser = StrOutputParser()
        self.draft_chain = self.draft_prompt_template | self.llm | self.output_parser

        retriever_tool = create_retriever_tool(
            self.retriever,
            "document_search",
            "업로드된 PDF 문서에서 정보를 검색하고 반환합니다. 문서 내용에 대한 질문에 답할 때 사용하세요."
        )
        web_search_tool = TavilySearch(max_results=3, tavily_api_key=TAVILY_API_KEY)
        tools = [retriever_tool, web_search_tool]
        
        self.update_prompt_template = ChatPromptTemplate.from_messages([
            ("system", UPDATE_PROMPT_TEMPLATE),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_tool_calling_agent(self.llm, tools, self.update_prompt_template)
        # We will handle JSON parsing manually for better error handling
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

        self.agent_with_chat_history = RunnableWithMessageHistory(
            agent_executor,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
        )

    def get_session_history(self, session_id: str):
        if session_id not in self.chat_history_store:
            self.chat_history_store[session_id] = ChatMessageHistory()
        return self.chat_history_store[session_id]

    def generate_draft(self, session_id: str) -> str:
        content = self.format_docs(self.processed_docs)
        draft = self.draft_chain.invoke({"content": content})
        history = self.get_session_history(session_id)
        history.add_user_message("제공된 문서를 바탕으로 블로그 초안을 생성해줘.")
        # Store the AI's response as if it were a valid JSON object for consistency
        history.add_ai_message(json.dumps({"type": "draft", "content": draft}))
        return draft

    def update_blog_post(self, user_request: str, session_id: str) -> dict:
        config = {"configurable": {"session_id": session_id}}
        response = self.agent_with_chat_history.invoke({"input": user_request}, config=config)
        
        # *** FIX: Add robust JSON parsing to prevent crashes ***
        try:
            # The output from the agent should be a string that we can parse into JSON
            output_str = response.get("output", "{}")
            parsed_json = json.loads(output_str)
            if isinstance(parsed_json, dict):
                return parsed_json
            else:
                # If parsing results in a non-dict, treat as a chat response
                return {"type": "chat", "content": str(parsed_json)}
        except (json.JSONDecodeError, TypeError):
            # If parsing fails, treat the entire output as a chat response
            return {"type": "chat", "content": response.get("output", "죄송합니다, 응답을 처리하는 중 오류가 발생했습니다.")}

    @staticmethod
    def format_docs(documents: list[Document]) -> str:
        return "\n\n".join(doc.page_content for doc in documents)

