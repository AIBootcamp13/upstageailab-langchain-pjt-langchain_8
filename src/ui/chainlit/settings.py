# src/ui/chainlit/settings.py

import chainlit as cl

from src.config import CONFIG, DEFAULT_PROFILE
from src.ui.chainlit.utils import rebuild_agent_with_new_model
from typing import Optional, List
from chainlit.types import ChatProfile


# Friendly labels and icons
PROVIDER_LABELS = {
    "openai": "OpenAI",
    "ollama": "Ollama",
}

MODEL_ICONS = {
    "gpt": "🤖",
    "llama": "🐏",
    "gemma": "🧠",
}

# Emoji to prefix profile display names (safe, not passed as image URLs)
PROFILE_EMOJI = {
    "default_cpu": "🟢",
    "high_gpu": "🔥",
}


@cl.set_chat_profiles
async def chat_profiles(current_user: Optional[object] = None) -> List[ChatProfile]:
    """Register chat profiles so they appear in the Chainlit UI profiles menu."""
    profiles: List[ChatProfile] = []
    for key, val in CONFIG.get("profiles", {}).items():
        # Only provide an `icon` value if it's a URL or a local path. Chainlit
        # treats the `icon` as an image source; plain emoji/text here can be
        # interpreted as a broken image URL in the UI. If no valid image is
        # configured, omit the `icon` field so Chainlit uses a safe default.
        # Human-friendly display name (prefix with emoji). Keep the original
        # config key in logic (default determination) but present a nicer label
        # to the user in the UI.
        display_label = PROFILE_LABELS.get(key, key.replace("_", " ").title())
        emoji = PROFILE_EMOJI.get(key, "")
        profile_kwargs = {
            "name": f"{emoji} {display_label}".strip(),
            "markdown_description": val.get("description", ""),
            "default": (key == DEFAULT_PROFILE),
        }

        icon_val = val.get("icon")
        if icon_val:
            # Treat as valid image source if it looks like a URL, data URI, or
            # absolute/relative file path.
            if isinstance(icon_val, str) and (
                icon_val.startswith("http://")
                or icon_val.startswith("https://")
                or icon_val.startswith("data:")
                or icon_val.startswith("/")
                or icon_val.startswith(".")
            ):
                profile_kwargs["icon"] = icon_val

        profiles.append(ChatProfile(**profile_kwargs))
    return profiles


# NOTE: We must not call ChatSettings at app startup because Chainlit context
# is not available. `setup_settings()` will be called per-thread in `on_chat_start`.


# 사용자 친화적인 레이블을 정의합니다.
PROFILE_LABELS = {
    "default_cpu": "Default (CPU)",
    "high_gpu": "High Performance (GPU)",
}

@cl.on_settings_update
async def on_settings_update(settings: dict):
    """Chainlit UI에서 설정이 변경될 때 호출됩니다."""
    # New settings: ModelProvider and ModelName
    new_provider = settings.get("ModelProvider")
    new_model = settings.get("ModelName")

    # If the provider changed (live provider pick) but no explicit model was selected,
    # send an updated ChatSettings with the models for that provider so the client
    # updates the ModelName select in-place.
    prev_provider = cl.user_session.get("llm_provider")
    if new_provider and new_provider != prev_provider and not new_model:
        models_for_provider = CONFIG.get("llm_providers", {}).get(new_provider, [])
        if not models_for_provider:
            await cl.Message(content=f"⚠️ `{new_provider}`에 이용 가능한 모델이 없습니다.").send()
            return

        # Build provider select (keep current selection)
        providers = list(CONFIG.get("llm_providers", {}).keys())
        provider_items = {PROVIDER_LABELS.get(p, p.title()): p for p in providers}
        provider_select = Select(
            id="ModelProvider",
            label="🤖 LLM 제공자 (Provider)",
            items=provider_items,
            initial_value=new_provider,
        )

        # Build the new model select for the chosen provider
        model_items = {}
        for m in models_for_provider:
            icon = next((ic for k, ic in MODEL_ICONS.items() if k in m), "🤖")
            model_items[f"{icon} {m}"] = m

        model_select = Select(
            id="ModelName",
            label="🔎 모델 선택 (Model)",
            items=model_items,
            initial_value=models_for_provider[0] if models_for_provider else None,
        )

        # Preserve the operation mode if present
        mode = settings.get("OperationMode", "draft")
        mode_select = Select(
            id="OperationMode",
            label="⚙️ 동작 모드 (Mode)",
            items={"Drafting": "draft", "Editing": "edit"},
            initial_value=mode,
        )

        try:
            await cl.ChatSettings([provider_select, model_select, mode_select]).send()
        except Exception:
            await cl.Message(content="설정 UI를 업데이트할 수 없습니다.").send()
        return

    # if provider changed but model not specified, pick the provider's first model
    if new_provider and not new_model:
        models_for_provider = CONFIG.get("llm_providers", {}).get(new_provider, [])
        if not models_for_provider:
            await cl.Message(content=f"⚠️ `{new_provider}`에 이용 가능한 모델이 없습니다.").send()
            return
        new_model = models_for_provider[0]

    if not new_provider and not new_model:
        return

    # Update session and rebuild agent
    cl.user_session.set("llm_provider", new_provider)
    cl.user_session.set("llm_model", new_model)
    await rebuild_agent_with_new_model(new_provider, new_model)


async def setup_settings():
    """채팅 시작 시 모델 프로필 선택을 위한 설정 패널을 구성하고 전송합니다."""
    # Provider select
    providers = list(CONFIG.get("llm_providers", {}).keys())
    # Fallback to a minimal provider list to ensure the UI shows options
    if not providers:
        providers = ["openai", "ollama"]
    provider_items = {PROVIDER_LABELS.get(p, p.title()): p for p in providers}
    # default provider from DEFAULT_PROFILE if available
    default_profile = CONFIG.get("profiles", {}).get(DEFAULT_PROFILE, {})
    default_provider = default_profile.get("llm_provider", providers[0] if providers else None)

    provider_select = Select(
        id="ModelProvider",
        label="🤖 LLM 제공자 (Provider)",
        items=provider_items,
        initial_value=default_provider,
    )

    # Model select based on default provider
    model_list = CONFIG.get("llm_providers", {}).get(default_provider, [])
    # Fallback: if the default provider has no models configured, use a small sane list
    if not model_list:
        model_list = ["gpt-4o", "gpt-3.5-turbo"] if default_provider == "openai" else ["llama3"]
    model_items = {}
    for m in model_list:
        icon = next((ic for k, ic in MODEL_ICONS.items() if k in m), "🤖")
        model_items[f"{icon} {m}"] = m

    default_model = default_profile.get("llm_model", model_list[0] if model_list else None)
    model_select = Select(
        id="ModelName",
        label="🔎 모델 선택 (Model)",
        items=model_items,
        initial_value=default_model,
    )

    # Mode select: operation modes (e.g., Draft vs Edit)
    mode_select = Select(
        id="OperationMode",
        label="⚙️ 동작 모드 (Mode)",
        items={"Drafting": "draft", "Editing": "edit"},
        initial_value="draft",
    )

    try:
        await cl.ChatSettings([provider_select, model_select, mode_select]).send()
    except Exception as e:
        # If ChatSettings can't be sent (context issues), log and notify the chat so
        # the user still has a way to pick a model via chat messages.
        import traceback

        traceback.print_exc()
        await cl.Message(content=(
            "설정 패널을 표시할 수 없습니다. 상단 우측의 설정(⚙️) 메뉴를 확인해주세요."
        )).send()