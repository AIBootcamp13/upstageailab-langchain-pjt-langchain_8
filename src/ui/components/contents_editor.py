# src/ui/components/contents_editor.py
import streamlit as st
import uuid

from src.agent import BlogContentAgent
from src.ui.enums import SessionKey

class ContentsEditor:
    """
    BlogContentAgent를 사용하여 블로그 초안을 생성하고 수정하는 UI 컴포넌트.
    이제 웹 검색 및 문서 검색이 가능한 Tool-Calling 에이전트를 사용합니다.
    """
    def render(self) -> bool:
        """Streamlit UI를 렌더링하고 콘텐츠 생성 및 수정 로직을 실행합니다."""
        st.subheader("초안 생성 및 퇴고")

        if "session_id" not in st.session_state:
            st.session_state.session_id = str(uuid.uuid4())
        
        session_id = st.session_state.session_id

        if SessionKey.BLOG_CREATOR_AGENT not in st.session_state:
            # Retriever와 함께 처리된 문서도 세션 상태에서 가져옵니다.
            if SessionKey.RETRIEVER not in st.session_state or "processed_documents" not in st.session_state:
                st.warning("먼저 파일을 업로드하여 Retriever와 문서를 초기화해야 합니다.")
                return False
            retriever = st.session_state[SessionKey.RETRIEVER]
            processed_docs = st.session_state["processed_documents"]
            # 에이전트 초기화 시 처리된 문서를 전달합니다.
            st.session_state[SessionKey.BLOG_CREATOR_AGENT] = BlogContentAgent(retriever, processed_docs)

        agent: BlogContentAgent = st.session_state[SessionKey.BLOG_CREATOR_AGENT]

        if SessionKey.BLOG_DRAFT not in st.session_state:
            if st.button("블로그 초안 생성하기", type="primary"):
                # agent.llm.model은 존재하지 않는 속성일 수 있으므로 모델 이름을 가져오는 방식을 수정합니다.
                model_name = agent.llm.model_name if hasattr(agent.llm, 'model_name') else agent.llm.model
                with st.spinner(f"초안 생성 중... (LLM: '{model_name}')"):
                    draft = agent.generate_draft(session_id)
                    st.session_state[SessionKey.BLOG_DRAFT] = draft
                st.rerun()

        if SessionKey.BLOG_DRAFT in st.session_state:
            st.markdown("---")
            st.markdown(st.session_state[SessionKey.BLOG_DRAFT])
            st.markdown("---")

            chat_history = agent.get_session_history(session_id).messages
            for message in chat_history:
                if message.type == "human":
                    with st.chat_message("user"):
                        st.markdown(message.content)
                elif message.type == "ai":
                    with st.chat_message("assistant"):
                        st.markdown(message.content)

            if prompt := st.chat_input("수정 요청 또는 문서/웹 검색을 입력하세요... (예: 문서에서 OVM의 장점을 요약해줘)"):
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    with st.spinner("요청을 처리하는 중..."):
                        updated_content = agent.update_blog_post(prompt, session_id)
                        st.session_state[SessionKey.BLOG_DRAFT] = updated_content
                        st.markdown(updated_content)
                        st.rerun()

        if st.button("발행 단계로 이동"):
            return True

        return False
