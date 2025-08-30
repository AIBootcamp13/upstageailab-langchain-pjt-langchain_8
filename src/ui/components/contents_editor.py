# src/ui/components/contents_editor.py
import json
import uuid
from dataclasses import dataclass

import streamlit as st

from src.agent import BlogContentAgent
from src.ui.enums import SessionKey


@dataclass(frozen=True)
class Message:
    """A class to represent a chat message."""

    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"

    role: str
    contents: str


class ContentsEditor:
    """
    Renders the main editor UI, combining a blog post preview with a conversational chat panel.
    """

    def render(self) -> bool:
        """Renders the main editor UI."""
        st.subheader("초안 생성 및 퇴고")

        agent = self._initialize_agent()
        session_id = st.session_state.session_id

        if SessionKey.BLOG_DRAFT not in st.session_state:
            self._generate_draft_with_progress(agent, session_id)
            return False

        draft_col, _, chat_col = st.columns([52, 1, 46])

        with draft_col:
            self._render_draft_preview()

        with chat_col:
            self._render_chat(agent, session_id)

        if st.button("발행 단계로 이동"):
            self.finalize_draft()
            return True
        return False

    def _initialize_agent(self) -> BlogContentAgent:
        """Initializes the BlogContentAgent if not already in the session."""
        if "session_id" not in st.session_state:
            st.session_state.session_id = str(uuid.uuid4())

        if SessionKey.BLOG_CREATOR_AGENT not in st.session_state:
            if SessionKey.RETRIEVER not in st.session_state or "processed_documents" not in st.session_state:
                st.warning("먼저 파일을 업로드하여 Retriever와 문서를 초기화해야 합니다.")
                st.stop()
            retriever = st.session_state[SessionKey.RETRIEVER]
            processed_docs = st.session_state["processed_documents"]
            st.session_state[SessionKey.BLOG_CREATOR_AGENT] = BlogContentAgent(retriever, processed_docs)

        return st.session_state[SessionKey.BLOG_CREATOR_AGENT]

    def _generate_draft_with_progress(self, agent: BlogContentAgent, session_id: str):
        """Shows a button to generate a draft and displays its progress using st.status."""
        if st.button("블로그 초안 생성하기", type="primary"):
            model_name = agent.llm.model_name if hasattr(agent.llm, "model_name") else agent.llm.model
            with st.status(f"💬 초안 생성 중... (LLM: '{model_name}')", expanded=True) as status:
                draft = agent.generate_draft(session_id)
                st.session_state[SessionKey.BLOG_DRAFT] = draft
                status.update(label="✅ 블로그 포스트 초안 생성 완료!", state="complete", expanded=False)
            st.rerun()

    def _render_draft_preview(self):
        """Renders the draft preview and markdown tabs within a bordered container."""
        # --- UI CHANGE: Increased container height for more vertical space ---
        with st.container(height=900, border=True):
            st.markdown("##### **블로그 초안**")
            preview_tab, markdown_tab = st.tabs(["🖼️ Preview", "👨‍💻 Markdown"])

            with preview_tab:
                st.markdown(st.session_state.get(SessionKey.BLOG_DRAFT, ""))

            with markdown_tab:
                st.code(st.session_state.get(SessionKey.BLOG_DRAFT, ""), language="markdown")

    def _render_chat(self, agent: BlogContentAgent, session_id: str):
        """Renders the chat panel within a bordered container."""
        # --- UI CHANGE: Increased container height for more vertical space ---
        with st.container(height=900, border=True):
            st.markdown("##### **수정 및 대화**")

            # --- UI CHANGE: Increased chat container height ---
            chat_container = st.container(height=850)
            with chat_container:
                # --- FIX: Use the new .get_messages() method for safety ---
                # This ensures compatibility with our new custom history object.
                chat_history = agent.get_session_history(session_id).get_messages()
                for msg in chat_history:
                    role = Message.ROLE_USER if msg.type == "human" else Message.ROLE_ASSISTANT
                    with st.chat_message(role):
                        content_to_display = self._parse_ai_message(msg.content, role)
                        st.markdown(content_to_display)

            if user_request := st.chat_input("수정하고 싶은 내용을 입력하세요..."):
                self._handle_user_prompt(agent, user_request, session_id)

    def _parse_ai_message(self, content: str, role: str) -> str:
        """
        Parses the AI's message content to decide what to display in the chat.
        """
        if role == Message.ROLE_USER:
            return content
        try:
            data = json.loads(content)
            if data.get("type") == "draft":
                return "초안이 수정되었습니다. 왼쪽 패널에서 확인 후 추가 요청을 해주세요."
            return data.get("content", content)
        except (json.JSONDecodeError, TypeError):
            return content

    def _handle_user_prompt(self, agent: BlogContentAgent, prompt: str, session_id: str):
        """Handles user input by calling the agent and updating the state."""
        with st.spinner("⏳ 수정 사항 반영 중..."):
            response_data = agent.update_blog_post(prompt, session_id)

            if response_data.get("type") == "draft":
                st.session_state[SessionKey.BLOG_DRAFT] = response_data.get("content")

        st.rerun()

    def finalize_draft(self):
        """Saves the final draft to the session state for the publishing stage."""
        st.session_state[SessionKey.BLOG_POST] = st.session_state.get(SessionKey.BLOG_DRAFT)

