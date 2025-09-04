# src/config.py
import os
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml
from dotenv import load_dotenv

# --- 초기 설정 ---
load_dotenv() # .env 파일에서 환경 변수를 로드합니다.

# 임시 기본값 설정 (YAML 로딩 전에 필요)
_ROOT_MARKER = "pyproject.toml"

# --- 경로 함수 ---
def find_project_root() -> Path:
    """pyproject.toml 파일을 기준으로 프로젝트의 루트 디렉토리를 찾습니다."""
    current_path = Path().resolve()
    while current_path != current_path.parent:
        if (current_path / _ROOT_MARKER).exists():
            return current_path
        current_path = current_path.parent
    raise FileNotFoundError("Project root not found.")

# --- 헬퍼 함수 ---
def get_env_var(key: str, default: str = None) -> str:
    """환경 변수를 가져오거나, 없으면 기본값을 사용하거나 에러를 발생시킵니다."""
    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"{key} not set in environment variables and no default provided.")
    return value

def load_yaml(path: Path) -> dict:
    """YAML 파일을 로드합니다."""
    p = Path(path)
    # If the file doesn't exist, return an empty dict so imports don't fail.
    if not p.exists():
        return {}
    try:
        with open(p, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            return data or {}
    except yaml.YAMLError:
        # If YAML is invalid, return empty dict to allow the app to continue running.
        return {}

# --- 핵심 설정 로딩 ---
ROOT_DIR = find_project_root()
CONFIG_FILE = ROOT_DIR / "configs" / "config.yaml"
PROMPTS_FILE = ROOT_DIR / "prompts" / "prompts.yaml"

CONFIG = load_yaml(CONFIG_FILE)
PROMPTS = load_yaml(PROMPTS_FILE)

# 시간대 설정: YAML에서 읽어옴 (기본값: UTC)
TIMEZONE_STR = CONFIG.get("app", {}).get("timezone", "UTC")
TIMEZONE: ZoneInfo = ZoneInfo(TIMEZONE_STR)

# 애플리케이션 설정: YAML에서 읽어옴
APP_CONFIG = CONFIG.get("app", {})
_ROOT_MARKER = APP_CONFIG.get("root_marker", "pyproject.toml")
DEFAULT_PROFILE = APP_CONFIG.get("default_profile", "default_cpu")
DIRECTORY_CONFIG = APP_CONFIG.get("directories", {})
LOGS_DIR_NAME = DIRECTORY_CONFIG.get("logs", "logs")
DATA_DIR_NAME = DIRECTORY_CONFIG.get("data", "data")

# --- 환경 프로필 선택 ---
# ENV_PROFILE 환경 변수를 읽어 활성 프로필을 결정합니다. (기본값: YAML에서 읽어옴)
ENV_PROFILE = get_env_var("ENV_PROFILE", DEFAULT_PROFILE)
ACTIVE_PROFILE = CONFIG["profiles"][ENV_PROFILE]

# --- API 키 ---
OPENAI_API_KEY = get_env_var("OPENAI_API_KEY")
UPSTAGE_API_KEY = get_env_var("UPSTAGE_API_KEY")
TAVILY_API_KEY = get_env_var("TAVILY_API_KEY")

# --- 디렉토리 경로 ---
LOG_ROOT_DIR = ROOT_DIR / LOGS_DIR_NAME
DATA_DIR = ROOT_DIR / DATA_DIR_NAME
LOG_ROOT_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# --- 로드된 설정값 변수화 ---
# 모델 설정
LLM_PROVIDER = ACTIVE_PROFILE["llm_provider"]
LLM_MODEL = ACTIVE_PROFILE["llm_model"]
EMBEDDING_PROVIDER = ACTIVE_PROFILE["embedding_provider"]
EMBEDDING_MODEL = ACTIVE_PROFILE["embedding_model"]

# 데이터 수집(Ingestion) 설정
INGESTION_CONFIG = CONFIG.get("ingestion", {})
INGESTION_PARSER = INGESTION_CONFIG.get("parser", "local")
API_LOADER_CONFIG = INGESTION_CONFIG.get("api_loader", {})

TEXT_SPLITTER_CONFIG = INGESTION_CONFIG.get("text_splitter", {})
DEFAULTS_CONFIG = CONFIG.get("defaults", {})
DEFAULT_TEXT_SPLITTER = DEFAULTS_CONFIG.get("text_splitter", {})
CHUNK_SIZE = TEXT_SPLITTER_CONFIG.get("chunk_size", DEFAULT_TEXT_SPLITTER.get("chunk_size", 1024))
CHUNK_OVERLAP = TEXT_SPLITTER_CONFIG.get("chunk_overlap", DEFAULT_TEXT_SPLITTER.get("chunk_overlap", 256))

# 벡터 저장소 설정
VECTOR_STORE_CONFIG = CONFIG.get("vector_store", {})
DEFAULT_VECTOR_STORE = DEFAULTS_CONFIG.get("vector_store", {})
COLLECTION_NAME = VECTOR_STORE_CONFIG.get("collection_name", DEFAULT_VECTOR_STORE.get("collection_name", "default_collection"))
SEARCH_TYPE = VECTOR_STORE_CONFIG.get("search_type", DEFAULT_VECTOR_STORE.get("search_type", "similarity"))
SEARCH_KWARGS = VECTOR_STORE_CONFIG.get("search_kwargs", DEFAULT_VECTOR_STORE.get("search_kwargs", {"k": 5}))

# 프롬프트 설정
DRAFT_PROMPT_TEMPLATE = PROMPTS.get("draft_prompt", "")
UPDATE_PROMPT_TEMPLATE = PROMPTS.get("update_prompt", "")

# --- 에이전트 설정 ---
AGENT_CONFIG = CONFIG.get("agent", {})
DEFAULT_AGENT = DEFAULTS_CONFIG.get("agent", {})

TAVILY_CONFIG = AGENT_CONFIG.get("tavily", {})
DEFAULT_TAVILY = DEFAULT_AGENT.get("tavily", {})
TAVILY_MAX_RESULTS = TAVILY_CONFIG.get("max_results", DEFAULT_TAVILY.get("max_results", 3))
TAVILY_SIMILARITY_THRESHOLD = TAVILY_CONFIG.get("similarity_threshold", DEFAULT_TAVILY.get("similarity_threshold", 0.9))

RETRIEVER_TOOL_CONFIG = AGENT_CONFIG.get("retriever_tool", {})
DEFAULT_RETRIEVER_TOOL = DEFAULT_AGENT.get("retriever_tool", {})
RETRIEVER_TOOL_NAME = RETRIEVER_TOOL_CONFIG.get("name", DEFAULT_RETRIEVER_TOOL.get("name", "document_search"))
RETRIEVER_TOOL_DESCRIPTION = RETRIEVER_TOOL_CONFIG.get("description", DEFAULT_RETRIEVER_TOOL.get("description", "Document retriever tool"))

MAX_HISTORY_MESSAGES = AGENT_CONFIG.get("max_history_messages", DEFAULT_AGENT.get("max_history_messages", 50))
HISTORY_TOKEN_LIMIT = AGENT_CONFIG.get("history_token_limit", DEFAULT_AGENT.get("history_token_limit", 3000))
HISTORY_STRATEGY = AGENT_CONFIG.get("history_strategy", DEFAULT_AGENT.get("history_strategy", "truncate"))

# LLM specific agent config
AGENT_LLM_CONFIG = AGENT_CONFIG.get("llm", {})
DEFAULT_AGENT_LLM = DEFAULT_AGENT.get("llm", {})
AGENT_LLM_MAX_TOKENS = AGENT_LLM_CONFIG.get("max_tokens", DEFAULT_AGENT_LLM.get("max_tokens", None))