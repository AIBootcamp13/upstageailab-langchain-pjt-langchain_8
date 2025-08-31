import asyncio
import os
import tempfile
import uuid
from pathlib import Path
from typing import Optional

import chainlit as cl

from src.agent import BlogContentAgent
from src.config import CONFIG, ACTIVE_PROFILE
from src.document_preprocessor import DocumentPreprocessor
from src.retriever import RetrieverFactory
from src.ui.enums import SessionKey
from src.vector_store import VectorStore
from src.artifacts import save_artifact, list_artifacts
from src.tokens import format_usage_summary


def _get_default_provider_and_model() -> tuple[str, str]:
    provider = ACTIVE_PROFILE.get("llm_provider")
    model = ACTIVE_PROFILE.get("llm_model")
    return provider, model


async def _ensure_ingestion() -> tuple[VectorStore, list]:
    vector_store: Optional[VectorStore] = cl.user_session.get(SessionKey.VECTOR_STORE)
    docs: Optional[list] = cl.user_session.get("processed_documents")
    if vector_store and docs:
        return vector_store, docs

    await cl.Message(content="업로드할 파일을 첨부해주세요 (PDF/MD/코드).", author="system").send()
    try:
        files = await cl.AskFileMessage(
            content="파일을 업로드하세요",
            accept=["application/pdf", "text/markdown", "text/plain"],
            max_size_mb=25,
            max_files=3,
        ).send()
    except Exception:
        # Likely headless mode or no UI client connected
        await cl.Message(content="파일 업로드 프롬프트를 건너뜁니다 (headless/무UI). 빈 지식으로 시작합니다.", author="system").send()
        files = []
    gathered_docs = []
    for f in files or []:
        # Try to extract raw bytes or a temporary file path depending on Chainlit version
        fname = getattr(f, "name", "upload")
        content_bytes = getattr(f, "content", None)
        fpath = getattr(f, "path", None) or getattr(f, "local_path", None)
        tmp_created = False
        if content_bytes is None and fpath and os.path.exists(str(fpath)):
            try:
                with open(fpath, "rb") as _rf:
                    content_bytes = _rf.read()
            except Exception:
                content_bytes = None
        if content_bytes is None:
            # Skip files we cannot read in this runtime
            await cl.Message(content=f"파일을 읽을 수 없습니다: {fname} (건너뜀)", author="system").send()
            continue

        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(fname).suffix or "") as tmp:
            tmp.write(content_bytes)
            path = Path(tmp.name)
            tmp_created = True
        try:
            pre = DocumentPreprocessor(path)
            parts = pre.process()
            gathered_docs.extend(parts)
        finally:
            if tmp_created and path.exists():
                path.unlink(missing_ok=True)

    vs = VectorStore()
    if gathered_docs:
        vs.add_documents(gathered_docs)
    cl.user_session.set(SessionKey.VECTOR_STORE, vs)
    cl.user_session.set("processed_documents", gathered_docs)
    return vs, gathered_docs


def _build_agent(provider: str, model: str, retriever, docs) -> BlogContentAgent:
    return BlogContentAgent(retriever=retriever, documents=docs, llm_provider=provider, llm_model=model)


def _rebuild_agent_preserve_history(provider: str, model: str):
    session_id: str = cl.user_session.get(SessionKey.SESSION_ID)
    old_agent: BlogContentAgent = cl.user_session.get(SessionKey.BLOG_CREATOR_AGENT)
    vs: VectorStore = cl.user_session.get(SessionKey.VECTOR_STORE)
    docs = cl.user_session.get("processed_documents", [])
    retriever = RetrieverFactory.create(vs)
    new_agent = _build_agent(provider, model, retriever, docs)
    # preserve history for this session
    if old_agent is not None:
        try:
            hist = old_agent.get_session_history(session_id)
            new_agent.session_histories[session_id] = hist
        except Exception:
            pass
    cl.user_session.set(SessionKey.BLOG_CREATOR_AGENT, new_agent)
    cl.user_session.set("selected_llm_provider", provider)
    cl.user_session.set("selected_llm_model", model)


