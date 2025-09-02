# src/ui/chainlit/callbacks.py

import chainlit as cl
import chainlit.input_widget as iw
import uuid
from src.ui.components.publisher import Publisher
from github import Github, GithubException
from datetime import datetime
from datetime import timedelta
import html
from src.ui.enums import SessionKey
from src.artifacts import save_artifact, list_artifacts
import json
import _uuid
from enum import Enum


async def _publish_with_inputs(session_id: str, post_title: str, category: str, selected_tags: list[str], github_pat: str, github_repo: str, draft: str):
    """Core publish logic extracted so multiple UI flows can call it."""
    publisher_instance = Publisher()

    # Mask helper
    def _mask_token(tok: str) -> str:
        if not tok:
            return ""
        if len(tok) <= 8:
            return "****"
        return f"{tok[:4]}...{tok[-4:]}"

    masked_pat = _mask_token(github_pat)
    await cl.Message(content=f"Publishing post '{post_title}' to {github_repo} (using PAT {masked_pat})...").send()

    # Build the post content using Publisher helpers
    slug = publisher_instance._make_slug_from_title(post_title)
    file_name = publisher_instance._make_jekyll_post_file_name(slug)
    file_path = f"{publisher_instance.POSTS_FOLDER}/{file_name}"
    front = publisher_instance._make_front_matter(post_title, [category], selected_tags)
    # Combine front matter and draft
    content = front + "\n\n" + (draft or "")

    if not (github_pat and github_repo):
        await cl.Message(content="❌ Missing GitHub credentials in session. Please configure via Publish Settings.").send()
        return

    # Attempt to create the file in the repo
    try:
        gh = Github(github_pat)
        repo = gh.get_repo(github_repo)
        # If file exists, repo.create_file will raise; we'll try once, and on conflict, append timestamp
        try:
            repo.create_file(path=file_path, message=f"feat: Publish blog post: {post_title}", content=content)
        except GithubException as e:
            # Detect file already exists and retry with timestamped filename
            err_text = str(e)
            if "already exists" in err_text or getattr(e, 'status', None) == 409:
                timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
                alt_file_name = file_name.replace(".md", f"-{timestamp}.md")
                alt_file_path = f"{publisher_instance.POSTS_FOLDER}/{alt_file_name}"
                repo.create_file(path=alt_file_path, message=f"feat: Publish blog post (alt): {post_title}", content=content)
                file_path = alt_file_path
            else:
                raise

        # Success
        username = github_repo.split("/")[0]
        slug = publisher_instance._make_slug_from_title(post_title)
        public_posts_path = publisher_instance.POSTS_FOLDER.lstrip("_").rstrip("/")
        blog_url = f"https://{username}.github.io/{public_posts_path}/{slug}/"
        await cl.Message(content=f"✅ Published '{post_title}'.\nURL: {blog_url}").send()
    except Exception as e:
        await cl.Message(content=f"❌ Failed to publish: {e!s}").send()
        return



class PublishState(Enum):
    IDLE = "IDLE"
    AWAITING_TITLE = "AWAITING_TITLE"
    AWAITING_CATEGORY = "AWAITING_CATEGORY"
    PUBLISHING = "PUBLISHING"


