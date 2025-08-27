# src/config.py
import os
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml
from dotenv import load_dotenv

# --- 초기 설정 ---
load_dotenv() # .env 파일에서 환경 변수를 로드합니다.
TIMEZONE: ZoneInfo = ZoneInfo("Asia/Seoul")
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

# --- 환경 프로필 선택 ---
# ENV_PROFILE 환경 변수를 읽어 활성 프로필을 결정합니다. (기본값: default_cpu)
ENV_PROFILE = get_env_var("ENV_PROFILE", "default_cpu")
ACTIVE_PROFILE = CONFIG["profiles"][ENV_PROFILE]

# --- API 키 ---
OPENAI_API_KEY = get_env_var("OPENAI_API_KEY")
UPSTAGE_API_KEY = get_env_var("UPSTAGE_API_KEY")

# --- 디렉토리 경로 ---
LOG_ROOT_DIR = ROOT_DIR / "logs"
DATA_DIR = ROOT_DIR / "data"
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
CHUNK_SIZE = TEXT_SPLITTER_CONFIG.get("chunk_size", 1024)
CHUNK_OVERLAP = TEXT_SPLITTER_CONFIG.get("chunk_overlap", 256)

# 벡터 저장소 설정
VECTOR_STORE_CONFIG = CONFIG.get("vector_store", {})
COLLECTION_NAME = VECTOR_STORE_CONFIG.get("collection_name", "default_collection")
SEARCH_TYPE = VECTOR_STORE_CONFIG.get("search_type", "similarity")
SEARCH_KWARGS = VECTOR_STORE_CONFIG.get("search_kwargs", {"k": 5})

# 프롬프트 설정
DRAFT_PROMPT_TEMPLATE = PROMPTS.get("draft_prompt", "")
UPDATE_PROMPT_TEMPLATE = PROMPTS.get("update_prompt", "")