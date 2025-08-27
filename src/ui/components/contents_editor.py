# src/ui/components/contents_editor.py
import streamlit as st

from src.agent import BlogContentAgent
from src.ui.enums import SessionKey

class ContentsEditor:
    """
    BlogContentAgent를 사용하여 블로그 초안을 생성하고 수정하는 UI 컴포넌트.
    Agent는 이제 중앙 설정에 따라 동적으로 LLM을 로드합니다.
    """
    def render(self) -> bool:
        """Streamlit UI를 렌더링하고 콘텐츠 생성 및 수정 로직을 실행합니다."""
        st.subheader("초안 생성 및 퇴고")

        # 세션에 BlogContentAgent가 없으면 새로 생성합니다.
        if SessionKey.BLOG_CREATOR_AGENT not in st.session_state:
            if SessionKey.RETRIEVER not in st.session_state:
                st.warning("먼저 파일을 업로드하여 Retriever를 초기화해야 합니다.")
                return False
            retriever = st.session_state[SessionKey.RETRIEVER]
            st.session_state[SessionKey.BLOG_CREATOR_AGENT] = BlogContentAgent(retriever)

        agent: BlogContentAgent = st.session_state[SessionKey.BLOG_CREATOR_AGENT]

        # 초안이 없으면 "초안 생성" 버튼을 표시합니다.
        if SessionKey.BLOG_DRAFT not in st.session_state:
            if st.button("블로그 초안 생성하기", type="primary"):
                # --- FIX: Changed agent.llm.model to agent.llm.model_name ---
                with st.spinner(f"초안 생성 중... (LLM: '{agent.llm.model_name}')"):
                    st.session_state[SessionKey.BLOG_DRAFT] = agent.generate_draft()
                st.rerun() # 초안을 표시하기 위해 UI를 새로고침합니다.

        # 초안이 있으면 화면에 표시하고 수정 UI를 제공합니다.
        if SessionKey.BLOG_DRAFT in st.session_state:
            draft = st.session_state[SessionKey.BLOG_DRAFT]
            st.markdown("---")
            st.markdown(draft)
            st.markdown("---")

            # 채팅 기반 수정 기능
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
                    with st.spinner("수정 사항을 반영하는 중..."):
                        updated_draft = agent.update_blog_post(
                            blog_post=st.session_state[SessionKey.BLOG_DRAFT],
                            user_request=prompt
                        )
                        st.session_state[SessionKey.BLOG_DRAFT] = updated_draft
                        st.markdown(updated_draft)
                        st.session_state.messages.append({"role": "assistant", "content": "수정되었습니다. 추가 요청이 있으신가요?"})

        if st.button("발행 단계로 이동"):
            return True

        return False