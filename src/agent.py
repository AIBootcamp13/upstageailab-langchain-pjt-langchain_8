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
    DRAFT_PROMPT_TEMPLATE,
    UPDATE_PROMPT_TEMPLATE,
)
from src.graph import GraphBuilder
from src.tokens import estimate_tokens, add_usage


class BlogContentAgent:
    """블로그 콘텐츠 생성을 위한 에이전트 클래스"""

    # --- __init__ now accepts llm_provider and llm_model ---
    def __init__(self, retriever, documents: List[Document], llm_provider: str, llm_model: str, agent_profile: str = "draft"):
        """에이전트를 초기화합니다."""
        self.documents = documents
        self.llm = self._get_llm(llm_provider, llm_model)
        self.agent_profile = agent_profile
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
        # Rebuild documents from Chainlit session if available (uploaded files)
        try:
            import chainlit as cl
            from src.ui.enums import SessionKey
            pd = cl.user_session.get(SessionKey.PROCESSED_DOCUMENTS)
            if pd and isinstance(pd, list):
                self.documents = pd
        except Exception:
            # Not running inside Chainlit context or no processed docs available
            pass

        joined_docs = "\n\n".join([doc.page_content for doc in self.documents])
        
        # Select the appropriate prompt based on agent profile
        if self.agent_profile == "draft":
            prompt_template = DRAFT_PROMPT_TEMPLATE
        elif self.agent_profile == "update":
            prompt_template = UPDATE_PROMPT_TEMPLATE
        else:
            # Default to draft prompt
            prompt_template = DRAFT_PROMPT_TEMPLATE
        
        # Fill in the content placeholder
        prompt = prompt_template.replace("{content}", joined_docs)
        
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

        # Debug: try to rebuild documents from Chainlit session so graph gets uploaded content
        try:
            import chainlit as cl
            from src.ui.enums import SessionKey
            pd = cl.user_session.get(SessionKey.PROCESSED_DOCUMENTS)
            if pd and isinstance(pd, list):
                self.documents = pd
                # Only replace the initial_state draft when it is empty. If a
                # draft was already provided (e.g., user edited it), prefer
                # that over reconstructed documents.
                if not initial_state.get("draft"):
                    initial_state["draft"] = "\n\n".join([doc.page_content for doc in self.documents])
        except Exception:
            pass

        # For traceability, send a debug message when running under Chainlit
        try:
            import chainlit as cl
            awaitable = getattr(cl, "Message", None)
            if awaitable:
                # Send a short debug message with sizes (best-effort).
                try:
                    msg = cl.Message(content=f"[debug] initial_state draft length={len(initial_state['draft'])}")
                    # We're in a synchronous generator context; schedule the send
                    # so we don't produce RuntimeWarning for un-awaited coroutines.
                    try:
                        import asyncio

                        asyncio.create_task(msg.send())
                    except Exception:
                        # As a last resort, call .send() without awaiting and ignore warnings
                        try:
                            msg.send()
                        except Exception:
                            pass
                except Exception:
                    # Best-effort debug msg; ignore failures
                    pass
        except Exception:
            # Not running in Chainlit context
            pass

        # Roughly estimate input tokens for this turn (router+nodes aggregate)
        concat_input = (draft or "") + "\n\n" + (user_request or "")
        in_tokens = estimate_tokens(concat_input, model=getattr(self.llm, "model", None))
        graph_stream = self.graph.stream(initial_state)

        final_draft = ""
        final_response = ""

        # Heuristic: if user asked for a specific summary length (e.g., "summarize in 300 words"),
        # try to enforce an approximate output length by post-processing the final_response.
        def extract_requested_word_limit(text: str) -> int | None:
            import re
            m = re.search(r"(summariz|summary|summarise|summarize).{0,20}(\d{2,5})\s*(words|word)", text, re.IGNORECASE)
            if m:
                try:
                    return int(m.group(2))
                except Exception:
                    return None
            return None

        requested_words = extract_requested_word_limit(user_request or "")

        # Track words yielded when a user requests a specific summary length.
        words_yielded = 0

        # Stream handler: yield draft updates and chat responses; enforce word cap if requested.
        for event in graph_stream:
            for node_name, node_output in event.items():
                if "draft" in node_output and isinstance(node_output["draft"], str):
                    new_content = node_output["draft"][len(final_draft) :]
                    if new_content:
                        final_draft += new_content
                        yield {"type": "draft", "content": new_content}

                if "response" in node_output and isinstance(node_output["response"], str):
                    new_content = node_output["response"][len(final_response) :]
                    if not new_content:
                        continue

                    if requested_words:
                        parts = new_content.split()
                        remaining = requested_words - words_yielded
                        if remaining <= 0:
                            # Limit reached; stop streaming further responses.
                            return
                        if len(parts) > remaining:
                            trimmed = " ".join(parts[:remaining])
                            final_response += trimmed
                            words_yielded += len(trimmed.split())
                            yield {"type": "chat", "content": trimmed}
                            # We've satisfied the requested length; stop.
                            return
                        else:
                            final_response += new_content
                            words_yielded += len(parts)
                            yield {"type": "chat", "content": new_content}
                    else:
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

        # If a word limit was requested, do a final trim and yield a concise version (non-stream)
        if requested_words and final_response:
            words = final_response.split()
            if len(words) > requested_words:
                trimmed = " ".join(words[:requested_words])
                # yield a final chat message with the trimmed summary
                yield {"type": "chat", "content": "\n\n" + trimmed}