from enum import Enum


class SessionKey(str, Enum):
    GITHUB_CLIENT = "github_client"
    GITHUB_PAT = "github_pat"
    GITHUB_REPO = "github_repo"
    # --- ADDED: Key to store the authenticated user's name ---
    GITHUB_USERNAME = "github_username"
    # Timestamp when PAT was stored (ISO format)
    GITHUB_PAT_STORED_AT = "github_pat_stored_at"

    CURRENT_STAGE = "current_stage"

    BLOG_DRAFT = "blog_draft"
    BLOG_POST = "blog_post"
    BLOG_CREATOR_AGENT = "blog_creator_agent"
    MESSAGE_LIST = "message_list"
    USER_REQUEST = "user_request"
    VECTOR_STORE = "vector_store"
    RETRIEVER = "retriever"
    PROCESSED_DOCUMENTS = "processed_documents"

    IS_PUBLISHED = "is_published"
    SESSION_ID = "session_id"
    VISION_MODEL = "vision_model"
    ASR_MODEL = "asr_model"