async def manage_publish_flow():
    """Central controller for the publish multi-step flow. Reads state from session and renders the appropriate UI."""
    state = cl.user_session.get("publish_state", PublishState.IDLE.value)
    # Ensure we have the enum value
    if isinstance(state, str):
        try:
            state = PublishState(state)
        except Exception:
            state = PublishState.IDLE

    draft = cl.user_session.get(SessionKey.BLOG_DRAFT, "")
    if not draft:
        await cl.Message(content="❌ No draft available to publish. Generate a draft first.").send()
        cl.user_session.set("publish_state", PublishState.IDLE.value)
        return

    if state == PublishState.AWAITING_TITLE:
        agent = cl.user_session.get(SessionKey.BLOG_CREATOR_AGENT)
        suggestions = []
        if agent:
            try:
                suggestions = await _suggest_titles(agent, draft)
            except Exception:
                suggestions = []

        actions = [cl.Action(name="custom_title", payload={}, label="✍️ Enter Custom Title")]
        for s in (suggestions or [])[:4]:
            actions.insert(0, cl.Action(name="select_title", payload={"title": s}, label=s))

        await cl.Message(content="**Step 1 of 2: Choose a Title**", actions=actions).send()
        return

    if state == PublishState.AWAITING_CATEGORY:
        title = cl.user_session.get("publish_title")
        if not title:
            await cl.Message(content="No title found in session. Returning to title selection.").send()
            cl.user_session.set("publish_state", PublishState.AWAITING_TITLE.value)
            await manage_publish_flow()
            return

        publisher_instance = Publisher()
        widgets = [
            iw.Select(id="category", label="Category", items=publisher_instance.categories),
            iw.Tags(id="tags", label="Tags", initial_value=[]),
        ]

        res = await cl.AskUserMessage(
            content=f"**Step 2 of 2: Categorize**\nSelected title: *{title}*",
            widgets=widgets,
            timeout=300,
        ).send()

        if not res:
            await cl.Message(content="Publishing cancelled. Returning to idle state.").send()
            cl.user_session.set("publish_state", PublishState.IDLE.value)
            return

        # Save inputs and transition to publishing
        cl.user_session.set("publish_category", res.get("category"))
        cl.user_session.set("publish_tags", res.get("tags") or [])
        cl.user_session.set("publish_state", PublishState.PUBLISHING.value)
        await manage_publish_flow()
        return

    if state == PublishState.PUBLISHING:
        # Gather everything and call publish
        title = cl.user_session.get("publish_title")
        category = cl.user_session.get("publish_category")
        selected_tags = cl.user_session.get("publish_tags") or []
        session_id = cl.user_session.get(SessionKey.SESSION_ID)
        if not session_id:
            session_id = str(uuid.uuid4())
            try:
                cl.user_session.set(SessionKey.SESSION_ID, session_id)
            except Exception:
                pass

        github_pat = cl.user_session.get(SessionKey.GITHUB_PAT)
        github_repo = cl.user_session.get(SessionKey.GITHUB_REPO)
        draft = cl.user_session.get(SessionKey.BLOG_DRAFT, "")

        # Reset state to idle before publishing to avoid duplicate flows
        cl.user_session.set("publish_state", PublishState.IDLE.value)

        await _publish_with_inputs(session_id, title, category, selected_tags, github_pat, github_repo, draft)
        return


@cl.action_callback("toggle_markdown_format")
async def on_toggle_markdown_format(action: cl.Action):
    """Toggle the format of a previously sent markdown display message."""
    # For stability across different Chainlit versions we enforce markdown-only views.
    await cl.Message(content="ℹ️ Markdown-only view is enforced — plain-text toggle disabled.").send()


@cl.action_callback("copy_instructions")
async def on_copy_instructions(action: cl.Action):
    """Provide detailed instructions for copying the markdown content."""
    await cl.Message(
        content="📋 **​How to Copy the Markdown Content:​**\n\n" +
                "**​Desktop/Laptop:​**\n" +
                "1. Click inside the gray text block above\n" +
                "2. Press `Ctrl+A` (Windows/Linux) or `Cmd+A` (Mac) to select all\n" +
                "3. Press `Ctrl+C` (Windows/Linux) or `Cmd+C` (Mac) to copy\n\n" +
                "**​Mobile:​**\n" +
                "1. Long press on the text block above\n" +
                "2. Tap 'Select All' from the menu\n" +
                "3. Tap 'Copy' from the menu\n\n" +
                "**​Alternative:​**\n" +
                "• You can also manually select text by clicking and dragging\n" +
                "• The content is now in your clipboard and ready to paste!"
    ).send()


@cl.action_callback("copy_to_clipboard")
async def on_copy_to_clipboard(action: cl.Action):
    """Legacy callback - redirect to copy instructions."""
    await on_copy_instructions(action)


@cl.action_callback("hide_markdown")
async def on_hide_markdown(action: cl.Action):
    """Legacy callback - no longer needed since we can't actually hide messages."""
    await cl.Message(content=" The markdown content will remain visible above for easy copying. You can continue with other actions.").send()


@cl.action_callback("save_draft")
async def on_save_draft(action: cl.Action):
    """'Save Draft' action callback."""
    session_id = cl.user_session.get(SessionKey.SESSION_ID)
    draft = cl.user_session.get(SessionKey.BLOG_DRAFT, "")
    if not draft:
        await cl.Message(content="There is no draft to save.").send()
        return
    artifact = save_artifact(session_id, "blog-draft", draft, kind="draft", ext="md")
    await cl.Message(content=f"✅ Draft saved as an artifact:\n`{artifact.file_path}`").send()


@cl.action_callback("list_artifacts")
async def on_list_artifacts(action: cl.Action):
    """'List Artifacts' action callback."""
    session_id = cl.user_session.get(SessionKey.SESSION_ID)
    artifacts = list_artifacts(session_id)
    if not artifacts:
        await cl.Message(content="No artifacts have been saved yet.").send()
        return
    elements = [
        cl.Text(
            name=a.file_path.name,
            content=f"Type: {a.kind}, Size: {a.size} bytes\nCreated: {a.created_at}",
        )
        for a in artifacts
    ]
    await cl.Message(content="**​List of Generated Artifacts:​**", elements=elements).send()