@cl.on_chat_start
async def on_chat_start():
    session_id = str(uuid.uuid4())
    cl.user_session.set(SessionKey.SESSION_ID, session_id)

    provider, model = _get_default_provider_and_model()
    cl.user_session.set("selected_llm_provider", provider)
    cl.user_session.set("selected_llm_model", model)

    vs, docs = await _ensure_ingestion()
    retriever = RetrieverFactory.create(vs)

    agent = _build_agent(provider, model, retriever, docs)
    cl.user_session.set(SessionKey.BLOG_CREATOR_AGENT, agent)

    await cl.Message(content=f"모델: {provider}/{model}\n문서 수: {len(docs)}", author="system").send()
    # Generate initial draft
    draft = agent.generate_draft(session_id)
    cl.user_session.set(SessionKey.BLOG_DRAFT, draft)
    await cl.Message(content=draft, author="assistant").send()


@cl.on_message
async def on_message(message: cl.Message):
    agent: BlogContentAgent = cl.user_session.get(SessionKey.BLOG_CREATOR_AGENT)
    session_id: str = cl.user_session.get(SessionKey.SESSION_ID)
    draft: str = cl.user_session.get(SessionKey.BLOG_DRAFT, "")

    # Slash-command router for Chainlit versions without on_command
    content = (message.content or "").strip()
    if content.startswith("/"):
        handled = await _handle_slash_command(content)
        if handled:
            return

    if not agent:
        await cl.Message(content="세션이 초기화되었습니다. /reset 후 다시 시작해주세요.", author="system").send()
        return

    # Prepare an assistant message to stream into
    stream_msg = cl.Message(content="", author="assistant")
    await stream_msg.send()

    # Get the streaming generator
    gen = agent.get_response(user_request=message.content, draft=draft, session_id=session_id)

    new_draft = draft
    async def run_stream():
        nonlocal new_draft
        loop = asyncio.get_running_loop()
        # agent.get_response is a sync generator; iterate in a thread to avoid blocking
        def iterate():
            for chunk in gen:
                yield chunk

        for chunk in iterate():
            if isinstance(chunk, dict):
                ctype = chunk.get("type")
                piece = str(chunk.get("content", ""))
            else:
                ctype = None
                piece = str(chunk)

            if ctype == "draft":
                new_draft += piece
                # update silently; don't spam UI for each token
            else:
                await stream_msg.stream_token(piece)

    await run_stream()
    # finalize
    await stream_msg.update()
    if new_draft != draft:
        cl.user_session.set(SessionKey.BLOG_DRAFT, new_draft)
        # Send a compact notice that draft updated
        await cl.Message(content="(초안이 업데이트되었습니다)", author="system").send()


@cl.set_starters
def starters():
    return [
        cl.Starter(label="문체 개선", message="문체를 더 자연스럽고 읽기 쉽게 개선해주세요."),
        cl.Starter(label="길이 조정", message="내용을 더 간결하게 요약해주세요."),
        cl.Starter(label="구조 개선", message="글의 구조와 흐름을 개선해주세요."),
        cl.Starter(label="제목 개선", message="제목을 더 매력적으로 개선해주세요."),
    ]

async def _cmd_save_draft():
    session_id: str = cl.user_session.get(SessionKey.SESSION_ID)
    draft: str = cl.user_session.get(SessionKey.BLOG_DRAFT, "")
    if not draft:
        await cl.Message(content="저장할 초안이 없습니다.", author="system").send()
        return
    meta = save_artifact(session_id, "blog-draft", draft, kind="draft", ext="md")
    await cl.Message(content=f"초안 저장됨: {meta.file_path.name}", author="system").send()

