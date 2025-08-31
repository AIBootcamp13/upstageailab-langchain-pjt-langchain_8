# src/ui/chainlit/utils.py

from pathlib import Path

import chainlit as cl

from src.agent import BlogContentAgent
from src.document_preprocessor import DocumentPreprocessor
from src.retriever import RetrieverFactory
from src.ui.enums import SessionKey
from src.vector_store import VectorStore



async def setup_agent(
    llm_provider: str, llm_model: str, force_new_docs: bool = False
) -> BlogContentAgent | None:
    """
    에이전트를 설정하거나 세션에서 가져옵니다.
    필요한 경우 사용자에게 문서 업로드를 요청합니다.
    """
    if force_new_docs or not cl.user_session.get(SessionKey.RETRIEVER):
        files = None
        while files is None:
            files = await cl.AskFileMessage(
                content="시작하려면 블로그 초안의 기반이 될 PDF 파일을 업로드해주세요.",
                accept=["application/pdf"],
                max_size_mb=100,
                timeout=300,
                raise_on_timeout=False,
            ).send()

        if not files:
            return None

        file = files[0]
        msg = cl.Message(content=f"`{file.name}` 파일을 처리 중입니다...")
        await msg.send()

        file_path = Path(file.path)
        try:
            preprocessor = DocumentPreprocessor(file_path)
            documents = preprocessor.process()
            cl.user_session.set("processed_documents", documents)
            msg.content = f"✅ `{file.name}` 처리 완료: **{len(documents)}개**의 청크 생성됨."
            await msg.update()

            vector_store = VectorStore()
            vector_store.add_documents(documents)
            cl.user_session.set(SessionKey.VECTOR_STORE, vector_store)
            
            retriever = RetrieverFactory.create(vector_store)
            cl.user_session.set(SessionKey.RETRIEVER, retriever)
        finally:
            pass

        await cl.Message(content="✅ 리트리버 생성 완료! 에이전트를 설정합니다.").send()

    retriever = cl.user_session.get(SessionKey.RETRIEVER)
    processed_docs = cl.user_session.get("processed_documents")

    agent = BlogContentAgent(
        retriever=retriever,
        documents=processed_docs,
        llm_provider=llm_provider,
        llm_model=llm_model,
    )
    cl.user_session.set(SessionKey.BLOG_CREATOR_AGENT, agent)
    return agent


async def rebuild_agent_with_new_model(llm_provider: str, llm_model: str) -> None:
    """
    Rebuild or update the BlogContentAgent in the user session when the model/profile changes.
    This will recreate the agent using the existing retriever and processed documents.
    """
    retriever = cl.user_session.get(SessionKey.RETRIEVER)
    processed_docs = cl.user_session.get("processed_documents")

    if not retriever or not processed_docs:
        # If we don't have documents/retriever, prompt user to setup agent flow
        await cl.Message(content="새 모델을 적용하려면 먼저 문서를 업로드하세요.").send()
        return

    agent = BlogContentAgent(
        retriever=retriever,
        documents=processed_docs,
        llm_provider=llm_provider,
        llm_model=llm_model,
    )
    cl.user_session.set(SessionKey.BLOG_CREATOR_AGENT, agent)
    await cl.Message(content=f"✅ 모델이 `{llm_model}`(provider={llm_provider})로 업데이트되었습니다.").send()

    # If we have a session id, regenerate the initial draft with the new model
    session_id = cl.user_session.get(SessionKey.SESSION_ID)
    if session_id:
        # Run generate_draft in thread and stream the result progressively to the UI
        draft = await cl.make_async(agent.generate_draft)(session_id=session_id)
        cl.user_session.set(SessionKey.BLOG_DRAFT, draft)

        # Stream the regenerated draft to the user in small chunks for better UX
        draft_msg = cl.Message(content="", author="BlogGenerator")
        await draft_msg.send()
        # send progressively in small groups of characters
        chunk_size = 8
        for i in range(0, len(draft), chunk_size):
            part = draft[i : i + chunk_size]
            await draft_msg.stream_token(part)
        await draft_msg.update()
        # send token summary if available
        try:
            from src.tokens import format_usage_summary
            from chainlit.element import Text
            from chainlit.sidebar import ElementSidebar

            token_summary = format_usage_summary(session_id)
            sidebar_text = Text(content=f"📊 **세션 토큰 사용량**\n\n---\n\n{token_summary}")
            await ElementSidebar.set_title("Session Tokens")
            await ElementSidebar.set_elements([sidebar_text])
        except Exception:
            pass