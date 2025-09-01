# src/agent.py
import json
from typing import Dict, Generator, List


from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_ollama import ChatOllama
from langchain_tavily import TavilySearch

from langchain_core.documents import Document
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI
from langchain.tools.retriever import create_retriever_tool

from src.config import (
    RETRIEVER_TOOL_NAME,
    RETRIEVER_TOOL_DESCRIPTION,
    TAVILY_MAX_RESULTS,
)
from src.graph import GraphBuilder
from src.tokens import estimate_tokens, add_usage


class BlogContentAgent:
    """블로그 콘텐츠 생성을 위한 에이전트 클래스"""

    # --- __init__ now accepts llm_provider and llm_model ---
    def __init__(self, retriever, documents: List[Document], llm_provider: str, llm_model: str):
        """에이전트를 초기화합니다."""
        self.documents = documents
        self.llm = self._get_llm(llm_provider, llm_model)
        self.tools = self._create_tools(retriever)
        self.graph = self._build_graph()
        self.session_histories: Dict[str, ChatMessageHistory] = {}

    def _get_llm(self, llm_provider: str, llm_model: str):
        """설정에 따라 LLM 클라이언트를 반환합니다."""
        if llm_provider == "openai":
            # enable streaming at the LLM level when possible
            try:
                return ChatOpenAI(model=llm_model, temperature=0, streaming=True)
            except TypeError:
                return ChatOpenAI(model=llm_model, temperature=0)
        elif llm_provider == "ollama":
            try:
                return ChatOllama(model=llm_model, temperature=0, streaming=True)
            except TypeError:
                return ChatOllama(model=llm_model, temperature=0)
        else:
            raise ValueError(f"지원하지 않는 LLM 제공자입니다: {llm_provider}")

    def _create_tools(self, retriever):
        """에이전트가 사용할 도구 목록을 생성합니다."""
        retriever_tool = create_retriever_tool(
            retriever,
            RETRIEVER_TOOL_NAME,
            RETRIEVER_TOOL_DESCRIPTION,
        )
        tools = [retriever_tool]
        # Avoid external API calls in Local GPU mode (ollama). Only add Tavily
        # when provider is not strictly local.
        try:
            provider = getattr(self.llm, "_llm_type", None) or getattr(self.llm, "__class__", type("", (), {})).__name__.lower()
            if isinstance(provider, str):
                is_local = "ollama" in provider
            else:
                is_local = False
        except Exception:
            is_local = False

        if not is_local:
            tavily_tool = TavilySearch(max_results=TAVILY_MAX_RESULTS)
            tools.append(tavily_tool)

        return tools

    def _build_graph(self) -> Runnable:
        """LangGraph 상태 머신을 빌드하고 컴파일합니다."""
        builder = GraphBuilder(self.llm, self.tools)
        return builder.build()

    def get_session_history(self, session_id: str) -> ChatMessageHistory:
        """세션 ID에 해당하는 대화 기록을 가져오거나 생성합니다."""
        if session_id not in self.session_histories:
            self.session_histories[session_id] = ChatMessageHistory()
        return self.session_histories[session_id]

    def generate_draft(self, session_id: str) -> str:
        """문서 내용을 기반으로 블로그 포스트의 초안을 생성합니다."""
        joined_docs = "\n\n".join([doc.page_content for doc in self.documents])
        # TODO: 프롬프트를 prompts.yaml에서 불러오도록 수정해야 합니다.
        prompt = f"""
        당신은 전문 기술 블로거입니다. 다음 문서를 참고하여 블로그 포스트 초안을 작성해주세요.
        독자들이 이해하기 쉽게 흥미로운 제목과 내용을 만들어주세요. 마크다운 형식으로 작성해주세요.

        [참고 문서]
        {joined_docs}
        """
        history = self.get_session_history(session_id)
        history.add_user_message("블로그 초안을 작성해줘.")
        # estimate input/output tokens around LLM call
        in_tokens = estimate_tokens(prompt, model=getattr(self.llm, "model", None))
        # Prefer async LLM call with Chainlit Langchain callback handler for streaming
        try:
            from chainlit import LangchainCallbackHandler

            # Use the async invoke if available to attach callbacks
            if hasattr(self.llm, "ainvoke"):
                ai_message = self.llm.ainvoke(prompt, callbacks=[LangchainCallbackHandler(stream_final_answer=True)])
                # if this returns a coroutine, await it
                if hasattr(ai_message, "__await__"):
                    ai_message = ai_message.__await__().__next__()
            else:
                ai_message = self.llm.invoke(prompt)
        except Exception:
            # Fallback to synchronous invoke
            ai_message = self.llm.invoke(prompt)

        out_tokens = estimate_tokens(getattr(ai_message, 'content', str(ai_message)), model=getattr(self.llm, "model", None))
        add_usage(session_id, in_tokens, out_tokens)

        content = getattr(ai_message, "content", str(ai_message))
        draft_json = json.dumps({"type": "draft", "content": content}, ensure_ascii=False)
        history.add_ai_message(draft_json)
        return content

    def update_blog_post(
        self, user_request: str, draft: str, session_id: str
    ) -> Generator[str, None, None]:
        """사용자의 요청에 따라 블로그 초안을 스트리밍 방식으로 업데이트합니다."""
        history = self.get_session_history(session_id)
        history.add_user_message(user_request)

        initial_state = {
            "draft": draft,
            "user_request": user_request,
            "chat_history": history.messages,
        }

        graph_stream = self.graph.stream(initial_state)

        final_draft = ""
        for event in graph_stream:
            for node_name, node_output in event.items():
                if "draft" in node_output and isinstance(node_output["draft"], str):
                    new_content = node_output["draft"][len(final_draft) :]
                    if new_content:
                        yield new_content
                        final_draft += new_content

        # --- FIX: Store a conversational summary, not the whole draft ---
        summary_message = "I have updated the draft based on your request."
        final_response_json = json.dumps(
            {"type": "draft", "content": summary_message}, ensure_ascii=False
        )
        # -----------------------------------------------------------------
        history.add_ai_message(final_response_json)
    
    def get_response(
        self, user_request: str, draft: str, session_id: str
    ) -> Generator[Dict[str, str], None, None]:
        """
        사용자의 요청을 처리하고, 스트리밍 방식으로 응답(초안 또는 채팅)을 반환합니다.
        """
        history = self.get_session_history(session_id)
        history.add_user_message(user_request)

        initial_state = {
            "draft": draft,
            "user_request": user_request,
            "chat_history": history.messages,
            "response": "",  # 응답 필드 초기화
        }

        # Roughly estimate input tokens for this turn (router+nodes aggregate)
        concat_input = (draft or "") + "\n\n" + (user_request or "")
        in_tokens = estimate_tokens(concat_input, model=getattr(self.llm, "model", None))
        graph_stream = self.graph.stream(initial_state)

        final_draft = ""
        final_response = ""

        # --- MODIFIED: Stream handler now yields a dictionary with type and content ---
        for event in graph_stream:
            for node_name, node_output in event.items():
                if "draft" in node_output and isinstance(node_output["draft"], str):
                    new_content = node_output["draft"][len(final_draft) :]
                    if new_content:
                        final_draft += new_content
                        yield {"type": "draft", "content": new_content}

                if "response" in node_output and isinstance(node_output["response"], str):
                    new_content = node_output["response"][len(final_response) :]
                    if new_content:
                        final_response += new_content
                        yield {"type": "chat", "content": new_content}

        # --- MODIFIED: Save the correct message type to history ---
        if final_draft:
            # 초안이 수정된 경우
            history.add_ai_message(
                json.dumps({"type": "draft", "content": "Draft updated."}, ensure_ascii=False)
            )
        elif final_response:
            # 채팅 응답이 생성된 경우
            history.add_ai_message(
                json.dumps({"type": "chat", "content": final_response}, ensure_ascii=False)
            )

        # Add output tokens (sum of both kinds)
        out_tokens = estimate_tokens(final_draft + final_response, model=getattr(self.llm, "model", None))
        add_usage(session_id, in_tokens, out_tokens)