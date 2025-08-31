# src/agent.py
import json
from typing import Any, Dict, List

from langchain.tools.retriever import create_retriever_tool
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from src.config import (
    DRAFT_PROMPT_TEMPLATE,
    LLM_MODEL,
    LLM_PROVIDER,
    RETRIEVER_TOOL_DESCRIPTION,
    RETRIEVER_TOOL_NAME,
    TAVILY_API_KEY,
)

# --- LangGraph 통합 ---
from src.graph import GraphBuilder


class AgentChatMessageHistory(ChatMessageHistory):
    """UI 호환성을 위해 get_messages 메서드를 추가한 사용자 정의 채팅 기록 클래스입니다."""

    def get_messages(self) -> List[BaseMessage]:
        """기록에서 모든 메시지를 검색합니다."""
        return self.messages


class BlogContentAgent:
    """
    LangGraph를 사용하여 블로그 게시물 초안을 작성하고 편집하는 에이전트입니다.
    웹 및 문서 검색 기능이 포함되어 있습니다.
    """

    def __init__(self, retriever, processed_docs: list[Document]):
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

        # 3. 도구(Tools) 설정
        retriever_tool = create_retriever_tool(
            retriever,
            RETRIEVER_TOOL_NAME,
            RETRIEVER_TOOL_DESCRIPTION,
        )
        web_search_tool = TavilySearch(max_results=3, tavily_api_key=TAVILY_API_KEY)
        tools = [retriever_tool, web_search_tool]

        # 4. LangGraph 빌드
        graph_builder = GraphBuilder(self.llm, tools)
        self.graph: Runnable = graph_builder.build()

    def get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        """주어진 세션 ID에 대한 채팅 기록을 가져오거나 새로 생성합니다."""
        if session_id not in self.chat_history_store:
            self.chat_history_store[session_id] = AgentChatMessageHistory()
        return self.chat_history_store[session_id]

    def generate_draft(self, session_id: str) -> str:
        """처리된 문서에서 초기 블로그 초안을 생성합니다."""
        content = self.format_docs(self.processed_docs)
        draft = self.draft_chain.invoke({"content": content})

        # --- 그래프와 호환되도록 채팅 기록 업데이트 ---
        history = self.get_session_history(session_id)
        history.add_user_message("제공된 문서를 바탕으로 블로그 초안을 생성해줘.")
        history.add_ai_message(
            AIMessage(
                content=json.dumps(
                    {"type": "draft", "content": draft}, ensure_ascii=False
                )
            )
        )
        return draft

    def update_blog_post(
        self, user_request: str, draft: str, session_id: str
    ) -> dict:
        """사용자 요청에 따라 블로그 게시물을 업데이트하기 위해 그래프를 실행합니다."""
        history = self.get_session_history(session_id)
        history.add_user_message(HumanMessage(content=user_request))

        # 그래프 실행을 위한 초기 상태(state)를 구성합니다.
        initial_state = {
            "draft": draft,
            "chat_history": history.messages,
            "user_request": user_request,
        }

        # 그래프 실행
        final_state = self.graph.invoke(initial_state)

        # AI 응답을 채팅 기록에 추가합니다.
        # 최종 초안을 포함하여 AI 메시지를 구성합니다.
        response_payload = {
            "type": "draft",
            "content": final_state["draft"],
        }
        ai_message = AIMessage(
            content=json.dumps(response_payload, ensure_ascii=False)
        )
        history.add_ai_message(ai_message)

        return response_payload

    @staticmethod
    def format_docs(documents: list[Document]) -> str:
        """Document 객체 리스트를 단일 문자열로 결합합니다."""
        return "\n\n".join(doc.page_content for doc in documents)
