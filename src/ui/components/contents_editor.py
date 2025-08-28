from dataclasses import dataclass

import streamlit as st
from langchain.memory import ConversationSummaryBufferMemory

from src.agent import BlogContentAgent
from src.ui.enums import SessionKey


@dataclass(frozen=True)
class Message:
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
    이제 대화형 메모리를 지원하여 연속적인 수정 요청을 처리합니다.
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

    def add_user_message(self, content: str):
        self.add_message(Message.create_as_user(content))

    def add_assistant_message(self, content: str):
        self.add_message(Message.create_as_assistant(content))

    def finalize_draft(self):
        st.session_state[SessionKey.BLOG_POST] = self.draft

    def render(self) -> bool:
        """Streamlit UI를 렌더링하고 콘텐츠 생성 및 수정 로직을 실행합니다."""
        st.subheader("초안 생성 및 퇴고")

<<<<<<< HEAD
        self.agent = self._initialize_agent()

        self._generate_draft_with_progress()

        draft_col, _, chat_col = st.columns([52, 1, 46])

        self._render_draft_preview(draft_col)

        self._render_chat(chat_col)

        if st.button("발행 단계로 이동"):
            self.finalize_draft()
            return True
        return False

    def _initialize_agent(self) -> BlogContentAgent:
        if SessionKey.RETRIEVER not in st.session_state:
            raise RuntimeError("먼저 파일을 업로드하여 Retriever를 초기화해야 합니다.")

        if SessionKey.BLOG_CREATOR_AGENT not in st.session_state:
=======
        # --- 메모리 및 에이전트 초기화 로직 ---
        if SessionKey.BLOG_CREATOR_AGENT not in st.session_state:
            if SessionKey.RETRIEVER not in st.session_state:
                st.warning("먼저 파일을 업로드하여 Retriever를 초기화해야 합니다.")
                return False

>>>>>>> feature/memory
            retriever = st.session_state[SessionKey.RETRIEVER]
            
            from src.config import LLM_PROVIDER, LLM_MODEL
            from langchain_openai import ChatOpenAI
            from langchain_ollama import ChatOllama

            if LLM_PROVIDER == "openai":
                llm = ChatOpenAI(model=LLM_MODEL)
            else:
                llm = ChatOllama(model=LLM_MODEL)
            
            memory = ConversationSummaryBufferMemory(
                llm=llm, 
                max_token_limit=1000,
                return_messages=True,
                memory_key="history",
                output_key="output"
            )
            st.session_state[SessionKey.MESSAGE_LIST] = memory

            st.session_state[SessionKey.BLOG_CREATOR_AGENT] = BlogContentAgent(retriever, memory)

        return st.session_state[SessionKey.BLOG_CREATOR_AGENT]

<<<<<<< HEAD
    def _generate_draft_with_progress(self):
        """초안이 없으면 초안을 생성하고, 있다면 그 값을 반환"""
        if self.draft:
            return
=======
        # 초안이 없으면 "초안 생성" 버튼을 표시합니다.
        if SessionKey.BLOG_DRAFT not in st.session_state:
            if st.button("블로그 초안 생성하기", type="primary"):
                with st.spinner(f"초안 생성 중... (LLM: '{agent.llm.model}')"):
                    draft = agent.generate_draft()
                    st.session_state[SessionKey.BLOG_DRAFT] = draft
                    agent.memory.save_context(
                        {"input": "초안을 생성해줘."},
                        {"output": draft}
                    )
                st.rerun()

        # 초안이 있으면 화면에 표시하고 수정 UI를 제공합니다.
        if SessionKey.BLOG_DRAFT in st.session_state:
            draft = st.session_state[SessionKey.BLOG_DRAFT]
            st.markdown("---")
            st.markdown(draft)
            st.markdown("---")

            if "messages" not in st.session_state:
                st.session_state.messages = []

            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            if prompt := st.chat_input("수정하고 싶은 내용을 입력하세요..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    # *** FIX: 스피너 메시지를 좀 더 일반적인 내용으로 변경 ***
                    with st.spinner("요청을 처리하는 중..."):
                        updated_draft = agent.update_blog_post(prompt)
                        st.session_state[SessionKey.BLOG_DRAFT] = updated_draft
                        st.markdown(updated_draft)
                        st.session_state.messages.append({"role": "assistant", "content": updated_draft})
>>>>>>> feature/memory

        with st.status(f"💬 초안 생성 중... (LLM: '{self.agent.llm.model_name}')", expanded=True) as status:
            self.draft = self.agent.generate_draft()
            status.update(label="✅  블로그 포스트 초안 생성 완료!", state="complete", expanded=False)

    def _render_draft_preview(self, draft_column):
        with draft_column:
            preview_tab, markdown_tab = st.tabs(["🖼️ Preview", "👨‍💻 Markdown"])
            with preview_tab:  # noqa: SIM117
                with st.container(height=720, width="stretch"):
                    st.markdown(self.draft)
            with markdown_tab:  # noqa: SIM117
                with st.container(height=720, width="stretch"):
                    st.code(self.draft, language="markdown")

    def _render_chat(self, chat_column):
        with chat_column:
            chat_container = st.container(height=720, width="stretch")
            with chat_container:
                for message in self.message_list:
                    with st.chat_message(message.role):
                        st.write(message.contents)
            self.user_request = st.chat_input("수정하고 싶은 내용을 입력하세요.")
            if self.user_request:
                with chat_container:  # noqa: SIM117
                    with st.chat_message(Message.ROLE_USER):
                        st.write(self.user_request)
                self.add_user_message(self.user_request)

        if self.user_request:
            with st.spinner("⏳ 수정 사항 반영 중..."):
                updated_draft = self.agent.update_blog_post(self.draft, self.user_request)

<<<<<<< HEAD
            self.draft = updated_draft
            self.add_assistant_message(f"'{self.user_request}' 를 반영했습니다.\n추가 요청이 있으신가요?")
            st.rerun()
=======
        return False
>>>>>>> feature/memory
