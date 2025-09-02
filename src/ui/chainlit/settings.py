# src/ui/chainlit/settings.py

import chainlit as cl
from typing import List, Optional
from chainlit.types import ChatProfile

from src.config import CONFIG
from src.ui.chainlit.utils import rebuild_agent_with_new_model
from src.ui.chainlit.settings_core import (
    setup_settings,
    PROVIDER_LABELS,
    get_provider_icon,
)


# This function sets up the persona selection in the top-left dropdown
@cl.set_chat_profiles
async def chat_profiles(current_user: Optional[object] = None) -> List[ChatProfile]:
    """Register chat profiles for different LLM providers."""
    profiles = []
    providers = CONFIG.get("llm_providers", {})

    for i, (provider_key, models) in enumerate(providers.items()):
        provider_name = PROVIDER_LABELS.get(provider_key, provider_key.title())
        all_models = ", ".join(models) if models else "No models"
        icon = get_provider_icon(provider_key)

        # Include emoji in the visible name only - Chainlit handles emojis better
        # when they're in the name rather than the icon field (which expects URLs)
        profiles.append(
            ChatProfile(
                name=f"{icon} {provider_name}",
                markdown_description=f"**{provider_name}**\n{all_models}",
                icon="",  # Leave icon empty to avoid <img src="emoji"> issues
                default=(i == 0),  # Set first profile as default
            )
        )

    return profiles


# This function handles changes made in the settings panel
@cl.on_settings_update
async def on_settings_update(settings: dict):
    """Called when settings are changed in the Chainlit UI."""
    print(f"Settings updated: {settings}")
    # Read the new values using the widget IDs
    new_model = settings.get("ModelName")
    new_agent = settings.get("AgentProfile")

    # Compare against existing session values first, then update session
    old_model = cl.user_session.get("llm_model")
    old_agent = cl.user_session.get("agent_profile")

    model_changed = new_model and new_model != old_model
    agent_changed = new_agent and new_agent != old_agent

    # Persist new values
    if model_changed:
        cl.user_session.set("llm_model", new_model)
    if agent_changed:
        cl.user_session.set("agent_profile", new_agent)

    # If the model or agent has changed, rebuild the agent (only when docs exist)
    if (model_changed or agent_changed):
        if cl.user_session.get("processed_documents"):
            await rebuild_agent_with_new_model(
                cl.user_session.get("llm_provider"),
                new_model if model_changed else cl.user_session.get("llm_model"),
                cl.user_session.get("agent_profile", "draft"),
            )
        else:
            changes = []
            if model_changed:
                changes.append(f"model: `{new_model}`")
            if agent_changed:
                agent_name = "Draft Writer" if new_agent == "draft" else "Content Editor"
                changes.append(f"agent: `{agent_name}`")
            await cl.Message(content=f"Settings updated: {', '.join(changes)}.").send()