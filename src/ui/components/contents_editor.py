# src/ui/components/contents_editor.py
import streamlit as st
import json
from dataclasses import dataclass

from langchain.memory import ConversationBufferWindowMemory
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama

from src.agent import BlogContentAgent
from src.ui.enums import SessionKey
from src.config import LLM_PROVIDER, LLM_MODEL

@dataclass(frozen=True)
class Message:
    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"
    role: str
    contents: str

class ContentsEditor:
    """
    BlogContentAgent를 사용하여 블로그 초안을 생성하고 수정하는 UI 컴포넌트.
    """
    def render(self) -> bool:
        st.subheader("초안 생성 및 퇴고")
        agent = self._initialize_agent()

        if "draft" not in st.session_state:
            self._generate_draft_with_progress(agent)
            return False

        draft_col, _, chat_col = st.columns([52, 1, 46])
        self._render_draft_preview(draft_col)
        self._render_chat(chat_col, agent)

        if st.button("발행 단계로 이동"):
            st.session_state[SessionKey.BLOG_POST] = st.session_state.draft
            return True
        return False

    def _initialize_agent(self) -> BlogContentAgent:
        if SessionKey.BLOG_CREATOR_AGENT not in st.session_state:
            if SessionKey.RETRIEVER not in st.session_state or "processed_documents" not in st.session_state:
                st.warning("먼저 파일을 업로드하여 Retriever와 문서를 초기화해야 합니다.")
                st.stop()

            retriever = st.session_state[SessionKey.RETRIEVER]
            processed_docs = st.session_state["processed_documents"]
            
            # The agent now manages its own memory, so we don't create it here.
            st.session_state[SessionKey.BLOG_CREATOR_AGENT] = BlogContentAgent(retriever, processed_docs)
        
        return st.session_state[SessionKey.BLOG_CREATOR_AGENT]

    def _generate_draft_with_progress(self, agent: BlogContentAgent):
        if st.button("블로그 초안 생성하기", type="primary"):
            model_name = getattr(agent.llm, "model_name", agent.llm.model)
            with st.status(f"💬 초안 생성 중... (LLM: '{model_name}')", expanded=True) as status:
                st.session_state.draft = agent.generate_draft()
                status.update(label="✅ 블로그 포스트 초안 생성 완료!", state="complete", expanded=False)
            st.rerun()

    def _render_draft_preview(self, draft_column):
        with draft_column:
            st.markdown("##### **블로그 초안**")
            preview_tab, markdown_tab = st.tabs(["🖼️ Preview", "👨‍💻 Markdown"])
            with preview_tab:
                with st.container(height=700, border=True):
                    st.markdown(st.session_state.get("draft", ""))
            with markdown_tab:
                with st.container(height=700, border=True):
                    st.code(st.session_state.get("draft", ""), language="markdown")

    def _render_chat(self, chat_column, agent: BlogContentAgent):
        with chat_column:
            st.markdown("##### **수정 및 대화**")
            chat_container = st.container(height=625, border=True)
            with chat_container:
                # Use the agent's helper to get the history
                for msg in agent.get_session_history().messages:
                    role = Message.ROLE_USER if msg.type == "human" else Message.ROLE_ASSISTANT
                    with st.chat_message(role):
                        st.markdown(msg.content)
            
            if user_request := st.chat_input("수정하고 싶은 내용을 입력하세요..."):
                self._handle_user_prompt(agent, user_request)

    def _handle_user_prompt(self, agent: BlogContentAgent, user_request: str):
        with st.spinner("⏳ 수정 사항 반영 중..."):
            current_draft = st.session_state.get("draft", "")
            response_data = agent.update_blog_post(user_request, current_draft)
            
            # The agent's response now reliably contains both keys.
            chat_response = response_data.get("chat_response")
            updated_draft = response_data.get("updated_draft")

            # Update the draft in the session state
            st.session_state.draft = updated_draft
            
            # The agent already saved the chat response to memory, so we just need to rerun.
        st.rerun()
