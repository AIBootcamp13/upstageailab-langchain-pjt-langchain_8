# src/ui/chainlit/settings.py

import chainlit as cl
from chainlit.input_widget import Select, TextInput
from typing import Optional, List
from chainlit.types import ChatProfile

from src.config import CONFIG, DEFAULT_PROFILE
from src.ui.chainlit.utils import rebuild_agent_with_new_model
from src.ui.enums import SessionKey
from urllib.parse import quote

# Consistent labels and icons
PROVIDER_LABELS = {
    "openai": "OpenAI",
    "ollama": "Ollama",
    "upstage": "Upstage"
}

MODEL_ICONS = {
    "gpt": "🤖",
    "llama": "🐏",
    "gemma": "🧠",
    "solar": "☀️"
}

PROFILE_EMOJI = {
    "default_cpu": "🟢",
    "high_gpu": "🔥",
}

# Badge styles for reliable inline SVG icons (no emoji rendering needed)
PROFILE_BADGE = {
    "default_cpu": {"bg": "#0FA958", "label": "CPU"},
    "high_gpu": {"bg": "#FF5722", "label": "GPU"},
}


def _emoji_svg_data_url(emoji: str, size: int = 48, bg: str = "transparent") -> str:
    """Return a data URL containing a tiny SVG with the given emoji centered.

    Chainlit expects `ChatProfile.icon` to be an image URL; using a data URL
    ensures the UI receives an image instead of an empty string which caused
    the blank icon placeholders.
    """
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 {size} {size}">'
        f'<rect width="100%" height="100%" fill="{bg}" />'
        f'<text x="50%" y="50%" dominant-baseline="central" text-anchor="middle" '
        f'font-size="{int(size * 0.8)}">{emoji}</text>'
        '</svg>'
    )
    return "data:image/svg+xml;utf8," + quote(svg)

def _badge_svg_data_url(profile_key: str, size: int = 48) -> str:
    """Return a data URL of a simple badge icon with a colored background and label.

    This avoids relying on emoji fonts inside SVG, which can render blank in some UIs.
    """
    spec = PROFILE_BADGE.get(profile_key, {"bg": "#444", "label": profile_key[:3].upper()})
    bg = spec["bg"]
    label = spec["label"]
    radius = int(size / 6)
    font_size = int(size * 0.42)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">' \
        f'<rect x="0" y="0" width="{size}" height="{size}" rx="{radius}" ry="{radius}" fill="{bg}" />' \
        f'<text x="50%" y="52%" dominant-baseline="middle" text-anchor="middle" fill="#ffffff" ' \
        f'font-family="Inter, Roboto, Arial, sans-serif" font-size="{font_size}" font-weight="700">{label}</text>' \
        '</svg>'
    )
    return "data:image/svg+xml;utf8," + quote(svg)

@cl.set_chat_profiles
async def chat_profiles(current_user: Optional[object] = None) -> List[ChatProfile]:
    """Register chat profiles so they appear in the main UI profiles menu."""
    profiles: List[ChatProfile] = []
    for key, val in CONFIG.get("profiles", {}).items():
        display_label = val.get("description", key.replace("_", " ").title())
        emoji = PROFILE_EMOJI.get(key, "⚫️")
        
        profile_kwargs = {
            "name": f"{emoji} {display_label}".strip(),
            "markdown_description": f"**Provider:** `{val.get('llm_provider')}`\n\n**Model:** `{val.get('llm_model')}`",
            "default": (key == DEFAULT_PROFILE),
        }

        icon_val = val.get("icon")
        # If a valid URL or data URI is provided in config, use it.
        if icon_val and isinstance(icon_val, str) and (
            icon_val.startswith("http") or icon_val.startswith("data:") or icon_val.startswith("/")
        ):
            profile_kwargs["icon"] = icon_val
        else:
            # Use a robust SVG badge icon to avoid blank rendering issues
            profile_kwargs["icon"] = _badge_svg_data_url(key)

        profiles.append(ChatProfile(**profile_kwargs))
    return profiles

