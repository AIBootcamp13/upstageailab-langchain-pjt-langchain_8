from dataclasses import dataclass

import streamlit as st
import uuid
import json
from dataclasses import dataclass

from src.agent import BlogContentAgent
from src.ui.enums import SessionKey

@dataclass(frozen=True)
class Message:
    """A class to represent a chat message, matching the sandbox UI style."""
    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"

    role: str
    contents: str

class ContentsEditor:
    """
    Renders the main editor UI, combining the sandbox UI style with the feature/memory-search agent.
    """

    def __init__(self):
        self.agent: BlogContentAgent | None = None

        if SessionKey.MESSAGE_LIST not in st.session_state:
            st.session_state[SessionKey.MESSAGE_LIST] = []

        if SessionKey.BLOG_DRAFT not in st.session_state:
            st.session_state[SessionKey.BLOG_DRAFT] = None

        if "user_request" not in st.session_state:
            st.session_state["user_request"] = None

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
    def user_request(self) -> str | None:
        return st.session_state["user_request"]

    @user_request.setter
    def user_request(self, value: str):
        st.session_state["user_request"] = value

    def add_message(self, message: Message):
        self.message_list.append(message)

    def finalize_draft(self):
        st.session_state[SessionKey.BLOG_POST] = self.draft

    def render(self) -> bool:
        """Renders the main editor UI."""
        st.subheader("초안 생성 및 퇴고")

        agent = self._initialize_agent()
        session_id = st.session_state.session_id

        if SessionKey.BLOG_DRAFT not in st.session_state:
            self._generate_draft_with_progress(agent, session_id)
            return False

        # Use the requested column layout with a small spacer
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
            model_name = agent.llm.model_name if hasattr(agent.llm, 'model_name') else agent.llm.model
            with st.status(f"💬 초안 생성 중... (LLM: '{model_name}')", expanded=True) as status:
                draft = agent.generate_draft(session_id)
                st.session_state[SessionKey.BLOG_DRAFT] = draft
                status.update(label="✅ 블로그 포스트 초안 생성 완료!", state="complete", expanded=False)
            st.rerun()

    def _render_draft_preview(self):
        """Renders the draft preview and markdown tabs."""
        # *** FIX: Wrap the entire panel in a single container for alignment. ***
        with st.container(height=750, border=True):
            st.markdown("##### **블로그 초안**")
            preview_tab, markdown_tab = st.tabs(["🖼️ Preview", "👨‍💻 Markdown"])
            
            with preview_tab:
                st.markdown(st.session_state.get(SessionKey.BLOG_DRAFT, ""))
            
            with markdown_tab:
                st.code(st.session_state.get(SessionKey.BLOG_DRAFT, ""), language="markdown")

    def _render_chat(self, agent: BlogContentAgent, session_id: str):
        """Renders the chat panel, adapting the agent's history to the Message dataclass."""
        # *** FIX: Wrap the entire panel in a single container for alignment. ***
        with st.container(height=750, border=True):
            st.markdown("##### **수정 및 대화**")
            
            chat_container = st.container(height=625)
            with chat_container:
                chat_history = agent.get_session_history(session_id).messages
                for msg in chat_history:
                    # Adapt LangChain's message object to the local Message dataclass
                    role = Message.ROLE_USER if msg.type == "human" else Message.ROLE_ASSISTANT
                    message = Message(role=role, contents=msg.content)
                    with st.chat_message(message.role):
                        content_to_display = self._parse_ai_message(message)
                        st.markdown(content_to_display)

            if user_request := st.chat_input("수정하고 싶은 내용을 입력하세요..."):
                self._handle_user_prompt(agent, user_request, session_id)

    def _parse_ai_message(self, message: Message) -> str:
        """Parses the AI's message content to decide what to display."""
        if message.role == Message.ROLE_USER:
            return message.contents
        try:
            data = json.loads(message.contents)
            if data.get("type") == "draft":
                return "초안이 수정되었습니다. 왼쪽 패널에서 확인 후 추가 요청을 해주세요."
            return data.get("content", message.contents)
        except (json.JSONDecodeError, TypeError):
            return message.contents

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
