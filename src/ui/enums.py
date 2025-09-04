from enum import Enum


class SessionKey(str, Enum):
    GITHUB_CLIENT = "github_client"
    GITHUB_PAT = "github_pat"
    GITHUB_REPO = "github_repo"
    # --- ADDED: Key to store the authenticated user's name ---
    GITHUB_USERNAME = "github_username"

    CURRENT_STAGE = "current_stage"

    BLOG_DRAFT = "blog_draft"
    BLOG_POST = "blog_post"
    BLOG_CREATOR_AGENT = "blog_creator_agent"
    MESSAGE_LIST = "message_list"
    USER_REQUEST = "user_request"
    VECTOR_STORE = "vector_store"
    RETRIEVER = "retriever"

    IS_PUBLISHED = "is_published"
    SESSION_ID = "session_id"