@cl.on_settings_update
async def on_settings_update(settings: dict):
    """Called when settings are changed in the Chainlit UI."""
    # Save edits coming from the DraftEditor
    if "DraftEditor" in settings:
        new_draft = settings.get("DraftEditor")
        if isinstance(new_draft, str):
            cl.user_session.set(SessionKey.BLOG_DRAFT, new_draft)
            await cl.Message(content="✅ Draft updated from settings.").send()
    # Persist mode if present
    if "OperationMode" in settings:
        cl.user_session.set("OperationMode", settings.get("OperationMode"))

    new_provider = settings.get("ModelProvider")
    prev_provider = cl.user_session.get("llm_provider")

    # This block handles the case where the user changes the provider,
    # which should trigger a refresh of the model dropdown.
    if new_provider and new_provider != prev_provider:
        cl.user_session.set("llm_provider", new_provider)
        # Re-send the entire settings panel with an updated model list
        await setup_settings() 
        return

    # This block handles the final selection and rebuilds the agent
    new_model = settings.get("ModelName")
    if not new_provider or not new_model:
        return

    cl.user_session.set("llm_provider", new_provider)
    cl.user_session.set("llm_model", new_model)
    
    # Rebuild agent only if documents have already been processed
    if cl.user_session.get("processed_documents"):
        await rebuild_agent_with_new_model(new_provider, new_model)
    else:
        # Otherwise, just save the selection and wait for a file upload
        await cl.Message(content=f"Model selection saved: `{new_model}`. Please upload a document to begin.").send()

async def setup_settings():
    """Configure and send the settings panel for model selection."""
    # 1. Provider Selection Dropdown
    providers = list(CONFIG.get("llm_providers", {}).keys())
    if not providers:
        # Fallback to prevent UI crash
        providers = ["openai", "ollama"]

    provider_items = {PROVIDER_LABELS.get(p, p.title()): p for p in providers}
    default_profile_config = CONFIG.get("profiles", {}).get(DEFAULT_PROFILE, {})
    default_provider = default_profile_config.get("llm_provider", providers[0])

    provider_select = Select(
        id="ModelProvider",
        label="🤖 LLM Provider",
        items=provider_items,  # dict[label -> value]
        initial_value=default_provider,
    )

    # 2. Model Selection Dropdown
    models_for_provider = CONFIG.get("llm_providers", {}).get(default_provider, [])
    if not models_for_provider:
        # Fallback to prevent UI crash
        models_for_provider = ["gpt-4o"] if default_provider == "openai" else ["llama3"]
    
    model_items = {}
    for m in models_for_provider:
        icon = next((ic for k, ic in MODEL_ICONS.items() if k in m.lower()), "⚫️")
        model_items[f"{icon} {m}"] = m

    default_model = default_profile_config.get("llm_model", models_for_provider[0] if models_for_provider else None)
    
    model_select = Select(
        id="ModelName",
        label="🔎 LLM Model",
        items=model_items,  # dict[label -> value]
        initial_value=default_model,
    )

    # 3. Mode Selection
    mode_select = Select(
        id="OperationMode",
        label="⚙️ Operation Mode",
        items={"Drafting": "draft", "Editing": "edit"},
        initial_value="draft",
    )

    # 4. Include a DraftEditor textarea in settings (most compatible inline path)
    current_draft = cl.user_session.get(SessionKey.BLOG_DRAFT) or ""
    draft_editor = TextInput(
        id="DraftEditor",
        label="📝 Draft Editor",
        initial=current_draft,
        placeholder="Edit your draft here…",
        multiline=True,
    )
    items = [provider_select, model_select, mode_select, draft_editor]

    # Send the settings panel to the UI
    try:
        await cl.ChatSettings(items).send()
    except Exception as e:
        print(f"Error setting up chat settings: {e}")
        await cl.Message(content="Could not display the settings panel. Please check the configuration.").send()