# src/ui/components/contents_editor.py
import streamlit as st
import uuid
import json

from src.agent import BlogContentAgent
from src.ui.enums import SessionKey

class ContentsEditor:
    """
    BlogContentAgent를 사용하여 블로그 초안을 생성하고 수정하는 UI 컴포넌트.
    라이브 프리뷰, 마크다운 탭, 별도의 채팅 패널을 갖춘 UI를 제공합니다.
    """
    def render(self) -> bool:
        """Streamlit UI를 렌더링하고 콘텐츠 생성 및 수정 로직을 실행합니다."""
        st.subheader("초안 생성 및 퇴고")

        agent = self._initialize_agent()
        session_id = st.session_state.session_id

        if SessionKey.BLOG_DRAFT not in st.session_state:
            self._generate_draft_if_needed(agent, session_id)
            return False

        draft_col, chat_col = st.columns([0.6, 0.4])

        with draft_col:
            self._render_draft_editor()

        with chat_col:
            self._render_chat_panel(agent, session_id)

        if st.button("발행 단계로 이동"):
            return True
        return False

    def _initialize_agent(self) -> BlogContentAgent:
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

    def _generate_draft_if_needed(self, agent: BlogContentAgent, session_id: str):
        if st.button("블로그 초안 생성하기", type="primary"):
            model_name = agent.llm.model_name if hasattr(agent.llm, 'model_name') else agent.llm.model
            with st.spinner(f"초안 생성 중... (LLM: '{model_name}')"):
                draft = agent.generate_draft(session_id)
                st.session_state[SessionKey.BLOG_DRAFT] = draft
            st.rerun()

    def _render_draft_editor(self):
        """Renders the draft editor with preview and markdown tabs."""
        # *** FIX: Wrap the editor in a container to match the chat panel. ***
        with st.container(height=700, border=True):
            st.markdown("##### **블로그 초안**")
            preview_tab, markdown_tab = st.tabs(["🖼️ Preview", "👨‍💻 Markdown"])
            
            with preview_tab:
                st.markdown(st.session_state.get(SessionKey.BLOG_DRAFT, ""))
            
            with markdown_tab:
                st.code(st.session_state.get(SessionKey.BLOG_DRAFT, ""), language="markdown")

    def _render_chat_panel(self, agent: BlogContentAgent, session_id: str):
        """Renders the chat panel for conversation and edits."""
        with st.container(height=700, border=True):
            st.markdown("##### **수정 및 대화**")
            
            chat_history = agent.get_session_history(session_id).messages
            for message in chat_history:
                role = "user" if message.type == "human" else "assistant"
                with st.chat_message(role):
                    content_to_display = self._parse_ai_message(message.content, role)
                    st.markdown(content_to_display)

            if prompt := st.chat_input("수정 요청 또는 질문을 입력하세요..."):
                self._handle_user_prompt(agent, prompt, session_id)

    def _parse_ai_message(self, message_content: str, role: str) -> str:
        """Parses AI's JSON response to determine what to display in the chat."""
        if role == "user":
            return message_content
        try:
            data = json.loads(message_content)
            if data.get("type") == "draft":
                return "초안이 수정되었습니다. 왼쪽 패널에서 확인 후 추가 요청을 해주세요."
            return data.get("content", message_content)
        except (json.JSONDecodeError, TypeError):
            return message_content

    def _handle_user_prompt(self, agent: BlogContentAgent, prompt: str, session_id: str):
        with st.spinner("요청을 처리하는 중..."):
            response_data = agent.update_blog_post(prompt, session_id)
            
            if response_data.get("type") == "draft":
                st.session_state[SessionKey.BLOG_DRAFT] = response_data.get("content")
        
        st.rerun()
