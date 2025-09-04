# src/agent.py
import json
from difflib import SequenceMatcher
from typing import Any, Dict, List, Type

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools.retriever import create_retriever_tool
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.documents import Document
from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.tools import BaseTool
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from pydantic import BaseModel, Field, PrivateAttr

from src.config import (
    DRAFT_PROMPT_TEMPLATE,
    LLM_MODEL,
    LLM_PROVIDER,
    TAVILY_API_KEY,
    UPDATE_PROMPT_TEMPLATE,
)


class TavilySearchSchema(BaseModel):
    """Tavily 검색 도구의 입력 스키마입니다."""

    query: str = Field(description="실행할 검색 쿼리입니다.")


class CachedTavilySearchTool(BaseTool):
    """
    TavilySearch를 래핑하여 결과를 캐시하고 중복 API 호출을 방지하는 도구입니다.
    """

    name: str = "tavily_search"
    description: str = "포괄적이고 정확하며 신뢰할 수 있는 결과를 위해 최적화된 검색 엔진입니다. 웹에서 정보를 찾을 때 유용합니다."
    args_schema: Type[BaseModel] = TavilySearchSchema
    _tool: TavilySearch = PrivateAttr(default_factory=lambda: TavilySearch(max_results=3, tavily_api_key=TAVILY_API_KEY))
    _cache: Dict[str, Any] = PrivateAttr(default_factory=dict)
    similarity_threshold: float = 0.9

    def _is_similar(self, query1: str, query2: str) -> bool:
        """두 쿼리가 설정된 임계값 기준으로 유사한지 확인합니다."""
        return SequenceMatcher(None, query1.lower(), query2.lower()).ratio() >= self.similarity_threshold

    def _run(self, query: str) -> str:
        """캐시를 사용하여 중복 호출을 피하면서 도구를 실행합니다."""
        for cached_query, result in self._cache.items():
            if self._is_similar(query, cached_query):
                print(f"--- CACHE HIT: '{query}'에 대해 유사한 쿼리 '{cached_query}'를 찾았습니다 ---")
                return result

        print(f"--- CACHE MISS: '{query}'에 대한 새로운 검색을 실행합니다 ---")
        result = self._tool.run(query)
        self._cache[query] = result
        return result


# --- FIX: Simplified the Chat History class ---
# The previous version incorrectly overrode the `.messages` attribute as a property,
# which caused the "'property' object has no attribute 'append'" error.
# This new version correctly inherits the `.messages` list from the parent class
# and only adds the `get_messages` method for compatibility with our UI component.
class AgentChatMessageHistory(ChatMessageHistory):
    """Custom chat history that adds a `get_messages` method for UI compatibility."""

    def get_messages(self) -> List[BaseMessage]:
        """Retrieves all messages from the history."""
        return self.messages


class BlogContentAgent:
    """
    웹 및 문서 검색을 사용하여 블로그 게시물 초안을 작성하고 편집하는 Tool-Calling 에이전트입니다.
    중복 도구 호출을 방지하기 위한 캐싱 기능이 내장되어 있습니다.
    """

    def __init__(self, retriever, processed_docs: list[Document]):
        self.retriever = retriever
        self.processed_docs = processed_docs
        self.chat_history_store: Dict[str, AgentChatMessageHistory] = {}

        # 1. LLM 초기화
        if LLM_PROVIDER == "openai":
            self.llm = ChatOpenAI(model=LLM_MODEL, temperature=0)
        elif LLM_PROVIDER == "ollama":
            self.llm = ChatOllama(model=LLM_MODEL, temperature=0)
        else:
            raise ValueError(f"지원되지 않는 LLM 제공자입니다: {LLM_PROVIDER}")

        # 2. 초기 초안 생성을 위한 체인 정의
        self.draft_prompt_template = ChatPromptTemplate.from_template(DRAFT_PROMPT_TEMPLATE)
        self.output_parser = StrOutputParser()
        self.draft_chain = self.draft_prompt_template | self.llm | self.output_parser

        # 3. Tool-Calling 에이전트 설정
        retriever_tool = create_retriever_tool(
            self.retriever,
            "document_search",
            "업로드된 PDF 문서에서 정보를 검색하고 반환합니다. 문서 내용에 대한 질문에 답할 때 사용하세요.",
        )
        cached_web_search_tool = CachedTavilySearchTool()
        tools = [retriever_tool, cached_web_search_tool]

        self.update_prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", UPDATE_PROMPT_TEMPLATE),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        agent = create_tool_calling_agent(self.llm, tools, self.update_prompt_template)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

        self.agent_with_chat_history = RunnableWithMessageHistory(
            agent_executor,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
        )

    def get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        """주어진 세션 ID에 대한 채팅 기록을 가져오거나 새로 생성합니다."""
        if session_id not in self.chat_history_store:
            self.chat_history_store[session_id] = AgentChatMessageHistory()
        return self.chat_history_store[session_id]

    def generate_draft(self, session_id: str) -> str:
        """처리된 문서에서 초기 블로그 초안을 생성합니다."""
        content = self.format_docs(self.processed_docs)
        draft = self.draft_chain.invoke({"content": content})

        history = self.get_session_history(session_id)
        history.add_user_message("제공된 문서를 바탕으로 블로그 초안을 생성해줘.")

        payload = {"type": "draft", "content": draft}
        history.add_ai_message(json.dumps(payload, ensure_ascii=False))
        return draft

    def update_blog_post(self, user_request: str, session_id: str) -> dict:
        """사용자 요청에 따라 블로그 게시물을 업데이트하기 위해 에이전트를 실행합니다."""
        config = {"configurable": {"session_id": session_id}}
        response = self.agent_with_chat_history.invoke({"input": user_request}, config=config)

        try:
            output_str = response.get("output", "{}")
            parsed_json = json.loads(output_str)
            return parsed_json if isinstance(parsed_json, dict) else {"type": "chat", "content": str(parsed_json)}
        except (json.JSONDecodeError, TypeError):
            return {"type": "chat", "content": response.get("output", "죄송합니다, 응답을 처리하는 중 오류가 발생했습니다.")}

    @staticmethod
    def format_docs(documents: list[Document]) -> str:
        """Document 객체 리스트를 단일 문자열로 결합합니다."""
        return "\n\n".join(doc.page_content for doc in documents)

