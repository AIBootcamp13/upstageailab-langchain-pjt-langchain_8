# src/ui/components/contents_editor.py
import streamlit as st
from langchain.memory import ConversationSummaryBufferMemory

from src.agent import BlogContentAgent
from src.ui.enums import SessionKey

class ContentsEditor:
    """
    BlogContentAgent를 사용하여 블로그 초안을 생성하고 수정하는 UI 컴포넌트.
    이제 대화형 메모리를 지원하여 연속적인 수정 요청을 처리합니다.
    """
    def render(self) -> bool:
        """Streamlit UI를 렌더링하고 콘텐츠 생성 및 수정 로직을 실행합니다."""
        st.subheader("초안 생성 및 퇴고")

        # --- 메모리 및 에이전트 초기화 로직 ---
        if SessionKey.BLOG_CREATOR_AGENT not in st.session_state:
            if SessionKey.RETRIEVER not in st.session_state:
                st.warning("먼저 파일을 업로드하여 Retriever를 초기화해야 합니다.")
                return False

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

        agent: BlogContentAgent = st.session_state[SessionKey.BLOG_CREATOR_AGENT]

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

        if st.button("발행 단계로 이동"):
            return True

        return False