@cl.action_callback("submit_inline_editor")
async def on_submit_inline_editor(action: cl.Action):
    """Handle submit from the inline TextInput editor."""
    payload = getattr(action, "payload", {}) or {}

    # Directly extract the editor content (most reliable path)
    new_draft = payload.get("editor")

    if isinstance(new_draft, str) and new_draft.strip():
        cl.user_session.set(SessionKey.BLOG_DRAFT, new_draft.strip())
        # Update preview on submit as well
        preview_msg_id = cl.user_session.get("preview_message_id")
        if preview_msg_id:
            await cl.Message(id=preview_msg_id).update(
                content="📄 Live Preview",
                elements=[cl.Text(content=new_draft.strip(), language="markdown", name="markdown_preview")]
            )
        await cl.Message(
            content="✅ Draft updated successfully from the inline editor.",
            actions=[
                cl.Action(name="save_draft", payload={"value": "save"}, label="💾 Save Updated Draft")
            ],
        ).send()
    else:
        # Fallback for unexpected cases
        await cl.Message(content="No content received. Please try editing again.").send()


@cl.action_callback("publish_post")
async def on_publish_post(action: cl.Action):
    """'Publish Post' action: Kicks off the multi-step publishing workflow."""
    draft = cl.user_session.get(SessionKey.BLOG_DRAFT, "")
    if not draft:
        await cl.Message(content="❌ No draft available to publish. Generate a draft first.").send()
        return

    # Check for and validate stored credentials
    stored_pat = cl.user_session.get(SessionKey.GITHUB_PAT)
    stored_repo = cl.user_session.get(SessionKey.GITHUB_REPO)
    stored_pat_at = cl.user_session.get(SessionKey.GITHUB_PAT_STORED_AT)

    if stored_pat_at:
        try:
            stored_dt = datetime.fromisoformat(stored_pat_at.replace('Z', '+00:00'))
            if datetime.utcnow() - stored_dt > timedelta(hours=24):
                cl.user_session.set(SessionKey.GITHUB_PAT, None)
                cl.user_session.set(SessionKey.GITHUB_REPO, None)
                cl.user_session.set(SessionKey.GITHUB_PAT_STORED_AT, None)
                stored_pat = None
                stored_repo = None
                await cl.Message(content="Stored GitHub PAT expired and was cleared.").send()
        except Exception:
            pass # Ignore parsing errors

    # If credentials are missing, inform user that in-app publishing is disabled.
    if not (stored_pat and stored_repo):
        await cl.Message(
            content=(
                "⚠️ Publishing via the in-app UI is temporarily disabled. "
                "Please configure credentials outside the app or publish via the repository/CLI."
            )
        ).send()
        return

    # Set state to awaiting title and delegate rendering to the controller
    cl.user_session.set("publish_state", PublishState.AWAITING_TITLE.value)
    await manage_publish_flow()
    return

    # Save creds into chainlit session for convenience (best-effort)
    try:
        cl.user_session.set(SessionKey.GITHUB_PAT, github_pat)
        cl.user_session.set(SessionKey.GITHUB_REPO, github_repo)
        cl.user_session.set(SessionKey.GITHUB_PAT_STORED_AT, datetime.utcnow().isoformat() + "Z")
    except Exception:
        # best-effort: ignore if session not writable
        pass

    # Ensure session id exists
    session_id = cl.user_session.get(SessionKey.SESSION_ID)
    if not session_id:
        session_id = str(uuid.uuid4())
        try:
            cl.user_session.set(SessionKey.SESSION_ID, session_id)
        except Exception:
            pass

    # Call the shared publish routine
    await _publish_with_inputs(session_id, post_title, category, selected_tags, github_pat, github_repo, draft)
    return


@cl.action_callback("view_markdown")
async def on_view_markdown(action: cl.Action):
    """Show the current draft as a markdown page with helper actions."""
    draft = cl.user_session.get(SessionKey.BLOG_DRAFT, "")
    if not draft:
        await cl.Message(content="No draft available to view. Generate a draft first.").send()
        return

    # Send the draft as a markdown-display Text element
    msg = cl.Message(content="📋 Blog Draft (Markdown)", elements=[cl.Text(content=draft, language="markdown", name="draft.md")])
    await msg.send()

    # Provide helper actions that operate on the displayed message
    await cl.Message(
        content="Actions for the markdown view:",
        parent_id=msg.id,
        actions=[
            cl.Action(name="copy_instructions", payload={}, label="📋 How to Copy"),
            cl.Action(name="save_draft", payload={"value": "save"}, label="💾 Save Draft"),
            cl.Action(name="publish_post", payload={"value": "publish"}, label="🚀 Publish Post"),
        ],
    ).send()


