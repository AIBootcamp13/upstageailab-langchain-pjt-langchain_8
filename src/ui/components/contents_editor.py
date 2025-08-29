import json
import uuid
from dataclasses import dataclass

import streamlit as st

from src.agent import BlogContentAgent
from src.ui.enums import SessionKey
from vector_store import VectorStore


@dataclass(frozen=True)
class Message:
    """A class to represent a chat message."""

    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"

    role: str
    contents: str

    @classmethod
    def create_as_user(cls, contents: str) -> "Message":
        return cls(
            role=cls.ROLE_USER,
            contents=contents,
        )

    @classmethod
    def create_as_assistant(cls, contents: str) -> "Message":
        return cls(
            role=cls.ROLE_ASSISTANT,
            contents=contents,
        )


class ContentsEditor:
    """
    BlogContentAgent를 사용하여 블로그 초안을 생성하고 수정하는 UI 컴포넌트.
    Agent는 이제 중앙 설정에 따라 동적으로 LLM을 로드합니다.
    """

    def __init__(self):
        self.agent: BlogContentAgent | None = None

        if SessionKey.MESSAGE_LIST not in st.session_state:
            st.session_state[SessionKey.MESSAGE_LIST] = []

        if SessionKey.BLOG_DRAFT not in st.session_state:
            st.session_state[SessionKey.BLOG_DRAFT] = None

        if SessionKey.SESSION_ID not in st.session_state:
            self.session_id = str(uuid.uuid4())

    @property
    def message_list(self) -> list[Message]:
        return st.session_state[SessionKey.MESSAGE_LIST]

    @property
    def draft(self) -> str | None:
        return st.session_state[SessionKey.BLOG_DRAFT]

    @draft.setter
    def draft(self, value: str):
        st.session_state[SessionKey.BLOG_DRAFT] = value

    @property
    def session_id(self) -> str:
        return st.session_state[SessionKey.SESSION_ID]

    @session_id.setter
    def session_id(self, value: str):
        st.session_state[SessionKey.SESSION_ID] = value

    def add_message(self, message: Message):
        self.message_list.append(message)

    def add_user_message(self, content: str):
        self.add_message(Message.create_as_user(content))

    def add_assistant_message(self, content: str):
        self.add_message(Message.create_as_assistant(content))

    def finalize_draft(self):
        st.session_state[SessionKey.BLOG_POST] = self.draft

    def render(self) -> bool:
        """Renders the main editor UI."""
        st.subheader("초안 생성 및 퇴고")

        agent = self._initialize_agent()

        self._generate_draft_with_progress(agent)

        # Use a two-column layout with a small spacer
        draft_col, _, chat_col = st.columns([52, 1, 46])

        with draft_col:
            self._render_draft_preview()

        with chat_col:
            self._render_chat(agent)

        if st.button("발행 단계로 이동"):
            self.finalize_draft()
            return True
        return False

    def _initialize_agent(self) -> BlogContentAgent:
        """Initializes the BlogContentAgent if not already in the session."""
        if SessionKey.VECTOR_STORE not in st.session_state:
            raise RuntimeError("먼저 파일을 업로드하여 VectorStore를 초기화해야 합니다.")

        if SessionKey.RETRIEVER not in st.session_state:
            raise RuntimeError("먼저 파일을 업로드하여 Retriever를 초기화해야 합니다.")

        if SessionKey.BLOG_CREATOR_AGENT not in st.session_state:
            retriever = st.session_state[SessionKey.RETRIEVER]
            vector_store: VectorStore = st.session_state[SessionKey.VECTOR_STORE]
            st.session_state[SessionKey.BLOG_CREATOR_AGENT] = BlogContentAgent(
                retriever, vector_store.get_all_documents()
            )

        return st.session_state[SessionKey.BLOG_CREATOR_AGENT]

    def _generate_draft_with_progress(self, agent: BlogContentAgent):
        """초안이 없으면 초안을 생성하고, 있다면 그 값을 반환"""
        if self.draft:
            return

        model_name = agent.llm.model_name if hasattr(agent.llm, "model_name") else agent.llm.model
        with st.status(f"💬 초안 생성 중... (LLM: '{model_name}')", expanded=True) as status:
            self.draft = agent.generate_draft(self.session_id)
            status.update(label="✅ 블로그 포스트 초안 생성 완료!", state="complete", expanded=False)

    def _render_draft_preview(self):
        """Renders the draft preview and markdown tabs within a bordered container."""
        with st.container(height=750, border=True):
            st.markdown("##### **블로그 초안**")
            preview_tab, markdown_tab = st.tabs(["🖼️ Preview", "👨‍💻 Markdown"])

            with preview_tab:
                st.markdown(self.draft)

            with markdown_tab:
                st.code(self.draft, language="markdown")

    def _render_chat(self, agent: BlogContentAgent):
        """Renders the chat panel within a bordered container."""
        with st.container(height=750, border=True):
            st.markdown("##### **수정 및 대화**")

            chat_container = st.container(height=625)
            with chat_container:
                chat_history = agent.get_session_history(self.session_id).messages
                for msg in chat_history:
                    role = Message.ROLE_USER if msg.type == "human" else Message.ROLE_ASSISTANT
                    with st.chat_message(role):
                        content_to_display = self._parse_ai_message(msg.content, role)
                        st.markdown(content_to_display)

            if user_request := st.chat_input("수정하고 싶은 내용을 입력하세요..."):
                self._handle_user_prompt(agent, user_request)

    def _parse_ai_message(self, content: str, role: str) -> str:
        """Parses the AI's message content to decide what to display."""
        if role == Message.ROLE_USER:
            return content
        try:
            data = json.loads(content)
            if data.get("type") == "draft":
                return "초안이 수정되었습니다. 왼쪽 패널에서 확인 후 추가 요청을 해주세요."
            return data.get("content", content)
        except (json.JSONDecodeError, TypeError):
            return content

    def _handle_user_prompt(self, agent: BlogContentAgent, prompt: str):
        """Handles user input by calling the agent and updating the state."""
        with st.spinner("⏳ 수정 사항 반영 중..."):
            response_data = agent.update_blog_post(prompt, self.session_id)

            if response_data.get("type") == "draft":
                self.draft = response_data.get("content")
        st.rerun()
