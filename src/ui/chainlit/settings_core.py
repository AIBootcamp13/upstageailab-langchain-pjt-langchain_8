# src/ui/chainlit/settings_core.py
import chainlit as cl
from chainlit.input_widget import Select
from typing import List, Optional
from chainlit.types import ChatProfile

from src.config import CONFIG
from src.ui.chainlit.icons import PROVIDER_ICONS


# Consistent labels and icons for the settings panel
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


def get_provider_icon(provider_key: str) -> str:
    """Get appropriate SVG icon for provider."""
    return PROVIDER_ICONS.get(provider_key, PROVIDER_ICONS.get("openai", ""))


async def setup_settings(forced_provider=None):
    """Configure and send the settings panel for model and agent selection."""
    providers = list(CONFIG.get("llm_providers", {}).keys())

    # Get the current provider from session (set by chat profile selection)
    # Allow an override when called from rebuild flow so we can show a
    # loading indicator for a provider that's being activated.
    current_provider = forced_provider or cl.user_session.get("llm_provider", providers[0] if providers else "")
    current_model = cl.user_session.get("llm_model", "")
    current_agent = cl.user_session.get("agent_profile", "draft")

    # Get available models for current provider
    models_for_provider = CONFIG.get("llm_providers", {}).get(current_provider, [])

    # If current model is not valid for the provider, use the first available
    if current_model not in models_for_provider and models_for_provider:
        current_model = models_for_provider[0]
        cl.user_session.set("llm_model", current_model)

    # Create the model dropdown
    model_items = {}
    for m in models_for_provider:
        icon = next((icon for keyword, icon in MODEL_ICONS.items() if keyword in m.lower()), "⚫️")
        model_items[f"{icon} {m}"] = m
        
    # If a model rebuild is in progress, show a small spinner in the label to
    # indicate loading. This reduces confusion caused by a missing icon.
    loading = cl.user_session.get("loading_model", False)
    model_label = f"🔎 {PROVIDER_LABELS.get(current_provider, current_provider.title())} Model"
    if loading:
        model_label = f"{model_label} ⏳"

    model_select = Select(
        id="ModelName",
        label=model_label,
        items=model_items,
        initial_value=current_model,
    )
    
    # Create agent profile dropdown
    agent_items = {
        "📝 Draft Writer": "draft",
        "✏️ Content Editor": "update"
    }
    
    agent_select = Select(
        id="AgentProfile",
        label="🎭 Agent Profile",
        items=agent_items,
        initial_value=current_agent,
    )
    
    # Send both selects to the settings panel
    await cl.ChatSettings([model_select, agent_select]).send()