@cl.action_callback("regenerate_draft")
async def on_regenerate_draft(action: cl.Action):
    """Regenerate the draft by invoking the agent's generate_draft and stream the result."""
    session_id = cl.user_session.get(SessionKey.SESSION_ID)
    agent = cl.user_session.get(SessionKey.BLOG_CREATOR_AGENT)
    if not agent:
        await cl.Message(content="No agent available to regenerate the draft. Start a session first.").send()
        return

    # Generate draft (may be async or sync)
    try:
        draft = await cl.make_async(agent.generate_draft)(session_id=session_id)
    except Exception as e:
        await cl.Message(content=f"Failed to regenerate draft: {e!s}").send()
        return

    cl.user_session.set(SessionKey.BLOG_DRAFT, draft)

    draft_msg = cl.Message(content="", author="📝 Draft")
    await draft_msg.send()
    # Stream the regenerated draft
    chunk_size = 10
    for i in range(0, len(draft), chunk_size):
        part = draft[i : i + chunk_size]
        await draft_msg.stream_token(part)
    await draft_msg.update()

    # Send follow-up with actions
    await cl.Message(
        content="Draft regenerated. How would you like to proceed?",
        parent_id=draft_msg.id,
        actions=[
            cl.Action(name="save_draft", payload={"value": "save"}, label="💾 Save Draft"),
            cl.Action(name="view_markdown", payload={"value": "view"}, label="📋 View Markdown"),
            cl.Action(name="toggle_tokens", payload={"value": "toggle"}, label="📊 Show Tokens"),
            cl.Action(name="list_artifacts", payload={"value": "list"}, label="📄 List Artifacts"),
            cl.Action(name="publish_post", payload={"value": "publish"}, label="🚀 Publish Post"),
        ],
    ).send()



@cl.action_callback("export_telemetry")
async def on_export_telemetry(action: cl.Action):
    """Export recorded message telemetry (SessionKey.MESSAGE_LIST) as a JSON artifact."""
    telemetry = cl.user_session.get(SessionKey.MESSAGE_LIST, []) or []
    if not telemetry:
        await cl.Message(content="ℹ️ No telemetry entries to export.").send()
        return

    # Serialize telemetry to JSON
    try:
        payload = json.dumps(telemetry, ensure_ascii=False, indent=2)
    except Exception:
        payload = json.dumps(telemetry, ensure_ascii=True, indent=2)

    # Ensure session id
    session_id = cl.user_session.get(SessionKey.SESSION_ID)
    if not session_id:
        session_id = str(_uuid.uuid4())
        cl.user_session.set(SessionKey.SESSION_ID, session_id)

    artifact = save_artifact(session_id, "message-telemetry", payload, kind="telemetry", ext="json")
    await cl.Message(content=f"✅ Telemetry exported as artifact:\n`{artifact.file_path}`").send()


async def _suggest_titles(agent, draft: str) -> list[str]:
    """Ask the agent's LLM to propose a list of short titles based on the draft."""
    prompt = (
        "Read the following blog draft and suggest 5 concise, SEO-friendly titles (one per line).\n\n"
        f"Draft:\n{draft[:4000]}\n\n"  # limit input
        "Return only the titles, each on its own line."
    )

    try:
        # Try to call the agent's LLM synchronously; wrap in asyncio if necessary
        if hasattr(agent.llm, "ainvoke"):
            resp = await agent.llm.ainvoke(prompt)
            content = getattr(resp, "content", str(resp))
        else:
            resp = agent.llm.invoke(prompt)
            content = getattr(resp, "content", str(resp))
    except Exception:
        # Last-resort: return empty list
        return []

    # Split lines and clean
    lines = [l.strip('-• 	') for l in content.splitlines() if l.strip()]
    # Heuristic: pick lines that look like titles (short)
    titles = [l for l in lines if 5 <= len(l) <= 120]
    return titles[:5]


