import json
import uuid
from dataclasses import dataclass
from typing import Any, Iterable, Optional

import streamlit as st

from src.agent import BlogContentAgent
from src.ui.enums import SessionKey
from src.artifacts import save_artifact, list_artifacts


@dataclass(frozen=True)
class Message:
    """A class to represent a chat message."""
    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"

    role: str
    contents: str


class ContentsEditor:
    """A Streamlit content editor with improved layout and styling."""
    def __init__(self):
        # inject base styles once
        self._inject_base_styles()

        # ensure session defaults
        if "panel_ratio" not in st.session_state:
            st.session_state.panel_ratio = 60  # left panel percent (default)

    def _inject_base_styles(self):
        st.markdown(
            """
            <style>
            /* Panel box */
            .panel-box {
                border: 1px solid #e6e9ef;
                border-radius: 10px;
                padding: 12px;
                background: var(--bg-color, #ffffff);
                box-shadow: 0 1px 4px rgba(16,24,40,0.03);
                max-height: 700px;
                overflow: auto;
            }

            /* Chat specific */
            .chat-container {
                max-height: 520px;
                overflow-y: auto;
                padding: 8px;
            }
            .msg {
                margin-bottom: 10px;
                padding: 10px 12px;
                border-radius: 10px;
                display: inline-block;
                max-width: 78%;
                word-wrap: break-word;
            }
            .msg.user {
                background: #eef2ff;
                color: #0f172a;
                float: right;
                text-align: right;
                clear: both;
            }
            .msg.assistant {
                background: #f8fafc;
                color: #0f172a;
                float: left;
                clear: both;
            }
            .msg .meta {
                display:block;
                font-size: 11px;
                color: #6b7280;
                margin-top: 6px;
            }

            /* Button sizing */
            .stButton>button {
                padding: 6px 10px !important;
                font-size: 13px !important;
                border-radius: 6px !important;
            }

            /* Small helpers */
            .refresh-btn { margin-top: 4px; }
            </style>
            """,
            unsafe_allow_html=True,
        )

    def render(self) -> bool:
        """Renders the main editor UI with responsive layout."""
        st.subheader("초안 생성 및 퇴고")

        agent = self._initialize_agent()
        session_id = st.session_state.session_id

        if SessionKey.BLOG_DRAFT not in st.session_state:
            self._generate_draft_with_progress(agent, session_id)
            return False

        # Layout selection
        layout_option = st.radio(
            "레이아웃 선택",
            ["나란히 보기", "탭으로 보기"],
            horizontal=True,
            help="화면 크기에 따라 편한 레이아웃을 선택하세요"
        )

        st.markdown("---")  # Visual separator

        if layout_option == "나란히 보기":
            self._render_side_by_side_layout(agent, session_id)
        else:
            self._render_tabbed_layout(agent, session_id)

        # Action button (always at the bottom)
        st.markdown("---")
        if st.button("발행 단계로 이동", type="primary"):
            self.finalize_draft()
            return True
        return False

    def _render_side_by_side_layout(self, agent: BlogContentAgent, session_id: str):
        """Renders the side-by-side layout for larger screens with adjustable ratio."""
        # Slider to adjust left panel width; persist in session_state
        left_percent = st.slider(
            "왼쪽 패널 넓이 (%)", min_value=30, max_value=70,
            value=st.session_state.get("panel_ratio", 60),
            key="panel_ratio_slider",
            help="초안 영역과 채팅 영역의 비율을 조정할 수 있습니다."
        )
        st.session_state.panel_ratio = left_percent

        left_col, right_col = st.columns([int(left_percent), int(100 - left_percent)])

        with left_col:
            self._render_draft_section()

        with right_col:
            self._render_chat_section(agent, session_id)

    def _render_tabbed_layout(self, agent: BlogContentAgent, session_id: str):
        """Renders the tabbed layout for better mobile experience."""
        draft_tab, chat_tab = st.tabs(["📝 블로그 초안", "💬 수정 및 대화"])

        with draft_tab:
            self._render_draft_section()

        with chat_tab:
            self._render_chat_section(agent, session_id)

    def _box_start(self, height_px: Optional[int] = None):
        style = f"max-height: {height_px}px;" if height_px else ""
        st.markdown(f'<div class="panel-box" style="{style}">', unsafe_allow_html=True)

    def _box_end(self):
        st.markdown("</div>", unsafe_allow_html=True)

    def _render_draft_section(self):
        """Renders the draft preview section."""
        st.markdown("##### **블로그 초안**")

        # Add refresh button for draft (right aligned)
        c_left, c_right = st.columns([3, 2])
        with c_right:
            if st.button("🔄 새로고침", help="초안을 새로고침합니다", key="refresh_draft"):
                st.rerun()
            # Quick export buttons
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("💾 초안 저장", key="save_draft_btn"):
                    draft = st.session_state.get(SessionKey.BLOG_DRAFT, "")
                    if draft:
                        meta = save_artifact(st.session_state.session_id, "blog-draft", draft, kind="draft", ext="md")
                        st.toast(f"초안 저장됨: {meta.file_path.name}")
            with col_b:
                if st.button("💾 본문 저장", key="save_post_btn"):
                    post = st.session_state.get(SessionKey.BLOG_POST, "") or st.session_state.get(SessionKey.BLOG_DRAFT, "")
                    if post:
                        meta = save_artifact(st.session_state.session_id, "blog-post", post, kind="post", ext="md")
                        st.toast(f"본문 저장됨: {meta.file_path.name}")

        # Panel box for content
        self._box_start(height_px=700)

        preview_tab, markdown_tab, stats_tab = st.tabs(["🖼️ Preview", "👨‍💻 Markdown", "📊 통계"])

        draft_content = st.session_state.get(SessionKey.BLOG_DRAFT, "")

        with preview_tab:
            if draft_content:
                st.markdown(draft_content)
            else:
                st.info("아직 생성된 초안이 없습니다.")

        with markdown_tab:
            if draft_content:
                st.code(draft_content, language="markdown")
            else:
                st.info("아직 생성된 초안이 없습니다.")

        with stats_tab:
            if draft_content:
                self._render_draft_statistics(draft_content)
            else:
                st.info("아직 생성된 초안이 없습니다.")

        self._box_end()

        # List artifacts for this session
        st.markdown("###### 생성된 아티팩트")
        artifacts = list_artifacts(st.session_state.session_id)
        if artifacts:
            for a in artifacts[:5]:
                with st.container(border=True):
                    st.caption(f"{a.created_at} • {a.kind} • {a.size} bytes")
                    st.write(a.name)
                    with open(a.file_path, "rb") as f:
                        st.download_button("다운로드", f, file_name=a.file_path.name, key=f"dl-{a.id}")
        else:
            st.caption("아직 저장된 아티팩트가 없습니다.")

    def _render_draft_statistics(self, draft_content: str):
        """Renders statistics about the draft."""
        # Basic statistics
        word_count = len(draft_content.split())
        char_count = len(draft_content)
        char_count_no_spaces = len(draft_content.replace(" ", ""))
        line_count = len(draft_content.split("\n"))

        # Display statistics in columns
        col1, col2 = st.columns(2)

        with col1:
            st.metric("단어 수", word_count)
            st.metric("문자 수 (공백 포함)", char_count)

        with col2:
            st.metric("문자 수 (공백 제외)", char_count_no_spaces)
            st.metric("줄 수", line_count)

        # Reading time estimation (assuming 200 words per minute for Korean)
        reading_time = max(1, round(word_count / 200))
        st.metric("예상 읽기 시간", f"{reading_time}분")

        # Header analysis
        headers = [line for line in draft_content.split("\n") if line.strip().startswith("#")]
        if headers:
            st.markdown("**제목 구조:**")
            for header in headers:
                level = len(header) - len(header.lstrip("#"))
                indent = "  " * (level - 1)
                st.text(f"{indent}• {header.strip('#').strip()}")

    def _render_chat_section(self, agent: BlogContentAgent, session_id: str):
        """Renders the chat section with improved UX."""
        st.markdown("##### **수정 및 대화**")

        # Chat controls (small buttons)
        col_left, col_mid, col_right = st.columns([2, 1, 1])
        with col_left:
            st.write("")  # spacer
        with col_mid:
            if st.button("🗑️ 대화 초기화", help="대화 기록을 초기화합니다", key="clear_chat"):
                self._clear_chat_history(agent, session_id)
                st.rerun()
        with col_right:
            auto_scroll = st.checkbox("자동 스크롤", value=True, help="새 메시지 시 자동으로 스크롤", key="auto_scroll")

        # Chat panel box
        self._box_start(height_px=700)

        # Messages container (HTML)
        history_html = self._render_chat_messages_html(agent, session_id)
        st.markdown(history_html, unsafe_allow_html=True)

        st.markdown("---")
        self._render_chat_input_section(agent, session_id)

        self._box_end()

    def _render_chat_messages_html(self, agent: BlogContentAgent, session_id: str) -> str:
        """Build an HTML string representing the chat history in a scrollable container."""
        history = None
        try:
            history = agent.get_session_history(session_id)
        except Exception:
            history = None

        messages: Optional[Iterable[Any]] = None
        if history is not None:
            # Try common access patterns in a robust way
            if hasattr(history, "messages"):
                messages = getattr(history, "messages")
            elif hasattr(history, "history"):
                messages = getattr(history, "history")
            elif hasattr(history, "get_messages"):
                try:
                    messages = history.get_messages()
                except Exception:
                    messages = None
            elif isinstance(history, (list, tuple)):
                messages = history

        # Render HTML
        html = ['<div class="chat-container">']
        if not messages:
            html.append('<div style="color:#6b7280;">대화가 없습니다. 오른쪽의 입력창에서 시작하세요.</div>')
        else:
            for m in messages:
                # support dict-like or objects
                role = None
                text = ""
                if isinstance(m, dict):
                    role = m.get("role") or m.get("sender") or m.get("type")
                    # try various content keys
                    text = (
                        m.get("content")
                        or m.get("message")
                        or m.get("text")
                        or m.get("body")
                        or ""
                    )
                else:
                    role = getattr(m, "role", None) or getattr(m, "sender", None) or getattr(m, "type", None)
                    text = getattr(m, "content", None) or getattr(m, "text", None) or getattr(m, "message", None) or str(m)

                # If assistant content is a JSON string like {"type": "chat"|"draft", "content": "..."}, parse it
                if isinstance(text, str):
                    try:
                        payload = json.loads(text)
                        if isinstance(payload, dict) and "content" in payload:
                            text = payload.get("content", text)
                    except Exception:
                        pass

                role = (role or "").lower()
                safe_text = str(text).replace("\n", "<br/>")
                if role in ("user", "human"):
                    html.append(f'<div class="msg user">{safe_text}</div>')
                else:
                    html.append(f'<div class="msg assistant">{safe_text}</div>')
        html.append("</div>")
        return "".join(html)

    def _render_chat_input_section(self, agent: BlogContentAgent, session_id: str):
        """Renders the chat input section with quick actions."""
        st.markdown("**빠른 수정 요청:**")
        qa_col1, qa_col2 = st.columns([1, 1])

        with qa_col1:
            if st.button("📝 문체 개선", key="qa_style"):
                self._handle_quick_action("문체를 더 자연스럽고 읽기 쉽게 개선해주세요.", agent, session_id)
            if st.button("📏 길이 조정", key="qa_length"):
                self._handle_quick_action("내용을 더 간결하게 요약해주세요.", agent, session_id)

        with qa_col2:
            if st.button("🎯 구조 개선", key="qa_structure"):
                self._handle_quick_action("글의 구조와 흐름을 개선해주세요.", agent, session_id)
            if st.button("✨ 제목 개선", key="qa_title"):
                self._handle_quick_action("제목을 더 매력적으로 개선해주세요.", agent, session_id)

        # Custom input using st.chat_input
        prompt = st.chat_input("수정하고 싶은 내용을 입력하세요...", key="user_chat_input")
        if prompt:
            self._handle_user_input(prompt, agent, session_id)

    def _handle_quick_action(self, action_prompt: str, agent: BlogContentAgent, session_id: str):
        """Handles quick action button clicks."""
        if st.session_state.get("processing_chat", False):
            st.warning("이미 처리 중입니다. 잠시 기다려주세요.")
            return

        self._handle_user_input(action_prompt, agent, session_id)

    def _handle_user_input(self, prompt: str, agent: BlogContentAgent, session_id: str):
        """Handles user input from chat or quick actions."""
        if st.session_state.get("processing_chat", False):
            return

        st.session_state.processing_chat = True

        try:
            # Add to history BEFORE generating a response
            history = agent.get_session_history(session_id)
            # many history objects provide add_user_message; try gracefully
            try:
                history.add_user_message(prompt)
            except Exception:
                # fallback: try append to list-like history
                try:
                    if hasattr(history, "messages") and isinstance(history.messages, list):
                        history.messages.append({"role": "user", "content": prompt})
                except Exception:
                    pass

            # Generate and display the AI's response
            with st.chat_message(Message.ROLE_ASSISTANT):
                response_generator = agent.get_response(
                    user_request=prompt,
                    draft=st.session_state.get(SessionKey.BLOG_DRAFT, ""),
                    session_id=session_id
                )

                # Process the stream from the agent
                self._process_agent_stream(response_generator)
        finally:
            st.session_state.processing_chat = False

        # Clear the input and refresh to show updated history
        st.rerun()

    def _process_agent_stream(self, response_generator: Any):
        """Consume a streaming generator (or an immediate response)."""
        # This is intentionally generic: if response_generator yields partial strings,
        # we write them to the chat message area (st.chat_message context used by caller).
        try:
            # Use a placeholder to progressively update streamed content
            placeholder = st.empty()
            if hasattr(response_generator, "__iter__") and not isinstance(response_generator, str):
                draft_accum = ""
                chat_accum = ""
                for chunk in response_generator:
                    if isinstance(chunk, dict):
                        ctype = chunk.get("type")
                        piece = str(chunk.get("content", ""))
                    else:
                        ctype = None
                        piece = str(chunk)

                    if ctype == "draft":
                        draft_accum += piece
                        # Show draft deltas in the assistant bubble as well
                        placeholder.markdown(draft_accum)
                    else:
                        chat_accum += piece
                        placeholder.markdown(chat_accum)

                # Update draft in session state if modified
                if draft_accum:
                    st.session_state[SessionKey.BLOG_DRAFT] = draft_accum
                # Ensure final content remains visible
                placeholder.markdown(draft_accum or chat_accum)
            else:
                # non-iterable or immediate string
                placeholder.markdown(str(response_generator))
        except Exception as e:
            st.error(f"응답 처리 중 오류가 발생했습니다: {e}")

    def _clear_chat_history(self, agent: BlogContentAgent, session_id: str):
        """Clears the chat history for the current session."""
        history = agent.get_session_history(session_id)
        try:
            history.clear()
        except Exception:
            # fallback: try clearing list-like
            if hasattr(history, "messages") and isinstance(history.messages, list):
                history.messages.clear()
        st.success("대화 기록이 초기화되었습니다.")

    def _initialize_agent(self) -> BlogContentAgent:
        """Initializes or updates the BlogContentAgent based on the selected model."""
        if "session_id" not in st.session_state:
            st.session_state.session_id = str(uuid.uuid4())

        selected_provider = st.session_state.get("selected_llm_provider")
        selected_model = st.session_state.get("selected_llm_model")

        if not selected_provider or not selected_model:
            st.warning("LLM Provider와 Model을 선택해주세요.")
            st.stop()

        current_agent_model = st.session_state.get("current_agent_model")

        # If agent is missing or model changed, (re)create agent
        if current_agent_model != selected_model or SessionKey.BLOG_CREATOR_AGENT not in st.session_state:
            retriever = st.session_state.get(SessionKey.RETRIEVER)
            processed_docs = st.session_state.get("processed_documents")

            if retriever is None or not processed_docs:
                st.warning("먼저 문서를 업로드해 벡터스토어를 초기화해주세요.")
                st.stop()

            # Attempt to construct BlogContentAgent with common kwargs
            try:
                agent = BlogContentAgent(
                    retriever=retriever,
                    documents=processed_docs,
                    llm_provider=selected_provider,
                    llm_model=selected_model,
                )
            except TypeError:
                # Fallback if BlogContentAgent signature differs
                agent = BlogContentAgent(retriever, processed_docs, selected_provider, selected_model)

            st.session_state[SessionKey.BLOG_CREATOR_AGENT] = agent
            st.session_state["current_agent_model"] = selected_model

        return st.session_state[SessionKey.BLOG_CREATOR_AGENT]

    # Placeholder for missing functions referenced earlier in your original file.
    # Keep these methods, and replace with your real implementations if different.
    def _generate_draft_with_progress(self, agent: BlogContentAgent, session_id: str):
        """Generate initial draft with a simple progress indicator using the agent."""
        with st.status("초안을 생성 중입니다...", expanded=True) as status:
            st.write("문서를 분석하고 있어요…")
            draft = agent.generate_draft(session_id)
            st.session_state[SessionKey.BLOG_DRAFT] = draft
            status.update(label="초안 생성 완료", state="complete")

    def finalize_draft(self):
        """Finalize the current draft and make it available for publishing."""
        draft = st.session_state.get(SessionKey.BLOG_DRAFT, "")
        if not draft:
            st.warning("이동할 초안이 없습니다.")
            return
        # 기본적으로 초안을 발행 대상 본문으로 복사
        st.session_state[SessionKey.BLOG_POST] = draft
        st.success("초안이 발행 단계로 이동되었습니다.")
