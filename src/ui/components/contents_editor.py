import streamlit as st

from src.agent import BlogContentAgent
from src.ui.enums import SessionKey


class ContentsEditor:
    """BlogCreatorAgent 를 사용해서 블로그 초안을 만들고, 블로그 글을 수정하는 클래스"""

    def render(self) -> bool:
        st.subheader("초안 퇴고하기")

        if st.button("다음"):
            return True

        if SessionKey.BLOG_CREATOR_AGENT not in st.session_state:
            retriever = st.session_state[SessionKey.RETRIEVER]
            st.session_state[SessionKey.BLOG_CREATOR_AGENT] = BlogContentAgent(retriever)

        agent: BlogContentAgent = st.session_state[SessionKey.BLOG_CREATOR_AGENT]

        if SessionKey.BLOG_DRAFT not in st.session_state:
            with st.spinner("초안 생성 중"):
                st.session_state[SessionKey.BLOG_DRAFT] = agent.generate_draft()

        draft = st.session_state[SessionKey.BLOG_DRAFT]
        st.markdown(draft)

        if SessionKey.MESSAGE_LIST not in st.session_state:
            st.session_state.message_list = []

        for message in st.session_state.message_list:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        if user_input := st.chat_input(placeholder="수정사항을 입력해주세요."):
            with st.chat_message("user"):
                st.write(user_input)

            st.session_state.message_list.append(
                {
                    "role": "user",
                    "content": user_input,
                }
            )

        return False