@cl.action_callback("open_publish_settings")
async def on_open_publish_settings(action: cl.Action):
    """Open a dedicated credentials/config dialog for publishing."""
    # Debug: confirm callback invocation
    try:
        await cl.Message(content="🔧 Opening Publish Settings...").send()
    except Exception:
        pass
    publisher_instance = Publisher()
    widgets = [
        iw.TextInput(id="github_username", label="GitHub Username", placeholder="your-username"),
        iw.TextInput(id="github_pat", label="GitHub PAT", placeholder="Personal Access Token", secret=True),
        iw.TextInput(id="github_repo", label="Repository (owner/repo)", placeholder="owner/repo"),
    ]
    try:
        res = await cl.AskUserMessage(content="Configure GitHub credentials for publishing.", widgets=widgets, timeout=300).send()
    except Exception as e:
        await cl.Message(content=f"⚠️ Failed to open Publish Settings dialog: {e!s}").send()
        return
    if not res:
        await cl.Message(content="Publish settings cancelled.").send()
        return

    github_username = res.get("github_username")
    github_pat = res.get("github_pat")
    github_repo = res.get("github_repo")

    if not (github_username and github_pat and github_repo):
        await cl.Message(content="Please provide username, PAT and repository to enable publishing.").send()
        return

    # Validate token by attempting to fetch the authenticated user
    try:
        gh = Github(github_pat)
        user = gh.get_user()
        actual_login = user.login
    except Exception as e:
        await cl.Message(content=f"Failed to validate GitHub credentials: {e!s}").send()
        return

    # Save credentials in session (best-effort)
    try:
        cl.user_session.set(SessionKey.GITHUB_PAT, github_pat)
        cl.user_session.set(SessionKey.GITHUB_REPO, github_repo)
        cl.user_session.set(SessionKey.GITHUB_USERNAME, actual_login)
        cl.user_session.set(SessionKey.GITHUB_PAT_STORED_AT, datetime.utcnow().isoformat() + "Z")
    except Exception:
        pass

    await cl.Message(content=f"✅ GitHub login succeeded as {actual_login}. You can now press Publish.").send()


async def _ask_for_category_and_tags(title: str):
    """Ask the user for category and tags, then call the publisher routine."""
    # Ensure we have necessary session and credentials
    draft = cl.user_session.get(SessionKey.BLOG_DRAFT, "")
    if not draft:
        await cl.Message(content="❌ No draft available to publish. Generate a draft first.").send()
        return

    publisher_instance = Publisher()
    widgets = [
        iw.Select(id="category", label="Category", items=publisher_instance.categories),
        iw.Tags(id="tags", label="Tags", initial_value=[]),
    ]

    res = await cl.AskUserMessage(
        content=f"**Step 2 of 2: Categorize**\nSelected title: *{title}*",
        widgets=widgets,
        timeout=300,
    ).send()

    if not res:
        await cl.Message(content="Publishing cancelled. No category/tag input received.").send()
        return

    category = res.get("category")
    selected_tags = res.get("tags") or []
    # Normalize tags to list if string
    if isinstance(selected_tags, str):
        selected_tags = [t.strip() for t in selected_tags.split(",") if t.strip()]

    # Ensure session id exists
    session_id = cl.user_session.get(SessionKey.SESSION_ID)
    if not session_id:
        session_id = str(uuid.uuid4())
        try:
            cl.user_session.set(SessionKey.SESSION_ID, session_id)
        except Exception:
            pass

    # Retrieve stored creds
    github_pat = cl.user_session.get(SessionKey.GITHUB_PAT)
    github_repo = cl.user_session.get(SessionKey.GITHUB_REPO)

    # Call the shared publish routine
    await _publish_with_inputs(session_id, title, category, selected_tags, github_pat, github_repo, draft)


@cl.action_callback("select_title")
async def on_select_title(action: cl.Action):
    """Handle selecting a suggested title: save it to session and advance state."""
    payload = getattr(action, "payload", {}) or {}
    title = payload.get("title")
    if not title:
        await cl.Message(content="No title selected. Please try again.").send()
        return
    cl.user_session.set("publish_title", title)
    cl.user_session.set("publish_state", PublishState.AWAITING_CATEGORY.value)
    await manage_publish_flow()


@cl.action_callback("custom_title")
async def on_custom_title(action: cl.Action):
    """Prompt for a custom title, save it, and advance the state machine."""
    res = await cl.AskUserMessage(
        content="Enter a custom title:",
        widgets=[iw.TextInput(id="title", label="Title")],
        timeout=300,
    ).send()

    if not res or not res.get("title"):
        await cl.Message(content="Title input cancelled or empty. Please try again.").send()
        return

    title = res.get("title").strip()
    if not title:
        await cl.Message(content="Empty title provided. Please try again.").send()
        return

    cl.user_session.set("publish_title", title)
    cl.user_session.set("publish_state", PublishState.AWAITING_CATEGORY.value)
    await manage_publish_flow()
