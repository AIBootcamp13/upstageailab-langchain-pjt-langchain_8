# src/ui/chainlit/callbacks.py

import chainlit as cl

from src.artifacts import list_artifacts, save_artifact
from src.ui.enums import SessionKey


@cl.action_callback("save_draft")
async def on_save_draft(action: cl.Action):
    """'초안 저장' 액션이 클릭되었을 때 호출됩니다."""
    session_id = cl.user_session.get(SessionKey.SESSION_ID)
    draft = cl.user_session.get(SessionKey.BLOG_DRAFT, "")
    if not draft:
        await cl.Message(content="저장할 초안이 없습니다.").send()
        return
    artifact = save_artifact(session_id, "blog-draft", draft, kind="draft", ext="md")
    await cl.Message(content=f"✅ 초안이 아티팩트로 저장되었습니다:\n`{artifact.file_path}`").send()


@cl.action_callback("list_artifacts")
async def on_list_artifacts(action: cl.Action):
    """'아티팩트 목록 보기' 액션이 클릭되었을 때 호출됩니다."""
    session_id = cl.user_session.get(SessionKey.SESSION_ID)
    artifacts = list_artifacts(session_id)
    if not artifacts:
        await cl.Message(content="저장된 아티팩트가 없습니다.").send()
        return
    elements = [
        cl.Text(
            name=a.file_path.name,
            content=f"종류: {a.kind}, 크기: {a.size} bytes",
            display="inline",
        )
        for a in artifacts
    ]
    await cl.Message(content="**생성된 아티팩트 목록:**", elements=elements).send()