async def _cmd_list_artifacts():
    session_id: str = cl.user_session.get(SessionKey.SESSION_ID)
    arts = list_artifacts(session_id)
    if not arts:
        await cl.Message(content="저장된 아티팩트가 없습니다.", author="system").send()
        return
    lines = [f"- {a.created_at} • {a.kind} • {Path(a.path).name} ({a.size} bytes)" for a in arts[:10]]
    await cl.Message(content="\n".join(lines), author="system").send()

async def _cmd_usage():
    session_id: str = cl.user_session.get(SessionKey.SESSION_ID)
    summary = format_usage_summary(session_id)
    await cl.Message(content=summary, author="system").send()

async def _cmd_model(args: dict | None):
    provider_current = cl.user_session.get("selected_llm_provider") or _get_default_provider_and_model()[0]
    model_current = cl.user_session.get("selected_llm_model") or _get_default_provider_and_model()[1]
    provider = provider_current
    model = model_current
    if args:
        p = args.get("provider")
        m = args.get("model")
        if p:
            provider = p
        if m:
            model = m
    else:
        msg = await cl.AskUserMessage(
            content=(
                "모델 설정을 입력하세요.\n"
                f"현재: {provider_current}/{model_current}\n\n"
                "예) provider=ollama, model=llama3:8b\n"
                "지원: provider=ollama|openai"
            ),
            timeout=120,
        ).send()
        if not msg or not msg.get("content"):
            await cl.Message(content="입력이 취소되었습니다.", author="system").send()
            return
        text = msg["content"].strip()
        # simple parse: key=value pairs separated by commas or spaces
        for part in text.replace(",", " ").split():
            if "=" in part:
                k, v = part.split("=", 1)
                k = k.strip().lower()
                v = v.strip()
                if k == "provider":
                    provider = v
                elif k == "model":
                    model = v

    if provider not in ("openai", "ollama"):
        await cl.Message(content="provider 는 openai 또는 ollama 이어야 합니다.", author="system").send()
        return
    if not model:
        await cl.Message(content="model 을 지정해주세요.", author="system").send()
        return

    try:
        _rebuild_agent_preserve_history(provider, model)
        await cl.Message(content=f"모델이 변경되었습니다: {provider}/{model}", author="system").send()
    except Exception as e:
        await cl.Message(content=f"모델 변경 실패: {e}", author="system").send()


async def _cmd_publish():
    # Minimal flow: save the current draft as artifact and guide user to Streamlit for final publish
    session_id: str = cl.user_session.get(SessionKey.SESSION_ID)
    draft: str = cl.user_session.get(SessionKey.BLOG_DRAFT, "")
    if not draft:
        await cl.Message(content="발행할 초안이 없습니다.", author="system").send()
        return
    meta = save_artifact(session_id, "blog-post", draft, kind="post", ext="md")
    await cl.Message(
        content=(
            f"본문 아티팩트 저장됨: {meta.file_path.name}\n"
            "현재 발행은 Streamlit Publisher에서 진행하세요 (src/app.py)."
        ),
        author="system",
    ).send()


async def _handle_slash_command(text: str) -> bool:
    # Parse commands like "/cmd key=value key=value"
    parts = text.split()
    if not parts:
        return False
    cmd = parts[0].lstrip("/").lower()
    args: dict[str, str] = {}
    for token in parts[1:]:
        if "=" in token:
            k, v = token.split("=", 1)
            args[k.strip().lower()] = v.strip()

    if cmd == "usage":
        await _cmd_usage()
        return True
    if cmd == "save_draft":
        await _cmd_save_draft()
        return True
    if cmd == "list_artifacts":
        await _cmd_list_artifacts()
        return True
    if cmd == "model":
        await _cmd_model(args or None)
        return True
    if cmd == "publish":
        await _cmd_publish()
        return True
    # Unknown command
    await cl.Message(content=f"알 수 없는 명령어입니다: /{cmd}", author="system").send()
    return True
